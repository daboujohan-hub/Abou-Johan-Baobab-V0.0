# 🌳 Baobab — Langage de programmation en français

![Logo Baobab 2026](docs/images/baobab-2026.jpg)

**Baobab** est un langage de programmation en français, conçu pour aider les débutants à apprendre la logique de programmation avant de passer progressivement à Python.

Il traduit le code Baobab en Python, puis l’exécute. Les erreurs sont présentées en français, avec des indications pour aider à les comprendre et à les corriger.

> Créé par **Aboudev 🇨🇮** — Côte d’Ivoire

## ✨ Fonctionnalités

- Syntaxe en français : `fonction`, `retourner`, `pour`, `dans`, `afficher`, `importer`.
- Traduction du code Baobab vers Python.
- Exécution de programmes `.bao`.
- Mode interactif pour essayer de petites instructions.
- Mode explication qui associe les lignes Baobab à leur équivalent Python.
- Bibliothèques françaises pour les dates, les fichiers, le dessin, les mathématiques, le hasard et le temps.
- Outils de test pour les programmes et exemples.
- Analyse de fichiers pour repérer les fichiers volumineux, les doublons et les fichiers anciens, sans les supprimer.

## 🖼️ Ajouter le logo au dépôt

Le README affiche le logo depuis ce chemin :

```text
docs/images/baobab-2026.jpg
```

Crée ce dossier dans le dépôt et place l’image `baobab-2026.jpg` à cet emplacement. Si tu utilises le fichier README fourni ici, conserve exactement ce chemin pour que l’image s’affiche sur GitHub.

## 🚀 Installation

Baobab nécessite **Python 3.8 ou une version plus récente**.

```bash
git clone https://github.com/daboujohan-hub/Abou-Johan-Baobab-V0.0.git
cd Abou-Johan-Baobab-V0.0
python -m baobab lancer exemples/bonjour.bao
```

Si Python est déjà installé et que le dépôt est présent sur ton appareil, passe directement dans le dossier du projet avant d’exécuter les commandes.

## ▶️ Utilisation

### Lancer un programme

```bash
python -m baobab lancer exemples/fonctions.bao
```

### Expliquer un programme

```bash
python -m baobab expliquer exemples/boucles.bao
```

### Afficher le Python généré

```bash
python -m baobab python exemples/boucles.bao
```

### Ouvrir le mode interactif

```bash
python -m baobab
```

La commande courte `bao` peut également être utilisée si elle est installée et disponible dans le terminal.

## 🧩 Exemple de code Baobab

```python
fonction carre(x):
    retourner x * x

pour i dans intervalle(1, 4):
    afficher(i, "au carré =", carre(i))
```

Ce programme calcule le carré des nombres de 1 à 3 et affiche le résultat.

## 📚 Bibliothèques françaises

| Bibliothèque | Exemples de fonctions |
|---|---|
| `dates` | `date_du_jour()`, `heure()`, `difference_en_jours(...)`, `age_depuis(...)` |
| `fichiers` | `lire(...)`, `ecrire(...)`, `ajouter_ligne(...)`, `existe(...)` |
| `dessin` | `avancer(...)`, `tourner_droite(...)`, `carre(...)`, `etoile(...)`, `sauvegarder(...)` |
| `mathematiques` | Fonctions mathématiques |
| `hasard` | Opérations aléatoires |
| `temps` | Fonctions liées au temps |
| `base` | Outils pour ouvrir, interroger et modifier une base de données |
| `donnees` | Lecture et écriture JSON et CSV |

### Exemple : dessiner une étoile en répétition

```python
importer dessin

dessin.couleur("red")

pour i dans intervalle(12):
    dessin.etoile(70)
    dessin.tourner_droite(30)

dessin.sauvegarder("etoiles.svg")
```

Le dessin est enregistré au format **SVG**. Ouvre le fichier dans un navigateur pour le visualiser.

## 🧪 Tests

Lancer les tests Python du projet :

```bash
python -m unittest discover tests
```

Baobab propose également des commandes de test pour les fichiers `.bao` :

```bash
baobab tester
baobab tester exemples
```

Un test Baobab utilise une fonction dont le nom commence par `test_` et les outils du module `tests`, par exemple `tests.egal`, `tests.contient` ou `tests.requete`.

## 🔍 Analyser des fichiers

```bash
baobab exemples/analyse_appareil.bao
```

Le module d’analyse peut repérer les gros fichiers, les doublons, les fichiers anciens et les fichiers probablement inutiles. **Il ne supprime rien automatiquement.**

## 🗂️ Structure du projet

```text
baobab/
├── mots_cles.py          # Dictionnaire français vers Python
├── lexeur.py             # Découpe le code en jetons
├── transpileur.py        # Traduit Baobab en Python
├── erreurs.py            # Messages d’erreur en français
├── executeur.py          # Exécution des programmes
├── explication.py        # Mode explication
├── repl.py               # Mode interactif
├── cli.py                # Commandes du terminal
└── bibliotheque/         # Bibliothèques intégrées

exemples/                 # Programmes d’exemple (.bao)
tests/                    # Tests automatiques
docs/
├── images/
│   └── baobab-2026.jpg   # Logo du projet
└── tutoriel.md           # Tutoriel d’apprentissage
```

## 📖 Apprendre Baobab

Consulte le tutoriel : [`docs/tutoriel.md`](docs/tutoriel.md).

## ⚠️ Limites et sécurité

- Baobab traduit le français vers Python : l’indentation et certaines règles de Python restent nécessaires.
- Certains mots avancés de Python, comme `async`, `await` et `match`, n’ont pas encore de traduction française dédiée.
- Le mélange de mots français et anglais est accepté.
- Certaines erreurs de syntaxe peuvent encore produire des messages généraux.
- Le module `serveur` est destiné à l’apprentissage : il ne fournit pas à lui seul HTTPS, comptes utilisateurs, base de données ou protection anti-spam. **Ne l’expose pas directement sur Internet.**
- Baobab exécute le code qu’on lui donne. **N’exécute pas les programmes d’une personne inconnue ou non fiable.**
- Les tâches du module `taches` s’arrêtent avec le programme. Sur Android, Termux peut aussi être mis en pause par le système.
- Le module `dessin` produit des images SVG, pas des animations.
- Le projet a surtout été testé sous Android (Termux) et Linux. Windows et macOS ne sont pas encore validés.
- Il n’y a pas encore d’éditeur avec coloration syntaxique ni de débogueur intégré.

## 🤝 Contribution

Les améliorations, exemples, tests et propositions de nouvelles instructions françaises peuvent aider Baobab à progresser. Avant de proposer une modification, vérifie les tests et décris clairement ce qui a changé.

## 📄 Licence

Ajoute ici la licence choisie pour le projet, par exemple un fichier `LICENSE` à la racine du dépôt. Ne revendique pas une licence tant qu’elle n’a pas été choisie et ajoutée.

---

**Baobab 2026** — apprendre la programmation en français, étape par étape. 🌳

    importer statistiques   moyenne, mediane, ecart_type, pourcentage, frequences
