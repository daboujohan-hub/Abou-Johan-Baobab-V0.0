import os, shutil, subprocess, sys

f = "docteur4.bao"
s = open(f, encoding="utf-8").read()
if "arret_signal" in s:
    print("Déjà installé : rien à faire.")
    sys.exit(0)

P_IMP = 'importer threading\n'
P_R = 'R["QUESTION_GARDE"] = 1\n'
P_A = 'fonction alarme_garde():'
P_AG = 'AGENTS = {}\n'
P_START = 'charger_reglages()\ncreer_script_armer()\n'
ok = all(s.count(a) == 1 for a in (P_IMP, P_R, P_A, P_AG, P_START))
ok = ok and "fonction agent_garde():" in s and s.index(P_A) < s.index("fonction agent_garde():") < s.index(P_AG)
if not ok:
    print("Le fichier ne ressemble pas à ce que j'attendais : rien n'a été modifié.")
    print("(La garde du chargeur doit déjà être installée.)")
    sys.exit(1)

NEW = r'''FICHIER_ARRET_VOULU = DOSSIER_DOCTEUR + "/arret_voulu"

fonction empreinte_agent():
    essayer:
        r = subprocess.run(["termux-fingerprint", "-t", "Docteur", "-d", "Arrêter l'alarme"], capture_output=vrai, text=vrai, timeout=30)
        donnees = json.loads(r.stdout)
    sauf subprocess.TimeoutExpired:
        retourner "refus"
    sauf Erreur:
        retourner "indisponible"
    si donnees.get("auth_result") == "AUTH_RESULT_SUCCESS":
        retourner "ok"
    retourner "refus"

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

fonction fin_alarme_garde(raison):
    essayer:
        os.remove(FICHIER_GARDE)
    sauf Erreur:
        passer
    etat_global["garde_debut_alarme"] = 0
    etat_global["garde_alarmes"] = 0
    etat_global["garde_vu_branche"] = faux
    etat_global["garde_empreinte_ok"] = vrai
    ecrire_journal("[Garde] " + raison)
    notifier("Garde", raison)

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
    en_alarme = etat_global.get("garde_debut_alarme", 0) > 0
    si fin <= 0 et non en_alarme:
        etat_global["garde_vu_branche"] = faux
        etat_global["garde_alarmes"] = 0
        si en_charge et avant == faux et R["QUESTION_GARDE"] == 1:
            proposer_garde()
        retourner
    si fin > 0 et t_actuel > fin et non en_alarme:
        fin_alarme_garde("La garde du chargeur est terminée (durée écoulée).")
        retourner
    si non en_alarme:
        si en_charge:
            etat_global["garde_vu_branche"] = vrai
            retourner
        si non etat_global.get("garde_vu_branche"):
            retourner
        etat_global["garde_debut_alarme"] = t_actuel
        etat_global["garde_alarmes"] = 0
        ecrire_journal("[Garde] ALARME : chargeur débranché pendant la garde")
        notifier("Garde", "ALARME : le chargeur a été débranché pendant la garde.")
    mode_empreinte = R["ALARME_JUSQU_EMPREINTE"] == 1 et etat_global.get("garde_empreinte_ok", vrai)
    si non mode_empreinte:
        si en_charge:
            etat_global["garde_debut_alarme"] = 0
            etat_global["garde_vu_branche"] = vrai
            etat_global["garde_alarmes"] = 0
            retourner
        n = etat_global.get("garde_alarmes", 0)
        si n < 40 et t_actuel - etat_global.get("garde_derniere", 0) >= 20:
            etat_global["garde_derniere"] = t_actuel
            etat_global["garde_alarmes"] = n + 1
            alarme_garde()
        retourner
    si t_actuel - etat_global["garde_debut_alarme"] > R["ALARME_MAX_MIN"] * 60:
        fin_alarme_garde("L'alarme s'est arrêtée seule après " + chaine(R["ALARME_MAX_MIN"]) + " minutes sans empreinte.")
        retourner
    alarme_garde()
    resultat = empreinte_agent()
    si resultat == "ok":
        fin_alarme_garde("Alarme arrêtée par ton empreinte. Garde désactivée.")
    sinonsi resultat == "indisponible":
        etat_global["garde_empreinte_ok"] = faux
        ecrire_journal("[Garde] lecteur d'empreinte indisponible : retour à l'arrêt par rebranchement du chargeur")

fonction arret_signal(numero, cadre):
    si non os.path.exists(FICHIER_ARRET_VOULU):
        ecrire_journal("[Docteur] ARRÊT FORCÉ détecté (signal " + chaine(numero) + ")")
        notifier("ALERTE", "Le Docteur a été arrêté de force. Quelqu'un touche peut-être à ton téléphone. Il va être relancé.")
        vibrer()
    sinon:
        ecrire_journal("Docteur arrêté volontairement")
    essayer:
        os.remove(FICHIER_PID)
    sauf Erreur:
        passer
    sys.exit(0)

'''
i = s.index(P_A)
j = s.index(P_AG)
s = s[:i] + NEW + s[j:]
s = s.replace(P_IMP, P_IMP + 'importer signal\n')
s = s.replace(P_R, P_R + 'R["ALARME_JUSQU_EMPREINTE"] = 1\nR["ALARME_MAX_MIN"] = 60\n')
s = s.replace(P_START, P_START + 'signal.signal(signal.SIGTERM, arret_signal)\n')
shutil.copy(f, f + ".avant_veilleur")
open(f, "w", encoding="utf-8").write(s)

