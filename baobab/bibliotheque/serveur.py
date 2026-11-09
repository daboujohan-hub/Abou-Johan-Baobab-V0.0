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
from http import HTTPStatus
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

_routes = {}
_methodes = {}  # {adresse: méthodes permises}
_dossiers_publics = []
_sessions = {}
_verrou_sessions = threading.Lock()

SILENCIEUX = False
TAILLE_MAX = 100_000  # taille maximale d'un formulaire (en octets)
COOKIES_SECURISES = os.environ.get("BAOBAB_HTTPS", "").lower() in ("1", "oui", "true")
NOM_COOKIE_SESSION = "baobab_session"
SESSION_DUREE = 7 * 24 * 3600  # une session inactive pendant 7 jours est oubliée
SESSIONS_MAX = 10_000
TAILLE_MAX_JSON = 1_000_000  # taille maximale d'un JSON reçu (en octets)
METHODES_PAR_DEFAUT = ("GET", "POST")
METHODES_CONFIGURABLES = ("GET", "POST", "PUT", "PATCH", "DELETE")

ENTETES_SECURITE = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}

_NOM_ENTETE = re.compile(r"^[A-Za-z0-9-]+\Z")
_TYPES_D_ADRESSE = {"entier": r"[0-9]+", "texte": r"[^/]+"}


# ---------------------------------------------------------------- réponses


def _verifier_entete(nom, valeur):
    if not _NOM_ENTETE.match(str(nom)):
        raise ValueError(f"Nom d'en-tête invalide : {nom!r}")
    if "\r" in str(valeur) or "\n" in str(valeur):
        raise ValueError("Une valeur d'en-tête ne peut pas contenir de retour à la ligne")


def _trop_profond(texte, maxi=64):
    prof = 0
    dans_chaine = False
    echappe = False
    for c in texte:
        if dans_chaine:
            if echappe:
                echappe = False
            elif c == "\\":
                echappe = True
            elif c == '"':
                dans_chaine = False
        elif c == '"':
            dans_chaine = True
        elif c in "[{":
            prof += 1
            if prof > maxi:
                return True
        elif c in "]}":
            prof -= 1
    return False


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
        f"<title>{echapper(titre)}</title>{style}{_balises_pwa()}"
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

    def __init__(self, gestionnaire, chemin, corps=b""):
        self.methode = gestionnaire.command
        self.chemin = chemin
        self.corps = corps
        self.type_contenu = gestionnaire.headers.get("Content-Type", "")
        self.entetes = {nom.lower(): valeur for nom, valeur in gestionnaire.headers.items()}
        self.adresse_ip = gestionnaire.client_address[0]
        self.cookies = _lire_cookies("; ".join(gestionnaire.headers.get_all("Cookie", [])))
        self._session = None
        self._cookie_a_poser = None

    @property
    def json(self):
        """Le JSON envoyé par l'application (dictionnaire, liste...), ou None s'il n'y a rien.

        Si le contenu n'est pas du JSON valide, la demande s'arrête toute seule (code 415 ou 400).
        """
        if not self.corps:
            return None
        if "json" not in self.type_contenu.lower():
            raise ErreurHTTP(415, "Le contenu doit être du JSON (Content-Type: application/json)")
        try:
            texte = self.corps.decode("utf-8")
            if _trop_profond(texte):
                raise ValueError("JSON trop profond")
            return json.loads(texte)
        except (ValueError, RecursionError):  # UnicodeDecodeError est une ValueError
            raise ErreurHTTP(400, "Le JSON envoyé est invalide") from None

    @property
    def jeton(self):
        """Le jeton d'accès envoyé par une application (Authorization: Bearer ...), ou None."""
        schema, _, valeur = self.entetes.get("authorization", "").partition(" ")
        valeur = valeur.strip()
        return valeur if schema.lower() == "bearer" and valeur else None

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


def _normaliser_methodes(methodes):
    if methodes is None:
        return METHODES_PAR_DEFAUT
    if isinstance(methodes, str):
        methodes = [methodes]
    resultat = set()
    for methode in methodes:
        nom = str(methode).upper()
        if nom in ("HEAD", "OPTIONS"):
            raise ValueError(f"{nom} est géré automatiquement : ne l'écris pas dans methodes")
        if nom not in METHODES_CONFIGURABLES:
            raise ValueError(
                f"Méthode inconnue : {methode!r} (possibles : {', '.join(METHODES_CONFIGURABLES)})")
        resultat.add(nom)
    if not resultat:
        raise ValueError("Il faut au moins une méthode")
    return tuple(sorted(resultat))


