# SPL Meter Setup Anleitung

Diese Anleitung beschreibt die vollständige Einrichtung des SPL Meter Projekts auf einem Raspberry Pi Zero W mit ICS43434 Mikrofon.

## Hardware-Voraussetzungen

- Raspberry Pi Zero W
- ICS43434 I2S-Mikrofon
- MicroSD-Karte (mindestens 16GB, Class 10)
- Stromversorgung (mindestens 2.5A)
- Jumper-Kabel für die Verbindungen

## Hardware-Anschluss

### Pinbelegung ICS43434 → Raspberry Pi Zero W

```
ICS43434     →    Raspberry Pi Zero W
----------         ------------------
Sel         →    Pin 38 (GPIO20)
Lrcl        →    Pin 40 (GPIO21)
BCLK        →    Pin 12 (GPIO18)  
Dout        →    Pin 35 (GPIO19)
GND         →    Pin 6  (GND)
3V          →    Pin 1  (3.3V)
```

### Wichtige Hinweise
- Das ICS43434 arbeitet mit 3.3V Spannung
- Verwende kurze Kabelverbindungen zur Minimierung von Störungen
- Das Mikrofon unterstützt 16-24 Bit Auflösung bei 8-96 kHz Abtastrate

## Raspberry Pi Konfiguration

### 1. I2S-Schnittstelle aktivieren

Füge folgende Zeilen zur `/boot/config.txt` hinzu:
```
dtparam=i2s=on
dtoverlay=i2s-mmap
```

**Schritte:**
```bash
sudo nano /boot/config.txt
# Zeilen am Ende hinzufügen
# Strg+X, Y, Enter zum Speichern
sudo reboot
```

### 2. System aktualisieren

```bash
sudo apt update
sudo apt upgrade -y
```

## Software-Installation

> **Tipp:** Alle Schritte 1–5 sind im Skript `setup.sh` automatisiert. Einfach ausführen:
> ```bash
> cd ~/projects/SPL_Meter
> bash setup.sh
> ```

### 1. Git installieren

```bash
sudo apt install git -y
```

### 2. Repository klonen

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/jonasblome/SPL_Meter.git
cd SPL_Meter
```

### 3. In den richtigen Branch wechseln

```bash
git checkout Mikrophone-Setup
```

### 4. Systemabhängigkeiten installieren

Diese Pakete werden zwingend benötigt, bevor pip-Pakete funktionieren:

```bash
sudo apt install -y \
    python3-pip \
    python3-venv \
    libopenblas-dev \
    portaudio19-dev
```

**Warum:**
- `libopenblas-dev` — numpy benötigt diese Bibliothek zur Laufzeit (`libopenblas.so.0`)
- `portaudio19-dev` — pyaudio benötigt diese Bibliothek zur Laufzeit

### 5. Virtual Environment einrichten und Pakete installieren

```bash
python3 -m venv spl_meter_env
source spl_meter_env/bin/activate
pip install --only-binary :all: -r requirements.txt
```

> **Wichtig:** `--only-binary :all:` verhindert, dass pip versucht, Pakete aus dem Quellcode zu kompilieren. Auf dem Pi Zero W würde das den Pi zum Einfrieren bringen oder stundenlang dauern. piwheels.org stellt fertige ARM-Wheels bereit.

## Tailscale Einrichtung (für Remote-Zugriff)

### 1. Tailscale installieren

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

### 2. Tailscale starten

```bash
sudo tailscale up
```

### 3. Authentifizierung

- Öffne die angezeigte URL in einem Browser
- Melde dich mit deinem Tailscale-Konto an
- Kopiere den Authentifizierungscode und füge ihn ein

### 4. Verbindung testen

```bash
tailscale status
```

## SSH-Konfiguration (für Remote-Entwicklung)

### 1. SSH-Config auf lokalem Rechner anpassen

Füge zu `~/.ssh/config` hinzu:
```ssh
Host raspberrypi
    HostName teamrapsberrypizero2-1.taild07c04.ts.net
    User teamrapsberry

