"""Module serveur : un serveur web en français.

    importer serveur

    fonction accueil():
        retourner "<h1>Bonjour !</h1>"

    serveur.route("/", accueil)
    serveur.demarrer(8000)

Ce que sait faire ce module :
  - des pages, des formulaires, du JSON, des redirections ;
  - serveur.repondre(...)        : choisir le code de réponse, les en-têtes, les cookies ;
  - serveur.route("/notes/<id:entier>", f) : des adresses avec paramètres ;
  - serveur.dossier_public(...)  : servir le CSS, les images, le JavaScript ;
  - serveur.cookie(...)          : poser un cookie ;
  - demande.session[...]         : se souvenir d'un visiteur (connexion) ;
  - serveur.modele(...)          : des pages à trous, avec protection du HTML.
"""

import functools
import inspect
import json
import mimetypes
import os
import re
import secrets
import threading
import time
from html import escape
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

_routes = {}
_dossiers_publics = []
_sessions = {}
_verrou_sessions = threading.Lock()

SILENCIEUX = False
TAILLE_MAX = 100_000  # taille maximale d'un formulaire (en octets)
COOKIES_SECURISES = os.environ.get("BAOBAB_HTTPS", "").lower() in ("1", "oui", "true")
NOM_COOKIE_SESSION = "baobab_session"
SESSION_DUREE = 7 * 24 * 3600  # une session inactive pendant 7 jours est oubliée
SESSIONS_MAX = 10_000

ENTETES_SECURITE = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}

_NOM_ENTETE = re.compile(r"^[A-Za-z0-9-]+$")
_TYPES_D_ADRESSE = {"entier": r"[0-9]+", "texte": r"[^/]+"}


# ---------------------------------------------------------------- réponses


def _verifier_entete(nom, valeur):
    if not _NOM_ENTETE.match(str(nom)):
        raise ValueError(f"Nom d'en-tête invalide : {nom!r}")
    if "\r" in str(valeur) or "\n" in str(valeur):
        raise ValueError("Une valeur d'en-tête ne peut pas contenir de retour à la ligne")


class Cookie:
    """Un cookie à envoyer au visiteur. Fabrique-le avec serveur.cookie(...)."""

    def __init__(self, nom, valeur, duree=None, securise=None, http_seulement=True,
                 meme_site="Lax", chemin="/"):
        if securise is None:
            securise = COOKIES_SECURISES
        meme_site = str(meme_site).capitalize()
        if meme_site not in ("Strict", "Lax", "None"):
            raise ValueError("meme_site doit être 'Strict', 'Lax' ou 'None'")
        if meme_site == "None" and not securise:
            raise ValueError("meme_site='None' demande securise=vrai (site en HTTPS)")
        valeur = str(valeur)
        if any(c in valeur for c in "\r\n\x00"):
            raise ValueError("La valeur d'un cookie ne peut pas contenir de retour à la ligne")
        self.nom = str(nom)
        self.valeur = valeur
        self.duree = duree
        self.securise = bool(securise)
        self.http_seulement = bool(http_seulement)
        self.meme_site = meme_site
        self.chemin = str(chemin)
        self.entete()  # vérifie tout de suite que le cookie est valide

    def entete(self):
        """Le texte de l'en-tête Set-Cookie."""
        pot = SimpleCookie()
        try:
            pot[self.nom] = self.valeur
        except CookieError:
            raise ValueError(f"Nom de cookie invalide : {self.nom!r}") from None
        morceau = pot[self.nom]
        morceau["path"] = self.chemin
        if self.duree is not None:
            morceau["max-age"] = int(self.duree)
        if self.http_seulement:
            morceau["httponly"] = True
        if self.securise:
            morceau["secure"] = True
        morceau["samesite"] = self.meme_site
        return morceau.OutputString()


def cookie(nom, valeur, duree=None, securise=None, http_seulement=True, meme_site="Lax"):
    """Fabrique un cookie. duree = secondes (0 = effacer le cookie).

    Par défaut le cookie est invisible pour le JavaScript (http_seulement) et n'est
    envoyé que par ton propre site (meme_site). Mets securise=vrai si ton site est en HTTPS.
    """
    return Cookie(nom, valeur, duree, securise, http_seulement, meme_site)


