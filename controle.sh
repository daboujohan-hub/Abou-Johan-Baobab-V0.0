D="$HOME/DOCTEUR"
F="$(pwd)/docteur4.bao"
M="$(pwd)/docteur_menu.bao"
ok() { echo "✅ $1"; }
ko() { echo "❌ $1"; }
a() { echo "⚠️  $1"; }
echo "== Contrôle du Docteur =="
now=$(date +%s)
last=$(cut -d. -f1 "$D/docteur.vivant" 2>/dev/null); [ -z "$last" ] && last=0
age=$((now - last))
if [ "$age" -le 180 ] && pgrep -f docteur4.bao >/dev/null 2>&1; then ok "Docteur actif (signe de vie il y a ${age}s)"; else ko "Docteur arrêté ou bloqué : tape docteur_on"; fi
if pgrep -f veilleur_boucle.sh >/dev/null 2>&1; then ok "Veilleur actif"; else a "Veilleur absent (patch_veilleur.py pas lancé, ou arrêté)"; fi
for t in termux-battery-status termux-notification termux-tts-speak termux-vibrate termux-fingerprint nmap git; do
  if command -v $t >/dev/null 2>&1; then ok "$t présent"; else ko "$t manquant"; fi
done
[ -f "$F" ] || { ko "docteur4.bao introuvable : va dans ~/ESPACE.DE.TRAVAIL/baobab_projet"; exit 1; }
for m in "agent_annonces:Annonces 6h/22h" "agent_garde:Garde du chargeur" "charge_pleine:Alerte batterie pleine" "arret_signal:Alerte arrêt forcé (veilleur)" "ALARME_JUSQU_EMPREINTE:Alarme jusqu'à l'empreinte"; do
  if grep -q "${m%%:*}" "$F"; then ok "${m#*:} installé"; else a "${m#*:} : pas installé"; fi
done
if grep -q "exiger_empreinte" "$M" 2>/dev/null; then ok "Empreinte pour les actions sensibles installée"; else a "Empreinte du menu : pas installée"; fi
if grep -q "EMPREINTE_MENU" "$M" 2>/dev/null; then ok "Menu verrouillé par l'empreinte installé"; else a "Verrou du menu : pas installé"; fi
if grep -q "baobab lancer docteur4.bao" "$HOME/.termux/boot/docteur.sh" 2>/dev/null; then ok "Démarrage automatique configuré (Termux:Boot)"; else a "Démarrage automatique absent"; fi
[ -f "$D/cle.key" ] && ok "Clé de chiffrement présente (copie-la ailleurs si ce n'est pas fait)" || a "Pas encore de clé (créée à la première sauvegarde)"
ls "$D/sauvegardes" 2>/dev/null | head -1 | grep -q . && ok "Sauvegarde : $(ls "$D/sauvegardes" | tail -1)" || a "Aucune sauvegarde encore"
grep -q "Annonce du" "$D/docteur.log" 2>/dev/null && ok "Annonce vocale déjà faite : $(grep 'Annonce du' "$D/docteur.log" | tail -1 | cut -c1-40)" || a "Aucune annonce vocale dans le journal"
e=$(tail -n 30 "$D/docteur.out" 2>/dev/null | grep -ci "Traceback\|Oups\|erreur")
[ "$e" -eq 0 ] && ok "Pas d'erreur récente dans docteur.out" || ko "$e ligne(s) d'erreur dans docteur.out : tape docteur_erreurs"
echo "-- 5 dernières lignes du journal :"; tail -n 5 "$D/docteur.log" 2>/dev/null | cut -c1-120
