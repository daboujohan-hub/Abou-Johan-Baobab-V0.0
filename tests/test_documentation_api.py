import http.client
import json
import os
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_serveur as serveur


def note(parametres):
    """Retourne une note.

    Paramètre : id (entier).
    <script>alert(1)</script>
    """
    return {"id": parametres["id"]}


def accueil(parametres, demande):
    """La page d'accueil."""
    return "ok"


class TestDocumentationApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.public = os.path.join(cls.temp.name, "mon_dossier_public")
        os.makedirs(cls.public)
        serveur.SILENCIEUX = True
        serveur._routes.clear()
        serveur._methodes.clear()
        serveur._dossiers_publics.clear()
        serveur._sessions.clear()
        serveur.dossier_public(cls.public)
        serveur.route("/", accueil)
        serveur.route("/notes/<id:entier>", note, methodes=["GET", "DELETE"])
        serveur.route("/admin", lambda: "secret")
        serveur.route("/profil/<nom>", lambda p: {})
        serveur.documenter(masquer=["/admin"])
        serveur.documenter("/aide", "Aide privée", acces=lambda demande: demande.entetes.get("x-cle") == "ok")
        serveur.route("/ajoutee_apres", lambda: "tard")
        cls.serveur = serveur._creer("127.0.0.1", 0)
        cls.port = cls.serveur.server_address[1]
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()
        serveur._routes.clear()
        serveur._methodes.clear()
        serveur._dossiers_publics.clear()
        serveur.SILENCIEUX = False
        cls.temp.cleanup()

    def demander(self, chemin, entetes=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            c.request("GET", chemin, headers=entetes or {})
            r = c.getresponse()
            return r.status, r.read().decode("utf-8")
        finally:
            c.close()

    def test_la_page_liste_les_adresses(self):
        code, html = self.demander("/documentation")
        self.assertEqual(code, 200)
        for attendu in ("/notes/&lt;id:entier&gt;", "/profil/&lt;nom&gt;", "Retourne une note.",
                        "<code>id</code> : entier", "<code>nom</code> : texte", "fonction accueil"):
            self.assertIn(attendu, html)

    def test_les_methodes_sont_affichees(self):
        _, html = self.demander("/documentation")
        self.assertIn("méthodes DELETE, GET", html)
        self.assertIn("méthodes GET, POST", html)

    def test_le_texte_des_fonctions_est_protege(self):
        _, html = self.demander("/documentation")
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)

    def test_adresses_masquees_et_pages_de_documentation_absentes(self):
        _, html = self.demander("/documentation")
        self.assertNotIn("/admin", html)
        self.assertNotIn("/documentation", html)
        self.assertNotIn("/aide", html)

    def test_une_adresse_ajoutee_apres_apparait(self):
        _, html = self.demander("/documentation")
        self.assertIn("/ajoutee_apres", html)

    def test_version_pour_les_programmes(self):
        code, texte = self.demander("/documentation.json")
        donnees = json.loads(texte)
        self.assertEqual(code, 200)
        adresses = {a["adresse"]: a for a in donnees["adresses"]}
        self.assertEqual(adresses["/notes/<id:entier>"]["parametres_adresse"],
                         [{"nom": "id", "type": "entier"}])
        self.assertEqual(adresses["/notes/<id:entier>"]["methodes"], ["DELETE", "GET"])
        self.assertEqual(adresses["/"]["methodes"], ["GET", "POST"])
        self.assertTrue(adresses["/"]["recoit_la_demande"])
        self.assertFalse(adresses["/notes/<id:entier>"]["recoit_la_demande"])
        self.assertNotIn("/admin", adresses)

    def test_le_chemin_du_dossier_public_n_est_jamais_revele(self):
        _, html = self.demander("/documentation")
        _, texte = self.demander("/documentation.json")
        self.assertIn("mon_dossier_public", html)
        self.assertNotIn(self.temp.name, html)
        self.assertNotIn(self.temp.name, texte)

    def test_acces_reserve(self):
        for chemin in ("/aide", "/aide.json"):
            self.assertEqual(self.demander(chemin)[0], 404, chemin)
            self.assertEqual(self.demander(chemin, {"X-Cle": "mauvaise"})[0], 404, chemin)
            self.assertEqual(self.demander(chemin, {"X-Cle": "ok"})[0], 200, chemin)

    def test_fonction_sans_description(self):
        _, texte = self.demander("/documentation.json")
        adresses = {a["adresse"]: a for a in json.loads(texte)["adresses"]}
        self.assertEqual(adresses["/profil/<nom>"]["description"], "")


if __name__ == "__main__":
    unittest.main()
