import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_donnees as donnees


class TestJsonProfond(unittest.TestCase):
    def test_limite_de_100_niveaux(self):
        self.assertEqual(len(donnees.depuis_json("[" * 100 + "]" * 100)), 1)
        with self.assertRaises(ValueError):
            donnees.depuis_json("[" * 101 + "]" * 101)
        with self.assertRaises(ValueError):
            donnees.depuis_json(b"[" * 101 + b"]" * 101)

    def test_les_textes_ne_comptent_pas(self):
        valeur = {"a": "[" * 500, "b": '"' + "{" * 500}
        self.assertEqual(donnees.depuis_json(json.dumps(valeur)), valeur)
        with self.assertRaises(ValueError):
            donnees.depuis_json('{"a": "ok", "b": ' + "[" * 101 + "]" * 101 + "}")

    def test_tres_profond_refuse_sans_planter(self):
        with self.assertRaises(ValueError):
            donnees.depuis_json("[" * 200000 + "]" * 200000)
        with self.assertRaises(ValueError):
            donnees.depuis_json("[" * 200000)

    def test_lire_json_refuse_un_fichier_trop_profond(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "profond.json")
            with open(chemin, "w", encoding="utf-8") as f:
                f.write("[" * 101 + "]" * 101)
            with self.assertRaises(ValueError):
                donnees.lire_json(chemin)
            bon = os.path.join(dossier, "bon.json")
            donnees.ecrire_json(bon, {"nom": "Élodie", "liste": [1, 2, {"x": [True, None]}]})
            self.assertEqual(donnees.lire_json(bon)["nom"], "Élodie")

    def test_json_normal_et_invalide_comme_avant(self):
        valeur = {"nom": "Élodie", "liste": [1, 2, {"x": [True, None]}], "texte": "a [b] {c}"}
        self.assertEqual(donnees.depuis_json(donnees.vers_json(valeur)), valeur)
        with self.assertRaises(ValueError):
            donnees.depuis_json("{pas du json")


if __name__ == "__main__":
    unittest.main()
