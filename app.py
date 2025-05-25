from flask import Flask, render_template, jsonify
import requests
import icalendar
import datetime
import pytz
import json
import os
import feedparser
from datetime import datetime, timedelta, date
import time
import re
import caldav
from caldav.elements import dav, cdav
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

app = Flask(__name__)

# iCloud Kalender Konfiguration
ICLOUD_EMAIL = os.getenv('ICLOUD_EMAIL', "patricklevart@me.com")
ICLOUD_APP_PASSWORD = os.getenv('ICLOUD_APP_PASSWORD', "xgrw-qssx-ruch-cbcd")
ICLOUD_CALDAV_URL = "https://caldav.icloud.com"

# OpenWeatherMap API Konfiguration
OPENWEATHERMAP_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY', "0a2a868ed80b8df9e7308888e0c387cf")

# Deutsche Wochentage und Monate für Datumsformatierung
WOCHENTAGE = {
    0: "Montag",
    1: "Dienstag",
    2: "Mittwoch",
    3: "Donnerstag",
    4: "Freitag",
    5: "Samstag",
    6: "Sonntag"
}

MONATE = {
    1: "Januar",
    2: "Februar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember"
}

def format_date_german(date):
    """Formatiert ein Datum im deutschen Format."""
    return f"{WOCHENTAGE[date.weekday()]}, {date.day}. {MONATE[date.month]} {date.year}"

def format_time_german(time):
    """Formatiert eine Uhrzeit im deutschen Format."""
    return f"{time.hour}:{time.minute:02d} Uhr"

def get_calendar_events():
    """Ruft Kalendereinträge von iCloud ab."""
    events = []
    
    try:
        print("Versuche, Verbindung zum iCloud-Kalender herzustellen...")
        # Verbindung zum iCloud CalDAV-Server herstellen
        client = caldav.DAVClient(
            url=ICLOUD_CALDAV_URL,
            username=ICLOUD_EMAIL,
            password=ICLOUD_APP_PASSWORD
        )
        
        print("Verbindung hergestellt, rufe Hauptkalender ab...")
        # Hauptkalender des Benutzers abrufen
        principal = client.principal()
        
        print("Hauptkalender abgerufen, suche nach verfügbaren Kalendern...")
        # Alle verfügbaren Kalender abrufen
        calendars = principal.calendars()
        print(f"Gefundene Kalender: {len(calendars)}")
        
        # Kalendernamen ausgeben
        for cal in calendars:
            print(f"Kalender gefunden: {cal.name}")
        
        # Aktuelle Zeit und Zeitraum für Ereignisse festlegen
        now = datetime.now()
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=30)  # Ereignisse für die nächsten 30 Tage
        
        # Kalender-Icons basierend auf Kalendertyp
        calendar_icons = {
            "Familie": "👪",
            "Patrick": "👤",
            "default": "👤"
        }
        
        # Spezielle Icons für bestimmte Ereignistypen
        event_type_icons = {
            "hochzeit": "🎵",
            "musik": "🎵",
            "konzert": "🎵",
            "tiktok": "👤",
            "meeting": "👤",
            "termin": "👤"
        }
        
        # Durch alle Kalender iterieren und nach 'Familie' und 'Patrick' filtern
        for calendar in calendars:
            calendar_name = calendar.name.lower() if calendar.name else ""
            
            print(f"Prüfe Kalender: {calendar_name}")
            
            # Nur die gewünschten Kalender verwenden
            if "familie" in calendar_name or "patrick" in calendar_name or "icloud" in calendar_name:
                print(f"Verwende Kalender: {calendar_name}")
                
                # Icon basierend auf Kalendername festlegen
                if "familie" in calendar_name:
                    default_icon = calendar_icons["Familie"]
                elif "patrick" in calendar_name:
                    default_icon = calendar_icons["Patrick"]
                else:
                    default_icon = calendar_icons["default"]
                
                try:
                    # Ereignisse im Zeitraum abrufen
                    print(f"Suche Ereignisse von {start_date} bis {end_date}")
                    calendar_events = calendar.date_search(start=start_date, end=end_date)
                    print(f"Gefundene Ereignisse: {len(calendar_events)}")
                    
                    for event in calendar_events:
                        try:
                            # Ereignisdaten parsen
                            event_data = event.data
                            ical = icalendar.Calendar.from_ical(event_data)
                            
                            for component in ical.walk():
                                if component.name == "VEVENT":
                                    # Titel des Ereignisses
                                    summary = str(component.get('summary', 'Unbekanntes Ereignis'))
                                    print(f"Ereignis gefunden: {summary}")
                                    
                                    # Startzeit des Ereignisses
                                    dtstart = component.get('dtstart').dt
                                    
                                    # Prüfen, ob es sich um ein ganztägiges Ereignis handelt
                                    all_day = isinstance(dtstart, date) and not isinstance(dtstart, datetime)
                                    
                                    # Wenn es ein datetime-Objekt ist, sicherstellen, dass es ein Zeitzonenobjekt hat
                                    if isinstance(dtstart, datetime) and dtstart.tzinfo is None:
                                        dtstart = dtstart.replace(tzinfo=pytz.UTC)
                                    
                                    # Für ganztägige Ereignisse oder Ereignisse in der Zukunft
                                    if all_day or (isinstance(dtstart, datetime) and dtstart.date() > now.date()):
                                        # Datum formatieren
                                        event_date = dtstart if isinstance(dtstart, date) else dtstart.date()
                                        if event_date.month == now.month:
                                            date_display = f"{MONATE[event_date.month]} {event_date.day}."
                                        else:
                                            date_display = f"{MONATE[event_date.month]} {event_date.day}."
                                    else:
                                        # Zeit formatieren für Ereignisse am selben Tag
                                        time_str = dtstart.strftime("%H:%M")
                                        date_display = f"{WOCHENTAGE[dtstart.weekday()]} um {time_str} Uhr"
                                    
                                    # Icon basierend auf Ereignistyp oder Kalendername festlegen
                                    icon = default_icon
                                    for keyword, specific_icon in event_type_icons.items():
                                        if keyword in summary.lower():
                                            icon = specific_icon
                                            break
                                    
                                    # Ereignis zum Array hinzufügen
                                    events.append({
                                        "title": summary,
                                        "time": f"{event_date.strftime('%d.%m.%Y')} {date_display}",
                                        "icon": icon
                                    })
                        except Exception as e:
                            print(f"Fehler beim Verarbeiten eines Ereignisses: {e}")
                except Exception as e:
                    print(f"Fehler beim Abrufen von Ereignissen aus Kalender {calendar_name}: {e}")
        
        # Ereignisse nach Datum sortieren
        events.sort(key=lambda x: x["time"], reverse=True)
        
        print(f"Insgesamt gefundene Ereignisse: {len(events)}")
        
        # Wenn keine Ereignisse gefunden wurden, Beispieldaten zurückgeben
        if not events:
            print("Keine Kalenderereignisse gefunden, verwende Beispieldaten")
            events = get_example_calendar_events()
            
    except Exception as e:
        print(f"Fehler beim Abrufen der Kalendereinträge: {e}")
        # Fallback-Daten bei Fehler
        events = get_example_calendar_events()
    
    return events

