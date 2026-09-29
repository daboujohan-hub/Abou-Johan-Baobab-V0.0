from . import __version__
from .erreurs import expliquer
from .transpileur import transpiler

SORTIES = ("quitter", "quitter()", "sortir", "sortir()")


def _lire_bloc():
    """Lit une ligne, ou un bloc entier (jusqu'à une ligne vide)."""
    try:
        ligne = input("baobab> ")
    except EOFError:
        return None
    lignes = [ligne]
    if ligne.rstrip().endswith(":"):
        while True:
            try:
                suite = input("....... ")
            except EOFError:
                break
            if suite.strip() == "":
                break
            lignes.append(suite)
    return "\n".join(lignes)


def _montrer(valeur):
    if valeur is None:
        return
    if valeur is True:
        print("vrai")
    elif valeur is False:
        print("faux")
    else:
        print(repr(valeur))


def _executer(code, espace):
    python = transpiler(code)
    try:
        try:
            compile_ = compile(python, "<baobab>", "eval")
            est_expression = True
        except SyntaxError:
            compile_ = compile(python + "\n", "<baobab>", "exec")
            est_expression = False
        if est_expression:
            _montrer(eval(compile_, espace))
        else:
            exec(compile_, espace)
    except SystemExit:
        raise
    except Exception as e:
        print("❌", expliquer(e, list(espace)))


def lancer():
    print(f"🌳 Baobab {__version__} - mode interactif")
    print("Tape du code Baobab. Écris 'quitter' pour sortir.\n")
    espace = {"__name__": "__main__"}
    while True:
        try:
            code = _lire_bloc()
        except KeyboardInterrupt:
            print()
            continue
        if code is None or code.strip() in SORTIES:
            print("À bientôt ! 🌳")
            return 0
        if code.strip():
            _executer(code, espace)
