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
