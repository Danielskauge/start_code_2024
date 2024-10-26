from datetime import datetime, timedelta
from building import Building, BuildingType, SolarSetup, GridTariff
from weather import WeatherData
from consumption import simulate_consumption
from solar import simulate_solar
from battery import optimize_battery
from spot_prices import get_spot_prices
from visualization import plot_energy_flow
from utils import get_coordinates_from_adress
from utils import export_simulation_results

def main():
    adress = "Sunnlandsskrenten 35b, 7032, Trondheim"
    # Initialize building
    building = Building(
        battery_capacity_kwh=10.0,
        battery_max_power_kw=5.0,
        num_occupants=4,
        location=(63.4305, 10.3950),  # Trondheim
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
        floor_area=150.0,
        num_floors=2,
        year_built=2010,
        heating_type="heat_pump"
    )
    
    # Get weather forecast for next day
    weather_forecast_tomorrow = WeatherData().get_forecast(building.location)
    
    # Simulate/predict consumption for next day
    consumption_tomorrow = simulate_consumption(
        building,
        weather_forecast_tomorrow
    )
    
    # Simulate solar generation for next day
    solar_generation_tomorrow = simulate_solar(
        building.solar,
        weather_forecast_tomorrow,
        building.location
    )
    
    # Get spot prices for tomorrow
    spot_prices_tomorrow = get_spot_prices()
    
    # Optimize battery operation for tomorrow
    soc, grid = optimize_battery(
        building.battery_capacity_kwh,
        building.battery_max_power_kw,
        spot_prices_tomorrow,
        consumption_tomorrow,
        solar_generation_tomorrow
    )
    
    # Create results directory if it doesn't exist
    import os
    os.makedirs("results", exist_ok=True)
    
    # Export results
    export_simulation_results(
        weather_forecast_tomorrow['timestamp'],  # Pass just the timestamps list
        consumption_tomorrow,
        solar_generation_tomorrow,
        soc,
        grid,
        spot_prices_tomorrow,
        "results/results.json"
    )
    
    # Visualize results
    plot_energy_flow(
        weather_forecast_tomorrow['timestamp'],
        consumption_tomorrow,
        solar_generation_tomorrow,
        soc,
        grid,
        spot_prices_tomorrow
    )

if __name__ == "__main__":
    main()
