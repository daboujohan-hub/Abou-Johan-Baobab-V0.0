import os
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_base as base

TABLE = "CREATE TABLE notes (id INTEGER PRIMARY KEY AUTOINCREMENT, texte TEXT)"


class TestBase(unittest.TestCase):
    def setUp(self):
        self.c = base.ouvrir(":memory:")
        base.executer(self.c, TABLE)

    def tearDown(self):
        base.fermer(self.c)

    def test_tables(self):
        self.assertEqual(base.tables(self.c), ["notes"])

    def test_inserer_et_chercher(self):
        identifiant = base.inserer(self.c, "notes", {"texte": "Bonjour"})
        self.assertEqual(identifiant, 1)
        self.assertEqual(base.chercher(self.c, "SELECT * FROM notes"),
                         [{"id": 1, "texte": "Bonjour"}])

    def test_valeurs_avec_points_d_interrogation(self):
        base.inserer(self.c, "notes", {"texte": "a"})
        base.inserer(self.c, "notes", {"texte": "b"})
        touchees = base.executer(self.c, "UPDATE notes SET texte = ? WHERE id = ?", ["z", 2])
        self.assertEqual(touchees, 1)
        lignes = base.chercher(self.c, "SELECT texte FROM notes WHERE id = ?", [2])
        self.assertEqual(lignes, [{"texte": "z"}])

    def test_injection_sql_dans_les_valeurs(self):
        piege = "x'); DROP TABLE notes; --"
        base.inserer(self.c, "notes", {"texte": piege})
        self.assertEqual(base.tables(self.c), ["notes"])
        self.assertEqual(base.chercher(self.c, "SELECT texte FROM notes")[0]["texte"], piege)

    def test_noms_de_table_et_de_colonne_surs(self):
        with self.assertRaises(ValueError):
            base.inserer(self.c, "notes; DROP TABLE notes", {"texte": "a"})
        with self.assertRaises(ValueError):
            base.inserer(self.c, "notes", {"texte) VALUES ('x'); --": "a"})
        self.assertEqual(base.tables(self.c), ["notes"])

    def test_rien_a_inserer(self):
        with self.assertRaises(ValueError):
            base.inserer(self.c, "notes", {})

    def test_select_sans_resultat(self):
        self.assertEqual(base.chercher(self.c, "SELECT * FROM notes"), [])

    def test_utilisable_depuis_un_autre_fil(self):
        # comme dans un serveur : la connexion est créée dans un fil et utilisée dans un autre
        resultat = []

        def travail():
            base.inserer(self.c, "notes", {"texte": "depuis un autre fil"})
            resultat.append(len(base.chercher(self.c, "SELECT * FROM notes")))

        fil = threading.Thread(target=travail)
        fil.start()
        fil.join()
        self.assertEqual(resultat, [1])

    def test_donnees_gardees_dans_un_fichier(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "test.db")
            c = base.ouvrir(chemin)
            base.executer(c, TABLE)
            base.inserer(c, "notes", {"texte": "persistant"})
            base.fermer(c)
            c = base.ouvrir(chemin)
            self.assertEqual(base.chercher(c, "SELECT texte FROM notes"), [{"texte": "persistant"}])
            base.fermer(c)


if __name__ == "__main__":
    unittest.main()
