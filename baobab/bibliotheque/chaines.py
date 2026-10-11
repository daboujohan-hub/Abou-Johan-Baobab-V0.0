"""Module chaines : travailler sur les textes (les « chaînes de caractères »).

    importer chaines

    afficher(chaines.sans_accents("Été"))               # Ete
    afficher(chaines.en_adresse("Mon Super Titre !"))   # mon-super-titre
"""

import re
import unicodedata
from collections import Counter

_LIGATURES = {"œ": "oe", "Œ": "oe", "æ": "ae", "Æ": "ae"}
_MOT = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*")   # aujourd'hui, peut-être = 1 mot
_MOT_SIMPLE = re.compile(r"[^\W_]+(?:-[^\W_]+)*")  # l'été = « l » et « été »
_NOMBRE = re.compile(r"(?<![\w.,])-?\d+(?:[.,]\d+)?")

MOTS_OUTILS = {
    "les", "des", "une", "que", "qui", "dont", "cet", "cette", "ces", "ils", "elles",
    "nous", "vous", "pas", "plus", "est", "sont", "être", "avoir", "ont", "mais",
    "donc", "car", "son", "ses", "mon", "mes", "ton", "tes", "leur", "leurs", "notre",
    "votre", "très", "aussi", "comme", "tout", "tous", "dans", "sur", "sous", "pour",
    "par", "avec", "sans", "aux", "elle", "fait", "the",
}


def _remplacer_ligature(trouve):
    """œ -> oe, Œuvre -> Oeuvre, ŒUVRE -> OEUVRE"""
    lettre = trouve.group()
    remplacement = _LIGATURES[lettre]
    if lettre.isupper():
        suivante = trouve.string[trouve.end():trouve.end() + 1]
        return remplacement.upper() if suivante.isupper() else remplacement.capitalize()
    return remplacement


def sans_accents(texte):
    """sans_accents("Élève à l'été") donne "Eleve a l'ete"."""
    texte = re.sub("[œŒæÆ]", _remplacer_ligature, texte)
    decompose = unicodedata.normalize("NFD", texte)
    return "".join(c for c in decompose if not unicodedata.combining(c))


def en_adresse(texte):
    """Pour les adresses de sites : en_adresse("Mon Super Titre !") donne "mon-super-titre"."""
    simple = sans_accents(texte).lower()
    return re.sub(r"[^a-z0-9]+", "-", simple).strip("-")


def compter_mots(texte):
    """Nombre de mots. « aujourd'hui » et « peut-être » comptent pour un seul mot."""
    return len(_MOT.findall(texte))


def est_palindrome(texte):
    """Vrai si le texte se lit pareil dans les deux sens (sans accents, majuscules ni ponctuation)."""
    lettres = re.sub(r"[^a-z0-9]", "", sans_accents(texte).lower())
    return lettres != "" and lettres == lettres[::-1]


def couper(texte, longueur, fin="…"):
    """Raccourcit un texte à `longueur` caractères au plus, avec « … » à la fin."""
    if len(texte) <= longueur:
        return texte
    if longueur <= len(fin):
        return texte[:max(longueur, 0)]
    return texte[:longueur - len(fin)].rstrip() + fin


def extraire_nombres(texte):
    """Les nombres d'un texte : extraire_nombres("3 chats, 2,5 kg") donne [3, 2.5].

    La virgule ou le point sert de séparateur décimal. Un nombre collé à des lettres
    (comme « A4 ») est ignoré.
    """
    nombres = []
    for brut in _NOMBRE.findall(texte):
        if "," in brut or "." in brut:
            nombres.append(float(brut.replace(",", ".")))
        else:
            nombres.append(int(brut))
    return nombres


def mots_frequents(texte, nombre=5):
    """Les mots les plus utilisés : {mot: nombre}, sans les petits mots (le, de, et...)."""
    mots = [m.lower() for m in _MOT_SIMPLE.findall(texte)]
    utiles = [m for m in mots if len(m) >= 3 and m not in MOTS_OUTILS]
    return dict(Counter(utiles).most_common(nombre))
