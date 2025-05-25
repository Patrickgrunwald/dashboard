# Dashboard

Ein interaktives Dashboard, das Kalenderereignisse, Wetterdaten und Nachrichten anzeigt.

## Funktionen

- Anzeige von iCloud-Kalenderereignissen
- Aktuelle Wetterdaten und Vorhersage
- Aktuelle Nachrichten
- Automatische Aktualisierung der Daten

## Installation

1. Repository klonen:
```bash
git clone https://github.com/IHR_USERNAME/dashboard.git
cd dashboard
```

2. Virtuelle Umgebung erstellen und aktivieren:
```bash
python -m venv .venv
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

## Verwendung

1. Server starten:
```bash
python app.py
```

2. Dashboard im Browser öffnen:
```
http://localhost:5001
```

## Technologien

- Python/Flask
- JavaScript
- iCloud CalDAV API
- OpenWeatherMap API
- RSS Feeds für Nachrichten 