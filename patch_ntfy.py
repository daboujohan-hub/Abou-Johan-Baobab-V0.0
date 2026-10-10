import os, shutil, sys

f = "docteur4.bao"
s = open(f, encoding="utf-8").read()
if "envoyer_ntfy" in s:
    print("Déjà installé : rien à faire.")
    sys.exit(0)

A_DND = '        si gravite == 3:\n            notifier(agent, message + " - " + explication)\n        retourner\n'
A_VIB = '    si gravite == 3:\n        vibrer()\n'
A_GARDE = '        notifier("Garde", "ALARME : le chargeur a été débranché pendant la garde.")\n'
A_ARRET = '        notifier("ALERTE", "Le Docteur a été arrêté de force. Quelqu\'un touche peut-être à ton téléphone. Il va être relancé.")\n'
A_AG = 'AGENTS = {}\n'
if any(s.count(a) != 1 for a in (A_DND, A_VIB, A_GARDE, A_ARRET, A_AG)):
    print("Le fichier ne ressemble pas à ce que j'attendais : rien n'a été modifié.")
    print("(La garde du chargeur et le veilleur doivent déjà être installés.)")
    sys.exit(1)

NEW = r'''FICHIER_NTFY_SUJET = DOSSIER_DOCTEUR + "/ntfy_sujet.txt"
FICHIER_NTFY_SERVEUR = DOSSIER_DOCTEUR + "/ntfy_serveur.txt"

fonction lire_texte(chemin):
    essayer:
        avec ouvrir(chemin, encoding="utf-8") comme f:
            retourner f.read().nettoyer()
    sauf Erreur:
        retourner ""

fonction envoyer_ntfy(titre_n, texte):
    sujet = lire_texte(FICHIER_NTFY_SUJET)
    si sujet == "":
        retourner
    serveur_n = lire_texte(FICHIER_NTFY_SERVEUR)
    si serveur_n == "":
        serveur_n = "https://ntfy.sh"
    si titre_n == "Sécurité":
        texte = "Des fichiers de tes projets ont disparu. Regarde ton téléphone."
    essayer:
        importer unicodedata
        titre_ascii = unicodedata.normalize("NFKD", titre_n).encode("ascii", "ignore").decode()
        demande = urllib.request.Request(serveur_n + "/" + sujet, data=texte[:400].encode("utf-8"), method="POST")
        demande.add_header("Title", "Docteur - " + titre_ascii)
        demande.add_header("Priority", "urgent")
        demande.add_header("Tags", "rotating_light")
        urllib.request.urlopen(demande, timeout=8).read()
    sauf Erreur comme e:
        ecrire_journal("ntfy : envoi échoué (" + chaine(e) + ")")

'''
shutil.copy(f, f + ".avant_ntfy")
s = s.replace(A_DND, '        si gravite == 3:\n            notifier(agent, message + " - " + explication)\n            envoyer_ntfy(agent, message)\n        retourner\n')
s = s.replace(A_VIB, '    si gravite == 3:\n        vibrer()\n        envoyer_ntfy(agent, message)\n')
s = s.replace(A_GARDE, A_GARDE + '        envoyer_ntfy("Garde", "ALARME : le chargeur a été débranché. Quelqu\'un a peut-être pris ton téléphone.")\n')
s = s.replace(A_ARRET, A_ARRET + '        envoyer_ntfy("ALERTE", "Le Docteur a été arrêté de force sur ton téléphone.")\n')
s = s.replace(A_AG, NEW + A_AG)
open(f, "w", encoding="utf-8").write(s)

# --- le veilleur envoie aussi l'alerte
V = os.path.expanduser("~/DOCTEUR/veilleur.sh")
ANCRE = "  termux-vibrate -d 800\n"
ajout = '''  if [ -f "$D/ntfy_sujet.txt" ] && command -v curl >/dev/null 2>&1; then
    S=$(cat "$D/ntfy_serveur.txt" 2>/dev/null); [ -z "$S" ] && S="https://ntfy.sh"
    curl -s -m 8 -H "Title: Docteur - ALERTE" -H "Priority: urgent" -d "Le Docteur ne repond plus sur ton telephone (arret force ou plantage)." "$S/$(cat "$D/ntfy_sujet.txt")" >/dev/null 2>&1
  fi
'''
if os.path.exists(V):
    v = open(V).read()
    if "ntfy_sujet" not in v and v.count(ANCRE) == 1:
        open(V, "w").write(v.replace(ANCRE, ANCRE + ajout))

# --- commandes pour activer / désactiver
BASHRC = os.path.expanduser("~/.bashrc")
MARQUE = "# --- Docteur ntfy ---"
b = open(BASHRC).read() if os.path.exists(BASHRC) else ""
if MARQUE not in b:
    bloc = """
""" + MARQUE + """
docteur_ntfy() {
  mkdir -p ~/DOCTEUR
  if [ ! -f ~/DOCTEUR/ntfy_sujet.txt ]; then
    python -c "import secrets;print('docteur-'+secrets.token_hex(8))" > ~/DOCTEUR/ntfy_sujet.txt
  fi
  echo "Sujet secret : $(cat ~/DOCTEUR/ntfy_sujet.txt)"
  echo "Sur l'autre telephone : installe l'application ntfy, touche +, entre ce sujet (serveur ntfy.sh)."
  python -c "import urllib.request as u;t=open('$HOME/DOCTEUR/ntfy_sujet.txt').read().strip();u.urlopen(u.Request('https://ntfy.sh/'+t,data='Test : le Docteur peut ecrire sur cet appareil'.encode(),headers={'Title':'Docteur - test'}),timeout=10)" 2>/dev/null && echo "Message de test envoye." || echo "Test non envoye : verifie ta connexion Internet."
}
docteur_ntfy_off() {
  rm -f ~/DOCTEUR/ntfy_sujet.txt
  echo "Alertes vers le deuxieme appareil desactivees."
}
"""
    open(BASHRC, "a").write(bloc)
print("Alerte vers un deuxième appareil ajoutée. Ancienne version : docteur4.bao.avant_ntfy")
print("Elle reste désactivée tant que tu n'as pas tapé : docteur_ntfy")
