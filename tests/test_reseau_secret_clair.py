import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_reseau as reseau

SECRET = {"Authorization": "Bearer jeton"}


class TestSecretEnClair(unittest.TestCase):
    def _rien_ne_part(self, appel):
        with mock.patch.object(reseau._OUVREUR, "open") as ouvrir, \
                mock.patch("urllib.request.urlopen") as urlopen:
            with self.assertRaises(ValueError):
                appel()
        self.assertEqual(ouvrir.call_count + urlopen.call_count, 0)

    def test_refuse_un_secret_sur_http_non_local(self):
        adresse = "http://exemple.org/api"
        self._rien_ne_part(lambda: reseau.telecharger_texte(adresse, entetes=SECRET))
        self._rien_ne_part(lambda: reseau.telecharger_json(adresse, entetes=SECRET))
        self._rien_ne_part(lambda: reseau.envoyer_json(adresse, {"a": 1}, entetes=SECRET))
        self._rien_ne_part(lambda: reseau.envoyer_formulaire(adresse, {"a": "1"}, entetes=SECRET))

    def test_noms_d_en_tetes_insensibles_a_la_casse(self):
        for nom in ("authorization", "COOKIE", "Proxy-Authorization", "cookie"):
            self._rien_ne_part(
                lambda nom=nom: reseau.telecharger_texte("http://exemple.org/", entetes={nom: "x"}))

    def test_adresses_locales_acceptees(self):
        for adresse in ("http://127.0.0.1:8000/x", "http://localhost/x", "http://[::1]:8000/x"):
            with mock.patch.object(reseau._OUVREUR, "open") as ouvrir:
                reseau._ouvrir(adresse, 5, SECRET)
            self.assertEqual(ouvrir.call_count, 1, adresse)

    def test_faux_locaux_refuses(self):
        for adresse in ("http://localhost.evil.com/", "http://127.0.0.1.evil.com/"):
            self._rien_ne_part(lambda a=adresse: reseau.telecharger_texte(a, entetes=SECRET))

    def test_https_accepte_avec_secret(self):
        with mock.patch.object(reseau._OUVREUR, "open") as ouvrir:
            reseau._ouvrir("https://exemple.org/api", 5, SECRET)
        self.assertEqual(ouvrir.call_count, 1)

    def test_http_sans_secret_accepte(self):
        with mock.patch.object(reseau._OUVREUR, "open") as ouvrir:
            reseau._ouvrir("http://exemple.org/", 5, {"X-Test": "1"})
        self.assertEqual(ouvrir.call_count, 1)
        with mock.patch("urllib.request.urlopen") as urlopen:
            reseau._ouvrir("http://exemple.org/", 5)
        self.assertEqual(urlopen.call_count, 1)


if __name__ == "__main__":
    unittest.main()