def route(chemin, fonction=None, methodes=None):
    """Associe une adresse (ex: "/contact") à une fonction.

    Les adresses peuvent avoir des parties variables : "/notes/<id:entier>" ou "/profil/<nom>".
    La valeur arrive dans les paramètres de ta fonction : parametres["id"].

    methodes : les méthodes permises, par exemple ["GET", "POST", "PUT", "DELETE"].
    Sans cela : GET et POST seulement. Une autre méthode reçoit le code 405.
    La fonction regarde demande.methode pour savoir laquelle est utilisée.
    """
    if not str(chemin).startswith("/"):
        raise ValueError("Une adresse doit commencer par « / »")
    permises = _normaliser_methodes(methodes)
    if "<" in chemin:
        _compiler_adresse(chemin)  # signale tout de suite une adresse mal écrite

    def enregistrer(f):
        _routes[chemin] = f
        _methodes[chemin] = permises
        return f

    if fonction is None:
        return enregistrer
    return enregistrer(fonction)


def documenter(chemin="/documentation", titre="Documentation"):
    """Ajoute une page qui liste les adresses du site et leurs méthodes.

    chemin : l'adresse de la page (la version JSON est chemin + ".json").
    """
    def adresses():
        ignorees = (chemin, chemin + ".json")
        return [{"adresse": a, "methodes": sorted(_methodes.get(a, ["GET", "POST"]))}
                for a in sorted(_routes) if a not in ignorees]

    def en_json(parametres, demande):
        corps = json.dumps({"titre": titre, "adresses": adresses()}, ensure_ascii=False)
        return repondre(corps, type_contenu="application/json")

    def en_html(parametres, demande):
        lignes = "".join(
            "<li><code>{}</code> : méthodes {}</li>".format(
                echapper(a["adresse"]), echapper(", ".join(a["methodes"])))
            for a in adresses())
        return page(titre, "<h1>{}</h1><ul>{}</ul>".format(echapper(titre), lignes))

    route(chemin, en_html)
    route(chemin + ".json", en_json)


def _trouver_route(chemin):
    """(l'adresse enregistrée, la fonction, les valeurs de l'adresse)"""
    fonction = _routes.get(chemin)
    if fonction is not None:
        return chemin, fonction, {}
    for modele_adresse, fonction in list(_routes.items()):
        if "<" not in modele_adresse:
            continue
        motif, types = _compiler_adresse(modele_adresse)
        trouve = motif.match(chemin)
        if trouve:
            valeurs = {}
            for nom, texte in trouve.groupdict().items():
                valeurs[nom] = int(texte) if types[nom] == "entier" else unquote(texte)
            return modele_adresse, fonction, valeurs
    return None, None, {}


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


# ---------------------------------------------- erreurs, CORS, jetons d'accès


def _phrase(code):
    try:
        return HTTPStatus(code).phrase
    except ValueError:
        return "Erreur"


class ErreurHTTP(Exception):
    """Arrête la demande avec un code précis : lever serveur.ErreurHTTP(404, "Note introuvable")

    L'application reçoit {"erreur": "Note introuvable"} avec le code 404.
    """

    def __init__(self, code, message="", entetes=None, details=None):
        if isinstance(code, bool) or not isinstance(code, int) or not 400 <= code <= 599:
            raise ValueError("Le code d'une erreur doit être un nombre entre 400 et 599")
        super().__init__(message)
        self.code = code
        self.message = str(message)
        self.details = details
        self.entetes = dict(entetes or {})
        for nom, valeur in self.entetes.items():
            _verifier_entete(nom, valeur)


def refuser(code, message="", details=None):
    """Arrête la demande tout de suite : serveur.refuser(404, "Cette note n'existe pas")"""
    raise ErreurHTTP(code, message, None, details)


def exiger_jeton(demande, cle, droit=None):
    """Exige un jeton d'accès valide (en-tête « Authorization: Bearer ... »).

    Retourne {"identite": ..., "droits": [...]}. Sinon la demande s'arrête avec le code 401
    (jeton absent, faux ou périmé) ou 403 (le jeton n'a pas le droit demandé).
    Les jetons se fabriquent avec securite.creer_jeton_acces(...).
    """
    from . import securite

    jeton = demande.jeton
    if jeton is None:
        raise ErreurHTTP(401, "Jeton d'accès manquant", {"WWW-Authenticate": "Bearer"})
    contenu = securite.verifier_jeton_acces(jeton, cle)
    if contenu is None:
        raise ErreurHTTP(401, "Jeton d'accès invalide ou périmé",
                         {"WWW-Authenticate": 'Bearer error="invalid_token"'})
    if droit is not None and droit not in contenu["droits"]:
        raise ErreurHTTP(403, "Ce jeton n'a pas le droit nécessaire")
    return contenu


