"""Module reseau : aller chercher des choses sur Internet.

    importer reseau

    page = reseau.telecharger_texte("https://example.org")
    infos = reseau.telecharger_json("https://api.github.com/repos/python/cpython")
    reseau.telecharger_fichier("https://example.org/image.png", "image.png")

Seules les adresses http:// et https:// sont acceptées (jamais file://).
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

DELAI = 10                              # secondes d'attente maximum
TAILLE_MAX_TEXTE = 5 * 1024 * 1024      # 5 Mo
TAILLE_MAX_FICHIER = 100 * 1024 * 1024  # 100 Mo


class ErreurReseau(OSError):
    """Le site n'a pas répondu comme prévu (pas de connexion, page introuvable...)."""


def _verifier(url):
    adresse = str(url)
    if urllib.parse.urlparse(adresse).scheme not in ("http", "https"):
        raise ValueError(
            "Seules les adresses qui commencent par http:// ou https:// sont acceptées")
    return adresse


def _ouvrir(url, delai):
    from baobab import __version__

    requete = urllib.request.Request(
        _verifier(url), headers={"User-Agent": f"Baobab/{__version__}", "Accept": "*/*"})
    try:
        return urllib.request.urlopen(requete, timeout=delai)
    except urllib.error.HTTPError as erreur:
        erreur.close()
        raise ErreurReseau(f"Le site a répondu : {erreur.code} {erreur.reason}") from None
    except OSError as erreur:
        raison = getattr(erreur, "reason", erreur)
        raise ErreurReseau(
            f"Impossible de joindre {url} ({raison}). Vérifie ta connexion Internet."
        ) from None


def telecharger_texte(url, delai=DELAI):
    """Le texte d'une page ou d'un fichier texte."""
    with _ouvrir(url, delai) as reponse:
        contenu = reponse.read(TAILLE_MAX_TEXTE + 1)
        if len(contenu) > TAILLE_MAX_TEXTE:
            raise ErreurReseau(
                f"La réponse dépasse la taille autorisée ({TAILLE_MAX_TEXTE} octets)")
        encodage = reponse.headers.get_content_charset() or "utf-8"
    try:
        return contenu.decode(encodage, errors="replace")
    except LookupError:
        return contenu.decode("utf-8", errors="replace")


def telecharger_json(url, delai=DELAI):
    """Va chercher du JSON et le transforme en liste ou dictionnaire."""
    return json.loads(telecharger_texte(url, delai))


def telecharger_fichier(url, chemin, taille_max=TAILLE_MAX_FICHIER, delai=DELAI):
    """Enregistre le fichier dans `chemin`. Retourne sa taille en octets.

    Le fichier n'apparaît que s'il est complet : jamais de fichier à moitié reçu.
    """
    temporaire = f"{chemin}.part"
    total = 0
    try:
        with _ouvrir(url, delai) as reponse, open(temporaire, "wb") as sortie:
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
