// Function to format date in German
function formatDate(date) {
    const options = { 
        weekday: 'long', 
        day: 'numeric', 
        month: 'long',
        timeZone: 'Europe/Berlin'
    };
    return date.toLocaleDateString('de-DE', options);
}

// Function to format time in German
function formatTime(date) {
    const options = { 
        hour: '2-digit', 
        minute: '2-digit',
        timeZone: 'Europe/Berlin'
    };
    return date.toLocaleTimeString('de-DE', options);
}

// Function to update the current time
function updateCurrentTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = formatTime(now);
    document.getElementById('current-date').textContent = formatDate(now);
}

// Update time every second
setInterval(updateCurrentTime, 1000);
updateCurrentTime();

// Function to display calendar events
function displayCalendarData(events) {
    const calendarContainer = document.getElementById('calendar-container');
    calendarContainer.innerHTML = '';

    if (events.length === 0) {
        calendarContainer.innerHTML = '<div class="no-events">Keine Termine in den nächsten 7 Tagen</div>';
        return;
    }

    events.forEach(event => {
        const eventElement = document.createElement('div');
        eventElement.className = 'calendar-entry';
        
        const eventContent = `
            <div class="calendar-entry-icon">${event.icon}</div>
            <div class="calendar-entry-content">
                <div class="calendar-entry-title">${event.title}</div>
                <div class="calendar-entry-time">${event.time}</div>
                ${event.location ? `<div class="calendar-entry-location">${event.location}</div>` : ''}
                <div class="calendar-entry-calendar">${event.calendar}</div>
            </div>
        `;
        
        eventElement.innerHTML = eventContent;
        calendarContainer.appendChild(eventElement);
    });
}

// Function to display weather data
function displayWeatherData(weather) {
    const weatherContainer = document.getElementById('weather-container');
    weatherContainer.innerHTML = '';

    weather.forEach(day => {
        const weatherElement = document.createElement('div');
        weatherElement.className = 'weather-day';
        
        const weatherContent = `
            <div class="weather-date">${day.date}</div>
            <div class="weather-icon">
                <img src="http://openweathermap.org/img/wn/${day.icon}@2x.png" alt="${day.description}">
            </div>
            <div class="weather-temp">${day.temp_min}° - ${day.temp_max}°</div>
            <div class="weather-desc">${day.description}</div>
        `;
        
        weatherElement.innerHTML = weatherContent;
        weatherContainer.appendChild(weatherElement);
    });
}

// Function to fetch and update data
function updateData() {
    // Fetch calendar data
    fetch('/api/calendar')
        .then(response => response.json())
        .then(data => {
            displayCalendarData(data);
        })
        .catch(error => {
            console.error('Error fetching calendar data:', error);
            document.getElementById('calendar-container').innerHTML = 
                '<div class="error">Fehler beim Laden der Kalenderdaten</div>';
        });

    // Fetch weather data
    fetch('/api/weather')
        .then(response => response.json())
        .then(data => {
            displayWeatherData(data);
        })
        .catch(error => {
            console.error('Error fetching weather data:', error);
            document.getElementById('weather-container').innerHTML = 
                '<div class="error">Fehler beim Laden der Wetterdaten</div>';
        });
}

// Update data every 5 minutes
setInterval(updateData, 5 * 60 * 1000);
updateData();

// Wetter-Icons erstellen
function createWeatherIcon(type, container) {
    let iconSvg = '';
    
    switch(type) {
        case 'sunny':
            iconSvg = '<svg viewBox="0 0 24 24" class="sunny-icon"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
            break;
        case 'cloudy':
            iconSvg = '<svg viewBox="0 0 24 24" class="cloudy-icon"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>';
            break;
        case 'rainy':
            iconSvg = '<svg viewBox="0 0 24 24" class="rainy-icon"><path d="M16 13v8"/><path d="M8 13v8"/><path d="M12 15v8"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/></svg>';
            break;
        default:
            iconSvg = '<svg viewBox="0 0 24 24" class="cloudy-icon"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>';
    }
    
    container.innerHTML = iconSvg;
}

// Wetterdaten anzeigen
function displayWeatherData(weather) {
    // Aktuelles Wetter
    document.getElementById('wind-value').textContent = weather.current.wind_speed;
    document.getElementById('weather-time').textContent = weather.current.time;
    document.getElementById('temp-value').textContent = weather.current.temperature;
    document.getElementById('feels-like').textContent = `Gefühlt ${weather.current.feels_like}°`;
    
    // Wetter-Icon
    createWeatherIcon(weather.current.icon, document.getElementById('weather-icon'));
    
    // Wettervorhersage
    const forecastDays = document.querySelectorAll('.forecast-day');
    
    weather.forecast.forEach((forecast, index) => {
        if (index < forecastDays.length) {
            const dayElement = forecastDays[index];
            
            dayElement.querySelector('.day-name').textContent = forecast.day;
            createWeatherIcon(forecast.icon, dayElement.querySelector('.day-icon'));
            dayElement.querySelector('.day-temp').textContent = `${forecast.temp_day}°`;
            dayElement.querySelector('.night-temp').textContent = `${forecast.temp_night}°`;
        }
    });
}

// Daten vom Server abrufen
function fetchDashboardData() {
    fetch('/api/data')
        .then(response => response.json())
        .then(data => {
            // Datum und Uhrzeit aktualisieren
            document.getElementById('current-date').textContent = data.datetime.date;
            document.getElementById('current-time').textContent = data.datetime.time;
            document.getElementById('current-seconds').textContent = data.datetime.seconds;
            
            // Kalendereinträge anzeigen
            displayCalendarEntries(data.calendar);
            
            // Wetterdaten anzeigen
            displayWeatherData(data.weather);
        })
        .catch(error => {
            console.error('Fehler beim Abrufen der Daten:', error);
        });
}

// Seite alle 5 Minuten neu laden
function setupAutoRefresh() {
    // Seite alle 5 Minuten neu laden
    setTimeout(() => {
        window.location.reload();
    }, 5 * 60 * 1000); // 5 Minuten in Millisekunden
}

// Initialisierung
document.addEventListener('DOMContentLoaded', () => {
    // Initiale Anzeige der Uhrzeit
    updateDateTime();
    
    // Uhrzeit jede Sekunde aktualisieren
    setInterval(updateDateTime, 1000);
    
    // Daten vom Server abrufen
    fetchDashboardData();
    
    // Daten alle 30 Sekunden aktualisieren (ohne Neuladen der Seite)
    setInterval(fetchDashboardData, 30 * 1000);
    
    // Seite alle 5 Minuten neu laden
    setupAutoRefresh();
});
