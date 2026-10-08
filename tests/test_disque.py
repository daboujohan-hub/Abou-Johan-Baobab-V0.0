import hashlib
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_disque as disque


def _ecrire(dossier, relatif, contenu=b"", age_jours=0):
    chemin = os.path.join(dossier, relatif)
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "wb") as f:
        f.write(contenu)
    if age_jours:
        date = time.time() - age_jours * 86400
        os.utime(chemin, (date, date))
    return chemin


def _photographie(dossier):
    """Empreinte de tout le dossier : sert à prouver que rien n'a changé."""
    h = hashlib.sha256()
    for racine, sous_dossiers, noms in sorted(os.walk(dossier)):
        sous_dossiers.sort()
        for nom in sorted(noms):
            chemin = os.path.join(racine, nom)
            h.update(chemin.encode())
            with open(chemin, "rb") as f:
                h.update(f.read())
            h.update(str(os.path.getmtime(chemin)).encode())
    return h.hexdigest()


class TestDisque(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        d = self.temp.name
        self.d = d
        _ecrire(d, "photos/a.jpg", b"A" * 1000)
        _ecrire(d, "photos/copie_de_a.jpg", b"A" * 1000)
        _ecrire(d, "photos/b.jpg", b"B" * 1000)  # même taille, contenu différent
        _ecrire(d, "notes/vide.txt", b"")
        _ecrire(d, "notes/brouillon.tmp", b"xyz")
        _ecrire(d, "notes/vieux.pdf", b"P" * 5000, age_jours=800)
        _ecrire(d, "musique/chanson.mp3", b"M" * 3000)
        _ecrire(d, "WhatsApp/Media/WhatsApp Images/photo1.jpg", b"1" * 200)
        _ecrire(d, "WhatsApp/Media/WhatsApp Documents/doc.pdf", b"2" * 300)
        _ecrire(d, "Pictures/.thumbnails/mini.jpg", b"3" * 50)
        self.fichiers = disque.scanner(d)

    def tearDown(self):
        self.temp.cleanup()

    def noms(self, liste):
        return sorted(os.path.basename(f.chemin) for f in liste)

    def test_scanner_compte_tout(self):
        self.assertEqual(len(self.fichiers), 10)

    def test_dossier_introuvable(self):
        with self.assertRaises(FileNotFoundError):
            disque.scanner(os.path.join(self.d, "n_existe_pas"))

    def test_resume_par_type(self):
        r = disque.resume(self.fichiers)
        self.assertEqual(r["images"][0], 5)
        self.assertEqual(r["audio"], (1, 3000))

    def test_plus_gros(self):
        self.assertEqual(os.path.basename(disque.plus_gros(self.fichiers, 1)[0].chemin), "vieux.pdf")

    def test_doublons_ignorent_les_faux_amis(self):
        groupes = disque.doublons(self.fichiers)
        self.assertEqual(len(groupes), 1)
        self.assertEqual(self.noms(groupes[0]), ["a.jpg", "copie_de_a.jpg"])
        self.assertEqual(disque.espace_gaspille(groupes), 1000)

    def test_anciens(self):
        self.assertEqual(self.noms(disque.anciens(self.fichiers, 365)), ["vieux.pdf"])

    def test_inutiles_et_raisons(self):
        trouves = {os.path.basename(f.chemin): raison for f, raison in disque.inutiles(self.fichiers)}
        self.assertEqual(sorted(trouves), ["brouillon.tmp", "mini.jpg", "vide.txt"])
        self.assertIn("vide", trouves["vide.txt"])

    def test_discussions_et_images(self):
        chats = disque.discussions(self.fichiers)
        self.assertEqual(self.noms(chats), ["doc.pdf", "photo1.jpg"])
        self.assertEqual(self.noms(disque.images(chats)), ["photo1.jpg"])

    def test_formater_taille(self):
        self.assertEqual(disque.formater_taille(500), "500 o")
        self.assertEqual(disque.formater_taille(1536), "1,5 Ko")
        self.assertEqual(disque.formater_taille(5 * 1024 * 1024), "5,0 Mo")

    def test_rapport_en_francais(self):
        texte = disque.rapport(self.fichiers)
        for morceau in ("10 fichiers", "Doublons : 1 groupe", "Probablement inutiles",
                        "applications de discussion", "Rien n'a été supprimé"):
            self.assertIn(morceau, texte)

    def test_lecture_seule(self):
        avant = _photographie(self.d)
        disque.rapport(disque.scanner(self.d))
        self.assertEqual(_photographie(self.d), avant)


if __name__ == "__main__":
    unittest.main()
