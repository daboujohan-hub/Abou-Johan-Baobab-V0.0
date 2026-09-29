"""Module dessin : une tortue qui dessine, résultat en image SVG.

Au départ, la tortue est au centre de la feuille et regarde vers le haut.
"""

import html
import math

_etat = {}


def nouvelle_feuille(largeur=400, hauteur=400):
    """Efface tout et recommence avec une feuille vierge."""
    _etat.clear()
    _etat.update({
        "largeur": largeur,
        "hauteur": hauteur,
        "x": largeur / 2,
        "y": hauteur / 2,
        "angle": 0.0,
        "crayon": True,
        "couleur": "black",
        "epaisseur": 2,
        "fond": "white",
        "formes": [],
    })


nouvelle_feuille()


def _n(nombre):
    return f"{nombre:.1f}"


def _ligne(x1, y1, x2, y2):
    _etat["formes"].append(
        f'<line x1="{_n(x1)}" y1="{_n(y1)}" x2="{_n(x2)}" y2="{_n(y2)}" '
        f'stroke="{_etat["couleur"]}" stroke-width="{_etat["epaisseur"]}" '
        f'stroke-linecap="round"/>'
    )


def avancer(distance):
    angle = math.radians(_etat["angle"])
    x2 = _etat["x"] + distance * math.sin(angle)
    y2 = _etat["y"] - distance * math.cos(angle)
    if _etat["crayon"]:
        _ligne(_etat["x"], _etat["y"], x2, y2)
    _etat["x"], _etat["y"] = x2, y2


def reculer(distance):
    avancer(-distance)


def tourner_droite(angle):
    _etat["angle"] = (_etat["angle"] + angle) % 360


def tourner_gauche(angle):
    tourner_droite(-angle)


def lever_crayon():
    _etat["crayon"] = False


def poser_crayon():
    _etat["crayon"] = True


def couleur(nom):
    """Couleur du trait : "red", "blue", "green", "#ff8800"..."""
    _etat["couleur"] = html.escape(str(nom), quote=True)


def epaisseur(taille):
    _etat["epaisseur"] = max(1, int(taille))


def fond(nom):
    _etat["fond"] = html.escape(str(nom), quote=True)


def aller_a(x, y):
    """Va au point (x, y). Le centre de la feuille est (0, 0)."""
    x2 = _etat["largeur"] / 2 + x
    y2 = _etat["hauteur"] / 2 - y
    if _etat["crayon"]:
        _ligne(_etat["x"], _etat["y"], x2, y2)
    _etat["x"], _etat["y"] = x2, y2


def carre(cote):
    for _ in range(4):
        avancer(cote)
        tourner_droite(90)


def triangle(cote):
    for _ in range(3):
        avancer(cote)
        tourner_droite(120)


def etoile(taille):
    for _ in range(5):
        avancer(taille)
        tourner_droite(144)


def cercle(rayon):
    """Cercle centré sur la position de la tortue."""
    _etat["formes"].append(
        f'<circle cx="{_n(_etat["x"])}" cy="{_n(_etat["y"])}" r="{_n(rayon)}" '
        f'fill="none" stroke="{_etat["couleur"]}" stroke-width="{_etat["epaisseur"]}"/>'
    )


def sauvegarder(nom="dessin.svg"):
    e = _etat
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{e["largeur"]}" '
        f'height="{e["hauteur"]}" viewBox="0 0 {e["largeur"]} {e["hauteur"]}">\n'
        f'<rect width="100%" height="100%" fill="{e["fond"]}"/>\n'
        + "\n".join(e["formes"])
        + "\n</svg>\n"
    )
    with open(nom, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"🎨 Dessin enregistré dans {nom}")
