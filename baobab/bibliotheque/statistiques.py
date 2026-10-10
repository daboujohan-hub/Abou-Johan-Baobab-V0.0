"""Module statistiques : analyser des chiffres.

    importer statistiques

    notes = [12, 15, 9, 14]
    afficher(statistiques.moyenne(notes))
    afficher(statistiques.frequences(notes))
"""

import statistics
from collections import Counter


def _liste_non_vide(valeurs):
    liste = list(valeurs)
    if not liste:
        raise ValueError("La liste est vide : il faut au moins une valeur")
    return liste


def moyenne(valeurs):
    """La moyenne : la somme divisée par le nombre de valeurs."""
    return statistics.fmean(_liste_non_vide(valeurs))


def mediane(valeurs):
    """La valeur du milieu quand on range les nombres du plus petit au plus grand."""
    return statistics.median(_liste_non_vide(valeurs))


def ecart_type(valeurs, echantillon=False):
    """À quel point les valeurs s'éloignent de la moyenne.

    Par défaut : l'écart type de la population, celui du lycée (σ).
    Avec echantillon=vrai : la version « échantillon » (comme ECARTYPE dans Excel).
    """
    liste = _liste_non_vide(valeurs)
    if echantillon:
        return statistics.stdev(liste)
    return statistics.pstdev(liste)


def pourcentage(partie, total, decimales=1):
    """pourcentage(1, 4) donne 25.0"""
    return round(100 * partie / total, decimales)


def frequences(valeurs):
    """Combien de fois chaque valeur apparaît : {valeur: nombre}, la plus fréquente d'abord."""
    return dict(Counter(valeurs).most_common())
