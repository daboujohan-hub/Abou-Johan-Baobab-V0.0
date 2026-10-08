"""Module disque : analyser les fichiers d'un dossier ou d'un appareil.

    importer disque

    trouves = disque.scanner("~/storage/shared")
    afficher(disque.rapport(trouves))

LECTURE SEULE : ce module ne supprime, ne déplace et ne modifie aucun fichier.
Il regarde les noms, les tailles et les dates. Il ne lit jamais le contenu de
tes messages (seulement, pour chercher les doublons, le contenu des fichiers
qui ont exactement la même taille).
"""

import hashlib
import os
import time
from collections import namedtuple

Fichier = namedtuple("Fichier", "chemin relatif taille modifie extension categorie")

CATEGORIES = {
    "images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".heic", ".heif", ".svg"},
    "vidéos": {".mp4", ".mkv", ".avi", ".mov", ".3gp", ".webm"},
    "audio": {".mp3", ".m4a", ".aac", ".wav", ".ogg", ".opus", ".flac", ".amr"},
    "documents": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
                  ".txt", ".odt", ".csv", ".md"},
    "archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "applications": {".apk", ".xapk", ".aab"},
}

# Signes qu'un fichier est probablement jetable (à vérifier par toi !)
EXTENSIONS_JETABLES = {".tmp", ".temp", ".bak", ".old", ".part", ".crdownload", ".swp"}
NOMS_JETABLES = {"thumbs.db", ".ds_store", "desktop.ini"}
DOSSIERS_JETABLES = {".thumbnails", "thumbnails", ".cache", "cache", "tmp", "temp",
                     "__pycache__"}

# Dossiers laissés par les applications de discussion
APPLICATIONS_DISCUSSION = ("whatsapp", "telegram", "signal", "messenger", "viber", "wechat")

_inaccessibles = []


def formater_taille(octets):
    """12345678 -> '11,8 Mo'"""
    valeur = float(octets)
    for unite in ("o", "Ko", "Mo", "Go"):
        if valeur < 1024 or unite == "Go":
            if unite == "o":
                return f"{int(valeur)} o"
            return f"{valeur:.1f}".replace(".", ",") + f" {unite}"
        valeur /= 1024


def categorie_de(chemin):
    extension = os.path.splitext(str(chemin))[1].lower()
    for nom, extensions in CATEGORIES.items():
        if extension in extensions:
            return nom
    return "autres"


def scanner(dossier):
    """Liste tous les fichiers du dossier (et de ses sous-dossiers)."""
    racine = os.path.abspath(os.path.expanduser(str(dossier)))
    if not os.path.isdir(racine):
        raise FileNotFoundError(f"Dossier introuvable : {racine}")

    _inaccessibles.clear()
    trouves = []
    a_visiter = [racine]
    while a_visiter:
        courant = a_visiter.pop()
        try:
            with os.scandir(courant) as entrees:
                for entree in entrees:
                    try:
                        if entree.is_symlink():
                            continue
                        if entree.is_dir(follow_symlinks=False):
                            a_visiter.append(entree.path)
                        elif entree.is_file(follow_symlinks=False):
                            infos = entree.stat(follow_symlinks=False)
                            trouves.append(Fichier(
                                entree.path,
                                os.path.relpath(entree.path, racine),
                                infos.st_size,
                                infos.st_mtime,
                                os.path.splitext(entree.name)[1].lower(),
                                categorie_de(entree.name),
                            ))
                    except OSError:
                        continue
        except OSError:
            _inaccessibles.append(courant)
    return trouves


def inaccessibles():
    """Les dossiers que le dernier scan n'a pas pu ouvrir (permissions)."""
    return list(_inaccessibles)


def taille_totale(fichiers):
    return sum(f.taille for f in fichiers)


def resume(fichiers):
    """{type: (nombre, taille)}, du plus lourd au plus léger."""
    totaux = {}
    for f in fichiers:
        nombre, taille = totaux.get(f.categorie, (0, 0))
        totaux[f.categorie] = (nombre + 1, taille + f.taille)
    return dict(sorted(totaux.items(), key=lambda element: -element[1][1]))


