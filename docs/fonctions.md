# Fonctions de Baobab

Cette page liste les 149 noms publics (fonctions et classes) des 16 modules de la
bibliothèque. Elle est **générée** : ne modifie pas la liste à la main. Change le code ou son texte
d'aide, puis lance `python docs/generer_fonctions.py`.

Pour utiliser un module : `importer nom_du_module`, puis `nom_du_module.fonction(...)`.

# À utiliser avec précaution

Règle d'or : tout ce qui vient d'un visiteur (formulaire, adresse, JSON, fichier reçu) est dangereux
tant qu'on ne l'a pas vérifié. Pour le vérifier : `serveur.valider`.

## Exécuter du code

- `avance.evaluer`, `avance.executer_texte` et `avance.compiler_texte` exécutent du VRAI code avec tes
  droits. Ce n'est pas un bac à sable. Jamais avec un texte venu d'un visiteur, d'une API ou d'un
  fichier inconnu.
- Pour lire une valeur reçue, utilise `avance.lire_valeur` (elle ne comprend que nombres, textes,
  listes, dictionnaires, vrai et faux) ou `donnees.depuis_json`.

## Fichiers

- `fichiers.supprimer` supprime pour de bon, sans corbeille. D'après le code, elle appelle directement
  `os.remove` sur le chemin donné.
- `fichiers.ecrire`, `donnees.ecrire_json`, `donnees.ecrire_csv` et `dessin.sauvegarder` remplacent un
  fichier qui existe déjà, sans demander.
- Un chemin fabriqué avec un texte du visiteur (par exemple `../`) peut sortir du dossier prévu.
  N'accepte que des noms choisis dans une liste que tu as écrite.

## Réseau

- `reseau.telecharger_texte`, `reseau.telecharger_json`, `reseau.telecharger_fichier` et
  `reseau.est_en_ligne` vont sur n'importe quelle adresse http ou https, y compris celles de ton propre
  appareil ou de ton réseau (127.0.0.1, la box...). Baobab ne les filtre pas : ne fabrique jamais
  l'adresse avec un texte du visiteur.
- `reseau.telecharger_fichier` écrit à l'endroit demandé (100 Mo au maximum) : même précaution que pour
  les fichiers.
- `reseau.envoyer_json` et `reseau.envoyer_formulaire` envoient tes données à un site : vérifie
  l'adresse. Les en-têtes secrets (Authorization, Cookie) sont refusés sur une adresse http:// qui
  n'est pas locale, et ne suivent pas une redirection vers un autre site. Une clé mise dans un en-tête
  que tu inventes toi-même, elle, n'est pas protégée.

## Base de données

- `base.executer` et `base.chercher` lancent du SQL : ne colle jamais un texte dans l'ordre SQL, passe
  les valeurs par le paramètre `valeurs`.
- `base.inserer` : le nom de la table n'est pas une valeur. Ne le prends jamais d'un visiteur.

## Serveur web

- `serveur.demarrer` : avec `hote="0.0.0.0"`, toutes les personnes du même Wi-Fi atteignent ton
  serveur. Garde `127.0.0.1` pour tes essais.
- `serveur.dossier_public` rend public tout ce qui est dans le dossier : jamais la racine du projet ni
  un dossier qui contient des clés ou des données.
- `serveur.modele` : le marqueur `|brut` coupe la protection HTML. Seulement pour du HTML que tu as
  fabriqué toi-même, jamais pour du texte de visiteur.
- `serveur.autoriser_origines` : avec `avec_cookies=True`, ne liste que tes propres sites.
- `serveur.documenter` montre toutes les routes et leurs textes d'aide à qui ouvre la page. N'y mets
  ni secret ni adresse privée, et cache des routes avec `masquer=`.
- Le serveur est éducatif : pas de HTTPS intégré, sessions gardées en mémoire, pas de jeton anti-CSRF.
  Ne l'expose pas sur Internet et ne l'utilise pas pour des données bancaires ou de santé.

## Mots de passe, jetons et clés

