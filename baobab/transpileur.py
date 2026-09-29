from .lexeur import decouper
from .mots_cles import ATTRIBUTS, DICTIONNAIRE, MODULES, MOTS_CLES


def _analyser(jetons):
    """Première passe : fonctions définies et modules importés."""
    definis = set()
    modules = set()
    ligne_import = False
    precedent = ""
    for type_jeton, valeur in jetons:
        if type_jeton == "AUTRE" and "\n" in valeur:
            ligne_import = False
        if type_jeton == "MOT":
            if valeur in ("importer", "depuis"):
                ligne_import = True
            elif ligne_import and valeur in MODULES:
                modules.add(valeur)
            if precedent == "fonction":
                definis.add(valeur)
        if not valeur.isspace():
            precedent = valeur
    return definis, modules


def transpiler(code_baobab):
    jetons = decouper(code_baobab)
    definis, modules = _analyser(jetons)

    resultat = []
    precedent = ""
    ligne_depuis = False
    apres_importer = False

    for type_jeton, valeur in jetons:
        if type_jeton == "AUTRE" and "\n" in valeur:
            ligne_depuis = False
            apres_importer = False

        sortie = valeur
        if type_jeton == "MOT":
            if precedent == ".":
                sortie = valeur if valeur in definis else ATTRIBUTS.get(valeur, valeur)
            elif precedent == "comme":
                sortie = valeur
            elif valeur in modules:
                sortie = MODULES[valeur]
            elif ligne_depuis and apres_importer and valeur not in MOTS_CLES:
                sortie = ATTRIBUTS.get(valeur, valeur)
            else:
                sortie = DICTIONNAIRE.get(valeur, valeur)

            if valeur == "depuis":
                ligne_depuis = True
            elif valeur == "importer" and ligne_depuis:
                apres_importer = True

        resultat.append(sortie)
        if not valeur.isspace():
            precedent = valeur
    return "".join(resultat)
