from typing import List
import requests
from datetime import datetime, timedelta
import pytz

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
            raise ValueError(f"Could not get exactly 24 hours of prices (got {len(prices)})")
        
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
