import http.client
import json
import os
import re
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_serveur as serveur
from baobab.transpileur import transpiler


class Rep:
    def __init__(self, reponse, corps):
        self.status = reponse.status
        self.entetes = reponse.msg
        self.corps = corps

    def entete(self, nom):
        return self.entetes.get(nom)

    def cookies(self):
        return self.entetes.get_all("Set-Cookie", [])

    def json(self):
        return json.loads(self.corps.decode("utf-8"))


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.public = os.path.join(cls.temp.name, "public")
        os.makedirs(os.path.join(cls.public, "sous"))
        with open(os.path.join(cls.public, "style.css"), "w", encoding="utf-8") as f:
            f.write("body{color:red}")
        with open(os.path.join(cls.public, "sous", "image.txt"), "w", encoding="utf-8") as f:
            f.write("contenu")
        with open(os.path.join(cls.public, "a b.txt"), "w", encoding="utf-8") as f:
            f.write("avec espace")
        with open(os.path.join(cls.public, ".cache"), "w", encoding="utf-8") as f:
            f.write("cache")
        with open(os.path.join(cls.temp.name, "secret.txt"), "w", encoding="utf-8") as f:
            f.write("TOP SECRET")
        cls.lien_possible = True
        try:
            os.symlink(os.path.join(cls.temp.name, "secret.txt"), os.path.join(cls.public, "lien.txt"))
        except (OSError, NotImplementedError):
            cls.lien_possible = False

        serveur.SILENCIEUX = True
        serveur._routes.clear()
        serveur._dossiers_publics.clear()
        serveur._sessions.clear()
        serveur.dossier_public(cls.public)

        def compte(p, d):
            d.session["n"] = d.session.get("n", 0) + 1
            return {"n": d.session["n"], "id": d.session.id}

        def connexion(p, d):
            d.session["utilisateur"] = "awa"
            d.nouvelle_session()
            return {"ok": True}

        def deconnexion(p, d):
            d.fermer_session()
            return "au revoir"

        serveur.route("/json404", lambda: serveur.repondre(
            {"erreur": "introuvable"}, code=404, entetes={"X-Test": "1"}))
        serveur.route("/texte", lambda: serveur.repondre("a,b", type_contenu="text/plain"))
        serveur.route("/binaire", lambda: serveur.repondre(b"\x00\x01", type_contenu="application/x-demo"))
        serveur.route("/cookie", lambda: serveur.repondre(
            "ok", cookies=[serveur.cookie("visiteur", "Awa", duree=3600)]))
        serveur.route("/cookie_securise", lambda: serveur.repondre(
            "ok", cookies=[serveur.cookie("v", "1", securise=True)]))
        serveur.route("/lire_cookies", lambda p, d: d.cookies)
        serveur.route("/notes/<id:entier>", lambda p: {"id": p["id"], "type": type(p["id"]).__name__})
        serveur.route("/profil/<nom>", lambda p: {"nom": p["nom"]})
        serveur.route("/compte", compte)
        serveur.route("/moi", lambda p, d: {"utilisateur": d.session.get("utilisateur")})
        serveur.route("/connexion", connexion)
        serveur.route("/deconnexion", deconnexion)
        serveur.route("/sans_session", lambda: "ok")

        cls.serveur = serveur._creer("127.0.0.1", 0)
        cls.port = cls.serveur.server_address[1]
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()
        serveur._routes.clear()
        serveur._dossiers_publics.clear()
        serveur._sessions.clear()
        serveur.SILENCIEUX = False
        cls.temp.cleanup()

    def demander(self, chemin, methode="GET", corps=None, entetes=None):
        connexion = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            connexion.request(methode, chemin, body=corps, headers=entetes or {})
            reponse = connexion.getresponse()
            return Rep(reponse, reponse.read())
        finally:
            connexion.close()

    @staticmethod
    def identifiant_de(reponse):
        for cookie in reponse.cookies():
            trouve = re.match(rf"{serveur.NOM_COOKIE_SESSION}=([^;]*)", cookie)
            if trouve:
                return trouve.group(1)
        return None


