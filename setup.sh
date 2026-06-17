#!/bin/bash
set -e

echo "========================================"
echo " SPL Meter Setup"
echo "========================================"

# 1. Systemabhängigkeiten
echo ""
echo "[1/4] Installiere Systemabhängigkeiten..."
sudo apt update
sudo apt install -y \
    git \
    python3-pip \
    python3-venv \
    libopenblas-dev \
    portaudio19-dev

# 2. I2S-Konfiguration prüfen
echo ""
echo "[2/4] Prüfe I2S-Konfiguration..."
CONFIG_FILE="/boot/firmware/config.txt"
if [ ! -f "$CONFIG_FILE" ]; then
    CONFIG_FILE="/boot/config.txt"
fi

I2S_MISSING=false
if ! grep -q "dtparam=i2s=on" "$CONFIG_FILE"; then
    echo "  -> dtparam=i2s=on fehlt, wird hinzugefügt..."
    echo "dtparam=i2s=on" | sudo tee -a "$CONFIG_FILE" > /dev/null
    I2S_MISSING=true
fi
if ! grep -q "dtoverlay=i2s-mmap" "$CONFIG_FILE"; then
    echo "  -> dtoverlay=i2s-mmap fehlt, wird hinzugefügt..."
    echo "dtoverlay=i2s-mmap" | sudo tee -a "$CONFIG_FILE" > /dev/null
    I2S_MISSING=true
fi
if [ "$I2S_MISSING" = false ]; then
    echo "  -> I2S bereits konfiguriert."
fi

# 3. Virtual Environment einrichten
echo ""
echo "[3/4] Richte Virtual Environment ein..."
if [ ! -d "spl_meter_env" ]; then
    python3 -m venv spl_meter_env
fi
source spl_meter_env/bin/activate

# 4. Python-Pakete installieren (nur Binär-Wheels, kein Kompilieren)
echo ""
echo "[4/4] Installiere Python-Pakete (piwheels, kein Kompilieren)..."
pip install --only-binary :all: -r requirements.txt

echo ""
echo "========================================"
echo " Setup abgeschlossen!"
echo "========================================"
echo ""
echo "Programm starten:"
echo "  source spl_meter_env/bin/activate"
echo "  python3 src/audio_input.py"
echo ""

if [ "$I2S_MISSING" = true ]; then
    echo "WICHTIG: I2S-Konfiguration wurde geändert."
    echo "Bitte jetzt neu starten: sudo reboot"
fi
