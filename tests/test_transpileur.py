import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from baobab.transpileur import transpiler


class TestTranspileur(unittest.TestCase):
    def test_afficher(self):
        self.assertEqual(transpiler('afficher("a")'), 'print("a")')

    def test_condition(self):
        code = "si x > 1:\n    afficher(x)\nsinon:\n    afficher(0)"
        attendu = "if x > 1:\n    print(x)\nelse:\n    print(0)"
        self.assertEqual(transpiler(code), attendu)

    def test_texte_intact(self):
        self.assertEqual(transpiler('afficher("si et sinon")'), 'print("si et sinon")')

    def test_commentaire_intact(self):
        self.assertEqual(transpiler("# si pour tantque"), "# si pour tantque")

    def test_apres_point(self):
        self.assertEqual(transpiler("objet.afficher()"), "objet.afficher()")

    def test_meme_nombre_de_lignes(self):
        code = "fonction f():\n    retourner vrai\n\nf()"
        self.assertEqual(transpiler(code).count("\n"), code.count("\n"))

    def test_fonction(self):
        self.assertEqual(
            transpiler("fonction f(a):\n    retourner a"),
            "def f(a):\n    return a",
        )


if __name__ == "__main__":
    unittest.main()
