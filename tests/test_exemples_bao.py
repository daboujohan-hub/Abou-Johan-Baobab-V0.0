import contextlib
import io
import os
import unittest

from baobab.testeur import lancer_tests

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


class TestExemplesEnBaobab(unittest.TestCase):
    """Lance les tests écrits en Baobab (exemples/test_*.bao) : les exemples doivent marcher."""

    def test_les_tests_des_exemples_passent(self):
        ancien = os.getcwd()
        os.chdir(RACINE)  # les exemples utilisent des chemins comme exemples/public
        try:
            sortie = io.StringIO()
            with contextlib.redirect_stdout(sortie):
                code = lancer_tests("exemples")
        finally:
            os.chdir(ancien)
        self.assertEqual(code, 0, sortie.getvalue())
        self.assertIn("réussi(s)", sortie.getvalue())


if __name__ == "__main__":
    unittest.main()
