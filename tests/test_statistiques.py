import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_statistiques as statistiques
from baobab.transpileur import transpiler


class TestMoyenneMediane(unittest.TestCase):
    def test_moyenne(self):
        self.assertEqual(statistiques.moyenne([1, 2, 3, 4]), 2.5)
        self.assertEqual(statistiques.moyenne([2, 4]), 3.0)
        self.assertIsInstance(statistiques.moyenne([2, 4]), float)

    def test_mediane(self):
        self.assertEqual(statistiques.mediane([3, 1, 2]), 2)
        self.assertEqual(statistiques.mediane([1, 2, 3, 4]), 2.5)

    def test_listes_vides(self):
        with self.assertRaises(ValueError):
            statistiques.moyenne([])
        with self.assertRaises(ValueError):
            statistiques.mediane([])
        with self.assertRaises(ValueError):
            statistiques.ecart_type([])


class TestEcartType(unittest.TestCase):
    def test_population(self):
        # exemple classique : moyenne 5, écart type 2
        self.assertEqual(statistiques.ecart_type([2, 4, 4, 4, 5, 5, 7, 9]), 2.0)

    def test_echantillon(self):
        valeur = statistiques.ecart_type([2, 4, 4, 4, 5, 5, 7, 9], echantillon=True)
        self.assertAlmostEqual(valeur, 2.13809, places=4)

    def test_une_seule_valeur(self):
        self.assertEqual(statistiques.ecart_type([5]), 0.0)
        with self.assertRaises(ValueError):
            statistiques.ecart_type([5], echantillon=True)


class TestPourcentageFrequences(unittest.TestCase):
    def test_pourcentage(self):
        self.assertEqual(statistiques.pourcentage(1, 4), 25.0)
        self.assertEqual(statistiques.pourcentage(1, 3), 33.3)
        self.assertEqual(statistiques.pourcentage(1, 3, 0), 33.0)

    def test_pourcentage_total_nul(self):
        with self.assertRaises(ZeroDivisionError):
            statistiques.pourcentage(1, 0)

    def test_frequences(self):
        resultat = statistiques.frequences("abracadabra")
        self.assertEqual(list(resultat.items()),
                         [("a", 5), ("b", 2), ("r", 2), ("c", 1), ("d", 1)])

    def test_frequences_de_mots(self):
        self.assertEqual(statistiques.frequences(["oui", "non", "oui"]), {"oui": 2, "non": 1})


class TestDansBaobab(unittest.TestCase):
    def test_noms_gardes(self):
        self.assertEqual(
            transpiler("importer statistiques\nstatistiques.moyenne(notes)"),
            "import baobab_statistiques\nbaobab_statistiques.moyenne(notes)",
        )


if __name__ == "__main__":
    unittest.main()
