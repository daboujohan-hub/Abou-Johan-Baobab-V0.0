"""Module dates. Les dates sont en texte : "AAAA-MM-JJ" (ex : "2026-09-29")."""

import calendar
import datetime

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def _lire(date_texte):
    return datetime.date.fromisoformat(date_texte)


def aujourdhui():
    return datetime.date.today().isoformat()


def annee():
    return datetime.date.today().year


def mois():
    return datetime.date.today().month


def jour():
    return datetime.date.today().day


def heure():
    return datetime.datetime.now().strftime("%H:%M:%S")


def nom_du_jour(date_texte=None):
    d = _lire(date_texte) if date_texte else datetime.date.today()
    return JOURS[d.weekday()]


def nom_du_mois(numero=None):
    if numero is None:
        numero = datetime.date.today().month
    return MOIS[numero - 1]


def date_du_jour():
    d = datetime.date.today()
    return f"{JOURS[d.weekday()]} {d.day} {MOIS[d.month - 1]} {d.year}"


def difference_en_jours(debut, fin):
    return (_lire(fin) - _lire(debut)).days


def jours_apres(date_texte, nombre_de_jours):
    d = _lire(date_texte) + datetime.timedelta(days=nombre_de_jours)
    return d.isoformat()


def age_depuis(date_naissance):
    n = _lire(date_naissance)
    t = datetime.date.today()
    return t.year - n.year - ((t.month, t.day) < (n.month, n.day))


def est_bissextile(an):
    return calendar.isleap(an)
