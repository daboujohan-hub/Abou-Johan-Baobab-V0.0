import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from baobab.explication import expliquer_code


class TestExplication(unittest.TestCase):
    def test_ligne_traduite(self):
        texte = expliquer_code('afficher("Salut")')
        self.assertIn('Baobab : afficher("Salut")', texte)
        self.assertIn('Python : print("Salut")', texte)

    def test_ligne_identique(self):
        texte = expliquer_code("x = 5")
        self.assertIn("(identique)", texte)

    def test_mots_traduits(self):
        texte = expliquer_code("si vrai:\n    passer")
        self.assertIn("si  ->  if", texte)
        self.assertIn("vrai  ->  True", texte)
        self.assertIn("passer  ->  pass", texte)

    def test_lignes_vides_ignorees(self):
        texte = expliquer_code("x = 1\n\ny = 2")
        self.assertNotIn("Ligne 2", texte)
        self.assertIn("Ligne 3", texte)


if __name__ == "__main__":
    unittest.main()
