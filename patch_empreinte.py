import shutil, sys

def lire(f):
    return open(f, encoding="utf-8").read()

d = lire("docteur4.bao")
m = lire("docteur_menu.bao")
if "exiger_empreinte" in m:
    print("Déjà installé : rien à faire.")
    sys.exit(0)

D1 = 'R["QUESTION_GARDE"] = 1\n'
M_IMP = 'importer shutil\nimporter temps\n'
M_ETAT = 'fonction etat_docteur():\n'
M_STOP = '''            os.remove(FICHIER_GARDE)
            afficher("✅ Garde désactivée")
'''
M_NET = '    supprimes = 0\n'
M_DOUB = '    pour c dans cibles:\n        essayer:\n            os.remove(c)\n'
M_REST = '    sortie = DOSSIER_DOCTEUR + "/restauration/" + nom.replace(".tar.gz.enc", "")\n'
M_REG = '    reglages[nom_reglage] = valeur\n'

ok = d.count(D1) == 1
for a in (M_IMP, M_ETAT, M_STOP, M_NET, M_DOUB, M_REST, M_REG):
    ok = ok and m.count(a) == 1
if not ok:
    print("Les fichiers ne ressemblent pas à ce que j'attendais : rien n'a été modifié.")
    print("(La garde du chargeur doit déjà être installée.)")
    sys.exit(1)

HELPERS = r'''fonction empreinte_requise():
    reglages = lire_json(FICHIER_REGLAGES, {})
    retourner reglages.get("EMPREINTE", 1) == 1

fonction exiger_empreinte(raison):
    si non empreinte_requise():
        retourner vrai
    afficher("👆 Pose ton doigt sur le capteur :", raison)
    pour options dans [["-t", "Docteur", "-d", raison], []]:
        essayer:
            r = subprocess.run(["termux-fingerprint"] + options, capture_output=vrai, text=vrai, timeout=60)
            donnees = json.loads(r.stdout)
        sauf FichierIntrouvable:
            afficher("❌ termux-api est absent : installe-le avec pkg install termux-api")
            retourner faux
        sauf Erreur:
            continuer
        si donnees.get("auth_result") == "AUTH_RESULT_SUCCESS":
            afficher("✅ Empreinte reconnue")
            retourner vrai
        afficher("❌ Empreinte refusée ou annulée : action bloquée.")
        retourner faux
    afficher("❌ Le lecteur d'empreinte ne répond pas. Vérifie que l'application Termux:API est installée et qu'une empreinte est enregistrée dans Android.")
    afficher("   Pour désactiver cette protection : mets EMPREINTE à 0 dans ~/DOCTEUR/reglages.json")
    retourner faux

'''
d = d.replace(D1, D1 + 'R["EMPREINTE"] = 1\n')
m = m.replace(M_IMP, 'importer shutil\nimporter subprocess\nimporter temps\n')
m = m.replace(M_ETAT, HELPERS + M_ETAT)
m = m.replace(M_STOP, '''            si exiger_empreinte("Désactiver la garde du chargeur"):
                os.remove(FICHIER_GARDE)
                afficher("✅ Garde désactivée")
''')
m = m.replace(M_NET, '    si non exiger_empreinte("Supprimer des fichiers"):\n        retourner\n' + M_NET)
m = m.replace(M_DOUB, '    si non exiger_empreinte("Supprimer des doublons"):\n        retourner\n' + M_DOUB)
m = m.replace(M_REST, '    si non exiger_empreinte("Restaurer une sauvegarde"):\n        retourner\n' + M_REST)
m = m.replace(M_REG, '    si non exiger_empreinte("Changer un réglage"):\n        retourner\n' + M_REG)

shutil.copy("docteur4.bao", "docteur4.bao.avant_empreinte")
shutil.copy("docteur_menu.bao", "docteur_menu.bao.avant_empreinte")
open("docteur4.bao", "w", encoding="utf-8").write(d)
open("docteur_menu.bao", "w", encoding="utf-8").write(m)
print("Protection par empreinte ajoutée. Anciennes versions : *.avant_empreinte")
