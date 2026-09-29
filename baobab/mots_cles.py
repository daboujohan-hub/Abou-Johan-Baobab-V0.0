MOTS_CLES = {
    "si": "if", "sinonsi": "elif", "sinon": "else",
    "pour": "for", "dans": "in", "tantque": "while",
    "fonction": "def", "retourner": "return",
    "classe": "class", "soi": "self", "construire": "__init__",
    "vrai": "True", "faux": "False", "rien": "None",
    "et": "and", "ou": "or", "non": "not", "est": "is",
    "importer": "import", "depuis": "from", "comme": "as",
    "essayer": "try", "sauf": "except", "finalement": "finally",
    "lever": "raise", "arreter": "break", "arrêter": "break",
    "continuer": "continue", "passer": "pass", "avec": "with",
}

FONCTIONS = {
    "afficher": "print", "saisir": "input", "longueur": "len",
    "intervalle": "range", "entier": "int",
    "decimal": "float", "décimal": "float",
    "chaine": "str", "chaîne": "str",
    "booleen": "bool", "booléen": "bool",
    "en_liste": "list", "en_dictionnaire": "dict",
    "en_ensemble": "set", "en_tuple": "tuple",
    "type_de": "type", "enumerer": "enumerate",
    "énumérer": "enumerate", "associer": "zip",
    "absolu": "abs", "maximum": "max", "minimum": "min",
    "somme": "sum", "trier": "sorted", "arrondir": "round",
    "ouvrir": "open",
}

DICTIONNAIRE = {**MOTS_CLES, **FONCTIONS}

# Modules français : traduits seulement si le programme les importe
MODULES = {
    "mathematiques": "math", "mathématiques": "math",
    "hasard": "random", "temps": "time",
    "systeme": "sys", "système": "sys",
}

# Mots utilisés après un point : objet.mot
ATTRIBUTS = {
    "ajouter": "append", "etendre": "extend", "inserer": "insert",
    "retirer": "remove", "depiler": "pop", "vider": "clear",
    "inverser": "reverse", "compter": "count", "copier": "copy",
    "trier": "sort",
    "majuscule": "upper", "minuscule": "lower",
    "capitaliser": "capitalize", "titre": "title",
    "separer": "split", "joindre": "join", "remplacer": "replace",
    "nettoyer": "strip", "commence_par": "startswith",
    "termine_par": "endswith", "trouver": "find", "formater": "format",
    "cles": "keys", "valeurs": "values", "elements": "items",
    "obtenir": "get",
    "racine": "sqrt", "puissance": "pow", "plafond": "ceil",
    "plancher": "floor", "sinus": "sin", "cosinus": "cos",
    "tangente": "tan", "logarithme": "log", "factorielle": "factorial",
    "entier": "randint", "decimal": "uniform", "choisir": "choice",
    "melanger": "shuffle", "nombre": "random",
    "attendre": "sleep", "maintenant": "time", "quitter": "exit",
}

# Bibliothèque française de Baobab
MODULES.update({
    "dates": "baobab_dates",
    "fichiers": "baobab_fichiers",
})
MODULES["dessin"] = "baobab_dessin"
