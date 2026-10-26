import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_serveur as serveur
import baobab_tests as tests


class TestRequeteJson(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        serveur.SILENCIEUX = True
        serveur._routes.clear()
        serveur._methodes.clear()
        serveur.route("/echo", lambda p, d: {"methode": d.methode, "json": d.json, "type": d.type_contenu,
                                             "auth": d.entetes.get("authorization")},
                      methodes=["GET", "POST", "PUT", "PATCH", "DELETE"])
        serveur.route("/formulaire", lambda p, d: {"methode": d.methode, "parametres": p})

    @classmethod
    def tearDownClass(cls):
        serveur._routes.clear()
        serveur._methodes.clear()
        serveur.SILENCIEUX = False

    def test_envoyer_du_json(self):
        reponse = tests.requete("/echo", json={"nom": "Élodie", "n": [1, 2]})
        donnees = reponse.json()
        self.assertEqual(donnees["methode"], "POST")
        self.assertEqual(donnees["json"], {"nom": "Élodie", "n": [1, 2]})
        self.assertIn("application/json", donnees["type"])

    def test_choisir_la_methode(self):
        for methode in ("PUT", "patch", "DELETE", "GET"):
            self.assertEqual(tests.requete("/echo", methode=methode).json()["methode"], methode.upper())
        self.assertEqual(tests.requete("/echo", json={"a": 1}, methode="PUT").json()["json"], {"a": 1})

    def test_en_tetes_personnalises(self):
        reponse = tests.requete("/echo", json={}, entetes={"Authorization": "Bearer abc"})
        self.assertEqual(reponse.json()["auth"], "Bearer abc")

    def test_formulaire_ou_json_pas_les_deux(self):
        with self.assertRaises(ValueError):
            tests.requete("/echo", {"a": "1"}, json={"b": 2})

    def test_les_formulaires_marchent_toujours(self):
        reponse = tests.requete("/formulaire", {"a": "1"})
        self.assertEqual((reponse.json()["methode"], reponse.json()["parametres"]), ("POST", {"a": "1"}))

    def test_une_route_qui_lit_du_json_refuse_un_formulaire(self):
        self.assertEqual(tests.requete("/echo", {"a": "1"}).code, 415)

    def test_le_navigateur_accepte_json_et_methode(self):
        nav = tests.navigateur()
        reponse = nav.requete("/echo", json={"x": 1}, methode="PATCH")
        self.assertEqual((reponse.code, reponse.json()["methode"]), (200, "PATCH"))

    def test_json_dans_la_reponse_d_erreur(self):
        reponse = tests.requete("/echo", methode="OPTIONS")
        self.assertEqual(reponse.code, 204)
        self.assertIn("PATCH", reponse.entetes["allow"])


if __name__ == "__main__":
    unittest.main()
