import shutil, sys

def lire(f):
    return open(f, encoding="utf-8").read()

def une_fois(s, ancre, nom):
    if s.count(ancre) != 1:
        print("Le fichier ne ressemble pas à ce que j'attendais (" + nom + ") : rien n'a été modifié.")
        sys.exit(1)

d = lire("docteur4.bao")
m = lire("docteur_menu.bao")
if "agent_garde" in d:
    print("Déjà installé : rien à faire.")
    sys.exit(0)

A1 = 'FICHIER_ANNONCES = DOSSIER_DOCTEUR + "/annonces.json"\n'
A2 = 'R["MODIF_MASSE"] = 40\n'
A3 = 'AGENTS = {}\n'
A4 = 'habitudes[:] = charger_json(FICHIER_HABITUDES, [])\ncharger_reglages()\n'
for a, n in ((A1, "constantes"), (A2, "réglages"), (A3, "agents"), (A4, "démarrage")):
    une_fois(d, a, n)

M1 = 'FICHIER_CLE = DOSSIER_DOCTEUR + "/cle.key"\n'
M2 = 'afficher("🩺 Menu du Docteur")\n'
M3 = '        sinonsi choix == "0":\n'
M4 = 'afficher("12 Appareils du Wi-Fi   13 Restaurer une sauvegarde   0 Quitter")\n'
for a, n in ((M1, "menu constantes"), (M2, "menu fonctions"), (M3, "menu choix"), (M4, "menu aide")):
    une_fois(m, a, n)

FONC = r'''fonction creer_script_armer():
    essayer:
        avec ouvrir(SCRIPT_ARMER, "w") comme f:
            f.write("#!/data/data/com.termux/files/usr/bin/sh\n")
            f.write("echo $(( $(date +%s) + $1 * 60 )) > " + FICHIER_GARDE + "\n")
        os.chmod(SCRIPT_ARMER, 493)
    sauf Erreur comme e:
        ecrire_journal("Script d'armement : erreur " + chaine(e))

fonction proposer_garde():
    essayer:
        subprocess.run(["termux-notification", "--id", "garde_question", "--title", "Docteur - téléphone en charge", "--content", "Tu t'éloignes ? Active la garde du chargeur.", "--button1", "Garder 1 h", "--button1-action", "sh " + SCRIPT_ARMER + " 60", "--button2", "Garder 3 h", "--button2-action", "sh " + SCRIPT_ARMER + " 180", "--button3", "Garder 8 h", "--button3-action", "sh " + SCRIPT_ARMER + " 480"], timeout=20)
    sauf Erreur:
        passer

fonction alarme_garde():
    phrase = "Attention. Ce téléphone est protégé et surveillé. Repose-le tout de suite et rebranche le chargeur."
    essayer:
        subprocess.run(["termux-volume", "alarm", "15"], timeout=10)
        subprocess.run(["termux-volume", "music", "15"], timeout=10)
    sauf Erreur:
        passer
    vibrer()
    essayer:
        r = subprocess.run(["termux-tts-speak", "-l", "fr", "-s", "ALARM", phrase], timeout=120)
        si r.returncode != 0:
            parler(phrase)
    sauf Erreur:
        passer

fonction agent_garde():
    t_actuel = temps.maintenant()
    fin = lire_nombre(FICHIER_GARDE)
    etat_global["garde_tic"] = etat_global.get("garde_tic", 0) + 1
    si fin <= 0 et etat_global["garde_tic"] % 6 != 0:
        retourner
    bat = lire_batterie()
    si bat == rien:
        retourner
    en_charge = bat["plugged"] != "UNPLUGGED"
    avant = etat_global.get("garde_branche")
    etat_global["garde_branche"] = en_charge
    si fin <= 0:
        etat_global["garde_vu_branche"] = faux
        etat_global["garde_alarmes"] = 0
        si en_charge et avant == faux et R["QUESTION_GARDE"] == 1:
            proposer_garde()
        retourner
    si t_actuel > fin:
        essayer:
            os.remove(FICHIER_GARDE)
        sauf Erreur:
            passer
        ecrire_journal("[Garde] terminée, durée écoulée")
        notifier("Garde", "La garde du chargeur est terminée.")
        retourner
    si en_charge:
        etat_global["garde_vu_branche"] = vrai
        etat_global["garde_alarmes"] = 0
        retourner
    si non etat_global.get("garde_vu_branche"):
        retourner
    n = etat_global.get("garde_alarmes", 0)
    si n == 0:
        ecrire_journal("[Garde] ALARME : chargeur débranché pendant la garde")
        notifier("Garde", "ALARME : le chargeur a été débranché pendant la garde.")
    si n < 40 et t_actuel - etat_global.get("garde_derniere", 0) >= 20:
        etat_global["garde_derniere"] = t_actuel
        etat_global["garde_alarmes"] = n + 1
        alarme_garde()

'''
d = d.replace(A1, A1 + 'FICHIER_GARDE = DOSSIER_DOCTEUR + "/garde.txt"\nSCRIPT_ARMER = DOSSIER_DOCTEUR + "/armer.sh"\n')
d = d.replace(A2, A2 + 'R["QUESTION_GARDE"] = 1\n')
d = d.replace(A3, FONC + A3 + 'AGENTS["Garde"] = (agent_garde, 5)\n')
d = d.replace(A4, A4 + 'creer_script_armer()\n')

MENU_F = r'''fonction commande_garde():
    fin = lire_nombre(FICHIER_GARDE)
    si fin > temps.maintenant():
        afficher("🛡️ Garde du chargeur active encore", entier((fin - temps.maintenant()) / 60), "minutes")
        si saisir("Tape STOP pour la désactiver (Entrée = la laisser) : ").nettoyer() == "STOP":
            os.remove(FICHIER_GARDE)
            afficher("✅ Garde désactivée")
        retourner
    afficher("La garde se déclenche seulement si le chargeur est débranché alors que le téléphone était en charge.")
    afficher("Branche d'abord le chargeur. Une alarme vocale forte retentit, sur ce téléphone seulement.")
    minutes = demander_minutes("Garde pendant combien de minutes ? (0 = annuler) : ")
    si minutes == rien ou minutes <= 0:
        afficher("Annulé.")
        retourner
    avec ouvrir(FICHIER_GARDE, "w") comme f:
        f.write(chaine(temps.maintenant() + minutes * 60))
    afficher("🛡️ Garde active pendant", minutes, "minutes. Désactive-la ici avec STOP quand tu reviens.")

'''
m = m.replace(M1, M1 + 'FICHIER_GARDE = DOSSIER_DOCTEUR + "/garde.txt"\n')
m = m.replace(M2, MENU_F + M2)
m = m.replace(M3, '        sinonsi choix == "14":\n            commande_garde()\n' + M3)
m = m.replace(M4, 'afficher("12 Appareils du Wi-Fi   13 Restaurer une sauvegarde   14 Garde du chargeur   0 Quitter")\n')

shutil.copy("docteur4.bao", "docteur4.bao.avant_garde")
shutil.copy("docteur_menu.bao", "docteur_menu.bao.avant_garde")
open("docteur4.bao", "w", encoding="utf-8").write(d)
open("docteur_menu.bao", "w", encoding="utf-8").write(m)
print("Garde du chargeur ajoutée (Docteur et menu). Anciennes versions : *.avant_garde")
