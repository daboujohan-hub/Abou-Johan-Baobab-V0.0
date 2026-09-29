import glob
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
from baobab.transpileur import transpiler


class TestExemples(unittest.TestCase):
    def test_tous_les_exemples_se_compilent(self):
        dossier = os.path.join(os.path.dirname(__file__), "..", "exemples")
        for chemin in sorted(glob.glob(os.path.join(dossier, "*.bao"))):
            with open(chemin, encoding="utf-8") as f:
                code = f.read()
            with self.subTest(fichier=os.path.basename(chemin)):
                compile(transpiler(code), chemin, "exec")


if __name__ == "__main__":
    unittest.main()
