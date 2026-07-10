#!/bin/bash
# wifi_connect.sh
# Liest WLAN-Zugangsdaten aus der wifi_config.json auf dem USB-Share
# und konfiguriert wpa_supplicant entsprechend.
# Wird als systemd-Service beim Boot ausgefuehrt.

set -e

USB_MOUNT="/mnt/usb_share"
BACKING_STORE="/home/teamrapsberry/backing_store.img"
WIFI_CONFIG_FILE="$USB_MOUNT/wifi_config.json"
WPA_CONF="/etc/wpa_supplicant/wpa_supplicant.conf"
LOG_TAG="wifi-connect"

log() {
    logger -t "$LOG_TAG" "$1"
    echo "$1"
}

# USB-Share mounten falls noch nicht gemountet
if ! mountpoint -q "$USB_MOUNT"; then
    if [ ! -f "$BACKING_STORE" ]; then
        log "FEHLER: Backing Store nicht gefunden: $BACKING_STORE"
        exit 1
    fi
    mkdir -p "$USB_MOUNT"
    LOOP_DEV=$(losetup --show -fP "$BACKING_STORE")
    mount -t vfat "${LOOP_DEV}" "$USB_MOUNT" -o ro,uid=1000,gid=1000 2>/dev/null || \
    mount -t vfat "${LOOP_DEV}p1" "$USB_MOUNT" -o ro,uid=1000,gid=1000 2>/dev/null || {
        log "FEHLER: USB-Share konnte nicht gemountet werden."
        losetup -d "$LOOP_DEV" 2>/dev/null
        exit 1
    }
    MOUNTED_HERE=true
fi

# Pruefen ob wifi_config.json vorhanden ist
if [ ! -f "$WIFI_CONFIG_FILE" ]; then
    log "Keine wifi_config.json auf USB-Share gefunden – WLAN-Konfiguration unveraendert."
    [ "$MOUNTED_HERE" = true ] && umount "$USB_MOUNT" 2>/dev/null; losetup -d "$LOOP_DEV" 2>/dev/null
    exit 0
fi

log "wifi_config.json gefunden – lese WLAN-Konfiguration..."

# Country-Code aus JSON lesen (Fallback: DE)
COUNTRY=$(python3 -c "
import json, sys
try:
    with open('$WIFI_CONFIG_FILE') as f:
        data = json.load(f)
    print(data.get('country', 'DE'))
except Exception as e:
    print('DE')
" 2>/dev/null)

# wpa_supplicant.conf neu schreiben
{
    echo "country=$COUNTRY"
    echo "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev"
    echo "update_config=1"
    echo ""

    python3 - <<PYEOF
import json, sys

try:
    with open("$WIFI_CONFIG_FILE") as f:
        data = json.load(f)
    networks = data.get("networks", [])
    if not networks:
        sys.exit(0)
    for net in networks:
        ssid = net.get("ssid", "")
        password = net.get("password", "")
        if not ssid:
            continue
        print("network={")
        print(f'    ssid="{ssid}"')
        if password:
            print(f'    psk="{password}"')
        else:
            print("    key_mgmt=NONE")
        print("}")
        print("")
except Exception as e:
    print(f"# FEHLER beim Lesen der wifi_config.json: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

} > "$WPA_CONF"

log "wpa_supplicant.conf aktualisiert mit $(python3 -c "
import json
with open('$WIFI_CONFIG_FILE') as f:
    d = json.load(f)
print(len(d.get('networks', [])))
" 2>/dev/null) Netzwerk(en)."

# USB-Share wieder unmounten (falls wir es selbst gemountet haben)
if [ "$MOUNTED_HERE" = true ]; then
    umount "$USB_MOUNT" 2>/dev/null || true
    losetup -d "$LOOP_DEV" 2>/dev/null || true
fi

# wpa_supplicant neu starten damit neue Konfiguration greift
log "Starte wpa_supplicant neu..."
wpa_cli -i wlan0 reconfigure 2>/dev/null || true

log "WLAN-Konfiguration abgeschlossen."
exit 0
