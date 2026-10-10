import shutil, sys
d = open("docteur4.bao", encoding="utf-8").read()
m = open("docteur_menu.bao", encoding="utf-8").read()
if "EMPREINTE_MENU" in m:
    print("Déjà installé : rien à faire.")
    sys.exit(0)
D1 = 'R["EMPREINTE"] = 1\n'
M1 = 'importer shutil\nimporter subprocess\nimporter temps\n'
M2 = 'afficher("🩺 Menu du Docteur")\n'
if d.count(D1) != 1 or m.count(M1) != 1 or m.count(M2) != 1 or "exiger_empreinte" not in m:
    print("Les fichiers ne ressemblent pas à ce que j'attendais : rien n'a été modifié.")
    print("(La protection par empreinte doit déjà être installée.)")
    sys.exit(1)
VERROU = r'''reglages_menu = lire_json(FICHIER_REGLAGES, {})
si reglages_menu.get("EMPREINTE_MENU", 1) == 1 et reglages_menu.get("EMPREINTE", 1) == 1:
    acces = faux
    pour essai dans intervalle(3):
        si exiger_empreinte("Ouvrir le menu du Docteur"):
            acces = vrai
            arreter
        afficher("Essai", essai + 1, "sur 3")
    si non acces:
        afficher("🔒 Menu verrouillé. Accès refusé.")
        sys.exit(1)

'''
shutil.copy("docteur4.bao", "docteur4.bao.avant_verrou")
shutil.copy("docteur_menu.bao", "docteur_menu.bao.avant_verrou")
open("docteur4.bao", "w", encoding="utf-8").write(d.replace(D1, D1 + 'R["EMPREINTE_MENU"] = 1\n'))
open("docteur_menu.bao", "w", encoding="utf-8").write(m.replace(M1, 'importer shutil\nimporter subprocess\nimporter sys\nimporter temps\n').replace(M2, VERROU + M2))
print("Menu verrouillé par l'empreinte. Anciennes versions : *.avant_verrou")