class Reponse:
    """Ce que ton application répond : contenu, code, en-têtes, cookies."""

    def __init__(self, contenu="", code=200, entetes=None, cookies=None, type_contenu=None):
        if isinstance(code, bool) or not isinstance(code, int) or not 100 <= code <= 599:
            raise ValueError("Le code de réponse doit être un nombre entre 100 et 599")
        self.contenu = contenu
        self.code = code
        self.entetes = dict(entetes or {})
        self.cookies = list(cookies or [])
        self.type_contenu = type_contenu
        for nom, valeur in self.entetes.items():
            _verifier_entete(nom, valeur)
        if type_contenu is not None:
            _verifier_entete("Content-Type", type_contenu)

    def corps_et_type(self):
        """(le corps en octets, le type de contenu)"""
        contenu = self.contenu
        if isinstance(contenu, (dict, list)):
            corps = json.dumps(contenu, ensure_ascii=False).encode("utf-8")
            type_contenu = "application/json; charset=utf-8"
        elif isinstance(contenu, (bytes, bytearray)):
            corps = bytes(contenu)
            type_contenu = "application/octet-stream"
        else:
            corps = ("" if contenu is None else str(contenu)).encode("utf-8")
            type_contenu = "text/html; charset=utf-8"
        if self.type_contenu:
            type_contenu = self.type_contenu
            if (not isinstance(contenu, (bytes, bytearray)) and type_contenu.startswith("text/")
                    and "charset" not in type_contenu):
                type_contenu += "; charset=utf-8"
        return corps, type_contenu


class _Redirection(Reponse):
    def __init__(self, chemin):
        super().__init__("", 303, {"Location": chemin})
        self.chemin = chemin


def repondre(contenu="", code=200, entetes=None, cookies=None, type_contenu=None):
    """Choisis ta réponse : repondre({"erreur": "introuvable"}, code=404)

    contenu : du texte (page HTML), un dictionnaire ou une liste (JSON), ou des octets
    entetes : {"Cache-Control": "no-store"}      cookies : [serveur.cookie(...)]
    type_contenu : par exemple "text/plain" ou "text/css"
    """
    return Reponse(contenu, code, entetes, cookies, type_contenu)


def rediriger(chemin):
    """À retourner par une fonction pour envoyer le visiteur vers une autre page."""
    chemin = str(chemin).replace("\r", "").replace("\n", "")
    return _Redirection("/" + chemin.lstrip("/"))


def echapper(texte):
    """Rend un texte sans danger avant de l'afficher dans une page."""
    return escape(str(texte))


def page(titre, contenu, css=None):
    """Fabrique une page HTML complète. css="/statique/style.css" pour ta propre feuille de style."""
    if css:
        style = f"<link rel='stylesheet' href='{echapper(css)}'>"
    else:
        style = (
            "<style>body{font-family:sans-serif;max-width:40rem;"
            "margin:2rem auto;padding:0 1rem}"
            "input,textarea{width:100%;padding:.5rem;font-size:1rem;box-sizing:border-box}"
            "button{padding:.6rem 1.2rem;font-size:1rem}</style>"
        )
    return (
        "<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{echapper(titre)}</title>{style}"
        f"</head><body>{contenu}</body></html>"
    )


# ------------------------------------------------------- modèles de pages

_MARQUE = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")


def _chercher(valeurs, chemin):
    courant = valeurs
    for morceau in chemin.split("."):
        if morceau.startswith("_"):
            raise ValueError(f"Le modèle ne peut pas lire « {morceau} » (noms privés interdits)")
        if isinstance(courant, dict) and morceau in courant:
            courant = courant[morceau]
        elif not isinstance(courant, (dict, str, int, float, list, tuple)) and hasattr(courant, morceau):
            courant = getattr(courant, morceau)
        else:
            raise ValueError(f"Le modèle utilise {{{{{chemin}}}}} mais cette valeur n'existe pas")
    return courant


