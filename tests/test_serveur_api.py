import http.client
import json
import os
import sys
import threading
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_serveur as serveur


class Rep:
    def __init__(self, reponse, corps):
        self.status = reponse.status
        self.entetes = reponse.msg
        self.corps = corps

    def entete(self, nom):
        return self.entetes.get(nom)

    def json(self):
        return json.loads(self.corps.decode("utf-8"))


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        serveur.SILENCIEUX = True
        serveur._routes.clear()
        serveur._methodes.clear()
        serveur._dossiers_publics.clear()
        serveur.autoriser_origines([])

        serveur.route("/echo", lambda p, d: {"json": d.json, "parametres": p, "methode": d.methode},
                      methodes=["POST", "PUT", "PATCH", "DELETE"])
        serveur.route("/formulaire", lambda p: {"parametres": p}, methodes=["POST"])
        serveur.route("/lecture", lambda: "bonjour")                       # GET et POST par défaut
        serveur.route("/ressource", lambda p, d: {"methode": d.methode},
                      methodes=["GET", "PUT", "DELETE"])
        serveur.route("/vide", lambda: serveur.repondre("", code=204), methodes=["DELETE"])
        serveur.route("/refuse", lambda: serveur.refuser(404, "Note introuvable"))
        serveur.route("/refuse_vide", lambda: serveur.refuser(403))
        serveur.route("/refuse_en_tetes", lambda: (_ for _ in ()).throw(
            serveur.ErreurHTTP(401, "Non", {"WWW-Authenticate": "Bearer"})))
        serveur.route("/plante", lambda: 1 / 0)
        cls.serveur = serveur._creer("127.0.0.1", 0)
        cls.port = cls.serveur.server_address[1]
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()
        serveur._routes.clear()
        serveur._methodes.clear()
        serveur.autoriser_origines([])
        serveur.SILENCIEUX = False

    def tearDown(self):
        serveur.autoriser_origines([])

    def demander(self, chemin, methode="GET", corps=None, entetes=None):
        connexion = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            connexion.request(methode, chemin, body=corps, headers=entetes or {})
            reponse = connexion.getresponse()
            return Rep(reponse, reponse.read())
        finally:
            connexion.close()

    def envoyer_json(self, chemin, donnees, methode="POST", entetes=None):
        corps = json.dumps(donnees, ensure_ascii=False).encode("utf-8")
        en_tetes = {"Content-Type": "application/json; charset=utf-8"}
        en_tetes.update(entetes or {})
        return self.demander(chemin, methode, corps, en_tetes)


class TestJson(Base):
    def test_lire_le_json_recu(self):
        r = self.envoyer_json("/echo", {"nom": "Élodie", "liste": [1, 2], "ok": True})
        self.assertEqual(r.status, 200)
        self.assertEqual(r.json()["json"], {"nom": "Élodie", "liste": [1, 2], "ok": True})

    def test_le_json_n_est_pas_melange_aux_parametres(self):
        r = self.envoyer_json("/echo?a=1", {"b": 2})
        self.assertEqual(r.json()["parametres"], {"a": "1"})

    def test_json_invalide(self):
        r = self.demander("/echo", "POST", b"{pas du json", {"Content-Type": "application/json"})
        self.assertEqual(r.status, 400)
        self.assertEqual(r.json(), {"erreur": "Le JSON envoyé est invalide"})

    def test_octets_invalides(self):
        r = self.demander("/echo", "POST", b"\xff\xfe", {"Content-Type": "application/json"})
        self.assertEqual(r.status, 400)

    def test_json_trop_profond(self):
        r = self.demander("/echo", "POST", b"[" * 200_000 + b"]" * 200_000,
                          {"Content-Type": "application/json"})
        self.assertEqual(r.status, 400)

    def test_contenu_qui_n_est_pas_du_json(self):
        r = self.demander("/echo", "POST", b"a=1",
                          {"Content-Type": "application/x-www-form-urlencoded"})
        self.assertEqual(r.status, 415)

    def test_pas_de_contenu(self):
        self.assertIsNone(self.demander("/echo", "POST").json()["json"])

    def test_json_trop_gros(self):
        with mock.patch.object(serveur, "TAILLE_MAX_JSON", 50):
            r = self.envoyer_json("/echo", {"texte": "x" * 100})
        self.assertEqual(r.status, 413)

    def test_les_formulaires_marchent_toujours(self):
        r = self.demander("/formulaire", "POST", b"nom=Awa",
                          {"Content-Type": "application/x-www-form-urlencoded"})
        self.assertEqual(r.json()["parametres"], {"nom": "Awa"})


