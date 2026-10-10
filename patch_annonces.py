import shutil, sys
f = "docteur4.bao"
s = open(f, encoding="utf-8").read()
if "agent_annonces" in s:
    print("Déjà installé : rien à faire.")
    sys.exit(0)
shutil.copy(f, f + ".avant_annonces")
const = 'FICHIER_CLE = DOSSIER_DOCTEUR + "/cle.key"\n'
fonc = '''fonction agent_annonces():
    maintenant_dt = datetime.datetime.now()
    jour = maintenant_dt.date().isoformat()
    heure_actuelle = maintenant_dt.hour
    si en_dnd() ou en_silence():
        retourner
    deja = charger_json(FICHIER_ANNONCES, {})
    si heure_actuelle == R["HEURE_NUIT_FIN"] et deja.get("matin") != jour:
        deja["matin"] = jour
        sauver_json(FICHIER_ANNONCES, deja)
        nb = longueur(historique)
        phrase = "Bonjour Abou. Il est " + chaine(heure_actuelle) + " heures. Je recommence à te parler pour t'expliquer les problèmes de ton appareil."
        si nb > 0:
            phrase = phrase + " Pendant la nuit, il y a eu " + chaine(nb) + " alertes. Tu les trouveras dans ton rapport."
        sinon:
            phrase = phrase + " Aucune alerte pendant la nuit."
        ecrire_journal("Annonce du matin")
        parler(phrase)
    sinonsi heure_actuelle == R["HEURE_NUIT_DEBUT"] et deja.get("soir") != jour:
        deja["soir"] = jour
        sauver_json(FICHIER_ANNONCES, deja)
        ecrire_journal("Annonce du soir")
        parler("Il est " + chaine(heure_actuelle) + " heures. Je passe en mode silencieux pour la nuit. Seules les alertes graves seront notifiées. Bonne nuit Abou.")

'''
ok = s.count(const) == 1 and s.count("AGENTS = {}\n") == 1
if not ok:
    print("Le fichier ne ressemble pas à ce que j'attendais : rien n'a été modifié.")
    sys.exit(1)
s = s.replace(const, const + 'FICHIER_ANNONCES = DOSSIER_DOCTEUR + "/annonces.json"\n')
s = s.replace("AGENTS = {}\n", fonc + 'AGENTS = {}\nAGENTS["Annonces"] = (agent_annonces, 60)\n')
open(f, "w", encoding="utf-8").write(s)
print("Annonces ajoutées. Sauvegarde de l'ancien fichier : docteur4.bao.avant_annonces")
