import requests
from datetime import datetime, timedelta
from functools import lru_cache
import logging
from typing import Dict, List, Union, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MET_API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
HEADERS = {
    "User-Agent": "EnergyDashboard/1.0 (your_email@example.com)"
}

class WeatherDataError(Exception):
    """Custom exception for weather data fetching errors."""
    pass

@lru_cache(maxsize=100)
def get_weather_data(lat: float, lon: float) -> Optional[Dict]:
    """Fetches weather data for given coordinates with caching."""
    url = f"{MET_API_URL}?lat={lat:.4f}&lon={lon:.4f}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Weather data request failed: {e}")
        return None

@lru_cache(maxsize=100)
def get_location_name(lat: float, lon: float) -> str:
    """Fetches location name via Nominatim."""
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
    try:
        response = requests.get(
            url,
            headers={"User-Agent": HEADERS["User-Agent"]},
            timeout=5
        )
        response.raise_for_status()
        return response.json().get("display_name", "Unknown Location")
    except requests.RequestException as e:
        logger.error(f"Geocoding failed: {e}")
        return "Unknown Location"

class CRESTDemandModel:
    """CREST domestic electricity demand model."""
    
    def __init__(self):
        self.base_temp = 20
        self.temp_factor = 1.5
        self.cloud_factor = 0.5
        self.resident_factor = 1.5
        self.size_factor = 0.1

    def calculate_demand(self, weather_data: Dict, residents: int, apartment_size: float) -> List[Dict]:
        """Calculate 24-hour demand forecast."""
        if not weather_data:
            return [{"day": "Today", "error": "Weather data unavailable"}]

        day_data = {
            "day": "Today",
            "hourly_demand": [],
            "average_demand": None
        }

        day_weather = [
            entry['data']['instant']['details']
            for entry in weather_data['properties']['timeseries'][:24]
        ]

        daily_demand = []

        for hour, weather in enumerate(day_weather):
            temp = weather.get("air_temperature", 15)
            cloud_cover = weather.get("cloud_area_fraction", 50)
            
            base_demand = self.temp_factor * max(0, self.base_temp - temp)
            cloud_demand = self.cloud_factor * cloud_cover / 100
            resident_demand = self.resident_factor * residents
            size_demand = self.size_factor * apartment_size
            
            demand = max(0, base_demand + cloud_demand + resident_demand + size_demand)
            
            day_data["hourly_demand"].append({
                "time": f"{hour:02}:00",
                "demand": f"{demand:.2f} kWh"
            })
            daily_demand.append(demand)

        if daily_demand:
            day_data["average_demand"] = f"{sum(daily_demand) / len(daily_demand):.2f} kWh"
        
        return [day_data]

def get_hourly_demand_data(lat: float, lon: float, residents: int, apartment_size: float) -> Union[List[Dict], str]:
    """Get hourly demand forecast for given location and parameters."""
    weather_data = get_weather_data(lat, lon)
    if weather_data is None:
        return "Weather data unavailable."
    
    model = CRESTDemandModel()
    return model.calculate_demand(weather_data, residents, apartment_size)
