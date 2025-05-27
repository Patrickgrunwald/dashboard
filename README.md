# Dashboard

Ein interaktives Dashboard, das Kalenderereignisse, Wetterdaten und Nachrichten anzeigt.

## Funktionen

* Anzeige von iCloud-Kalenderereignissen
* Aktuelle Wetterdaten und Vorhersage
* Automatische Aktualisierung der Daten

## Installation

1. Repository klonen:
```bash
git clone https://github.com/Patrickgrunwald/dashboard.git
cd dashboard
```

2. Virtuelle Umgebung erstellen und aktivieren:
```bash
python3 -m venv .venv
source .venv/bin/activate  # Für Unix/MacOS
# oder
.venv\Scripts\activate  # Für Windows
```

3. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

4. Umgebungsvariablen konfigurieren:
Erstellen Sie eine `.env`-Datei im Projektverzeichnis mit folgenden Variablen:
```
ICLOUD_EMAIL=ihre.email@example.com
ICLOUD_APP_PASSWORD=ihr-app-passwort
OPENWEATHERMAP_API_KEY=ihr-api-key
```

## Lokale Entwicklung

1. Server starten:
```bash
python3 app.py
```

2. Dashboard im Browser öffnen:
```
http://localhost:8080
```

## Deployment auf Render.com

1. Erstellen Sie ein neues Web Service auf Render.com
2. Verbinden Sie Ihr GitHub-Repository
3. Konfigurieren Sie die Umgebungsvariablen in den Render.com-Einstellungen
4. Deploy wird automatisch durchgeführt

## Technologien

* Python/Flask
* JavaScript
* iCloud CalDAV API
* OpenWeatherMap API 