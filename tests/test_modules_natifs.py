import contextlib
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
from baobab.executeur import executer
from baobab.transpileur import transpiler


class TestModulesNatifs(unittest.TestCase):
    def test_les_noms_d_un_module_baobab_ne_sont_pas_traduits(self):
        self.assertEqual(
            transpiler('importer base\nbase.inserer(c, "t", {})'),
            'import baobab_base\nbaobab_base.inserer(c, "t", {})',
        )

    def test_avec_un_alias(self):
        self.assertEqual(
            transpiler('importer base comme b\nb.inserer(c, "t", {})'),
            'import baobab_base as b\nb.inserer(c, "t", {})',
        )

    def test_depuis_importer(self):
        self.assertEqual(
            transpiler("depuis base importer inserer"),
            "from baobab_base import inserer",
        )

    def test_les_listes_gardent_leurs_methodes(self):
        self.assertEqual(
            transpiler("importer base\nl.ajouter(3)\nl.inserer(0, 1)"),
            "import baobab_base\nl.append(3)\nl.insert(0, 1)",
        )

    def test_les_modules_python_sont_toujours_traduits(self):
        self.assertEqual(
            transpiler("importer hasard\nhasard.entier(1, 6)"),
            "import random\nrandom.randint(1, 6)",
        )
        self.assertEqual(
            transpiler("importer hasard comme h\nh.entier(1, 6)"),
            "import random as h\nh.randint(1, 6)",
        )
        self.assertEqual(
            transpiler("depuis hasard importer entier"),
            "from random import randint",
        )

    def test_programme_complet_avec_base(self):
        code = (
            "importer base\n"
            "c = base.ouvrir(\":memory:\")\n"
            "base.executer(c, \"CREATE TABLE n (id INTEGER PRIMARY KEY, t TEXT)\")\n"
            "base.inserer(c, \"n\", {\"t\": \"Bonjour\"})\n"
            "afficher(base.chercher(c, \"SELECT * FROM n\"))\n"
        )
        sortie = io.StringIO()
        with contextlib.redirect_stdout(sortie):
            self.assertEqual(executer(code, "<test>"), 0)
        self.assertEqual(sortie.getvalue().strip(), "[{'id': 1, 't': 'Bonjour'}]")


if __name__ == "__main__":
    unittest.main()