def plus_gros(fichiers, nombre=10):
    return sorted(fichiers, key=lambda f: -f.taille)[:nombre]


def anciens(fichiers, jours=365):
    """Fichiers non modifiés depuis plus de N jours (les plus lourds d'abord)."""
    limite = time.time() - jours * 86400
    return sorted((f for f in fichiers if f.modifie < limite), key=lambda f: -f.taille)


def images(fichiers):
    return [f for f in fichiers if f.categorie == "images"]


def discussions(fichiers):
    """Fichiers rangés dans les dossiers d'applications de discussion (WhatsApp...)."""
    return [f for f in fichiers
            if any(nom in f.chemin.lower() for nom in APPLICATIONS_DISCUSSION)]


def _empreinte(chemin, limite=None):
    h = hashlib.sha256()
    lu = 0
    with open(chemin, "rb") as fichier:
        while True:
            morceau = fichier.read(1024 * 1024)
            if not morceau:
                break
            h.update(morceau)
            lu += len(morceau)
            if limite and lu >= limite:
                break
    return h.hexdigest()


def doublons(fichiers):
    """Groupes de fichiers strictement identiques (même contenu)."""
    par_taille = {}
    for f in fichiers:
        if f.taille > 0:
            par_taille.setdefault(f.taille, []).append(f)

    groupes = []
    for candidats in par_taille.values():
        if len(candidats) < 2:
            continue
        par_debut = {}
        for f in candidats:
            try:
                par_debut.setdefault(_empreinte(f.chemin, 65536), []).append(f)
            except OSError:
                continue
        for memes_debuts in par_debut.values():
            if len(memes_debuts) < 2:
                continue
            complets = {}
            for f in memes_debuts:
                try:
                    complets.setdefault(_empreinte(f.chemin), []).append(f)
                except OSError:
                    continue
            groupes += [g for g in complets.values() if len(g) > 1]
    return sorted(groupes, key=lambda g: -espace_gaspille([g]))


def espace_gaspille(groupes):
    """Place qu'on gagnerait en gardant UN seul exemplaire de chaque groupe."""
    return sum((len(g) - 1) * g[0].taille for g in groupes)


def appartient_a_une_application(fichier):
    """Vrai si le fichier est rangé dans Android/... (dossiers gérés par les applications)."""
    return f"{os.sep}android{os.sep}" in fichier.chemin.lower()


def inutiles(fichiers):
    """Fichiers probablement jetables : [(fichier, raison)], les plus lourds d'abord.

    Ce sont des indices, pas des certitudes : à vérifier toi-même !
    """
    resultat = []
    for f in fichiers:
        nom = os.path.basename(f.chemin).lower()
        dossiers = {d.lower() for d in f.relatif.split(os.sep)[:-1]}
        if f.taille == 0:
            resultat.append((f, "fichier vide"))
        elif f.extension in EXTENSIONS_JETABLES:
            resultat.append((f, f"fichier temporaire ou copie ({f.extension})"))
        elif nom in NOMS_JETABLES:
            resultat.append((f, "fichier système inutile"))
        elif dossiers & DOSSIERS_JETABLES:
            resultat.append((f, "dossier de cache ou de miniatures"))
    return sorted(resultat, key=lambda element: -element[0].taille)


def inutiles_par_raison(fichiers):
    """{raison: (nombre, taille)}, du plus lourd au plus léger."""
    totaux = {}
    for f, raison in inutiles(fichiers):
        nombre, taille = totaux.get(raison, (0, 0))
        totaux[raison] = (nombre + 1, taille + f.taille)
    return dict(sorted(totaux.items(), key=lambda element: -element[1][1]))


def installateurs(fichiers):
    """Fichiers d'installation d'applications (.apk), les plus lourds d'abord."""
    return sorted((f for f in fichiers if f.categorie == "applications"),
                  key=lambda f: -f.taille)