_ORIGINE = re.compile(r"^https?://[a-z0-9.-]+(:[0-9]{1,5})?$")
_cors = {"origines": frozenset(), "avec_cookies": False, "entetes": ("Content-Type", "Authorization")}


def autoriser_origines(origines, avec_cookies=False, entetes=()):
    """Autorise des sites ou des applications web à appeler ton API depuis un navigateur (CORS).

        serveur.autoriser_origines(["https://monsite.org", "http://localhost:3000"])

    origines : la liste des sites autorisés ("https://monsite.org", sans chemin).
               "*" autorise tout le monde, mais jamais avec les cookies.
    avec_cookies : vrai pour que ces sites puissent envoyer les cookies (jamais avec "*").
    entetes : en-têtes supplémentaires autorisés (Content-Type et Authorization le sont déjà).
    Une liste vide supprime toutes les autorisations.
    """
    liste = set()
    for origine in origines:
        propre = str(origine).strip().lower().rstrip("/")
        if propre != "*" and not _ORIGINE.match(propre):
            raise ValueError(
                f"Origine invalide : {origine!r} (écris par exemple https://monsite.org, sans chemin)")
        liste.add(propre)
    if "*" in liste and avec_cookies:
        raise ValueError("« * » (tout le monde) ne peut pas être autorisé avec les cookies")
    for nom in entetes:
        if not _NOM_ENTETE.match(str(nom)):
            raise ValueError(f"Nom d'en-tête invalide : {nom!r}")
    _cors["origines"] = frozenset(liste)
    _cors["avec_cookies"] = bool(avec_cookies)
    _cors["entetes"] = tuple(dict.fromkeys(("Content-Type", "Authorization") + tuple(entetes)))


def _entetes_cors(origine):
    if not _cors["origines"]:
        return {}
    if "*" in _cors["origines"]:
        return {"Access-Control-Allow-Origin": "*"}
    entetes = {"Vary": "Origin"}
    if str(origine).lower() in _cors["origines"]:
        entetes["Access-Control-Allow-Origin"] = origine
        if _cors["avec_cookies"]:
            entetes["Access-Control-Allow-Credentials"] = "true"
    return entetes


def _entetes_cors_preliminaire(origine, methode, entetes_demandes, permises):
    base = _entetes_cors(origine)
    if "Access-Control-Allow-Origin" not in base:
        return None
    if methode.strip().upper() not in permises:
        return None
    autorises = {nom.lower() for nom in _cors["entetes"]}
    demandes = [nom.strip() for nom in entetes_demandes.split(",") if nom.strip()]
    if any(nom.lower() not in autorises for nom in demandes):
        return None
    base["Access-Control-Allow-Methods"] = ", ".join(sorted(permises))
    if demandes:
        base["Access-Control-Allow-Headers"] = ", ".join(demandes)
    base["Access-Control-Max-Age"] = "600"
    return base


