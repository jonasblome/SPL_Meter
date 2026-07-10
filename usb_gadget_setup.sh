#!/bin/bash
# usb_gadget_setup.sh
# Aktiviert den Raspberry Pi Zero als USB-Mass-Storage-Gadget.
# Wird per systemd-Service beim Boot ausgefuehrt.

set -e

GADGET_DIR="/sys/kernel/config/usb_gadget/mygadget"
BACKING_STORE="/home/teamrapsberry/backing_store.img"
USB_MOUNT="/mnt/usb_share"

# libcomposite laden
modprobe libcomposite || {
    echo "FEHLER: libcomposite konnte nicht geladen werden."
    exit 1
}

# Backing Store pruefen
if [ ! -f "$BACKING_STORE" ]; then
    echo "FEHLER: Backing Store nicht gefunden: $BACKING_STORE"
    exit 1
fi

# Internen Mount freigeben, falls vorhanden, damit der PC exklusiven Zugriff hat
if mountpoint -q "$USB_MOUNT" 2>/dev/null; then
    umount "$USB_MOUNT" || true
fi

# Altes Gadget bereinigen, falls vorhanden
if [ -d "$GADGET_DIR" ]; then
    echo "" > "$GADGET_DIR/UDC" 2>/dev/null || true
    rm -f "$GADGET_DIR/configs/c.1/mass_storage.usb0"
    rm -rf "$GADGET_DIR/functions/mass_storage.usb0"
    rm -rf "$GADGET_DIR/configs/c.1/strings/0x409"
    rm -rf "$GADGET_DIR/configs/c.1"
    rm -rf "$GADGET_DIR/strings/0x409"
    rm -rf "$GADGET_DIR"
fi

# Neues Gadget anlegen
mkdir -p "$GADGET_DIR"
cd "$GADGET_DIR"

echo 0x1d6b > idVendor
echo 0x0104 > idProduct
echo 0x0100 > bcdDevice
echo 0x0200 > bcdUSB

mkdir -p strings/0x409
echo "1234567890" > strings/0x409/serialnumber
echo "TU Berlin" > strings/0x409/manufacturer
echo "SPL Meter Storage" > strings/0x409/product

mkdir -p configs/c.1/strings/0x409
echo "Config 1: Mass Storage" > configs/c.1/strings/0x409/configuration
echo 250 > configs/c.1/MaxPower

mkdir -p functions/mass_storage.usb0
echo 0 > functions/mass_storage.usb0/lun.0/cdrom
echo 0 > functions/mass_storage.usb0/lun.0/ro
echo "$BACKING_STORE" > functions/mass_storage.usb0/lun.0/file

ln -s functions/mass_storage.usb0 configs/c.1/

# UDC aktivieren (Gadget am PC sichtbar machen)
ls /sys/class/udc > UDC

echo "USB Mass Storage Gadget aktiviert."
