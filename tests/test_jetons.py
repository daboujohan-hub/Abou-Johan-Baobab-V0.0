import http.client
import json
import os
import sys
import threading
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_securite as securite
import baobab_serveur as serveur

CLE = "une-cle-secrete-assez-longue"


class TestJetonsDAcces(unittest.TestCase):
    def test_aller_retour(self):
        jeton = securite.creer_jeton_acces("Élodie", CLE, 60, ["lecture", "ecriture"])
        self.assertEqual(securite.verifier_jeton_acces(jeton, CLE),
                         {"identite": "Élodie", "droits": ["ecriture", "lecture"]})

    def test_droits_uniques_et_ranges(self):
        jeton = securite.creer_jeton_acces("awa", CLE, 60, ["b", "a", "b"])
        self.assertEqual(securite.verifier_jeton_acces(jeton, CLE)["droits"], ["a", "b"])

    def test_sans_droits(self):
        jeton = securite.creer_jeton_acces("awa", CLE)
        self.assertEqual(securite.verifier_jeton_acces(jeton, CLE), {"identite": "awa", "droits": []})

    def test_la_duree_est_obligatoire(self):
        for duree in (0, None, -5):
            with self.assertRaises(ValueError, msg=str(duree)):
                securite.creer_jeton_acces("awa", CLE, duree)

    def test_jeton_perime(self):
        with mock.patch.object(securite, "time", mock.Mock(time=lambda: 1000)):
            jeton = securite.creer_jeton_acces("awa", CLE, 60)
            self.assertIsNotNone(securite.verifier_jeton_acces(jeton, CLE))
        self.assertIsNone(securite.verifier_jeton_acces(jeton, CLE))  # maintenant : bien plus tard

    def test_jeton_modifie_ou_faux(self):
        jeton = securite.creer_jeton_acces("awa", CLE, 60, ["lecture"])
        corps, expiration, signature = jeton.split(".")
        autre = securite.creer_jeton_acces("awa", CLE, 60, ["lecture", "admin"]).split(".")[0]
        for mauvais in (jeton[:-1] + ("0" if jeton[-1] != "0" else "1"),
                        f"{autre}.{expiration}.{signature}", "", "abc", None, "a.b.c"):
            self.assertIsNone(securite.verifier_jeton_acces(mauvais, CLE), mauvais)

    def test_autre_cle(self):
        jeton = securite.creer_jeton_acces("awa", CLE, 60)
        self.assertIsNone(securite.verifier_jeton_acces(jeton, "une-autre-cle-tout-aussi-longue"))

    def test_une_signature_ordinaire_n_est_pas_un_jeton(self):
        # un texte signé avec la même clé, mais qui n'a pas la forme d'un jeton
        for texte in ("abc", "[1, 2]", '{"x": 1}', '{"i": 5}', '{"i": "awa", "d": "tout"}'):
            self.assertIsNone(securite.verifier_jeton_acces(securite.signer(texte, CLE, 60), CLE), texte)


class TestJetonsSurLeServeur(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        serveur.SILENCIEUX = True
        serveur._routes.clear()
        serveur._methodes.clear()
        serveur.route("/prive", lambda p, d: serveur.exiger_jeton(d, CLE))
        serveur.route("/ecriture", lambda p, d: serveur.exiger_jeton(d, CLE, "ecriture"))
        serveur.route("/jeton_lu", lambda p, d: {"jeton": d.jeton})
        cls.serveur = serveur._creer("127.0.0.1", 0)
        cls.port = cls.serveur.server_address[1]
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()
        serveur._routes.clear()
        serveur._methodes.clear()
        serveur.SILENCIEUX = False

    def demander(self, chemin, jeton=None, entete="Authorization", prefixe="Bearer "):
        connexion = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            entetes = {entete: prefixe + jeton} if jeton is not None else {}
            connexion.request("GET", chemin, headers=entetes)
            reponse = connexion.getresponse()
            return reponse.status, reponse.getheader("WWW-Authenticate"), json.loads(reponse.read())
        finally:
            connexion.close()

    def test_sans_jeton(self):
        code, entete, corps = self.demander("/prive")
        self.assertEqual(code, 401)
        self.assertEqual(entete, "Bearer")
        self.assertIn("manquant", corps["erreur"])

    def test_jeton_valide(self):
        jeton = securite.creer_jeton_acces("awa", CLE, 60, ["lecture"])
        code, _, corps = self.demander("/prive", jeton)
        self.assertEqual((code, corps), (200, {"identite": "awa", "droits": ["lecture"]}))

    def test_jeton_invalide_ou_perime(self):
        valide = securite.creer_jeton_acces("awa", CLE, 60)
        with mock.patch.object(securite, "time", mock.Mock(time=lambda: 1000)):
            perime = securite.creer_jeton_acces("awa", CLE, 60)
        autre_cle = securite.creer_jeton_acces("awa", "une-autre-cle-tout-aussi-longue", 60)
        for mauvais in (valide + "x", perime, autre_cle, "n-importe-quoi"):
            code, entete, _ = self.demander("/prive", mauvais)
            self.assertEqual(code, 401, mauvais)
            self.assertIn("invalid_token", entete)

    def test_droit_manquant_puis_present(self):
        lecteur = securite.creer_jeton_acces("awa", CLE, 60, ["lecture"])
        self.assertEqual(self.demander("/ecriture", lecteur)[0], 403)
        redacteur = securite.creer_jeton_acces("awa", CLE, 60, ["lecture", "ecriture"])
        self.assertEqual(self.demander("/ecriture", redacteur)[0], 200)

    def test_lecture_de_l_entete(self):
        for jeton, prefixe in (("abc", "Bearer "), ("abc", "bearer "), ("abc", "BEARER   ")):
            self.assertEqual(self.demander("/jeton_lu", jeton, prefixe=prefixe)[2], {"jeton": "abc"})
        for prefixe, jeton in (("Basic ", "xyz"), ("Bearer", ""), ("", "abc")):
            self.assertEqual(self.demander("/jeton_lu", jeton, prefixe=prefixe)[2], {"jeton": None},
                             (prefixe, jeton))
        self.assertEqual(self.demander("/jeton_lu")[2], {"jeton": None})


if __name__ == "__main__":
    unittest.main()
