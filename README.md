# Dashboard

Ein interaktives Dashboard mit Wetter, Kalender und Nachrichten.

## Funktionen

- Aktuelle Wetterdaten und 5-Tage-Vorhersage
- iCloud Kalender Integration
- Aktuelle Nachrichten
- Responsive Design

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

4. Konfiguration:
- Erstellen Sie eine `.env` Datei mit Ihren API-Keys:
```
OPENWEATHERMAP_API_KEY=ihr_api_key
ICLOUD_EMAIL=ihre_email
ICLOUD_APP_PASSWORD=ihr_app_password
```

5. Anwendung starten:
```bash
python app.py
```

Die Anwendung ist dann unter `http://localhost:5001` verfügbar.

## Technologien

- Python/Flask
- OpenWeatherMap API
- iCloud CalDAV
- HTML/CSS/JavaScript 