# Remote SSH Verbindung zum Raspberry Pi Zero via Tailscale & VS Code

Diese Anleitung beschreibt Schritt für Schritt, wie man sich vom Windows-PC per VS Code Remote-SSH mit dem Raspberry Pi Zero verbindet. Als VPN-Tunnel wird Tailscale verwendet, damit die Verbindung auch außerhalb des lokalen Netzwerks funktioniert.

---

## 0. Erstverbindung über WLAN (bei Neuinstallation / neuer SD-Karte)

Falls der Pi frisch aufgesetzt wurde und Tailscale noch nicht installiert ist, kann man sich über das lokale WLAN verbinden, um Tailscale einzurichten.

### Vorbereitung auf der boot-Partition (am PC)

1. SD-Karte in den PC einlegen – die **boot**-Partition erscheint im Explorer.
2. Eine Datei `wpa_supplicant.conf` auf der boot-Partition erstellen mit folgendem Inhalt:
   ```
   country=DE
   ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
   update_config=1

   network={
       ssid="EUER_WLAN_NAME"
       psk="EUER_WLAN_PASSWORT"
   }
   ```
3. Eine **leere Datei** namens `ssh` (ohne Dateiendung!) auf der boot-Partition erstellen – das aktiviert den SSH-Server beim Boot.
4. SD-Karte in den Pi einsetzen und Pi einschalten.

### Verbindung herstellen

1. IP-Adresse des Pi herausfinden – z. B. im Router unter verbundene Geräte (Beispiel: `192.168.178.67`).
2. Per SSH verbinden:
   ```bash
   ssh teamrapsberry@192.168.178.67
   ```
3. Beim ersten Verbinden erscheint die **Host-Key-Verifizierung**:
   ```
   The authenticity of host '192.168.178.67' can't be established.
   ED25519 key fingerprint is SHA256:...
   Are you sure you want to continue connecting (yes/no/[fingerprint])?
   ```
   → `yes` eingeben und Enter drücken. Der Fingerprint wird gespeichert und die Frage erscheint danach nicht mehr.
4. Passwort eingeben: **`tuberlin`**

### Tailscale auf dem Pi installieren

Nach erfolgreicher SSH-Verbindung:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Den angezeigten Link im Browser öffnen, um den Pi im Tailscale-Netzwerk zu autorisieren. Danach ist der Pi auch ohne lokales WLAN über Tailscale erreichbar.

> **Hinweis:** Die WLAN-Verbindung wird nur für die Ersteinrichtung benötigt. Sobald Tailscale läuft, funktioniert die Verbindung über `teamrapsberrypizero2-1.taild07c04.ts.net` von überall.
>
> **Tipp:** Die aktuellen Maschinendetails (Hostname, IP-Adressen, Verbindungsstatus) findet man im Tailscale Admin-Panel unter: https://login.tailscale.com/admin/machines

### Verbindung über Tailscale testen

Sobald Tailscale auf dem Pi eingerichtet ist, kann man sich von überall verbinden:

```bash
ssh teamrapsberry@teamrapsberrypizero2-1.taild07c04.ts.net
```

Beim ersten Verbinden über Tailscale erscheint erneut die Host-Key-Verifizierung (da der Hostname neu ist):

```
The authenticity of host 'teamrapsberrypizero2-1.taild07c04.ts.net (100.72.31.30)' can't be established.
ED25519 key fingerprint is SHA256:JD9hMhMuhRpLQ4rJVEZvZSjkdsyMqG0IUWaDvOm+SiM.
This host key is known by the following other names/addresses:
    C:\Users\Lars/.ssh/known_hosts:6: 192.168.178.67
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added 'teamrapsberrypizero2-1.taild07c04.ts.net' (ED25519) to the list of known hosts.
```

→ `yes` eingeben. Danach Passwort eingeben: **`tuberlin`**

Bei erfolgreicher Verbindung erscheint der Pi-Prompt:

```
Linux TeamRaspberryPiZero2 6.12.75+rpt-rpi-v6 #1 Raspbian 1:6.12.75-1+rpt1 (2026-03-11) armv6l

teamrapsberry@TeamRaspberryPiZero2:~ $
```

Die Verbindung steht – der Pi ist jetzt über Tailscale erreichbar, unabhängig vom lokalen Netzwerk.

---

## 1. Benötigte Programme installieren

### Auf dem Windows-PC

| Programm | Download |
|---|---|
| **Visual Studio Code** | https://code.visualstudio.com |
| **Tailscale für Windows** | https://tailscale.com/download/windows |
| **OpenSSH Client** (Windows-Feature) | Einstellungen → Apps → Optionale Features → „OpenSSH-Client" |

> OpenSSH prüfen: PowerShell öffnen und `ssh -V` eingeben. Erscheint eine Versionsnummer, ist es installiert.

