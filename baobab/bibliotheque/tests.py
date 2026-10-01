"""Module tests : vérifier qu'une application fonctionne.

    importer tests

    fonction test_addition():
        tests.egal(2 + 2, 4)

Lance les tests avec :  baobab tester mon_fichier_de_tests.bao
"""

import http.client
import json
import threading
import urllib.parse

_serveur = None
_verrou = threading.Lock()


def _court(valeur, limite=200):
    texte = repr(valeur)
    return texte if len(texte) <= limite else texte[:limite] + "…"


def _echec(message):
    raise AssertionError(message)


def egal(obtenu, attendu):
    if obtenu != attendu:
        _echec(f"Attendu {_court(attendu)} mais obtenu {_court(obtenu)}")


def different(a, b):
    if a == b:
        _echec(f"Les deux valeurs sont égales : {_court(a)}")


def est_vrai(valeur):
    if not valeur:
        _echec(f"Attendu une valeur vraie mais obtenu {_court(valeur)}")


def est_faux(valeur):
    if valeur:
        _echec(f"Attendu une valeur fausse mais obtenu {_court(valeur)}")


def contient(ensemble, element):
    if element not in ensemble:
        _echec(f"{_court(element)} est introuvable dans {_court(ensemble)}")


def ne_contient_pas(ensemble, element):
    if element in ensemble:
        _echec(f"{_court(element)} ne devrait pas se trouver dans {_court(ensemble)}")


def proche(a, b, marge=0.001):
    if abs(a - b) > marge:
        _echec(f"{a} et {b} sont différents (marge autorisée : {marge})")


def leve_erreur(fonction, classe=Exception):
    """Vérifie que la fonction (sans argument) provoque bien cette erreur."""
    try:
        fonction()
    except classe:
        return
    except Exception as erreur:
        _echec(f"Attendu une erreur {classe.__name__} mais {type(erreur).__name__} est survenue")
    _echec(f"Attendu une erreur {classe.__name__} mais rien ne s'est passé")


class Reponse:
    """Ce que ton application a répondu : code, texte, adresse (redirection)."""

    def __init__(self, code, texte, adresse):
        self.code = code
        self.texte = texte
        self.adresse = adresse

    def json(self):
        return json.loads(self.texte)

    def __repr__(self):
        return f"Reponse(code={self.code}, adresse={self.adresse!r})"


def _obtenir_serveur():
    global _serveur
    with _verrou:
        if _serveur is None:
            from . import serveur

            serveur.SILENCIEUX = True
            _serveur = serveur._creer("127.0.0.1", 0)
            threading.Thread(target=_serveur.serve_forever, daemon=True).start()
        return _serveur


def requete(chemin, donnees=None):
    """Visite une page de ton application, sans navigateur.

    Sans données : visite (GET).  Avec un dictionnaire : envoie un formulaire (POST).
    """
    port = _obtenir_serveur().server_address[1]
    connexion = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        if donnees is None:
            connexion.request("GET", chemin)
        else:
            connexion.request(
                "POST", chemin, body=urllib.parse.urlencode(donnees),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        reponse = connexion.getresponse()
        texte = reponse.read().decode("utf-8")
        return Reponse(reponse.status, texte, reponse.getheader("Location"))
    finally:
        connexion.close()
