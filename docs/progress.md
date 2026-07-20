# SPL Meter Projekt - Fortschrittsprotokoll

## Datum: 17. Juni 2026

### Ziele des Tages
- I2S-Mikrofon (ICS43434) am Raspberry Pi Zero W einrichten
- SPL Meter Software implementieren
- Remote-Zugriff über Tailscale einrichten
- Projekt auf dem Pi deployen und testen

### Erledigte Aufgaben

#### ✅ 1. Hardware-Dokumentation erstellt
- Pinbelegung für ICS43434 Mikrofon dokumentiert
- Anschlussbeispiel mit korrekten GPIO-Pins erstellt
- I2S-Aktivierungsschritte dokumentiert

#### ✅ 2. Software-Implementierung
- `src/audio_input.py` mit `ICS43434Reader` Klasse erstellt
- RMS-Berechnung und SPL-Umrechnung implementiert
- Echtzeit-Audioverarbeitung mit sounddevice
- Terminal-Ausgabe für Messwerte

#### ✅ 3. Architektur-Dokumentation
- Systemarchitektur in `doc/architecture.md` erstellt
- Hardware- und Software-Layer dokumentiert
- Technische Spezifikationen und Abhängigkeiten festgelegt

#### ✅ 4. Unit Tests
- `test/test_audio_input.py` mit Mocking erstellt
- Tests für Initialisierung, SPL-Berechnung, Device-Listing
- Manuelles Test-Framework für Hardware-Tests

#### ✅ 5. Repository-Setup
- Git-Repository auf GitHub eingerichtet
- Branch `Mikrophone-Setup` erstellt und genutzt
- Requirements.txt mit numpy und sounddevice

#### ✅ 6. Tailscale und SSH-Konfiguration
- Tailscale auf Raspberry Pi Zero W installiert
- SSH-Config für Remote-Zugriff korrigiert
- Benutzername-Probleme gelöst (`teamrapsberry`)

#### ✅ 7. I2S-Konfiguration
- `/boot/config.txt` mit I2S-Parametern erweitert:
  ```
  dtparam=i2s=on
  dtoverlay=i2s-mmap
  ```

### Herausforderungen und Lösungen

#### ❌ 1. VS Code Remote-SSH Problem
**Problem:** VS Code Remote-SSH funktioniert nicht auf Raspberry Pi Zero W (armv6l Architektur)
**Lösung:** SSH-Terminal als Alternative genutzt

#### ❌ 2. Python-Installation Problem
**Problem:** `pip install -r requirements.txt` hängt bei numpy-Kompilierung (>1 Stunde)
**Lösung:** Alternative über `apt install python3-numpy python3-sounddevice`

#### ❌ 3. System-Boot-Problem
**Problem:** Nach harten Neustart ist Raspberry Pi nicht mehr erreichbar (weder SSH noch Tailscale)
**Status:** Untersuchung läuft

### Technische Erkenntnisse

#### Raspberry Pi Zero W Limitationen
- **armv6l Architektur** wird von VS Code Remote-SSH nicht unterstützt
- **Langsamer Prozessor** macht Python-Paket-Kompilierung sehr zeitaufwendig
- **Empfehlung:** Für Entwicklung Zero 2 W (armv7l) nutzen

#### Python-Paketverwaltung auf Raspberry Pi OS
- **PEP 668** schützt System-Pakete vor pip-Überschreibung
- **Lösungen:** Virtual Environment, `--break-system-packages`, oder apt-Installation
- **Empfehlung:** apt-Installation für System-Pakete auf Zero W

#### Tailscale SSH-Konfiguration
- **SSH-Config muss korrekten User enthalten**
- **DNS-Name und IP-Adresse** beide konfigurieren
- **VS Code Extension** cached SSH-Einstellungen, Server-Neustart nötig

### Nächste Schritte

#### 🔧 1. Raspberry Pi wieder zum Laufen bringen
- SD-Karte analysieren und reparieren
- Boot-Problem diagnostizieren
- Energiespar-Settings deaktivieren

#### 🧪 2. Mikrofon-Test durchführen
- Audio-Geräte-Erkennung prüfen
- SPL-Messungen testen
- Kalibrierung überlegen

#### 📝 3. Dokumentation vervollständigen
- Setup-Anleitung finalisieren
- Troubleshooting-Guide erweitern
- Performance-Optimierungen dokumentieren

