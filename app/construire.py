"""Construit app/www/index.html : l'application d'apprentissage Baobab (Pyodide + Web Worker)."""
import importlib.util
import json
import os
import re

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(RACINE, "app")
SOURCES = os.path.join(RACINE, "baobab")
SORTIE = os.path.join(APP, "www")
PYODIDE_BASE = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/"


def lire(nom):
    with open(os.path.join(APP, nom), encoding="utf-8") as f:
        return f.read()


def charger_lecons():
    spec = importlib.util.spec_from_file_location("lecons_app", os.path.join(APP, "lecons.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.LECONS


def trouver_version():
    for nom in ("__init__.py", "cli.py"):
        chemin = os.path.join(SOURCES, nom)
        if os.path.exists(chemin):
            with open(chemin, encoding="utf-8") as f:
                m = re.search(r'(?:__version__|VERSION|version)\s*=\s*["\'](\d[^"\']*)["\']', f.read())
            if m:
                return m.group(1)
    return "0.15.0"


def en_json(objet):
    return json.dumps(objet, ensure_ascii=False).replace("</", "<\\/")


fichiers = {}
for dossier, _, noms in os.walk(SOURCES):
    if "__pycache__" in dossier:
        continue
    for nom in noms:
        if nom.endswith(".py"):
            chemin = os.path.join(dossier, nom)
            relatif = "baobab/" + os.path.relpath(chemin, SOURCES).replace(os.sep, "/")
            with open(chemin, encoding="utf-8") as f:
                fichiers[relatif] = f.read()

page = lire("modele.html")
page = page.replace("__PYODIDE_BASE__", PYODIDE_BASE)
page = page.replace("__VERSION__", trouver_version())
page = page.replace("__HARNAIS__", lire("harnais.py"))
page = page.replace("__WORKER__", lire("worker.js"))
page = page.replace("__EXEMPLE__", en_json(lire("exemple_complet.bao")))
page = page.replace("__LECONS__", en_json(charger_lecons()))
page = page.replace("__SOURCES__", en_json(fichiers))
assert not re.search(r"__(SOURCES|HARNAIS|WORKER|LECONS|EXEMPLE|VERSION|PYODIDE_BASE)__", page), "placeholder restant"

os.makedirs(SORTIE, exist_ok=True)
with open(os.path.join(SORTIE, "index.html"), "w", encoding="utf-8") as f:
    f.write(page)
print("Application construite :", len(fichiers), "fichiers Baobab,", len(charger_lecons()), "leçons")
