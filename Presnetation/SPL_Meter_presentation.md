---
marp: true
theme: default
paginate: true
---

<style>
section {
  font-size: 20px;
  background-color: #000000;
  color: #ffffff;
}

h1, h2, h3, h4, h5, h6 {
  color: #ffffff;
}

a {
  color: #66b3ff;
}

code {
  color: #f0f0f0;
  background-color: #222222;
  font-size: 16px;
}

pre {
  background-color: #1a1a1a;
}

pre code {
  font-size: 14px;
}

strong {
  color: #ffffff;
}

th, td {
  color: #ffffff;
  border-color: #555555;
}

.two-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
</style>

# SPL Meter on a Raspberry Pi Zero W

**Jonas Blome (510438), Jonathan Ploch (XXXXXX), Lars Dickmann (0486312), Tianyi Feng (XXXXXX)**

---

# Agenda

1. Aufgabe & Ziel
2. Anforderungen
3. Umsetzung & Architektur
4. Code-Einblicke
5. Setup & Betrieb
6. Dokumentation
7. Live-Demonstration
8. Ausblick & Diskussion

---

# Aufgabe

<div class="two-columns">
<div>

**Ziel:** Portables, eingebettetes Schallpegelmessgerät (SPL Meter) auf Raspberry Pi Zero W.

**Fokus:**
- Echtzeit-Audioanalyse
- Hardwarenahe Python-Programmierung
- Ressourcenschonende Umsetzung

</div>
<div>

**Ergebnis:**
- SPL-Metriken in Echtzeit
- Web-UI für Bedienung
- JSON-Export & Audio-Aufnahme
- Autonomer Betrieb am Pi

</div>
</div>

---

# Anforderungen

<div class="two-columns">
<div>

## Muss
- I2S-Audioeingang 48 kHz
- Peak, RMS, SPL in dB
- Fast (125 ms) & Slow (1 s)
- Leq-Messung
- Oktav-/Terzbandanalyse
- A- & Z-Frequenzbewertung
- Web-UI
- JSON-Export

</div>
<div>

## Kann
- Mikrofonkalibrierung
- Command-Line-Steuerung
- Audio-Aufzeichnung
- Simulierter Betrieb per WAV

</div>
</div>

---

# Umsetzung

<div class="two-columns">
<div>

## Software
- Python 3.12.x
- Flask
- PyAudio
- NumPy
- SciPy

## Hardware
- Raspberry Pi Zero W
- Adafruit I2S MEMS Mikrofon ICS-43434
- VS Code Remote + Tailscale

</div>
<div>

## Komponenten
- `main.py` – Einstieg
- `SPLMeter.py` – Orchestration
- `AudioDeviceManager.py` – I2S-Stream
- `AudioDeviceSimulator.py` – WAV-Test
- `AudioProcessor.py` – Berechnungen
- `UIHandler.py` – Flask-Web-UI

</div>
</div>

---

# Architektur & Datenfluss

<div class="two-columns">
<div>

**Fluss:**
1. Mikrofon liefert PCM-Blöcke
2. `AudioDeviceManager` liest 32-Bit-Worte
3. Konvertierung zu Float [-1, 1]
4. `AudioProcessor` berechnet Metriken
5. `UIHandler` aktualisiert Web-UI
6. Export / Aufnahme

</div>
<div>

**Start:**

```bash
python3 src/main.py
```

**Simulation:**

```bash
python3 src/main.py --simulate tests/testfiles/demo.wav
```

</div>
</div>

---

# Audio-Eingang: I2S → Float

ICS-43434 liefert 24-Bit-MSB-justiert in 32-Bit-Worten:

```python
raw = np.frombuffer(in_data, dtype=np.int32)
audio = raw >> 8
audio_float = audio.astype(np.float32) / 8388608.0
```

Danach: SPL, RMS, Peak, Filterbänder, Zeitbewertung.

---

# SPL-Berechnung

```python
def compute_spl_db(self, audio, p0=20e-6):
    rms = np.sqrt(np.mean(audio**2))
    return 20 * np.log10(rms / p0)
```

Leq (energetischer Mittelwert):

```python
self.leq_sum_square += np.sum(audio**2)
mean_square = self.leq_sum_square / n
leq = 10 * np.log10(mean_square / p0**2)
```