# --- le veilleur : un petit programme séparé qui surveille le Docteur
projet = os.getcwd()
D = os.path.expanduser("~/DOCTEUR")
os.makedirs(D, exist_ok=True)
VEILLEUR = '''#!/data/data/com.termux/files/usr/bin/sh
D="$HOME/DOCTEUR"
[ -f "$D/arret_voulu" ] && exit 0
now=$(date +%s)
last=$(cut -d. -f1 "$D/docteur.vivant" 2>/dev/null)
[ -z "$last" ] && last=0
age=$((now - last))
[ "$age" -le 240 ] && exit 0
prev=$(cat "$D/veilleur.dernier" 2>/dev/null)
[ -z "$prev" ] && prev=0
if [ $((now - prev)) -ge 1800 ]; then
  echo "$now" > "$D/veilleur.dernier"
  echo "$(date '+%Y-%m-%d %H:%M:%S') | [Veilleur] Docteur silencieux depuis ${age}s : alerte et relance" >> "$D/docteur.log"
  termux-notification --title "Docteur - ALERTE" --content "Le Docteur ne répond plus (arrêt forcé ou plantage). Je le relance." --priority high
  termux-vibrate -d 800
  h=$(date +%H)
  if [ "$h" -ge 6 ] && [ "$h" -lt 22 ]; then
    termux-tts-speak -l fr "Alerte. Le Docteur ne répond plus. Je le relance."
  fi
fi
if ! pgrep -f docteur4.bao >/dev/null 2>&1; then
  cd "''' + projet + '''" && nohup baobab lancer docteur4.bao >> "$D/docteur.out" 2>&1 &
fi
'''
BOUCLE = '''#!/data/data/com.termux/files/usr/bin/sh
while true; do
  sh "$HOME/DOCTEUR/veilleur.sh"
  sleep 30
done
'''
JOB = '''#!/data/data/com.termux/files/usr/bin/sh
sh "$HOME/DOCTEUR/veilleur.sh"
pgrep -f veilleur_boucle.sh >/dev/null 2>&1 || nohup sh "$HOME/DOCTEUR/veilleur_boucle.sh" >/dev/null 2>&1 &
'''
for nom, texte in (("veilleur.sh", VEILLEUR), ("veilleur_boucle.sh", BOUCLE), ("veilleur_job.sh", JOB)):
    chemin = os.path.join(D, nom)
    open(chemin, "w").write(texte)
    os.chmod(chemin, 0o755)

# --- raccourcis : docteur_on / docteur_off (le plus récent écrase l'ancien)
BASHRC = os.path.expanduser("~/.bashrc")
MARQUE = "# --- Docteur veilleur ---"
b = open(BASHRC).read() if os.path.exists(BASHRC) else ""
if MARQUE not in b:
    bloc = '''
''' + MARQUE + '''
docteur_on() {
  rm -f ~/DOCTEUR/arret_voulu
  (cd "''' + projet + '''" && termux-wake-lock && nohup baobab lancer docteur4.bao >> ~/DOCTEUR/docteur.out 2>&1 &)
  pkill -f veilleur_boucle.sh
  (nohup sh ~/DOCTEUR/veilleur_boucle.sh >/dev/null 2>&1 &)
  echo "Docteur et veilleur lancés"
}
docteur_off() {
  if ! grep -q '"EMPREINTE": 0' ~/DOCTEUR/reglages.json 2>/dev/null; then
    r=$(termux-fingerprint -t "Docteur" -d "Arrêter le Docteur" 2>/dev/null)
    case "$r" in
      *AUTH_RESULT_SUCCESS*) ;;
      *) echo "Empreinte non reconnue : arrêt bloqué."; return ;;
    esac
  fi
  touch ~/DOCTEUR/arret_voulu
  pkill -f veilleur_boucle.sh
  pkill -f docteur4.bao
  echo "Docteur arrêté"
}
'''
    open(BASHRC, "a").write(bloc)

# --- démarrage automatique au redémarrage du téléphone
BOOT = os.path.expanduser("~/.termux/boot/docteur.sh")
if os.path.exists(BOOT) and "veilleur_boucle" not in open(BOOT).read():
    open(BOOT, "a").write('rm -f "$HOME/DOCTEUR/arret_voulu"\nnohup sh "$HOME/DOCTEUR/veilleur_boucle.sh" >/dev/null 2>&1 &\n')

# --- tâche de secours Android toutes les 15 minutes
try:
    subprocess.run(["termux-job-scheduler", "--job-id", "77", "--period-ms", "900000", "--persisted", "true", "-s", os.path.join(D, "veilleur_job.sh")], capture_output=True, timeout=20)
    print("Tâche de secours Android enregistrée (toutes les 15 minutes).")
except Exception:
    print("Tâche de secours Android non enregistrée (termux-job-scheduler absent) : le veilleur fonctionne quand même.")
print("Veilleur et alarme jusqu'à l'empreinte ajoutés. Ancienne version : docteur4.bao.avant_veilleur")
