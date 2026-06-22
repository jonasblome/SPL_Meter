# SPL Meter Architecture

## Projektübersicht

Dieses Projekt implementiert ein einfaches SPL (Sound Pressure Level) Meter auf einem Raspberry Pi Zero W mit einem ICS43434 I2S-Mikrofon. Das Ziel ist die Ausgabe von reinen Messdaten über das Terminal.

## Systemarchitektur

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi Zero W                      │
├─────────────────────────────────────────────────────────────┤
│  Hardware Layer                                             │
│  ┌─────────────┐                                            │
│  │ ICS43434    │ I2S Interface                              │
│  │ Mikrofon    │ GPIO 18, 19, 20, 21                        │
│  │             │ Sel → GND (linker Kanal)                   │
│  └─────────────┘                                            │
├─────────────────────────────────────────────────────────────┤
│  Software Layer                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Audio Device Manager                      │    │
│  │  • I2S-Kommunikation                                │    │
│  │  • Audio-Stream-Management                          │    │
│  │  • Geräte-Enumeration                               │    │
│  │  • RMS-Berechnung                                   │    │
│  │  • SPL-Umrechnung                                   │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Output Module                          │    │
│  │  • Terminal-Ausgabe                                 │    │
│  │  • Datenformatierung                                │    │
│  │  • Echtzeit-Display                                 │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  Application Layer                                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Main Program                           │   │
│  │  • Initialisierung                                 │   │
│  │  • Steuerung                                       │   │
│  │  • Fehlerbehandlung                                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Module-Struktur

### 1. Audio Device Manager (`src/AudioDeviceManager.py`)

**Verantwortlichkeiten:**
- I2S-Mikrofon-Initialisierung
- Audio-Stream-Management
- Geräte-Enumeration und -Auswahl
- Echtzeit-Audioverarbeitung
- RMS-Berechnung
- SPL-Umrechnung

**Hauptkomponenten:**
- `AudioDeviceManager` Klasse
- Audio-Callback-Funktion
- Konfigurierbare Geräteauswahl über `device_index`

### 2. Output Module (geplant)

**Verantwortlichkeiten:**
- Terminal-Ausgabe
- Datenformatierung
- Logging

## Datenfluss

```
ICS43434 Mikrofon
       ↓
   I2S Interface
       ↓
   Audio Stream
       ↓
   RMS Berechnung
       ↓
   SPL Umrechnung
       ↓
   Terminal Ausgabe
```

## Technische Spezifikationen

### Audio-Parameter
- **Abtastrate:** 48 kHz (konfigurierbar)
- **Bit-Tiefe:** 32-bit PCM (I2S-Treiber), 24-bit effektive Daten
- **Kanäle:** 2 (Stereo, ICS43434 liefert links/rechts)
- **Chunk-Größe:** 1024 Samples

### SPL-Berechnung
- **Referenzdruck:** 20 µPa (0.00002 Pa)
- **Formel:** SPL(dB) = 20 * log10(RMS / 0.00002)
- **Ausgabeformat:** RMS-Wert, SPL in dB, Peak-Wert

## Abhängigkeiten

### System-Anforderungen
- Raspberry Pi Zero W
- I2S-fähiges Mikrofon (ICS43434)
- Aktiviertes I2S-Interface
- `dtoverlay=googlevoicehat-soundcard` in `/boot/firmware/config.txt`

### Python-Pakete
- `numpy`: Numerische Berechnungen
- `pyaudio`: Audio-I/O

### System-Pakete (über apt)
- `python3-pip`: Python-Paketmanager
- `python3-venv`: Virtual Environment
- `libopenblas-dev`: Laufzeitbibliothek für numpy
- `portaudio19-dev`: Laufzeitbibliothek für pyaudio
- `raspi-gpio`: Diagnosetool für GPIO-Pin-Modi

## Erweiterungsmöglichkeiten

### Zukünftige Features
- Kalibrierungsfunktion
- Frequenzanalyse (FFT)
- Datenlogging
- Web-Interface
- Alarm-Funktion bei Schwellenwerten

### Modulare Erweiterungen
- `spl_calibrator.py`: Kalibrierungsmodule
- `data_logger.py`: Datenspeicherung
- `web_interface.py`: Web-Dashboard
- `alarm_system.py`: Schwellenwert-Alarme

## Fehlerbehandlung

### Mögliche Fehlerquellen
- I2S-Interface nicht verfügbar
- Mikrofon nicht verbunden
- Audio-Geräte-Probleme
- Berechnungsfehler

### Strategien
- Geräte-Überprüfung vor Start
- Graceful Error Handling
- Logging von Fehlern
- Benutzerfreundliche Fehlermeldungen

## Performance-Überlegungen

### Optimierungen
- Effiziente Audio-Buffer-Verwaltung
- Minimale Latenz durch Callback-Architektur
- Speicheroptimierte Berechnungen

### Ressourcen-Nutzung
- CPU: < 10% für Audioverarbeitung
- RAM: < 50MB
- Speicher: Nur temporäre Daten
