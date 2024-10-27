from typing import List, Dict, Tuple
from datetime import datetime
import numpy as np

# Physical constants
STANDARD_TEST_TEMP_C = 25.0  # Temperature at which solar panels are rated
MAX_THEORETICAL_IRRADIANCE = 1000  # W/m² at sea level on clear day
MAX_CLOUD_BLOCKING = 0.75  # Clouds block up to 75% of radiation
DIFFUSE_MIN_RATIO = 0.2  # Minimum diffuse fraction even on clear days

def simulate_solar(
    solar_setup: 'SolarSetup',
    weather_data: Dict[str, List],
    location: Tuple[float, float]
) -> List[float]:
    """
    Simulate solar panel power generation for next day using simplified model:
    
    P = P_peak * (I_total/1000) * f_temp * η
    
    where:
    - P is output power
    - I_total combines direct and diffuse radiation
    - f_temp accounts for temperature derating
    - η is panel efficiency
    
    Parameters:
        solar_setup: Solar panel configuration
        weather_data: Weather forecast for next day
        location: (latitude, longitude) of installation
    """
    generation = []
    lat, lon = location
    
    for i in range(len(weather_data['timestamp'])):
        time = weather_data['timestamp'][i]
        temp = weather_data['temperature'][i]
        clouds = weather_data['cloud_cover'][i]
        
        # Calculate total irradiance from sun position and weather
        irr = _calculate_irradiance(time, lat, lon, clouds)
        
        # Account for panel orientation relative to sun
        iam = _calculate_iam(time, solar_setup.azimuth_angle, solar_setup.tilt_angle)
        
        # Temperature affects panel efficiency linearly
        temp_factor = 1 + solar_setup.temp_coefficient * (temp - STANDARD_TEST_TEMP_C) / 100
        
        # Split radiation into direct (affected by angle) and diffuse components
        diffuse_ratio = min(1.0, clouds/100 + DIFFUSE_MIN_RATIO)
        direct_irr = irr * (1 - diffuse_ratio) * iam
        
        # Diffuse radiation comes from whole sky dome - use view factor
        sky_view_factor = (1 + np.cos(np.radians(solar_setup.tilt_angle))) / 2
        diffuse_irr = irr * diffuse_ratio * sky_view_factor
        
        total_irr = direct_irr + diffuse_irr
        
        # Final power calculation
        power = (solar_setup.peak_power_kw * (total_irr / MAX_THEORETICAL_IRRADIANCE) * 
                temp_factor * solar_setup.efficiency)
        
        generation.append(max(0, power))
    
    return generation

def _calculate_iam(time: datetime, azimuth: float, tilt: float) -> float:
    """
    Calculate Incident Angle Modifier - accounts for reduced panel efficiency 
    when light hits at non-perpendicular angles.
    
    A proper implementation would:
    1. Calculate actual solar position (altitude, azimuth)
    2. Compute angle of incidence using spherical trigonometry
    3. Apply ASHRAE formula: IAM(θ) = 1 - b₀(1/cos(θ) - 1)
    
    This is a simplified geometric approximation.
    """
    hour = time.hour
    day_of_year = time.timetuple().tm_yday
    
    # Approximate day length variation through year
    solar_noon = 12
    annual_phase = 2 * np.pi * (day_of_year - 80) / 365  # 80 is spring equinox
    day_length = 12 + 4 * np.sin(annual_phase)  # Varies ±4 hours around 12
    
    sunrise = solar_noon - day_length/2
    sunset = solar_noon + day_length/2
    
    if hour < sunrise or hour > sunset:
        return 0
    
    # Simple cosine approximation of panel orientation effect
    time_angle = np.pi * (hour - sunrise) / (sunset - sunrise)
    panel_factor = np.cos(np.radians(tilt)) + np.cos(np.radians(azimuth - 180))
    
    return max(0, np.sin(time_angle) * panel_factor / 2)

def _calculate_irradiance(time: datetime, lat: float, lon: float, cloud_cover: float) -> float:
    """
    Calculate solar irradiance based on position and cloud cover.
    
    Uses simplified model:
    I = I_max * time_factor * cloud_factor
    
    where:
    - I_max is theoretical clear sky irradiance
    - time_factor models daily sun position
    - cloud_factor reduces radiation based on cloud cover
    """
    hour = time.hour
    day_of_year = time.timetuple().tm_yday
    
    # Same day length calculation as in IAM
    solar_noon = 12
    annual_phase = 2 * np.pi * (day_of_year - 80) / 365
    day_length = 12 + 4 * np.sin(annual_phase)
    
    sunrise = solar_noon - day_length/2
    sunset = solar_noon + day_length/2
    
    if hour < sunrise or hour > sunset:
        return 0
    
    # Sun position effect (0-1)
    time_factor = np.sin(np.pi * (hour - sunrise) / (sunset - sunrise))
    
    # Cloud attenuation (0-1)
    cloud_factor = 1 - (cloud_cover / 100) * MAX_CLOUD_BLOCKING
    
    return MAX_THEORETICAL_IRRADIANCE * time_factor * cloud_factor
