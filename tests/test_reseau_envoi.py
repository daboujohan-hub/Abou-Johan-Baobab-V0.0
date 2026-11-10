import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_reseau as reseau


class Site(BaseHTTPRequestHandler):
    """Un petit site : /echo renvoie ce qu'il reçoit (en JSON), les autres adresses redirigent."""

    def _repondre(self, corps, code=200, entetes=()):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corps)))
        for nom, valeur in entetes:
            self.send_header(nom, valeur)
        self.end_headers()
        self.wfile.write(corps)

    def _traiter(self):
        taille = int(self.headers.get("Content-Length") or 0)
        corps = self.rfile.read(taille) if taille else b""
        autre = f"http://127.0.0.1:{self.server.autre_port}/echo"
        if self.path == "/echo":
            info = {
                "methode": self.command,
                "entetes": {nom.lower(): valeur for nom, valeur in self.headers.items()},
                "corps": corps.decode("utf-8", "replace"),
            }
            self.server.recus.append(info)
            self._repondre(json.dumps(info).encode("utf-8"))
        elif self.path == "/meme-site":
            self._repondre(b"", 302, [("Location", "/echo")])
        elif self.path == "/autre-site":
            self._repondre(b"", 302, [("Location", autre)])
        elif self.path == "/autre-site-307":
            self._repondre(b"", 307, [("Location", autre)])
        elif self.path == "/vide":
            self._repondre(b"")
        elif self.path == "/profond":
            self._repondre(b"[" * 200 + b"]" * 200)
        else:
            self._repondre(b"oups", 500)

    do_GET = do_POST = do_PUT = do_DELETE = _traiter

    def log_message(self, format, *arguments):
        pass


class TestEnvoi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = ThreadingHTTPServer(("127.0.0.1", 0), Site)
        cls.b = ThreadingHTTPServer(("127.0.0.1", 0), Site)
        for serveur, autre in ((cls.a, cls.b), (cls.b, cls.a)):
            serveur.recus = []
            serveur.autre_port = autre.server_address[1]
            threading.Thread(target=serveur.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.a.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        for serveur in (cls.a, cls.b):
            serveur.shutdown()
            serveur.server_close()

    def setUp(self):
        self.a.recus.clear()
        self.b.recus.clear()

    def test_envoyer_json_envoie_le_corps_et_le_type(self):
        retour = reseau.envoyer_json(self.url + "/echo", {"n": [1, 2], "ok": True})
        self.assertEqual(retour["methode"], "POST")
        self.assertTrue(retour["entetes"]["content-type"].startswith("application/json"))
        self.assertEqual(json.loads(retour["corps"]), {"n": [1, 2], "ok": True})

    def test_envoyer_json_garde_les_accents_en_utf8(self):
        retour = reseau.envoyer_json(self.url + "/echo", {"nom": "Élodie"})
        self.assertIn("Élodie", retour["corps"])

    def test_envoyer_formulaire(self):
        texte = reseau.envoyer_formulaire(self.url + "/echo", {"a": "1", "b": "é"})
        retour = json.loads(texte)
        self.assertEqual(retour["corps"], "a=1&b=%C3%A9")
        self.assertEqual(retour["entetes"]["content-type"], "application/x-www-form-urlencoded")

    def test_choisir_la_methode(self):
        self.assertEqual(
            reseau.envoyer_json(self.url + "/echo", {"a": 1}, methode="put")["methode"], "PUT")
        self.assertEqual(
            reseau.envoyer_json(self.url + "/echo", {}, methode="DELETE")["methode"], "DELETE")
        with self.assertRaises(ValueError):
            reseau.envoyer_json(self.url + "/echo", {}, methode="TRACE")

    def test_entetes_personnalises_envoyes(self):
        retour = reseau.telecharger_json(
            self.url + "/echo", entetes={"X-Cle": "abc", "Authorization": "Bearer jeton"})
        self.assertEqual(retour["entetes"]["x-cle"], "abc")
        self.assertEqual(retour["entetes"]["authorization"], "Bearer jeton")
        self.assertTrue(retour["entetes"]["user-agent"].startswith("Baobab/"))

    def test_entrees_invalides_refusees(self):
        adresse = self.url + "/echo"
        with self.assertRaises(ValueError):
            reseau.telecharger_texte(adresse, entetes={"X-Test": "a\r\nX-Autre: b"})
        with self.assertRaises(ValueError):
            reseau.telecharger_texte(adresse, entetes={"X Test": "a"})
        with self.assertRaises(TypeError):
            reseau.telecharger_texte(adresse, entetes=["X-Test"])
        with self.assertRaises(TypeError):
            reseau.envoyer_formulaire(adresse, ["a"])
        with self.assertRaises(ValueError):
            reseau.envoyer_json("file:///etc/passwd", {})
        self.assertEqual(self.a.recus, [])

    def test_secrets_gardes_sur_le_meme_site(self):
        retour = reseau.telecharger_json(
            self.url + "/meme-site", entetes={"Authorization": "Bearer jeton"})
        self.assertEqual(retour["entetes"]["authorization"], "Bearer jeton")

    def test_secrets_retires_vers_un_autre_site(self):
        retour = reseau.telecharger_json(
            self.url + "/autre-site",
            entetes={"Authorization": "Bearer jeton", "X-Cle": "abc"})
        self.assertEqual(len(self.b.recus), 1)
        self.assertNotIn("authorization", retour["entetes"])
        self.assertNotIn("x-cle", retour["entetes"])
        self.assertTrue(retour["entetes"]["user-agent"].startswith("Baobab/"))

    def test_redirection_302_vers_un_autre_site_sans_donnees_ni_secrets(self):
        retour = reseau.envoyer_json(
            self.url + "/autre-site", {"mot": "secret"},
            entetes={"Authorization": "Bearer jeton", "X-Cle": "abc"})
        self.assertEqual(retour["methode"], "GET")
        self.assertEqual(retour["corps"], "")
        self.assertNotIn("authorization", retour["entetes"])
        self.assertNotIn("x-cle", retour["entetes"])
        self.assertEqual(len(self.b.recus), 1)

    def test_redirection_307_vers_un_autre_site_refusee(self):
        with self.assertRaises(reseau.ErreurReseau):
            reseau.envoyer_json(self.url + "/autre-site-307", {"mot": "secret"})
        self.assertEqual(self.b.recus, [])

    def test_reponse_vide_donne_rien(self):
        self.assertIsNone(reseau.envoyer_json(self.url + "/vide", {"a": 1}))

    def test_json_trop_profond_refuse(self):
        with self.assertRaises(reseau.ErreurReseau):
            reseau.telecharger_json(self.url + "/profond")

    def test_erreur_du_site(self):
        with self.assertRaises(reseau.ErreurReseau) as contexte:
            reseau.telecharger_texte(self.url + "/erreur")
        self.assertIn("500", str(contexte.exception))


if __name__ == "__main__":
    unittest.main()
