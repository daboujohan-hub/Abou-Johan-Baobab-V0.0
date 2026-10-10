#!/data/data/com.termux/files/usr/bin/sh
# Installation automatique du Docteur Appareil v4
cd "$(dirname "$0")" || exit 1

echo "== Installation du Docteur Appareil v4 =="

if ! command -v baobab >/dev/null 2>&1; then
    echo "Baobab est introuvable. Installe-le : pip install -i https://test.pypi.org/simple/ baobab-francais"
    exit 1
fi

mkdir -p "$HOME/DOCTEUR"

echo "-- Outils Termux (voix, notifications, détection Wi-Fi)"
pkg install -y termux-api nmap git >/dev/null 2>&1 || echo "   (certains paquets n'ont pas pu être installés : vérifie ta connexion)"

if ! command -v termux-battery-status >/dev/null 2>&1; then
    echo "ATTENTION : termux-api est absent. Installe aussi l'application Termux:API (même source que Termux)."
fi

echo "-- Vérification du code"
baobab python docteur4.bao > "$HOME/DOCTEUR/verif.py" 2>&1
if grep -q "Oups" "$HOME/DOCTEUR/verif.py"; then
    echo "ERREUR dans docteur4.bao :"
    head -n 6 "$HOME/DOCTEUR/verif.py"
    exit 1
fi
python -m py_compile "$HOME/DOCTEUR/verif.py" 2>/dev/null || echo "   (la vérification Python a signalé un souci : si le Docteur ne démarre pas, envoie-moi docteur.out)"

echo "-- Démarrage automatique au redémarrage du téléphone (Termux:Boot)"
mkdir -p "$HOME/.termux/boot"
cat > "$HOME/.termux/boot/docteur.sh" <<EOF
#!/data/data/com.termux/files/usr/bin/sh
mkdir -p "\$HOME/DOCTEUR"
termux-wake-lock
cd "$(pwd)"
nohup baobab lancer docteur4.bao >> "\$HOME/DOCTEUR/docteur.out" 2>&1 &
nohup baobab lancer docteur_web.bao >> "\$HOME/DOCTEUR/docteur_web.out" 2>&1 &
EOF
chmod +x "$HOME/.termux/boot/docteur.sh"

echo "-- (Re)lancement"
pkill -f docteur3.bao 2>/dev/null
pkill -f docteur4.bao 2>/dev/null
pkill -f docteur_web.bao 2>/dev/null
sleep 1
termux-wake-lock 2>/dev/null
nohup baobab lancer docteur4.bao >> "$HOME/DOCTEUR/docteur.out" 2>&1 &
nohup baobab lancer docteur_web.bao >> "$HOME/DOCTEUR/docteur_web.out" 2>&1 &
sleep 4

echo ""
echo "Docteur lancé."
echo "  Menu            : baobab lancer docteur_menu.bao"
echo "  Page web        : http://localhost:8765/etat"
echo "  Journal         : tail -n 20 ~/DOCTEUR/docteur.log"
echo "  Erreurs         : tail -n 20 ~/DOCTEUR/docteur.out"
echo "  Arrêter         : pkill -f docteur4.bao"
echo ""
echo "Pour que le démarrage automatique marche : installe l'application Termux:Boot, ouvre-la une fois,"
echo "et mets Termux et Termux:Boot sur 'Non restreint' dans les réglages de batterie d'Android."
echo ""
echo "IMPORTANT : la clé ~/DOCTEUR/cle.key (créée à la première sauvegarde) déchiffre tes sauvegardes."
echo "Copie-la dans un endroit sûr, sans elle les sauvegardes sont illisibles."