def _allow(permises):
    toutes = set(permises) | {"OPTIONS"}
    if "GET" in toutes:
        toutes.add("HEAD")
    return ", ".join(sorted(toutes))


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
        self._lancer()

    do_HEAD = do_POST = do_PUT = do_PATCH = do_DELETE = do_GET

    def do_OPTIONS(self):
        self._preliminaire()

    def _lire_corps(self):
        """Lit le corps de la demande. Retourne (octets, type de contenu), ou None si refusé."""
        type_contenu = self.headers.get("Content-Type", "")
        if self.command not in ("POST", "PUT", "PATCH", "DELETE"):
            return b"", type_contenu
        try:
            taille = int(self.headers.get("Content-Length", 0) or 0)
        except ValueError:
            taille = -1
        if taille < 0:
            self._envoyer_simple(400, "<h1>Demande incorrecte</h1>")
            return None
        limite = TAILLE_MAX_JSON if "json" in type_contenu.lower() else TAILLE_MAX
        if taille > limite:
            self._envoyer_simple(413, "<h1>Message trop long</h1>")
            return None
        return self.rfile.read(taille), type_contenu

    def _lancer(self):
        lu = self._lire_corps()
        if lu is None:
            return
        corps, type_contenu = lu
        adresse = urlparse(self.path)
        chemin = adresse.path or "/"
        demande = Demande(self, chemin, corps)

        if self.command in ("GET", "HEAD"):
            fichier = _fichier_public(chemin)
            if fichier is not None:
                self._envoyer_fichier(fichier)
                return

        modele_adresse, fonction, valeurs = _trouver_route(chemin)
        if fonction is None:
            self._envoyer_simple(404, "<h1>404</h1><p>Cette page n'existe pas.</p>", "Page introuvable")
            return
        permises = _methodes.get(modele_adresse, METHODES_PAR_DEFAUT)
        if ("GET" if self.command == "HEAD" else self.command) not in permises:
            self._envoyer_simple(
                405, "<h1>405</h1><p>Cette méthode n'est pas permise ici.</p>",
                "Méthode non permise", {"Allow": _allow(permises)})
            return

        parametres = _lire_champs(adresse.query)
        if "json" not in type_contenu.lower():
            parametres.update(_lire_champs(corps.decode("utf-8", errors="replace")))
        parametres.update(valeurs)  # les valeurs de l'adresse l'emportent sur le reste

        try:
            resultat = _appeler(fonction, parametres, demande)
            reponse = resultat if isinstance(resultat, Reponse) else Reponse(resultat)
            corps_reponse, type_reponse = reponse.corps_et_type()
        except ErreurHTTP as erreur:
            contenu = {"erreur": erreur.message or _phrase(erreur.code)}
            if erreur.details:
                contenu["details"] = erreur.details
            reponse = Reponse(contenu, erreur.code, erreur.entetes)
            corps_reponse, type_reponse = reponse.corps_et_type()
        except Exception as erreur:
            from baobab.erreurs import expliquer

            explication = expliquer(erreur)
            if not SILENCIEUX:
                print(f"❌ Erreur sur {chemin} : {explication}")
            self._envoyer_simple(
                500, f"<h1>Erreur dans le programme</h1><p>{echapper(explication)}</p>", "Erreur")
            return
        self._envoyer(reponse, corps_reponse, type_reponse, demande)

    def _preliminaire(self):
        """OPTIONS : « quelles méthodes sont permises ici ? » (et la vérification CORS)."""
        chemin = urlparse(self.path).path or "/"
        modele_adresse, fonction, _ = _trouver_route(chemin)
        if fonction is None:
            self._envoyer_simple(404, "<h1>404</h1><p>Cette page n'existe pas.</p>", "Page introuvable")
            return
        permises = set(_methodes.get(modele_adresse, METHODES_PAR_DEFAUT))
        entetes = {"Allow": _allow(permises)}
        origine = self.headers.get("Origin")
        demandee = self.headers.get("Access-Control-Request-Method")
        if origine and demandee:  # la requête préliminaire d'un navigateur
            cors = _entetes_cors_preliminaire(
                origine, demandee, self.headers.get("Access-Control-Request-Headers", ""), permises)
            if cors is None:
                self._envoyer_simple(
                    403, "<h1>403</h1><p>Origine, méthode ou en-têtes non autorisés.</p>",
                    "Refusé", entetes)
                return
            entetes.update(cors)
        self._envoyer(Reponse("", 204, entetes), b"", "text/plain", None)

    def _envoyer(self, reponse, corps, type_contenu, demande=None):
        sans_corps = reponse.code in (204, 304) or 100 <= reponse.code < 200
        entetes = {}
        if not sans_corps:
            entetes["content-type"] = ("Content-Type", type_contenu)
            entetes["content-length"] = ("Content-Length", str(len(corps)))
        for nom, valeur in ENTETES_SECURITE.items():
            entetes[nom.lower()] = (nom, valeur)
        origine = self.headers.get("Origin")
        if origine:
            for nom, valeur in _entetes_cors(origine).items():
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
        if not sans_corps and self.command != "HEAD":
            self.wfile.write(corps)
        if not SILENCIEUX:
            print(f"📥 {self.command} {self.path} -> {reponse.code}")

    def _envoyer_simple(self, code, contenu, titre="Erreur", entetes=None):
        reponse = Reponse(page(titre, contenu), code, entetes)
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
                while self.command != "HEAD":
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


# ------------------------------------------- limiter les abus (limiter)

import copy  # noqa: E402
import hashlib  # noqa: E402
import math  # noqa: E402
import struct  # noqa: E402
import zlib  # noqa: E402
from collections import deque  # noqa: E402

