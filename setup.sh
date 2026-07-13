#!/bin/bash
set -e

echo "========================================"
echo " SPL Meter Setup"
echo "========================================"

# 1. Systemabhängigkeiten
echo ""
echo "[1/7] Installiere Systemabhängigkeiten..."
sudo apt update
sudo apt install -y \
    git \
    python3-pip \
    python3-venv \
    libopenblas-dev \
    portaudio19-dev \
    dosfstools

# 2. I2S-Konfiguration prüfen
echo ""
echo "[2/7] Prüfe I2S-Konfiguration..."
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
if ! grep -q "dtoverlay=googlevoicehat-soundcard" "$CONFIG_FILE"; then
    echo "  -> dtoverlay=googlevoicehat-soundcard fehlt, wird hinzugefügt..."
    echo "dtoverlay=googlevoicehat-soundcard" | sudo tee -a "$CONFIG_FILE" > /dev/null
    I2S_MISSING=true
fi
if [ "$I2S_MISSING" = false ]; then
    echo "  -> I2S bereits konfiguriert."
fi

# 3. Virtual Environment einrichten
echo ""
echo "[3/7] Richte Virtual Environment ein..."
if [ ! -d "spl_meter_env" ]; then
    python3 -m venv spl_meter_env
fi
source spl_meter_env/bin/activate

# 4. Python-Pakete installieren (nur Binär-Wheels, kein Kompilieren)
echo ""
echo "[4/7] Installiere Python-Pakete (piwheels, kein Kompilieren)..."
pip install --only-binary :all: -r requirements.txt

# 5. systemd-Service für Autostart einrichten
echo ""
echo "[5/7] Richte Autostart-Service ein..."
PROJECT_DIR="$(pwd)"
PYTHON_BIN="$PROJECT_DIR/spl_meter_env/bin/python3"
SERVICE_USER="${SUDO_USER:-$USER}"
SERVICE_FILE="spl-meter.service"

sed -e "s|USER_PLACEHOLDER|$SERVICE_USER|g" \
    -e "s|WORKDIR_PLACEHOLDER|$PROJECT_DIR|g" \
    -e "s|PYTHON_PLACEHOLDER|$PYTHON_BIN|g" \
    "$PROJECT_DIR/$SERVICE_FILE" | sudo tee /etc/systemd/system/$SERVICE_FILE > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_FILE

# 6. WLAN-Connect-Service einrichten (liest wifi_config.json vom USB-Share)
echo ""
echo "[6/7] Richte WLAN-Connect-Service ein..."
WIFI_SCRIPT="$PROJECT_DIR/wifi_connect.sh"
WIFI_SERVICE="$PROJECT_DIR/wifi-connect.service"

if [ ! -f "$WIFI_SCRIPT" ]; then
    echo "  WARNUNG: wifi_connect.sh nicht gefunden – WLAN-Service wird nicht eingerichtet."
else
    sudo cp "$WIFI_SCRIPT" /usr/local/sbin/wifi_connect.sh
    sudo chmod +x /usr/local/sbin/wifi_connect.sh
    sudo cp "$WIFI_SERVICE" /etc/systemd/system/wifi-connect.service
    sudo systemctl daemon-reload
    sudo systemctl enable wifi-connect.service
    echo "  -> wifi-connect.service aktiviert."
    echo ""
    echo "  WLAN-Konfiguration:"
    echo "  Lege die Datei 'wifi_config.json' auf das USB-Laufwerk (SPL Meter Storage)."
    echo "  Beim naechsten Boot liest der Pi die WLAN-Zugangsdaten automatisch aus dieser Datei."
    echo "  Vorlage: $PROJECT_DIR/usb_share/wifi_config.json"
fi

echo ""
echo "========================================"
echo " Setup abgeschlossen!"
echo "========================================"
echo ""
echo "Service verwalten:"
echo "  sudo systemctl start  spl-meter.service"
echo "  sudo systemctl stop   spl-meter.service"
echo "  sudo systemctl status spl-meter.service"
echo ""
echo "WLAN-Service:"
echo "  sudo systemctl status wifi-connect.service"
echo "  sudo journalctl -u wifi-connect.service"
echo ""
echo "Manuell starten:"
echo "  source spl_meter_env/bin/activate"
echo "  python3 src/main.py"
echo ""

# 7. USB-Mass-Storage-Gadget einrichten (Pi erscheint als Laufwerk am PC)
echo ""
echo "[7/7] Richte USB-Mass-Storage-Gadget ein..."
USB_GADGET_SCRIPT="$PROJECT_DIR/usb_gadget_setup.sh"
USB_GADGET_SERVICE="$PROJECT_DIR/usb-gadget.service"
BACKING_STORE="/home/teamrapsberry/backing_store.img"

