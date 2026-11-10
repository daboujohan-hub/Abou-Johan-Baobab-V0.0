"""Module donnees : lire et écrire du JSON et des tableaux CSV.

    importer donnees

    eleves = [{"nom": "Awa", "note": 15}]
    donnees.ecrire_json("eleves.json", eleves)
    afficher(donnees.lire_json("eleves.json"))
"""

import csv
import json
import os
import re


JSON_PROFONDEUR_MAX = 100
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


def vers_json(valeur):
    """Transforme une liste ou un dictionnaire en texte JSON."""
    return json.dumps(valeur, ensure_ascii=False)


def depuis_json(texte):
    """Transforme un texte JSON en liste, dictionnaire, nombre..."""
    if isinstance(texte, (bytes, bytearray)):
        verifie = bytes(texte).decode("utf-8", "replace")
    else:
        verifie = texte
    if isinstance(verifie, str) and not _json_pas_trop_profond(verifie):
        raise ValueError("Le JSON est trop profond (maximum " + str(JSON_PROFONDEUR_MAX) + " niveaux)")
    return json.loads(texte)


def lire_json(chemin):
    with open(chemin, encoding="utf-8") as fichier:
        return depuis_json(fichier.read())


def ecrire_json(chemin, valeur):
    """Écrit en JSON lisible. Le fichier est remplacé d'un seul coup :
    jamais de fichier à moitié écrit si le programme s'arrête."""
    temporaire = f"{chemin}.tmp"
    try:
        with open(temporaire, "w", encoding="utf-8") as fichier:
            json.dump(valeur, fichier, ensure_ascii=False, indent=2)
        os.replace(temporaire, chemin)
    finally:
        if os.path.exists(temporaire):
            os.remove(temporaire)


def lire_csv(chemin, separateur=","):
    """Lit un tableau CSV : une liste de dictionnaires.

    La 1re ligne donne les noms des colonnes. Toutes les valeurs sont du texte.
    Pour les fichiers Excel français, utilise le séparateur ";".
    """
    with open(chemin, encoding="utf-8-sig", newline="") as fichier:
        return [dict(ligne) for ligne in csv.DictReader(fichier, delimiter=separateur)]


def ecrire_csv(chemin, lignes, separateur=","):
    """Écrit une liste de dictionnaires dans un tableau CSV."""
    colonnes = []
    for ligne in lignes:
        for nom in ligne:
            if nom not in colonnes:
                colonnes.append(nom)
    with open(chemin, "w", encoding="utf-8", newline="") as fichier:
        ecrivain = csv.DictWriter(fichier, fieldnames=colonnes,
                                  delimiter=separateur, restval="")
        ecrivain.writeheader()
        ecrivain.writerows(lignes)
