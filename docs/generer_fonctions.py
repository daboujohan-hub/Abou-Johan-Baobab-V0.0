"""Génère docs/fonctions.md : les précautions, puis la liste de toutes les fonctions de Baobab.

Lancer : python docs/generer_fonctions.py
"""
import importlib
import inspect
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

import baobab  # enregistre les modules

DOSSIER = os.path.join(RACINE, "baobab", "bibliotheque")
SORTIE = os.path.join(RACINE, "docs", "fonctions.md")

# Les fonctions citées dans les précautions : le test vérifie qu'elles existent et sont citées.
DANGEREUSES = [
    "avance.evaluer", "avance.executer_texte", "avance.compiler_texte",
    "fichiers.supprimer", "fichiers.ecrire", "donnees.ecrire_json", "donnees.ecrire_csv",
    "dessin.sauvegarder",
    "reseau.telecharger_texte", "reseau.telecharger_json", "reseau.telecharger_fichier",
    "reseau.envoyer_json", "reseau.envoyer_formulaire", "reseau.est_en_ligne",
    "base.executer", "base.chercher", "base.inserer",
    "serveur.demarrer", "serveur.dossier_public", "serveur.modele",
    "serveur.autoriser_origines", "serveur.documenter",
    "securite.hacher_mot_de_passe", "securite.signer", "securite.creer_jeton_acces",
    "taches.toutes_les", "taches.chaque_jour",
]

ENTETE = r"""# Fonctions de Baobab

Cette page liste les __TOTAL__ noms publics (fonctions et classes) des __MODULES__ modules de la
bibliothèque. Elle est **générée** : ne modifie pas la liste à la main. Change le code ou son texte
d'aide, puis lance `python docs/generer_fonctions.py`.

Pour utiliser un module : `importer nom_du_module`, puis `nom_du_module.fonction(...)`.

"""

