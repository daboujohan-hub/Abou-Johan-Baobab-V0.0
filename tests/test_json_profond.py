import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_serveur as serveur

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# Un petit serveur lancé dans un autre processus, avec des fils à pile réduite (comme sur beaucoup de
# téléphones). Si Python plante en lisant le JSON, ce processus-là plante, pas celui des tests.
PROGRAMME = r'''
import http.client, json, sys, threading
sys.path.insert(0, sys.argv[1])
import baobab
import baobab_serveur as serveur
serveur.SILENCIEUX = True
serveur.route("/echo", lambda p, d: {"json": d.json}, methodes=["POST"])
threading.stack_size(262144)
srv = serveur._creer("127.0.0.1", 0)
threading.Thread(target=srv.serve_forever, daemon=True).start()

def envoyer(corps):
    c = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=20)
    c.request("POST", "/echo", body=corps, headers={"Content-Type": "application/json"})
    r = c.getresponse(); d = r.read(); c.close()
    return r.status, json.loads(d)

print(json.dumps([
    envoyer(b"[" * 200000 + b"]" * 200000)[0],
    envoyer(b'{"a": [1, {"b": [2]}]}'),
    envoyer(b"[" * 101 + b"]" * 101)[0],
]))
'''


class TestJsonTropProfond(unittest.TestCase):
    def test_pas_de_plantage_meme_avec_une_petite_pile(self):
        resultat = subprocess.run([sys.executable, "-c", PROGRAMME, RACINE],
                                  capture_output=True, text=True, timeout=120)
        self.assertEqual(resultat.returncode, 0,
                         f"Python a planté (code {resultat.returncode}) : {resultat.stderr[-300:]}")
        trop_profond, normal, juste_trop = json.loads(resultat.stdout)
        self.assertEqual(trop_profond, 400)
        self.assertEqual(normal, [200, {"json": {"a": [1, {"b": [2]}]}}])
        self.assertEqual(juste_trop, 400)      # 101 niveaux : refusé

    def test_mesure_de_la_profondeur(self):
        pas_trop = serveur._json_pas_trop_profond
        self.assertTrue(pas_trop("[" * 100 + "]" * 100))
        self.assertFalse(pas_trop("[" * 101 + "]" * 101))
        self.assertFalse(pas_trop("{" * 101))                         # même sans fermer
        self.assertTrue(pas_trop('{"a": [1, {"b": [2]}]}'))
        self.assertTrue(pas_trop("[1,2]" * 5000))                     # beaucoup d'éléments, peu de niveaux
        self.assertTrue(pas_trop("[[1],[2],[3]]", maximum=2))
        self.assertFalse(pas_trop("[[[1]]]", maximum=2))

    def test_les_textes_ne_comptent_pas(self):
        pas_trop = serveur._json_pas_trop_profond
        self.assertTrue(pas_trop('{"a": "' + "[" * 500 + '"}'))                      # crochets dans un texte
        self.assertTrue(pas_trop('{"a": "\\"' + "[" * 500 + '"}'))                    # guillemet échappé dans un texte
        self.assertFalse(pas_trop('{"a": "ok", "b": ' + "[" * 101 + "]" * 101 + "}"))  # après un texte, ça compte

    def test_json_normal_toujours_accepte(self):
        donnees = {"nom": "Élodie", "liste": [1, 2, {"x": [True, None]}], "texte": "a [b] {c}"}
        self.assertTrue(serveur._json_pas_trop_profond(json.dumps(donnees)))


if __name__ == "__main__":
    unittest.main()
