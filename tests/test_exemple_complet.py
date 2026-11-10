import os
import subprocess
import sys
import unittest

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestExempleComplet(unittest.TestCase):
    def test_tout_passe_avec_le_vrai_interpreteur(self):
        env = dict(os.environ)
        env["PYTHONPATH"] = RACINE + os.pathsep + env.get("PYTHONPATH", "")
        r = subprocess.run(
            [sys.executable, "-m", "baobab", "lancer", os.path.join(RACINE, "app", "exemple_complet.bao")],
            capture_output=True, text=True, timeout=30, cwd=RACINE, env=env)
        sortie = r.stdout + r.stderr
        self.assertEqual(r.returncode, 0, sortie)
        self.assertNotIn("❌", sortie)
        self.assertEqual(sortie.count("✅"), 11, sortie)


if __name__ == "__main__":
    unittest.main()
