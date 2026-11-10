import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from baobab.bibliotheque import calendrier


class TestCalendrier(unittest.TestCase):
    def test_jour_et_format(self):
        self.assertEqual(calendrier.jour_de_la_semaine(2026, 11, 10), "mardi")
        self.assertEqual(calendrier.formater_date(2026, 11, 10), "mardi 10 novembre 2026")
        self.assertEqual(calendrier.formater_date(2026, 1, 1), "jeudi 1er janvier 2026")

    def test_jours_entre(self):
        self.assertEqual(calendrier.jours_entre(2026, 11, 10, 2026, 12, 25), 45)
        self.assertEqual(calendrier.jours_entre(2026, 12, 25, 2026, 11, 10), -45)

    def test_bissextile_et_mois(self):
        self.assertTrue(calendrier.est_bissextile(2024))
        self.assertFalse(calendrier.est_bissextile(2100))
        self.assertTrue(calendrier.est_bissextile(2000))
        self.assertEqual(calendrier.jours_dans_mois(2024, 2), 29)
        self.assertEqual(calendrier.jours_dans_mois(2026, 2), 28)

    def test_refus(self):
        with self.assertRaises(ValueError):
            calendrier.formater_date(2026, 2, 30)
        with self.assertRaises(ValueError):
            calendrier.jours_dans_mois(2026, 13)


if __name__ == "__main__":
    unittest.main()
