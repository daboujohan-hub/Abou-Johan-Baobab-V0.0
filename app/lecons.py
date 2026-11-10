"""Leçons de l'application Baobab.

Pour ajouter une leçon : copie un bloc, change l'id, et remplis les champs.
Le test tests/test_lecons.py vérifie chaque leçon avec le vrai interpréteur.
"""

LECONS = [
    {
        "id": "afficher",
        "titre": "Afficher un message",
        "niveau": "Débutant",
        "explication": "Pour que Baobab écrive quelque chose à l'écran, on utilise afficher(...). Le texte se met entre guillemets.",
        "exemple": 'afficher("Bonjour")',
        "consigne": "Affiche le message : Bonjour Baobab",
        "depart": "# Écris ton code ici\n",
        "attendu": "Bonjour Baobab",
        "solution": 'afficher("Bonjour Baobab")',
        "indice": 'Écris afficher("...") avec ton message entre les guillemets.',
    },
    {
        "id": "variables",
        "titre": "Les variables",
        "niveau": "Débutant",
        "explication": "Une variable garde une valeur sous un nom. On écrit nom = valeur, puis on peut l'utiliser partout dans le programme.",
        "exemple": 'prenom = "Awa"\nafficher("Bonjour", prenom)',
        "consigne": "Crée une variable age qui vaut 15, puis affiche : Mon age est 15 (en utilisant la variable).",
        "depart": "# Crée la variable age, puis affiche le message\n",
        "attendu": "Mon age est 15",
        "solution": 'age = 15\nafficher("Mon age est", age)',
        "exige": ["="],
        "indice": 'afficher("Mon age est", age) écrit le texte, puis la valeur de la variable.',
    },
    {
        "id": "calculs",
        "titre": "Faire des calculs",
        "niveau": "Débutant",
        "explication": "Baobab calcule comme une calculatrice : + - * / . La multiplication et la division passent avant l'addition et la soustraction.",
        "exemple": "afficher(7 * 6)",
        "consigne": "3 articles coûtent chacun 1500 FCFA. Affiche le total, avec une multiplication.",
        "depart": "prix = 1500\nquantite = 3\n# Affiche le total\n",
        "attendu": "4500",
        "solution": "prix = 1500\nquantite = 3\nafficher(prix * quantite)",
        "exige": ["*"],
        "indice": "Multiplie prix par quantite : afficher(prix * quantite)",
    },
    {"id": "conditions", "titre": "Les conditions (si)", "niveau": "Débutant", "bientot": True},
    {"id": "boucles", "titre": "Les boucles (pour)", "niveau": "Intermédiaire", "bientot": True},
    {"id": "listes", "titre": "Les listes", "niveau": "Intermédiaire", "bientot": True},
    {"id": "fonctions", "titre": "Les fonctions", "niveau": "Intermédiaire", "bientot": True},
    {"id": "dictionnaires", "titre": "Les dictionnaires", "niveau": "Avancé", "bientot": True},
    {"id": "modules", "titre": "Les modules (nombres, calendrier)", "niveau": "Avancé", "bientot": True},
    {"id": "projet", "titre": "Mini-projet", "niveau": "Avancé", "bientot": True},
]
