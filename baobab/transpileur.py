from .lexeur import decouper
from .mots_cles import ATTRIBUTS, DICTIONNAIRE, FONCTIONS, MODULES, MOTS_CLES


def _noms_du_programmeur(jetons):
    """Mots de Baobab (maximum, somme...) que le programmeur utilise comme SES noms.

    Dans ce programme, ces mots ne sont plus traduits : ils lui appartiennent.
    """
    sig = [(t, v) for t, v in jetons if not v.isspace() and t != "COMMENTAIRE"]
    noms = set()
    profondeur = 0
    parametres = None  # profondeur de la parenthèse des paramètres d'une fonction
    attend_parametres = False
    dans_pour = False

    for i, (type_jeton, valeur) in enumerate(sig):
        precedent = sig[i - 1][1] if i > 0 else ""
        suivant = sig[i + 1][1] if i + 1 < len(sig) else ""
        suivant2 = sig[i + 2][1] if i + 2 < len(sig) else ""

        if type_jeton != "MOT":
            if valeur in ("(", "[", "{"):
                profondeur += 1
                if valeur == "(" and attend_parametres:
                    parametres = profondeur
                    attend_parametres = False
            elif valeur in (")", "]", "}"):
                if parametres == profondeur:
                    parametres = None
                profondeur -= 1
            continue

        if valeur == "pour":
            dans_pour = True
        elif valeur == "dans":
            dans_pour = False
        elif valeur == "fonction":
            attend_parametres = True
        elif valeur in FONCTIONS and precedent != ".":
            est_nom_cree = (
                precedent in ("fonction", "comme")
                or dans_pour
                or (suivant == "=" and suivant2 != "=" and profondeur == 0)
                or (parametres is not None and profondeur == parametres
                    and precedent in ("(", ",", "*"))
            )
            if est_nom_cree:
                noms.add(valeur)
    return noms


def _analyser(jetons):
    """Première passe : fonctions définies, modules importés, noms du programmeur."""
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
            if precedent == "fonction" and valeur not in MOTS_CLES:
                definis.add(valeur)
        if not valeur.isspace():
            precedent = valeur
    return definis, modules, _noms_du_programmeur(jetons)


def _traduire_fstring(texte, definis, modules, noms):
    """Traduit aussi le code écrit entre accolades dans un f"...".

    Exemple : f"Il y a {longueur(x)} éléments"
    """
    debut = 0
    while debut < len(texte) and texte[debut] not in "\"'":
        debut += 1
    if "f" not in texte[:debut].lower() or "{" not in texte:
        return texte

    resultat = []
    i = 0
    while i < len(texte):
        if texte[i] != "{":
            resultat.append(texte[i])
            i += 1
        elif texte[i + 1:i + 2] == "{":  # {{ = une vraie accolade
            resultat.append("{{")
            i += 2
        else:
            profondeur = 1
            j = i + 1
            while j < len(texte) and profondeur > 0:
                if texte[j] == "{":
                    profondeur += 1
                elif texte[j] == "}":
                    profondeur -= 1
                j += 1
            if profondeur != 0:  # accolade jamais fermée : on laisse tel quel
                resultat.append(texte[i:])
                break
            interieur = texte[i + 1:j - 1]
            resultat.append("{" + _traduire(interieur, definis, modules, noms) + "}")
            i = j
    return "".join(resultat)


def _traduire(code, definis, modules, noms):
    resultat = []
    precedent = ""
    ligne_depuis = False
    apres_importer = False

    for type_jeton, valeur in decouper(code):
        if type_jeton == "AUTRE" and "\n" in valeur:
            ligne_depuis = False
            apres_importer = False

        sortie = valeur
        if type_jeton == "TEXTE":
            sortie = _traduire_fstring(valeur, definis, modules, noms)
        elif type_jeton == "MOT":
            if precedent == ".":
                sortie = valeur if valeur in definis else ATTRIBUTS.get(valeur, valeur)
            elif precedent == "comme":
                sortie = valeur
            elif valeur in modules:
                sortie = MODULES[valeur]
            elif ligne_depuis and apres_importer and valeur not in MOTS_CLES:
                sortie = ATTRIBUTS.get(valeur, valeur)
            elif valeur in noms:
                sortie = valeur
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


def transpiler(code_baobab):
    definis, modules, noms = _analyser(decouper(code_baobab))
    return _traduire(code_baobab, definis, modules, noms)
