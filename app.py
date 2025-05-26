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
OPENWEATHERMAP_API_KEY = "6a32dac6c38966d881b839bcf4b59b08"  # Direkter API Key
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
        
        # Liste der bereits verarbeiteten Kalender-Namen
        processed_calendars = set()
        
        for cal in calendars:
            calendar_name = cal.name.lower() if cal.name else "Unbenannter Kalender"
            print(f"Kalender gefunden: {cal.name}")
            
            # Überspringe doppelte Kalender
            if calendar_name in processed_calendars:
                print(f"Überspringe doppelten Kalender: {cal.name}")
                continue
                
            processed_calendars.add(calendar_name)
            
            # Relevante Kalender filtern
            relevant_calendars = ["familie", "patrick", "icloud", "deejay"]
            if any(keyword in calendar_name for keyword in relevant_calendars) or not calendar_name:
                print(f"Verwende Kalender: {cal.name or 'Unbenannter Kalender'}")
                
                # Icon basierend auf Kalendername
                default_icon = "👤"  # Standard-Icon
                if "familie" in calendar_name:
                    default_icon = "👪"
                elif "deejay" in calendar_name:
                    default_icon = "🎵"
                
                try:
                    now_dt = datetime.now(pytz.utc)
                    start_date_dt = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_date_dt = start_date_dt + timedelta(days=30)
                    
                    print(f"Suche Ereignisse von {start_date_dt.date()} bis {end_date_dt.date()}")
                    calendar_events_raw = cal.date_search(start=start_date_dt, end=end_date_dt, expand=True)
                    print(f"Gefundene Ereignisse in '{cal.name or 'Unbenannter Kalender'}': {len(calendar_events_raw)}")
                    
                    processed_event_uids = set()
                    
                    for event_raw in calendar_events_raw:
                        try:
                            event_data = event_raw.data
                            ical = icalendar.Calendar.from_ical(event_data)
                            
                            for component in ical.walk():
                                if component.name == "VEVENT":
                                    uid = str(component.get('uid'))
                                    event_instance_id = uid
                                    if component.get('recurrence-id'):
                                        event_instance_id += str(component.get('recurrence-id').dt)
                                    
                                    if event_instance_id in processed_event_uids:
                                        continue
                                    processed_event_uids.add(event_instance_id)
                                    
                                    summary = str(component.get('summary', 'Unbekanntes Ereignis'))
                                    dtstart_obj = component.get('dtstart').dt
                                    
                                    # Normalisiere dtstart zu einem zeitzonenbewussten datetime-Objekt in UTC
                                    if isinstance(dtstart_obj, date) and not isinstance(dtstart_obj, datetime):
                                        dtstart_utc = datetime(dtstart_obj.year, dtstart_obj.month, dtstart_obj.day, 0, 0, 0, tzinfo=pytz.utc)
                                        all_day = True
                                    elif isinstance(dtstart_obj, datetime):
                                        if dtstart_obj.tzinfo is None:
                                            dtstart_utc = pytz.utc.localize(dtstart_obj)
                                        else:
                                            dtstart_utc = dtstart_obj.astimezone(pytz.utc)
                                        all_day = False
                                        if dtstart_utc.hour == 0 and dtstart_utc.minute == 0 and dtstart_utc.second == 0 and component.get('X-APPLE-ALL-DAY') == 'TRUE':
                                            all_day = True
                                    else:
                                        print(f"Unbekannter Typ für dtstart: {type(dtstart_obj)} für Event {summary}")
                                        continue
                                    
                                    dtstart_local = dtstart_utc.astimezone()
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
                                    else:
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
                                    
                                    # Icon basierend auf Ereignistyp
                                    icon = default_icon
                                    event_type_icons = {
                                        "hochzeit": "🎵",
                                        "musik": "🎵",
                                        "konzert": "🎵",
                                        "tiktok": "👤",
                                        "meeting": "👤",
                                        "termin": "👤"
                                    }
                                    
                                    for keyword, specific_icon in event_type_icons.items():
                                        if keyword in summary.lower():
                                            icon = specific_icon
                                            break
                                    
                                    events.append({
                                        "title": summary,
                                        "time": time_display,
                                        "timestamp": dtstart_utc.timestamp(),
                                        "icon": icon,
                                        "all_day": all_day,
                                        "calendar": cal.name or "Unbenannter Kalender"
                                    })
                        except Exception as e:
                            print(f"Fehler beim Verarbeiten eines Ereignisses: {e}")
                except Exception as e:
                    print(f"Fehler beim Abrufen von Ereignissen aus Kalender {cal.name or 'Unbenannter Kalender'}: {e}")
        
        # Ereignisse nach Zeitstempel sortieren
        events.sort(key=lambda x: x["timestamp"])
        
        print(f"Insgesamt gefundene und verarbeitete Ereignisse: {len(events)}")
        
        if not events:
            print("Keine Kalenderereignisse gefunden, verwende Beispieldaten")
            return get_example_calendar_events()
            
    except Exception as e:
        print(f"Kritischer Fehler beim Abrufen der Kalendereinträge: {e}")
        return get_example_calendar_events()
    
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
        response_current.raise_for_status()
        data_current = response_current.json()

        weather_data_result["current"] = {
            "temperature": round(data_current['main']['temp']),
            "feels_like": round(data_current['main']['feels_like']),
            "wind_speed": round(data_current['wind']['speed'] * 3.6), # m/s zu km/h
            "wind_direction": deg_to_cardinal(data_current['wind']['deg']),
            "description": data_current['weather'][0]['description'].capitalize(),
            "icon": map_owm_icon_to_simple(data_current['weather'][0]['icon']),
            "humidity": data_current['main']['humidity'],
            "city": data_current['name']
        }
        
        # 5-Tage-Vorhersage mit der kostenlosen API
        url_forecast = f"https://api.openweathermap.org/data/2.5/forecast?q={WEATHER_CITY}&units=metric&lang=de&appid={OPENWEATHERMAP_API_KEY}"
        response_forecast = requests.get(url_forecast)
        response_forecast.raise_for_status()
        data_forecast = response_forecast.json()

        # Gruppiere die Vorhersagen nach Tagen
        daily_forecasts = {}
        for item in data_forecast['list']:
            date = datetime.fromtimestamp(item['dt']).date()
            if date not in daily_forecasts:
                daily_forecasts[date] = {
                    'temp_min': float('inf'),
                    'temp_max': float('-inf'),
                    'icon': item['weather'][0]['icon'],
                    'description': item['weather'][0]['description']
                }
            
            daily_forecasts[date]['temp_min'] = min(daily_forecasts[date]['temp_min'], item['main']['temp_min'])
            daily_forecasts[date]['temp_max'] = max(daily_forecasts[date]['temp_max'], item['main']['temp_max'])

        # Konvertiere die gruppierten Daten in das gewünschte Format
        today = datetime.now().date()
        for i, (date, forecast) in enumerate(sorted(daily_forecasts.items())[:5]):
            day_name = ""
            if date == today:
                day_name = "Heute"
            elif date == today + timedelta(days=1):
                day_name = "Morgen"
            else:
                day_name = WOCHENTAGE[date.weekday()]

            weather_data_result["forecast"].append({
                "day": day_name,
                "temp_day": round(forecast['temp_max']),
                "temp_night": round(forecast['temp_min']),
                "icon": map_owm_icon_to_simple(forecast['icon']),
                "description": forecast['description'].capitalize()
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
        "weather": get_weather_data()
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

    app.run(host='0.0.0.0', port=5000, debug=True)