def modele(texte, valeurs):
    """Une page à trous : modele("Bonjour {{nom}} !", {"nom": "Awa"}).

    {{nom}} est protégé automatiquement (le HTML devient du texte inoffensif).
    {{nom|brut}} insère du HTML tel quel : à réserver à ce que tu as fabriqué toi-même.
    {{utilisateur.nom}} lit dans un dictionnaire.
    """
    def remplacer(trouve):
        expression = trouve.group(1)
        brut = False
        if "|" in expression:
            nom, _, option = expression.partition("|")
            expression, option = nom.strip(), option.strip()
            if option != "brut":
                raise ValueError(f"Option inconnue dans {{{{{trouve.group(1)}}}}} : seul |brut existe")
            brut = True
        valeur = _chercher(valeurs, expression)
        texte_valeur = "" if valeur is None else str(valeur)
        return texte_valeur if brut else echapper(texte_valeur)

    return _MARQUE.sub(remplacer, texte)


def repeter(ligne, elements):
    """Répète un modèle pour chaque élément d'une liste.

    repeter("<li>{{texte}}</li>", [{"texte": "a"}, {"texte": "b"}])
    Pour une liste de textes, utilise {{element}}.
    """
    morceaux = []
    for element in elements:
        valeurs = element if isinstance(element, dict) else {"element": element}
        morceaux.append(modele(ligne, valeurs))
    return "".join(morceaux)


# ------------------------------------------------------------- sessions


class Session(dict):
    """Ce que ton site retient d'un visiteur. Utilise-la comme un dictionnaire."""

    def __init__(self, identifiant, donnees=None):
        super().__init__(donnees or {})
        self.id = identifiant
        self.derniere_activite = time.time()


def _purger_sessions():  # à appeler avec le verrou
    maintenant = time.time()
    for identifiant in [i for i, s in _sessions.items()
                        if maintenant - s.derniere_activite > SESSION_DUREE]:
        del _sessions[identifiant]
    while len(_sessions) >= SESSIONS_MAX:
        plus_ancienne = min(_sessions, key=lambda i: _sessions[i].derniere_activite)
        del _sessions[plus_ancienne]


def _sessions_creer(donnees=None):
    with _verrou_sessions:
        _purger_sessions()
        session = Session(secrets.token_urlsafe(32), donnees)
        _sessions[session.id] = session
        return session


def _sessions_trouver(identifiant):
    if not identifiant:
        return None
    with _verrou_sessions:
        session = _sessions.get(identifiant)
        if session is None:
            return None
        if time.time() - session.derniere_activite > SESSION_DUREE:
            del _sessions[identifiant]
            return None
        session.derniere_activite = time.time()
        return session


def _sessions_supprimer(identifiant):
    with _verrou_sessions:
        _sessions.pop(identifiant, None)


def _cookie_de_session(identifiant):
    return Cookie(NOM_COOKIE_SESSION, identifiant, duree=SESSION_DUREE)


def _lire_cookies(entete):
    pot = SimpleCookie()
    try:
        pot.load(entete)
    except CookieError:
        return {}
    return {nom: morceau.value for nom, morceau in pot.items()}


class Demande:
    """Ce que le visiteur a envoyé. Ajoute un 2e paramètre à ta fonction pour la recevoir :

        fonction accueil(parametres, demande):
            demande.session["visites"] = demande.session.obtenir("visites", 0) + 1
    """

    def __init__(self, gestionnaire, chemin):
        self.methode = gestionnaire.command
        self.chemin = chemin
        self.entetes = {nom.lower(): valeur for nom, valeur in gestionnaire.headers.items()}
        self.adresse_ip = gestionnaire.client_address[0]
        self.cookies = _lire_cookies("; ".join(gestionnaire.headers.get_all("Cookie", [])))
        self._session = None
        self._cookie_a_poser = None

    @property
    def session(self):
        """La session de ce visiteur (créée à la première utilisation)."""
        if self._session is None:
            self._session = _sessions_trouver(self.cookies.get(NOM_COOKIE_SESSION))
            if self._session is None:
                self._session = _sessions_creer()
                self._cookie_a_poser = _cookie_de_session(self._session.id)
        return self._session

    def nouvelle_session(self, garder_donnees=True):
        """Change l'identifiant de session. À faire juste après une connexion réussie."""
        ancienne = self.session
        donnees = dict(ancienne) if garder_donnees else {}
        _sessions_supprimer(ancienne.id)
        self._session = _sessions_creer(donnees)
        self._cookie_a_poser = _cookie_de_session(self._session.id)
        return self._session

    def fermer_session(self):
        """Déconnecte le visiteur : sa session est oubliée."""
        identifiant = self.cookies.get(NOM_COOKIE_SESSION)
        if identifiant:
            _sessions_supprimer(identifiant)
        if self._session is not None:
            _sessions_supprimer(self._session.id)
        self._session = None
        self._cookie_a_poser = Cookie(NOM_COOKIE_SESSION, "", duree=0)


