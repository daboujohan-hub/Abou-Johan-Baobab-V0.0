import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_serveur as serveur


class TestNomsDEntetes(unittest.TestCase):
    def test_un_nom_ne_peut_pas_finir_par_un_retour_a_la_ligne(self):
        for nom in ("X-A\n", "X-A\r\n", "X-A\r", "X A", "X:A", "", "X-é"):
            with self.assertRaises(ValueError, msg=repr(nom)):
                serveur.repondre("x", entetes={nom: "valeur"})
            with self.assertRaises(ValueError, msg=repr(nom)):
                serveur.ErreurHTTP(400, "x", {nom: "valeur"})
        with self.assertRaises(ValueError):
            serveur.autoriser_origines([], entetes=["X-A\n"])

    def test_les_noms_normaux_passent(self):
        for nom in ("X-A", "Cache-Control", "X-Perso-1"):
            serveur.repondre("x", entetes={nom: "valeur"})


if __name__ == "__main__":
    unittest.main()