---

# Zeitbewertung & Gewichtung

Fast (τ=0.125 s) und Slow (τ=1.0 s):

```python
def compute_fast_state(self, audio):
    return self.process_time_weighting_block(
        audio, self.fast_state, tau=0.125)
```

A-Gewichtung über Oktav-Filterbank:

```python
sos = signal.butter(10, [f_low, f_high],
                    btype='bandpass', fs=48000, output='sos')
```

---

# Web-UI: Flask + SSE

<div class="two-columns">
<div>

**Endpunkte:**
- `POST /start` – Messung starten
- `POST /stop` – Messung stoppen
- `POST /leq_start` – Leq-Messung
- `POST /calibrate` – Kalibrierung
- `GET /stream` – Echtzeit-Events

</div>
<div>

```python
@self.app.route("/stream")
def stream():
    def event_generator():
        while device_manager.is_recording:
            payload = json.dumps({
                "spl_db": dm.latest_spl_db,
                "peak": dm.latest_peak,
                "leq_db": dm.latest_leq_db,
            })
            yield f"data: {payload}\n\n"
            time.sleep(0.0167)
    return Response(event_generator(),
                    mimetype="text/event-stream")
```

</div>
</div>

---

# Setup & Betrieb

<div class="two-columns">
<div>

## setup.sh
1. Systemabhängigkeiten
2. I2S aktivieren
3. Python-Virtual-Env
4. Pakete installieren
5. Services einrichten
6. USB-Gadget konfigurieren

</div>
<div>

## Services
- `spl-meter.service` – Hauptanwendung
- `wifi-connect.service` – WLAN aus USB-Share
- `sync-recordings.service` – Aufnahmen syncen
- `usb-gadget.service` – USB-Laufwerk

</div>
</div>

---

# Bash-Skripte im Überblick

<div class="two-columns">
<div>

## wifi_connect.sh
- Liest `wifi_config.json` vom USB-Share
- Schreibt `wpa_supplicant.conf`
- Startet WLAN ohne SSH

## usb_gadget_setup.sh
- Aktiviert USB-Mass-Storage-Gadget
- Pi erscheint als `SPL Meter Storage`

</div>
<div>

## sync_recordings.sh
- Kopiert lokale WAVs auf USB-Laufwerk
- Löscht älteste Dateien bei > 1.6 GB

```ini
# spl-meter.service
[Unit]
After=network.target sound.target

[Service]
ExecStart=.../python3 src/main.py
Restart=on-failure
```

</div>
</div>

---

# Dokumentation

<div class="two-columns">
<div>

- `README.md` – Überblick & Start
- `docs/userguide.md` – Web-UI-Bedienung
- `docs/architecture/architecture.md` – Komponenten

</div>
<div>

- `docs/connecting_to_raspberry_pi_zero.md` – SSH & Tailscale
- `setup.sh` / `spl-meter.service` – Installation
- Inline-Docstrings im Code

</div>
</div>

Ziel: Benutzer kann die Software ohne weitere Hilfe nutzen.

---

# Folie: Live Demo

<div class="two-columns">
<div>

**Was zeigen wir:**
- Start auf dem Pi
- Web-UI im Browser
- Echtzeitpegel (SPL, Fast, Slow)
- Leq-Messung über 10 s
- JSON-Export

</div>
<div>

**Hinweise:**
- Stabile Stromversorgung
- Mikrofon vorab prüfen
- Fallback: `python3 src/main.py --simulate tests/testfiles/demo.wav`
- Netzwerkverbindung testen

</div>
</div>

---

# Demonstration

1. Pi verbinden & Software starten
2. `http://<pi-ip>:5000` öffnen
3. Kalibrierung (optional)
4. Messung starten
5. Fast/Slow beobachten
6. Leq-Messung starten
7. Messung stoppen
8. JSON-Export anzeigen
9. Simulation zeigen

---

# Ausblick & Diskussion

- Weitere Metriken: Lmin, Lmax, L10, L90
- Automatische Kalibrierung
- Einsatz im Arbeitsschutz / Umweltmonitoring
- Latenz & Energieverbrauch auf Pi Zero W optimieren

---

# Vielen Dank!

Fragen?
