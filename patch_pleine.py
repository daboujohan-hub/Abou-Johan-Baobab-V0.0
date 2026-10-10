import shutil, sys
f = "docteur4.bao"
s = open(f, encoding="utf-8").read()
if "charge_pleine" in s:
    print("Déjà installé : rien à faire.")
    sys.exit(0)
A1 = 'R["QUESTION_GARDE"] = 1\n'
A2 = '    si en_charge et niveau >= R["SEUIL_HAUT"]:\n'
if s.count(A1) != 1 or s.count(A2) != 1:
    print("Le fichier ne ressemble pas à ce que j'attendais : rien n'a été modifié.")
    sys.exit(1)
NOUVEAU = r'''    si en_charge et niveau >= R["SEUIL_PLEINE"]:
        signaler("Batterie", "charge_pleine", 3, "Batterie pleine à " + chaine(niveau) + " pour cent, débranche le chargeur", "Rester branché à fond fait chauffer et use la batterie. Si tu n'es pas là, active la protection de charge d'Android.")
'''
shutil.copy(f, f + ".avant_pleine")
s = s.replace(A1, A1 + 'R["SEUIL_PLEINE"] = 90\n')
s = s.replace(A2, NOUVEAU + A2)
open(f, "w", encoding="utf-8").write(s)
print("Alerte batterie pleine ajoutée. Ancienne version : docteur4.bao.avant_pleine")