class TestReponses(Base):
    def test_code_et_entetes(self):
        r = self.demander("/json404")
        self.assertEqual(r.status, 404)
        self.assertEqual(r.json(), {"erreur": "introuvable"})
        self.assertEqual(r.entete("X-Test"), "1")
        self.assertIn("application/json", r.entete("Content-Type"))

    def test_type_de_contenu(self):
        self.assertEqual(self.demander("/texte").entete("Content-Type"), "text/plain; charset=utf-8")
        r = self.demander("/binaire")
        self.assertEqual(r.entete("Content-Type"), "application/x-demo")
        self.assertEqual(r.corps, b"\x00\x01")

    def test_entetes_de_securite(self):
        r = self.demander("/texte")
        self.assertEqual(r.entete("X-Content-Type-Options"), "nosniff")
        self.assertEqual(r.entete("X-Frame-Options"), "SAMEORIGIN")

    def test_codes_invalides(self):
        for code in (99, 600, "404", True, None):
            with self.assertRaises(ValueError):
                serveur.repondre("x", code=code)

    def test_injection_d_entetes_refusee(self):
        with self.assertRaises(ValueError):
            serveur.repondre("x", entetes={"X-A": "ok\r\nSet-Cookie: pirate=1"})
        with self.assertRaises(ValueError):
            serveur.repondre("x", entetes={"X A": "ok"})


class TestAdresses(Base):
    def test_entier(self):
        self.assertEqual(self.demander("/notes/12").json(), {"id": 12, "type": "int"})

    def test_pas_un_entier(self):
        self.assertEqual(self.demander("/notes/abc").status, 404)

    def test_l_adresse_l_emporte_sur_les_parametres(self):
        self.assertEqual(self.demander("/notes/12?id=99").json()["id"], 12)

    def test_texte_decode(self):
        self.assertEqual(self.demander("/profil/Awa%20K").json(), {"nom": "Awa K"})

    def test_un_morceau_ne_contient_pas_de_slash(self):
        self.assertEqual(self.demander("/profil/a/b").status, 404)

    def test_adresses_mal_ecrites(self):
        with self.assertRaises(ValueError):
            serveur.route("/x/<id:inconnu>", lambda: "")
        with self.assertRaises(ValueError):
            serveur.route("sans-slash", lambda: "")
        with self.assertRaises(ValueError):
            serveur.route("/x/<a>/<a>", lambda: "")


class TestFichiersPublics(Base):
    def test_css(self):
        r = self.demander("/statique/style.css")
        self.assertEqual(r.status, 200)
        self.assertEqual(r.entete("Content-Type"), "text/css; charset=utf-8")
        self.assertEqual(r.corps, b"body{color:red}")
        self.assertEqual(r.entete("X-Content-Type-Options"), "nosniff")

    def test_sous_dossier_et_espace(self):
        self.assertEqual(self.demander("/statique/sous/image.txt").corps, b"contenu")
        self.assertEqual(self.demander("/statique/a%20b.txt").corps, b"avec espace")

    def test_fichiers_caches_refuses(self):
        self.assertEqual(self.demander("/statique/.cache").status, 404)
        self.assertEqual(self.demander("/statique/%2ecache").status, 404)

    def test_sortie_du_dossier_refusee(self):
        for chemin in ("/statique/../secret.txt", "/statique/%2e%2e/secret.txt",
                       "/statique/..%2fsecret.txt", "/statique/..%5csecret.txt",
                       "/statique/sous/../../secret.txt"):
            r = self.demander(chemin)
            self.assertEqual(r.status, 404, chemin)
            self.assertNotIn(b"TOP SECRET", r.corps, chemin)

    def test_lien_vers_l_exterieur_refuse(self):
        if not self.lien_possible:
            self.skipTest("liens symboliques indisponibles")
        r = self.demander("/statique/lien.txt")
        self.assertEqual(r.status, 404)
        self.assertNotIn(b"TOP SECRET", r.corps)

    def test_dossiers_et_inconnus(self):
        for chemin in ("/statique/sous", "/statique/", "/statique", "/statique/absent.css"):
            self.assertEqual(self.demander(chemin).status, 404, chemin)

    def test_seulement_en_lecture(self):
        self.assertEqual(self.demander("/statique/style.css", "POST", "a=1").status, 404)

    def test_mauvaise_configuration(self):
        with self.assertRaises(ValueError):
            serveur.dossier_public(self.public, "/")
        with self.assertRaises(FileNotFoundError):
            serveur.dossier_public(os.path.join(self.temp.name, "absent"))


