# SPL Meter Architecture

## Projektübersicht

Dieses Projekt implementiert ein einfaches SPL (Sound Pressure Level) Meter auf einem Raspberry Pi Zero W mit einem ICS43434 I2S-Mikrofon. Das Ziel ist die Ausgabe von reinen Messdaten über das Terminal.

## Systemarchitektur

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi Zero W                      │
├─────────────────────────────────────────────────────────────┤
│  Hardware Layer                                            │
│  ┌─────────────┐                                           │
│  │ ICS43434    │ I2S Interface                            │
│  │ Mikrofon    │ GPIO 18, 19, 21                          │
│  └─────────────┘                                           │
├─────────────────────────────────────────────────────────────┤
│  Software Layer                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Audio Input Module                        │   │
│  │  • I2S-Kommunikation                               │   │
│  │  • Audio-Stream-Management                         │   │
│  │  • RMS-Berechnung                                  │   │
│  │  • SPL-Umrechnung                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Output Module                          │   │
│  │  • Terminal-Ausgabe                                │   │
│  │  • Datenformatierung                               │   │
│  │  • Echtzeit-Display                                │   │
│  └─────────────────────────────────────────────────────┘   │
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

### 1. Audio Input Module (`src/audio_input.py`)

**Verantwortlichkeiten:**
- I2S-Mikrofon-Initialisierung
- Audio-Stream-Management
- Echtzeit-Audioverarbeitung
- RMS-Berechnung
- SPL-Umrechnung

**Hauptkomponenten:**
- `ICS43434Reader` Klasse
- Audio-Callback-Funktion
- Geräte-Konfiguration

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
- **Abtastrate:** 44.1 kHz (konfigurierbar)
- **Bit-Tiefe:** 32-bit Float
- **Kanäle:** 1 (Mono)
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

### Python-Pakete
- `numpy`: Numerische Berechnungen
- `sounddevice`: Audio-I/O

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
