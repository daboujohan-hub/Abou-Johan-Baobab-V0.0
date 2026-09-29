import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from baobab.transpileur import transpiler


class TestV02(unittest.TestCase):
    def test_methode_liste(self):
        self.assertEqual(transpiler("l.ajouter(3)"), "l.append(3)")

    def test_module(self):
        code = "importer mathematiques\nafficher(mathematiques.racine(16))"
        self.assertEqual(transpiler(code), "import math\nprint(math.sqrt(16))")

    def test_depuis_importer(self):
        self.assertEqual(
            transpiler("depuis mathematiques importer racine, plafond"),
            "from math import sqrt, ceil",
        )

    def test_depuis_importer_entier(self):
        self.assertEqual(
            transpiler("depuis hasard importer entier"),
            "from random import randint",
        )

    def test_alias(self):
        code = "importer hasard comme h\nh.entier(1, 3)"
        self.assertEqual(transpiler(code), "import random as h\nh.randint(1, 3)")

    def test_variable_temps_sans_import(self):
        self.assertEqual(transpiler("temps = 5"), "temps = 5")

    def test_methode_definie_par_utilisateur(self):
        code = "fonction ajouter(soi, x):\n    passer\no.ajouter(1)"
        self.assertEqual(
            transpiler(code), "def ajouter(self, x):\n    pass\no.ajouter(1)"
        )

    def test_conversions(self):
        self.assertEqual(transpiler("en_liste(intervalle(3))"), "list(range(3))")

    def test_classe(self):
        code = "classe A:\n    fonction construire(soi):\n        passer"
        self.assertEqual(
            transpiler(code), "class A:\n    def __init__(self):\n        pass"
        )


if __name__ == "__main__":
    unittest.main()