LIMITES_MAX = 50_000        # nombre maximal de visiteurs suivis en mémoire
_limites = {}               # {(nom, visiteur): (moments des demandes, durée)}
_verrou_limites = threading.Lock()


def _maintenant():
    return time.monotonic()


def _purger_limites(maintenant):  # à appeler avec le verrou
    for cle in [c for c, (moments, duree) in _limites.items()
                if not moments or maintenant - moments[-1] >= duree]:
        del _limites[cle]
    if len(_limites) > LIMITES_MAX:
        anciens = sorted(_limites, key=lambda c: _limites[c][0][-1])
        for cle in anciens[:len(_limites) - LIMITES_MAX]:
            del _limites[cle]


def limiter(demande, nom, maximum, duree, cle=None):
    """Limite le nombre de demandes : au-delà, la demande s'arrête avec le code 429.

        serveur.limiter(demande, "commentaires", 10, 60)               # 10 par minute et par visiteur
        serveur.limiter(demande, "connexion", 5, 300, cle=nom)         # 5 par 5 minutes et par nom

    nom : le nom de cette limite.   maximum : nombre de demandes permises.
    duree : sur combien de secondes.   cle : ce qui identifie le visiteur (par défaut : son adresse IP).
    Retourne le nombre de demandes qu'il lui reste. L'en-tête Retry-After dit quand réessayer.

    Attention : le compte est gardé en mémoire (oublié si le serveur redémarre). Derrière un
    relais de l'hébergeur, tous les visiteurs peuvent avoir la même adresse IP : passe alors cle=.
    """
    if not isinstance(nom, str) or not nom:
        raise ValueError("Le nom de la limite doit être un texte non vide")
    if isinstance(maximum, bool) or not isinstance(maximum, int) or maximum < 1:
        raise ValueError("maximum doit être un nombre entier d'au moins 1")
    if isinstance(duree, bool) or not isinstance(duree, (int, float)) or duree <= 0:
        raise ValueError("duree doit être un nombre de secondes supérieur à 0")
    visiteur = str(cle) if cle is not None else demande.adresse_ip
    maintenant = _maintenant()
    with _verrou_limites:
        moments, _ = _limites.get((nom, visiteur), (deque(), duree))
        while moments and maintenant - moments[0] >= duree:
            moments.popleft()
        if len(moments) >= maximum:
            attente = max(1, math.ceil(moments[0] + duree - maintenant))
            _limites[(nom, visiteur)] = (moments, duree)
            raise ErreurHTTP(429, f"Trop de demandes : réessaie dans {attente} seconde(s)",
                             {"Retry-After": str(attente)})
        moments.append(maintenant)
        _limites[(nom, visiteur)] = (moments, duree)
        if len(_limites) > LIMITES_MAX:
            _purger_limites(maintenant)
        return maximum - len(moments)


# ------------------------------------------ validation des données (valider)

_ABSENT = object()
_REGLES_CONNUES = {"type", "obligatoire", "defaut", "min", "max", "choix", "motif", "nettoyer", "elements"}
_TYPES_DE_DONNEES = ("texte", "entier", "decimal", "booleen", "liste")
_VRAI = {"vrai", "true", "1", "oui"}
_FAUX = {"faux", "false", "0", "non"}
TEXTE_MAX_PAR_DEFAUT = 10_000
LISTE_MAX_PAR_DEFAUT = 1_000


def _nombre_de_regle(regle, cle):
    valeur = regle.get(cle)
    if valeur is not None and (isinstance(valeur, bool) or not isinstance(valeur, (int, float))):
        raise ValueError(f"La règle « {cle} » doit être un nombre")
    return valeur


