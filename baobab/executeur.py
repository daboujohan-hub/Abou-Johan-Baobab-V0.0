"""L'exécuteur lance le code Python généré à partir du Baobab."""

import sys
import traceback

from .erreurs import expliquer
from .transpileur import transpiler


def _ligne_de(source_lignes, numero):
    if numero and 1 <= numero <= len(source_lignes):
        return source_lignes[numero - 1].strip()
    return ""


def _afficher_erreur(exception, nom_fichier, source_lignes, numero, noms=()):
    print("\n❌ Oups, une erreur dans ton programme Baobab", file=sys.stderr)
    if numero:
        print(f"   Fichier : {nom_fichier}, ligne {numero}", file=sys.stderr)
        texte = _ligne_de(source_lignes, numero)
        if texte:
            print(f"   Code    : {texte}", file=sys.stderr)
    print(f"   Explication : {expliquer(exception, noms)}", file=sys.stderr)


def executer(code_baobab, nom_fichier="<baobab>"):
    """Exécute du code Baobab. Retourne 0 si tout va bien, 1 sinon."""
    source_lignes = code_baobab.splitlines()
    code_python = transpiler(code_baobab)

    try:
        compile_ = compile(code_python, nom_fichier, "exec")
    except SyntaxError as e:
        _afficher_erreur(e, nom_fichier, source_lignes, e.lineno)
        return 1

    espace = {"__name__": "__main__"}
    try:
        exec(compile_, espace)
    except KeyboardInterrupt:
        print("\nProgramme interrompu.", file=sys.stderr)
        return 1
    except Exception as e:
        numero = None
        for cadre in traceback.extract_tb(e.__traceback__):
            if cadre.filename == nom_fichier:
                numero = cadre.lineno
        _afficher_erreur(e, nom_fichier, source_lignes, numero, list(espace))
        return 1
    return 0
