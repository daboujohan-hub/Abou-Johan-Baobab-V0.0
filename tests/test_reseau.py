import os
import socket
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_reseau as reseau
from baobab.transpileur import transpiler

AGENTS = []


class Site(BaseHTTPRequestHandler):
    def _repondre(self, corps, type_contenu="text/plain; charset=utf-8", code=200, entetes=()):
        self.send_response(code)
        self.send_header("Content-Type", type_contenu)
        self.send_header("Content-Length", str(len(corps)))
        for nom, valeur in entetes:
            self.send_header(nom, valeur)
        self.end_headers()
        self.wfile.write(corps)

    def do_GET(self):
        AGENTS.append(self.headers.get("User-Agent"))
        if self.path == "/texte":
            self._repondre("Bonjour é".encode("utf-8"))
        elif self.path == "/latin1":
            self._repondre("é".encode("latin-1"), "text/plain; charset=iso-8859-1")
        elif self.path == "/json":
            self._repondre(b'{"langage": "Baobab", "version": 1}', "application/json")
        elif self.path == "/json_casse":
            self._repondre(b"{pas du json")
        elif self.path == "/redirection":
            self._repondre(b"", code=302, entetes=[("Location", "/texte")])
        elif self.path == "/binaire":
            self._repondre(bytes(range(256)) * 20, "application/octet-stream")
        else:
            self._repondre(b"introuvable", code=404)

    def log_message(self, format, *arguments):
        pass


class TestReseau(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.serveur = ThreadingHTTPServer(("127.0.0.1", 0), Site)
        cls.base = f"http://127.0.0.1:{cls.serveur.server_address[1]}"
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()

    def test_texte_avec_accents(self):
        self.assertEqual(reseau.telecharger_texte(self.base + "/texte"), "Bonjour é")

    def test_texte_dans_un_autre_encodage(self):
        self.assertEqual(reseau.telecharger_texte(self.base + "/latin1"), "é")

    def test_json(self):
        self.assertEqual(reseau.telecharger_json(self.base + "/json"),
                         {"langage": "Baobab", "version": 1})

    def test_json_invalide(self):
        with self.assertRaises(ValueError):
            reseau.telecharger_json(self.base + "/json_casse")

    def test_page_introuvable(self):
        with self.assertRaises(reseau.ErreurReseau) as ctx:
            reseau.telecharger_texte(self.base + "/absente")
        self.assertIn("404", str(ctx.exception))

    def test_redirection_suivie(self):
        self.assertEqual(reseau.telecharger_texte(self.base + "/redirection"), "Bonjour é")

    def test_nom_du_programme_envoye(self):
        reseau.telecharger_texte(self.base + "/texte")
        self.assertTrue(AGENTS[-1].startswith("Baobab/"))

    def test_texte_trop_gros(self):
        with mock.patch.object(reseau, "TAILLE_MAX_TEXTE", 5):
            with self.assertRaises(reseau.ErreurReseau):
                reseau.telecharger_texte(self.base + "/texte")

    def test_telecharger_fichier(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "donnees.bin")
            taille = reseau.telecharger_fichier(self.base + "/binaire", chemin)
            self.assertEqual(taille, 5120)
            with open(chemin, "rb") as f:
                self.assertEqual(f.read(), bytes(range(256)) * 20)
            self.assertEqual(os.listdir(dossier), ["donnees.bin"])

    def test_fichier_trop_gros_ne_laisse_rien(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "gros.bin")
            with self.assertRaises(reseau.ErreurReseau):
                reseau.telecharger_fichier(self.base + "/binaire", chemin, taille_max=1000)
            self.assertEqual(os.listdir(dossier), [])

    def test_est_en_ligne(self):
        self.assertTrue(reseau.est_en_ligne(self.base + "/texte"))
        self.assertFalse(reseau.est_en_ligne(self.base + "/absente"))

    def test_serveur_injoignable(self):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        adresse = f"http://127.0.0.1:{port}/"
        with self.assertRaises(reseau.ErreurReseau) as ctx:
            reseau.telecharger_texte(adresse, delai=2)
        self.assertIn("Impossible de joindre", str(ctx.exception))
        self.assertFalse(reseau.est_en_ligne(adresse, delai=2))

    def test_adresses_dangereuses_refusees(self):
        for adresse in ("file:///etc/passwd", "ftp://exemple.org/x", "/chemin/local"):
            with self.assertRaises(ValueError):
                reseau.telecharger_texte(adresse)
            self.assertFalse(reseau.est_en_ligne(adresse))

    def test_encoder_adresse(self):
        self.assertEqual(reseau.encoder_adresse({"q": "baobab", "page": 2}), "q=baobab&page=2")
        self.assertEqual(reseau.encoder_adresse({"ville": "Abidjan é"}), "ville=Abidjan+%C3%A9")
        self.assertEqual(reseau.encoder_adresse({}), "")

    def test_noms_gardes_dans_baobab(self):
        self.assertEqual(
            transpiler("importer reseau\nreseau.telecharger_texte(u)"),
            "import baobab_reseau\nbaobab_reseau.telecharger_texte(u)",
        )


if __name__ == "__main__":
    unittest.main()
