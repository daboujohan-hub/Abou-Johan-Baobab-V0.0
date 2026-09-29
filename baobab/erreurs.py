import re

SYNTAXE = {
    "invalid syntax": "syntaxe invalide",
    "expected ':'": "il manque le signe ':' à la fin de la ligne",
    "unterminated string literal": "texte non fermé (il manque un guillemet)",
    "unexpected indent": "espaces inattendus au début de la ligne",
    "expected an indented block": "il faut décaler la ligne suivante avec 4 espaces",
    "unindent does not match": "l'indentation ne correspond à aucun bloc précédent",
    "was never closed": "une parenthèse ou un crochet n'est pas fermé",
}


def _traduire_syntaxe(message):
    for anglais, francais in SYNTAXE.items():
        if anglais in message:
            return francais
    return message


def expliquer(exception):
    """Retourne une phrase en français qui explique l'erreur."""
    msg = str(exception)

    if isinstance(exception, SyntaxError):
        return "Erreur d'écriture : " + _traduire_syntaxe(exception.msg or msg)
    if isinstance(exception, ModuleNotFoundError):
        m = re.search(r"'(.+?)'", msg)
        return f"Le module '{m.group(1) if m else '?'}' est introuvable."
    if isinstance(exception, NameError):
        m = re.search(r"'(.+?)'", msg)
        nom = m.group(1) if m else "?"
        return f"Le nom '{nom}' n'existe pas. Vérifie l'orthographe ou crée-le d'abord."
    if isinstance(exception, AttributeError):
        noms = re.findall(r"'(.+?)'", msg)
        if noms:
            return f"Cet objet n'a pas de '{noms[-1]}'. Vérifie le nom de la méthode."
        return "Cet objet n'a pas cette méthode."
    if isinstance(exception, ZeroDivisionError):
        return "Division par zéro : on ne peut pas diviser par 0."
    if isinstance(exception, IndexError):
        return "Cette position n'existe pas dans la liste (trop grande)."
    if isinstance(exception, KeyError):
        return f"Cette clé n'existe pas : {msg}"
    if isinstance(exception, FileNotFoundError):
        return "Fichier introuvable. Vérifie le nom et le dossier."
    if isinstance(exception, ValueError):
        return "Valeur incorrecte : la conversion est impossible (ex: entier('abc'))."
    if isinstance(exception, TypeError):
        return "Types incompatibles : tu mélanges par exemple un texte et un nombre."
    if isinstance(exception, KeyboardInterrupt):
        return "Programme interrompu."
    return f"Erreur ({type(exception).__name__}) : {msg}"
