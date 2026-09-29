import os
import sys

from . import __version__
from .executeur import executer
from .explication import expliquer_code
from .repl import lancer as mode_interactif
from .transpileur import transpiler

AIDE = """🌳 Baobab {version} - programmer en français

Utilisation :
  baobab                          Mode interactif
  baobab <fichier>                Exécuter un programme
  baobab lancer   <fichier.bao>   Exécuter un programme
  baobab expliquer <fichier.bao>  Voir chaque ligne avec son équivalent Python
  baobab python   <fichier.bao>   Voir le code Python généré
  baobab version                  Afficher la version
"""


def _lire(chemin):
    try:
        with open(chemin, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Fichier introuvable : {chemin}", file=sys.stderr)
        return None


def principal(args=None):
    args = sys.argv[1:] if args is None else args

    if not args or args[0] == "interactif":
        return mode_interactif()

    if args[0] in ("aide", "-h", "--help"):
        print(AIDE.format(version=__version__))
        return 0

    commande = args[0]

    if commande == "version":
        print(f"Baobab {__version__}")
        return 0

    if commande in ("lancer", "python", "expliquer"):
        if len(args) < 2:
            print("Il manque le nom du fichier.", file=sys.stderr)
            return 1
        code = _lire(args[1])
        if code is None:
            return 1
        if commande == "lancer":
            return executer(code, args[1])
        if commande == "expliquer":
            print(expliquer_code(code))
            return 0
        print(transpiler(code))
        return 0

    # baobab mon_programme.bao  ->  raccourci pour : baobab lancer mon_programme.bao
    if os.path.isfile(commande):
        code = _lire(commande)
        return executer(code, commande) if code is not None else 1

    print(f"Commande inconnue : {commande}\n", file=sys.stderr)
    print(AIDE.format(version=__version__))
    return 1
