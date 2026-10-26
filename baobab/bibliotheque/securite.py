"""Module securite : protéger les mots de passe et les données sensibles.

    importer securite

    empreinte = securite.hacher_mot_de_passe("mon mot de passe")   # à garder dans ta base
    securite.verifier_mot_de_passe("mon mot de passe", empreinte)  # vrai

Règle d'or : on ne garde JAMAIS un mot de passe, seulement son empreinte.
"""

import base64
import hashlib
import hmac
import secrets
import time
import unicodedata

ALGORITHME = "pbkdf2_sha256"
ITERATIONS = 600_000        # plus c'est grand, plus c'est lent à casser (et à vérifier)
MOT_DE_PASSE_MAX = 1024


def _octets(mot_de_passe):
    if not isinstance(mot_de_passe, str):
        raise TypeError("Le mot de passe doit être un texte")
    if mot_de_passe == "":
        raise ValueError("Le mot de passe est vide")
    if len(mot_de_passe) > MOT_DE_PASSE_MAX:
        raise ValueError(f"Le mot de passe est trop long ({MOT_DE_PASSE_MAX} caractères maximum)")
    return unicodedata.normalize("NFKC", mot_de_passe).encode("utf-8")


def hacher_mot_de_passe(mot_de_passe):
    """Transforme un mot de passe en empreinte, impossible à ramener au mot de passe.

    L'empreinte contient un « sel » au hasard : deux personnes qui ont le même mot de
    passe n'ont pas la même empreinte.
    """
    sel = secrets.token_bytes(16)
    empreinte = hashlib.pbkdf2_hmac("sha256", _octets(mot_de_passe), sel, ITERATIONS)
    return f"{ALGORITHME}${ITERATIONS}${sel.hex()}${empreinte.hex()}"


def verifier_mot_de_passe(mot_de_passe, empreinte):
    """Vrai si ce mot de passe correspond à l'empreinte. Ne provoque jamais d'erreur.

    Astuce : si l'utilisateur n'existe pas, vérifie quand même contre une fausse
    empreinte, pour ne pas révéler (par le temps de réponse) quels comptes existent.
    """
    try:
        algorithme, iterations, sel_hex, empreinte_hex = str(empreinte).split("$")
        if algorithme != ALGORITHME:
            return False
        iterations = int(iterations)
        if not 1 <= iterations <= 10_000_000:
            return False
        sel = bytes.fromhex(sel_hex)
        attendue = bytes.fromhex(empreinte_hex)
        calculee = hashlib.pbkdf2_hmac(
            "sha256", _octets(mot_de_passe), sel, iterations, dklen=len(attendue))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(calculee, attendue)


def jeton_aleatoire(octets=32):
    """Un code secret impossible à deviner (liens de réinitialisation, invitations, clés)."""
    if octets < 16:
        raise ValueError("Un jeton de moins de 16 octets n'est pas assez sûr")
    return secrets.token_urlsafe(octets)


def _cle_en_octets(cle):
    valeur = cle.encode("utf-8") if isinstance(cle, str) else bytes(cle)
    if len(valeur) < 16:
        raise ValueError(
            "La clé est trop courte (16 caractères minimum). "
            "Fabrique-en une avec securite.jeton_aleatoire()")
    return valeur


def _vers_texte(octets):
    return base64.urlsafe_b64encode(octets).decode("ascii").rstrip("=")


def _depuis_texte(texte):
    return base64.urlsafe_b64decode(texte + "=" * (-len(texte) % 4))


def _calculer_signature(cle, message):
    return hmac.new(cle, message.encode("ascii"), hashlib.sha256).hexdigest()


def signer(valeur, cle, duree=None):
    """Ajoute une signature : si quelqu'un modifie la valeur, on le détectera.

    duree : nombre de secondes pendant lesquelles la signature reste valable (facultatif).
    La clé doit rester SECRÈTE : garde-la hors de ton code (variable d'environnement).
    """
    cle = _cle_en_octets(cle)
    expiration = int(time.time() + duree) if duree else 0
    message = f"{_vers_texte(str(valeur).encode('utf-8'))}.{expiration}"
    return f"{message}.{_calculer_signature(cle, message)}"


