# 🌳 Guide d'utilisation de Baobab (version 0.14.0)

Baobab est un langage de programmation **en français**. Il traduit ton programme en Python,
puis l'exécute. Les erreurs sont expliquées en français, avec des suggestions.

## 1. Installer

Il faut Python 3.8 ou plus récent.

Sans rien installer (depuis le dossier du projet) :

    python -m baobab lancer exemples/bonjour.bao

Avec les commandes courtes `baobab` et `bao` (elles font la même chose) :

    pip install .

Sur Termux (téléphone Android), si l'installation se plaint de la construction :

    pip install . --no-build-isolation

Quand le paquet sera publié, ce sera simplement : `pip install baobab-francais`

## 2. Les commandes

| Commande | Ce qu'elle fait |
|---|---|
| `baobab` | ouvre le mode interactif (tape `quitter` pour sortir) |
| `baobab programme.bao` | exécute un programme (aussi : `baobab lancer programme.bao`) |
| `baobab expliquer programme.bao` | montre chaque ligne avec son équivalent Python |
| `baobab python programme.bao` | affiche le code Python généré |
| `baobab tester [fichier ou dossier]` | lance les tests (fichiers `test_*.bao`) |
| `baobab version` | affiche la version |

`bao` remplace `baobab` partout (utile si `baobab` existe déjà sur ton ordinateur).
`Ctrl+C` arrête un programme.

## 3. Ton premier programme

Crée un fichier `salut.bao` :

    nom = saisir("Ton prénom : ")
    afficher("Bienvenue dans Baobab,", nom)

Lance-le : `baobab salut.bao`

Règles à retenir :
- une ligne `si`, `pour`, `tantque`, `fonction`, `classe`... se termine par **`:`** ;
- les lignes du bloc sont décalées de **4 espaces** ;
- un commentaire commence par **`#`**.

## 4. Les mots du langage

**Structure**

| Baobab | Python | Exemple |
|---|---|---|
| `si` `sinonsi` `sinon` | if elif else | `si age >= 18:` |
| `pour` ... `dans` | for ... in | `pour i dans intervalle(5):` |
| `tantque` | while | `tantque n > 0:` |
| `arreter` `continuer` `passer` | break continue pass | |
| `fonction` `retourner` | def return | `fonction double(x):` |
| `classe` `soi` `construire` `parent()` | class self __init__ super() | |
| `essayer` `sauf` `finalement` `lever` | try except finally raise | |
| `importer` `depuis` `comme` | import from as | `importer dates` |
| `avec` `globale` `nonlocale` | with global nonlocal | |
| `anonyme` | lambda | `anonyme x: x * 2` |
| `effacer` `verifier` `produire` | del assert yield | |
| `programme_principal` | `__name__ == "__main__"` | `si programme_principal:` |

