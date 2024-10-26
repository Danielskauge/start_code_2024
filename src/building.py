from dataclasses import dataclass
from typing import Tuple, Optional
from enum import Enum

class BuildingType(Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"

@dataclass
class GridTariff:
    """Grid power pricing configuration"""
    fixed_rate: float  # NOK/kWh
    time_of_use: bool  # Whether to use time-based pricing
    peak_hours_rate: Optional[float] = None  # NOK/kWh during peak hours
    peak_hours: Optional[Tuple[int, int]] = None  # (start_hour, end_hour)

@dataclass
class SolarSetup:
    """Solar panel configuration"""
    peak_power_kw: float
    azimuth_angle: float  # 0=North, 90=East, 180=South, 270=West
    tilt_angle: float     # 0=Horizontal, 90=Vertical
    efficiency: float = 0.2
    temp_coefficient: float = -0.4  # Power temperature coefficient (%/°C)

@dataclass
class Building:
    """Simplified building energy system configuration"""
    battery_capacity_kwh: float
    battery_max_power_kw: float
    location: Tuple[float, float]
    solar: SolarSetup