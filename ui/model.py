import requests
from datetime import datetime, timedelta
from functools import lru_cache
import logging
from typing import Dict, List, Union, Optional
from heatModule.buildingHeatLoss import BuildingHeatLoss
from heatModule.heatingModule import HeatingSystem

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
def get_heating_simulation(
    lat: float, 
    lon: float, 
    building_params: Dict, 
    heating_params: Dict
) -> Dict:
    """Run the heating simulation using the new models."""
    # Fetch weather data
    weather_data = get_weather_data(lat, lon)
    if weather_data is None:
        return {"error": "Weather data unavailable."}
    
    # Extract outside temperatures for the next 24 hours
    temperatures_outside = [
        entry['data']['instant']['details'].get('air_temperature', 15)
        for entry in weather_data['properties']['timeseries'][:24]
    ]
    
    # Initialize the BuildingHeatLoss instance with provided parameters
    building = BuildingHeatLoss(**building_params)
    
    # Initialize the HeatingSystem instance
    heating_system = HeatingSystem(
        building=building,
        COP=heating_params.get('COP', 3.5),
        min_Q_heating=heating_params.get('min_Q_heating', 0),
        max_Q_heating=heating_params.get('max_Q_heating', 5)
    )
    
    # Define temperature setpoints (assuming constant setpoint)
    temperature_setpoints = [heating_params.get('temperature_setpoint', 20)] * 24
    
    # Run the simulation
    temperatures_inside, energy_consumption, Q_heating, Q_loss = heating_system.simulate_heating(
        temperatures_outside,
        temperature_setpoints,
        heating_params.get('initial_temperature_inside', 18)
    )
    
    # Prepare the results
    results = {
        'temperatures_inside': temperatures_inside,
        'temperatures_outside': temperatures_outside,
        'energy_consumption': energy_consumption,
        'Q_heating': Q_heating,
        'Q_loss': Q_loss
    }
    
    return results
