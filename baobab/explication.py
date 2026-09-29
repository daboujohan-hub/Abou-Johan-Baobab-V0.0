from .lexeur import decouper
from .transpileur import transpiler


def _mots_traduits(code_baobab, code_python):
    """Liste (mot Baobab, mot Python) pour chaque mot traduit."""
    a = decouper(code_baobab)
    b = decouper(code_python)
    if len(a) != len(b):
        return []
    vus = {}
    for (type1, mot1), (_, mot2) in zip(a, b):
        if type1 == "MOT" and mot1 != mot2 and mot1 not in vus:
            vus[mot1] = mot2
    return list(vus.items())


def expliquer_code(code_baobab):
    """Retourne un texte : chaque ligne Baobab avec son équivalent Python."""
    code_python = transpiler(code_baobab)
    lignes_baobab = code_baobab.split("\n")
    lignes_python = code_python.split("\n")

    sortie = []
    for numero, (baobab, python) in enumerate(zip(lignes_baobab, lignes_python), 1):
        if not baobab.strip():
            continue
        sortie.append(f"Ligne {numero}")
        sortie.append(f"  Baobab : {baobab.rstrip()}")
        if baobab == python:
            sortie.append("  Python : (identique)")
        else:
            sortie.append(f"  Python : {python.rstrip()}")
        sortie.append("")

    mots = _mots_traduits(code_baobab, code_python)
    if mots:
        sortie.append("Mots traduits :")
        for baobab, python in mots:
            sortie.append(f"  {baobab}  ->  {python}")
    return "\n".join(sortie)
