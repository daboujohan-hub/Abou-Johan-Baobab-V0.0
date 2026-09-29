# 🌳 Baobab

Un langage de programmation **en français**, pensé pour les débutants,
avec une transition facile vers Python.

Baobab traduit ton code français en Python, puis l'exécute.
Les erreurs sont expliquées en français.

## Exemple

    fonction carre(x):
        retourner x * x

    pour i dans intervalle(1, 4):
        afficher(i, "au carré =", carre(i))

## Utilisation

    python -m baobab                              mode interactif
    python -m baobab lancer exemples/fonctions.bao
    python -m baobab expliquer exemples/boucles.bao
    python -m baobab python exemples/boucles.bao

- `lancer` exécute le programme
- `expliquer` montre chaque ligne Baobab avec son équivalent Python
- `python` affiche le code Python généré

## Installation

    git clone https://github.com/daboujohan-hub/Abou-Johan-Baobab-V0.0.git
    cd Abou-Johan-Baobab-V0.0
    python -m baobab lancer exemples/bonjour.bao

Il faut seulement Python 3.8 ou plus récent.

## Tests

    python -m unittest discover tests

## Structure

    baobab/mots_cles.py     dictionnaire français -> Python
    baobab/lexeur.py        découpe le code en jetons
    baobab/transpileur.py   traduit Baobab en Python
    baobab/erreurs.py       messages d'erreur en français
    baobab/executeur.py     exécute le code
    baobab/explication.py   mode explication
    baobab/repl.py          mode interactif
    baobab/cli.py           commandes
    exemples/               programmes d'exemple (.bao)
    tests/                  tests automatiques

Créé par Aboudev 🇨🇮
