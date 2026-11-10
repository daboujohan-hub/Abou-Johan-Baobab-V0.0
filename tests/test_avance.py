import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_avance as avance


class TestAvance(unittest.TestCase):
    def test_lire_valeur_lit_les_valeurs_simples(self):
        self.assertEqual(avance.lire_valeur("[1, 2, 3]"), [1, 2, 3])
        self.assertEqual(avance.lire_valeur('{"a": [1, 2], "b": "x"}'), {"a": [1, 2], "b": "x"})
        self.assertEqual(avance.lire_valeur("[vrai, faux]"), [True, False])
        self.assertEqual(avance.lire_valeur("  42  "), 42)
        self.assertEqual(avance.lire_valeur("'texte'"), "texte")

    def test_lire_valeur_refuse_le_code(self):
        for texte in ("__import__('os').getcwd()", "afficher(1)", "1 + 1",
                      "[x for x in [1]]", "", "{pas valide"):
            with self.assertRaises(ValueError, msg=texte):
                avance.lire_valeur(texte)

    def test_taille_et_profondeur_limitees(self):
        self.assertEqual(len(avance.lire_valeur("[" * 100 + "]" * 100)), 1)
        for texte in ("[" * 101 + "]" * 101, "[" * 200000 + "]" * 200000,
                      "[" * 200000, "1" * 100001):
            with self.assertRaises(ValueError):
                avance.lire_valeur(texte)

    def test_les_textes_ne_comptent_pas(self):
        valeur = avance.lire_valeur('["' + "[" * 500 + '"]')
        self.assertEqual(valeur, ["[" * 500])

    def test_evaluer(self):
        self.assertEqual(avance.evaluer("2 + 3"), 5)
        self.assertEqual(avance.evaluer("x * 2", {"x": 21}), 42)
        self.assertEqual(avance.evaluer("longueur([1, 2, 3])"), 3)
        self.assertEqual(avance.evaluer("vrai"), True)

    def test_evaluer_refuse_les_mauvais_types(self):
        with self.assertRaises(TypeError):
            avance.evaluer(5)
        with self.assertRaises(TypeError):
            avance.evaluer("1", variables=[1])

    def test_executer_texte(self):
        resultat = avance.executer_texte("a = 5\nb = a * 2")
        self.assertEqual((resultat["a"], resultat["b"]), (5, 10))
        self.assertNotIn("__builtins__", resultat)
        donnees = {"x": 1}
        avance.executer_texte("x = 99", donnees)
        self.assertEqual(donnees, {"x": 1})

    def test_compiler_texte(self):
        self.assertEqual(avance.evaluer(avance.compiler_texte("2 + 3", "eval")), 5)
        self.assertEqual(avance.executer_texte(avance.compiler_texte("z = 7"))["z"], 7)
        with self.assertRaises(ValueError):
            avance.compiler_texte("1", "autre")
        with self.assertRaises(TypeError):
            avance.compiler_texte(5)


if __name__ == "__main__":
    unittest.main()
