import requests
from functools import lru_cache
from typing import Dict, Optional, List, Tuple
import logging
from model.heatModule.buildingHeatLoss import BuildingHeatLoss
from model.heatModule.heatingModule import HeatingSystem
from model.PV.solar import SolarSetup, simulate_solar
from fetchers import WeatherData, get_spot_prices
# Import appliance models
from model.appliance.appliance import (
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
WEATHER_DATA_FETCHER = WeatherData()


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


def get_PV_simulation(
        peak_power_kw: float,
        azimuth_angle: float,  # 0=North, 90=East, 180=South, 270=West
        tilt_angle: float,     # 0=Horizontal, 90=Vertical
        weather_data: Dict[str, List],
        location: Tuple[float, float],
        efficiency: float = 0.2,
        temp_coefficient: float = -0.4  # Power temperature coefficient (%/°C)
) -> List[float]:
    """
    Simulate solar panel power generation for next day

    Args:
        peak_power_kw: Peak power output in kW
        azimuth_angle: Orientation of the panels (0=North, 90=East, 180=South, 270=West)
        tilt_angle: Tilt angle of the panels (0=Horizontal, 90=Vertical)
        efficiency: Panel efficiency (default 0.2)
        temp_coefficient: Power temperature coefficient (%/°C) (default -0.4)
        weather_data: Weather forecast for next day
        location: (latitude, longitude) of installation

    Returns:
        List of power generation values for each hour
    """
    solar_setup = SolarSetup(
        peak_power_kw,
        azimuth_angle,
        tilt_angle,
        efficiency,
        temp_coefficient
    )

    generation = simulate_solar(
        solar_setup,
        weather_data,
        location
    )

    return generation


def get_simulation_results(
    lat: float,
    lon: float,
    building_params: Dict,
    heating_params: Dict,
    occupant_profile: List[int],
    include_appliances: bool = True
) -> Dict:
    """Run the heating and appliance simulation using the new models."""
    # Fetch weather data
    weather_data = WEATHER_DATA_FETCHER.get_forecast((lat, lon))
    if weather_data is None:
        return {"error": "Weather data unavailable."}

    # Extract outside temperatures for the next 24 hours
    temperatures_outside = weather_data["temperature"]

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
    temperature_setpoints = [heating_params.get(
        'temperature_setpoint', 20)] * 24

    # Adjust for internal heat gains from occupants
    # Assuming each occupant generates 100W of heat
    internal_heat_gains = [
        occupants * 0.1 for occupants in occupant_profile]  # Convert W to kW

    # Run the heating simulation
    temperatures_inside, energy_consumption_heating, Q_heating, Q_loss = heating_system.simulate_heating(
        temperatures_outside,
        temperature_setpoints,
        heating_params.get('initial_temperature_inside', 18),
        internal_heat_gains=internal_heat_gains
    )

    # Run the appliance simulation
    if include_appliances:
        appliance_energy_consumption = get_appliance_consumption(
            occupant_profile)
    else:
        # Initialize zero profiles for each appliance
        appliance_names = ['Dish Washer',
                           'Washing Machine', 'Tumble Dryer', 'Oven']
        appliance_energy_consumption = {
            name: [0]*24 for name in appliance_names}

    # Sum up the appliance consumptions to get total appliance consumption
    total_appliance_consumption = [
        sum(appliance_energy_consumption[name][i]
            for name in appliance_energy_consumption)
        for i in range(24)
    ]

    # Combine energy consumptions
    total_energy_consumption = [
        heating + appliance_total
        for heating, appliance_total in zip(energy_consumption_heating, total_appliance_consumption)
    ]
    PV_energy_production = get_PV_simulation(
        peak_power_kw=building_params['solar_panel_peak_power'],
        azimuth_angle=building_params['solar_panel_azimuth'],
        efficiency=building_params['solar_panel_efficiency'],
        temp_coefficient=building_params['solar_panel_temp_coefficient'],
        tilt_angle=building_params['roof_pitch'],
        weather_data=weather_data,
        location=(lat, lon)
    )

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