PRECAUTIONS = r"""# À utiliser avec précaution

Règle d'or : tout ce qui vient d'un visiteur (formulaire, adresse, JSON, fichier reçu) est dangereux
tant qu'on ne l'a pas vérifié. Pour le vérifier : `serveur.valider`.

## Exécuter du code

- `avance.evaluer`, `avance.executer_texte` et `avance.compiler_texte` exécutent du VRAI code avec tes
  droits. Ce n'est pas un bac à sable. Jamais avec un texte venu d'un visiteur, d'une API ou d'un
  fichier inconnu.
- Pour lire une valeur reçue, utilise `avance.lire_valeur` (elle ne comprend que nombres, textes,
  listes, dictionnaires, vrai et faux) ou `donnees.depuis_json`.

## Fichiers

- `fichiers.supprimer` supprime pour de bon, sans corbeille. D'après le code, elle appelle directement
  `os.remove` sur le chemin donné.
- `fichiers.ecrire`, `donnees.ecrire_json`, `donnees.ecrire_csv` et `dessin.sauvegarder` remplacent un
  fichier qui existe déjà, sans demander.
- Un chemin fabriqué avec un texte du visiteur (par exemple `../`) peut sortir du dossier prévu.
  N'accepte que des noms choisis dans une liste que tu as écrite.

## Réseau

- `reseau.telecharger_texte`, `reseau.telecharger_json`, `reseau.telecharger_fichier` et
  `reseau.est_en_ligne` vont sur n'importe quelle adresse http ou https, y compris celles de ton propre
  appareil ou de ton réseau (127.0.0.1, la box...). Baobab ne les filtre pas : ne fabrique jamais
  l'adresse avec un texte du visiteur.
- `reseau.telecharger_fichier` écrit à l'endroit demandé (100 Mo au maximum) : même précaution que pour
  les fichiers.
- `reseau.envoyer_json` et `reseau.envoyer_formulaire` envoient tes données à un site : vérifie
  l'adresse. Les en-têtes secrets (Authorization, Cookie) sont refusés sur une adresse http:// qui
  n'est pas locale, et ne suivent pas une redirection vers un autre site. Une clé mise dans un en-tête
  que tu inventes toi-même, elle, n'est pas protégée.

## Base de données

- `base.executer` et `base.chercher` lancent du SQL : ne colle jamais un texte dans l'ordre SQL, passe
  les valeurs par le paramètre `valeurs`.
- `base.inserer` : le nom de la table n'est pas une valeur. Ne le prends jamais d'un visiteur.

## Serveur web

- `serveur.demarrer` : avec `hote="0.0.0.0"`, toutes les personnes du même Wi-Fi atteignent ton
  serveur. Garde `127.0.0.1` pour tes essais.
- `serveur.dossier_public` rend public tout ce qui est dans le dossier : jamais la racine du projet ni
  un dossier qui contient des clés ou des données.
- `serveur.modele` : le marqueur `|brut` coupe la protection HTML. Seulement pour du HTML que tu as
  fabriqué toi-même, jamais pour du texte de visiteur.
- `serveur.autoriser_origines` : avec `avec_cookies=True`, ne liste que tes propres sites.
- `serveur.documenter` montre toutes les routes et leurs textes d'aide à qui ouvre la page. N'y mets
  ni secret ni adresse privée, et cache des routes avec `masquer=`.
- Le serveur est éducatif : pas de HTTPS intégré, sessions gardées en mémoire, pas de jeton anti-CSRF.
  Ne l'expose pas sur Internet et ne l'utilise pas pour des données bancaires ou de santé.

## Mots de passe, jetons et clés

- `securite.hacher_mot_de_passe` : garde seulement l'empreinte, jamais le mot de passe.
- `securite.creer_jeton_acces` et `securite.signer` signent mais ne chiffrent pas : le contenu est
  lisible par tous. N'y mets aucun secret. Un jeton ne peut pas être annulé avant sa fin : donne-lui une
  durée courte.
- La clé de signature est un secret : jamais écrite dans un code envoyé sur GitHub.

## Tâches en arrière-plan

- `taches.toutes_les` et `taches.chaque_jour` continuent de tourner tant qu'on ne les arrête pas. Une
  tâche mal écrite se répète sans fin (batterie, disque, réseau). Utilise `taches.lister` pour voir ce
  qui tourne et `taches.tout_annuler` pour tout arrêter.

"""


def inventaire():
    noms = sorted(f[:-3] for f in os.listdir(DOSSIER)
                  if f.endswith(".py") and not f.startswith("_"))
    resultat = []
    for nom in noms:
        m = importlib.import_module("baobab.bibliotheque." + nom)
        elements = []
        for n, o in sorted(vars(m).items()):
            if n.startswith("_") or not callable(o) or getattr(o, "__module__", None) != m.__name__:
                continue
            try:
                signature = str(inspect.signature(o))
            except (TypeError, ValueError):
                signature = "()"
            resume = (inspect.getdoc(o) or "").strip().split("\n")[0]
            elements.append((n, signature, resume))
        resultat.append((nom, elements))
    return resultat


def generer():
    inv = inventaire()
    total = sum(len(elements) for _, elements in inv)
    texte = ENTETE.replace("__TOTAL__", str(total)).replace("__MODULES__", str(len(inv)))
    texte += PRECAUTIONS + "# Toutes les fonctions\n\n"
    for nom, elements in inv:
        texte += "## {} ({})\n\n".format(nom, len(elements))
        for n, signature, resume in elements:
            ligne = "- `{}.{}{}`".format(nom, n, signature)
            if resume:
                ligne += " : " + resume
            texte += ligne + "\n"
        texte += "\n"
    return texte, total, len(inv)


if __name__ == "__main__":
    texte, total, modules = generer()
    with open(SORTIE, "w", encoding="utf-8") as f:
        f.write(texte)
    print("docs/fonctions.md :", total, "noms,", modules, "modules")
