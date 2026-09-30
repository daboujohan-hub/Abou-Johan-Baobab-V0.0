import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_serveur as serveur


def _lire(adresse):
    with urllib.request.urlopen(adresse) as reponse:
        return reponse.status, reponse.read().decode("utf-8")


class TestServeur(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        serveur.SILENCIEUX = True
        serveur._routes.clear()
        serveur.route("/", lambda: "<h1>Salut</h1>")
        serveur.route("/api", lambda: {"langage": "Baobab"})
        serveur.route("/bonjour", lambda p: "Bonjour " + serveur.echapper(p.get("nom", "?")))
        serveur.route("/erreur", lambda: 1 / 0)
        cls.serveur = serveur._creer("127.0.0.1", 0)
        cls.base = f"http://127.0.0.1:{cls.serveur.server_address[1]}"
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()
        serveur.SILENCIEUX = False

    def test_page(self):
        code, corps = _lire(self.base + "/")
        self.assertEqual(code, 200)
        self.assertIn("Salut", corps)

    def test_json(self):
        _, corps = _lire(self.base + "/api")
        self.assertEqual(json.loads(corps), {"langage": "Baobab"})

    def test_parametres(self):
        _, corps = _lire(self.base + "/bonjour?nom=Awa")
        self.assertIn("Bonjour Awa", corps)

    def test_parametre_dangereux_echappe(self):
        _, corps = _lire(self.base + "/bonjour?nom=%3Cscript%3E")
        self.assertNotIn("<script>", corps)

    def test_404(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            _lire(self.base + "/inconnue")
        self.assertEqual(ctx.exception.code, 404)
        ctx.exception.close()

    def test_500_en_francais(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            _lire(self.base + "/erreur")
        self.assertEqual(ctx.exception.code, 500)
        self.assertIn("Division par zéro", ctx.exception.read().decode("utf-8"))
        ctx.exception.close()

    def test_echapper(self):
        self.assertEqual(serveur.echapper("<b>"), "&lt;b&gt;")


if __name__ == "__main__":
    unittest.main()