# --------------------------------------------------------- adresses (routes)


@functools.lru_cache(maxsize=256)
def _compiler_adresse(chemin):
    morceaux, types, position = [], {}, 0
    for trouve in re.finditer(r"<([A-Za-z_][A-Za-z0-9_]*)(?::([a-z]+))?>", chemin):
        nom, genre = trouve.group(1), trouve.group(2) or "texte"
        if genre not in _TYPES_D_ADRESSE:
            raise ValueError(
                f"Type inconnu dans l'adresse : <{nom}:{genre}> (types possibles : entier, texte)")
        morceaux.append(re.escape(chemin[position:trouve.start()]))
        morceaux.append(f"(?P<{nom}>{_TYPES_D_ADRESSE[genre]})")
        types[nom] = genre
        position = trouve.end()
    morceaux.append(re.escape(chemin[position:]))
    try:
        return re.compile("^" + "".join(morceaux) + "$"), types
    except re.error:
        raise ValueError(f"Adresse invalide : {chemin} (un nom est utilisé deux fois ?)") from None


def route(chemin, fonction=None):
    """Associe une adresse (ex: "/contact") à une fonction.

    Les adresses peuvent avoir des parties variables : "/notes/<id:entier>" ou "/profil/<nom>".
    La valeur arrive dans les paramètres de ta fonction : parametres["id"].
    """
    if not str(chemin).startswith("/"):
        raise ValueError("Une adresse doit commencer par « / »")
    if "<" in chemin:
        _compiler_adresse(chemin)  # signale tout de suite une adresse mal écrite

    def enregistrer(f):
        _routes[chemin] = f
        return f

    if fonction is None:
        return enregistrer
    return enregistrer(fonction)


def _trouver_route(chemin):
    fonction = _routes.get(chemin)
    if fonction is not None:
        return fonction, {}
    for modele_adresse, fonction in list(_routes.items()):
        if "<" not in modele_adresse:
            continue
        motif, types = _compiler_adresse(modele_adresse)
        trouve = motif.match(chemin)
        if trouve:
            valeurs = {}
            for nom, texte in trouve.groupdict().items():
                valeurs[nom] = int(texte) if types[nom] == "entier" else unquote(texte)
            return fonction, valeurs
    return None, {}


# ------------------------------------------------------- fichiers publics


def dossier_public(dossier, prefixe="/statique"):
    """Sert les fichiers d'un dossier (CSS, images, JavaScript...).

    dossier_public("public") : le fichier public/style.css devient /statique/style.css
    Les fichiers cachés (.nom) et tout ce qui sort du dossier sont refusés.
    """
    racine = os.path.realpath(os.path.expanduser(str(dossier)))
    if not os.path.isdir(racine):
        raise FileNotFoundError(f"Dossier introuvable : {racine}")
    prefixe = "/" + str(prefixe).strip("/")
    if prefixe == "/":
        raise ValueError("Le préfixe ne peut pas être « / » (il cacherait tes pages)")
    _dossiers_publics.append((prefixe, racine))


def _fichier_public(chemin):
    for prefixe, racine in _dossiers_publics:
        if not chemin.startswith(prefixe + "/"):
            continue
        relatif = unquote(chemin[len(prefixe) + 1:])
        if not relatif or "\x00" in relatif or "\\" in relatif:
            return None
        parties = [p for p in relatif.split("/") if p]
        if not parties or any(p.startswith(".") for p in parties):
            return None
        candidat = os.path.realpath(os.path.join(racine, *parties))
        try:
            if os.path.commonpath([racine, candidat]) != racine:
                return None
        except ValueError:
            return None
        if os.path.isfile(candidat):
            return candidat
    return None


# ------------------------------------------------------------ le serveur


def _appeler(fonction, parametres, demande):
    try:
        nombre = len(inspect.signature(fonction).parameters)
    except (TypeError, ValueError):
        nombre = 0
    if nombre >= 2:
        return fonction(parametres, demande)
    if nombre == 1:
        return fonction(parametres)
    return fonction()


