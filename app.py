from flask import Flask, render_template, jsonify
import requests
import icalendar
import datetime # Keep this top-level import
import pytz
import json
import os
import feedparser
from datetime import datetime, timedelta, date # Specific imports from datetime
import time
import re
import caldav
from caldav.elements import dav, cdav

app = Flask(__name__)

# iCloud Kalender Konfiguration
ICLOUD_EMAIL = os.environ.get("ICLOUD_EMAIL", "patricklevart@me.com") # Besser aus Umgebungsvariablen
ICLOUD_APP_PASSWORD = os.environ.get("ICLOUD_APP_PASSWORD", "xgrw-qssx-ruch-cbcd") # Besser aus Umgebungsvariablen
ICLOUD_CALDAV_URL = "https://caldav.icloud.com"

# OpenWeatherMap Konfiguration
OPENWEATHERMAP_API_KEY = os.environ.get("0a2a868ed80b8df9e7308888e0c387cf") # Hole Key aus Umgebungsvariable
WEATHER_CITY = "Mühlacker,DE" # Stadt für Wetterdaten

# Deutsche Wochentage und Monate für Datumsformatierung
WOCHENTAGE = {
    0: "Mo", # Kürzer für Wetter-Forecast
    1: "Di",
    2: "Mi",
    3: "Do",
    4: "Fr",
    5: "Sa",
    6: "So"
}
WOCHENTAGE_LANG = { # Für Kalender
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

def format_date_german(dt_obj): # dt_obj statt date, um konsistent zu sein
    """Formatiert ein Datum im deutschen Format."""
    return f"{WOCHENTAGE_LANG[dt_obj.weekday()]}, {dt_obj.day}. {MONATE[dt_obj.month]} {dt_obj.year}"

def format_time_german(time_obj): # dt_obj statt time
    """Formatiert eine Uhrzeit im deutschen Format."""
    return f"{time_obj.hour}:{time_obj.minute:02d} Uhr"

def deg_to_cardinal(deg):
    """Konvertiert Windrichtung in Grad zu Himmelsrichtungen."""
    dirs = ["N", "NNO", "NO", "ONO", "O", "OSO", "SO", "SSO", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = round(deg / (360. / len(dirs)))
    return dirs[ix % len(dirs)]

def map_owm_icon_to_simple(owm_icon_code):
    """ Mappt OpenWeatherMap Icon Codes zu einfacheren Bezeichnungen oder FontAwesome Icons.
        Hier eine sehr simple Version. Du kannst das erweitern.
        Siehe: https://openweathermap.org/weather-conditions """
    mapping = {
        "01d": "sunny", "01n": "clear-night", # clear sky
        "02d": "partly-cloudy-day", "02n": "partly-cloudy-night", # few clouds
        "03d": "cloudy", "03n": "cloudy", # scattered clouds
        "04d": "mostly-cloudy", "04n": "mostly-cloudy", # broken clouds, overcast
        "09d": "rain", "09n": "rain", # shower rain
        "10d": "rainy-day", "10n": "rainy-night", # rain
        "11d": "thunderstorm", "11n": "thunderstorm", # thunderstorm
        "13d": "snow", "13n": "snow", # snow
        "50d": "fog", "50n": "fog"  # mist
    }
    return mapping.get(owm_icon_code, "cloudy") # Fallback

def get_calendar_events():
    """Ruft Kalendereinträge von iCloud ab."""
    events = []
    if not ICLOUD_EMAIL or not ICLOUD_APP_PASSWORD:
        print("iCloud-Zugangsdaten nicht konfiguriert. Verwende Beispieldaten für Kalender.")
        return get_example_calendar_events()
        
    try:
        print("Versuche, Verbindung zum iCloud-Kalender herzustellen...")
        client = caldav.DAVClient(
            url=ICLOUD_CALDAV_URL,
            username=ICLOUD_EMAIL,
            password=ICLOUD_APP_PASSWORD
        )
        
        print("Verbindung hergestellt, rufe Hauptkalender ab...")
        principal = client.principal()
        
        print("Hauptkalender abgerufen, suche nach verfügbaren Kalendern...")
        calendars = principal.calendars()
        print(f"Gefundene Kalender: {len(calendars)}")
        
        for cal in calendars:
            print(f"Kalender gefunden: {cal.name}")
        
        now_dt = datetime.now(pytz.utc) # Zeitzonenbewusst für Vergleiche
        start_date_dt = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date_dt = start_date_dt + timedelta(days=30)
        
        calendar_icons = {
            "Familie": "👪",
            "Patrick": "👤",
            "default": "👤"
        }
        
        event_type_icons = {
            "hochzeit": "🎵",
            "musik": "🎵",
            "konzert": "🎵",
            "tiktok": "👤",
            "meeting": "👤",
            "termin": "👤"
        }
        
        processed_event_uids = set() # Um Duplikate von wiederkehrenden Ereignissen zu vermeiden

        for calendar in calendars:
            calendar_name = calendar.name.lower() if calendar.name else ""
            print(f"Prüfe Kalender: {calendar_name}")
            
            relevant_calendars = ["familie", "patrick", "icloud"] # Schlüsselwörter für relevante Kalender
            if any(keyword in calendar_name for keyword in relevant_calendars) or not calendar_name: # Auch Kalender ohne Namen prüfen (manchmal der Hauptkalender)

                print(f"Verwende Kalender: {calendar.name or 'Unbenannter Kalender'}")
                
                default_icon = calendar_icons["default"]
                if "familie" in calendar_name:
                    default_icon = calendar_icons["Familie"]
                elif "patrick" in calendar_name:
                    default_icon = calendar_icons["Patrick"]
                
                try:
                    print(f"Suche Ereignisse von {start_date_dt.date()} bis {end_date_dt.date()}")
                    # Wichtig: caldav sucht mit datetime-Objekten
                    calendar_events_raw = calendar.date_search(start=start_date_dt, end=end_date_dt, expand=True) # expand=True für wiederkehrende Termine
                    print(f"Gefundene Ereignisse in '{calendar.name or 'Unbenannter Kalender'}': {len(calendar_events_raw)}")
                    
                    for event_raw in calendar_events_raw:
                        try:
                            event_data = event_raw.data
                            ical = icalendar.Calendar.from_ical(event_data)
                            
                            for component in ical.walk():
                                if component.name == "VEVENT":
                                    uid = str(component.get('uid'))
                                    # Wenn eine Instanz eines wiederkehrenden Ereignisses, kann die UID gleich sein,
                                    # aber die RECURRENCE-ID unterscheidet sie. Wir fügen beide hinzu.
                                    event_instance_id = uid
                                    if component.get('recurrence-id'):
                                        event_instance_id += str(component.get('recurrence-id').dt)

                                    if event_instance_id in processed_event_uids:
                                        continue # Bereits verarbeitete Instanz überspringen
                                    processed_event_uids.add(event_instance_id)

                                    summary = str(component.get('summary', 'Unbekanntes Ereignis'))
                                    dtstart_obj = component.get('dtstart').dt
                                    
                                    # Normalisiere dtstart zu einem zeitzonenbewussten datetime-Objekt in UTC
                                    if isinstance(dtstart_obj, date) and not isinstance(dtstart_obj, datetime): # Ganztägig
                                        dtstart_utc = datetime(dtstart_obj.year, dtstart_obj.month, dtstart_obj.day, 0, 0, 0, tzinfo=pytz.utc)
                                        all_day = True
                                    elif isinstance(dtstart_obj, datetime):
                                        if dtstart_obj.tzinfo is None:
                                            dtstart_utc = pytz.utc.localize(dtstart_obj) # Annahme: naive Zeiten sind UTC oder lokale Zeit des Servers
                                        else:
                                            dtstart_utc = dtstart_obj.astimezone(pytz.utc)
                                        all_day = False
                                        # Überprüfen, ob es sich um ein ganztägiges Ereignis handelt, das als Mitternacht UTC dargestellt wird
                                        if dtstart_utc.hour == 0 and dtstart_utc.minute == 0 and dtstart_utc.second == 0 and component.get('X-APPLE-ALL-DAY') == 'TRUE':
                                            all_day = True
                                    else:
                                        print(f"Unbekannter Typ für dtstart: {type(dtstart_obj)} für Event {summary}")
                                        continue
                                    
                                    # In lokale Zeitzone umwandeln für Anzeige
                                    dtstart_local = dtstart_utc.astimezone() # Lokale Systemzeitzone

                                    # Datums- und Zeitanzeige Logik
                                    today_local = datetime.now().date()
                                    event_date_local = dtstart_local.date()

                                    time_display = ""
                                    if all_day:
                                        if event_date_local == today_local:
                                            time_display = "Heute (Ganztägig)"
                                        elif event_date_local == today_local + timedelta(days=1):
                                            time_display = "Morgen (Ganztägig)"
                                        else:
                                            time_display = f"{WOCHENTAGE_LANG[event_date_local.weekday()].split(',')[0]} {event_date_local.day}."
                                            if event_date_local.month != today_local.month:
                                                time_display = f"{MONATE[event_date_local.month]} {event_date_local.day}."
                                    else: # Nicht ganztägig
                                        event_time_str = dtstart_local.strftime("%H:%M")
                                        if event_date_local == today_local:
                                            time_display = f"Heute um {event_time_str} Uhr"
                                        elif event_date_local == today_local + timedelta(days=1):
                                            time_display = f"Morgen um {event_time_str} Uhr"
                                        else:
                                            day_name = WOCHENTAGE_LANG[event_date_local.weekday()].split(',')[0]
                                            if event_date_local.month == today_local.month:
                                                 time_display = f"{day_name} {event_date_local.day}. {event_time_str} Uhr"
                                            else:
                                                 time_display = f"{MONATE[event_date_local.month]} {event_date_local.day}. {event_time_str} Uhr"

                                    icon = default_icon
                                    for keyword, specific_icon in event_type_icons.items():
                                        if keyword in summary.lower():
                                            icon = specific_icon
                                            break
                                    
                                    events.append({
                                        "title": summary,
                                        "time": time_display,
                                        "timestamp": dtstart_utc.timestamp(), # Für Sortierung
                                        "icon": icon,
                                        "all_day": all_day
                                    })
                        except Exception as e:
                            print(f"Fehler beim Verarbeiten eines Ereignisses: {e} (Event Raw: {event_raw.url})")
                except Exception as e:
                    print(f"Fehler beim Abrufen von Ereignissen aus Kalender {calendar.name or 'Unbenannter Kalender'}: {e}")
        
        # Ereignisse nach Zeitstempel sortieren
        events.sort(key=lambda x: (x["timestamp"])) # Erst nach Zeit, dann ganztägige zuerst, wenn Zeit gleich ist
        
        print(f"Insgesamt gefundene und verarbeitete Ereignisse: {len(events)}")
        
        if not events:
            print("Keine Kalenderereignisse gefunden, verwende Beispieldaten")
            return get_example_calendar_events() # Rückgabe, um weitere Verarbeitung zu stoppen
            
    except Exception as e:
        print(f"Kritischer Fehler beim Abrufen der Kalendereinträge: {e}")
        return get_example_calendar_events() # Rückgabe
    
    return events

def get_example_calendar_events():
    """Liefert Beispiel-Kalenderdaten zurück."""
    return [
        {"title": "Meeting mit Team", "time": "Heute um 14:30 Uhr", "timestamp": datetime.now().replace(hour=14, minute=30).timestamp(), "icon": "👤", "all_day": False},
        {"title": "Geburtstag Mama", "time": "Morgen (Ganztägig)", "timestamp": (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0).timestamp(), "icon": "👪", "all_day": True},
        {"title": "Konzertbesuch", "time": f"{MONATE[(datetime.now() + timedelta(days=5)).month]} {(datetime.now() + timedelta(days=5)).day}. 20:00 Uhr", "timestamp": (datetime.now() + timedelta(days=5)).replace(hour=20, minute=0).timestamp(), "icon": "🎵", "all_day": False},
    ]

def get_weather_data():
    """Ruft Wetterdaten für die konfigurierte Stadt ab."""
    if not OPENWEATHERMAP_API_KEY:
        print("OpenWeatherMap API Key nicht konfiguriert. Verwende Beispiel-Wetterdaten.")
        return get_example_weather_data()

    weather_data_result = {
        "current": {},
        "forecast": []
    }

    try:
        # Aktuelles Wetter
        url_current = f"https://api.openweathermap.org/data/2.5/weather?q={WEATHER_CITY}&units=metric&lang=de&appid={OPENWEATHERMAP_API_KEY}"
        response_current = requests.get(url_current)
        response_current.raise_for_status() # Löst HTTPError für schlechte Antworten (4XX oder 5XX)
        data_current = response_current.json()

        weather_data_result["current"] = {
            "temperature": round(data_current['main']['temp']),
            "feels_like": round(data_current['main']['feels_like']),
            "wind_speed": round(data_current['wind']['speed'] * 3.6), # m/s zu km/h
            "wind_direction": deg_to_cardinal(data_current['wind']['deg']),
            "description": data_current['weather'][0]['description'].capitalize(),
            "icon": map_owm_icon_to_simple(data_current['weather'][0]['icon']),
            "humidity": data_current['main']['humidity'], # Luftfeuchtigkeit
            "city": data_current['name']
        }
        
        # 5-Tage-Vorhersage (enthält Daten alle 3 Stunden)
        # Wir müssen die Tages-Min/Max-Temperaturen aggregieren.
        # Besser: One Call API (benötigt Lat/Lon, aber liefert direkt tägliche Vorhersage)
        # Für Einfachheit hier erstmal mit /forecast, dann Aggregation:

        # Schritt 1: Lat/Lon für OneCall API abrufen (nur einmal, oder wenn CITY sich ändert)
        # Dieser Teil könnte ausgelagert und gecacht werden, falls die Stadt sich nicht oft ändert
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={WEATHER_CITY}&limit=1&appid={OPENWEATHERMAP_API_KEY}"
        geo_resp = requests.get(geo_url)
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()
        if not geo_data:
            raise ValueError(f"Stadt {WEATHER_CITY} nicht gefunden.")
        
        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']

        # Schritt 2: OneCall API für tägliche Vorhersage
        url_onecall = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=current,minutely,hourly,alerts&units=metric&lang=de&appid={OPENWEATHERMAP_API_KEY}"
        response_onecall = requests.get(url_onecall)
        response_onecall.raise_for_status()
        data_onecall = response_onecall.json()

        today_weekday = datetime.now().weekday()

        for i, daily_forecast in enumerate(data_onecall['daily'][:5]): # Nächste 5 Tage
            day_dt = datetime.fromtimestamp(daily_forecast['dt'])
            day_name = ""
            if day_dt.date() == date.today():
                day_name = "Heute"
            elif day_dt.date() == date.today() + timedelta(days=1):
                day_name = "Morgen"
            else:
                day_name = WOCHENTAGE[day_dt.weekday()] # Verwendet die kurzen Wochentagsnamen

            weather_data_result["forecast"].append({
                "day": day_name,
                "temp_day": round(daily_forecast['temp']['day']),
                "temp_night": round(daily_forecast['temp']['night']),
                "icon": map_owm_icon_to_simple(daily_forecast['weather'][0]['icon']),
                "description": daily_forecast['weather'][0]['description'].capitalize()
            })
        
        return weather_data_result

    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Abrufen der Wetterdaten (Request Error): {e}")
        return get_example_weather_data()
    except (KeyError, IndexError, ValueError) as e:
        print(f"Fehler beim Verarbeiten der Wetterdaten (Data Error): {e}")
        return get_example_weather_data()
    except Exception as e:
        print(f"Allgemeiner Fehler beim Abrufen der Wetterdaten: {e}")
        return get_example_weather_data()

def get_example_weather_data():
    """Liefert Beispiel-Wetterdaten zurück."""
    return {
        "current": {
            "temperature": 17,
            "feels_like": 17,
            "wind_speed": 7, # km/h
            "wind_direction": "W",
            "description": "Leicht bewölkt",
            "icon": "partly-cloudy-day",
            "humidity": 60,
            "city": "Musterstadt"
        },
        "forecast": [
            {"day": "Heute", "temp_day": 17, "temp_night": 4, "icon": "partly-cloudy-day", "description": "Sonnig"},
            {"day": "Morgen", "temp_day": 17, "temp_night": 10, "icon": "cloudy", "description": "Bewölkt"},
            {"day": "Mi", "temp_day": 19, "temp_night": 11, "icon": "rain", "description": "Regen"},
            {"day": "Do", "temp_day": 16, "temp_night": 7, "icon": "sunny", "description": "Sonnig"},
            {"day": "Fr", "temp_day": 23, "temp_night": 10, "icon": "partly-cloudy-day", "description": "Leicht bewölkt"}
        ]
    }

def get_news_data():
    """Ruft aktuelle Nachrichten aus Deutschland ab. Diese Funktion ist bereits dynamisch."""
    try:
        news_sources = [
            "https://www.tagesschau.de/xml/rss2/",
            "https://rss.sueddeutsche.de/rss/Topthemen",
            "https://www.spiegel.de/schlagzeilen/tops/index.rss",
            "https://www.zeit.de/news/index.rss",
            # "https://www.faz.net/rss/aktuell/" # FAZ blockiert oft direkte Abfragen ohne User-Agent
        ]
        
        headers = { # Einige Feeds benötigen einen User-Agent
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        for source_url in news_sources:
            try:
                print(f"Versuche Nachrichten von: {source_url}")
                # feedparser kann den User-Agent nicht direkt übergeben, daher requests nutzen, wenn feedparser Probleme hat
                # Aber meistens geht es auch so. Für robustere Lösung:
                # response = requests.get(source_url, headers=headers, timeout=10)
                # response.raise_for_status()
                # feed = feedparser.parse(response.content)
                feed = feedparser.parse(source_url, agent=headers.get('User-Agent')) # agent-Parameter nutzen

                if feed.bozo: # Prüfen, ob beim Parsen ein Fehler aufgetreten ist
                    print(f"Bozo-Exception beim Parsen von {source_url}: {feed.bozo_exception}")
                    # Manchmal sind die Daten trotzdem da
                
                if feed.entries and len(feed.entries) > 0:
                    entry = feed.entries[0]
                    
                    source_name = feed.feed.get("title", "Unbekannte Quelle")
                    published_time_parsed = None
                    if 'published_parsed' in entry and entry.published_parsed:
                        published_time_parsed = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    elif 'updated_parsed' in entry and entry.updated_parsed:
                        published_time_parsed = datetime.fromtimestamp(time.mktime(entry.updated_parsed))

                    time_str = "unbekannte Zeit"
                    if published_time_parsed:
                        now = datetime.now(pytz.utc) # Zeitzonenbewusst
                        # Mache published_time_parsed zeitzonenbewusst (nehme UTC an, wenn nicht vorhanden)
                        if published_time_parsed.tzinfo is None:
                            published_time_parsed = pytz.utc.localize(published_time_parsed)
                        else:
                            published_time_parsed = published_time_parsed.astimezone(pytz.utc)

                        diff = now - published_time_parsed
                        
                        if diff.days > 1:
                            time_str = f"vor {diff.days} Tagen"
                        elif diff.days == 1:
                            time_str = "gestern"
                        elif diff.seconds // 3600 > 0:
                            hours = diff.seconds // 3600
                            time_str = f"vor {hours} Std." if hours > 1 else "vor 1 Std."
                        elif diff.seconds // 60 > 0:
                            minutes = diff.seconds // 60
                            time_str = f"vor {minutes} Min." if minutes > 1 else "vor 1 Min."
                        else:
                            time_str = "gerade eben"
                    
                    title = entry.get('title', "Kein Titel")
                    
                    content = entry.get('summary', entry.get('description', ''))
                    content = re.sub(r'<.*?>', '', content) # HTML-Tags entfernen
                    content = content.strip()

                    # Kürze den Inhalt, falls zu lang
                    max_len = 150
                    if len(content) > max_len:
                        content = content[:max_len].rsplit(' ', 1)[0] + "..."
                    
                    if not content and title: # Wenn kein Inhalt, aber Titel, nimm Titel als Fallback
                         content = "Weitere Informationen im Artikel."

                    print(f"Nachricht gefunden: {title[:30]}... von {source_name}")
                    return {
                        "source": f"{source_name}, {time_str}",
                        "headline": title,
                        "content": content
                    }
            except requests.exceptions.RequestException as e:
                print(f"Fehler beim Abrufen von {source_url} (Request Error): {e}")
            except Exception as e:
                print(f"Allgemeiner Fehler beim Verarbeiten von {source_url}: {e}")
                continue
        
        print("Keine Nachrichten von RSS-Feeds erhalten. Verwende Beispiel-Nachrichten.")
        return get_example_news_data()

    except Exception as e:
        print(f"Kritischer Fehler beim Abrufen der Nachrichten: {e}")
        return get_example_news_data()

def get_example_news_data():
    return {
        "source": "Süddeutsche Zeitung, vor einer Stunde",
        "headline": "Beispiel-Nachricht: Söder grillt – Peta protestiert",
        "content": "Dies ist ein Beispieltext, da keine echten Nachrichten abgerufen werden konnten. Markus Söder, Wurstfan, lässt sich das Grillen nicht entgehen."
    }

@app.route('/')
def index():
    """Hauptroute für das Dashboard."""
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """API-Endpunkt, der alle Daten für das Dashboard bereitstellt."""
    now = datetime.now() # Lokale Zeit des Servers
    
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
    # Für lokale Entwicklung kann man den Key auch direkt setzen, falls die Umgebungsvariable nicht geht
    # if not OPENWEATHERMAP_API_KEY:
    #    OPENWEATHERMAP_API_KEY = "DEIN_API_KEY_HIER_NUR_FUER_TESTS"
    
    if not OPENWEATHERMAP_API_KEY:
        print("WARNUNG: OPENWEATHERMAP_API_KEY ist nicht gesetzt. Wetterdaten sind Beispiele.")
    if not ICLOUD_EMAIL or not ICLOUD_APP_PASSWORD:
        print("WARNUNG: ICLOUD_EMAIL oder ICLOUD_APP_PASSWORD nicht gesetzt. Kalenderdaten sind Beispiele.")

    app.run(host='0.0.0.0', port=5001, debug=True)
