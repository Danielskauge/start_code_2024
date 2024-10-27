from typing import Dict
from datetime import datetime, timedelta
from building import Building, BuildingType, SolarSetup, GridTariff
from consumption import simulate_consumption
from solar import simulate_solar
from battery import optimize_battery
from spot_prices import get_spot_prices
from utils import export_simulation_results

def run_simulation(
    lat: float,
    lon: float,
    num_occupants: int,
    floor_area: float,
    num_floors: int,
    year_built: int,
    heating_type: str
) -> Dict:
    """
    Run a building energy simulation with the specified parameters.
    """
    # Import WeatherData within the function to avoid circular imports
    from weather import WeatherData

    # Initialize building with user-specified parameters
    building = Building(
        battery_capacity_kwh=10.0,
        battery_max_power_kw=5.0,
        num_occupants=num_occupants,
        location=(lat, lon),
        building_type=BuildingType.RESIDENTIAL,
        solar=SolarSetup(
            peak_power_kw=7.0,
            azimuth_angle=180,  # South-facing
            tilt_angle=35,
            efficiency=0.2,
            temp_coefficient=-0.4
        ),
        tariff=GridTariff(
            fixed_rate=1.0,
            time_of_use=True,
            peak_hours_rate=2.0,
            peak_hours=(8, 20)
        ),
        floor_area=floor_area,
        num_floors=num_floors,
        year_built=year_built,
        heating_type=heating_type
    )

    # Set default dates for weather data
    start_date = (datetime.now() + timedelta(days=1)).date()
    end_date = start_date

    # Fetch weather data for the next day
    weather = WeatherData().get_forecast((lat, lon))

    # Combine weather data into a single structure for simulation
    combined_weather_data = weather

    # Simulate consumption based on the building and weather data
    consumption = simulate_consumption(building, combined_weather_data)

    # Simulate solar generation
    solar_generation = simulate_solar(building.solar, combined_weather_data, building.location)

    # Calculate the number of hours in the simulation period
    num_hours = len(combined_weather_data['timestamp'])

    # Get spot prices for the simulation period
    spot_prices = get_spot_prices(num_hours)

    # Optimize battery operation
    soc, grid = optimize_battery(
        building.battery_capacity_kwh,
        building.battery_max_power_kw,
        spot_prices,
        consumption,
        solar_generation
    )

    # Prepare results for export
    results = export_simulation_results(
        combined_weather_data['timestamp'],
        consumption,
        solar_generation,
        soc,
        grid,
        spot_prices
    )

    return results
