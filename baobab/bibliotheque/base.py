"""Module base : une base de données SQLite, en français.

    importer base

    c = base.ouvrir("mes_donnees.db")
    base.executer(c, "CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, texte TEXT)")
    base.inserer(c, "notes", {"texte": "Bonjour"})
    afficher(base.chercher(c, "SELECT * FROM notes"))
    base.fermer(c)
"""

import re
import sqlite3
import threading

_verrou = threading.RLock()
_NOM_VALIDE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _verifier_nom(nom, genre):
    if not _NOM_VALIDE.match(str(nom)):
        raise ValueError(
            f"Nom de {genre} invalide : {nom!r} (lettres, chiffres et _ seulement)")
    return nom


def ouvrir(chemin):
    """Ouvre (ou crée) une base. ":memory:" crée une base temporaire."""
    return sqlite3.connect(str(chemin), check_same_thread=False)


def fermer(connexion):
    with _verrou:
        connexion.close()


def executer(connexion, ordre, valeurs=()):
    """Exécute un ordre SQL qui modifie la base. Retourne le nombre de lignes touchées.

    Mets les valeurs avec des ? : executer(c, "UPDATE notes SET texte = ? WHERE id = ?", ["Salut", 1])
    """
    with _verrou:
        curseur = connexion.execute(ordre, tuple(valeurs))
        connexion.commit()
        return curseur.rowcount


def chercher(connexion, ordre, valeurs=()):
    """Exécute un SELECT. Retourne une liste de dictionnaires {colonne: valeur}."""
    with _verrou:
        curseur = connexion.execute(ordre, tuple(valeurs))
        colonnes = [description[0] for description in curseur.description or []]
        return [dict(zip(colonnes, ligne)) for ligne in curseur.fetchall()]


def inserer(connexion, table, valeurs):
    """Ajoute une ligne : inserer(c, "notes", {"texte": "Bonjour"}). Retourne son identifiant."""
    if not valeurs:
        raise ValueError("Il faut au moins une valeur à insérer")
    _verifier_nom(table, "table")
    colonnes = [_verifier_nom(nom, "colonne") for nom in valeurs]
    ordre = (f"INSERT INTO {table} ({', '.join(colonnes)}) "
             f"VALUES ({', '.join('?' for _ in colonnes)})")
    with _verrou:
        curseur = connexion.execute(ordre, tuple(valeurs[nom] for nom in colonnes))
        connexion.commit()
        return curseur.lastrowid


def tables(connexion):
    """Les noms des tables de la base."""
    lignes = chercher(
        connexion,
        "SELECT name FROM sqlite_master WHERE type = 'table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name")
    return [ligne["name"] for ligne in lignes]
