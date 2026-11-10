import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from baobab.bibliotheque import nombres


class TestNombres(unittest.TestCase):
    def test_en_lettres(self):
        cas = {
            0: "zéro", 1: "un", 16: "seize", 17: "dix-sept", 21: "vingt et un",
            22: "vingt-deux", 70: "soixante-dix", 71: "soixante et onze",
            75: "soixante-quinze", 80: "quatre-vingts", 81: "quatre-vingt-un",
            90: "quatre-vingt-dix", 91: "quatre-vingt-onze", 99: "quatre-vingt-dix-neuf",
            100: "cent", 101: "cent un", 200: "deux cents", 201: "deux cent un",
            280: "deux cent quatre-vingts",
            999: "neuf cent quatre-vingt-dix-neuf",
            1000: "mille", 1500: "mille cinq cents", 2000: "deux mille",
            80000: "quatre-vingt mille", 200000: "deux cent mille",
            1000000: "un million", 2000000: "deux millions",
            2500000: "deux millions cinq cent mille", 1000000000: "un milliard",
            -5: "moins cinq",
        }
        for n, attendu in cas.items():
            self.assertEqual(nombres.en_lettres(n), attendu, n)

    def test_formats(self):
        self.assertEqual(nombres.formater_nombre(1500000), "1 500 000")
        self.assertEqual(nombres.formater_monnaie(5000), "5 000 FCFA")
        self.assertEqual(nombres.formater_monnaie(750, "euros"), "750 euros")

    def test_refus(self):
        with self.assertRaises(TypeError):
            nombres.en_lettres("12")
        with self.assertRaises(ValueError):
            nombres.en_lettres(10 ** 12)


if __name__ == "__main__":
    unittest.main()