def _lire_champs(texte):
    return {cle: valeurs[0] for cle, valeurs in parse_qs(texte).items()}


class _Gestionnaire(BaseHTTPRequestHandler):
    def do_GET(self):
        self._traiter({})

    def do_POST(self):
        try:
            taille = int(self.headers.get("Content-Length", 0) or 0)
        except ValueError:
            self._envoyer_simple(400, "<h1>Demande incorrecte</h1>")
            return
        if taille > TAILLE_MAX:
            self._envoyer_simple(413, "<h1>Message trop long</h1>")
            return
        corps = self.rfile.read(taille).decode("utf-8", errors="replace")
        self._traiter(_lire_champs(corps))

    def _traiter(self, formulaire):
        adresse = urlparse(self.path)
        chemin = adresse.path or "/"
        demande = Demande(self, chemin)

        if self.command == "GET":
            fichier = _fichier_public(chemin)
            if fichier is not None:
                self._envoyer_fichier(fichier)
                return

        parametres = _lire_champs(adresse.query)
        parametres.update(formulaire)
        fonction, valeurs = _trouver_route(chemin)
        if fonction is None:
            self._envoyer_simple(404, "<h1>404</h1><p>Cette page n'existe pas.</p>", "Page introuvable")
            return
        parametres.update(valeurs)  # les valeurs de l'adresse l'emportent sur le reste

        try:
            resultat = _appeler(fonction, parametres, demande)
            reponse = resultat if isinstance(resultat, Reponse) else Reponse(resultat)
            corps, type_contenu = reponse.corps_et_type()
        except Exception as erreur:
            from baobab.erreurs import expliquer

            explication = expliquer(erreur)
            if not SILENCIEUX:
                print(f"❌ Erreur sur {chemin} : {explication}")
            self._envoyer_simple(
                500, f"<h1>Erreur dans le programme</h1><p>{echapper(explication)}</p>", "Erreur")
            return
        self._envoyer(reponse, corps, type_contenu, demande)

    def _envoyer(self, reponse, corps, type_contenu, demande=None):
        entetes = {"content-type": ("Content-Type", type_contenu),
                   "content-length": ("Content-Length", str(len(corps)))}
        for nom, valeur in ENTETES_SECURITE.items():
            entetes[nom.lower()] = (nom, valeur)
        for nom, valeur in reponse.entetes.items():
            entetes[nom.lower()] = (nom, str(valeur))
        cookies = list(reponse.cookies)
        if demande is not None and demande._cookie_a_poser is not None:
            cookies.append(demande._cookie_a_poser)

        self.send_response(reponse.code)
        for nom, valeur in entetes.values():
            self.send_header(nom, valeur)
        for un_cookie in cookies:
            self.send_header("Set-Cookie", un_cookie.entete())
        self.end_headers()
        self.wfile.write(corps)
        if not SILENCIEUX:
            print(f"📥 {self.command} {self.path} -> {reponse.code}")

    def _envoyer_simple(self, code, contenu, titre="Erreur"):
        reponse = Reponse(page(titre, contenu), code)
        corps, type_contenu = reponse.corps_et_type()
        self._envoyer(reponse, corps, type_contenu)

    def _envoyer_fichier(self, chemin_fichier):
        type_contenu = mimetypes.guess_type(chemin_fichier)[0] or "application/octet-stream"
        if type_contenu.startswith("text/") or type_contenu in (
                "application/javascript", "application/json", "image/svg+xml"):
            type_contenu += "; charset=utf-8"
        try:
            with open(chemin_fichier, "rb") as fichier:
                taille = os.fstat(fichier.fileno()).st_size
                self.send_response(200)
                self.send_header("Content-Type", type_contenu)
                self.send_header("Content-Length", str(taille))
                self.send_header("Cache-Control", "no-cache")
                for nom, valeur in ENTETES_SECURITE.items():
                    self.send_header(nom, valeur)
                self.end_headers()
                while True:
                    morceau = fichier.read(64 * 1024)
                    if not morceau:
                        break
                    self.wfile.write(morceau)
        except OSError:
            return
        if not SILENCIEUX:
            print(f"📥 {self.command} {self.path} -> 200 (fichier)")

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
