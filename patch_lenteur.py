import shutil, sys
f = "docteur4.bao"
s = open(f, encoding="utf-8").read()
if "agent_lenteur" in s:
    print("Déjà installé : rien à faire.")
    sys.exit(0)
P_R = 'R["QUESTION_GARDE"] = 1\n'
P_AG = 'AGENTS = {}\n'
if s.count(P_R) != 1 or s.count(P_AG) != 1:
    print("Le fichier ne ressemble pas à ce que j'attendais : rien n'a été modifié.")
    print("(La garde du chargeur doit déjà être installée.)")
    sys.exit(1)
NEW = r'''FICHIER_LENTEUR = DOSSIER_DOCTEUR + "/lenteur.json"

fonction mesurer_vitesse_cpu():
    code = "import time;t=time.perf_counter();s=sum(i*i%7 for i in range(300000));print((time.perf_counter()-t)*1000)"
    essayer:
        r = subprocess.run([sys.executable, "-c", code], capture_output=vrai, text=vrai, timeout=60)
        retourner decimal(r.stdout.nettoyer())
    sauf Erreur:
        retourner rien

fonction causes_lenteur():
    causes = []
    libre_ram = memoire_libre()
    si libre_ram != rien et libre_ram < 20:
        causes.ajouter("mémoire presque pleine (" + chaine(arrondir(libre_ram)) + " pour cent libre)")
    bat = etat_global["batterie"]
    si bat != rien:
        si bat["temperature"] >= R["SEUIL_CHALEUR"]:
            causes.ajouter("téléphone chaud, il ralentit pour se protéger")
        si bat["plugged"] == "UNPLUGGED" et bat["percentage"] <= 20:
            causes.ajouter("batterie faible, Android réduit la puissance")
    si stockage_utilise() >= R["SEUIL_STOCKAGE"]:
        causes.ajouter("stockage presque plein")
    essayer:
        avec ouvrir("/proc/loadavg") comme f:
            charge = decimal(f.read().separer()[0])
        coeurs = os.cpu_count() ou 1
        si charge > coeurs * 1.5:
            causes.ajouter("beaucoup de programmes tournent en même temps")
    sauf Erreur:
        passer
    retourner causes

fonction agent_lenteur():
    mesure = mesurer_vitesse_cpu()
    si mesure == rien:
        retourner
    donnees = charger_json(FICHIER_LENTEUR, {"echantillons": []})
    ech = donnees.get("echantillons", [])
    ech.ajouter(arrondir(mesure, 1))
    si longueur(ech) > 300:
        ech.depiler(0)
    donnees["echantillons"] = ech
    sauver_json(FICHIER_LENTEUR, donnees)
    si longueur(ech) < R["LENTEUR_MIN_ECHANTILLONS"]:
        retourner
    ordre = trier(ech)
    base = ordre[entier(longueur(ordre) * 0.3)]
    si longueur(ech) == R["LENTEUR_MIN_ECHANTILLONS"]:
        ecrire_journal("[Performance] apprentissage terminé : vitesse de référence " + chaine(base) + " ms")
    derniers = trier(ech[-3:])
    ratio = derniers[1] / base
    si ratio >= R["LENTEUR_FACTEUR"]:
        causes = causes_lenteur()
        si longueur(causes) == 0:
            texte = "La cause n'est pas évidente. Redémarre le téléphone si ça dure, et regarde Réglages, Batterie."
        sinon:
            texte = "Causes probables : " + ", ".joindre(causes) + "."
        signaler("Performance", "telephone_lent", 2, "Téléphone lent : " + chaine(arrondir(ratio, 1)) + " fois plus lent que d'habitude", texte)

'''
shutil.copy(f, f + ".avant_lenteur")
s = s.replace(P_R, P_R + 'R["LENTEUR_FACTEUR"] = 2.5\nR["LENTEUR_MIN_ECHANTILLONS"] = 20\n')
s = s.replace(P_AG, NEW + P_AG + 'AGENTS["Lenteur"] = (agent_lenteur, 60)\n')
open(f, "w", encoding="utf-8").write(s)
print("Alerte téléphone lent ajoutée. Ancienne version : docteur4.bao.avant_lenteur")
print("Elle apprend la vitesse normale de ton téléphone pendant les 20 premières minutes.")