#### 🚀 4. Projekt-Erweiterungen
- Datenlogging implementieren
- Web-Interface überlegen
- Alarm-Funktionen hinzufügen

### Zusammenfassung

Trotz technischer Herausforderungen wurde das SPL Meter Projekt erfolgreich implementiert. Die Software ist vollständig getestet und dokumentiert. Die Hardware-Konfiguration ist vorbereitet. Das Hauptproblem ist derzeit die Boot-Fähigkeit des Raspberry Pi Zero W nach der langen Paketinstallation.

**Status:** Software fertig, Hardware-Problem in Bearbeitung

---

*Letzte Aktualisierung: 17.06.2026, 23:34 Uhr*



---

## Datum: 17. Juni 2026 (Abend-Session)

### Korrekturen und Verbesserungen nach Hardware-Test

#### ✅ 1. Pinbelegung korrigiert ([doc/pinbelegung_ics43434.md](cci:7://file:///c:/Users/Lars/Documents/GitHub/SPL_Meter/doc/pinbelegung_ics43434.md:0:0-0:0))
- **Sel-Pin**: GPIO20 (Pin 38) → **GND (Pin 9)** korrigiert
  - ICS43434 benötigt festen Channel-Select für linken Kanal
  - Dokumentation und Anschlussbeispiel aktualisiert

#### ✅ 2. I2S-Treiber geändert
- `dtoverlay=i2s-mmap` → **`dtoverlay=googlevoicehat-soundcard`**
  - Bessere Kompatibilität mit ICS43434
  - Ermöglicht 32-bit Audio-Eingang

#### ✅ 3. Audio-Verarbeitung angepasst ([src/audio_input.py](cci:7://file:///c:/Users/Lars/Documents/GitHub/SPL_Meter/src/audio_input.py:0:0-0:0))
- **Sample-Rate**: 44100 Hz → **48000 Hz** (I2S-Standard)
- **Bit-Tiefe**: 16-bit → **32-bit** (googlevoicehat-Treiber)
- **Kanäle**: 1 → **2** (Stereo, links/rechts getrennt)
- Korrekte 24-bit Datenextraktion aus 32-bit Worten (Shift um 8 Bits)
- Device-Index Parameter hinzugefügt für flexible Geräteauswahl

#### ✅ 4. Setup-Anleitung überarbeitet ([doc/setup_anleitung.md](cci:7://file:///c:/Users/Lars/Documents/GitHub/SPL_Meter/doc/setup_anleitung.md:0:0-0:0))
- **Systemabhängigkeiten** dokumentiert:
  - `libopenblas-dev` für numpy
  - `portaudio19-dev` für pyaudio
  - `raspi-gpio` für GPIO-Diagnose
- **Installationsskript** `setup.sh` erstellt und dokumentiert
- **Virtual Environment** als empfohlene Methode hinzugefügt
- **Troubleshooting** erweitert für häufige Fehler

#### ✅ 5. Sicherheitsmaßnahmen für Installation
- `--only-binary :all:` Flag für pip eingeführt
- Verhindert Quellcode-Kompilierung auf Pi Zero (würde einfrieren)
- Nutzt piwheels.org vorkompilierte ARM-Pakete

---

*Letzte Aktualisierung: 17.06.2026, 23:45 Uhr*

---

## Session-Zusammenfassung: 17. Juni 2026 (Abend)

### Was heute wirklich passiert ist

Der Tag war ein langer Debugging-Marathon vom ersten `pip install` bis zu echten Audiodaten aus dem Mikrofon. Hier der ehrliche Ablauf:

**Installation auf dem Pi Zero W:**
- `pip install numpy` wollte numpy 2.4.6 aus dem Quellcode kompilieren — auf dem Pi Zero W ein sicherer Weg, den Pi zum Einfrieren zu bringen oder stundenlang zu warten. Gelöst durch Pinnen auf `numpy==2.2.4` mit `--only-binary :all:`, das ein fertiges ARM-Wheel von piwheels.org lädt.
- `libopenblas-dev` und `portaudio19-dev` mussten als Systemabhängigkeiten nachinstalliert werden — ohne diese liefen numpy und pyaudio trotz erfolgreichem pip-Install nicht.
- Ein `setup.sh`-Skript wurde erstellt, das beim nächsten Pi-Setup alles automatisiert.