def get_example_calendar_events():
    """Liefert Beispiel-Kalenderdaten zurück."""
    current_date = datetime.now()
    
    example_events = [
        {
            "title": "Keaz Start",
            "time": f"{WOCHENTAGE[0]} um 14:30 Uhr",
            "icon": "👤"
        },
        {
            "title": "Harry Durst",
            "time": f"{WOCHENTAGE[0]} um 17:00 Uhr",
            "icon": "👤"
        },
        {
            "title": "Inolab Pforzheim 10:30",
            "time": "Juni 2.",
            "icon": "👤"
        },
        {
            "title": "Mama hab dich lieb",
            "time": "Juni 2.",
            "icon": "👪"
        },
        {
            "title": "Velly Blue meets Adstrong",
            "time": "Juni 3.",
            "icon": "👤"
        },
        {
            "title": "Hochzeit Silke Follner",
            "time": "Juni 6.",
            "icon": "🎵"
        },
        {
            "title": "TikTok at Cannes 2025",
            "time": "Juni 16.",
            "icon": "👤"
        }
    ]
    
    return example_events

def get_weather_data():
    """Ruft Wetterdaten für Mühlacker ab."""
    try:
        # OpenWeatherMap API für Mühlacker
        url = f"https://api.openweathermap.org/data/2.5/forecast?q=Mühlacker,de&units=metric&lang=de&appid={OPENWEATHERMAP_API_KEY}"
        print(f"Rufe Wetterdaten ab von: {url}")
        
        # Timeout nach 5 Sekunden
        response = requests.get(url, timeout=5)
        print(f"API Antwort Status: {response.status_code}")
        print(f"API Antwort: {response.text[:200]}...")  # Zeige die ersten 200 Zeichen der Antwort
        
        data = response.json()
        
        if response.status_code != 200:
            error_msg = data.get('message', 'Unbekannter Fehler')
            print(f"API Fehler: {error_msg}")
            raise Exception(f"API Fehler: {error_msg}")
        
        # Aktuelle Zeit mit Zeitzone
        tz = pytz.timezone('Europe/Berlin')
        current_time = datetime.now(tz).strftime("%H:%M")
        print(f"Aktuelle Zeit: {current_time}")
        
        # Aktuelle Wetterdaten
        current = data['list'][0]
        print(f"Aktuelle Wetterdaten: {current}")
        
        weather_data = {
            "current": {
                "temperature": round(current['main']['temp']),
                "feels_like": round(current['main']['feels_like']),
                "wind_speed": round(current['wind']['speed']),
                "wind_direction": get_wind_direction(current['wind']['deg']),
                "time": current_time,
                "icon": get_weather_icon(current['weather'][0]['main'].lower())
            },
            "forecast": []
        }
        
        print(f"Formatiertes Wetter: {weather_data['current']}")
        
        # Wettervorhersage für die nächsten 5 Tage
        current_date = datetime.now(tz).date()
        processed_dates = set()
        
        # Sortiere die Vorhersagen nach Datum
        sorted_forecasts = sorted(data['list'], key=lambda x: x['dt'])
        
        for item in sorted_forecasts:
            forecast_date = datetime.fromtimestamp(item['dt'], tz).date()
            
            # Nur einen Eintrag pro Tag und nur für die nächsten 5 Tage
            if forecast_date > current_date and forecast_date not in processed_dates and len(processed_dates) < 5:
                processed_dates.add(forecast_date)
                
                # Finde die höchste und niedrigste Temperatur für diesen Tag
                day_temps = [temp['main']['temp'] for temp in data['list'] 
                           if datetime.fromtimestamp(temp['dt'], tz).date() == forecast_date]
                
                # Bestimme das dominante Wetter für den Tag
                day_weather = [temp['weather'][0]['main'].lower() for temp in data['list']
                             if datetime.fromtimestamp(temp['dt'], tz).date() == forecast_date]
                dominant_weather = max(set(day_weather), key=day_weather.count)
                
                forecast_entry = {
                    "day": get_day_name(item['dt']),
                    "temp_day": round(max(day_temps)),
                    "temp_night": round(min(day_temps)),
                    "icon": get_weather_icon(dominant_weather)
                }
                weather_data["forecast"].append(forecast_entry)
                print(f"Vorhersage für {forecast_date}: {forecast_entry}")
        
        return weather_data
    except requests.exceptions.Timeout:
        print("Timeout beim Abrufen der Wetterdaten")
        return get_fallback_weather_data()
    except requests.exceptions.RequestException as e:
        print(f"Netzwerkfehler beim Abrufen der Wetterdaten: {e}")
        return get_fallback_weather_data()
    except Exception as e:
        print(f"Unerwarteter Fehler beim Abrufen der Wetterdaten: {e}")
        return get_fallback_weather_data()

