from typing import List, Tuple, Dict, Optional
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass


def get_spot_prices(area: str = 'NO3', include_vat: bool = True) -> List[float]:
    """
    Get spot prices for tomorrow from hvakosterstrommen.no API

    Parameters:
        area: Price area code (NO1-NO5, default: NO3 for Trondheim)
        include_vat: Whether to add VAT (25%, except NO4)

    Returns:
        List of 24 hourly prices in NOK/kWh for tomorrow. 
        Prices can be negative during periods of excess power.

    Raises:
        ValueError: If prices are not yet available or API call fails
    """
    tomorrow = datetime.now().date() + timedelta(days=1)
    date_str = tomorrow.strftime('%Y/%m-%d')

    url = f"https://www.hvakosterstrommen.no/api/v1/prices/{date_str}_{area}.json"

    try:
        response = requests.get(url, headers={
            'User-Agent': 'BuildingEnergySimulator/1.0 (danielrs@stud.ntnu.no)'
        })
        response.raise_for_status()

        data = response.json()

        # Extract prices and ensure we get exactly 24 hours
        prices = []
        hour_seen = set()

        for data_this_hour in data:
            # Convert time to hour of day
            time = datetime.fromisoformat(data_this_hour['time_start'])
            hour_of_day = time.hour

            # Skip if we've already seen this hour (handles DST changes)
            if hour_of_day in hour_seen:
                continue

            hour_seen.add(hour_of_day)
            prices.append(data_this_hour['NOK_per_kWh'])  # Can be negative!

            # Stop after 24 hours
            if len(prices) == 24:
                break

        if len(prices) != 24:
            raise ValueError(
                f"Could not get exactly 24 hours of prices (got {len(prices)})")

        # Add VAT if requested (except for NO4)
        # Note: VAT is only applied to positive prices!
        if include_vat and area != 'NO4':
            prices = [price * 1.25 if price > 0 else price for price in prices]

        return prices

    except requests.RequestException as e:
        raise ValueError(f"Error fetching spot prices: {e}")
    except (KeyError, ValueError, TypeError) as e:
        raise ValueError(f"Error parsing spot price data: {e}")


def get_price_area_from_location(lat: float, lon: float) -> str:
    """
    Determine price area based on coordinates

    Price areas in Norway:
    NO1: Oslo / Øst-Norge
    NO2: Kristiansand / Sør-Norge
    NO3: Trondheim / Midt-Norge
    NO4: Tromsø / Nord-Norge (no VAT on electricity)
    NO5: Bergen / Vest-Norge
    """
    if lat > 65:
        return 'NO4'  # Northern Norway
    elif lon < 5.5:
        return 'NO5'  # Western Norway
    elif lat > 63:
        return 'NO3'  # Central Norway
    elif lon < 7.5:
        return 'NO2'  # Southwest Norway
    else:
        return 'NO1'  # Southeast Norway


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
        Fetch weather forecast for the next day from Yr.
        Returns data for 00:00-23:00 tomorrow.
        """
        lat, lon = self._round_coordinates(location)

        if cached_data := self._get_cached_data(lat, lon):
            return cached_data

        try:
            data = self._fetch_weather_data(lat, lon)
            return self._process_timeseries(data)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return self._generate_synthetic_data()

    def _round_coordinates(self, location: Tuple[float, float]) -> Tuple[float, float]:
        """Round coordinates to 4 decimal places as per API TOS."""
        return round(location[0], 4), round(location[1], 4)

    def _get_cached_data(self, lat: float, lon: float) -> Optional[Dict[str, List]]:
        """Check and return cached data if valid."""
        cache_key = f"{lat},{lon}"
        if cache_key in self.cache:
            cached_data, expires = self.cache[cache_key]
            if datetime.now() < expires:
                return cached_data
        return None

    def _fetch_weather_data(self, lat: float, lon: float) -> Dict:
        """Fetch and cache raw weather data from API."""
        params = {'lat': lat, 'lon': lon}
        response = requests.get(
            self.base_url, headers=self.headers, params=params)

        if response.status_code == 200:
            data = response.json()
            expires = datetime.strptime(
                response.headers['Expires'], '%a, %d %b %Y %H:%M:%S GMT')
            self.cache[f"{lat},{lon}"] = (data, expires)
            return data
        raise requests.exceptions.RequestException(
            f"API returned status code {response.status_code}")

    def _process_timeseries(self, data: Dict) -> Dict[str, List]:
        """Process raw API data into structured timeseries for the next day."""
        tomorrow = datetime.now().date() + timedelta(days=1)

        # Create list of all hours for tomorrow
        hours = []
        for hour in range(24):
            hours.append(datetime.combine(
                tomorrow, datetime.min.time()) + timedelta(hours=hour))

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
            time_str = entry['time']
            time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            if time.date() == tomorrow:
                hour = time.hour
                instant = entry['data']['instant']['details']

                result['temperature'][hour] = instant.get('air_temperature', 0)
                result['cloud_cover'][hour] = instant.get(
                    'cloud_area_fraction', 0)
                result['wind_speed'][hour] = instant.get('wind_speed', 0)
                result['humidity'][hour] = instant.get('relative_humidity', 0)
                result['pressure'][hour] = instant.get(
                    'air_pressure_at_sea_level', 0)

                # Get precipitation for the next hour
                precip = entry['data'].get('next_1_hours', {}).get(
                    'details', {}).get('precipitation_amount', 0)
                result['precipitation'][hour] = precip

        return result

    def _generate_synthetic_data(self) -> Dict[str, List]:
        """Generate synthetic weather data if API call fails."""
        tomorrow = datetime.now().date() + timedelta(days=1)
        hours = [datetime.combine(
            tomorrow, datetime.min.time()) + timedelta(hours=i) for i in range(24)]

        # Generate synthetic weather data
        result = {
            'timestamp': hours,
            'temperature': [15 + 5 * (1 + np.sin(2 * np.pi * (hour - 6) / 24)) for hour in range(24)],
            'cloud_cover': [50] * 24,
            'wind_speed': [5] * 24,
            'humidity': [70] * 24,
            'precipitation': [0] * 24,
            'pressure': [1013] * 24
        }

        return result
