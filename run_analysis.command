#!/bin/bash
cd "$(dirname "$0")"
echo "=== TELEMEETRIA ANALÜÜSI KÄIVITAMINE ==="
if command -v python3 &> /dev/null; then
    python3 analyze_telemetry.py
elif command -v python &> /dev/null; then
    python analyze_telemetry.py
else
    echo "Viga: Python ei ole installitud või kättesaadav."
fi
echo ""
echo "Protsess lõpetas töö."
read -p "Vajuta Enter sulgemiseks..."