class TestMethodes(Base):
    def test_get_et_post_par_defaut(self):
        self.assertEqual(self.demander("/lecture").status, 200)
        self.assertEqual(self.demander("/lecture", "POST", b"").status, 200)

    def test_les_autres_methodes_refusees_par_defaut(self):
        for methode in ("PUT", "PATCH", "DELETE"):
            r = self.demander("/lecture", methode, b"")
            self.assertEqual(r.status, 405, methode)
            permises = {m.strip() for m in r.entete("Allow").split(",")}
            self.assertEqual(permises, {"GET", "HEAD", "OPTIONS", "POST"})

    def test_methodes_choisies(self):
        self.assertEqual(self.demander("/ressource").json(), {"methode": "GET"})
        self.assertEqual(self.demander("/ressource", "PUT", b"").json(), {"methode": "PUT"})
        self.assertEqual(self.demander("/ressource", "DELETE").json(), {"methode": "DELETE"})
        self.assertEqual(self.demander("/ressource", "POST", b"").status, 405)
        self.assertEqual(self.demander("/ressource", "PATCH", b"").status, 405)

    def test_get_refuse_si_non_permis(self):
        self.assertEqual(self.demander("/echo").status, 405)

    def test_reponse_sans_contenu(self):
        r = self.demander("/vide", "DELETE")
        self.assertEqual(r.status, 204)
        self.assertEqual(r.corps, b"")
        self.assertIsNone(r.entete("Content-Length"))
        self.assertIsNone(r.entete("Content-Type"))

    def test_head(self):
        get = self.demander("/lecture")
        head = self.demander("/lecture", "HEAD")
        self.assertEqual(head.status, 200)
        self.assertEqual(head.corps, b"")
        self.assertEqual(head.entete("Content-Length"), str(len(get.corps)))
        self.assertEqual(self.demander("/echo", "HEAD").status, 405)

    def test_options_sans_cors(self):
        r = self.demander("/ressource", "OPTIONS")
        self.assertEqual(r.status, 204)
        permises = {m.strip() for m in r.entete("Allow").split(",")}
        self.assertEqual(permises, {"DELETE", "GET", "HEAD", "OPTIONS", "PUT"})

    def test_adresse_inconnue(self):
        for methode in ("GET", "PUT", "OPTIONS"):
            self.assertEqual(self.demander("/inconnue", methode, b"" if methode == "PUT" else None).status, 404)

    def test_methodes_mal_ecrites(self):
        for mauvaises in (["TRACE"], ["HEAD"], ["OPTIONS"], [], ["GET", "VOLER"]):
            with self.assertRaises(ValueError, msg=str(mauvaises)):
                serveur.route("/x", lambda: "", methodes=mauvaises)
        serveur.route("/x_ok", lambda: "", methodes="get")
        self.assertEqual(serveur._methodes["/x_ok"], ("GET",))


class TestErreurs(Base):
    def test_refuser(self):
        r = self.demander("/refuse")
        self.assertEqual(r.status, 404)
        self.assertEqual(r.json(), {"erreur": "Note introuvable"})

    def test_message_par_defaut(self):
        r = self.demander("/refuse_vide")
        self.assertEqual((r.status, r.json()), (403, {"erreur": "Forbidden"}))

    def test_entetes_d_erreur(self):
        r = self.demander("/refuse_en_tetes")
        self.assertEqual(r.status, 401)
        self.assertEqual(r.entete("WWW-Authenticate"), "Bearer")

    def test_codes_et_entetes_invalides(self):
        for code in (200, 399, 600, True, "404", None):
            with self.assertRaises(ValueError):
                serveur.ErreurHTTP(code, "x")
        with self.assertRaises(ValueError):
            serveur.ErreurHTTP(400, "x", {"X-A": "ok\r\nSet-Cookie: pirate=1"})

    def test_les_autres_erreurs_restent_des_500(self):
        self.assertEqual(self.demander("/plante").status, 500)