### Auf dem Raspberry Pi Zero (einmalig durch Administrator)

- **Tailscale für Linux / Raspberry Pi OS:**
  ```bash
  curl -fsSL https://tailscale.com/install.sh | sh
  sudo tailscale up
  ```
- **OpenSSH Server:**
  ```bash
  sudo apt install openssh-server -y
  sudo systemctl enable ssh
  sudo systemctl start ssh
  ```

---

## 2. VS Code Erweiterung installieren

1. VS Code öffnen.
2. Erweiterungen öffnen: `Strg + Umschalt + X`
3. Suchen: **Remote - SSH**
4. Herausgeber: Microsoft
5. Auf **Install** klicken.

> Optional aber empfohlen: auch **Remote Explorer** (wird meist automatisch mitinstalliert).

---

## 3. Tailscale-Einladung annehmen (in ein bestehendes Netzwerk eingeladen werden)

1. Du erhältst eine Einladungs-E-Mail von Tailscale (von einem Teammitglied verschickt).
2. Link in der E-Mail anklicken → Browser öffnet sich.
3. Mit GitHub, Google oder E-Mail-Konto bei Tailscale anmelden / registrieren.
4. Tailscale für Windows installieren (falls noch nicht geschehen, siehe Schritt 1).
5. Tailscale starten → unten rechts im System-Tray erscheint das Tailscale-Symbol.
6. Auf das Symbol klicken → **Log in** → Browser-Login abschließen.
7. Nach erfolgreichem Login: Tailscale zeigt „Connected" und das Gerät erscheint im gemeinsamen Netzwerk.

> Das Team-Netzwerk nutzt die Domain `taild07c04.ts.net`. Der Pi ist unter `teamrapsberrypizero2-1.taild07c04.ts.net` erreichbar, sobald beide Geräte im selben Tailscale-Netzwerk eingeloggt sind.
>
> Die aktuellen Maschinendetails (Hostname, Tailscale-IP, Verbindungsstatus) findet man unter: https://login.tailscale.com/admin/machines

![Tailscale zeigt teamrapsberrypizero2-1 als verbundenes Gerät](image-1.png)
*Die Tailscale-Oberfläche zeigt das Netzwerk `taild07c04.ts.net`. Der Raspberry Pi (**teamrapsberrypizero2-1**) erscheint mit einem grünen Punkt – er ist aktiv verbunden und erreichbar.*


---

![Remote Explorer zeigt raspberrypi als SSH-Host](image.png)
*Der Remote Explorer (linke Seitenleiste) zeigt unter „SSH (Windsurf)" den eingerichteten Host **raspberrypi**. Ein Klick auf den Pfeil neben `raspberrypi` öffnet die Verbindung direkt. Mit dem **+**-Symbol oben rechts neben „SSH (Windsurf)" kann die `~/.ssh/config` geöffnet und bearbeitet werden, um neue Hosts hinzuzufügen.*

## 4. SSH Config einrichten (`~/.ssh/config`)

Die Datei `C:\Users\Lars\.ssh\config` muss folgenden Eintrag enthalten (ist bereits eingerichtet):

```
Host raspberrypi
    HostName teamrapsberrypizero2-1.taild07c04.ts.net
    User teamrapsberry
```

**Erklärung:**

