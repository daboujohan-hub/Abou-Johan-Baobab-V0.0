import http.client
import json
import os
import re
import struct
import sys
import tempfile
import threading
import unittest
import zlib
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import baobab  # enregistre les modules
import baobab_serveur as serveur

SIGNATURE = b"\x89PNG\r\n\x1a\n"


def decoder_png(octets):
    """Lit un PNG (en vérifiant les contrôles CRC). Retourne (largeur, hauteur, lignes de pixels RVB)."""
    assert octets[:8] == SIGNATURE
    position, donnees_image, largeur, hauteur = 8, b"", None, None
    while position < len(octets):
        longueur = struct.unpack(">I", octets[position:position + 4])[0]
        genre = octets[position + 4:position + 8]
        donnees = octets[position + 8:position + 8 + longueur]
        crc = struct.unpack(">I", octets[position + 8 + longueur:position + 12 + longueur])[0]
        assert zlib.crc32(genre + donnees) & 0xFFFFFFFF == crc, f"CRC faux pour {genre}"
        if genre == b"IHDR":
            largeur, hauteur, profondeur, type_couleur = struct.unpack(">IIBB", donnees[:10])
            assert (profondeur, type_couleur) == (8, 2)
        elif genre == b"IDAT":
            donnees_image += donnees
        position += 12 + longueur
    brut = zlib.decompress(donnees_image)
    taille_ligne = 1 + 3 * largeur
    assert len(brut) == taille_ligne * hauteur
    lignes = []
    for y in range(hauteur):
        ligne = brut[y * taille_ligne:(y + 1) * taille_ligne]
        assert ligne[0] == 0
        lignes.append(ligne[1:])
    return largeur, hauteur, lignes


def pixel(lignes, x, y):
    return tuple(lignes[y][3 * x:3 * x + 3])


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        serveur.SILENCIEUX = True
        cls.serveur = serveur._creer("127.0.0.1", 0)
        cls.port = cls.serveur.server_address[1]
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()
        serveur._pwa.clear()
        serveur._routes.clear()
        serveur._methodes.clear()
        serveur.SILENCIEUX = False

    def setUp(self):
        serveur._routes.clear()
        serveur._methodes.clear()
        serveur._pwa.clear()

    def tearDown(self):
        serveur._pwa.clear()

    def demander(self, chemin, methode="GET"):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            c.request(methode, chemin, body=b"" if methode == "POST" else None)
            r = c.getresponse()
            return r.status, r, r.read()
        finally:
            c.close()


class TestActivation(Base):
    def test_rien_tant_que_ce_n_est_pas_active(self):
        self.assertNotIn("manifest", serveur.page("T", "x"))
        self.assertEqual(self.demander("/manifest.webmanifest")[0], 404)
        self.assertEqual(self.demander("/sw.js")[0], 404)

    def test_les_pages_recoivent_les_balises(self):
        serveur.application_installable("Mes notes", couleur="#1b5e20")
        html = serveur.page("T", "<p>x</p>")
        for attendu in ("<link rel='manifest' href='/manifest.webmanifest'>",
                        "<meta name='theme-color' content='#1b5e20'>",
                        "<link rel='apple-touch-icon' href='/icone-192.png'>",
                        "<script src='/pwa.js' defer></script>"):
            self.assertIn(attendu, html)
        self.assertTrue(html.index("</head>") > html.index("manifest"))

    def test_les_six_adresses_en_lecture_seule(self):
        serveur.application_installable("Mes notes")
        for chemin in ("/manifest.webmanifest", "/sw.js", "/pwa.js", "/icone-192.png",
                       "/icone-512.png", "/hors-ligne"):
            self.assertEqual(self.demander(chemin)[0], 200, chemin)
            self.assertEqual(self.demander(chemin, "POST")[0], 405, chemin)

    def test_reactiver_remplace_la_configuration(self):
        serveur.application_installable("Premier", couleur="#111111")
        serveur.application_installable("Second", couleur="#222222")
        manifeste = json.loads(self.demander("/manifest.webmanifest")[2])
        self.assertEqual((manifeste["name"], manifeste["theme_color"]), ("Second", "#222222"))
        self.assertIn("#222222", serveur.page("T", "x"))


