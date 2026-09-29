# 🌳 Tutoriel Baobab

Apprends à programmer en français, pas à pas.
Crée un fichier par leçon (par exemple `lecon1.bao`) et lance-le avec :

    python -m baobab lancer lecon1.bao

## Leçon 1 : afficher un message

    afficher("Bonjour !")

Essaie de changer le texte entre guillemets.

## Leçon 2 : variables et saisie

    nom = saisir("Ton prénom : ")
    afficher("Salut", nom)

Une variable est une boîte qui garde une valeur. Ici, la boîte `nom` garde ce que tu tapes.

## Leçon 3 : conditions

    age = entier(saisir("Ton âge : "))

    si age >= 18:
        afficher("Tu es majeur")
    sinon:
        afficher("Tu es mineur")

Attention : le `:` à la fin de la ligne et les 4 espaces avant les lignes du bloc sont obligatoires.

## Leçon 4 : boucles

    pour i dans intervalle(1, 6):
        afficher("Compteur :", i)

    n = 3
    tantque n > 0:
        afficher("Décompte", n)
        n = n - 1

`pour` répète un nombre de fois connu, `tantque` répète tant que la condition est vraie.

## Leçon 5 : fonctions

    fonction double(x):
        retourner x * 2

    afficher(double(21))

Une fonction est une recette que tu écris une fois et que tu utilises quand tu veux.

## Leçon 6 : listes

    fruits = ["mangue", "banane"]
    fruits.ajouter("papaye")
    fruits.trier()

    pour f dans fruits:
        afficher(f.majuscule())

    afficher("Il y a", longueur(fruits), "fruits")

## Leçon 7 : les erreurs

    nombre = entier(saisir("Un nombre : "))

Tape `abc` : Baobab t'explique l'erreur en français. Pour l'éviter :

    essayer:
        nombre = entier(saisir("Un nombre : "))
    sauf ErreurValeur:
        afficher("Ce n'est pas un nombre !")

## Leçon 8 : voir le Python derrière

    python -m baobab expliquer lecon3.bao

Baobab montre chaque ligne avec son équivalent Python. Tu apprends Python sans t'en rendre compte !

## Mini-projets

- Le jeu **devine le nombre** : `exemples/devine.bao`
- Un **quiz** avec tes propres questions : `exemples/quiz.bao`
- Un **dessin** avec la tortue : `exemples/dessin.bao`

Bon courage, et n'oublie pas : il n'y a pas de limite tant qu'on continue d'essayer 🌳
