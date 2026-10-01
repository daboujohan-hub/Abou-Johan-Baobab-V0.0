"""Permet d'importer des fichiers .bao depuis d'autres fichiers Baobab.

    importer outils        # charge outils.bao, placé à côté du programme
"""

import importlib.abc
import importlib.util
import os
import sys

from .transpileur import transpiler

_dossiers = []


def ajouter_dossier(dossier):
    """Indique un dossier où chercher les fichiers .bao à importer."""
    if dossier not in _dossiers:
        _dossiers.append(dossier)


class _Chargeur(importlib.abc.Loader):
    def __init__(self, chemin):
        self.chemin = chemin

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        with open(self.chemin, encoding="utf-8") as f:
            code_baobab = f.read()
        code = compile(transpiler(code_baobab), self.chemin, "exec")
        exec(code, module.__dict__)


class _Chercheur(importlib.abc.MetaPathFinder):
    def find_spec(self, nom, chemin=None, cible=None):
        if "." in nom:
            return None
        for dossier in _dossiers:
            candidat = os.path.join(dossier, nom + ".bao")
            if os.path.isfile(candidat):
                return importlib.util.spec_from_file_location(
                    nom, candidat, loader=_Chargeur(candidat)
                )
        return None


def installer():
    if not any(isinstance(f, _Chercheur) for f in sys.meta_path):
        sys.meta_path.append(_Chercheur())