class TestManifeste(Base):
    def test_contenu(self):
        serveur.application_installable("Mes notes", couleur="#1b5e20", fond="#eeeeee",
                                        description="Prendre des notes", page_d_accueil="/accueil")
        code, reponse, corps = self.demander("/manifest.webmanifest")
        self.assertEqual(code, 200)
        self.assertEqual(reponse.getheader("Content-Type"), "application/manifest+json")
        self.assertEqual(reponse.getheader("Cache-Control"), "no-cache")
        m = json.loads(corps)
        self.assertEqual((m["name"], m["short_name"], m["start_url"], m["scope"], m["display"], m["lang"]),
                         ("Mes notes", "Mes notes", "/accueil", "/", "standalone", "fr"))
        self.assertEqual((m["theme_color"], m["background_color"], m["description"]),
                         ("#1b5e20", "#eeeeee", "Prendre des notes"))
        self.assertEqual({(i["src"], i["sizes"], i["type"]) for i in m["icons"]},
                         {("/icone-192.png", "192x192", "image/png"), ("/icone-512.png", "512x512", "image/png")})

    def test_nom_court_par_defaut_et_choisi(self):
        serveur.application_installable("Un nom vraiment très long")
        self.assertEqual(json.loads(self.demander("/manifest.webmanifest")[2])["short_name"], "Un nom vraim")
        serveur.application_installable("Un nom vraiment très long", nom_court="Notes")
        self.assertEqual(json.loads(self.demander("/manifest.webmanifest")[2])["short_name"], "Notes")

    def test_caracteres_speciaux(self):
        serveur.application_installable('L\'app "spéciale" <b>& co</b>')
        manifeste = json.loads(self.demander("/manifest.webmanifest")[2])
        self.assertEqual(manifeste["name"], 'L\'app "spéciale" <b>& co</b>')


class TestServiceWorker(Base):
    def test_fichiers_javascript(self):
        serveur.application_installable("Mes notes")
        code, reponse, corps = self.demander("/sw.js")
        self.assertEqual(reponse.getheader("Content-Type"), "application/javascript; charset=utf-8")
        self.assertEqual(reponse.getheader("Cache-Control"), "no-cache")
        texte = corps.decode("utf-8")
        self.assertRegex(texte, r'const VERSION = "baobab-[0-9a-f]{8}";')
        self.assertIn('"/hors-ligne"', texte)
        self.assertIn('e.request.mode === "navigate"', texte)
        self.assertNotIn("cache.put", texte)  # aucune réponse du site n'est gardée
        enregistrement = self.demander("/pwa.js")[2].decode("utf-8")
        self.assertIn("serviceWorker.register('/sw.js')", enregistrement)

    def test_la_version_change_avec_la_configuration(self):
        versions = set()
        for nom, couleur in (("A", "#111111"), ("B", "#111111"), ("A", "#222222"), ("A", "#111111")):
            serveur.application_installable(nom, couleur=couleur)
            versions.add(re.search(r'baobab-([0-9a-f]{8})', self.demander("/sw.js")[2].decode()).group(1))
        self.assertEqual(len(versions), 3)

    def test_page_hors_ligne(self):
        serveur.application_installable("<i>Mes</i> notes", page_d_accueil="/accueil")
        html = self.demander("/hors-ligne")[2].decode("utf-8")
        self.assertIn("&lt;i&gt;Mes&lt;/i&gt; notes", html)
        self.assertNotIn("<i>Mes</i>", html)
        self.assertIn("href='/accueil'", html)
        self.assertIn("manifest", html)


