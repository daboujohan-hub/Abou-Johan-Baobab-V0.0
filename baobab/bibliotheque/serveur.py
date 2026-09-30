"""Module serveur : un petit serveur web en français.

    importer serveur

    fonction accueil():
        retourner "<h1>Bonjour !</h1>"

    serveur.route("/", accueil)
    serveur.demarrer(8000)
"""

import inspect
import json
import os
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

_routes = {}
SILENCIEUX = False
TAILLE_MAX = 100_000  # taille maximale d'un formulaire (en octets)


class _Redirection:
    def __init__(self, chemin):
        self.chemin = chemin


def route(chemin, fonction=None):
    """Associe une adresse (ex: "/contact") à une fonction."""
    def enregistrer(f):
        _routes[chemin] = f
        return f

    if fonction is None:
        return enregistrer
    return enregistrer(fonction)


def rediriger(chemin):
    """À retourner par une fonction pour envoyer le visiteur vers une autre page."""
    chemin = str(chemin).replace("\r", "").replace("\n", "")
    return _Redirection("/" + chemin.lstrip("/"))


def echapper(texte):
    """Rend un texte sans danger avant de l'afficher dans une page."""
    return escape(str(texte))


def page(titre, contenu):
    """Fabrique une page HTML complète."""
    return (
        "<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{echapper(titre)}</title>"
        "<style>body{font-family:sans-serif;max-width:40rem;"
        "margin:2rem auto;padding:0 1rem}"
        "input,textarea{width:100%;padding:.5rem;font-size:1rem;box-sizing:border-box}"
        "button{padding:.6rem 1.2rem;font-size:1rem}</style>"
        f"</head><body>{contenu}</body></html>"
    )


def _appeler(fonction, parametres):
    try:
        nombre = len(inspect.signature(fonction).parameters)
    except (TypeError, ValueError):
        nombre = 0
    return fonction(parametres) if nombre >= 1 else fonction()


def _lire_champs(texte):
    return {cle: valeurs[0] for cle, valeurs in parse_qs(texte).items()}


class _Gestionnaire(BaseHTTPRequestHandler):
    def do_GET(self):
        self._traiter({})

    def do_POST(self):
        try:
            taille = int(self.headers.get("Content-Length", 0) or 0)
        except ValueError:
            self._repondre(400, page("Erreur", "<h1>Demande incorrecte</h1>"))
            return
        if taille > TAILLE_MAX:
            self._repondre(413, page("Trop long", "<h1>Message trop long</h1>"))
            return
        corps = self.rfile.read(taille).decode("utf-8", errors="replace")
        self._traiter(_lire_champs(corps))

    def _traiter(self, formulaire):
        adresse = urlparse(self.path)
        parametres = _lire_champs(adresse.query)
        parametres.update(formulaire)
        fonction = _routes.get(adresse.path)

        if fonction is None:
            self._repondre(404, page("Page introuvable",
                                     "<h1>404</h1><p>Cette page n'existe pas.</p>"))
            return
        try:
            resultat = _appeler(fonction, parametres)
        except Exception as erreur:
            from baobab.erreurs import expliquer

            explication = expliquer(erreur)
            if not SILENCIEUX:
                print(f"❌ Erreur sur {adresse.path} : {explication}")
            self._repondre(500, page(
                "Erreur",
                f"<h1>Erreur dans le programme</h1><p>{echapper(explication)}</p>"))
            return
        self._repondre(200, resultat)

    def _repondre(self, code, contenu):
        if isinstance(contenu, _Redirection):
            code = 303
            self.send_response(303)
            self.send_header("Location", contenu.chemin)
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            if isinstance(contenu, (dict, list)):
                corps = json.dumps(contenu, ensure_ascii=False)
                type_contenu = "application/json; charset=utf-8"
            else:
                corps = "" if contenu is None else str(contenu)
                type_contenu = "text/html; charset=utf-8"
            donnees = corps.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", type_contenu)
            self.send_header("Content-Length", str(len(donnees)))
            self.end_headers()
            self.wfile.write(donnees)
        if not SILENCIEUX:
            print(f"📥 {self.command} {self.path} -> {code}")

    def log_message(self, format, *arguments):
        pass


def _creer(hote, port):
    return ThreadingHTTPServer((hote, port), _Gestionnaire)


def demarrer(port=None, hote=None):
    """Démarre le serveur. Ctrl+C pour l'arrêter.

    Par défaut, seul ton appareil peut visiter le site (127.0.0.1).
    Sur un hébergeur (variable PORT définie), le site devient public.
    """
    if port is None:
        port = int(os.environ.get("PORT", 8000))
    if hote is None:
        hote = "0.0.0.0" if "PORT" in os.environ else "127.0.0.1"
    serveur = _creer(hote, port)
    print(f"🌳 Serveur Baobab prêt : http://localhost:{port}  (Ctrl+C pour arrêter)")
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        print("\nServeur arrêté.")
    finally:
        serveur.server_close()
