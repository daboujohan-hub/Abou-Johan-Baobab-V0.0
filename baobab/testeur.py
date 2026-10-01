"""Lance les tests écrits en Baobab.

Un fichier de tests s'appelle test_*.bao et contient des fonctions test_* :

    importer tests

    fonction test_addition():
        tests.egal(2 + 2, 4)

Fonctions facultatives : avant_chaque() et apres_chaque().
"""

import glob
import importlib
import linecache
import os
import sys
import time
import traceback

from .erreurs import expliquer
from .importeur import ajouter_dossier


def _trouver_fichiers(chemin):
    if chemin is not None and os.path.isfile(chemin):
        return [chemin]
    dossiers = [chemin] if chemin else [".", "tests"]
    fichiers = []
    for dossier in dossiers:
        fichiers += sorted(glob.glob(os.path.join(dossier, "test_*.bao")))
    return fichiers


def _endroit_de_l_echec(exception):
    """Dernier endroit d'un fichier .bao dans la trace : (fichier, ligne, texte)."""
    fichier, numero = None, None
    for cadre in traceback.extract_tb(exception.__traceback__):
        if cadre.filename.endswith(".bao"):
            fichier, numero = cadre.filename, cadre.lineno
    texte = linecache.getline(fichier, numero).strip() if fichier and numero else ""
    return fichier, numero, texte


def _detail(exception, avec_explication):
    fichier, numero, texte = _endroit_de_l_echec(exception)
    lignes = []
    if numero:
        lignes.append(f"ligne {numero} : {texte}")
    if avec_explication:
        lignes.append(expliquer(exception))
    else:
        lignes.append(str(exception) or "La vérification a échoué")
    return lignes


def _executer_fichier(fichier, resultats):
    nom_module = os.path.splitext(os.path.basename(fichier))[0]
    ajouter_dossier(os.path.dirname(os.path.abspath(fichier)))
    print(f"\n📂 {fichier}")

    sys.modules.pop(nom_module, None)
    try:
        module = importlib.import_module(nom_module)
    except Exception as erreur:
        print("  💥 Impossible de charger ce fichier")
        for ligne in _detail(erreur, True):
            print(f"     {ligne}")
        resultats["erreurs"] += 1
        return

    avant = getattr(module, "avant_chaque", None)
    apres = getattr(module, "apres_chaque", None)
    tests = [(n, f) for n, f in vars(module).items() if n.startswith("test_") and callable(f)]
    if not tests:
        print("  (aucune fonction test_* trouvée)")

    for nom, fonction in tests:
        try:
            if avant:
                avant()
            fonction()
            print(f"  ✅ {nom}")
            resultats["reussis"] += 1
        except AssertionError as erreur:
            print(f"  ❌ {nom}")
            for ligne in _detail(erreur, False):
                print(f"     {ligne}")
            resultats["echoues"] += 1
        except Exception as erreur:
            print(f"  💥 {nom}")
            for ligne in _detail(erreur, True):
                print(f"     {ligne}")
            resultats["erreurs"] += 1
        finally:
            if apres:
                try:
                    apres()
                except Exception:
                    pass


def lancer_tests(chemin=None):
    """Lance tous les tests. Retourne 0 si tout est réussi, 1 sinon."""
    fichiers = _trouver_fichiers(chemin)
    if not fichiers:
        print("Aucun fichier test_*.bao trouvé.")
        print("Crée un fichier comme test_mon_appli.bao, puis lance : baobab tester")
        return 1

    resultats = {"reussis": 0, "echoues": 0, "erreurs": 0}
    debut = time.perf_counter()
    for fichier in fichiers:
        _executer_fichier(fichier, resultats)
    duree = time.perf_counter() - debut

    total = sum(resultats.values())
    print(f"\n{'─' * 40}")
    morceaux = [f"{resultats['reussis']} réussi(s)"]
    if resultats["echoues"]:
        morceaux.append(f"{resultats['echoues']} échoué(s)")
    if resultats["erreurs"]:
        morceaux.append(f"{resultats['erreurs']} en erreur")
    print(f"{'🎉' if total == resultats['reussis'] else '⚠️ '} {', '.join(morceaux)} sur {total} ({duree:.2f} s)")
    return 0 if total == resultats["reussis"] else 1
