import sys
sys.path.append('/Users/danielskauge/start_code_2024')
import requests
from functools import lru_cache
import logging
from typing import Dict, Optional, List
from ui.heatModule.buildingHeatLoss import BuildingHeatLoss
from ui.heatModule.heatingModule import HeatingSystem
# Import appliance models
from ui.appliance.appliance import (
    DishWasherStatistics,
    WashingMachineStatistics,
    TumbleDryerStatistics,
    OvenStatistics
)
import numpy as np

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

def get_appliance_consumption(occupant_profile: List[int]) -> Dict[str, List[float]]:
    """Simulate appliance energy consumption based on occupant profile."""
    resolution = 60  # minutes
    occupancy = np.array(occupant_profile)
    
    appliances = [
        ('Dish Washer', DishWasherStatistics()),
        ('Washing Machine', WashingMachineStatistics()),
        ('Tumble Dryer', TumbleDryerStatistics()),
        ('Oven', OvenStatistics())
    ]
    
    appliance_load_profiles = {}
    for name, appliance in appliances:
        load_profile = appliance.sample_load_profile(
            resolution=resolution,
            occupancy=occupancy
        )
        appliance_load_profiles[name] = load_profile.tolist()
        
    return appliance_load_profiles

def get_heating_simulation(
    weather_data: Dict[str, List],
    building_params: Dict, 
    heating_params: Dict,
    occupant_profile: List[int],
    include_appliances: bool = True
) -> Dict:
    """Run the heating and appliance simulation using the new models."""
    # Extract outside temperatures for the next 24 hours
    temperatures_outside = weather_data['temperature']
    
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
    
    # Adjust for internal heat gains from occupants
    # Assuming each occupant generates 100W of heat
    internal_heat_gains = [occupants * 0.1 for occupants in occupant_profile]  # Convert W to kW
    
    # Run the heating simulation
    temperatures_inside, energy_consumption_heating, Q_heating, Q_loss = heating_system.simulate_heating(
        temperatures_outside,
        temperature_setpoints,
        heating_params.get('initial_temperature_inside', 18),
        internal_heat_gains=internal_heat_gains
    )
    
    # Run the appliance simulation
    if include_appliances:
        appliance_energy_consumption = get_appliance_consumption(occupant_profile)
    else:
        # Initialize zero profiles for each appliance
        appliance_names = ['Dish Washer', 'Washing Machine', 'Tumble Dryer', 'Oven']
        appliance_energy_consumption = {name: [0]*24 for name in appliance_names}
    
    # Sum up the appliance consumptions to get total appliance consumption
    total_appliance_consumption = [
        sum(appliance_energy_consumption[name][i] for name in appliance_energy_consumption)
        for i in range(24)
    ]
    
    # Combine energy consumptions
    total_energy_consumption = [
        heating + appliance_total
        for heating, appliance_total in zip(energy_consumption_heating, total_appliance_consumption)
    ]
    
    # Prepare the results
    results = {
        'temperatures_inside': temperatures_inside,
        'temperatures_outside': temperatures_outside,
        'energy_consumption_heating': energy_consumption_heating,
        'energy_consumption_appliances': appliance_energy_consumption,  # Now a dict
        'total_energy_consumption': total_energy_consumption,
        'Q_heating': Q_heating,
        'Q_loss': Q_loss
    }
    
    return results
