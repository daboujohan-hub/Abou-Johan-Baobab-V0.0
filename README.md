# 🌳 Baobab

Un langage de programmation **en français**, pensé pour les débutants,
avec une transition facile vers Python.

Baobab traduit ton code français en Python, puis l'exécute.
Les erreurs sont expliquées en français, avec des suggestions de correction.

## Exemple

    fonction carre(x):
        retourner x * x

    pour i dans intervalle(1, 4):
        afficher(i, "au carré =", carre(i))

## Utilisation

    python -m baobab                                mode interactif
    python -m baobab lancer exemples/fonctions.bao
    python -m baobab expliquer exemples/boucles.bao
    python -m baobab python exemples/boucles.bao

- `lancer` exécute le programme
- `expliquer` montre chaque ligne Baobab avec son équivalent Python
- `python` affiche le code Python généré

## Bibliothèque française

    importer dates       date_du_jour(), heure(), difference_en_jours(...), age_depuis(...)
    importer fichiers    lire(...), ecrire(...), ajouter_ligne(...), existe(...)
    importer dessin      avancer(...), tourner_droite(...), carre(...), etoile(...), sauvegarder(...)
    importer mathematiques, hasard, temps

Exemple avec le dessin (l'image s'enregistre en .svg, à ouvrir dans un navigateur) :

    importer dessin

    dessin.couleur("red")
    pour i dans intervalle(12):
        dessin.etoile(70)
        dessin.tourner_droite(30)
    dessin.sauvegarder("etoiles.svg")

## Installation

    git clone https://github.com/daboujohan-hub/Abou-Johan-Baobab-V0.0.git
    cd Abou-Johan-Baobab-V0.0
    python -m baobab lancer exemples/bonjour.bao

Il faut seulement Python 3.8 ou plus récent.

## Tests

    python -m unittest discover tests

## Structure

    baobab/mots_cles.py       dictionnaire français -> Python
    baobab/lexeur.py          découpe le code en jetons
    baobab/transpileur.py     traduit Baobab en Python
    baobab/erreurs.py         messages d'erreur en français
    baobab/executeur.py       exécute le code
    baobab/explication.py     mode explication
    baobab/repl.py            mode interactif
    baobab/cli.py             commandes
    baobab/bibliotheque/      dates, fichiers, dessin
    exemples/                 programmes d'exemple (.bao)
    tests/                    tests automatiques

Créé par Aboudev 🇨🇮

## Apprendre

Voir le tutoriel : [docs/tutoriel.md](docs/tutoriel.md)

## Tester ses applications

    baobab tester              lance tous les fichiers test_*.bao
    baobab tester exemples     lance les tests d un dossier

Un test est une fonction test_... qui utilise le module tests (tests.egal, tests.contient, tests.requete).

## Limites connues

- Baobab **traduit le français vers Python** : même vitesse, mêmes règles (indentation, `:`). Python doit être installé.
- Quelques mots avancés de Python n'ont pas encore de version française (`async`, `await`, `match`...). Ils fonctionnent quand même, en anglais.
- Le mélange français/anglais est accepté, ce qui est pratique mais peut donner de mauvaises habitudes.
- Si tu définis dans un fichier `.bao` une méthode qui porte le nom d'une méthode de liste ou de texte (`ajouter`, `trier`, `separer`...) et que tu l'appelles depuis un **autre** fichier, Baobab la traduira à tort.
- Les erreurs de syntaxe restent assez générales.
- Le module `serveur` sert à apprendre : pas de HTTPS, pas de comptes, pas de base de données, pas d'anti-spam. Ne l'expose pas tel quel sur Internet.
- Baobab exécute n'importe quel code sans protection : ne lance jamais le code d'un inconnu.
- Les tâches du module `taches` s'arrêtent avec le programme (sur téléphone, Android peut mettre Termux en pause).
- Le module `dessin` produit des images SVG, pas d'animation.
- Testé surtout sous Android (Termux) et Linux, avec un Python récent. Pas encore testé sous Windows ni macOS.
- Pas d'éditeur avec couleurs ni de débogueur pour l'instant.

## Commande courte

La commande `bao` fait la même chose que `baobab` (utile si `baobab` existe déjà sur ton ordinateur).