def verifier_signature(texte_signe, cle):
    """Retourne la valeur d'origine si la signature est bonne, sinon None (rien).

    None veut dire : modifiée, fausse, périmée ou signée avec une autre clé.
    """
    cle = _cle_en_octets(cle)
    try:
        corps, expiration, signature = str(texte_signe).split(".")
        attendue = _calculer_signature(cle, f"{corps}.{expiration}")
        if not hmac.compare_digest(signature, attendue):
            return None
        if int(expiration) and time.time() > int(expiration):
            return None
        return _depuis_texte(corps).decode("utf-8")
    except (ValueError, TypeError, UnicodeError):
        return None


# ------------------------------------------------------- jetons d'accès

import json as _json  # noqa: E402  (pour les jetons d'accès ci-dessous)


def creer_jeton_acces(identite, cle, duree=3600, droits=()):
    """Fabrique un jeton d'accès pour une application (envoyé dans « Authorization: Bearer ... »).

        jeton = securite.creer_jeton_acces("awa", CLE, 3600, ["lecture", "ecriture"])

    identite : à qui appartient le jeton.   duree : secondes de validité (obligatoire : un jeton
    sans fin de validité est dangereux).   droits : ce que le jeton permet de faire.
    Le contenu est signé mais PAS caché : n'y mets aucun secret. Un jeton ne peut pas être
    annulé avant sa fin : garde une durée courte.
    """
    if not duree or duree <= 0:
        raise ValueError("Un jeton d'accès doit avoir une durée de validité positive (en secondes)")
    contenu = {"i": str(identite), "d": sorted({str(droit) for droit in droits})}
    return signer(_json.dumps(contenu, ensure_ascii=False, separators=(",", ":")), cle, duree)


def verifier_jeton_acces(jeton, cle):
    """Retourne {"identite": ..., "droits": [...]} si le jeton est bon, sinon None.

    None veut dire : modifié, faux, périmé, ou fabriqué avec une autre clé.
    """
    texte = verifier_signature(jeton, cle)
    if texte is None:
        return None
    try:
        contenu = _json.loads(texte)
    except ValueError:
        return None
    if not isinstance(contenu, dict) or not isinstance(contenu.get("i"), str):
        return None
    droits = contenu.get("d", [])
    if not isinstance(droits, list):
        return None
    return {"identite": contenu["i"], "droits": [str(droit) for droit in droits]}


# ------------------------------------------------------- jetons d'accès

import json as _json  # noqa: E402  (pour les jetons d'accès ci-dessous)


def creer_jeton_acces(identite, cle, duree=3600, droits=()):
    """Fabrique un jeton d'accès pour une application (envoyé dans « Authorization: Bearer ... »).

        jeton = securite.creer_jeton_acces("awa", CLE, 3600, ["lecture", "ecriture"])

    identite : à qui appartient le jeton.   duree : secondes de validité (obligatoire : un jeton
    sans fin de validité est dangereux).   droits : ce que le jeton permet de faire.
    Le contenu est signé mais PAS caché : n'y mets aucun secret. Un jeton ne peut pas être
    annulé avant sa fin : garde une durée courte.
    """
    if not duree or duree <= 0:
        raise ValueError("Un jeton d'accès doit avoir une durée de validité positive (en secondes)")
    contenu = {"i": str(identite), "d": sorted({str(droit) for droit in droits})}
    return signer(_json.dumps(contenu, ensure_ascii=False, separators=(",", ":")), cle, duree)


def verifier_jeton_acces(jeton, cle):
    """Retourne {"identite": ..., "droits": [...]} si le jeton est bon, sinon None.

    None veut dire : modifié, faux, périmé, ou fabriqué avec une autre clé.
    """
    texte = verifier_signature(jeton, cle)
    if texte is None:
        return None
    try:
        contenu = _json.loads(texte)
    except ValueError:
        return None
    if not isinstance(contenu, dict) or not isinstance(contenu.get("i"), str):
        return None
    droits = contenu.get("d", [])
    if not isinstance(droits, list):
        return None
    return {"identite": contenu["i"], "droits": [str(droit) for droit in droits]}
