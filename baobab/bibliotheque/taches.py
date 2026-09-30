"""Module taches : des tâches automatiques dans tes applications.

    importer taches

    fonction sauvegarde():
        afficher("Sauvegarde !")

    taches.toutes_les(60, sauvegarde)      # toutes les 60 secondes
    taches.chaque_jour("08:30", sauvegarde)  # tous les jours à 08:30
    taches.apres(10, sauvegarde)           # une seule fois, dans 10 secondes
    taches.demarrer()                      # garde le programme en vie
"""

import datetime
import threading
import time

_condition = threading.Condition()
_liste = []
_fil = None
SILENCIEUX = False


class _Tache:
    def __init__(self, nom, fonction, prochain, intervalle=None, heure=None):
        self.nom = nom
        self.fonction = fonction
        self.prochain = prochain
        self.intervalle = intervalle
        self.heure = heure
        self.executions = 0


def _prochaine_heure(heure, maintenant=None):
    """Instant (en secondes) de la prochaine fois qu'il sera HH:MM."""
    try:
        h, m = (int(x) for x in str(heure).split(":"))
        cible = datetime.time(h, m)
    except ValueError:
        raise ValueError("L'heure doit s'écrire HH:MM, par exemple 08:30")
    if maintenant is None:
        maintenant = datetime.datetime.now()
    prochain = datetime.datetime.combine(maintenant.date(), cible)
    if prochain <= maintenant:
        prochain += datetime.timedelta(days=1)
    return prochain.timestamp()


def _executer(tache):
    tache.executions += 1
    try:
        tache.fonction()
    except Exception as erreur:
        if not SILENCIEUX:
            from baobab.erreurs import expliquer

            print(f"❌ Erreur dans la tâche « {tache.nom} » : {expliquer(erreur)}")


def _reprogrammer(tache):
    if tache.intervalle is not None:
        tache.prochain += tache.intervalle
        maintenant = time.time()
        if tache.prochain <= maintenant:  # retard (veille du téléphone...)
            tache.prochain = maintenant + tache.intervalle
    elif tache.heure is not None:
        tache.prochain = _prochaine_heure(tache.heure)
    else:
        _liste.remove(tache)


def _boucle():
    while True:
        with _condition:
            while not _liste:
                _condition.wait()
            tache = min(_liste, key=lambda t: t.prochain)
            attente = tache.prochain - time.time()
            if attente > 0:
                _condition.wait(timeout=attente)
                continue
            _reprogrammer(tache)
        threading.Thread(target=_executer, args=(tache,), daemon=True).start()


def _planifier(fonction, prochain, intervalle=None, heure=None, nom=None):
    global _fil
    tache = _Tache(nom or getattr(fonction, "__name__", "tâche"),
                   fonction, prochain, intervalle, heure)
    with _condition:
        _liste.append(tache)
        if _fil is None or not _fil.is_alive():
            _fil = threading.Thread(target=_boucle, daemon=True)
            _fil.start()
        _condition.notify_all()
    return fonction


def toutes_les(secondes, fonction=None, nom=None):
    """Lance la fonction toutes les N secondes."""
    if secondes <= 0:
        raise ValueError("Le nombre de secondes doit être positif")

    def enregistrer(f):
        return _planifier(f, time.time() + secondes, intervalle=secondes, nom=nom)

    return enregistrer if fonction is None else enregistrer(fonction)


def chaque_jour(heure, fonction=None, nom=None):
    """Lance la fonction tous les jours à HH:MM (ex: "08:30")."""
    prochain = _prochaine_heure(heure)

    def enregistrer(f):
        return _planifier(f, prochain, heure=heure, nom=nom)

    return enregistrer if fonction is None else enregistrer(fonction)


def apres(secondes, fonction=None, nom=None):
    """Lance la fonction une seule fois, dans N secondes."""
    def enregistrer(f):
        return _planifier(f, time.time() + secondes, nom=nom)

    return enregistrer if fonction is None else enregistrer(fonction)


def lister():
    """La liste des tâches prévues, en texte."""
    with _condition:
        return [
            f"{t.nom} : prochaine exécution à "
            f"{time.strftime('%H:%M:%S', time.localtime(t.prochain))}, "
            f"déjà lancée {t.executions} fois"
            for t in sorted(_liste, key=lambda t: t.prochain)
        ]


def annuler(nom):
    """Supprime les tâches de ce nom. Retourne le nombre de tâches supprimées."""
    with _condition:
        a_supprimer = [t for t in _liste if t.nom == nom]
        for t in a_supprimer:
            _liste.remove(t)
        _condition.notify_all()
        return len(a_supprimer)


def tout_annuler():
    with _condition:
        _liste.clear()
        _condition.notify_all()


def demarrer():
    """Garde le programme en vie pour que les tâches continuent. Ctrl+C pour arrêter."""
    if not _liste:
        print("⚠️  Aucune tâche prévue : utilise taches.toutes_les(...) d'abord.")
    print("⏰ Les tâches tournent (Ctrl+C pour arrêter)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTâches arrêtées.")
