"""Module avance : des fonctions puissantes, à utiliser avec précaution.

    importer avance

    avance.lire_valeur("[1, 2, vrai]")       # SÛR : seulement nombres, textes, listes, dictionnaires...
    avance.evaluer("2 + 3")                  # exécute une expression Baobab
    avance.executer_texte("a = 5")           # exécute un programme Baobab, rend ses variables
    avance.compiler_texte("2 + 3", "eval")   # prépare le code pour le lancer plus tard

evaluer, executer_texte et compiler_texte exécutent du VRAI code : ce n'est PAS un bac à sable.
N'y mets jamais un texte venu d'un visiteur, d'un formulaire, d'une API ou d'un fichier inconnu.
Pour lire une donnée reçue, utilise lire_valeur (ou donnees.depuis_json).
"""

import ast
import re

LONGUEUR_MAX_VALEUR = 100000
PROFONDEUR_MAX_VALEUR = 100
_BLOCS = re.compile(r'''"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|[\[\]{}()]''')


def _transpiler(texte):
    from baobab.transpileur import transpiler
    return transpiler(texte)


def _profondeur_ok(texte, maximum=PROFONDEUR_MAX_VALEUR):
    profondeur = 0
    for morceau in _BLOCS.finditer(texte):
        signe = morceau.group()
        if signe in ("[", "{", "("):
            profondeur += 1
            if profondeur > maximum:
                return False
        elif signe in ("]", "}", ")"):
            profondeur -= 1
    return True


def lire_valeur(texte):
    """Lit une valeur simple : nombre, texte, liste, dictionnaire, vrai, faux. Jamais de code."""
    if isinstance(texte, (bytes, bytearray)):
        texte = bytes(texte).decode("utf-8", "replace")
    if not isinstance(texte, str):
        raise TypeError("lire_valeur attend un texte")
    if len(texte) > LONGUEUR_MAX_VALEUR:
        raise ValueError("Texte trop long (maximum " + str(LONGUEUR_MAX_VALEUR) + " caractères)")
    if not _profondeur_ok(texte):
        raise ValueError("Valeur trop imbriquée (maximum " + str(PROFONDEUR_MAX_VALEUR) + " niveaux)")
    try:
        return ast.literal_eval(_transpiler(texte.strip()))
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        raise ValueError(
            "Ce texte n'est pas une valeur simple (nombre, texte, liste, dictionnaire, vrai, faux)"
        ) from None


def _espace(variables):
    if variables is None:
        return {}
    if not isinstance(variables, dict):
        raise TypeError('Les variables doivent être un dictionnaire : {"nom": valeur}')
    return dict(variables)


def _code(texte, mode):
    if isinstance(texte, str):
        source = texte.strip() if mode == "eval" else texte
        return compile(_transpiler(source), "<" + mode + ">", mode)
    if hasattr(texte, "co_code"):
        return texte
    raise TypeError("Il faut un texte (ou du code préparé avec compiler_texte)")


def evaluer(texte, variables=None):
    """Calcule une expression Baobab et rend le résultat. variables : {"nom": valeur} en plus."""
    return eval(_code(texte, "eval"), _espace(variables))


def executer_texte(texte, variables=None):
    """Exécute un programme Baobab écrit dans un texte. Rend le dictionnaire des variables créées."""
    espace = _espace(variables)
    exec(_code(texte, "exec"), espace)
    espace.pop("__builtins__", None)
    return espace


def compiler_texte(texte, mode="exec"):
    """Prépare du code ("exec" : un programme, "eval" : une expression) pour evaluer / executer_texte."""
    if mode not in ("exec", "eval"):
        raise ValueError('Le mode doit être "exec" ou "eval"')
    if not isinstance(texte, str):
        raise TypeError("compiler_texte attend un texte")
    return _code(texte, mode)
