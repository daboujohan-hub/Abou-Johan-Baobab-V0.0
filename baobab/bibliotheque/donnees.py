"""Module donnees : lire et écrire du JSON et des tableaux CSV.

    importer donnees

    eleves = [{"nom": "Awa", "note": 15}]
    donnees.ecrire_json("eleves.json", eleves)
    afficher(donnees.lire_json("eleves.json"))
"""

import csv
import json
import os


def vers_json(valeur):
    """Transforme une liste ou un dictionnaire en texte JSON."""
    return json.dumps(valeur, ensure_ascii=False)


def depuis_json(texte):
    """Transforme un texte JSON en liste, dictionnaire, nombre..."""
    return json.loads(texte)


def lire_json(chemin):
    with open(chemin, encoding="utf-8") as fichier:
        return json.load(fichier)


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