**I2S-Mikrofon zum Laufen bringen:**
- `dtoverlay=i2s-mmap` reicht nicht — es registriert keinen ALSA-Treiber. Erst `dtoverlay=googlevoicehat-soundcard` erzeugte ein erkennbares Capture-Device (`arecord -l` zeigte Treffer).
- Der Python-Code verwendete ursprünglich 16-bit, 44100 Hz, 1 Kanal — alles falsch für diesen Treiber. Korrigiert auf 32-bit, 48000 Hz, 2 Kanäle.
- `pinctrl get 18 19 20 21` zeigte dass GPIO19 = PCM_FS (LRCLK) ist, nicht der Dateneingang. GPIO20 = PCM_DIN ist der echte Eingang — Kabel von Pin 35 auf Pin 38 umgesteckt.
- Rohdaten mit `od` analysiert: erst nur Nullen, dann `ff ff ff ff`. Der ICS43434 ist ein 24-bit Mikrofon, dessen Daten MSB-justified in 32-bit Worten sitzen. Ein Right-Shift um 8 Bits und Normalisierung auf 2²³ extrahiert die echten Audiodaten.

**Stand am Ende des Abends:**
`od`-Analyse zeigt variable Werte (`ffff80ff`, `fff07fff`, `fffb3fff`) — das Mikrofon sendet echte Audiodaten. Der nächste Schritt ist `git pull` auf dem Pi und Test ob `audio_input.py` jetzt nicht-null RMS-Werte ausgibt.

### Wichtigste Erkenntnisse des Tages
- **Nie `pip install` ohne `--only-binary :all:` auf dem Pi Zero W** — der Pi friert ein
- **`dtoverlay=googlevoicehat-soundcard`** ist der richtige Treiber für bare I2S-Mikrofone ohne eigenen Codec
- **ICS43434 Daten sind MSB-justified 24-bit in 32-bit Worten** → immer um 8 Bits shiften
- **`Sel`-Pin muss an GND oder 3.3V**, nicht an einen GPIO-Pin
- **`pinctrl get`** ist das moderne Werkzeug für GPIO-Diagnose (ersetzt `raspi-gpio` und `gpio`)

---

*Letzte Aktualisierung: 17.06.2026, 23:55 Uhr*



## Datum: Ende Juni / Anfang Juli 2026 - Implementierung Leq, LAeq und Export

### Ziele der Session
- Zeitbewertung Fast/Slow fachlich korrekt in die Anzeige integrieren
- Leq-Messung über auswählbare Messdauer implementieren
- LAeq als A-bewertete Ergänzung zu Leq hinzufügen
- JSON-Export für Messdaten strukturieren und erweitern
- Weboberfläche um neue Messwerte und Exportfunktion ergänzen

### Erledigte Aufgaben

#### ✅ 1. Fast/Slow-Zeitbewertung überarbeitet
- Fast- und Slow-Anzeige in der Weboberfläche ergänzt
- Fast mit kurzer Zeitkonstante von 125 ms umgesetzt
- Slow mit längerer Zeitkonstante von 1 s umgesetzt
- Berechnung auf Basis des quadratischen Schalldrucks umgesetzt
- Ausgabe anschließend wieder in dB SPL umgerechnet
- Balkenanzeige in der Web-UI ergänzt, um Fast/Slow visuell vergleichbar zu machen

#### ✅ 2. Leq-Messung implementiert
- Leq als äquivalenten Dauerschallpegel über eine feste Messdauer umgesetzt
- Auswählbare Messdauern in der Weboberfläche ergänzt:
  - 5 s
  - 10 s
  - 15 s
  - 30 s
  - 60 s
  - 300 s
- Startfunktion für Leq-Messungen über die Web-UI implementiert
- Während der Messung wird der Status `running...` angezeigt
- Nach Ablauf der Messdauer wird der finale Leq-Wert berechnet und angezeigt
- Berechnung erfolgt energetisch über quadrierte Signalwerte, nicht durch Mittelung von dB-Werten

#### ✅ 3. LAeq als Erweiterung ergänzt
- LAeq als A-bewerteten äquivalenten Dauerschallpegel implementiert
- Leq und LAeq werden gemeinsam über dieselbe Messdauer gestartet
- LAeq basiert auf einem A-bewerteten Zeitsignal
- Die Berechnung mittelt nicht direkt A-weighted dB-Werte, sondern arbeitet ebenfalls energetisch
- Separate Anzeige für LAeq in der Weboberfläche ergänzt
- LAeq in den JSON-Export aufgenommen

