#!/usr/bin/env python3
"""Vérifie les variables du serveur TermChat sans afficher les secrets.
Usage : python3 verifier_variables.py variables.env   (lignes CLE=VALEUR copiées depuis Railway)
        python3 verifier_variables.py                  (lit l'environnement courant)"""
import base64, json, os, sys
from pathlib import Path

def lire_env(chemin):
    env = {}
    for ligne in Path(chemin).read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, val = ligne.split("=", 1)
        cle = cle.strip()
        if cle.startswith("export "):
            cle = cle[7:].strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        env[cle] = val
    return env

env = lire_env(sys.argv[1]) if len(sys.argv) > 1 else dict(os.environ)
g = lambda k: env.get(k, "").strip()
ok, avert, err = [], [], []

# 1) Obligatoires : sans eux le serveur ne démarre pas
if len(g("ADMIN_CODE")) >= 12: ok.append("ADMIN_CODE")
else: err.append("ADMIN_CODE manquant ou de moins de 12 caractères")

brut = g("FIREBASE_CREDS")
if not brut:
    err.append("FIREBASE_CREDS manquant")
else:
    try:
        j = json.loads(brut)
        manque = [c for c in ("project_id", "client_email", "private_key") if not j.get(c)]
        if manque: err.append("FIREBASE_CREDS : champs absents " + ", ".join(manque))
        else: ok.append("FIREBASE_CREDS")
    except ValueError:
        err.append("FIREBASE_CREDS n'est pas un JSON valide")

for cle in ("CERT_B64", "KEY_B64"):
    v = g(cle)
    if not v:
        err.append(f"{cle} manquant (certificat TLS)"); continue
    try:
        if b"-----BEGIN" in base64.b64decode(v): ok.append(cle)
        else: err.append(f"{cle} décodé, mais ce n'est pas un fichier PEM")
    except Exception:
        err.append(f"{cle} : base64 invalide")

# 2) Fonctions de l'appli (désactivées par défaut)
for cle, role in (("PUSH_ACTIF", "notifications"), ("ALLOW_INLINE_MEDIA", "messages vocaux"),
                  ("ALLOW_ACCOUNT_DELETION", "suppression de compte")):
    if g(cle) == "1": ok.append(f"{cle}=1 ({role})")
    else: err.append(f"{cle} doit valoir 1 ({role}) ; valeur actuelle : {g(cle) or 'absente'}")

# 3) Sécurité et options
k = g("FILE_ENCRYPTION_KEY")
if not k:
    avert.append("FILE_ENCRYPTION_KEY absente : les secrets 2FA sont stockés en clair")
else:
    try:
        if len(base64.urlsafe_b64decode(k + "=" * (-len(k) % 4))) == 32: ok.append("FILE_ENCRYPTION_KEY")
        else: err.append("FILE_ENCRYPTION_KEY invalide : 32 octets attendus (base64 url-safe)")
    except Exception:
        err.append("FILE_ENCRYPTION_KEY invalide (base64)")
if len(g("EDUMAP_ADMIN_PASSWORD")) < 12:
    avert.append("EDUMAP_ADMIN_PASSWORD absent ou court : modération EduMap impossible")
else:
    ok.append("EDUMAP_ADMIN_PASSWORD")
if not g("RESEND_API_KEY"):
    avert.append("RESEND_API_KEY absente : aucun e-mail ne sera envoyé")
if g("ALLOW_FILE_SEND") == "1":
    avert.append("ALLOW_FILE_SEND=1 : l'appli V1 n'envoie pas de fichiers, laisse 0")
for cle in ("PRODUCTION_MODE", "REQUIRE_TLS", "REQUIRE_FIREBASE"):
    if g(cle) == "0": avert.append(f"{cle}=0 : à ne pas faire en ligne")
for cle in ("ALLOW_LEGACY_SHA256_LOGIN", "ALLOW_SELF_SIGNED_DEV_CERT"):
    if g(cle) == "1": avert.append(f"{cle}=1 : à ne pas faire en ligne")

# 4) Côté appli (si lancé dans le dossier TermChatApp)
app = Path("app.json")
if app.exists():
    try:
        d = json.loads(app.read_text(encoding="utf-8")).get("expo", {})
        if d.get("name") != "TermChat": avert.append("app.json : name devrait être TermChat")
        if not d.get("android", {}).get("googleServicesFile"):
            avert.append("app.json : pas de googleServicesFile (notifications Android non livrées en production)")
        if not Path("assets/sounds/termchat_notif.mp3").exists():
            avert.append("assets/sounds/termchat_notif.mp3 absent")
    except ValueError:
        avert.append("app.json illisible")

def montrer(titre, lignes, icone):
    if lignes:
        print(f"\n{titre}")
        for l in lignes: print(f"  {icone} {l}")
montrer("OK", ok, "✅"); montrer("À VÉRIFIER", avert, "⚠️"); montrer("ERREURS", err, "❌")
print(f"\n{len(ok)} bon(s), {len(avert)} avertissement(s), {len(err)} erreur(s)")
sys.exit(1 if err else 0)
