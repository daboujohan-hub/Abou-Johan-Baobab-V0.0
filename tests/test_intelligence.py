import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from baobab.transpileur import transpiler


class TestNomsDuProgrammeur(unittest.TestCase):
    def test_variable_qui_ressemble_a_un_mot_baobab(self):
        self.assertEqual(
            transpiler("maximum = 10\nafficher(maximum)"),
            "maximum = 10\nprint(maximum)",
        )

    def test_parametre_de_fonction(self):
        self.assertEqual(
            transpiler("fonction f(somme):\n    retourner somme"),
            "def f(somme):\n    return somme",
        )

    def test_variable_de_boucle(self):
        self.assertEqual(
            transpiler("pour minimum dans [1]:\n    afficher(minimum)"),
            "for minimum in [1]:\n    print(minimum)",
        )

    def test_fonction_du_programmeur(self):
        code = "fonction somme(a, b):\n    retourner a + b\nafficher(somme(1, 2))"
        attendu = "def somme(a, b):\n    return a + b\nprint(somme(1, 2))"
        self.assertEqual(transpiler(code), attendu)

    def test_mot_baobab_toujours_traduit_sinon(self):
        self.assertEqual(transpiler("afficher(maximum(1, 2))"), "print(max(1, 2))")

    def test_argument_nomme_ne_compte_pas(self):
        self.assertEqual(
            transpiler("x = trier(l, key=longueur)"), "x = sorted(l, key=len)"
        )


class TestFString(unittest.TestCase):
    def test_code_dans_les_accolades(self):
        self.assertEqual(
            transpiler('afficher(f"Il y a {longueur(x)} éléments")'),
            'print(f"Il y a {len(x)} éléments")',
        )

    def test_texte_hors_accolades_intact(self):
        self.assertEqual(transpiler('f"si {x} et"'), 'f"si {x} et"')

    def test_accolades_doubles(self):
        self.assertEqual(transpiler('f"{{si}}"'), 'f"{{si}}"')

    def test_format(self):
        self.assertEqual(transpiler('f"{prix:.2f} F"'), 'f"{prix:.2f} F"')

    def test_module_dans_fstring(self):
        code = 'importer hasard\nafficher(f"{hasard.entier(1, 6)}")'
        attendu = 'import random\nprint(f"{random.randint(1, 6)}")'
        self.assertEqual(transpiler(code), attendu)

    def test_texte_normal_avec_accolades_intact(self):
        self.assertEqual(transpiler('afficher("{longueur}")'), 'print("{longueur}")')


class TestNouveauxMots(unittest.TestCase):
    def test_lambda(self):
        self.assertEqual(
            transpiler("carre = anonyme x: x * x"), "carre = lambda x: x * x"
        )

    def test_effacer_et_verifier(self):
        self.assertEqual(transpiler("effacer x"), "del x")
        self.assertEqual(transpiler("verifier x > 0"), "assert x > 0")

    def test_parent(self):
        code = (
            "classe B(A):\n"
            "    fonction construire(soi, nom):\n"
            "        parent().construire(nom)"
        )
        attendu = (
            "class B(A):\n"
            "    def __init__(self, nom):\n"
            "        super().__init__(nom)"
        )
        self.assertEqual(transpiler(code), attendu)

    def test_fonctions_utiles(self):
        self.assertEqual(
            transpiler("en_liste(appliquer(carre, l))"), "list(map(carre, l))"
        )
        self.assertEqual(transpiler("tous(l)"), "all(l)")


if __name__ == "__main__":
    unittest.main()
