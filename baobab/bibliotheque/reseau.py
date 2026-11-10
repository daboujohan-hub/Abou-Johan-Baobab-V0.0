"""Module reseau : aller chercher des choses sur Internet, et en envoyer.

    importer reseau

    page = reseau.telecharger_texte("https://example.org")
    infos = reseau.telecharger_json("https://api.github.com/repos/python/cpython")
    reseau.telecharger_fichier("https://example.org/image.png", "image.png")

    reponse = reseau.envoyer_json("https://exemple.org/api", {"nom": "Awa"},
                                  entetes={"Authorization": "Bearer ..."})
    texte = reseau.envoyer_formulaire("https://exemple.org/contact", {"nom": "Awa"})

Seules les adresses http:// et https:// sont acceptées (jamais file://).
Tes en-têtes personnalisés (jetons, clés...) ne suivent jamais une redirection vers un autre site.
"""

import ipaddress
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

DELAI = 10                              # secondes d'attente maximum
TAILLE_MAX_TEXTE = 5 * 1024 * 1024      # 5 Mo
TAILLE_MAX_FICHIER = 100 * 1024 * 1024  # 100 Mo
JSON_PROFONDEUR_MAX = 100               # niveaux acceptés dans un JSON reçu
METHODES_ENVOI = ("POST", "PUT", "PATCH", "DELETE")
_SECRETS_TOUJOURS = ("Authorization", "Cookie", "Proxy-authorization")


class ErreurReseau(OSError):
    """Le site n'a pas répondu comme prévu (pas de connexion, page introuvable...)."""


def _verifier(url):
    adresse = str(url)
    if urllib.parse.urlparse(adresse).scheme not in ("http", "https"):
        raise ValueError(
            "Seules les adresses qui commencent par http:// ou https:// sont acceptées")
    return adresse


def _origine(url):
    """(schéma, site, port) : deux adresses du même site ont la même origine."""
    p = urllib.parse.urlsplit(url)
    port = p.port or {"http": 80, "https": 443}.get(p.scheme)
    return (p.scheme, (p.hostname or "").lower(), port)


class _SuiviRedirections(urllib.request.HTTPRedirectHandler):
    """Suit les redirections, mais n'envoie jamais tes secrets à un autre site."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        nouvelle = super().redirect_request(req, fp, code, msg, headers, newurl)
        if nouvelle is None:
            return None
        secrets = getattr(req, "_secrets", set())
        nouvelle._secrets = secrets
        if _origine(req.full_url) != _origine(newurl):
            if code in (307, 308) and req.data is not None:
                fp.close()
                raise ErreurReseau(
                    "Redirection refusée : tes données auraient été envoyées à un autre site")
            for nom in secrets:
                nouvelle.headers.pop(nom, None)
                nouvelle.unredirected_hdrs.pop(nom, None)
        return nouvelle


_OUVREUR = urllib.request.build_opener(_SuiviRedirections)


def _preparer_entetes(entetes):
    if entetes is None:
        return {}
    if not isinstance(entetes, dict):
        raise TypeError('Les en-têtes doivent être un dictionnaire : {"Nom": "valeur"}')
    propres = {}
    for nom, valeur in entetes.items():
        nom, valeur = str(nom), str(valeur)
        if (not nom or ":" in nom or any(c.isspace() for c in nom)
                or "\r" in valeur or "\n" in valeur):
            raise ValueError(
                "En-tête invalide : pas d'espace ni de « : » dans le nom, "
                "pas de retour à la ligne dans la valeur")
        propres[nom] = valeur
    return propres


def _est_local(url):
    """Vrai pour localhost, 127.x.x.x et ::1 (ton propre appareil)."""
    hote = (urllib.parse.urlsplit(url).hostname or "").lower()
    if hote == "localhost" or hote.endswith(".localhost"):
        return True
    try:
        return ipaddress.ip_address(hote).is_loopback
    except ValueError:
        return False


def _refuser_secret_en_clair(url, entetes):
    """Pas de secret (jeton, cookie) sur http:// : il serait lisible par n'importe qui sur le réseau."""
    if urllib.parse.urlsplit(url).scheme != "http" or _est_local(url):
        return
    interdits = {nom.lower() for nom in _SECRETS_TOUJOURS}
    trouves = [nom for nom in entetes if nom.lower() in interdits]
    if trouves:
        raise ValueError(
            "Refusé : l'en-tête secret (" + ", ".join(trouves) + ") ne part pas sur une adresse "
            "http:// : n'importe qui sur le réseau pourrait le lire. Utilise https://")


def _ouvrir(url, delai, entetes=None, donnees=None, type_contenu=None, methode=None):
    from baobab import __version__

    propres = _preparer_entetes(entetes)
    _refuser_secret_en_clair(_verifier(url), propres)
    envoyes = {"User-Agent": f"Baobab/{__version__}", "Accept": "*/*"}
    envoyes.update(propres)
    if type_contenu and not any(nom.lower() == "content-type" for nom in propres):
        envoyes["Content-Type"] = type_contenu
    requete = urllib.request.Request(
        _verifier(url), data=donnees, headers=envoyes, method=methode)
    requete._secrets = {nom.capitalize() for nom in propres} | set(_SECRETS_TOUJOURS)
    try:
        if propres or donnees is not None:
            return _OUVREUR.open(requete, timeout=delai)
        return urllib.request.urlopen(requete, timeout=delai)
    except ErreurReseau:
        raise
    except urllib.error.HTTPError as erreur:
        erreur.close()
        raise ErreurReseau(f"Le site a répondu : {erreur.code} {erreur.reason}") from None
    except OSError as erreur:
        raison = getattr(erreur, "reason", erreur)
        raise ErreurReseau(
            f"Impossible de joindre {url} ({raison}). Vérifie ta connexion Internet."
        ) from None