| Feld | Bedeutung |
|---|---|
| `Host raspberrypi` | Kurzname / Alias, den du später in VS Code auswählst |
| `HostName` | Tailscale-Hostname des Pi (prüfe den aktuellen Namen unter https://login.tailscale.com/admin/machines) |
| `User` | Benutzername auf dem Pi → **`teamrapsberry`** |

> **Passwort:** `tuberlin`

> Datei speichern. Keine Dateiendung (nicht `.txt`).

---

## 5. Verbindung in VS Code herstellen

### Variante A – über den Remote Explorer (einfacher)

1. Remote Explorer in der linken Seitenleiste öffnen (Computer-Symbol mit Verbindungspfeil).
2. Unter „SSH (Windsurf)" erscheint der Host **raspberrypi**.
3. Auf den **Pfeil** (→) neben `raspberrypi` klicken → Verbindung wird hergestellt.
4. Beim ersten Mal: Betriebssystem wählen → **Linux**.
5. Passwort eingeben: **`tuberlin`**
6. VS Code ist jetzt verbunden – unten links erscheint `SSH: raspberrypi`.

### Variante B – über die Befehlspalette

1. `Strg + Umschalt + P` drücken → Befehlspalette öffnet sich.
2. Eintippen: **Remote-SSH: Connect to Host…** → Enter.
3. In der Liste erscheint **raspberrypi** (aus der SSH-Config).
4. Auswählen → neues VS Code-Fenster öffnet sich.
5. Beim ersten Mal: Betriebssystem wählen → **Linux**.
6. Passwort eingeben: **`tuberlin`**
7. VS Code ist jetzt mit dem Raspberry Pi verbunden – unten links erscheint `SSH: raspberrypi`.

### Weitere nützliche Befehle (Strg + Umschalt + P)

| Befehl | Zweck |
|---|---|
| `Remote-SSH: Connect to Host…` | Verbindung herstellen |
| `Remote-SSH: Open Configuration File…` | SSH-Config direkt in VS Code bearbeiten |
| `Remote-SSH: Kill VS Code Server on Host…` | Verbindung auf dem Pi zurücksetzen (bei Problemen) |
| `Remote-SSH: Show Log` | Fehlerdiagnose / Verbindungslog anzeigen |

---

## 6. Verbindung testen (Terminal auf dem Pi)

Nach erfolgreicher Verbindung:

1. In VS Code: `Strg + ö` (oder Terminal → New Terminal).
2. Das Terminal läuft jetzt **auf dem Raspberry Pi**.
3. Testen:
   ```bash
   hostname
   uname -a
   python3 --version
   ```

---

## 7. Troubleshooting

| Problem | Lösung |
|---|---|
| Verbindung schlägt fehl | Tailscale auf beiden Geräten geöffnet und eingeloggt? |
| `ssh: connect to host … port 22: Connection refused` | SSH-Server auf Pi läuft? → `sudo systemctl status ssh` |
| Passwort wird nicht akzeptiert | Benutzername: `teamrapsberry` · Passwort: `tuberlin` |
| VS Code hängt beim Verbinden | `Remote-SSH: Kill VS Code Server on Host…` ausführen, dann erneut verbinden |
| Pi nicht im Tailscale-Netzwerk sichtbar | `sudo tailscale status` auf dem Pi prüfen |


## 8. Auf Dateien des Raspberry Pi zugreifen

Nach erfolgreicher Verbindung kann man Dateien auf dem Pi direkt in VS Code öffnen und bearbeiten:

1. `Strg + Umschalt + P` → **Remote-SSH: Open Folder on SSH Host…** → Enter.
2. Es öffnet sich ein „Open File"-Dialog, der das Dateisystem des Pi zeigt.
3. Der Startpfad ist das Home-Verzeichnis des Nutzers: `/home/teamrapsberry/`
4. Ordner auswählen (z. B. `projects`) → **OK** klicken.
5. VS Code öffnet nun den gewählten Ordner – alle Dateien darin lassen sich direkt bearbeiten.

![Open File Dialog zeigt das Home-Verzeichnis des Pi](image-2.png)
*Der „Open File"-Dialog zeigt das Dateisystem des Raspberry Pi unter `/home/teamrapsberry/`. Sichtbar sind u. a. der Ordner `projects` sowie Konfigurationsdateien wie `.bashrc` und `.profile`. Über **Show Local** kann stattdessen das lokale Windows-Dateisystem geöffnet werden.*

---

## 9. Terminal-Befehle auf dem Pi

Das Terminal in VS Code läuft nach der Verbindung direkt auf dem Raspberry Pi (erkennbar am Prompt `teamrapsberry@TeamRaspberryPiZero2:~$`).

### Navigation & Dateien

| Befehl | Bedeutung |
|---|---|
| `pwd` | Aktuellen Pfad anzeigen |
| `ls` | Inhalt des aktuellen Ordners auflisten |
| `ls -la` | Detaillierte Liste inkl. versteckter Dateien |
| `cd ordnername` | In einen Ordner wechseln |
| `cd ~` | Zurück ins Home-Verzeichnis (`/home/teamrapsberry`) |
| `cd ..` | Eine Ebene nach oben |
| `mkdir ordnername` | Neuen Ordner erstellen |
| `cat dateiname` | Inhalt einer Datei anzeigen |
| `rm dateiname` | Datei löschen |
| `rm -r ordnername` | Ordner mit Inhalt löschen |

### Git – Repository klonen & aktualisieren

```bash
# Git-Version prüfen
git -v

# In Home-Verzeichnis wechseln
cd ~

# Projektordner erstellen und wechseln
mkdir projects
cd projects

# Repository klonen (Beispiel – URL anpassen)
git clone https://github.com/TEAM/PythonAkustik.git

# In das geklonte Repository wechseln
cd PythonAkustik

# Neueste Änderungen holen (Pull)
git pull
```

### Python ausführen

```bash
# Python-Version prüfen
python3 --version

# Skript ausführen
python3 main.py
```

![Terminal auf dem Pi zeigt Git-Befehle und Navigation](image-3.png)
*Das integrierte VS Code Terminal läuft direkt auf dem Raspberry Pi. Hier wird mit `git -v` die Git-Version geprüft, ein `projects`-Ordner erstellt, ein Repository geklont und anschließend in das Projektverzeichnis gewechselt.*