class TestCookies(Base):
    def test_poser_un_cookie(self):
        entete = self.demander("/cookie").cookies()[0]
        for morceau in ("visiteur=Awa", "Max-Age=3600", "HttpOnly", "SameSite=Lax", "Path=/"):
            self.assertIn(morceau, entete)
        self.assertNotIn("Secure", entete)

    def test_cookie_securise(self):
        self.assertIn("Secure", self.demander("/cookie_securise").cookies()[0])

    def test_lire_les_cookies(self):
        r = self.demander("/lire_cookies", entetes={"Cookie": "a=1; b=deux"})
        self.assertEqual(r.json(), {"a": "1", "b": "deux"})

    def test_valeurs_speciales(self):
        entete = serveur.cookie("x", "a b;c").entete()
        self.assertEqual(serveur._lire_cookies(entete.split("; ")[0]), {"x": "a b;c"})

    def test_effacer(self):
        self.assertIn("Max-Age=0", serveur.cookie("x", "", duree=0).entete())

    def test_cookies_refuses(self):
        with self.assertRaises(ValueError):
            serveur.cookie("nom invalide;", "x")
        with self.assertRaises(ValueError):
            serveur.cookie("x", "ligne1\r\nligne2")
        with self.assertRaises(ValueError):
            serveur.cookie("x", "1", meme_site="None")
        with self.assertRaises(ValueError):
            serveur.cookie("x", "1", meme_site="Bizarre")
        serveur.cookie("x", "1", meme_site="None", securise=True)


class TestSessions(Base):
    def en_tete_cookie(self, identifiant):
        return {"Cookie": f"{serveur.NOM_COOKIE_SESSION}={identifiant}"}

    def test_premiere_visite_puis_retour(self):
        r1 = self.demander("/compte")
        identifiant = self.identifiant_de(r1)
        self.assertEqual(r1.json()["n"], 1)
        self.assertTrue(identifiant)
        cookie = r1.cookies()[0]
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)

        r2 = self.demander("/compte", entetes=self.en_tete_cookie(identifiant))
        self.assertEqual(r2.json()["n"], 2)
        self.assertEqual(r2.json()["id"], identifiant)
        self.assertEqual(r2.cookies(), [])  # pas de nouveau cookie

    def test_visiteurs_separes(self):
        a = self.demander("/compte")
        b = self.demander("/compte")
        self.assertNotEqual(self.identifiant_de(a), self.identifiant_de(b))
        self.assertEqual(b.json()["n"], 1)

    def test_identifiant_invente_refuse(self):
        r = self.demander("/compte", entetes=self.en_tete_cookie("identifiant-invente"))
        self.assertEqual(r.json()["n"], 1)
        nouveau = self.identifiant_de(r)
        self.assertIsNotNone(nouveau)                  # le serveur donne SON identifiant
        self.assertNotEqual(nouveau, "identifiant-invente")
        self.assertNotIn("identifiant-invente", serveur._sessions)

    def test_pas_de_cookie_sans_session(self):
        self.assertEqual(self.demander("/sans_session").cookies(), [])

    def test_connexion_change_l_identifiant_et_garde_les_donnees(self):
        ancien = self.identifiant_de(self.demander("/compte"))
        r = self.demander("/connexion", entetes=self.en_tete_cookie(ancien))
        nouveau = self.identifiant_de(r)
        self.assertTrue(nouveau)
        self.assertNotEqual(nouveau, ancien)
        # l'ancien identifiant ne donne plus accès à rien
        self.assertIsNone(self.demander("/moi", entetes=self.en_tete_cookie(ancien)).json()["utilisateur"])
        # le nouveau a gardé les données
        self.assertEqual(self.demander("/moi", entetes=self.en_tete_cookie(nouveau)).json()["utilisateur"], "awa")

    def test_deconnexion(self):
        ancien = self.identifiant_de(self.demander("/compte"))
        nouveau = self.identifiant_de(self.demander("/connexion", entetes=self.en_tete_cookie(ancien)))
        r = self.demander("/deconnexion", entetes=self.en_tete_cookie(nouveau))
        self.assertIn("Max-Age=0", r.cookies()[0])
        self.assertIsNone(self.demander("/moi", entetes=self.en_tete_cookie(nouveau)).json()["utilisateur"])

    def test_expiration(self):
        identifiant = self.identifiant_de(self.demander("/compte"))
        with mock.patch.object(serveur, "SESSION_DUREE", 0.05):
            time.sleep(0.15)
            r = self.demander("/compte", entetes=self.en_tete_cookie(identifiant))
        self.assertEqual(r.json()["n"], 1)
        self.assertNotEqual(self.identifiant_de(r), identifiant)

    def test_nombre_de_sessions_limite(self):
        with mock.patch.object(serveur, "SESSIONS_MAX", 3):
            for _ in range(8):
                serveur._sessions_creer()
            self.assertLessEqual(len(serveur._sessions), 3)

    def test_cookie_de_session_securise_en_https(self):
        with mock.patch.object(serveur, "COOKIES_SECURISES", True):
            self.assertIn("Secure", self.demander("/compte").cookies()[0])


