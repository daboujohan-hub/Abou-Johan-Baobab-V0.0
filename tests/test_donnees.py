import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_donnees as donnees


class TestJson(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.chemin = os.path.join(self.temp.name, "t.json")

    def tearDown(self):
        self.temp.cleanup()

    def test_aller_retour_avec_accents(self):
        valeur = {"nom": "Élodie", "liste": [1, 2, 3], "ok": True}
        donnees.ecrire_json(self.chemin, valeur)
        self.assertEqual(donnees.lire_json(self.chemin), valeur)
        with open(self.chemin, encoding="utf-8") as f:
            self.assertIn("Élodie", f.read())  # écrit tel quel, pas \u00c9

    def test_pas_de_fichier_temporaire_oublie(self):
        donnees.ecrire_json(self.chemin, [1])
        self.assertEqual(os.listdir(self.temp.name), ["t.json"])

    def test_erreur_d_ecriture_garde_l_ancien_fichier(self):
        donnees.ecrire_json(self.chemin, {"v": 1})
        with self.assertRaises(TypeError):
            donnees.ecrire_json(self.chemin, {"v": object()})
        self.assertEqual(donnees.lire_json(self.chemin), {"v": 1})
        self.assertEqual(os.listdir(self.temp.name), ["t.json"])

    def test_texte(self):
        self.assertEqual(donnees.depuis_json(donnees.vers_json({"é": [1, None]})), {"é": [1, None]})
        self.assertEqual(donnees.vers_json({"é": 1}), '{"é": 1}')

    def test_json_invalide(self):
        with self.assertRaises(ValueError):
            donnees.depuis_json("{pas du json")

    def test_fichier_absent(self):
        with self.assertRaises(FileNotFoundError):
            donnees.lire_json(os.path.join(self.temp.name, "absent.json"))


class TestCsv(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.chemin = os.path.join(self.temp.name, "t.csv")

    def tearDown(self):
        self.temp.cleanup()

    def test_aller_retour_point_virgule(self):
        lignes = [{"nom": "Awa", "ville": "Abidjan; Cocody"}, {"nom": "Élodie", "ville": "Paris"}]
        donnees.ecrire_csv(self.chemin, lignes, ";")
        self.assertEqual(donnees.lire_csv(self.chemin, ";"), lignes)

    def test_les_valeurs_reviennent_en_texte(self):
        donnees.ecrire_csv(self.chemin, [{"note": 15}])
        self.assertEqual(donnees.lire_csv(self.chemin), [{"note": "15"}])

    def test_colonnes_differentes(self):
        donnees.ecrire_csv(self.chemin, [{"a": 1}, {"a": 2, "b": 3}])
        self.assertEqual(donnees.lire_csv(self.chemin),
                         [{"a": "1", "b": ""}, {"a": "2", "b": "3"}])

    def test_fichier_excel_avec_bom(self):
        with open(self.chemin, "w", encoding="utf-8-sig", newline="") as f:
            f.write("nom;age\nAwa;20\n")
        self.assertEqual(donnees.lire_csv(self.chemin, ";"), [{"nom": "Awa", "age": "20"}])


if __name__ == "__main__":
    unittest.main()
