import sys
sys.path.append('/Users/danielskauge/start_code_2024/src')
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from weather import WeatherData
from solar import simulate_solar
from spot_prices import get_spot_prices, get_price_area_from_location
from battery import optimize_battery
from ui.model import get_heating_simulation


@dataclass
class SolarSetup:
    """Solar panel configuration parameters"""
    peak_power_kw: float = 5.0
    efficiency: float = 0.20
    azimuth_angle: float = 180.0  # South-facing
    tilt_angle: float = 35.0
    temp_coefficient: float = -0.35  # %/°C power reduction

@dataclass
class BatterySetup:
    """Battery configuration parameters"""
    capacity_kwh: float = 13.5
    charge_rate_kw: float = 5.0
    initial_soc: float = 50.0

def run_full_simulation(
    lat: float,
    lon: float,
    building_params: Dict,
    heating_params: Dict,
    occupant_profile: List[int],
    solar_setup: Optional[SolarSetup] = None,
    battery_setup: Optional[BatterySetup] = None,
    include_appliances: bool = True
) -> Dict:
    """
    Run comprehensive building simulation including heating, solar, and battery optimization.
    
    Args:
        lat: Latitude of building location
        lon: Longitude of building location
        building_params: Building thermal parameters
        heating_params: Heating system parameters
        occupant_profile: List of hourly occupancy values
        solar_setup: Solar panel configuration (optional)
        battery_setup: Battery system configuration (optional)
        include_appliances: Whether to include appliance loads
    
    Returns:
        Dict containing all simulation results including heating, solar generation,
        battery optimization and spot prices
    """
    # Get weather data
    weather = WeatherData()
    weather_data = weather.get_forecast((lat, lon))
    
    # Get heating simulation results
    heating_results = get_heating_simulation(
        weather_data=weather_data,
        building_params=building_params,
        heating_params=heating_params,
        occupant_profile=occupant_profile,
        include_appliances=include_appliances
    )
    
    # Initialize results with heating simulation
    results = heating_results.copy()
    
    # Remove initial temperature value to match 24-hour format. First value is the initial temperature.
    results['temperatures_inside'] = results['temperatures_inside'][1:]
    
    # Add solar generation if setup provided
    if solar_setup is None:
        solar_setup = SolarSetup()
    
    solar_generation = simulate_solar(
        solar_setup=solar_setup,
        weather_data=weather_data,
        location=(lat, lon)
    )
    results['solar_generation'] = solar_generation
    
    # Get spot prices for location
    price_area = get_price_area_from_location(lat, lon)
    spot_prices = get_spot_prices(area=price_area)
    results['spot_prices'] = spot_prices
    # Run battery optimization if setup provided
    if battery_setup is None:
        battery_setup = BatterySetup()
    
    battery_soc, grid_power = optimize_battery(
        battery_capacity_kwh=battery_setup.capacity_kwh,
        battery_charge_rate_kw=battery_setup.charge_rate_kw,
        spot_prices=results['spot_prices'],
        load_kwh=results['total_energy_consumption'],
        pv_production_kwh=solar_generation,
        initial_soc=battery_setup.initial_soc
    )
    
    results['battery_soc'] = battery_soc
    results['grid_power'] = grid_power
    
    return results