def get_fallback_weather_data():
    """Liefert Fallback-Wetterdaten bei Fehlern."""
    tz = pytz.timezone('Europe/Berlin')
    current_time = datetime.now(tz).strftime("%H:%M")
    current_date = datetime.now(tz).date()
    
    # Realistische Beispieldaten für Mühlacker
    weather_data = {
        "current": {
            "temperature": 22,
            "feels_like": 23,
            "wind_speed": 12,
            "wind_direction": "SW",
            "time": current_time,
            "icon": "sunny"
        },
        "forecast": []
    }
    
    # Wettervorhersage für die nächsten 5 Tage
    for i in range(5):
        forecast_date = current_date + timedelta(days=i+1)
        day_name = get_day_name(int(datetime.combine(forecast_date, datetime.min.time()).timestamp()))
        
        # Realistische Temperaturwerte basierend auf der Jahreszeit
        temp_day = 20 + i  # Steigende Temperaturen
        temp_night = 10 + i  # Steigende Nachttemperaturen
        
        # Abwechselnde Wetterbedingungen
        icons = ['sunny', 'cloudy', 'rainy', 'sunny', 'cloudy']
        
        forecast_entry = {
            "day": day_name,
            "temp_day": temp_day,
            "temp_night": temp_night,
            "icon": icons[i]
        }
        weather_data["forecast"].append(forecast_entry)
    
    return weather_data

def get_wind_direction(degrees):
    """Konvertiert Windrichtung in Grad zu Himmelsrichtung."""
    directions = ['N', 'NO', 'O', 'SO', 'S', 'SW', 'W', 'NW']
    index = round(degrees / 45) % 8
    return directions[index]

def get_weather_icon(weather_main):
    """Konvertiert Wetterbeschreibung in Icon-Typ."""
    icon_map = {
        'clear': 'sunny',
        'clouds': 'cloudy',
        'rain': 'rainy',
        'drizzle': 'rainy',
        'thunderstorm': 'rainy',
        'snow': 'rainy',
        'mist': 'cloudy',
        'fog': 'cloudy'
    }
    return icon_map.get(weather_main, 'cloudy')

