import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_serveur as serveur
import baobab_tests as tests


class TestNavigateur(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        serveur.SILENCIEUX = True
        serveur._routes.clear()
        serveur.route("/pose", lambda: serveur.repondre("ok", cookies=[serveur.cookie("a", "1")]))
        serveur.route("/efface", lambda: serveur.repondre("ok", cookies=[serveur.cookie("a", "", duree=0)]))
        serveur.route("/lit", lambda p, d: d.cookies)
        serveur.route("/saut", lambda: serveur.rediriger("/lit"))
        serveur.route("/boucle", lambda: serveur.rediriger("/boucle"))
        serveur.route("/ailleurs", lambda: serveur.rediriger("/saut"))

        def compte(p, d):
            d.session["n"] = d.session.get("n", 0) + 1
            return {"n": d.session["n"]}

        serveur.route("/compte", compte)

    @classmethod
    def tearDownClass(cls):
        serveur._routes.clear()
        serveur.SILENCIEUX = False

    def test_garde_les_cookies(self):
        nav = tests.navigateur()
        nav.requete("/pose")
        self.assertEqual(nav.cookies, {"a": "1"})
        self.assertEqual(nav.requete("/lit").json(), {"a": "1"})

    def test_oublie_un_cookie_efface(self):
        nav = tests.navigateur()
        nav.requete("/pose")
        reponse = nav.requete("/efface")
        self.assertEqual(reponse.cookies_effaces, ["a"])
        self.assertEqual(nav.cookies, {})
        self.assertEqual(nav.requete("/lit").json(), {})

    def test_deux_navigateurs_deux_visiteurs(self):
        a, b = tests.navigateur(), tests.navigateur()
        self.assertEqual(a.requete("/compte").json()["n"], 1)
        self.assertEqual(a.requete("/compte").json()["n"], 2)
        self.assertEqual(b.requete("/compte").json()["n"], 1)

    def test_suivre_les_redirections(self):
        nav = tests.navigateur()
        nav.requete("/pose")
        sans = nav.requete("/saut")
        self.assertEqual((sans.code, sans.adresse), (303, "/lit"))
        avec = nav.requete("/saut", suivre=True)
        self.assertEqual((avec.code, avec.json()), (200, {"a": "1"}))
        self.assertEqual(nav.requete("/ailleurs", suivre=True).json(), {"a": "1"})

    def test_une_boucle_de_redirections_s_arrete(self):
        reponse = tests.navigateur().requete("/boucle", suivre=True)
        self.assertEqual(reponse.code, 303)

    def test_cookies_envoyes_a_la_main(self):
        reponse = tests.requete("/lit", cookies={"x": "y", "z": "deux mots"})
        self.assertEqual(reponse.json(), {"x": "y", "z": "deux mots"})

    def test_details_de_la_reponse(self):
        reponse = tests.requete("/pose")
        self.assertEqual(reponse.cookies, {"a": "1"})
        self.assertIn("HttpOnly", reponse.cookies_bruts[0])
        self.assertEqual(reponse.entetes["x-content-type-options"], "nosniff")

    def test_formulaire_avec_le_navigateur(self):
        nav = tests.navigateur()
        reponse = nav.requete("/lit", {})
        self.assertEqual(reponse.code, 200)


if __name__ == "__main__":
    unittest.main()