def _valider_champ(valeur, regle):
    """(valeur propre, None), ou (None, message d'erreur), ou (_ABSENT, None) si le champ est facultatif et absent."""
    if not isinstance(regle, dict):
        raise ValueError("Chaque règle doit être un dictionnaire, par exemple {\"type\": \"texte\"}")
    inconnues = set(regle) - _REGLES_CONNUES
    if inconnues:
        raise ValueError(f"Règle inconnue : {', '.join(sorted(inconnues))} "
                         f"(règles possibles : {', '.join(sorted(_REGLES_CONNUES))})")
    genre = regle.get("type", "texte")
    if genre not in _TYPES_DE_DONNEES:
        raise ValueError(f"Type inconnu : {genre!r} (types possibles : {', '.join(_TYPES_DE_DONNEES)})")
    minimum, maximum = _nombre_de_regle(regle, "min"), _nombre_de_regle(regle, "max")
    if "elements" in regle and not isinstance(regle["elements"], dict):
        raise ValueError("La règle « elements » doit être un dictionnaire")
    if "choix" in regle and not isinstance(regle["choix"], (list, tuple, set, frozenset)):
        raise ValueError("La règle « choix » doit être une liste")
    if "motif" in regle:
        try:
            re.compile(regle["motif"])
        except (re.error, TypeError):
            raise ValueError("La règle « motif » n'est pas une expression régulière valide") from None
    obligatoire = regle.get("obligatoire", "defaut" not in regle)

    if valeur is _ABSENT or valeur is None:
        if "defaut" in regle:
            return copy.deepcopy(regle["defaut"]), None
        return (None, "obligatoire") if obligatoire else (_ABSENT, None)

    if genre == "texte":
        if not isinstance(valeur, str):
            return None, "doit être un texte"
        if "\x00" in valeur:
            return None, "contient un caractère interdit"
        if regle.get("nettoyer", True):
            valeur = valeur.strip()
        if valeur == "" and obligatoire:
            return None, "ne peut pas être vide"
        limite = maximum if maximum is not None else TEXTE_MAX_PAR_DEFAUT
        if minimum is not None and len(valeur) < minimum:
            return None, f"{minimum:g} caractères minimum"
        if len(valeur) > limite:
            return None, f"{limite:g} caractères maximum"
        if "motif" in regle and not re.fullmatch(regle["motif"], valeur):
            return None, "format invalide"
    elif genre in ("entier", "decimal"):
        if isinstance(valeur, bool):
            return None, "doit être un nombre entier" if genre == "entier" else "doit être un nombre"
        if isinstance(valeur, str):
            texte = valeur.strip()
            if genre == "entier" and re.fullmatch(r"[+-]?[0-9]{1,18}", texte):
                valeur = int(texte)
            elif genre == "decimal" and re.fullmatch(r"[+-]?([0-9]+\.?[0-9]*|\.[0-9]+)", texte):
                valeur = float(texte)
        if genre == "entier" and not (isinstance(valeur, int) and not isinstance(valeur, bool)):
            return None, "doit être un nombre entier"
        if genre == "decimal":
            if not isinstance(valeur, (int, float)):
                return None, "doit être un nombre"
            try:
                valeur = float(valeur)
            except OverflowError:
                return None, "doit être un nombre"
            if not math.isfinite(valeur):
                return None, "doit être un nombre"
        if minimum is not None and valeur < minimum:
            return None, f"doit être au moins {minimum:g}"
        if maximum is not None and valeur > maximum:
            return None, f"doit être au plus {maximum:g}"
    elif genre == "booleen":
        if isinstance(valeur, str) and valeur.strip().casefold() in _VRAI | _FAUX:
            valeur = valeur.strip().casefold() in _VRAI
        if not isinstance(valeur, bool):
            return None, "doit être vrai ou faux"
    else:  # liste
        if not isinstance(valeur, list):
            return None, "doit être une liste"
        limite = maximum if maximum is not None else LISTE_MAX_PAR_DEFAUT
        if minimum is not None and len(valeur) < minimum:
            return None, f"{minimum:g} éléments minimum"
        if len(valeur) > limite:
            return None, f"{limite:g} éléments maximum"
        if "elements" in regle:
            propres, erreurs = [], []
            for position, element in enumerate(valeur):
                propre, erreur = _valider_champ(element, {**regle["elements"], "obligatoire": True})
                if erreur:
                    erreurs.append(f"élément {position + 1} : {erreur}")
                else:
                    propres.append(propre)
            if erreurs:
                return None, "; ".join(erreurs[:3])
            valeur = propres

    if "choix" in regle and valeur not in regle["choix"]:
        return None, "doit être l'une des valeurs : " + ", ".join(str(c) for c in regle["choix"])
    return valeur, None


