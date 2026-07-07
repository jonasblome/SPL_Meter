# SPL Meter – Nutzeranleitung

Diese Anleitung beschreibt, wie das SPL Meter auf dem Raspberry Pi Zero betrieben wird: von der WLAN-Einrichtung über den Fernzugriff bis hin zur Bedienung über die Weboberfläche.

---

## 1. Gerät mit WLAN verbinden

Das SPL Meter benötigt eine Netzwerkverbindung, damit du per SSH oder über die Web-UI darauf zugreifen kannst. Es gibt zwei Möglichkeiten, das WLAN einzurichten.

### Variante A: Vor dem ersten Boot ( empfohlen )

Diese Variante funktioniert nur bei einer frischen SD-Karte oder vor dem Einschalten des Pi.

1. SD-Karte in den Computer einlegen.
2. Die Partition **`boot`** öffnet sich im Explorer.
3. Eine Datei mit dem Namen **`wpa_supplicant.conf`** im Stammverzeichnis der `boot`-Partition anlegen.
4. Folgenden Inhalt einfügen und WLAN-Name sowie Passwort anpassen:

```
country=DE
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="EUER_WLAN_NAME"
    psk="EUER_WLAN_PASSWORT"
}
```

5. Eine **leere Datei** mit dem Namen **`ssh`** (ohne Dateiendung!) anlegen. Das aktiviert den SSH-Server beim Boot.
6. SD-Karte in den Pi einsetzen und Strom anschließen.
7. Nach ca. 30–60 Sekunden bootet der Pi und verbindet sich mit dem WLAN.

### Variante B: Über SSH (Pi ist bereits erreichbar)

Wenn du bereits eine Verbindung zum Pi hast, kannst du das WLAN auch nachträglich konfigurieren:

```bash
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```

Dort den gewünschten `network`-Block einfügen, speichern (`Strg+O`, `Enter`) und beenden (`Strg+X`). Anschließend neu verbinden:

```bash
sudo wpa_cli -i wlan0 reconfigure
```

> **Hinweis:** Wenn der Pi über Tailscale erreichbar sein soll, muss nach der WLAN-Verbindung Tailscale einmalig eingerichtet werden (siehe Kapitel 3).

---

## 2. SSH-Verbindung herstellen

Sobald der Pi im Netzwerk ist, kannst du dich per SSH mit ihm verbinden. Die Standard-Anmeldedaten lauten:

- **Benutzername:** `teamrapsberry`
- **Passwort:** `tuberlin`

### Lokale Verbindung (im selben Netzwerk)

1. IP-Adresse des Pi ermitteln, z. B. im Router-Admin unter „Verbundene Geräte“.
2. Im Terminal oder PowerShell folgenden Befehl eingeben:

```bash
ssh teamrapsberry@<IP-ADRESSE>
```

Beispiel:

```bash
ssh teamrapsberry@192.168.178.67
```

3. Beim ersten Verbinden erscheint eine Host-Key-Abfrage:

