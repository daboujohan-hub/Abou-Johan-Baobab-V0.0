"""Le lexeur découpe le code en morceaux (« jetons »).

Types de jetons :
  TEXTE       : "bonjour" ou 'bonjour' ou un texte sur plusieurs lignes
  COMMENTAIRE : # ceci est un commentaire
  MOT         : afficher, si, age, ...
  AUTRE       : espaces, chiffres, symboles, retours à la ligne
"""

import re

MOTIF = re.compile(
    r"""
    (?P<TEXTE>
        [rRbBfF]{0,2}(?:\"\"\".*?\"\"\"|'''.*?'''
        |"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')
    )
    |(?P<COMMENTAIRE>\#[^\n]*)
    |(?P<MOT>[^\W\d]\w*)
    |(?P<AUTRE>\d+\.?\d*|\s+|.)
    """,
    re.VERBOSE | re.DOTALL,
)


def decouper(code):
    """Transforme le code en liste de (type, valeur)."""
    jetons = []
    for m in MOTIF.finditer(code):
        jetons.append((m.lastgroup, m.group()))
    return jetons