if [ ! -f "$USB_GADGET_SCRIPT" ] || [ ! -f "$USB_GADGET_SERVICE" ]; then
    echo "  WARNUNG: USB-Gadget-Skript oder -Service nicht gefunden."
else
    # Konfliktierende Raspberry-Pi-USB-Gadget-Services deaktivieren
    for CONFLICT_SERVICE in rpi-usb-gadget.service rpi-usb-gadget-ics.service; do
        if systemctl list-unit-files "$CONFLICT_SERVICE" &>/dev/null; then
            echo "  -> Deaktiviere konfliktierenden Service: $CONFLICT_SERVICE"
            sudo systemctl disable "$CONFLICT_SERVICE" 2>/dev/null || true
            sudo systemctl mask "$CONFLICT_SERVICE" 2>/dev/null || true
        fi
    done

    # Sicherstellen, dass nur dwc2 automatisch geladen wird
    sudo mkdir -p /etc/modules-load.d
    echo "dwc2" | sudo tee /etc/modules-load.d/usb-gadget.conf > /dev/null

    if [ ! -f "$BACKING_STORE" ]; then
        echo "  Backing Store $BACKING_STORE fehlt, erstelle 4 GB FAT32-Image..."
        dd if=/dev/zero of="$BACKING_STORE" bs=1M count=4096 status=progress
        mkdosfs -F 32 "$BACKING_STORE"
    fi

    # wifi_config.json-Vorlage auf das Laufwerk kopieren, falls noch nicht vorhanden
    WIFI_TEMPLATE="$PROJECT_DIR/usb_share/wifi_config.json"
    if [ -f "$WIFI_TEMPLATE" ]; then
        TEMP_MOUNT="/tmp/usb_gadget_bootstrap"
        mkdir -p "$TEMP_MOUNT"
        LOOP_DEV=$(sudo losetup --show -fP "$BACKING_STORE")
        if sudo mount -t vfat "${LOOP_DEV}" "$TEMP_MOUNT" 2>/dev/null || \
           sudo mount -t vfat "${LOOP_DEV}p1" "$TEMP_MOUNT" 2>/dev/null; then
            if [ ! -f "$TEMP_MOUNT/wifi_config.json" ]; then
                sudo cp "$WIFI_TEMPLATE" "$TEMP_MOUNT/wifi_config.json"
                echo "  -> wifi_config.json-Vorlage auf USB-Laufwerk kopiert."
            else
                echo "  -> wifi_config.json bereits auf USB-Laufwerk vorhanden."
            fi
            sudo umount "$TEMP_MOUNT" 2>/dev/null || true
        else
            echo "  WARNUNG: Backing Store konnte nicht gemountet werden."
        fi
        sudo losetup -d "$LOOP_DEV" 2>/dev/null || true
        rmdir "$TEMP_MOUNT" 2>/dev/null || true
    fi

    sudo cp "$USB_GADGET_SCRIPT" /usr/local/sbin/usb_gadget_setup.sh
    sudo chmod +x /usr/local/sbin/usb_gadget_setup.sh
    sudo cp "$USB_GADGET_SERVICE" /etc/systemd/system/usb-gadget.service

    # Sync-Service installieren: Kopiert lokale Aufnahmen auf den USB-Share,
    # bevor das Gadget aktiv wird.
    SYNC_SCRIPT="$PROJECT_DIR/sync_recordings.sh"
    SYNC_SERVICE="$PROJECT_DIR/sync-recordings.service"
    if [ -f "$SYNC_SCRIPT" ] && [ -f "$SYNC_SERVICE" ]; then
        sudo cp "$SYNC_SCRIPT" /usr/local/sbin/sync_recordings.sh
        sudo chmod +x /usr/local/sbin/sync_recordings.sh
        sudo cp "$SYNC_SERVICE" /etc/systemd/system/sync-recordings.service
    fi

    sudo systemctl daemon-reload
    sudo systemctl enable sync-recordings.service
    sudo systemctl enable usb-gadget.service
    sudo systemctl start sync-recordings.service
    sudo systemctl start usb-gadget.service
    echo "  -> sync-recordings.service und usb-gadget.service aktiviert."
    echo ""
    echo "  USB-Laufwerk:"
    echo "  Nach dem Boot erscheint der SPL Meter als 'SPL Meter Storage' am PC."
    echo "  Aufnahmen aus /home/teamrapsberry/recordings_local werden vorher"
    echo "  in den recordings-Ordner des USB-Laufwerks kopiert."
fi

if [ "$I2S_MISSING" = true ]; then
    echo "WICHTIG: I2S-Konfiguration wurde geändert."
    echo "Bitte jetzt neu starten: sudo reboot"
fi
