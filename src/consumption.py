from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np
from enum import Enum
from building import Building, BuildingType

class ApplianceType(Enum):
    CONSTANT = "constant"        # e.g., fridge
    OCCUPANCY = "occupancy"      # e.g., lights
    SCHEDULED = "scheduled"      # e.g., dishwasher
    TEMPERATURE = "temperature"  # e.g., heating/cooling
    RANDOM = "random"           # e.g., kettle, TV

class Appliance:
    def __init__(
        self,
        name: str,
        type: ApplianceType,
        rated_power: float,
        duty_cycle: float = 1.0,
        temperature_dependent: bool = False,
        occupancy_dependent: bool = False,
        schedule: Optional[List[float]] = None
    ):
        self.name = name
        self.type = type
        self.rated_power = rated_power
        self.duty_cycle = duty_cycle
        self.temperature_dependent = temperature_dependent
        self.occupancy_dependent = occupancy_dependent
        self.schedule = schedule if schedule is not None else [1.0] * 24

class TimeOfDay(Enum):
    NIGHT = "night"      # 00:00-06:00
    MORNING = "morning"  # 06:00-09:00
    DAY = "day"         # 09:00-17:00
    EVENING = "evening"  # 17:00-00:00

# Occupancy profiles for each building type and time period
OCCUPANCY_PROFILES = {
    BuildingType.RESIDENTIAL: {
        'weekday': {
            TimeOfDay.NIGHT: 0.9,    # Most people sleeping
            TimeOfDay.MORNING: 0.7,   # People getting ready
            TimeOfDay.DAY: 0.2,      # People at work
            TimeOfDay.EVENING: 0.8,   # People at home
        },
        'weekend': {
            TimeOfDay.NIGHT: 0.9,
            TimeOfDay.MORNING: 0.8,
            TimeOfDay.DAY: 0.6,
            TimeOfDay.EVENING: 0.7,
        }
    },
    BuildingType.COMMERCIAL: {
        'weekday': {
            TimeOfDay.NIGHT: 0.1,    # Security/cleaning
            TimeOfDay.MORNING: 0.6,   # Starting work
            TimeOfDay.DAY: 0.9,      # Full operation
            TimeOfDay.EVENING: 0.3,   # Some overtime
        },
        'weekend': {
            TimeOfDay.NIGHT: 0.1,
            TimeOfDay.MORNING: 0.1,
            TimeOfDay.DAY: 0.2,
            TimeOfDay.EVENING: 0.1,
        }
    },
    BuildingType.INDUSTRIAL: {
        'weekday': {
            TimeOfDay.NIGHT: 0.5,    # Night shift
            TimeOfDay.MORNING: 0.8,   # Morning shift
            TimeOfDay.DAY: 1.0,      # Peak operation
            TimeOfDay.EVENING: 0.7,   # Evening shift
        },
        'weekend': {
            TimeOfDay.NIGHT: 0.3,
            TimeOfDay.MORNING: 0.4,
            TimeOfDay.DAY: 0.5,
            TimeOfDay.EVENING: 0.3,
        }
    }
}

def get_building_appliances(building_type: BuildingType) -> List[Appliance]:
    """Return list of typical appliances for building type"""
    
    if building_type == BuildingType.RESIDENTIAL:
        return [
            Appliance("Fridge", ApplianceType.CONSTANT, rated_power=0.1, duty_cycle=0.3),
            Appliance("Lights", ApplianceType.OCCUPANCY, rated_power=0.2),
            Appliance("TV", ApplianceType.RANDOM, rated_power=0.15),
            Appliance("Heating", ApplianceType.TEMPERATURE, rated_power=2.0, temperature_dependent=True),
            Appliance("Dishwasher", ApplianceType.SCHEDULED, rated_power=1.2, 
                     schedule=[0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0]),
        ]
    
    elif building_type == BuildingType.COMMERCIAL:
        return [
            Appliance("HVAC", ApplianceType.TEMPERATURE, rated_power=5.0, temperature_dependent=True),
            Appliance("Lighting", ApplianceType.OCCUPANCY, rated_power=1.0),
            Appliance("Computers", ApplianceType.SCHEDULED, rated_power=2.0,
                     schedule=[0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0]),
            Appliance("Servers", ApplianceType.CONSTANT, rated_power=3.0, duty_cycle=0.8),
        ]
    
    else:  # INDUSTRIAL
        return [
            Appliance("Process Heat", ApplianceType.SCHEDULED, rated_power=10.0),
            Appliance("Ventilation", ApplianceType.CONSTANT, rated_power=5.0),
            Appliance("Machinery", ApplianceType.SCHEDULED, rated_power=15.0,
                     schedule=[0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0]),
        ]

