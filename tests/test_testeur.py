import contextlib
import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_serveur as serveur
import baobab_tests as tests
from baobab import importeur
from baobab.executeur import executer
from baobab.testeur import lancer_tests
from baobab.transpileur import transpiler


def _ecrire(dossier, nom, texte):
    chemin = os.path.join(dossier, nom)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte)
    return chemin


class Nettoyage(unittest.TestCase):
    modules = ()

    def tearDown(self):
        for nom in self.modules:
            sys.modules.pop(nom, None)
        importeur._dossiers.clear()


class TestImporteur(Nettoyage):
    modules = ("mod_outil_xyz",)

    def test_importer_un_fichier_bao(self):
        with tempfile.TemporaryDirectory() as dossier:
            _ecrire(dossier, "mod_outil_xyz.bao", "fonction double(x):\n    retourner x * 2\n")
            importeur.ajouter_dossier(dossier)
            import mod_outil_xyz

            self.assertEqual(mod_outil_xyz.double(4), 8)


class TestModuleTests(unittest.TestCase):
    def test_egal_echoue_avec_message(self):
        with self.assertRaises(AssertionError) as ctx:
            tests.egal(1, 2)
        self.assertIn("Attendu 2 mais obtenu 1", str(ctx.exception))

    def test_egal_reussit(self):
        tests.egal(3, 3)
        tests.contient([1, 2], 2)
        tests.est_vrai(1)
        tests.est_faux(0)
        tests.proche(0.1 + 0.2, 0.3)

    def test_leve_erreur(self):
        tests.leve_erreur(lambda: 1 / 0, ZeroDivisionError)
        with self.assertRaises(AssertionError):
            tests.leve_erreur(lambda: 1, ZeroDivisionError)

    def test_requete_get_et_post(self):
        serveur.route("/ping_test", lambda: "pong")
        serveur.route("/echo_test", lambda p: p)
        reponse = tests.requete("/ping_test")
        self.assertEqual(reponse.code, 200)
        self.assertIn("pong", reponse.texte)
        self.assertEqual(tests.requete("/echo_test", {"a": "1"}).json(), {"a": "1"})
        self.assertEqual(tests.requete("/absente_test").code, 404)


class TestTesteur(Nettoyage):
    modules = ("test_fictif_xyz", "test_propre_xyz")

    def _lancer(self, dossier):
        sortie = io.StringIO()
        with contextlib.redirect_stdout(sortie):
            code = lancer_tests(dossier)
        return code, sortie.getvalue()

    def test_echecs_et_erreurs_en_francais(self):
        with tempfile.TemporaryDirectory() as dossier:
            _ecrire(dossier, "test_fictif_xyz.bao", (
                "importer tests\n\n"
                "fonction test_ok():\n    tests.egal(1 + 1, 2)\n\n"
                "fonction test_echec():\n    tests.egal(1, 2)\n\n"
                "fonction test_erreur():\n    x = 1 / 0\n"
            ))
            code, texte = self._lancer(dossier)
        self.assertEqual(code, 1)
        self.assertIn("✅ test_ok", texte)
        self.assertIn("❌ test_echec", texte)
        self.assertIn("Attendu 2 mais obtenu 1", texte)
        self.assertIn("ligne 7", texte)
        self.assertIn("💥 test_erreur", texte)
        self.assertIn("Division par zéro", texte)

    def test_tout_reussi(self):
        with tempfile.TemporaryDirectory() as dossier:
            _ecrire(dossier, "test_propre_xyz.bao",
                    "importer tests\n\nfonction test_ok():\n    tests.egal(2, 2)\n")
            code, texte = self._lancer(dossier)
        self.assertEqual(code, 0)
        self.assertIn("1 réussi(s)", texte)

    def test_aucun_fichier(self):
        with tempfile.TemporaryDirectory() as dossier:
            code, texte = self._lancer(dossier)
        self.assertEqual(code, 1)
        self.assertIn("Aucun fichier", texte)


class TestExecuteurEtModules(Nettoyage):
    modules = ("casse_xyz",)

    def test_erreur_dans_un_fichier_importe(self):
        with tempfile.TemporaryDirectory() as dossier:
            _ecrire(dossier, "casse_xyz.bao", "x = 1\ny = 1 / 0\n")
            principal = _ecrire(dossier, "principal_xyz.bao", "importer casse_xyz\n")
            erreur = io.StringIO()
            with contextlib.redirect_stderr(erreur):
                code = executer("importer casse_xyz\n", principal)
        self.assertEqual(code, 1)
        self.assertIn("casse_xyz.bao", erreur.getvalue())
        self.assertIn("ligne 2", erreur.getvalue())
        self.assertIn("Division par zéro", erreur.getvalue())


class TestProgrammePrincipal(unittest.TestCase):
    def test_traduction(self):
        self.assertEqual(
            transpiler("si programme_principal:\n    afficher(1)"),
            'if __name__ == "__main__":\n    print(1)',
        )


if __name__ == "__main__":
    unittest.main()
