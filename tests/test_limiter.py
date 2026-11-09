import http.client
import json
import os
import sys
import threading
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_serveur as serveur


class Horloge:
    """Une horloge qu'on avance à la main."""

    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def visiteur(ip="1.1.1.1"):
    return SimpleNamespace(adresse_ip=ip)


class TestLimiter(unittest.TestCase):
    def setUp(self):
        serveur._limites.clear()
        self.horloge = Horloge()
        patch = mock.patch.object(serveur, "_maintenant", self.horloge)
        patch.start()
        self.addCleanup(patch.stop)

    def test_le_reste_diminue_puis_la_limite_tombe(self):
        v = visiteur()
        self.assertEqual([serveur.limiter(v, "x", 3, 60) for _ in range(3)], [2, 1, 0])
        with self.assertRaises(serveur.ErreurHTTP) as ctx:
            serveur.limiter(v, "x", 3, 60)
        self.assertEqual(ctx.exception.code, 429)
        self.assertIn("réessaie", ctx.exception.message)

    def test_retry_after(self):
        v = visiteur()
        for _ in range(2):
            serveur.limiter(v, "x", 2, 60)
        self.horloge.t += 20.5
        with self.assertRaises(serveur.ErreurHTTP) as ctx:
            serveur.limiter(v, "x", 2, 60)
        self.assertEqual(ctx.exception.entetes["Retry-After"], "40")  # 60 - 20,5 arrondi vers le haut

    def test_fenetre_glissante(self):
        v = visiteur()
        serveur.limiter(v, "x", 2, 60)               # à 1000
        self.horloge.t += 30
        serveur.limiter(v, "x", 2, 60)               # à 1030
        with self.assertRaises(serveur.ErreurHTTP):
            serveur.limiter(v, "x", 2, 60)
        self.horloge.t += 31                          # 1061 : la première demande est sortie de la fenêtre
        self.assertEqual(serveur.limiter(v, "x", 2, 60), 0)
        with self.assertRaises(serveur.ErreurHTTP):
            serveur.limiter(v, "x", 2, 60)
        self.horloge.t += 60
        self.assertEqual(serveur.limiter(v, "x", 2, 60), 1)

    def test_une_demande_refusee_ne_prolonge_pas_l_attente(self):
        v = visiteur()
        serveur.limiter(v, "x", 1, 60)
        for _ in range(5):
            self.horloge.t += 10
            with self.assertRaises(serveur.ErreurHTTP):
                serveur.limiter(v, "x", 1, 60)
        self.horloge.t += 10                          # 60 secondes après la seule demande acceptée
        self.assertEqual(serveur.limiter(v, "x", 1, 60), 0)

    def test_visiteurs_et_noms_independants(self):
        serveur.limiter(visiteur("1.1.1.1"), "x", 1, 60)
        serveur.limiter(visiteur("2.2.2.2"), "x", 1, 60)
        serveur.limiter(visiteur("1.1.1.1"), "autre", 1, 60)
        with self.assertRaises(serveur.ErreurHTTP):
            serveur.limiter(visiteur("1.1.1.1"), "x", 1, 60)

    def test_la_cle_remplace_l_adresse(self):
        serveur.limiter(visiteur("1.1.1.1"), "connexion", 1, 60, cle="awa")
        serveur.limiter(visiteur("1.1.1.1"), "connexion", 1, 60, cle="bob")      # même IP, autre clé
        with self.assertRaises(serveur.ErreurHTTP):
            serveur.limiter(visiteur("9.9.9.9"), "connexion", 1, 60, cle="awa")  # autre IP, même clé

    def test_parametres_invalides(self):
        v = visiteur()
        for arguments in (("", 1, 60), (None, 1, 60), ("x", 0, 60), ("x", True, 60), ("x", 1.5, 60),
                          ("x", 1, 0), ("x", 1, -5), ("x", 1, True), ("x", 1, "60")):
            with self.assertRaises(ValueError, msg=str(arguments)):
                serveur.limiter(v, *arguments)

    def test_la_memoire_reste_bornee(self):
        with mock.patch.object(serveur, "LIMITES_MAX", 5):
            for i in range(20):
                self.horloge.t += 1
                serveur.limiter(visiteur(f"10.0.0.{i}"), "x", 5, 1000)
            self.assertLessEqual(len(serveur._limites), 5)
            self.horloge.t += 5000  # tout est périmé : la purge vide ce qui ne sert plus
            for i in range(6):
                serveur.limiter(visiteur(f"10.1.0.{i}"), "x", 5, 1000)
            self.assertLessEqual(len(serveur._limites), 6)

    def test_plusieurs_fils_en_meme_temps(self):
        v, acceptes, refuses = visiteur(), [], []

        def appeler():
            try:
                serveur.limiter(v, "x", 20, 60)
                acceptes.append(1)
            except serveur.ErreurHTTP:
                refuses.append(1)

        fils = [threading.Thread(target=appeler) for _ in range(80)]
        for fil in fils:
            fil.start()
        for fil in fils:
            fil.join()
        self.assertEqual((len(acceptes), len(refuses)), (20, 60))


class TestLimiterSurLeServeur(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        serveur.SILENCIEUX = True
        serveur._routes.clear()
        serveur._methodes.clear()
        serveur._limites.clear()

        def commentaire(parametres, demande):
            reste = serveur.limiter(demande, "commentaire", 2, 60)
            return {"reste": reste}

        serveur.route("/commentaire", commentaire)
        cls.serveur = serveur._creer("127.0.0.1", 0)
        cls.port = cls.serveur.server_address[1]
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()
        serveur._routes.clear()
        serveur._methodes.clear()
        serveur._limites.clear()
        serveur.SILENCIEUX = False

    def test_code_429_et_retry_after(self):
        reponses = []
        for _ in range(3):
            c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
            c.request("GET", "/commentaire")
            r = c.getresponse()
            reponses.append((r.status, r.getheader("Retry-After"), json.loads(r.read())))
            c.close()
        self.assertEqual([r[0] for r in reponses], [200, 200, 429])
        self.assertEqual(reponses[0][2], {"reste": 1})
        self.assertGreaterEqual(int(reponses[2][1]), 1)
        self.assertIn("Trop de demandes", reponses[2][2]["erreur"])


if __name__ == "__main__":
    unittest.main()