def _lire_texte(reponse):
    contenu = reponse.read(TAILLE_MAX_TEXTE + 1)
    if len(contenu) > TAILLE_MAX_TEXTE:
        raise ErreurReseau(
            f"La réponse dépasse la taille autorisée ({TAILLE_MAX_TEXTE} octets)")
    encodage = reponse.headers.get_content_charset() or "utf-8"
    try:
        return contenu.decode(encodage, errors="replace")
    except LookupError:
        return contenu.decode("utf-8", errors="replace")


_STRUCTURE_JSON = re.compile(r'"(?:[^"\\]|\\.)*"|[\[\]{}]')


def _json_pas_trop_profond(texte, maximum=JSON_PROFONDEUR_MAX):
    """Faux si le JSON a plus de `maximum` niveaux (les crochets dans les textes ne comptent pas)."""
    profondeur = 0
    for morceau in _STRUCTURE_JSON.finditer(texte):
        signe = morceau.group()
        if signe == "[" or signe == "{":
            profondeur += 1
            if profondeur > maximum:
                return False
        elif signe == "]" or signe == "}":
            profondeur -= 1
    return True


def _charger_json(texte):
    if not _json_pas_trop_profond(texte):
        raise ErreurReseau("La réponse JSON est trop profonde pour être lue sans risque")
    return json.loads(texte)


def telecharger_texte(url, delai=DELAI, entetes=None):
    """Le texte d'une page ou d'un fichier texte. entetes : {"Nom": "valeur"} en plus."""
    with _ouvrir(url, delai, entetes) as reponse:
        return _lire_texte(reponse)


def telecharger_json(url, delai=DELAI, entetes=None):
    """Va chercher du JSON et le transforme en liste ou dictionnaire."""
    return _charger_json(telecharger_texte(url, delai, entetes))


def telecharger_fichier(url, chemin, taille_max=TAILLE_MAX_FICHIER, delai=DELAI, entetes=None):
    """Enregistre le fichier dans `chemin`. Retourne sa taille en octets.

    Le fichier n'apparaît que s'il est complet : jamais de fichier à moitié reçu.
    """
    temporaire = f"{chemin}.part"
    total = 0
    try:
        with _ouvrir(url, delai, entetes) as reponse, open(temporaire, "wb") as sortie:
            while True:
                morceau = reponse.read(64 * 1024)
                if not morceau:
                    break
                total += len(morceau)
                if total > taille_max:
                    raise ErreurReseau(
                        f"Le fichier dépasse la taille autorisée ({taille_max} octets)")
                sortie.write(morceau)
        os.replace(temporaire, chemin)
    finally:
        if os.path.exists(temporaire):
            os.remove(temporaire)
    return total


def _envoyer(url, corps, type_contenu, entetes, delai, methode):
    verbe = str(methode).upper()
    if verbe not in METHODES_ENVOI:
        raise ValueError("Méthode non permise pour envoyer : " + ", ".join(METHODES_ENVOI))
    with _ouvrir(url, delai, entetes, corps, type_contenu, verbe) as reponse:
        return _lire_texte(reponse)


def envoyer_json(url, donnees, entetes=None, delai=DELAI, methode="POST"):
    """Envoie `donnees` en JSON. Retourne la réponse en liste ou dictionnaire (ou rien si vide).

    methode : "POST" (par défaut), "PUT", "PATCH" ou "DELETE".
    """
    corps = json.dumps(donnees, ensure_ascii=False).encode("utf-8")
    texte = _envoyer(url, corps, "application/json; charset=utf-8", entetes, delai, methode)
    if not texte.strip():
        return None
    return _charger_json(texte)


def envoyer_formulaire(url, donnees, entetes=None, delai=DELAI, methode="POST"):
    """Envoie un formulaire ({"nom": "valeur"}). Retourne le texte de la réponse."""
    if not isinstance(donnees, dict):
        raise TypeError('Le formulaire doit être un dictionnaire : {"nom": "valeur"}')
    corps = urllib.parse.urlencode(donnees).encode("ascii")
    return _envoyer(url, corps, "application/x-www-form-urlencoded", entetes, delai, methode)


def est_en_ligne(url, delai=5):
    """Vrai si le site répond sans erreur. Ne provoque jamais d'erreur."""
    try:
        with _ouvrir(url, delai):
            return True
    except (ErreurReseau, ValueError):
        return False


def encoder_adresse(parametres):
    """encoder_adresse({"q": "baobab", "page": 2}) donne 'q=baobab&page=2'"""
    return urllib.parse.urlencode(parametres)