def par_application(fichiers):
    """{application: (nombre, taille, nombre d'images)} pour WhatsApp, Telegram..."""
    totaux = {}
    for f in fichiers:
        chemin = f.chemin.lower()
        for nom in APPLICATIONS_DISCUSSION:
            if nom in chemin:
                nombre, taille, images_ = totaux.get(nom, (0, 0, 0))
                totaux[nom] = (nombre + 1, taille + f.taille,
                               images_ + (1 if f.categorie == "images" else 0))
                break
    return dict(sorted(totaux.items(), key=lambda element: -element[1][1]))


def contenant(fichiers, mot):
    """Fichiers dont le chemin contient ce mot (ex : '20261008', 'VID', 'IMG')."""
    mot = str(mot).lower()
    return [f for f in fichiers if mot in f.relatif.lower()]


def _lignes(titre, elements):
    return [titre] + [f"  {ligne}" for ligne in elements]


def rapport(fichiers, nombre=5):
    """Un rapport en français, prêt à afficher."""
    sortie = [f"📊 {len(fichiers)} fichiers, {formater_taille(taille_totale(fichiers))} au total", ""]

    sortie += _lignes("Par type :", [
        f"{nom} : {n} ({formater_taille(t)})" for nom, (n, t) in resume(fichiers).items()
    ])

    sortie += ["", *_lignes(f"🔎 Les {nombre} plus gros fichiers :", [
        f"{formater_taille(f.taille)}  {f.relatif}" for f in plus_gros(fichiers, nombre)
    ])]

    apk = installateurs(fichiers)
    if apk:
        sortie += ["", f"📦 Installateurs d'applications (.apk) : {len(apk)} "
                       f"({formater_taille(taille_totale(apk))})",
                   "  Une fois l'application installée, on n'en a en général plus besoin :"]
        sortie += [f"  {formater_taille(f.taille)}  {f.relatif}" for f in apk[:nombre]]

    groupes = doublons(fichiers)
    sortie += ["", f"🔁 Doublons : {len(groupes)} groupe(s), "
                   f"{formater_taille(espace_gaspille(groupes))} récupérables"]
    for g in groupes[:nombre]:
        sortie.append(f"  {len(g)} copies de {formater_taille(g[0].taille)} : {g[0].relatif}")

    vieux = anciens(fichiers)
    sortie += ["", f"🕰️  Non modifiés depuis plus d'un an : {len(vieux)} "
                   f"({formater_taille(taille_totale(vieux))})"]
    for f in vieux[:nombre]:
        sortie.append(f"  {formater_taille(f.taille)}  {f.relatif}")

    jetables = inutiles(fichiers)
    sortie += ["", f"🗑️  Probablement inutiles (à vérifier) : {len(jetables)} "
                   f"({formater_taille(taille_totale([f for f, _ in jetables]))})"]
    for raison, (n, t) in inutiles_par_raison(fichiers).items():
        sortie.append(f"  {raison} : {n} fichier(s), {formater_taille(t)}")
    if jetables:
        sortie.append("  Les plus lourds :")
        for f, _ in jetables[:nombre]:
            sortie.append(f"    {formater_taille(f.taille)}  {f.relatif}")
    chez_les_applications = [f for f, _ in jetables if appartient_a_une_application(f)]
    if chez_les_applications:
        sortie += [f"  ⚠️  {len(chez_les_applications)} fichier(s) dans Android/... : "
                   "ces dossiers appartiennent aux applications.",
                   "  Ne les supprime pas à la main : fais-le depuis l'application "
                   "(ex : WhatsApp > Stockage)."]

    chats = discussions(fichiers)
    sortie += ["", f"💬 Médias des applications de discussion : {len(chats)} fichiers "
                   f"({formater_taille(taille_totale(chats))})"]
    for application, (n, t, nb_images) in par_application(fichiers).items():
        sortie.append(f"  {application} : {n} fichiers ({formater_taille(t)}), "
                      f"dont {nb_images} image(s)")

    if _inaccessibles:
        sortie += ["", f"⚠️  {len(_inaccessibles)} dossier(s) non lisibles (permissions) :"]
        sortie += [f"  {d}" for d in _inaccessibles[:nombre]]

    sortie += ["", "Rien n'a été supprimé ni modifié."]
    return "\n".join(sortie)
