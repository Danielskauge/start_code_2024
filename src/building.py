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
class Building:
    """Simplified building energy system configuration"""
    battery_capacity_kwh: float
    battery_max_power_kw: float
    location: Tuple[float, float]
    solar: SolarSetup