"""Module fichiers : lire et écrire des fichiers texte."""

import os


def lire(chemin):
    with open(chemin, encoding="utf-8") as f:
        return f.read()


def lire_lignes(chemin):
    return lire(chemin).splitlines()


def ecrire(chemin, texte):
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(str(texte))


def ajouter_texte(chemin, texte):
    with open(chemin, "a", encoding="utf-8") as f:
        f.write(str(texte))


def ajouter_ligne(chemin, texte):
    ajouter_texte(chemin, str(texte) + "\n")


def existe(chemin):
    return os.path.exists(chemin)


def supprimer(chemin):
    os.remove(chemin)


def lister(dossier="."):
    return sorted(os.listdir(dossier))


def taille(chemin):
    return os.path.getsize(chemin)
