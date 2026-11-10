import io
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from baobab import mots_cles
from baobab.transpileur import transpiler

NOUVEAUX = {
    "nom_du_fichier": "name", "tampon": "buffer", "numero_descripteur": "fileno",
    "erreurs_encodage": "errors", "detacher_tampon": "detach", "est_terminal": "isatty",
    "tampon_par_ligne": "line_buffering", "fins_de_ligne": "newlines",
    "reconfigurer": "reconfigure", "ecriture_directe": "write_through",
}


class TestAttributsFichiers(unittest.TestCase):
    def test_traductions(self):
        for francais, python in NOUVEAUX.items():
            self.assertEqual(transpiler("f." + francais), "f." + python, francais)
        self.assertEqual(mots_cles._ATTRIBUTS_FICHIERS_IGNORES, [])

    def test_les_noms_python_existent_vraiment(self):
        for python in NOUVEAUX.values():
            self.assertTrue(hasattr(io.TextIOWrapper, python), python)

    def test_un_nom_defini_par_le_programmeur_reste_intact(self):
        sortie = transpiler("fonction tampon(soi):\n    passer\nf.tampon")
        self.assertIn("f.tampon", sortie)
        self.assertNotIn("buffer", sortie)


if __name__ == "__main__":
    unittest.main()