- `securite.hacher_mot_de_passe` : garde seulement l'empreinte, jamais le mot de passe.
- `securite.creer_jeton_acces` et `securite.signer` signent mais ne chiffrent pas : le contenu est
  lisible par tous. N'y mets aucun secret. Un jeton ne peut pas être annulé avant sa fin : donne-lui une
  durée courte.
- La clé de signature est un secret : jamais écrite dans un code envoyé sur GitHub.

## Tâches en arrière-plan

- `taches.toutes_les` et `taches.chaque_jour` continuent de tourner tant qu'on ne les arrête pas. Une
  tâche mal écrite se répète sans fin (batterie, disque, réseau). Utilise `taches.lister` pour voir ce
  qui tourne et `taches.tout_annuler` pour tout arrêter.

# Toutes les fonctions

## avance (4)

- `avance.compiler_texte(texte, mode='exec')` : Prépare du code ("exec" : un programme, "eval" : une expression) pour evaluer / executer_texte.
- `avance.evaluer(texte, variables=None)` : Calcule une expression Baobab et rend le résultat. variables : {"nom": valeur} en plus.
- `avance.executer_texte(texte, variables=None)` : Exécute un programme Baobab écrit dans un texte. Rend le dictionnaire des variables créées.
- `avance.lire_valeur(texte)` : Lit une valeur simple : nombre, texte, liste, dictionnaire, vrai, faux. Jamais de code.

## base (6)

- `base.chercher(connexion, ordre, valeurs=())` : Exécute un SELECT. Retourne une liste de dictionnaires {colonne: valeur}.
- `base.executer(connexion, ordre, valeurs=())` : Exécute un ordre SQL qui modifie la base. Retourne le nombre de lignes touchées.
- `base.fermer(connexion)`
- `base.inserer(connexion, table, valeurs)` : Ajoute une ligne : inserer(c, "notes", {"texte": "Bonjour"}). Retourne son identifiant.
- `base.ouvrir(chemin)` : Ouvre (ou crée) une base. ":memory:" crée une base temporaire.
- `base.tables(connexion)` : Les noms des tables de la base.

## calendrier (5)

- `calendrier.est_bissextile(annee)`
- `calendrier.formater_date(annee, mois, jour)` : (2026, 11, 10) -> « mardi 10 novembre 2026 » ; le 1er du mois s'écrit « 1er ».
- `calendrier.jour_de_la_semaine(annee, mois, jour)` : (2026, 11, 10) -> « mardi ».
- `calendrier.jours_dans_mois(annee, mois)`
- `calendrier.jours_entre(annee1, mois1, jour1, annee2, mois2, jour2)` : Nombre de jours entre deux dates (négatif si la seconde est avant la première).

## chaines (7)

- `chaines.compter_mots(texte)` : Nombre de mots. « aujourd'hui » et « peut-être » comptent pour un seul mot.
- `chaines.couper(texte, longueur, fin='…')` : Raccourcit un texte à `longueur` caractères au plus, avec « … » à la fin.
- `chaines.en_adresse(texte)` : Pour les adresses de sites : en_adresse("Mon Super Titre !") donne "mon-super-titre".
- `chaines.est_palindrome(texte)` : Vrai si le texte se lit pareil dans les deux sens (sans accents, majuscules ni ponctuation).
- `chaines.extraire_nombres(texte)` : Les nombres d'un texte : extraire_nombres("3 chats, 2,5 kg") donne [3, 2.5].
- `chaines.mots_frequents(texte, nombre=5)` : Les mots les plus utilisés : {mot: nombre}, sans les petits mots (le, de, et...).
- `chaines.sans_accents(texte)` : sans_accents("Élève à l'été") donne "Eleve a l'ete".

## dates (12)

- `dates.age_depuis(date_naissance)`
- `dates.annee()`
- `dates.aujourdhui()`
- `dates.date_du_jour()`
- `dates.difference_en_jours(debut, fin)`
- `dates.est_bissextile(an)`
- `dates.heure()`
- `dates.jour()`
- `dates.jours_apres(date_texte, nombre_de_jours)`
- `dates.mois()`
- `dates.nom_du_jour(date_texte=None)`
- `dates.nom_du_mois(numero=None)`

## dessin (16)

