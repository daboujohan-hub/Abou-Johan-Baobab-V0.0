import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules baobab_dates, baobab_fichiers...
import baobab_dates as dates
import baobab_fichiers as fichiers
from baobab.transpileur import transpiler


class TestDates(unittest.TestCase):
    def test_bissextile(self):
        self.assertTrue(dates.est_bissextile(2024))
        self.assertFalse(dates.est_bissextile(2025))

    def test_difference(self):
        self.assertEqual(dates.difference_en_jours("2026-01-01", "2026-01-11"), 10)

    def test_jours_apres(self):
        self.assertEqual(dates.jours_apres("2026-01-30", 3), "2026-02-02")

    def test_nom_du_jour(self):
        self.assertEqual(dates.nom_du_jour("2026-09-29"), "mardi")

    def test_nom_du_mois(self):
        self.assertEqual(dates.nom_du_mois(2), "février")


class TestFichiers(unittest.TestCase):
    def test_ecrire_lire_ajouter(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "a.txt")
            fichiers.ecrire(chemin, "un")
            fichiers.ajouter_ligne(chemin, " deux")
            self.assertEqual(fichiers.lire(chemin), "un deux\n")
            self.assertTrue(fichiers.existe(chemin))
            fichiers.supprimer(chemin)
            self.assertFalse(fichiers.existe(chemin))


class TestImportBaobab(unittest.TestCase):
    def test_transpilation(self):
        code = "importer dates\nafficher(dates.annee())"
        self.assertEqual(
            transpiler(code), "import baobab_dates\nprint(baobab_dates.annee())"
        )

    def test_execution(self):
        espace = {}
        code = 'importer fichiers\nr = fichiers.existe("zzz_inexistant.txt")'
        exec(transpiler(code), espace)
        self.assertFalse(espace["r"])


if __name__ == "__main__":
    unittest.main()