def valider(donnees, regles):
    """Vérifie les données reçues. Retourne les données propres, ou arrête la demande (code 422).

        valide = serveur.valider(demande.json, {
            "nom":   {"type": "texte", "min": 3, "max": 30},
            "age":   {"type": "entier", "min": 0, "max": 150, "defaut": 18},
            "role":  {"type": "texte", "choix": ["eleve", "prof"], "defaut": "eleve"},
            "mail":  {"type": "texte", "motif": "[^@ ]+@[^@ ]+", "obligatoire": False},
        })

    Types : texte, entier, decimal, booleen, liste (avec "elements": {règle de chaque élément}).
    Règles : type, obligatoire, defaut, min, max (valeur, ou longueur pour un texte ou une liste),
             choix, motif (le texte entier doit correspondre), nettoyer (enlever les espaces, oui par défaut).
    Un champ est obligatoire, sauf s'il a un defaut ou "obligatoire": False.
    Les champs que tu n'as pas décrits sont IGNORÉS : un visiteur ne peut pas en ajouter.
    Les formulaires envoient du texte : "12" est accepté pour un entier.
    L'erreur envoyée à l'application : {"erreur": ..., "details": {"nom": "3 caractères minimum"}}
    """
    if not isinstance(regles, dict) or not regles:
        raise ValueError("regles doit être un dictionnaire non vide")
    if donnees is None:
        donnees = {}
    if not isinstance(donnees, dict):
        raise ErreurHTTP(422, "Les données envoyées doivent être un objet JSON : {\"champ\": valeur}")
    propres, erreurs = {}, {}
    for nom, regle in regles.items():
        valeur, erreur = _valider_champ(donnees.get(nom, _ABSENT), regle)
        if erreur:
            erreurs[nom] = erreur
        elif valeur is not _ABSENT:
            propres[nom] = valeur
    if erreurs:
        raise ErreurHTTP(422, "Les données envoyées ne sont pas valides", None, erreurs)
    return propres


# ------------------------------- application installable sur le téléphone (PWA)

_pwa = {}
_COULEUR = re.compile(r"^#[0-9a-fA-F]{6}\Z")
_SIGNATURE_PNG = b"\x89PNG\r\n\x1a\n"
ICONE_MAX = 1_000_000  # octets


def _balises_pwa():
    if not _pwa:
        return ""
    return (
        "<link rel='manifest' href='/manifest.webmanifest'>"
        f"<meta name='theme-color' content='{_pwa['couleur']}'>"
        "<link rel='apple-touch-icon' href='/icone-192.png'>"
        "<script src='/pwa.js' defer></script>"
    )


def _morceau_png(genre, donnees):
    corps = genre + donnees
    return struct.pack(">I", len(donnees)) + corps + struct.pack(">I", zlib.crc32(corps) & 0xFFFFFFFF)


@functools.lru_cache(maxsize=16)
def _icone_png(taille, couleur):
    """Une icône simple : un baobab blanc (houppier et gros tronc) sur la couleur choisie."""
    fond = bytes.fromhex(couleur[1:])
    blanc = b"\xff\xff\xff"
    lignes = []
    for y in range(taille):
        v = (y + 0.5) / taille
        segments = []
        if abs(v - 0.36) <= 0.20:
            demi = 0.30 * math.sqrt(max(0.0, 1 - ((v - 0.36) / 0.20) ** 2))
            segments.append((0.5 - demi, 0.5 + demi))
        if 0.50 <= v <= 0.84:
            demi = 0.08 + 0.08 * (v - 0.50) / 0.34
            segments.append((0.5 - demi, 0.5 + demi))
        ligne = bytearray(fond * taille)
        for debut, fin in segments:
            a, b = round(debut * taille), round(fin * taille)
            ligne[3 * a:3 * b] = blanc * (b - a)
        lignes.append(bytes(ligne))
    brut = b"".join(b"\x00" + ligne for ligne in lignes)
    return (_SIGNATURE_PNG
            + _morceau_png(b"IHDR", struct.pack(">IIBBBBB", taille, taille, 8, 2, 0, 0, 0))
            + _morceau_png(b"IDAT", zlib.compress(brut, 9))
            + _morceau_png(b"IEND", b""))


def _lire_icone(chemin):
    chemin = os.path.expanduser(str(chemin))
    if not os.path.isfile(chemin):
        raise FileNotFoundError(f"Icône introuvable : {chemin}")
    if os.path.getsize(chemin) > ICONE_MAX:
        raise ValueError(f"L'icône est trop lourde ({ICONE_MAX} octets maximum)")
    with open(chemin, "rb") as fichier:
        contenu = fichier.read()
    if contenu[:8] != _SIGNATURE_PNG or contenu[12:16] != b"IHDR":
        raise ValueError("L'icône doit être une image PNG")
    largeur, hauteur = struct.unpack(">II", contenu[16:24])
    if largeur != hauteur or largeur < 512:
        raise ValueError("L'icône doit être carrée, d'au moins 512 x 512 pixels")
    return contenu


