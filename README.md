# 🌳 Baobab

Un langage de programmation **en français**, pensé pour les débutants,
avec une transition facile vers Python.

## Utilisation (sans installation)

    python -m baobab lancer exemples/bonjour.bao
    python -m baobab python exemples/fonctions.bao   # voir le code Python

## Installation (commande `baobab`)

    pip install -e .
    baobab lancer exemples/bonjour.bao

## Tests

    python -m unittest discover tests

## Structure

    baobab/mots_cles.py    dictionnaire français -> Python
    baobab/lexeur.py       découpe le code en jetons
    baobab/transpileur.py  traduit Baobab en Python
    baobab/erreurs.py      messages d'erreur en français
    baobab/executeur.py    exécute le code
    baobab/cli.py          commandes
    exemples/              programmes d'exemple (.bao)
    tests/                 tests automatiques

Créé par Aboudev 🇨🇮