class TestCors(Base):
    SITE = "https://monsite.org"

    def avec_origine(self, origine, chemin="/lecture", methode="GET"):
        return self.demander(chemin, methode, entetes={"Origin": origine})

    def test_rien_par_defaut(self):
        r = self.avec_origine(self.SITE)
        self.assertIsNone(r.entete("Access-Control-Allow-Origin"))
        self.assertIsNone(r.entete("Vary"))

    def test_origine_autorisee(self):
        serveur.autoriser_origines([self.SITE, "http://localhost:3000"])
        r = self.avec_origine(self.SITE)
        self.assertEqual(r.entete("Access-Control-Allow-Origin"), self.SITE)
        self.assertEqual(r.entete("Vary"), "Origin")
        self.assertIsNone(r.entete("Access-Control-Allow-Credentials"))
        r = self.avec_origine("HTTP://LocalHost:3000")
        self.assertEqual(r.entete("Access-Control-Allow-Origin"), "HTTP://LocalHost:3000")

    def test_origine_non_autorisee(self):
        serveur.autoriser_origines([self.SITE])
        for origine in ("https://pirate.org", "https://monsite.org.pirate.org", "null",
                        "http://monsite.org"):
            r = self.avec_origine(origine)
            self.assertIsNone(r.entete("Access-Control-Allow-Origin"), origine)
            self.assertEqual(r.entete("Vary"), "Origin", origine)

    def test_tout_le_monde_jamais_avec_les_cookies(self):
        serveur.autoriser_origines(["*"])
        self.assertEqual(self.avec_origine("https://n-importe-qui.org").entete("Access-Control-Allow-Origin"), "*")
        with self.assertRaises(ValueError):
            serveur.autoriser_origines(["*"], avec_cookies=True)

    def test_cookies_pour_les_origines_choisies_seulement(self):
        serveur.autoriser_origines([self.SITE], avec_cookies=True)
        self.assertEqual(self.avec_origine(self.SITE).entete("Access-Control-Allow-Credentials"), "true")
        autre = self.avec_origine("https://pirate.org")
        self.assertIsNone(autre.entete("Access-Control-Allow-Credentials"))
        self.assertIsNone(autre.entete("Access-Control-Allow-Origin"))

    def test_origines_mal_ecrites(self):
        for mauvaise in ("monsite.org", "https://monsite.org/chemin", "javascript:alert(1)",
                         "https://", "ftp://monsite.org", "https://mon site.org"):
            with self.assertRaises(ValueError, msg=mauvaise):
                serveur.autoriser_origines([mauvaise])
        serveur.autoriser_origines(["https://monsite.org/"])  # le « / » final est enlevé
        self.assertIn("https://monsite.org", serveur._cors["origines"])

    def test_requete_preliminaire_autorisee(self):
        serveur.autoriser_origines([self.SITE])
        r = self.demander("/ressource", "OPTIONS", entetes={
            "Origin": self.SITE, "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "Authorization, content-type"})
        self.assertEqual(r.status, 204)
        self.assertEqual(r.entete("Access-Control-Allow-Origin"), self.SITE)
        self.assertIn("PUT", r.entete("Access-Control-Allow-Methods"))
        self.assertEqual(r.entete("Access-Control-Allow-Headers"), "Authorization, content-type")
        self.assertEqual(r.entete("Access-Control-Max-Age"), "600")

    def test_requete_preliminaire_refusee(self):
        serveur.autoriser_origines([self.SITE])
        cas = [
            {"Origin": "https://pirate.org", "Access-Control-Request-Method": "PUT"},
            {"Origin": self.SITE, "Access-Control-Request-Method": "POST"},       # non permise ici
            {"Origin": self.SITE, "Access-Control-Request-Method": "PUT",
             "Access-Control-Request-Headers": "X-Pirate"},
        ]
        for entetes in cas:
            r = self.demander("/ressource", "OPTIONS", entetes=entetes)
            self.assertEqual(r.status, 403, entetes)
            self.assertIsNone(r.entete("Access-Control-Allow-Methods"), entetes)

    def test_en_tetes_supplementaires(self):
        serveur.autoriser_origines([self.SITE], entetes=["X-Application"])
        r = self.demander("/ressource", "OPTIONS", entetes={
            "Origin": self.SITE, "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Application"})
        self.assertEqual(r.status, 204)

    def test_supprimer_les_autorisations(self):
        serveur.autoriser_origines([self.SITE])
        serveur.autoriser_origines([])
        self.assertIsNone(self.avec_origine(self.SITE).entete("Access-Control-Allow-Origin"))


class TestDocumentationDesMethodes(Base):
    def test_la_documentation_montre_les_methodes(self):
        serveur.documenter()
        donnees = self.demander("/documentation.json").json()
        adresses = {a["adresse"]: a for a in donnees["adresses"]}
        self.assertEqual(adresses["/ressource"]["methodes"], ["DELETE", "GET", "PUT"])
        self.assertEqual(adresses["/lecture"]["methodes"], ["GET", "POST"])
        html = self.demander("/documentation").corps.decode("utf-8")
        self.assertIn("méthodes DELETE, GET, PUT", html)


if __name__ == "__main__":
    unittest.main()
