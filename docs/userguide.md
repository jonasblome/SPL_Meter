# SPL Meter – Nutzeranleitung

Diese Anleitung beschreibt, wie das SPL Meter auf dem Raspberry Pi Zero betrieben wird: von der WLAN-Einrichtung über den Fernzugriff bis hin zur Bedienung über die Weboberfläche.

---

## 1. Gerät mit WLAN verbinden

Das SPL Meter benötigt eine Netzwerkverbindung, damit du per SSH oder über die Web-UI darauf zugreifen kannst. Es gibt zwei Möglichkeiten, das WLAN einzurichten.

### Variante A: Über das USB-Laufwerk ( empfohlen )

Das SPL Meter liest beim Boot automatisch eine Datei namens **`wifi_config.json`** vom USB-Laufwerk (dem „SPL Meter Storage"-Laufwerk, das am PC erscheint). So können WLAN-Zugangsdaten für mehrere Netzwerke hinterlegt werden, ohne SSH-Zugang zu benötigen.

**Schritt 1 – Datei anlegen oder bearbeiten:**

1. USB-Datenkabel an den Pi anschließen und warten bis das Laufwerk „SPL Meter Storage" im Explorer erscheint.
2. Im Stammverzeichnis des Laufwerks eine Datei namens **`wifi_config.json`** anlegen (falls noch nicht vorhanden).
3. Folgenden Inhalt einfügen und die SSIDs sowie Passwörter anpassen:

```json
{
    "networks": [
        {
            "ssid": "Heimnetz",
            "password": "mein_passwort"
        },
        {
            "ssid": "Buero_WLAN",
            "password": "buero_passwort"
        }
    ],
    "country": "DE"
}
```

> **Mehrere Netzwerke:** Es können beliebig viele `network`-Einträge angegeben werden. Der Pi verbindet sich automatisch mit dem stärksten verfügbaren Netzwerk aus der Liste.

> **Offenes Netzwerk (kein Passwort):** Eintrag ohne `"password"`-Feld anlegen oder `"password": ""` setzen.

**Schritt 2 – Pi neu starten:**

Beim nächsten Boot liest der `wifi-connect`-Service die Datei aus und konfiguriert das WLAN automatisch. Es ist kein weiterer Eingriff nötig.


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


## 3. Audioaufnahmen auf dem Pi ansehen

Das SPL Meter kann Audiodaten während der Messung als WAV-Dateien speichern. Dafür muss in der Weboberfläche die Option **„Store Audio“** aktiviert sein (siehe Kapitel 4).

### Speicherort

Während des Betriebs werden WAV-Dateien lokal auf dem Pi abgelegt:

```
/home/teamrapsberry/recordings_local
```

Der Dateiname setzt sich aus dem aktuellen Datum und der Uhrzeit zusammen, z. B.:

```
2026-07-06_14-32-10.wav
```

Beim nächsten Boot werden diese Dateien automatisch in den `recordings`-Ordner auf dem USB-Laufwerk kopiert, damit sie später am PC über „SPL Meter Storage" abgerufen werden können.

> **Speicherlimit:** Damit der Speicher nicht überläuft, werden alte WAV-Dateien automatisch gelöscht, sobald das gesamte Aufnahmevolumen 1,6 GB überschreitet. Es werden immer die ältesten Dateien zuerst entfernt.

### Aufnahmen ansehen

Per SSH auf dem Pi:

```bash
ls -la /home/teamrapsberry/recordings_local
```

Eine Datei herunterladen:

```bash
scp teamrapsberry@<IP-ADRESSE>:/home/teamrapsberry/recordings_local/2026-07-06_14-32-10.wav .
```

Oder über das USB-Laufwerk: Nach einem Reboot findest du die bisherigen Aufnahmen auf „SPL Meter Storage" im Ordner `recordings`.

> **Achtung:** Das USB-Laufwerk wird erst korrekt erkannt, wenn der Pi vollständig gebootet ist. Zuerst Strom anschließen, warten und erst dann das Daten-USB-Kabel mit dem PC verbinden.

---

## 4. SPL Meter im Allgemeinen bedienen

Das SPL Meter wird über eine **Web-UI** gesteuert. Die Flask-Weboberfläche läuft direkt auf dem Pi und ist über jeden Browser erreichbar.

### Starten des Dienstes

Nach der Einrichtung mit `setup.sh` startet das SPL Meter **automatisch beim Boot** als Systemdienst. Du musst es also **nicht selbst starten**, sobald der Pi läuft.

Im Normalfall reicht es, die IP-Adresse des Pi zu ermitteln und die Web-UI im Browser zu öffnen:

```
http://<IP-ADRESSE-DES-PI>:8501
```

Beispiel:

```
http://192.168.178.67:8501
```

Wenn du über Tailscale verbunden bist, funktioniert auch:

```
http://teamrapsberrypizero2-1.taild07c04.ts.net:8501
```

Falls nötig, kann der Dienst manuell gesteuert werden:

```bash
sudo systemctl start  spl-meter.service
sudo systemctl stop   spl-meter.service
sudo systemctl status spl-meter.service
```

Oder manuell aus dem Projektverzeichnis starten (nur für Tests oder Entwicklung):

```bash
cd ~/SPL_Meter
source spl_meter_env/bin/activate
python3 src/main.py
```

### Kommandozeilenoptionen

Das Skript `src/main.py` kennt derzeit nur einen optionalen Parameter:

| Befehl | Bedeutung |
|---|---|
| `python3 src/main.py` | Startet das SPL Meter mit dem echten Mikrofon (I2S). |
| `python3 src/main.py --simulate /pfad/zur/datei.wav` | Startet das SPL Meter im Simulationsmodus und liest die Audioausgabe aus einer WAV-Datei. |

Beispiel für den Simulationsmodus:

```bash
python3 src/main.py --simulate /home/teamrapsberry/testsignal.wav
```

> **Hinweis:** Die Klasse `CommandLineController` in `@c:\Users\Lars\Documents\GitHub\SPL_Meter\src\CommandLineController.py` ist aktuell nur ein Platzhalter und stellt keine weiteren Befehle zur Verfügung. Alle Steuerung erfolgt über die Web-UI oder den systemd-Dienst.

### Funktionen der Web-UI

Die Oberfläche zeigt folgende Bereiche an:

| Bereich | Bedeutung |
|---|---|
| **Start / Stop Measurement** | Mikrofonaufnahme starten oder stoppen |
| **Leq Duration** | Messdauer für eine Leq-Messung auswählen (5 s, 10 s, 15 s, 30 s, 60 s, 300 s) |
| **Start Leq** | Eine integrierte Leq-Messung über die gewählte Dauer starten |
| **Store Audio** | Aktiviert die Speicherung der Aufnahme als WAV-Datei unter `/home/teamrapsberry/recordings_local` |
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

1. Pi einschalten und warten, bis er mit dem Netzwerk verbunden ist.
2. IP-Adresse des Pi ermitteln und die Web-UI im Browser öffnen: `http://<IP-ADRESSE>:8501`.
   > Der Dienst startet automatisch – es ist kein manuelles Starten nötig.
3. Optional: **„Store Audio“** (im Voraus!) aktivieren, um die Aufnahme zu speichern.
4. Auf **„Start Measurement“** klicken.
5. Optional: **„Leq Duration“** wählen und **„Start Leq“** klicken.
6. Nach der Messung auf **„Stop Measurement“** klicken.
7. Aufgenommene WAV-Dateien liegen zunächst unter `/home/teamrapsberry/recordings_local`.
8. Nach einem Reboot erscheinen die Aufnahmen automatisch auf dem USB-Laufwerk unter `recordings/`.

---

## 5. Wichtige Hinweise

- Der Pi Zero hat zwei Micro-USB-Anschlüsse: **PWR IN** (nur Strom) und **USB** (Daten + Strom). Für den Mass-Storage-Modus zuerst Strom anschließen, booten lassen und dann das Datenkabel an den USB-Port stecken.
- Für stabile Datenverbindungen ein **Charge & Sync**-Kabel verwenden, kein reines Ladekabel.
- Bei Problemen mit der WLAN-Verbindung die IP-Adresse im Router prüfen oder `sudo systemctl status spl-meter.service` auf dem Pi ausführen.
- **Speicherlimit für Aufnahmen:** Das SPL Meter löscht automatisch die ältesten WAV-Dateien, sobald das gesamte Aufnahmevolumen 1,6 GB überschreitet. Wichtige Messungen sollten daher regelmäßig vom Pi oder USB-Laufwerk gesichert werden.

---

## 6. Weitere Dokumente

- Verbindung über Tailscale & VS Code: `@c:\Users\Lars\Documents\GitHub\SPL_Meter\docs\connecting_to_raspberry_pi_zero.md`
- Erstinstallation & Systemdienst: `@c:\Users\Lars\Documents\GitHub\SPL_Meter\setup.sh`
- Hardware-Anschluss des Mikrofons: `@c:\Users\Lars\Documents\GitHub\SPL_Meter\docs\pinbelegung_ics43434.md`