class TestModeles(unittest.TestCase):
    def test_bases(self):
        self.assertEqual(serveur.modele("Bonjour {{nom}} !", {"nom": "Awa"}), "Bonjour Awa !")
        self.assertEqual(serveur.modele("{{ nom }}", {"nom": "Awa"}), "Awa")
        self.assertEqual(serveur.modele("{{x}}", {"x": None}), "")
        self.assertEqual(serveur.modele("{{n}}", {"n": 3}), "3")

    def test_html_protege(self):
        self.assertEqual(serveur.modele("{{x}}", {"x": "<b>&</b>"}), "&lt;b&gt;&amp;&lt;/b&gt;")
        self.assertEqual(serveur.modele("{{x|brut}}", {"x": "<b>ok</b>"}), "<b>ok</b>")

    def test_valeurs_imbriquees(self):
        valeurs = {"utilisateur": {"nom": "Awa", "ville": {"nom": "Abidjan"}}}
        self.assertEqual(serveur.modele("{{utilisateur.nom}} / {{utilisateur.ville.nom}}", valeurs), "Awa / Abidjan")

    def test_valeur_manquante(self):
        with self.assertRaises(ValueError) as ctx:
            serveur.modele("{{nom}}", {})
        self.assertIn("nom", str(ctx.exception))

    def test_option_inconnue(self):
        with self.assertRaises(ValueError):
            serveur.modele("{{x|truc}}", {"x": 1})

    def test_noms_prives_interdits(self):
        with self.assertRaises(ValueError):
            serveur.modele("{{x.__class__}}", {"x": "texte"})
        with self.assertRaises(ValueError):
            serveur.modele("{{_secret}}", {"_secret": 1})

    def test_une_valeur_n_est_jamais_reinterpretee_comme_un_modele(self):
        self.assertEqual(serveur.modele("{{a}}", {"a": "{{b}}", "b": "SECRET"}), "{{b}}")

    def test_repeter(self):
        liste = [{"texte": "a"}, {"texte": "<b>"}]
        self.assertEqual(serveur.repeter("<li>{{texte}}</li>", liste), "<li>a</li><li>&lt;b&gt;</li>")
        self.assertEqual(serveur.repeter("[{{element}}]", ["x", "y"]), "[x][y]")
        self.assertEqual(serveur.repeter("{{x}}", []), "")

    def test_page_avec_ou_sans_css(self):
        avec = serveur.page("T", "<p>x</p>", css="/statique/style.css")
        self.assertIn("href='/statique/style.css'", avec)
        self.assertNotIn("<style>", avec)
        self.assertIn("<style>", serveur.page("T", "x"))


class TestDansBaobab(unittest.TestCase):
    def test_noms_gardes(self):
        code = ("importer serveur\n"
                'serveur.dossier_public("public")\n'
                'serveur.route("/notes/<id:entier>", f)\n'
                'serveur.repondre({}, code=404)\n'
                "serveur.modele(t, v)\n")
        attendu = ("import baobab_serveur\n"
                   'baobab_serveur.dossier_public("public")\n'
                   'baobab_serveur.route("/notes/<id:entier>", f)\n'
                   'baobab_serveur.repondre({}, code=404)\n'
                   "baobab_serveur.modele(t, v)\n")
        self.assertEqual(transpiler(code), attendu)

    def test_session_dans_baobab(self):
        self.assertEqual(
            transpiler('demande.session["n"] = demande.session.obtenir("n", 0) + 1'),
            'demande.session["n"] = demande.session.get("n", 0) + 1',
        )


if __name__ == "__main__":
    unittest.main()
