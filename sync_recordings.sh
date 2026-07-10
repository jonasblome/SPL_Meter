#!/bin/bash
# sync_recordings.sh
# Kopiert lokale Aufnahmen auf das USB-Laufwerk, bevor das Gadget aktiv wird.

LOCAL_RECORDINGS="/home/teamrapsberry/recordings_local"
USB_MOUNT="/mnt/usb_share"
BACKING_STORE="/home/teamrapsberry/backing_store.img"

set -e

# Sicherstellen, dass libcomposite geladen ist (fuer spaeteres Gadget)
modprobe libcomposite 2>/dev/null || true

if [ ! -d "$LOCAL_RECORDINGS" ] || [ -z "$(ls -A "$LOCAL_RECORDINGS" 2>/dev/null)" ]; then
    echo "Keine lokalen Aufnahmen zum Synchronisieren."
    exit 0
fi

if [ ! -f "$BACKING_STORE" ]; then
    echo "Backing Store nicht gefunden, überspringe Sync."
    exit 0
fi

mkdir -p "$USB_MOUNT"

# Backing Store intern mounten
LOOP_DEV=$(sudo losetup --show -fP "$BACKING_STORE")
if sudo mount -t vfat "${LOOP_DEV}" "$USB_MOUNT" 2>/dev/null || \
   sudo mount -t vfat "${LOOP_DEV}p1" "$USB_MOUNT" 2>/dev/null; then
    
    mkdir -p "$USB_MOUNT/recordings"
    cp -ru "$LOCAL_RECORDINGS"/* "$USB_MOUNT/recordings/" 2>/dev/null || true
    echo "Aufnahmen auf USB-Laufwerk kopiert."
    
    sudo umount "$USB_MOUNT" 2>/dev/null || true
else
    echo "WARNUNG: Backing Store konnte nicht gemountet werden, Sync übersprungen."
fi

sudo losetup -d "$LOOP_DEV" 2>/dev/null || true