**Valeurs et logique** : `vrai` `faux` `rien` — `et` `ou` `non` `est` `dans`
(par exemple `x est non rien` veut dire « x n'est pas vide »).

**Fonctions intégrées** : `afficher` `saisir` `longueur` `intervalle` `entier` `decimal`
`chaine` `booleen` `en_liste` `en_dictionnaire` `en_ensemble` `en_tuple` `type_de`
`enumerer` `associer` `absolu` `maximum` `minimum` `somme` `trier` `arrondir` `ouvrir`
`appliquer` `filtrer` `tous` `au_moins_un` `est_instance` `inverse` `caractere` `code_de`
`quotient_reste`

**Erreurs** (pour `sauf`) : `Erreur` `ErreurValeur` `ErreurType` `ErreurNom` `ErreurIndex`
`ErreurCle` `DivisionParZero` `FichierIntrouvable`

**Méthodes** (après un point) :
- listes : `ajouter` `etendre` `inserer` `retirer` `depiler` `vider` `inverser` `compter` `copier` `trier`
- textes : `majuscule` `minuscule` `capitaliser` `titre` `separer` `joindre` `remplacer` `nettoyer`
  `commence_par` `termine_par` `trouver` `formater`
- dictionnaires : `cles` `valeurs` `elements` `obtenir`

**Modules de Python en français** : `mathematiques` (`racine` `puissance` `plafond` `plancher`
`sinus` `cosinus` `tangente` `logarithme` `factorielle`), `hasard` (`entier` `decimal` `choisir`
`melanger` `nombre`), `temps` (`maintenant` `attendre`), `systeme` (`quitter`).

**Bon à savoir**
- Les textes entre guillemets et les commentaires ne sont **jamais** modifiés.
- Dans un `f"...{ ... }..."`, le code entre accolades est traduit.
- **Tes propres noms sont respectés** : si tu crées une variable, une fonction ou un paramètre
  nommé `maximum`, `somme`, `tous`..., Baobab n'y touche pas dans ton programme.
- Tu peux mélanger français et anglais (`print` marche aussi). Ce qui n'est pas connu passe
  tel quel à Python.

## 5. Plusieurs fichiers

Un fichier `.bao` placé à côté de ton programme s'importe par son nom :

    importer outils          # charge outils.bao

Pour qu'un fichier serve à la fois de programme et de bibliothèque, termine-le ainsi :

    si programme_principal:
        serveur.demarrer(8000)

Ce bloc ne s'exécute que si on lance le fichier directement, pas quand un autre fichier
(ou un test) l'importe.

Attention : une méthode définie dans un autre fichier ne doit pas porter le nom d'une méthode
de liste ou de texte (`ajouter`, `trier`, `separer`...), sinon Baobab la traduirait à tort.

## 6. La bibliothèque française

On les importe par leur nom : `importer dates`. Les accents sont acceptés pour
`mathématiques`, `données`, `chaînes`, `sécurité` et `tâches`.

| Module | Pour faire quoi | Fonctions principales |
|---|---|---|
| `dates` | dates et heures | `date_du_jour` `heure` `aujourdhui` `annee` `mois` `jour` `nom_du_jour` `nom_du_mois` `difference_en_jours` `jours_apres` `age_depuis` `est_bissextile` |
| `fichiers` | lire et écrire des fichiers | `lire` `lire_lignes` `ecrire` `ajouter_texte` `ajouter_ligne` `existe` `supprimer` `lister` `taille` |
| `donnees` | JSON et tableaux CSV | `lire_json` `ecrire_json` `vers_json` `depuis_json` `lire_csv` `ecrire_csv` |
| `base` | base de données SQLite | `ouvrir` `executer` `chercher` `inserer` `tables` `fermer` |
| `statistiques` | analyser des chiffres | `moyenne` `mediane` `ecart_type` `pourcentage` `frequences` |
| `chaines` | travailler sur les textes | `sans_accents` `en_adresse` `compter_mots` `est_palindrome` `couper` `extraire_nombres` `mots_frequents` |
| `dessin` | dessiner (image .svg) | `avancer` `tourner_droite` `couleur` `carre` `triangle` `etoile` `cercle` `sauvegarder` ... |
| `serveur` | sites et API | `route` `repondre` `rediriger` `page` `modele` `repeter` `echapper` `cookie` `dossier_public` `documenter` `demarrer` |
| `securite` | mots de passe et signatures | `hacher_mot_de_passe` `verifier_mot_de_passe` `jeton_aleatoire` `signer` `verifier_signature` |
| `reseau` | parler avec Internet | `telecharger_texte` `telecharger_json` `telecharger_fichier` `envoyer_json` `envoyer_formulaire` `est_en_ligne` `encoder_adresse` |
| `taches` | tâches automatiques | `toutes_les` `chaque_jour` `apres` `lister` `annuler` `demarrer` |
| `tests` | tester ses programmes | `egal` `different` `est_vrai` `est_faux` `contient` `proche` `leve_erreur` `requete` `navigateur` |
| `disque` | analyser des fichiers (lecture seule) | `scanner` `rapport` `plus_gros` `doublons` `anciens` `inutiles` `images` `discussions` |

Chaque fonction a une description : ouvre le fichier du module dans `baobab/bibliotheque/`.

**Le serveur : la demande du visiteur.** Si ta fonction a un deuxième paramètre, elle reçoit
la demande :

    fonction accueil(parametres, demande):
        demande.session["visites"] = demande.session.obtenir("visites", 0) + 1
        retourner "Visite numéro " + chaine(demande.session["visites"])

La demande contient `methode`, `chemin`, `entetes`, `cookies`, `adresse_ip`, `session`
(avec `nouvelle_session()` et `fermer_session()`).

## 7. Recettes

**Analyser des notes**

    importer statistiques
    notes = [12, 15, 9, 14]
    afficher("Moyenne :", arrondir(statistiques.moyenne(notes), 2))
    afficher("Médiane :", statistiques.mediane(notes))

**Tenir un carnet**

    importer fichiers
    importer dates
    fichiers.ajouter_ligne("carnet.txt", dates.date_du_jour() + " : j'ai appris Baobab")
    pour ligne dans fichiers.lire_lignes("carnet.txt"):
        afficher(ligne)

**Garder des données dans une base**

    importer base
    c = base.ouvrir("mes_donnees.db")
    base.executer(c, "CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, texte TEXT)")
    base.inserer(c, "notes", {"texte": "Bonjour"})
    afficher(base.chercher(c, "SELECT * FROM notes"))
    base.fermer(c)

**Un petit site**

    importer serveur

    fonction accueil(parametres):
        nom = parametres.obtenir("nom", "visiteur")
        retourner serveur.page("Accueil", serveur.modele("<h1>Bonjour {{nom}} !</h1>", {"nom": nom}))

    serveur.route("/", accueil)

    si programme_principal:
        serveur.demarrer(8000)

Lance-le, puis ouvre `http://localhost:8000/?nom=Awa`. Les exemples complets sont dans
`exemples/` : `livre_or.bao`, `espace_membre.bao` (inscription et connexion),
`api_notes.bao`, `api_documentee.bao`.

**Une tâche automatique**

    importer taches
    importer dates

    fonction battement():
        afficher("Il est", dates.heure())

    taches.toutes_les(5, battement)
    taches.demarrer()

**Tester**

Dans un fichier `test_mes_calculs.bao` :

    importer tests

    fonction double(x):
        retourner x * 2

    fonction test_double():
        tests.egal(double(4), 8)

Puis : `baobab tester test_mes_calculs.bao`. Pour un site, `tests.navigateur()` simule un
visiteur qui garde ses cookies (voir `exemples/test_espace_membre.bao`).

**Analyser les fichiers de ton téléphone** (lecture seule, rien n'est supprimé)

    baobab exemples/analyse_appareil.bao

Sur Termux, lance d'abord une fois `termux-setup-storage`.

## 8. Les règles d'or de la sécurité

1. **Ne garde jamais un mot de passe** : seulement `securite.hacher_mot_de_passe(...)`.
2. Pour afficher ce qu'écrit un visiteur, utilise toujours `serveur.modele` ou `serveur.echapper`.
3. Après une connexion réussie, appelle `demande.nouvelle_session()`.
4. Garde tes clés et jetons **hors du code** (variables d'environnement), jamais sur GitHub.
5. En ligne, utilise le **HTTPS** et lance ton site avec la variable `BAOBAB_HTTPS=1`.
6. Protège `serveur.documenter(...)` avec `acces=` : cette page révèle comment ton site est fait.
7. Limite les essais de connexion (voir `exemples/espace_membre.bao`).
8. N'exécute **jamais** le programme d'un inconnu : Baobab n'a pas de protection contre ça.

## 9. En cas de problème

| Message ou symptôme | Que faire |
|---|---|
| « Erreur d'écriture : syntaxe invalide » | cherche un `:` oublié, un guillemet ou une parenthèse non fermés ; `baobab python fichier.bao` montre le Python obtenu |
| « Le nom 'x' n'existe pas. Voulais-tu dire... ? » | faute de frappe, ou variable pas encore créée |
| « Le module 'xxx' est introuvable » | vérifie l'orthographe ; si ça marche avec `python -m baobab` mais pas avec `baobab`, réinstalle : `pip uninstall baobab-francais` puis `pip install .` |
| « Fichier introuvable » | tu n'es pas dans le bon dossier : `cd` vers ton projet |
| Rien ne se passe sur Termux | autorise le stockage (`termux-setup-storage`) ; les tâches s'arrêtent quand l'écran s'éteint |
| Un test échoue | lis la ligne indiquée et la différence « Attendu ... mais obtenu ... » |

Pour vérifier tout le projet : `python -m unittest discover tests`

## 10. Les limites à connaître

- Baobab traduit vers Python : **même vitesse que Python**, et il faut Python pour l'exécuter.
- Le serveur sert à apprendre et aux petits sites : sessions en mémoire (perdues au redémarrage),
  pas de HTTPS intégré, pas de temps réel, pas encore de lecture du JSON reçu.
- Pas de fenêtres ni de boutons : Baobab produit du texte, des pages web et des images.
- Testé surtout sous Android (Termux) et Linux ; Windows et macOS pas encore vérifiés.
- Pas de vérification de sécurité par des experts : pas pour des données bancaires ou de santé.

## 11. Aller plus loin

- `docs/tutoriel.md` : 8 leçons pour débuter
- `docs/cahier-des-charges.md` : ce qui est fait et ce qui vient
- `exemples/` : des programmes à lire et à modifier
- `README.md` : la présentation du projet

## 12. Une API pour une application mobile (version 0.15.0)

Une application (Android, iPhone, Flutter, React Native, un site JavaScript) parle à ton serveur
en JSON. Le modèle complet est dans `exemples/api_mobile.bao`.

    demande.json                      le JSON reçu (dictionnaire ou liste), 400 s'il est invalide
    serveur.route(adresse, f, methodes=["GET", "PUT", "DELETE"])    les méthodes permises (sinon 405)
    serveur.refuser(404, "Introuvable")                             une erreur propre, en JSON
    serveur.repondre(contenu, code=201)                             choisir le code de réponse
    securite.creer_jeton_acces("awa", CLE, 3600, ["lecture"])       fabriquer un jeton
    serveur.exiger_jeton(demande, CLE, "lecture")                   exiger un jeton (401 ou 403 sinon)
    serveur.autoriser_origines(["https://monsite.org"])             CORS : quels sites web ont le droit
    tests.requete("/notes", json={...}, methode="PUT", entetes={...})   tester tout cela

Règles : HTTPS en ligne ; jeton à durée courte ; clé hors du code ; aucun secret dans un jeton
(il est signé mais lisible) ; CORS ne protège que les navigateurs.
