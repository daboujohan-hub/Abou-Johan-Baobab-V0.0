"""Construit app/www/index.html : un éditeur Baobab qui tourne dans le navigateur (Pyodide)."""
import json
import os

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(RACINE, "baobab")
SORTIE = os.path.join(RACINE, "app", "www")
PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js"

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

HARNAIS = """
import sys
sys.path.insert(0, "/baobab_src")
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr

_pret = {"importeur": False}

def lancer_baobab(source):
    sortie = io.StringIO()
    try:
        from baobab.transpileur import transpiler
        if not _pret["importeur"]:
            _pret["importeur"] = True
            try:
                from baobab import importeur
                if hasattr(importeur, "installer"):
                    importeur.installer()
            except Exception:
                sortie.write(traceback.format_exc())
        code = transpiler(source)
        with redirect_stdout(sortie), redirect_stderr(sortie):
            exec(compile(code, "<programme>", "exec"), {"__name__": "__main__"})
    except BaseException:
        sortie.write(traceback.format_exc())
    return sortie.getvalue()
"""

PAGE = r"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Éditeur Baobab</title>
<style>
body{font-family:sans-serif;margin:0;padding:1rem;background:#102a14;color:#e8f5e9}
h1{font-size:1.3rem;margin:.2rem 0 .8rem}
textarea{width:100%;box-sizing:border-box;height:14rem;font:14px monospace;padding:.6rem;border-radius:8px;border:1px solid #2e7d32;background:#0b1d0e;color:#e8f5e9}
button{margin:.6rem 0;padding:.7rem 1.4rem;font-size:1rem;border:0;border-radius:8px;background:#43a047;color:#fff}
button:disabled{opacity:.5}
pre{white-space:pre-wrap;background:#0b1d0e;padding:.8rem;border-radius:8px;min-height:4rem}
#statut{opacity:.8;font-size:.9rem;margin-bottom:.6rem}
</style></head><body>
<h1>🌳 Éditeur Baobab</h1>
<div id="statut">Chargement de Python (première fois : environ 10 Mo)…</div>
<textarea id="prog" spellcheck="false" autocapitalize="off">afficher("Bonjour depuis Baobab !")
importer nombres
afficher(nombres.en_lettres(2500))
afficher(nombres.formater_monnaie(75000))</textarea>
<button id="go" disabled>▶ Exécuter</button>
<pre id="sortie"></pre>
<script type="application/json" id="sources">__SOURCES__</script>
<script type="text/x-python" id="harnais">__HARNAIS__</script>
<script src="__PYODIDE__"></script>
<script>
const statut = document.getElementById("statut");
const bouton = document.getElementById("go");
const sortie = document.getElementById("sortie");
let lancer = null;

async function demarrer() {
  try {
    const py = await loadPyodide();
    const sources = JSON.parse(document.getElementById("sources").textContent);
    const creer = (d) => { try { py.FS.mkdir(d); } catch (e) {} };
    creer("/baobab_src");
    for (const [chemin, texte] of Object.entries(sources)) {
      let courant = "/baobab_src";
      for (const m of chemin.split("/").slice(0, -1)) { courant += "/" + m; creer(courant); }
      py.FS.writeFile("/baobab_src/" + chemin, texte);
    }
    py.runPython(document.getElementById("harnais").textContent);
    lancer = py.globals.get("lancer_baobab");
    statut.textContent = "Prêt.";
    bouton.disabled = false;
  } catch (e) {
    statut.textContent = "Erreur de chargement : " + e;
  }
}

bouton.onclick = () => {
  bouton.disabled = true;
  sortie.textContent = "…";
  setTimeout(() => {
    try { sortie.textContent = lancer(document.getElementById("prog").value) || "(rien affiché)"; }
    catch (e) { sortie.textContent = String(e); }
    bouton.disabled = false;
  }, 30);
};
window.addEventListener("load", demarrer);
</script></body></html>
"""

os.makedirs(SORTIE, exist_ok=True)
donnees = json.dumps(fichiers, ensure_ascii=False).replace("</", "<\\/")
page = (PAGE.replace("__SOURCES__", donnees)
            .replace("__HARNAIS__", HARNAIS)
            .replace("__PYODIDE__", PYODIDE))
with open(os.path.join(SORTIE, "index.html"), "w", encoding="utf-8") as f:
    f.write(page)
print("Page construite :", len(fichiers), "fichiers Baobab embarqués")
