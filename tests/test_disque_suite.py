import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_disque as disque


def _ecrire(dossier, relatif, contenu=b""):
    chemin = os.path.join(dossier, relatif)
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "wb") as f:
        f.write(contenu)
    return chemin


class TestDisqueSuite(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        d = self.temp.name
        _ecrire(d, "Download/appli_installee.apk", b"A" * 5000)
        _ecrire(d, "Download/petite.apk", b"B" * 100)
        _ecrire(d, "Android/media/com.whatsapp/WhatsApp/.Shared/x.enc.tmp", b"T" * 800)
        _ecrire(d, "Android/media/com.whatsapp/WhatsApp/Media/Images/IMG-20261008-WA0001.jpg", b"1" * 300)
        _ecrire(d, "Android/media/com.whatsapp/WhatsApp/Media/Images/IMG-20261009-WA0002.jpg", b"2" * 400)
        _ecrire(d, "Telegram/Telegram Images/photo.jpg", b"3" * 200)
        _ecrire(d, "Download/vide.lock", b"")
        self.fichiers = disque.scanner(d)

    def tearDown(self):
        self.temp.cleanup()

    def noms(self, liste):
        return [os.path.basename(f.chemin) for f in liste]

    def test_inutiles_les_plus_lourds_d_abord(self):
        noms = [os.path.basename(f.chemin) for f, _ in disque.inutiles(self.fichiers)]
        self.assertEqual(noms, ["x.enc.tmp", "vide.lock"])

    def test_inutiles_par_raison(self):
        raisons = disque.inutiles_par_raison(self.fichiers)
        self.assertEqual(raisons["fichier vide"], (1, 0))
        self.assertEqual(raisons["fichier temporaire ou copie (.tmp)"], (1, 800))

    def test_dossiers_des_applications(self):
        par_nom = {os.path.basename(f.chemin): disque.appartient_a_une_application(f)
                   for f in self.fichiers}
        self.assertTrue(par_nom["x.enc.tmp"])
        self.assertFalse(par_nom["appli_installee.apk"])

    def test_installateurs(self):
        self.assertEqual(self.noms(disque.installateurs(self.fichiers)),
                         ["appli_installee.apk", "petite.apk"])

    def test_par_application(self):
        r = disque.par_application(self.fichiers)
        self.assertEqual(r["whatsapp"], (3, 1500, 2))
        self.assertEqual(r["telegram"], (1, 200, 1))

    def test_contenant(self):
        images = disque.images(disque.discussions(self.fichiers))
        self.assertEqual(self.noms(disque.contenant(images, "20261008")), ["IMG-20261008-WA0001.jpg"])

    def test_rapport_avertit_pour_les_dossiers_d_applications(self):
        texte = disque.rapport(self.fichiers)
        self.assertIn("Installateurs d'applications", texte)
        self.assertIn("Ne les supprime pas à la main", texte)
        self.assertIn("whatsapp : 3 fichiers", texte)


if __name__ == "__main__":
    unittest.main()