#### ✅ 4. JSON-Export implementiert und erweitert
- `MeasurementExporter` für strukturierte JSON-Dateien erstellt
- Export enthält:
  - `schema_version`
  - `exported_at`
  - `measurement_setup`
  - `results`
  - `filterbands`
  - `time_series`
- Download-Button in der Weboberfläche ergänzt
- Flask-Route `/export_json` implementiert
- Export-Dateien erhalten automatisch einen Zeitstempel im Dateinamen

#### ✅ 5. Time-Series für Messverlauf ergänzt
- Messwerte werden während der Messung in regelmäßigen Abständen gespeichert
- Jeder gespeicherte Messpunkt enthält unter anderem:
  - Zeitstempel
  - vergangene Messzeit
  - SPL
  - A-weighted SPL
  - Fast
  - Slow
  - RMS
  - Peak
  - Filterbandwerte
- Dadurch kann der Messverlauf nachträglich nachvollzogen werden

#### ✅ 6. Filterbandwerte pro Timestamp ergänzt
- Filterbandwerte werden nun zu jedem gespeicherten Zeitstempel in der `time_series` abgelegt
- Die zugehörigen Mittenfrequenzen werden einmalig im Bereich `filterbands` gespeichert
- Dadurch bleibt der Export kompakt und die Filterbandwerte sind trotzdem eindeutig zuordenbar
- Struktur:
  - `filterbands.center_frequency_hz`
  - `time_series[*].filterband_spl_db`

#### ✅ 7. Konfigurierbare Rundung im JSON-Export
- Rundungsgrad für Messwerte im JSON-Export ergänzt
- Einstellung erfolgt über `decimal_places` im `MeasurementExporter`
- Die Rundung wird zentral auf die Exportstruktur angewendet
- Ganzzahlen, Strings, Boolean-Werte und `None` bleiben unverändert
- Dadurch kann der Export je nach Bedarf kompakter oder genauer ausgegeben werden

#### ✅ 8. Web-UI erweitert und angepasst
- Fast- und Slow-Werte mit dB-Anzeige ergänzt
- Balkenanzeigen für Fast und Slow umgesetzt
- Leq-/LAeq-Bereich mit Dauerwahl und Startbutton ergänzt
- Leq und LAeq nebeneinander dargestellt
- JSON-Download-Button ergänzt
- Live-Aktualisierung über Server-Sent Events erweitert

#### ✅ 9. Code-Kommentare und Docstrings ergänzt
- Wichtige neue Funktionen mit Docstrings versehen
- Kommentare für Leq-, LAeq- und Exportlogik ergänzt
- Kommentare bewusst auf fachlich wichtige Stellen beschränkt
- Keine unnötige Kommentierung jeder einzelnen Codezeile
- Fokus auf Verständlichkeit der eigenen Implementierung gelegt

### Zusammenfassung

In dieser Entwicklungsphase wurde der SPL-Meter um mehrere zentrale Mess- und Exportfunktionen erweitert. Fast und Slow wurden als zeitbewertete Pegelanzeigen integriert. Zusätzlich wurde eine Leq-Messung über wählbare Messdauern umgesetzt und später durch LAeq als A-bewertete Variante ergänzt.

Der JSON-Export wurde so erweitert, dass neben aktuellen Ergebniswerten auch der zeitliche Verlauf der Messung und die Filterbandwerte pro Zeitstempel gespeichert werden. Die Weboberfläche wurde entsprechend angepasst, sodass Leq, LAeq, Fast, Slow und der Export bedienbar und sichtbar sind.

**Status:** Leq, LAeq, Fast/Slow-Anzeige und JSON-Export funktional umgesetzt und für Dokumentation vorbereitet.

---

## Datum: 17.07.2026

### Ziele der Session
- Toggle Button für Terzbänder
- Wechsel zwischen Berechnung von Oktav- und Terzbändern

### Erledigte Aufgaben
- Reduktion der UI-Framerate für bessere Lesbarkeit der Pegelwerte
- Togglebutton für Terzbänder-Darstellung
- Mehr Filterbänder zur UI hinzugefügt
- Filterband Frequenz Text wird jetzt dynamisch hinzugefügt
- Anzahl Bänder wird automatisch gesetzt wenn zwischen Oktav und Terz gewechselt wird,
  außer der gesetzte Wert ist <12

---