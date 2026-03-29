#!/bin/bash
echo "============================================================"
echo "  Erasmus LA Helper - Avvio"
echo "============================================================"
echo ""

# Controlla Python
if ! command -v python3 &> /dev/null; then
    echo "[ERRORE] Python3 non trovato. Installalo da https://python.org"
    exit 1
fi

# Directory dello script
cd "$(dirname "$0")"

# Installa dipendenze
echo "Controllo dipendenze..."
pip3 install -r requirements.txt --quiet 2>&1 || pip install -r requirements.txt --quiet

echo ""
echo "Avvio del server..."
echo "Apertura browser su: http://localhost:5050"
echo ""
echo "Per fermare il server premi CTRL+C"
echo "============================================================"

# Apri browser dopo 1.5 secondi
(sleep 1.5 && python3 -c "import webbrowser; webbrowser.open('http://localhost:5050')" 2>/dev/null || open "http://localhost:5050" 2>/dev/null) &

python3 app.py
