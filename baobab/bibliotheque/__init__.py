import importlib
import pkgutil
import sys


def enregistrer():
    """Rend chaque module du dossier importable sous le nom baobab_<nom>."""
    for info in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f"{__name__}.{info.name}")
        sys.modules[f"baobab_{info.name}"] = module
