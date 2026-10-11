import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_chaines as chaines
from baobab.transpileur import transpiler


class TestAccentsEtAdresses(unittest.TestCase):
    def test_sans_accents(self):
        self.assertEqual(chaines.sans_accents("Élève à l'été, cœur Œuvre ç"),
                         "Eleve a l'ete, coeur Oeuvre c")

    def test_ligatures_en_majuscules(self):
        self.assertEqual(chaines.sans_accents("ŒUVRE Œuvre æ"), "OEUVRE Oeuvre ae")

    def test_texte_sans_accent_inchange(self):
        self.assertEqual(chaines.sans_accents("Bonjour 123"), "Bonjour 123")

    def test_en_adresse(self):
        self.assertEqual(chaines.en_adresse("Mon Super Titre !"), "mon-super-titre")
        self.assertEqual(chaines.en_adresse("  Été 2026 : l'Œuvre  "), "ete-2026-l-oeuvre")
        self.assertEqual(chaines.en_adresse("!!!"), "")


class TestMotsEtPalindromes(unittest.TestCase):
    def test_compter_mots(self):
        self.assertEqual(chaines.compter_mots("Bonjour le monde"), 3)
        self.assertEqual(chaines.compter_mots("aujourd'hui peut-être"), 2)
        self.assertEqual(chaines.compter_mots("Hé ! Oui, là."), 3)
        self.assertEqual(chaines.compter_mots(""), 0)

    def test_palindromes(self):
        self.assertTrue(chaines.est_palindrome("Ésope reste ici et se repose"))
        self.assertTrue(chaines.est_palindrome("Engage le jeu que je le gagne"))
        self.assertTrue(chaines.est_palindrome("12321"))
        self.assertFalse(chaines.est_palindrome("Bonjour"))
        self.assertFalse(chaines.est_palindrome(""))
        self.assertFalse(chaines.est_palindrome("!!!"))


class TestCouper(unittest.TestCase):
    def test_couper(self):
        self.assertEqual(chaines.couper("Bonjour tout le monde", 10), "Bonjour t…")
        self.assertEqual(chaines.couper("court", 10), "court")
        self.assertEqual(chaines.couper("abcdef", 4, "..."), "a...")

    def test_jamais_plus_long_que_demande(self):
        for longueur in range(0, 12):
            self.assertLessEqual(len(chaines.couper("Bonjour tout le monde", longueur)), longueur)

    def test_espace_a_la_coupure(self):
        self.assertEqual(chaines.couper("Bonjour tout", 9), "Bonjour…")


class TestNombres(unittest.TestCase):
    def test_extraire_nombres(self):
        texte = "J'ai 3 chats et 2,5 kg, soit 4.75 € à -4°C, de 10-20 ans"
        self.assertEqual(chaines.extraire_nombres(texte), [3, 2.5, 4.75, -4, 10, 20])

    def test_types(self):
        resultat = chaines.extraire_nombres("3 et 2,5")
        self.assertIsInstance(resultat[0], int)
        self.assertIsInstance(resultat[1], float)

    def test_nombres_colles_a_des_lettres_ignores(self):
        self.assertEqual(chaines.extraire_nombres("Feuille A4 et 5kg"), [5])

    def test_aucun_nombre(self):
        self.assertEqual(chaines.extraire_nombres("Bonjour"), [])


class TestMotsFrequents(unittest.TestCase):
    def test_mots_frequents(self):
        phrase = "Le baobab est un arbre. Le baobab est grand, et l'arbre du baobab est vieux."
        self.assertEqual(chaines.mots_frequents(phrase, 2), {"baobab": 3, "arbre": 2})

    def test_petits_mots_ignores(self):
        self.assertEqual(chaines.mots_frequents("le la les un une des de du et ou"), {})

    def test_texte_vide(self):
        self.assertEqual(chaines.mots_frequents(""), {})

    def test_majuscules_et_accents(self):
        self.assertEqual(chaines.mots_frequents("Été été ÉTÉ soleil Soleil", 1), {"été": 3})


class TestDansBaobab(unittest.TestCase):
    def test_noms_gardes(self):
        self.assertEqual(
            transpiler("importer chaines\nchaines.couper(t, 5)"),
            "import baobab_chaines\nbaobab_chaines.couper(t, 5)",
        )

    def test_une_variable_nommee_texte_reste_libre(self):
        self.assertEqual(
            transpiler("importer chaines\ntexte = saisir()\nchaines.compter_mots(texte)"),
            "import baobab_chaines\ntexte = input()\nbaobab_chaines.compter_mots(texte)",
        )


if __name__ == "__main__":
    unittest.main()
