"""Nombres et montants en français : en_lettres, formater_nombre, formater_monnaie."""

_UNITES = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit",
           "neuf", "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize"]
_DIZAINES = {2: "vingt", 3: "trente", 4: "quarante", 5: "cinquante", 6: "soixante"}


def _moins_de_100(n, final=True):
    if n < 17:
        return _UNITES[n]
    if n < 20:
        return "dix-" + _UNITES[n - 10]
    if n < 70:
        d, u = divmod(n, 10)
        mot = _DIZAINES[d]
        if u == 0:
            return mot
        if u == 1:
            return mot + " et un"
        return mot + "-" + _UNITES[u]
    if n < 80:
        if n == 71:
            return "soixante et onze"
        return "soixante-" + _moins_de_100(n - 60)
    if n == 80:
        return "quatre-vingts" if final else "quatre-vingt"
    return "quatre-vingt-" + _moins_de_100(n - 80)


def _moins_de_1000(n, final):
    """final : vrai si rien ne suit ce groupe (pour « cents » et « quatre-vingts »)."""
    centaines, reste = divmod(n, 100)
    parties = []
    if centaines:
        mot = "cent" if centaines == 1 else _UNITES[centaines] + " cent"
        if reste == 0 and final and centaines > 1:
            mot += "s"
        parties.append(mot)
    if reste:
        parties.append(_moins_de_100(reste, final))
    return " ".join(parties)


def en_lettres(n):
    """1500 -> « mille cinq cents »."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("en_lettres attend un nombre entier")
    if n < 0:
        return "moins " + en_lettres(-n)
    if n == 0:
        return "zéro"
    if n >= 10 ** 12:
        raise ValueError("Nombre trop grand (maximum : 999 999 999 999)")
    milliards, reste = divmod(n, 10 ** 9)
    millions, reste = divmod(reste, 10 ** 6)
    milliers, unites = divmod(reste, 1000)
    parties = []
    if milliards:
        parties.append(_moins_de_1000(milliards, True) + (" milliard" if milliards == 1 else " milliards"))
    if millions:
        parties.append(_moins_de_1000(millions, True) + (" million" if millions == 1 else " millions"))
    if milliers:
        parties.append("mille" if milliers == 1 else _moins_de_1000(milliers, False) + " mille")
    if unites:
        parties.append(_moins_de_1000(unites, True))
    return " ".join(parties)


def formater_nombre(n):
    """1500000 -> « 1 500 000 »."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("formater_nombre attend un nombre entier")
    return f"{n:,}".replace(",", " ")


def formater_monnaie(n, devise="FCFA"):
    """5000 -> « 5 000 FCFA »."""
    return formater_nombre(n) + " " + devise