def application_installable(nom, couleur="#2e7d32", nom_court=None, description="", icone=None,
                            fond="#ffffff", page_d_accueil="/"):
    """Rend ton site installable sur l'écran d'accueil du téléphone (application web, PWA).

        serveur.application_installable("Mes notes", couleur="#1b5e20")

    Crée toute seule : /manifest.webmanifest, /sw.js, /pwa.js, /icone-192.png, /icone-512.png
    et /hors-ligne (la page montrée sans connexion). Les pages faites avec serveur.page(...)
    reçoivent automatiquement ce qu'il faut.
    icone : une image PNG carrée d'au moins 512 pixels (sinon un petit baobab est dessiné).
    Pour que le téléphone propose l'installation, le site doit être en HTTPS (sauf en local).
    Le mode hors connexion se limite à une page d'information : rien de personnel n'est gardé.
    """
    nom = str(nom).strip()
    if not 1 <= len(nom) <= 45:
        raise ValueError("Le nom doit avoir entre 1 et 45 caractères")
    nom_court = str(nom_court).strip() if nom_court else nom[:12]
    if not 1 <= len(nom_court) <= 12:
        raise ValueError("Le nom court doit avoir entre 1 et 12 caractères")
    for valeur in (couleur, fond):
        if not _COULEUR.match(str(valeur)):
            raise ValueError("Une couleur s'écrit comme #2e7d32 (# et 6 chiffres ou lettres a-f)")
    if len(str(description)) > 300:
        raise ValueError("La description ne doit pas dépasser 300 caractères")
    accueil = str(page_d_accueil)
    if not accueil.startswith("/") or accueil.startswith("//") or any(c in accueil for c in "\r\n\\"):
        raise ValueError("page_d_accueil doit être une adresse de ton site, comme « / »")
    image = _lire_icone(icone) if icone else None

    version = hashlib.sha256(f"{nom}|{couleur}|{fond}".encode("utf-8")).hexdigest()[:8]
    manifeste = json.dumps({
        "name": nom, "short_name": nom_court, "description": str(description),
        "start_url": accueil, "scope": "/", "display": "standalone", "lang": "fr",
        "background_color": fond, "theme_color": couleur,
        "icons": [{"src": "/icone-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
                  {"src": "/icone-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"}],
    }, ensure_ascii=False)
    ouvrier = f'''const VERSION = "baobab-{version}";
const HORS_LIGNE = "/hors-ligne";
self.addEventListener("install", (e) => {{
  e.waitUntil(caches.open(VERSION).then((c) => c.add(HORS_LIGNE)).then(() => self.skipWaiting()));
}});
self.addEventListener("activate", (e) => {{
  e.waitUntil(caches.keys()
    .then((noms) => Promise.all(noms.filter((n) => n !== VERSION).map((n) => caches.delete(n))))
    .then(() => self.clients.claim()));
}});
self.addEventListener("fetch", (e) => {{
  if (e.request.mode === "navigate") {{
    e.respondWith(fetch(e.request).catch(() => caches.match(HORS_LIGNE)));
  }}
}});
'''
    enregistrement = ("if ('serviceWorker' in navigator) {\n"
                      "  window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js'));\n}\n")

    def icone_de(taille):
        return lambda: repondre(image if image else _icone_png(taille, couleur), type_contenu="image/png",
                                entetes={"Cache-Control": "public, max-age=86400"})

    def page_hors_ligne():
        return page("Hors ligne", modele(
            "<h1>Pas de connexion</h1><p>{{nom}} a besoin d'Internet pour fonctionner. "
            "Réessaie quand ta connexion sera revenue.</p><p><a href='{{accueil}}'>Réessayer</a></p>",
            {"nom": nom, "accueil": accueil}))

    _pwa.clear()
    _pwa.update({"nom": nom, "couleur": couleur})
    sans_cache = {"Cache-Control": "no-cache"}
    for adresse, fonction in (
            ("/manifest.webmanifest", lambda: repondre(manifeste, type_contenu="application/manifest+json",
                                                       entetes=sans_cache)),
            ("/sw.js", lambda: repondre(ouvrier, type_contenu="application/javascript; charset=utf-8",
                                        entetes=sans_cache)),
            ("/pwa.js", lambda: repondre(enregistrement, type_contenu="application/javascript; charset=utf-8",
                                         entetes=sans_cache)),
            ("/icone-192.png", icone_de(192)),
            ("/icone-512.png", icone_de(512)),
            ("/hors-ligne", page_hors_ligne)):
        route(adresse, fonction, methodes=["GET"])
