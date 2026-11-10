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

# Noms d'erreurs en français (pour essayer / sauf)
DICTIONNAIRE.update({
    "Erreur": "Exception",
    "ErreurValeur": "ValueError",
    "ErreurType": "TypeError",
    "ErreurNom": "NameError",
    "ErreurIndex": "IndexError",
    "ErreurCle": "KeyError",
    "DivisionParZero": "ZeroDivisionError",
    "FichierIntrouvable": "FileNotFoundError",
})
MODULES["serveur"] = "baobab_serveur"

# Plus de mots pour les développeurs
_NOUVEAUX_MOTS = {
    "anonyme": "lambda",
    "globale": "global",
    "nonlocale": "nonlocal",
    "effacer": "del",
    "verifier": "assert",
    "vérifier": "assert",
    "produire": "yield",
}
_NOUVELLES_FONCTIONS = {
    "appliquer": "map",
    "filtrer": "filter",
    "tous": "all",
    "au_moins_un": "any",
    "est_instance": "isinstance",
    "inverse": "reversed",
    "caractere": "chr",
    "caractère": "chr",
    "code_de": "ord",
    "quotient_reste": "divmod",
    "parent": "super",
}
MOTS_CLES.update(_NOUVEAUX_MOTS)
FONCTIONS.update(_NOUVELLES_FONCTIONS)
DICTIONNAIRE.update(_NOUVEAUX_MOTS)
DICTIONNAIRE.update(_NOUVELLES_FONCTIONS)
ATTRIBUTS["construire"] = "__init__"
MODULES.update({"taches": "baobab_taches", "tâches": "baobab_taches"})

# Importer des tests et écrire des programmes réutilisables
MODULES["tests"] = "baobab_tests"
_PRINCIPAL = {"programme_principal": '__name__ == "__main__"'}
MOTS_CLES.update(_PRINCIPAL)
DICTIONNAIRE.update(_PRINCIPAL)
MODULES["disque"] = "baobab_disque"
MODULES.update({"base": "baobab_base", "donnees": "baobab_donnees", "données": "baobab_donnees"})
MODULES["statistiques"] = "baobab_statistiques"
MODULES["reseau"] = "baobab_reseau"
MODULES.update({"chaines": "baobab_chaines", "chaînes": "baobab_chaines"})
MODULES.update({"securite": "baobab_securite", "sécurité": "baobab_securite"})


# Fonctions Python ajoutées en français (eval, exec et compile exclues : sécurité)
_NOUVELLES_FONCTIONS = {
    "binaire": "bin", "octal": "oct", "hexadecimal": "hex",
    "octets": "bytes", "octets_modifiables": "bytearray", "vue_memoire": "memoryview",
    "complexe": "complex", "ensemble_fige": "frozenset", "decoupe": "slice",
    "iterateur": "iter", "element_suivant": "next",
    "iterateur_asynchrone": "aiter", "suivant_asynchrone": "anext",
    "objet_de_base": "object", "attribut_calcule": "property",
    "methode_de_classe": "classmethod", "methode_statique": "staticmethod",
    "est_sous_classe": "issubclass", "appelable": "callable",
    "lire_attribut": "getattr", "definir_attribut": "setattr",
    "supprimer_attribut": "delattr", "a_attribut": "hasattr",
    "attributs_de": "dir", "variables_de": "vars",
    "globales": "globals", "locales": "locals",
    "representation_texte": "repr", "en_ascii": "ascii",
    "calculer_empreinte": "hash", "identifiant_objet": "id",
    "aide_python": "help", "quitter": "quit", "point_d_arret": "breakpoint",
}
for _fr, _py in _NOUVELLES_FONCTIONS.items():
    DICTIONNAIRE.setdefault(_fr, _py)
    if isinstance(FONCTIONS, dict):
        FONCTIONS.setdefault(_fr, _py)
