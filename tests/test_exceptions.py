import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from baobab.transpileur import transpiler


class TestExceptions(unittest.TestCase):
    def test_traduction(self):
        self.assertEqual(transpiler("sauf ErreurValeur:"), "except ValueError:")

    def test_execution(self):
        code = 'essayer:\n    x = entier("abc")\nsauf ErreurValeur:\n    x = -1'
        espace = {}
        exec(transpiler(code), espace)
        self.assertEqual(espace["x"], -1)


if __name__ == "__main__":
    unittest.main()
