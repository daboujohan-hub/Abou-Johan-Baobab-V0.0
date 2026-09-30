import datetime
import os
import sys
import threading
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_taches as taches


class TestTaches(unittest.TestCase):
    def setUp(self):
        taches.SILENCIEUX = True
        taches.tout_annuler()

    def tearDown(self):
        taches.tout_annuler()
        taches.SILENCIEUX = False

    def test_toutes_les(self):
        compteur = []
        assez = threading.Event()

        def tic():
            compteur.append(1)
            if len(compteur) >= 3:
                assez.set()

        taches.toutes_les(0.05, tic)
        self.assertTrue(assez.wait(3), "la tâche ne s'est pas répétée")

    def test_apres_une_seule_fois(self):
        compteur = []
        taches.apres(0.05, lambda: compteur.append(1))
        time.sleep(0.4)
        self.assertEqual(len(compteur), 1)

    def test_decorateur(self):
        fait = threading.Event()

        @taches.apres(0.05)
        def travail():
            fait.set()

        self.assertTrue(fait.wait(3))

    def test_une_erreur_ne_bloque_pas_les_autres(self):
        fait = threading.Event()
        taches.apres(0.05, lambda: 1 / 0, nom="casse")
        taches.apres(0.1, fait.set, nom="bonne")
        self.assertTrue(fait.wait(3))

    def test_heure_invalide(self):
        with self.assertRaises(ValueError):
            taches.chaque_jour("abc", lambda: None)

    def test_prochaine_heure(self):
        matin = datetime.datetime(2026, 9, 30, 7, 0)
        soir = datetime.datetime(2026, 9, 30, 9, 0)
        meme_jour = datetime.datetime.fromtimestamp(taches._prochaine_heure("08:30", matin))
        lendemain = datetime.datetime.fromtimestamp(taches._prochaine_heure("08:30", soir))
        self.assertEqual(meme_jour, datetime.datetime(2026, 9, 30, 8, 30))
        self.assertEqual(lendemain, datetime.datetime(2026, 10, 1, 8, 30))

    def test_lister_et_annuler(self):
        taches.toutes_les(100, lambda: None, nom="sauvegarde")
        self.assertEqual(len(taches.lister()), 1)
        self.assertIn("sauvegarde", taches.lister()[0])
        self.assertEqual(taches.annuler("sauvegarde"), 1)
        self.assertEqual(taches.lister(), [])

    def test_secondes_negatives(self):
        with self.assertRaises(ValueError):
            taches.toutes_les(0, lambda: None)


if __name__ == "__main__":
    unittest.main()
