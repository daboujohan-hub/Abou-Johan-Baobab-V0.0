import linecache
import os
import sys
import traceback

from .erreurs import expliquer
from .importeur import ajouter_dossier
from .transpileur import transpiler


def _afficher_erreur(exception, fichier, numero, texte_ligne, noms=()):
    print("\n❌ Oups, une erreur dans ton programme Baobab", file=sys.stderr)
    if numero:
        print(f"   Fichier : {fichier}, ligne {numero}", file=sys.stderr)
        if texte_ligne:
            print(f"   Code    : {texte_ligne}", file=sys.stderr)
    print(f"   Explication : {expliquer(exception, noms)}", file=sys.stderr)


def executer(code_baobab, nom_fichier="<baobab>"):
    """Exécute du code Baobab. Retourne 0 si tout va bien, 1 sinon."""
    source_lignes = code_baobab.splitlines()
    code_python = transpiler(code_baobab)

    # les fichiers .bao placés à côté du programme peuvent être importés
    if os.path.isfile(nom_fichier):
        ajouter_dossier(os.path.dirname(os.path.abspath(nom_fichier)))

    def texte_de(fichier, numero):
        if not numero:
            return ""
        if fichier == nom_fichier and 1 <= numero <= len(source_lignes):
            return source_lignes[numero - 1].strip()
        return linecache.getline(fichier, numero).strip()

    try:
        compile_ = compile(code_python, nom_fichier, "exec")
    except SyntaxError as e:
        _afficher_erreur(e, nom_fichier, e.lineno, texte_de(nom_fichier, e.lineno))
        return 1

    espace = {"__name__": "__main__"}
    try:
        exec(compile_, espace)
    except KeyboardInterrupt:
        print("\nProgramme interrompu.", file=sys.stderr)
        return 1
    except Exception as e:
        fichier, numero = nom_fichier, None
        if isinstance(e, SyntaxError) and str(e.filename).endswith(".bao"):
            fichier, numero = e.filename, e.lineno
        else:
            for cadre in traceback.extract_tb(e.__traceback__):
                if cadre.filename == nom_fichier or cadre.filename.endswith(".bao"):
                    fichier, numero = cadre.filename, cadre.lineno
        _afficher_erreur(e, fichier, numero, texte_de(fichier, numero), list(espace))
        return 1
    return 0
