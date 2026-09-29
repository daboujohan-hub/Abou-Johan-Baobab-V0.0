import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_dessin as dessin


class TestDessin(unittest.TestCase):
    def test_sauvegarde_svg(self):
        dessin.nouvelle_feuille()
        dessin.avancer(100)
        with tempfile.TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "d.svg")
            dessin.sauvegarder(chemin)
            with open(chemin, encoding="utf-8") as f:
                contenu = f.read()
        self.assertIn("<svg", contenu)
        self.assertIn("<line", contenu)

    def test_crayon_leve(self):
        dessin.nouvelle_feuille()
        dessin.lever_crayon()
        dessin.avancer(50)
        self.assertEqual(dessin._etat["formes"], [])


if __name__ == "__main__":
    unittest.main()
