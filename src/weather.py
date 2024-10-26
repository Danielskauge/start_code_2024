from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import requests
import numpy as np
from dataclasses import dataclass

@dataclass
class WeatherData:
    """Weather data handler for Yr API"""
    
    def __init__(self):
        self.base_url = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
        self.headers = {
            'User-Agent': 'BuildingEnergySimulator/1.0 (danielrs@stud.ntnu.no)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        }
        self.cache = {}

    def get_forecast(self, location: Tuple[float, float]) -> Dict[str, List]:
        """
        Fetch weather forecast for next day from Yr
        Returns data for 00:00-23:00 tomorrow
        """
        lat, lon = self._round_coordinates(location)
        
        if cached_data := self._get_cached_data(lat, lon):
            return cached_data
        
        try:
            data = self._fetch_weather_data(lat, lon)
            return self._process_timeseries(data, lat, lon)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return self._generate_synthetic_data()

    def _round_coordinates(self, location: Tuple[float, float]) -> Tuple[float, float]:
        """Round coordinates to 4 decimals as per API TOS"""
        return round(location[0], 4), round(location[1], 4)

    def _get_cached_data(self, lat: float, lon: float) -> Optional[Dict[str, List]]:
        """Check and return cached data if valid"""
        cache_key = f"{lat},{lon}"
        if cache_key in self.cache:
            cached_data, expires = self.cache[cache_key]
            if datetime.now() < expires:
                return cached_data
        return None

    def _fetch_weather_data(self, lat: float, lon: float) -> Dict:
        """Fetch and cache raw weather data from API"""
        params = {'lat': lat, 'lon': lon}
        response = requests.get(self.base_url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            expires = datetime.strptime(response.headers['Expires'], '%a, %d %b %Y %H:%M:%S GMT')
            self.cache[f"{lat},{lon}"] = (data, expires)
            return data
        raise requests.exceptions.RequestException(f"API returned status code {response.status_code}")

    def _process_timeseries(self, data: Dict, lat: float, lon: float) -> Dict[str, List]:
        """Process raw API data into structured timeseries for next day"""
        tomorrow = datetime.now().date() + timedelta(days=1)
        
        # Create list of all hours for tomorrow
        hours = []
        for hour in range(24):
            hours.append(datetime.combine(tomorrow, datetime.min.time()) + timedelta(hours=hour))
        
        result = {
            'timestamp': hours,
            'temperature': [0] * 24,
            'cloud_cover': [0] * 24,
            'wind_speed': [0] * 24,
            'humidity': [0] * 24,
            'precipitation': [0] * 24,
            'pressure': [0] * 24
        }
        
        # Map API data to our hourly structure
        for entry in data['properties']['timeseries']:
            time = datetime.fromisoformat(entry['time'].replace('Z', '+00:00'))
            if time.date() == tomorrow:
                hour = time.hour
                instant = entry['data']['instant']['details']
                
                result['temperature'][hour] = instant.get('air_temperature', 0)
                result['cloud_cover'][hour] = instant.get('cloud_area_fraction', 0)
                result['wind_speed'][hour] = instant.get('wind_speed', 0)
                result['humidity'][hour] = instant.get('relative_humidity', 0)
                result['pressure'][hour] = instant.get('air_pressure_at_sea_level', 0)
                
                # Get precipitation for next hour
                precip = entry['data'].get('next_1_hours', {}).get('details', {}).get('precipitation_amount', 0)
                result['precipitation'][hour] = precip
        
        return result

