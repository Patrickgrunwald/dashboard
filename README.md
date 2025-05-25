# Dashboard

Ein modernes Dashboard mit Kalender, Wetter und Nachrichten.

## Features

- Kalender-Integration mit iCloud
- Wettervorhersage
- Aktuelle Nachrichten
- Automatische Aktualisierung alle 5 Sekunden
- Responsive Design

## Installation

1. Repository klonen:
```bash
git clone https://github.com/yourusername/dashboard.git
cd dashboard
```

2. Virtuelle Umgebung erstellen und aktivieren:
```bash
python3 -m venv .venv
source .venv/bin/activate  # Unter Windows: .venv\Scripts\activate
```

3. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

4. App starten:
```bash
python app.py
```

Die App ist dann unter http://localhost:5001 erreichbar.

## Konfiguration

Die iCloud-Kalender-Konfiguration erfolgt in der `app.py` Datei:

```python
ICLOUD_EMAIL = "your-email@example.com"
ICLOUD_APP_PASSWORD = "your-app-password"
ICLOUD_CALDAV_URL = "https://caldav.icloud.com"
```

## Lizenz

MIT 