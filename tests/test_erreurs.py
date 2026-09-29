import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from baobab.erreurs import expliquer


class TestErreurs(unittest.TestCase):
    def test_faute_sur_mot_baobab(self):
        texte = expliquer(NameError("name 'afficer' is not defined"))
        self.assertIn("Voulais-tu dire 'afficher'", texte)

    def test_faute_sur_variable(self):
        texte = expliquer(NameError("name 'prenm' is not defined"), ["prenom", "age"])
        self.assertIn("Voulais-tu dire 'prenom'", texte)

    def test_pas_de_suggestion(self):
        texte = expliquer(NameError("name 'zzzzz' is not defined"))
        self.assertNotIn("Voulais-tu dire", texte)

    def test_faute_sur_methode(self):
        texte = expliquer(AttributeError("'list' object has no attribute 'ajouer'"))
        self.assertIn("Voulais-tu dire 'ajouter'", texte)


if __name__ == "__main__":
    unittest.main()
