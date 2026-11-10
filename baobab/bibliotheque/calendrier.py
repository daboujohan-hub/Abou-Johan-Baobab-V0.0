"""Calendrier en français : jour_de_la_semaine, formater_date, jours_entre..."""
import calendar
import datetime

_JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
_MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
         "août", "septembre", "octobre", "novembre", "décembre"]


def _date(annee, mois, jour):
    try:
        return datetime.date(annee, mois, jour)
    except (TypeError, ValueError):
        raise ValueError("Date invalide : {}/{}/{}".format(jour, mois, annee)) from None


def jour_de_la_semaine(annee, mois, jour):
    """(2026, 11, 10) -> « mardi »."""
    return _JOURS[_date(annee, mois, jour).weekday()]


def formater_date(annee, mois, jour):
    """(2026, 11, 10) -> « mardi 10 novembre 2026 » ; le 1er du mois s'écrit « 1er »."""
    d = _date(annee, mois, jour)
    numero = "1er" if jour == 1 else str(jour)
    return "{} {} {} {}".format(_JOURS[d.weekday()], numero, _MOIS[mois - 1], annee)


def jours_entre(annee1, mois1, jour1, annee2, mois2, jour2):
    """Nombre de jours entre deux dates (négatif si la seconde est avant la première)."""
    return (_date(annee2, mois2, jour2) - _date(annee1, mois1, jour1)).days


def est_bissextile(annee):
    return calendar.isleap(annee)


def jours_dans_mois(annee, mois):
    if not isinstance(mois, int) or not 1 <= mois <= 12:
        raise ValueError("Le mois doit être entre 1 et 12")
    return calendar.monthrange(annee, mois)[1]