def get_day_name(timestamp):
    """Konvertiert Unix-Timestamp in Wochentag."""
    days = ['Heute', 'Morgen', 'Mo.', 'Di.', 'Mi.', 'Do.', 'Fr.', 'Sa.', 'So.']
    date = datetime.fromtimestamp(timestamp)
    if date.date() == datetime.now().date():
        return 'Heute'
    elif date.date() == datetime.now().date() + timedelta(days=1):
        return 'Morgen'
    else:
        return days[date.weekday() + 2]  # +2 wegen 'Heute' und 'Morgen'

def get_news_data():
    """Ruft aktuelle Nachrichten aus Deutschland ab."""
    try:
        # Deutsche Nachrichtenquellen
        news_sources = [
            "https://www.tagesschau.de/xml/rss2/",
            "https://rss.sueddeutsche.de/rss/Topthemen",
            "https://www.spiegel.de/schlagzeilen/tops/index.rss"
        ]
        
        # Versuche, Nachrichten von einer der Quellen zu erhalten
        for source_url in news_sources:
            try:
                feed = feedparser.parse(source_url)
                if feed.entries and len(feed.entries) > 0:
                    entry = feed.entries[0]  # Nehme den neuesten Eintrag
                    
                    # Quelle und Zeitstempel
                    source_name = feed.feed.title
                    published_time = entry.get('published', '')
                    
                    # Versuche, einen relativen Zeitstempel zu erstellen (z.B. "vor einer Stunde")
                    time_str = "vor einer Stunde"  # Fallback
                    if published_time:
                        try:
                            # Versuche, den Zeitstempel zu parsen
                            pub_time = datetime.strptime(published_time, "%a, %d %b %Y %H:%M:%S %z")
                            now = datetime.now(pub_time.tzinfo)
                            diff = now - pub_time
                            
                            if diff.days > 0:
                                time_str = f"vor {diff.days} Tagen"
                            elif diff.seconds // 3600 > 0:
                                hours = diff.seconds // 3600
                                time_str = f"vor {hours} Stunde{'n' if hours > 1 else ''}"
                            elif diff.seconds // 60 > 0:
                                minutes = diff.seconds // 60
                                time_str = f"vor {minutes} Minute{'n' if minutes > 1 else ''}"
                            else:
                                time_str = "gerade eben"
                        except:
                            pass
                    
                    # Titel und Inhalt
                    title = entry.title
                    
                    # Inhalt extrahieren und HTML-Tags entfernen
                    content = entry.get('description', '')
                    content = re.sub(r'<.*?>', '', content)  # HTML-Tags entfernen
                    
                    # Wenn der Inhalt zu kurz ist, versuche andere Felder
                    if len(content) < 50:
                        content = entry.get('summary', content)
                        content = re.sub(r'<.*?>', '', content)  # HTML-Tags entfernen
                    
                    # Wenn immer noch zu kurz, verwende einen Standardtext
                    if len(content) < 50:
                        content = "Weitere Informationen sind auf der Website der Nachrichtenquelle verfügbar."
                    
                    return {
                        "source": f"{source_name}, {time_str}",
                        "headline": title,
                        "content": content
                    }
            except Exception as e:
                print(f"Fehler beim Abrufen von {source_url}: {e}")
                continue
        
        # Fallback, wenn keine Quelle funktioniert
        return {
            "source": "Süddeutsche Zeitung, vor einer Stunde",
            "headline": "Viechtach: Söder grillt – Peta protestiert",
            "content": "Markus Söder, eingefleischter Wurstfan, lässt sich das Schweinegrillen in Viechtach nicht entgehen. Während auf dem Rost die Tiere brutzeln, gehen die Protestschilder hoch."
        }
    except Exception as e:
        print(f"Fehler beim Abrufen der Nachrichten: {e}")
        return {
            "source": "Nachrichtendienst nicht verfügbar",
            "headline": "Keine aktuellen Nachrichten",
            "content": "Derzeit können keine Nachrichten abgerufen werden. Bitte versuchen Sie es später erneut."
        }

@app.route('/')
def index():
    """Hauptroute für das Dashboard."""
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """API-Endpunkt, der alle Daten für das Dashboard bereitstellt."""
    now = datetime.now()
    
    data = {
        "datetime": {
            "date": format_date_german(now),
            "time": now.strftime("%H:%M"),
            "seconds": now.strftime("%S")
        },
        "calendar": get_calendar_events(),
        "weather": get_weather_data(),
        "news": get_news_data()
    }
    
    return jsonify(data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