def get_time_period(hour: int) -> TimeOfDay:
    """Convert hour to time period"""
    if 0 <= hour < 6:
        return TimeOfDay.NIGHT
    elif 6 <= hour < 9:
        return TimeOfDay.MORNING
    elif 9 <= hour < 17:
        return TimeOfDay.DAY
    else:
        return TimeOfDay.EVENING

def is_weekend(timestamp: datetime) -> bool:
    """Check if timestamp is on weekend"""
    return timestamp.weekday() >= 5

def generate_synthetic_consumption(timestamps: List[datetime]) -> List[float]:
    """
    Generate synthetic consumption data with realistic patterns
    
    Args:
        timestamps: List of hourly timestamps
    
    Returns:
        List of hourly consumption values in kW
    """
    consumption = []
    
    for timestamp in timestamps:
        hour = timestamp.hour
        
        # Base load (always on)
        base_load = 0.5
        
        # Daily pattern
        hour_factor = np.sin(hour * np.pi / 12) * 0.5 + 1.0
        
        # Morning peak (7-9)
        if 7 <= hour <= 9:
            hour_factor *= 1.5
            
        # Evening peak (17-21)
        if 17 <= hour <= 21:
            hour_factor *= 1.8
            
        # Night valley (0-5)
        if 0 <= hour <= 5:
            hour_factor *= 0.6
        
        # Add some random variation
        random_factor = np.random.normal(1, 0.1)
        
        # Combine all factors
        load = base_load * hour_factor * random_factor
        
        consumption.append(max(0, load))
    
    return consumption

def simulate_consumption(building: Building, weather_data: Dict[str, List]) -> List[float]:
    """
    Main consumption simulation function, now using synthetic data
    
    Args:
        building: Building configuration
        weather_data: Weather forecast data
        
    Returns:
        List of hourly consumption values in kW
    """
    return generate_synthetic_consumption(weather_data['timestamp'])

def simulate_simple_consumption(building: Building, weather_data: Dict[str, List]) -> List[float]:
    """
    Simplified consumption simulation with realistic daily patterns
    
    Args:
        building: Building configuration
        weather_data: Weather forecast data
        
    Returns:
        List of hourly consumption values in kW
    """
    consumption = []
    timestamps = weather_data['timestamp']
    temperatures = weather_data['temperature']
    
    for i, timestamp in enumerate(timestamps):
        hour = timestamp.hour
        temperature = temperatures[i]
        
        # Base load
        base_load = 0.5
        
        # Daily pattern (higher during day, lower at night)
        hour_factor = np.sin(hour * np.pi / 12) * 0.5 + 1.0
        
        # Morning peak (7-9)
        if 7 <= hour <= 9:
            hour_factor *= 1.5
            
        # Evening peak (17-21)
        if 17 <= hour <= 21:
            hour_factor *= 1.8
            
        # Night valley (0-5)
        if 0 <= hour <= 5:
            hour_factor *= 0.6
        
        # Temperature effect (more consumption when very cold or very hot)
        temp_factor = 1.0
        if temperature < 16:
            temp_factor += 0.1 * (16 - temperature)  # More heating needed
        elif temperature > 22:
            temp_factor += 0.05 * (temperature - 22)  # More cooling needed
        
        # Random variation
        random_factor = np.random.normal(1, 0.1)
        
        # Combine all factors
        load = base_load * hour_factor * temp_factor * random_factor
        
        # Scale based on battery size as a proxy for building size
        # Assuming larger batteries are installed in larger buildings
        size_factor = building.battery_capacity_kwh / 10  # Normalized to 10kWh battery
        load *= size_factor
        
        consumption.append(max(0, load))
    
    return consumption
