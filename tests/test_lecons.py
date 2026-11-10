import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _charger():
    spec = importlib.util.spec_from_file_location("lecons_app", os.path.join(RACINE, "app", "lecons.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.LECONS


def _lancer(code):
    with tempfile.TemporaryDirectory() as dossier:
        chemin = os.path.join(dossier, "programme.bao")
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(code)
        env = dict(os.environ)
        env["PYTHONPATH"] = RACINE + os.pathsep + env.get("PYTHONPATH", "")
        r = subprocess.run([sys.executable, "-m", "baobab", "lancer", chemin],
                           capture_output=True, text=True, timeout=30, cwd=dossier, env=env)
        return r.returncode, r.stdout + r.stderr


def _norm(texte):
    return "\n".join(l.rstrip() for l in texte.replace("\r", "").split("\n")).strip()


LECONS = _charger()
ACTIVES = [l for l in LECONS if not l.get("bientot")]


class TestLecons(unittest.TestCase):
    def test_identifiants_uniques(self):
        ids = [l["id"] for l in LECONS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_champs_obligatoires(self):
        for l in ACTIVES:
            for champ in ("titre", "niveau", "explication", "exemple", "consigne",
                          "depart", "attendu", "solution", "indice"):
                self.assertTrue(l.get(champ), (l["id"], champ))

    def test_les_exemples_s_executent(self):
        for l in ACTIVES:
            code, sortie = _lancer(l["exemple"])
            self.assertEqual(code, 0, (l["id"], sortie))

    def test_les_solutions_donnent_l_attendu(self):
        for l in ACTIVES:
            code, sortie = _lancer(l["solution"])
            self.assertEqual(_norm(sortie), _norm(l["attendu"]), l["id"])
            for morceau in l.get("exige", []):
                self.assertIn(morceau, l["solution"], l["id"])

    def test_le_depart_ne_reussit_pas_deja(self):
        for l in ACTIVES:
            _, sortie = _lancer(l["depart"])
            self.assertNotEqual(_norm(sortie), _norm(l["attendu"]), l["id"])


if __name__ == "__main__":
    unittest.main()
