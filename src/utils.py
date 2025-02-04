# utils.py

from typing import Tuple, Optional, Dict, List
import requests
import json
from datetime import datetime

def get_coordinates_from_address(address: str) -> Tuple[float, float]:
    """
    Get coordinates from Norwegian address using Kartverket's API

    The API is flexible and accepts various formats:
    - "Streetname Number, Postal Code, City"
    - "Streetname Number, City"
    - "Streetname Number"

    Examples:
        >>> get_coordinates_from_address("Haukelandveien 9, 0380, Bergen")
        (60.3879, 5.3345)
        >>> get_coordinates_from_address("Karl Johans gate 1, Oslo")
        (59.9133, 10.7389)

    Parameters:
        address: Norwegian address string

    Returns:
        Tuple of (latitude, longitude)

    Raises:
        ValueError: If address cannot be found or geocoding fails
    """
    # Clean up the address string
    address = address.strip()

    # Kartverket's geocoding API endpoint
    base_url = "https://ws.geonorge.no/adresser/v1/sok"

    # Create parameters
    params = {
        'sok': address,
        'treffPerSide': 1,  # We only want the best match
        'asciiKompatibel': True,
        'utkoordsys': 4326  # WGS84 (standard GPS coordinates)
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()

        data = response.json()

        if not data.get('adresser'):
            raise ValueError(f"No matches found for address: {address}")

        # Get the first (best) match
        best_match = data['adresser'][0]

        # Extract coordinates (Kartverket returns them as [lon, lat])
        representasjonspunkt = best_match.get('representasjonspunkt', {})
        lon = representasjonspunkt.get('lon')
        lat = representasjonspunkt.get('lat')

        if not all([lat, lon]):
            raise ValueError(f"Could not extract coordinates for address: {address}")

        return (float(lat), float(lon))

    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error fetching coordinates: {str(e)}")
    except (KeyError, IndexError) as e:
        raise ValueError(f"Error parsing API response: {str(e)}")

def export_simulation_results(
    timestamps: List[datetime],
    consumption: List[float],
    solar_generation: List[float],
    battery_soc: List[float],
    grid_power: List[float],
    spot_prices: List[float],
    filepath: Optional[str] = None
) -> Dict:
    """
    Export simulation results in a format suitable for frontend visualization

    Parameters:
        timestamps: List of datetime objects
        consumption: List of consumption values (kW)
        solar_generation: List of solar generation values (kW)
        battery_soc: List of battery state of charge values (%)
        grid_power: List of grid power values (kW)
        spot_prices: List of spot prices (NOK/kWh)
        filepath: Optional path to save JSON file

    Returns:
        Dictionary with formatted data

    Example output format:
    {
        "metadata": {
            "start_time": "2024-03-20T00:00:00",
            "end_time": "2024-03-20T23:00:00",
            "num_datapoints": 24
        },
        "timeseries": {
            "timestamps": ["2024-03-20T00:00:00", ...],
            "consumption": [0.5, 0.6, ...],
            "solar_generation": [0.0, 0.1, ...],
            "battery": {
                "soc": [50.0, 51.2, ...],
                "power": [-0.5, 0.8, ...]  # Calculated from grid and net load
            },
            "grid_power": [0.8, -0.2, ...],
            "spot_prices": [1.2, 1.1, ...]
        },
        "summary": {
            "total_consumption": 100.5,  # kWh
            "total_solar_generation": 45.2,  # kWh
            "max_grid_power": 5.5,  # kW
            "average_spot_price": 1.15,  # NOK/kWh
            "self_consumption_ratio": 0.85  # Solar energy used / solar energy generated
        }
    }
    """
    # Calculate battery power from grid power and net load
    battery_power = [g - (c - s) for g, c, s in zip(grid_power, consumption, solar_generation)]

    # Calculate summary statistics
    total_consumption = sum(consumption)
    total_solar = sum(solar_generation)
    solar_used = sum(min(c, s) for c, s in zip(consumption, solar_generation))

    data = {
        "metadata": {
            "start_time": timestamps[0].isoformat(),
            "end_time": timestamps[-1].isoformat(),
            "num_datapoints": len(timestamps)
        },
        "timeseries": {
            "timestamps": [t.isoformat() for t in timestamps],
            "consumption": consumption,
            "solar_generation": solar_generation,
            "battery": {
                "soc": battery_soc,
                "power": battery_power
            },
            "grid_power": grid_power,
            "spot_prices": spot_prices
        },
        "summary": {
            "total_consumption": round(total_consumption, 2),
            "total_solar_generation": round(total_solar, 2),
            "max_grid_power": round(max(abs(p) for p in grid_power), 2),
            "average_spot_price": round(sum(spot_prices) / len(spot_prices), 2),
            "self_consumption_ratio": round(solar_used / total_solar if total_solar > 0 else 0, 2)
        }
    }

    if filepath:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    return data

def load_building_config(config_path: str) -> Building:
    """
    Load building configuration from JSON file
    
    Example config file:
    {
        "building": {
            "battery_capacity_kwh": 10.0,
            "battery_max_power_kw": 5.0,
            "num_occupants": 4,
            "location": {
                "address": "Sunnlandsskrenten 35b, 7032, Trondheim",
                "coordinates": [63.4305, 10.3950]
            },
            "building_type": "residential",
            "floor_area": 150.0,
            "num_floors": 2,
            "year_built": 2010,
            "heating_type": "heat_pump"
        },
        "solar": {
            "peak_power_kw": 7.0,
            "azimuth_angle": 180,
            "tilt_angle": 35,
            "efficiency": 0.2,
            "temp_coefficient": -0.4
        },
        "tariff": {
            "fixed_rate": 1.0,
            "time_of_use": true,
            "peak_hours_rate": 2.0,
            "peak_hours": [8, 20]
        }
    }
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Get coordinates from address if not provided
        location = config['building']['location']
        if 'coordinates' in location:
            coordinates = tuple(location['coordinates'])
        else:
            coordinates = get_coordinates_from_adress(location['address'])
        
        # Create SolarSetup
        solar = SolarSetup(
            peak_power_kw=config['solar']['peak_power_kw'],
            azimuth_angle=config['solar']['azimuth_angle'],
            tilt_angle=config['solar']['tilt_angle'],
            efficiency=config['solar']['efficiency'],
            temp_coefficient=config['solar']['temp_coefficient']
        )
        
        # Create GridTariff
        tariff = GridTariff(
            fixed_rate=config['tariff']['fixed_rate'],
            time_of_use=config['tariff']['time_of_use'],
            peak_hours_rate=config['tariff'].get('peak_hours_rate'),
            peak_hours=tuple(config['tariff']['peak_hours']) if config['tariff'].get('peak_hours') else None
        )
        
        # Create Building
        return Building(
            battery_capacity_kwh=config['building']['battery_capacity_kwh'],
            battery_max_power_kw=config['building']['battery_max_power_kw'],
            num_occupants=config['building']['num_occupants'],
            location=coordinates,
            building_type=BuildingType(config['building']['building_type']),
            solar=solar,
            tariff=tariff,
            floor_area=config['building']['floor_area'],
            num_floors=config['building']['num_floors'],
            year_built=config['building']['year_built'],
            heating_type=config['building']['heating_type']
        )
        
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise ValueError(f"Error loading building config: {str(e)}")