```
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

→ `yes` eingeben und das Passwort **`tuberlin`** eingeben.

### Verbindung über Tailscale (auch außerhalb des lokalen Netzwerks)

Tailscale ermöglicht den Zugriff auf den Pi, egal wo du dich befindest. Voraussetzung ist, dass Tailscale auf dem Pi und auf deinem Computer installiert und eingeloggt ist.

```bash
ssh teamrapsberry@teamrapsberrypizero2-1.taild07c04.ts.net
```

> Der aktuelle Tailscale-Hostname und Status sind im Tailscale-Admin-Panel unter [https://login.tailscale.com/admin/machines](https://login.tailscale.com/admin/machines) ersichtlich.

### Verbindung über VS Code Remote-SSH

Detaillierte Schritte für VS Code mit Tailscale findest du in der Datei:

- `@c:\Users\Lars\Documents\GitHub\SPL_Meter\docs\connecting_to_raspberry_pi_zero.md`

Darin ist erklärt, wie du die SSH-Config, die Remote-SSH-Erweiterung und die Verbindung in VS Code einrichtest.

---

## 3. Audioaufnahmen auf dem Pi ansehen

Das SPL Meter kann Audiodaten während der Messung als WAV-Dateien speichern. Dafür muss in der Weboberfläche die Option **„Store Audio“** aktiviert sein (siehe Kapitel 4).

### Speicherort

Aufgenommene WAV-Dateien werden im folgenden Ordner abgelegt:

```
/mnt/usb_share/recordings
```

Der Dateiname setzt sich aus dem aktuellen Datum und der Uhrzeit zusammen, z. B.:

```
2026-07-06_14-32-10.wav
```

### Aufnahmen ansehen

Per SSH auf dem Pi:

```bash
ls -la /mnt/usb_share/recordings
```

Eine Datei anhören oder herunterladen:

```bash
scp teamrapsberry@<IP-ADRESSE>:/mnt/usb_share/recordings/2026-07-06_14-32-10.wav .
```

Oder über die Weboberfläche des Mass-Storage-Gadgets: Wenn der Pi als USB-Laufwerk erkannt wird, findest du die Aufnahmen auf dem freigegebenen Speicher unter dem Ordner `recordings`.

> **Achtung:** Das USB-Laufwerk wird erst korrekt erkannt, wenn der Pi vollständig gebootet ist. Zuerst Strom anschließen, warten und erst dann das Daten-USB-Kabel mit dem PC verbinden.

---

## 4. SPL Meter im Allgemeinen bedienen

Das SPL Meter wird über eine **Web-UI** gesteuert. Die Flask-Weboberfläche läuft direkt auf dem Pi und ist über jeden Browser erreichbar.

### Starten des Dienstes

Nach der Einrichtung mit `setup.sh` startet das SPL Meter automatisch als Systemdienst:

```bash
sudo systemctl start  spl-meter.service
sudo systemctl stop   spl-meter.service
sudo systemctl status spl-meter.service
```

Manuell starten:

```bash
cd ~/SPL_Meter
source spl_meter_env/bin/activate
python3 src/main.py
```

### Aufruf der Web-UI

Sobald der Dienst läuft, ist die Oberfläche unter folgender Adresse erreichbar:

```
http://<IP-ADRESSE-DES-PI>:8501
```

Wenn du über Tailscale verbunden bist, funktioniert auch:

```
http://teamrapsberrypizero2-1.taild07c04.ts.net:8501
```

### Funktionen der Web-UI

Die Oberfläche zeigt folgende Bereiche an:

| Bereich | Bedeutung |
|---|---|
| **Start / Stop Measurement** | Mikrofonaufnahme starten oder stoppen |
| **Leq Duration** | Messdauer für eine Leq-Messung auswählen (5 s, 10 s, 15 s, 30 s, 60 s, 300 s) |
| **Start Leq** | Eine integrierte Leq-Messung über die gewählte Dauer starten |
| **Store Audio** | Aktiviert die Speicherung der Aufnahme als WAV-Datei unter `/mnt/usb_share/recordings` |
| **Calibration** | Mikrofon mit einem bekannten Schalldruckpegel (z. B. 94 dB) kalibrieren |

### Angezeigte Messwerte

| Wert | Erklärung |
|---|---|
| **A-Weighted** | A-bewerteter Schalldruckpegel in dB |
| **SPL** | Roher Schalldruckpegel in dB |
| **RMS** | Effektivwert des Audiosignals |
| **Peak** | Maximaler Spitzenwert |
| **Fast** | Zeitbewertung „Fast“ (0,125 s) |
| **Slow** | Zeitbewertung „Slow“ (1,0 s) |
| **Leq** | Äquivalenter Dauerschallpegel für die gewählte Messdauer |

Darunter wird die Aufteilung der Schalldruckpegel nach Frequenzbändern als Balken dargestellt.

### Ablauf einer typischen Messung

1. Pi einschalten und sicherstellen, dass er mit dem Netzwerk verbunden ist.
2. Web-UI im Browser öffnen.
4. Optional: **„Store Audio“** (im Voraus!) aktivieren, um die Aufnahme zu speichern.
3. Auf **„Start Measurement“** klicken.
5. Optional: **„Leq Duration“** wählen und **„Start Leq“** klicken.
6. Nach der Messung auf **„Stop Measurement“** klicken.
7. Aufgenommene WAV-Dateien liegen unter `/mnt/usb_share/recordings`.

---

## 5. Wichtige Hinweise

- Der Pi Zero hat zwei Micro-USB-Anschlüsse: **PWR IN** (nur Strom) und **USB** (Daten + Strom). Für den Mass-Storage-Modus zuerst Strom anschließen, booten lassen und dann das Datenkabel an den USB-Port stecken.
- Für stabile Datenverbindungen ein **Charge & Sync**-Kabel verwenden, kein reines Ladekabel.
- Bei Problemen mit der WLAN-Verbindung die IP-Adresse im Router prüfen oder `sudo systemctl status spl-meter.service` auf dem Pi ausführen.

---

## 6. Weitere Dokumente

- Verbindung über Tailscale & VS Code: `@c:\Users\Lars\Documents\GitHub\SPL_Meter\docs\connecting_to_raspberry_pi_zero.md`
- Erstinstallation & Systemdienst: `@c:\Users\Lars\Documents\GitHub\SPL_Meter\setup.sh`
- Hardware-Anschluss des Mikrofons: `@c:\Users\Lars\Documents\GitHub\SPL_Meter\docs\pinbelegung_ics43434.md`
