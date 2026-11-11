import os
import sys
import unittest

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "docs"))

import generer_fonctions as gen

AIDE = "Lance : python docs/generer_fonctions.py"
SEPARATEUR = "# Toutes les fonctions"


def _doc():
    with open(os.path.join(RACINE, "docs", "fonctions.md"), encoding="utf-8") as f:
        return f.read()


class TestDocFonctions(unittest.TestCase):
    def test_chaque_module_et_chaque_fonction_est_listee(self):
        doc = _doc()
        for module, elements in gen.inventaire():
            self.assertIn("## " + module + " ", doc, module + ". " + AIDE)
            for nom, _, _ in elements:
                self.assertIn("`" + module + "." + nom, doc, module + "." + nom + ". " + AIDE)

    def test_les_fonctions_des_precautions_existent(self):
        connues = {m + "." + n for m, elements in gen.inventaire() for n, _, _ in elements}
        for nom in gen.DANGEREUSES:
            self.assertIn(nom, connues, nom + " n'existe plus : mets à jour DANGEREUSES")

    def test_chaque_fonction_dangereuse_est_citee_dans_les_precautions(self):
        precautions = _doc().split(SEPARATEUR)[0]
        for nom in gen.DANGEREUSES:
            self.assertIn("`" + nom + "`", precautions, nom + ". " + AIDE)


if __name__ == "__main__":
    unittest.main()