- `dessin.aller_a(x, y)` : Va au point (x, y). Le centre de la feuille est (0, 0).
- `dessin.avancer(distance)`
- `dessin.carre(cote)`
- `dessin.cercle(rayon)` : Cercle centré sur la position de la tortue.
- `dessin.couleur(nom)` : Couleur du trait : "red", "blue", "green", "#ff8800"...
- `dessin.epaisseur(taille)`
- `dessin.etoile(taille)`
- `dessin.fond(nom)`
- `dessin.lever_crayon()`
- `dessin.nouvelle_feuille(largeur=400, hauteur=400)` : Efface tout et recommence avec une feuille vierge.
- `dessin.poser_crayon()`
- `dessin.reculer(distance)`
- `dessin.sauvegarder(nom='dessin.svg')`
- `dessin.tourner_droite(angle)`
- `dessin.tourner_gauche(angle)`
- `dessin.triangle(cote)`

## disque (20)

- `disque.Fichier(chemin, relatif, taille, modifie, extension, categorie)` : Fichier(chemin, relatif, taille, modifie, extension, categorie)
- `disque.anciens(fichiers, jours=365)` : Fichiers non modifiés depuis plus de N jours (les plus lourds d'abord).
- `disque.appartient_a_une_application(fichier)` : Vrai si le fichier est rangé dans Android/... (dossiers gérés par les applications).
- `disque.categorie_de(chemin)`
- `disque.contenant(fichiers, mot)` : Fichiers dont le chemin contient ce mot (ex : '20261008', 'VID', 'IMG').
- `disque.discussions(fichiers)` : Fichiers rangés dans les dossiers d'applications de discussion (WhatsApp...).
- `disque.doublons(fichiers)` : Groupes de fichiers strictement identiques (même contenu).
- `disque.espace_gaspille(groupes)` : Place qu'on gagnerait en gardant UN seul exemplaire de chaque groupe.
- `disque.formater_taille(octets)` : 12345678 -> '11,8 Mo'
- `disque.images(fichiers)`
- `disque.inaccessibles()` : Les dossiers que le dernier scan n'a pas pu ouvrir (permissions).
- `disque.installateurs(fichiers)` : Fichiers d'installation d'applications (.apk), les plus lourds d'abord.
- `disque.inutiles(fichiers)` : Fichiers probablement jetables : [(fichier, raison)], les plus lourds d'abord.
- `disque.inutiles_par_raison(fichiers)` : {raison: (nombre, taille)}, du plus lourd au plus léger.
- `disque.par_application(fichiers)` : {application: (nombre, taille, nombre d'images)} pour WhatsApp, Telegram...
- `disque.plus_gros(fichiers, nombre=10)`
- `disque.rapport(fichiers, nombre=5)` : Un rapport en français, prêt à afficher.
- `disque.resume(fichiers)` : {type: (nombre, taille)}, du plus lourd au plus léger.
- `disque.scanner(dossier)` : Liste tous les fichiers du dossier (et de ses sous-dossiers).
- `disque.taille_totale(fichiers)`

## donnees (6)

- `donnees.depuis_json(texte)` : Transforme un texte JSON en liste, dictionnaire, nombre...
- `donnees.ecrire_csv(chemin, lignes, separateur=',')` : Écrit une liste de dictionnaires dans un tableau CSV.
- `donnees.ecrire_json(chemin, valeur)` : Écrit en JSON lisible. Le fichier est remplacé d'un seul coup :
- `donnees.lire_csv(chemin, separateur=',')` : Lit un tableau CSV : une liste de dictionnaires.
- `donnees.lire_json(chemin)`
- `donnees.vers_json(valeur)` : Transforme une liste ou un dictionnaire en texte JSON.

## fichiers (9)

- `fichiers.ajouter_ligne(chemin, texte)`
- `fichiers.ajouter_texte(chemin, texte)`
- `fichiers.ecrire(chemin, texte)`
- `fichiers.existe(chemin)`
- `fichiers.lire(chemin)`
- `fichiers.lire_lignes(chemin)`
- `fichiers.lister(dossier='.')`
- `fichiers.supprimer(chemin)`
- `fichiers.taille(chemin)`

## nombres (3)

- `nombres.en_lettres(n)` : 1500 -> « mille cinq cents ».
- `nombres.formater_monnaie(n, devise='FCFA')` : 5000 -> « 5 000 FCFA ».
- `nombres.formater_nombre(n)` : 1500000 -> « 1 500 000 ».

## reseau (8)

- `reseau.ErreurReseau()` : Le site n'a pas répondu comme prévu (pas de connexion, page introuvable...).
- `reseau.encoder_adresse(parametres)` : encoder_adresse({"q": "baobab", "page": 2}) donne 'q=baobab&page=2'
- `reseau.envoyer_formulaire(url, donnees, entetes=None, delai=10, methode='POST')` : Envoie un formulaire ({"nom": "valeur"}). Retourne le texte de la réponse.
- `reseau.envoyer_json(url, donnees, entetes=None, delai=10, methode='POST')` : Envoie `donnees` en JSON. Retourne la réponse en liste ou dictionnaire (ou rien si vide).
- `reseau.est_en_ligne(url, delai=5)` : Vrai si le site répond sans erreur. Ne provoque jamais d'erreur.
- `reseau.telecharger_fichier(url, chemin, taille_max=104857600, delai=10, entetes=None)` : Enregistre le fichier dans `chemin`. Retourne sa taille en octets.
- `reseau.telecharger_json(url, delai=10, entetes=None)` : Va chercher du JSON et le transforme en liste ou dictionnaire.
- `reseau.telecharger_texte(url, delai=10, entetes=None)` : Le texte d'une page ou d'un fichier texte. entetes : {"Nom": "valeur"} en plus.

## securite (7)

- `securite.creer_jeton_acces(identite, cle, duree=3600, droits=())` : Fabrique un jeton d'accès pour une application (envoyé dans « Authorization: Bearer ... »).
- `securite.hacher_mot_de_passe(mot_de_passe)` : Transforme un mot de passe en empreinte, impossible à ramener au mot de passe.
- `securite.jeton_aleatoire(octets=32)` : Un code secret impossible à deviner (liens de réinitialisation, invitations, clés).
- `securite.signer(valeur, cle, duree=None)` : Ajoute une signature : si quelqu'un modifie la valeur, on le détectera.
- `securite.verifier_jeton_acces(jeton, cle)` : Retourne {"identite": ..., "droits": [...]} si le jeton est bon, sinon None.
- `securite.verifier_mot_de_passe(mot_de_passe, empreinte)` : Vrai si ce mot de passe correspond à l'empreinte. Ne provoque jamais d'erreur.
- `securite.verifier_signature(texte_signe, cle)` : Retourne la valeur d'origine si la signature est bonne, sinon None (rien).

## serveur (22)

- `serveur.Cookie(nom, valeur, duree=None, securise=None, http_seulement=True, meme_site='Lax', chemin='/')` : Un cookie à envoyer au visiteur. Fabrique-le avec serveur.cookie(...).
- `serveur.Demande(gestionnaire, chemin, corps=b'')` : Ce que le visiteur a envoyé. Ajoute un 2e paramètre à ta fonction pour la recevoir :
- `serveur.ErreurHTTP(code, message='', entetes=None, details=None)` : Arrête la demande avec un code précis : lever serveur.ErreurHTTP(404, "Note introuvable")
- `serveur.Reponse(contenu='', code=200, entetes=None, cookies=None, type_contenu=None)` : Ce que ton application répond : contenu, code, en-têtes, cookies.
- `serveur.Session(identifiant, donnees=None)` : Ce que ton site retient d'un visiteur. Utilise-la comme un dictionnaire.
- `serveur.application_installable(nom, couleur='#2e7d32', nom_court=None, description='', icone=None, fond='#ffffff', page_d_accueil='/')` : Rend ton site installable sur l'écran d'accueil du téléphone (application web, PWA).
- `serveur.autoriser_origines(origines, avec_cookies=False, entetes=())` : Autorise des sites ou des applications web à appeler ton API depuis un navigateur (CORS).
- `serveur.cookie(nom, valeur, duree=None, securise=None, http_seulement=True, meme_site='Lax')` : Fabrique un cookie. duree = secondes (0 = effacer le cookie).
- `serveur.demarrer(port=None, hote=None)` : Démarre le serveur. Ctrl+C pour l'arrêter.
- `serveur.documenter(chemin='/documentation', titre='Documentation', masquer=(), acces=None)` : Crée une page qui liste automatiquement les adresses de ton application.
- `serveur.dossier_public(dossier, prefixe='/statique')` : Sert les fichiers d'un dossier (CSS, images, JavaScript...).
- `serveur.echapper(texte)` : Rend un texte sans danger avant de l'afficher dans une page.
- `serveur.exiger_jeton(demande, cle, droit=None)` : Exige un jeton d'accès valide (en-tête « Authorization: Bearer ... »).
- `serveur.limiter(demande, nom, maximum, duree, cle=None)` : Limite le nombre de demandes : au-delà, la demande s'arrête avec le code 429.
- `serveur.modele(texte, valeurs)` : Une page à trous : modele("Bonjour {{nom}} !", {"nom": "Awa"}).
- `serveur.page(titre, contenu, css=None)` : Fabrique une page HTML complète. css="/statique/style.css" pour ta propre feuille de style.
- `serveur.rediriger(chemin)` : À retourner par une fonction pour envoyer le visiteur vers une autre page.
- `serveur.refuser(code, message='', details=None)` : Arrête la demande tout de suite : serveur.refuser(404, "Cette note n'existe pas")
- `serveur.repeter(ligne, elements)` : Répète un modèle pour chaque élément d'une liste.
- `serveur.repondre(contenu='', code=200, entetes=None, cookies=None, type_contenu=None)` : Choisis ta réponse : repondre({"erreur": "introuvable"}, code=404)
- `serveur.route(chemin, fonction=None, methodes=None)` : Associe une adresse (ex: "/contact") à une fonction.
- `serveur.valider(donnees, regles)` : Vérifie les données reçues. Retourne les données propres, ou arrête la demande (code 422).

## statistiques (5)

- `statistiques.ecart_type(valeurs, echantillon=False)` : À quel point les valeurs s'éloignent de la moyenne.
- `statistiques.frequences(valeurs)` : Combien de fois chaque valeur apparaît : {valeur: nombre}, la plus fréquente d'abord.
- `statistiques.mediane(valeurs)` : La valeur du milieu quand on range les nombres du plus petit au plus grand.
- `statistiques.moyenne(valeurs)` : La moyenne : la somme divisée par le nombre de valeurs.
- `statistiques.pourcentage(partie, total, decimales=1)` : pourcentage(1, 4) donne 25.0

## taches (7)

- `taches.annuler(nom)` : Supprime les tâches de ce nom. Retourne le nombre de tâches supprimées.
- `taches.apres(secondes, fonction=None, nom=None)` : Lance la fonction une seule fois, dans N secondes.
- `taches.chaque_jour(heure, fonction=None, nom=None)` : Lance la fonction tous les jours à HH:MM (ex: "08:30").
- `taches.demarrer()` : Garde le programme en vie pour que les tâches continuent. Ctrl+C pour arrêter.
- `taches.lister()` : La liste des tâches prévues, en texte.
- `taches.tout_annuler()`
- `taches.toutes_les(secondes, fonction=None, nom=None)` : Lance la fonction toutes les N secondes.

## tests (12)

- `tests.Navigateur()` : Un faux navigateur : il garde les cookies d'une requête à l'autre.
- `tests.Reponse(code, texte, adresse, entetes=None, cookies_bruts=None)` : Ce que ton application a répondu.
- `tests.contient(ensemble, element)`
- `tests.different(a, b)`
- `tests.egal(obtenu, attendu)`
- `tests.est_faux(valeur)`
- `tests.est_vrai(valeur)`
- `tests.leve_erreur(fonction, classe=<class 'Exception'>)` : Vérifie que la fonction (sans argument) provoque bien cette erreur.
- `tests.navigateur()` : Un faux navigateur avec ses propres cookies (un par visiteur à simuler).
- `tests.ne_contient_pas(ensemble, element)`
- `tests.proche(a, b, marge=0.001)`
- `tests.requete(chemin, donnees=None, entetes=None, cookies=None, json=None, methode=None)` : Visite une page de ton application, sans navigateur.

