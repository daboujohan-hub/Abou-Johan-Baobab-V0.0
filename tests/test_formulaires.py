import http.client
import os
import sys
import threading
import unittest
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_serveur as serveur


class TestFormulaires(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        serveur.SILENCIEUX = True
        serveur._routes.clear()
        cls.recu = []

        def envoyer(parametres):
            cls.recu.append(dict(parametres))
            return serveur.rediriger("/merci")

        serveur.route("/envoyer", envoyer)
        serveur.route("/merci", lambda: "<h1>Merci</h1>")
        cls.serveur = serveur._creer("127.0.0.1", 0)
        cls.port = cls.serveur.server_address[1]
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()
        serveur.SILENCIEUX = False

    def _poster(self, corps, entetes=None):
        connexion = http.client.HTTPConnection("127.0.0.1", self.port)
        connexion.request("POST", "/envoyer", body=corps, headers=entetes or {})
        reponse = connexion.getresponse()
        reponse.read()
        connexion.close()
        return reponse

    def test_post_puis_redirection(self):
        reponse = self._poster("nom=Awa&message=Salut")
        self.assertEqual(reponse.status, 303)
        self.assertEqual(reponse.getheader("Location"), "/merci")
        self.assertEqual(self.recu[-1], {"nom": "Awa", "message": "Salut"})

    def test_navigateur_suit_la_redirection(self):
        requete = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/envoyer", data=b"nom=Bob", method="POST")
        with urllib.request.urlopen(requete) as reponse:
            self.assertIn("Merci", reponse.read().decode("utf-8"))

    def test_formulaire_trop_gros(self):
        reponse = self._poster(b"x", {"Content-Length": "999999"})
        self.assertEqual(reponse.status, 413)

    def test_redirection_sure(self):
        self.assertEqual(serveur.rediriger("//autre-site.com").chemin, "/autre-site.com")


if __name__ == "__main__":
    unittest.main()