class TestIcones(Base):
    def test_icones_par_defaut(self):
        serveur.application_installable("Mes notes", couleur="#1b5e20")
        for taille in (192, 512):
            code, reponse, corps = self.demander(f"/icone-{taille}.png")
            self.assertEqual(reponse.getheader("Content-Type"), "image/png")
            self.assertIn("max-age", reponse.getheader("Cache-Control"))
            largeur, hauteur, lignes = decoder_png(corps)
            self.assertEqual((largeur, hauteur), (taille, taille))
            fond = (0x1b, 0x5e, 0x20)
            self.assertEqual(pixel(lignes, 0, 0), fond)
            self.assertEqual(pixel(lignes, taille - 1, taille - 1), fond)
            self.assertEqual(pixel(lignes, taille // 2, int(0.36 * taille)), (255, 255, 255))   # houppier
            self.assertEqual(pixel(lignes, taille // 2, int(0.70 * taille)), (255, 255, 255))   # tronc
            self.assertEqual(pixel(lignes, int(0.1 * taille), int(0.7 * taille)), fond)         # à côté du tronc
            self.assertEqual(pixel(lignes, taille // 2, int(0.95 * taille)), fond)              # sous le tronc

    def test_icone_personnalisee(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "mon_icone.png")
            with open(chemin, "wb") as f:
                f.write(serveur._icone_png(512, "#aa0000"))
            serveur.application_installable("Mes notes", icone=chemin)
        self.assertEqual(self.demander("/icone-512.png")[2], serveur._icone_png(512, "#aa0000"))
        self.assertEqual(self.demander("/icone-192.png")[2], serveur._icone_png(512, "#aa0000"))

    def test_icones_refusees(self):
        with tempfile.TemporaryDirectory() as dossier:
            def ecrire(nom, octets):
                chemin = os.path.join(dossier, nom)
                with open(chemin, "wb") as f:
                    f.write(octets)
                return chemin
            cas = {
                "texte.png": b"ceci n'est pas une image" * 5,
                "petite.png": serveur._icone_png(192, "#aa0000"),
                "gif.png": b"GIF89a" + b"\x00" * 40,
            }
            for nom, octets in cas.items():
                with self.assertRaises(ValueError, msg=nom):
                    serveur.application_installable("X", icone=ecrire(nom, octets))
            with mock.patch.object(serveur, "ICONE_MAX", 100):
                with self.assertRaises(ValueError):
                    serveur.application_installable("X", icone=ecrire("grosse.png", serveur._icone_png(512, "#aa0000")))
            with self.assertRaises(FileNotFoundError):
                serveur.application_installable("X", icone=os.path.join(dossier, "absente.png"))
        self.assertEqual(serveur._pwa, {})  # une configuration refusée ne laisse rien d'activé


class TestValeursRefusees(Base):
    def test_noms(self):
        for nom in ("", "   ", "x" * 46):
            with self.assertRaises(ValueError, msg=repr(nom)):
                serveur.application_installable(nom)
        with self.assertRaises(ValueError):
            serveur.application_installable("Nom", nom_court="x" * 13)
        with self.assertRaises(ValueError):
            serveur.application_installable("Nom", description="x" * 301)

    def test_couleurs(self):
        for mauvaise in ("red", "#12345", "#12345g", "123456", "#1234567",
                         "#000000'><script>alert(1)</script>", "#000000\n"):
            with self.assertRaises(ValueError, msg=mauvaise):
                serveur.application_installable("Nom", couleur=mauvaise)
            with self.assertRaises(ValueError, msg=mauvaise):
                serveur.application_installable("Nom", fond=mauvaise)

    def test_page_d_accueil(self):
        for mauvaise in ("accueil", "//autre.org", "http://autre.org/", "javascript:alert(1)", "/a\\b", "/a\nb"):
            with self.assertRaises(ValueError, msg=repr(mauvaise)):
                serveur.application_installable("Nom", page_d_accueil=mauvaise)
        serveur.application_installable("Nom", page_d_accueil="/mes/notes?x=1")


if __name__ == "__main__":
    unittest.main()