Host raspberrypi-ip
    HostName 100.72.31.30
    User teamrapsberry
```

### 2. Verbindung testen

```bash
ssh teamrapsberry@teamrapsberrypizero2-1.taild07c04.ts.net
```

## Projekt-Test

### 1. Zum Projekt-Verzeichnis navigieren

```bash
cd ~/SPL_Meter
```

### 2. Mikrofon-Test starten

```bash
python3 src/audio_input.py
```

**Erwartete Ausgabe:**
```
ICS43434 Microphone Reader
========================================
Available audio devices:
[Geräteliste]
Starting recording at 44100 Hz...
Press Ctrl+C to stop recording
RMS: 0.000123, SPL: 45.23 dB, Max: 0.000456
RMS: 0.000098, SPL: 43.82 dB, Max: 0.000234
...
```

## Fehlerbehandlung

### Häufige Probleme

#### 1. "git: command not found"
```bash
sudo apt install git -y
```

#### 2. "externally-managed-environment" Fehler
Niemals `pip install` direkt (ohne venv) ausführen. Immer Virtual Environment nutzen (siehe Schritt 5).

#### 3. pip installiert numpy aus Quellcode / Pi friert ein
`requirements.txt` verwendet `numpy==2.2.4` (gepinnte Version mit piwheels-Wheel).  
Immer `--only-binary :all:` verwenden:
```bash
pip install --only-binary :all: -r requirements.txt
```

#### 4. "libopenblas.so.0: cannot open shared object file"
```bash
sudo apt install libopenblas-dev -y
```

#### 5. "Could not import the PyAudio C module 'pyaudio._portaudio'"
```bash
sudo apt install portaudio19-dev -y
pip install pyaudio
```

#### 6. Kein Audio-Gerät gefunden (`Invalid input device`)
- I2S-Treiber noch nicht aktiv — prüfen mit `arecord -l`
- Falls leer: `/boot/firmware/config.txt` bearbeiten und folgende Zeilen hinzufügen:
```
dtparam=i2s=on
dtoverlay=i2s-mmap
```
- Danach: `sudo reboot`

#### 7. SSH-Verbindung schlägt fehl
- Überprüfe SSH-Config
- Stelle sicher, dass Tailscale läuft
- Prüfe Benutzername in SSH-Config

### Debugging-Befehle

#### Audio-Geräte prüfen
```bash
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

#### I2S-Status prüfen
```bash
dmesg | grep i2s
```

#### Tailscale-Status prüfen
```bash
sudo tailscale status
```

## Projekt-Struktur

```
SPL_Meter/
├── doc/
│   ├── pinbelegung_ics43434.md    # Pinbelegung und Anschluss
│   ├── architecture.md            # Systemarchitektur
│   └── setup_anleitung.md         # Diese Anleitung
├── src/
│   └── audio_input.py             # Hauptprogramm
├── test/
│   └── test_audio_input.py        # Unit Tests
├── requirements.txt               # Python-Abhängigkeiten
└── README.md                      # Projektbeschreibung
```

## Nächste Schritte

1. **Kalibrierung:** Implementiere eine Kalibrierungsfunktion für genaue SPL-Messungen
2. **Datenlogging:** Speichere Messdaten in einer Datei
3. **Web-Interface:** Erstelle ein Web-Dashboard für die Anzeige
4. **Alarm-Funktion:** Implementiere Schwellenwert-Alarme

## Unterstützung

Bei Problemen:
- Prüfe die Pinbelegungsdokumentation in `doc/pinbelegung_ics43434.md`
- Konsultiere die Architekturdokumentation in `doc/architecture.md`
- Nutze die Unit Tests in `test/test_audio_input.py`

---

**Hinweis:** Diese Anleitung wurde für Raspberry Pi Zero W mit Raspberry Pi OS Lite erstellt. Bei anderen Versionen können einige Schritte abweichen.
