"""Module tests : vérifier qu'une application fonctionne.

    importer tests

    fonction test_addition():
        tests.egal(2 + 2, 4)

    fonction test_connexion():
        nav = tests.navigateur()                       # un faux navigateur qui garde les cookies
        reponse = nav.requete("/connexion", {"nom": "awa", "mot_de_passe": "secret123"})
        tests.egal(reponse.code, 303)

Lance les tests avec :  baobab tester mon_fichier_de_tests.bao
"""

import http.client
import json
import threading
import urllib.parse
from http.cookies import CookieError, SimpleCookie

_serveur = None
_verrou = threading.Lock()
REDIRECTIONS_MAX = 5


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
    """Ce que ton application a répondu.

    code, texte, adresse (redirection), entetes (noms en minuscules),
    cookies ({nom: valeur} posés par le site), cookies_effaces, cookies_bruts.
    """

    def __init__(self, code, texte, adresse, entetes=None, cookies_bruts=None):
        self.code = code
        self.texte = texte
        self.adresse = adresse
        self.entetes = entetes or {}
        self.cookies_bruts = list(cookies_bruts or [])
        self.cookies, self.cookies_effaces = _lire_set_cookie(self.cookies_bruts)

    def json(self):
        return json.loads(self.texte)

    def __repr__(self):
        return f"Reponse(code={self.code}, adresse={self.adresse!r})"


def _lire_set_cookie(lignes):
    poses, effaces = {}, []
    for ligne in lignes:
        pot = SimpleCookie()
        try:
            pot.load(ligne)
        except CookieError:
            continue
        for nom, morceau in pot.items():
            duree = morceau["max-age"]
            try:
                efface = duree != "" and int(duree) <= 0
            except ValueError:
                efface = False
            if efface:
                effaces.append(nom)
            else:
                poses[nom] = morceau.value
    return poses, effaces


def _en_tete_cookie(cookies):
    pot = SimpleCookie()
    for nom, valeur in cookies.items():
        pot[nom] = valeur
    return "; ".join(f"{nom}={pot[nom].coded_value}" for nom in cookies)


def _obtenir_serveur():
    global _serveur
    from . import serveur

    serveur.SILENCIEUX = True  # pendant les tests, pas de messages « GET / -> 200 »
    with _verrou:
        if _serveur is None:
            _serveur = serveur._creer("127.0.0.1", 0)
            threading.Thread(target=_serveur.serve_forever, daemon=True).start()
        return _serveur


def requete(chemin, donnees=None, entetes=None, cookies=None):
    """Visite une page de ton application, sans navigateur.

    Sans données : visite (GET).  Avec un dictionnaire : envoie un formulaire (POST).
    entetes : {"Nom": "valeur"} en plus.  cookies : {"nom": "valeur"} à envoyer.
    """
    port = _obtenir_serveur().server_address[1]
    envoyes = dict(entetes or {})
    if cookies:
        envoyes["Cookie"] = _en_tete_cookie(cookies)
    connexion = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        if donnees is None:
            connexion.request("GET", chemin, headers=envoyes)
        else:
            envoyes["Content-Type"] = "application/x-www-form-urlencoded"
            connexion.request("POST", chemin, body=urllib.parse.urlencode(donnees), headers=envoyes)
        reponse = connexion.getresponse()
        texte = reponse.read().decode("utf-8")
        return Reponse(
            reponse.status, texte, reponse.getheader("Location"),
            {nom.lower(): valeur for nom, valeur in reponse.getheaders()},
            reponse.msg.get_all("Set-Cookie", []),
        )
    finally:
        connexion.close()


class Navigateur:
    """Un faux navigateur : il garde les cookies d'une requête à l'autre.

    nav.cookies : les cookies qu'il a retenus.
    """

    def __init__(self):
        self.cookies = {}

    def _retenir(self, reponse):
        self.cookies.update(reponse.cookies)
        for nom in reponse.cookies_effaces:
            self.cookies.pop(nom, None)

    def requete(self, chemin, donnees=None, entetes=None, suivre=False):
        """Comme tests.requete, avec ses cookies. suivre=vrai suit les redirections."""
        reponse = requete(chemin, donnees, entetes, self.cookies)
        self._retenir(reponse)
        redirections = 0
        while (suivre and reponse.code in (301, 302, 303, 307, 308)
               and reponse.adresse and reponse.adresse.startswith("/")
               and redirections < REDIRECTIONS_MAX):
            reponse = requete(reponse.adresse, None, entetes, self.cookies)
            self._retenir(reponse)
            redirections += 1
        return reponse


def navigateur():
    """Un faux navigateur avec ses propres cookies (un par visiteur à simuler)."""
    return Navigateur()
