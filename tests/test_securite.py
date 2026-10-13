import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_securite as securite
from baobab.transpileur import transpiler


class TestMotsDePasse(unittest.TestCase):
    def setUp(self):
        # peu d'itérations : les tests restent rapides (la vraie valeur est 600 000)
        patch = mock.patch.object(securite, "ITERATIONS", 1000)
        patch.start()
        self.addCleanup(patch.stop)

    def test_aller_retour(self):
        empreinte = securite.hacher_mot_de_passe("mon mot de passe")
        self.assertTrue(securite.verifier_mot_de_passe("mon mot de passe", empreinte))
        self.assertFalse(securite.verifier_mot_de_passe("autre chose", empreinte))

    def test_l_empreinte_ne_contient_pas_le_mot_de_passe(self):
        empreinte = securite.hacher_mot_de_passe("secret-unique-123")
        self.assertNotIn("secret-unique-123", empreinte)
        self.assertTrue(empreinte.startswith("pbkdf2_sha256$1000$"))

    def test_deux_empreintes_differentes_pour_le_meme_mot_de_passe(self):
        a = securite.hacher_mot_de_passe("identique")
        b = securite.hacher_mot_de_passe("identique")
        self.assertNotEqual(a, b)
        self.assertTrue(securite.verifier_mot_de_passe("identique", a))
        self.assertTrue(securite.verifier_mot_de_passe("identique", b))

    def test_accents_ecrits_de_deux_facons(self):
        empreinte = securite.hacher_mot_de_passe("é")           # un seul caractère
        self.assertTrue(securite.verifier_mot_de_passe("e\u0301", empreinte))  # e + accent

    def test_une_ancienne_empreinte_reste_valable(self):
        ancienne = securite.hacher_mot_de_passe("abc")
        with mock.patch.object(securite, "ITERATIONS", 2000):
            self.assertTrue(securite.verifier_mot_de_passe("abc", ancienne))

    def test_mots_de_passe_refuses(self):
        with self.assertRaises(ValueError):
            securite.hacher_mot_de_passe("")
        with self.assertRaises(ValueError):
            securite.hacher_mot_de_passe("x" * 2000)
        with self.assertRaises(TypeError):
            securite.hacher_mot_de_passe(12345)

    def test_verifier_ne_plante_jamais(self):
        empreinte = securite.hacher_mot_de_passe("abc")
        for mauvais in ("", "abc", "a$b$c$d", None, 12, "pbkdf2_sha256$x$zz$yy",
                        "pbkdf2_sha256$99999999999$00$00", "autre$1000$00$00"):
            self.assertFalse(securite.verifier_mot_de_passe("abc", mauvais), mauvais)
        self.assertFalse(securite.verifier_mot_de_passe("", empreinte))
        self.assertFalse(securite.verifier_mot_de_passe(None, empreinte))

    def test_empreinte_modifiee_refusee(self):
        empreinte = securite.hacher_mot_de_passe("abc")
        modifiee = empreinte[:-1] + ("0" if empreinte[-1] != "0" else "1")
        self.assertFalse(securite.verifier_mot_de_passe("abc", modifiee))


class TestJetons(unittest.TestCase):
    def test_jetons_differents_et_assez_longs(self):
        a, b = securite.jeton_aleatoire(), securite.jeton_aleatoire()
        self.assertNotEqual(a, b)
        self.assertGreaterEqual(len(a), 40)

    def test_jeton_trop_court(self):
        with self.assertRaises(ValueError):
            securite.jeton_aleatoire(8)


CLE = "une-cle-secrete-assez-longue"


class TestSignatures(unittest.TestCase):
    def test_aller_retour_avec_accents(self):
        signe = securite.signer("Élodie a 3 ans", CLE)
        self.assertEqual(securite.verifier_signature(signe, CLE), "Élodie a 3 ans")

    def test_les_nombres_reviennent_en_texte(self):
        self.assertEqual(securite.verifier_signature(securite.signer(42, CLE), CLE), "42")

    def test_valeur_modifiee(self):
        corps, expiration, signature = securite.signer("awa", CLE).split(".")
        autre = securite.signer("koffi", CLE).split(".")[0]
        self.assertIsNone(securite.verifier_signature(f"{autre}.{expiration}.{signature}", CLE))

    def test_signature_modifiee_ou_invalide(self):
        signe = securite.signer("awa", CLE)
        for mauvais in (signe[:-1] + ("0" if signe[-1] != "0" else "1"), "", "a.b", "a.b.c.d",
                        None, "é.0.é"):
            self.assertIsNone(securite.verifier_signature(mauvais, CLE), mauvais)

    def test_autre_cle(self):
        signe = securite.signer("awa", CLE)
        self.assertIsNone(securite.verifier_signature(signe, "une-autre-cle-tout-aussi-longue"))

    def test_expiration(self):
        with mock.patch.object(securite, "time", mock.Mock(time=lambda: 1000)):
            signe = securite.signer("awa", CLE, duree=60)
        with mock.patch.object(securite, "time", mock.Mock(time=lambda: 1030)):
            self.assertEqual(securite.verifier_signature(signe, CLE), "awa")
        with mock.patch.object(securite, "time", mock.Mock(time=lambda: 1100)):
            self.assertIsNone(securite.verifier_signature(signe, CLE))

    def test_l_expiration_ne_peut_pas_etre_prolongee(self):
        with mock.patch.object(securite, "time", mock.Mock(time=lambda: 1000)):
            signe = securite.signer("awa", CLE, duree=60)
        corps, expiration, signature = signe.split(".")
        triche = f"{corps}.9999999999.{signature}"
        with mock.patch.object(securite, "time", mock.Mock(time=lambda: 1100)):
            self.assertIsNone(securite.verifier_signature(triche, CLE))

    def test_cle_trop_courte(self):
        with self.assertRaises(ValueError):
            securite.signer("awa", "court")
        with self.assertRaises(ValueError):
            securite.verifier_signature("a.0.b", "court")

    def test_cle_en_octets(self):
        signe = securite.signer("awa", CLE.encode())
        self.assertEqual(securite.verifier_signature(signe, CLE), "awa")


class TestDansBaobab(unittest.TestCase):
    def test_noms_gardes(self):
        self.assertEqual(
            transpiler("importer securite\nsecurite.hacher_mot_de_passe(m)"),
            "import baobab_securite\nbaobab_securite.hacher_mot_de_passe(m)",
        )
        self.assertEqual(
            transpiler("importer sécurité\nsécurité.jeton_aleatoire()"),
            "import baobab_securite\nbaobab_securite.jeton_aleatoire()",
        )


if __name__ == "__main__":
    unittest.main()
