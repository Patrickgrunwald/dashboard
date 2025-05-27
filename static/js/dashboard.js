// Weather icon mapping
const weatherIcons = {
    'sunny': 'fa-sun',
    'clear-night': 'fa-moon',
    'partly-cloudy-day': 'fa-cloud-sun',
    'partly-cloudy-night': 'fa-cloud-moon',
    'cloudy': 'fa-cloud',
    'mostly-cloudy': 'fa-cloud',
    'rain': 'fa-cloud-rain',
    'rainy-day': 'fa-cloud-sun-rain',
    'rainy-night': 'fa-cloud-moon-rain',
    'thunderstorm': 'fa-bolt',
    'snow': 'fa-snowflake',
    'fog': 'fa-smog'
};

// Update time and date
function updateDateTime() {
    const now = new Date();
    const dateElement = document.getElementById('current-date');
    const timeElement = document.getElementById('current-time');
    
    dateElement.textContent = now.toLocaleDateString('de-DE', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    
    timeElement.textContent = now.toLocaleTimeString('de-DE', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Update weather information
function updateWeather(data) {
    // Current weather
    const currentWeather = data.weather.current;
    document.getElementById('current-temp').textContent = currentWeather.temperature;
    document.getElementById('wind-speed').textContent = currentWeather.wind_speed;
    document.getElementById('humidity').textContent = currentWeather.humidity;
    
    const currentIcon = document.getElementById('current-weather-icon');
    currentIcon.className = `weather-icon fas ${weatherIcons[currentWeather.icon] || 'fa-cloud'}`;
    
    // Forecast
    const forecastContainer = document.getElementById('weather-forecast');
    forecastContainer.innerHTML = '';
    
    data.weather.forecast.forEach(day => {
        const forecastItem = document.createElement('div');
        forecastItem.className = 'forecast-item';
        forecastItem.innerHTML = `
            <div class="day">${day.day}</div>
            <i class="fas ${weatherIcons[day.icon] || 'fa-cloud'}"></i>
            <div class="temp">${day.temp_day}°</div>
        `;
        forecastContainer.appendChild(forecastItem);
    });
}

// Update calendar events
function updateCalendar(data) {
    const eventsContainer = document.getElementById('calendar-events');
    eventsContainer.innerHTML = '';
    
    data.calendar.forEach(event => {
        const eventElement = document.createElement('div');
        eventElement.className = 'event';
        eventElement.innerHTML = `
            <div class="event-icon">${event.icon}</div>
            <div class="event-details">
                <div class="event-title">${event.title}</div>
                <div class="event-time">${event.time}</div>
            </div>
        `;
        eventsContainer.appendChild(eventElement);
    });
}

// Fetch and update all data
async function updateDashboard() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        
        updateDateTime();
        updateWeather(data);
        updateCalendar(data);
    } catch (error) {
        console.error('Error updating dashboard:', error);
    }
}

// Initial update
updateDashboard();

// Update every minute
setInterval(updateDashboard, 60000); 