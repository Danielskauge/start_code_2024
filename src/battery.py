from typing import List, Tuple
import numpy as np

def optimize_battery(
    battery_capacity_kwh: float,
    battery_charge_rate_kw: float,
    spot_prices: List[float],
    load_kwh: List[float],
    pv_production_kwh: List[float],
    initial_soc: float = 50.0
) -> Tuple[List[float], List[float]]:
    """
    Optimizes battery charging/discharging schedule based on spot prices.
    
    Args:
        battery_capacity_kwh: Total battery capacity in kWh
        battery_charge_rate_kw: Maximum charge/discharge rate in kW
        spot_prices: Hourly spot prices for next day
        load_kwh: Predicted hourly load demand in kWh
        pv_production_kwh: Predicted hourly PV production in kWh
        initial_soc: Initial battery state of charge (%)
    
    Returns:
        Tuple[List[float], List[float]]: Lists of hourly state of charge (%) 
        and grid power (kW, positive = from grid, negative = to grid)
    """
    hours = len(spot_prices)
    state_of_charge = [0] * hours
    power_from_grid = [0] * hours
    
    # Calculate price thresholds for charging/discharging
    avg_price = sum(spot_prices) / len(spot_prices)
    charge_threshold = avg_price * 0.9    # Charge when price is below 90% of average
    discharge_threshold = avg_price * 1.1  # Discharge when price is above 110% of average
    
    # Initialize first hour
    net_load = load_kwh[0] - pv_production_kwh[0]
    state_of_charge[0] = initial_soc
    
    # Determine first hour operation
    if spot_prices[0] <= charge_threshold and initial_soc < 90:
        max_charge = min(
            battery_charge_rate_kw,
            (battery_capacity_kwh * (100 - initial_soc) / 100)
        )
        charge_power = min(max_charge, battery_charge_rate_kw)
        power_from_grid[0] = net_load + charge_power
        state_of_charge[0] = initial_soc + (charge_power / battery_capacity_kwh * 100)
        
    elif spot_prices[0] >= discharge_threshold and initial_soc > 10:
        max_discharge = min(
            battery_charge_rate_kw,
            (battery_capacity_kwh * initial_soc / 100)
        )
        discharge_power = min(max_discharge, net_load)
        power_from_grid[0] = net_load - discharge_power
        state_of_charge[0] = initial_soc - (discharge_power / battery_capacity_kwh * 100)
        
    else:
        power_from_grid[0] = net_load
        state_of_charge[0] = initial_soc
    
    # Optimize remaining hours
    for hour in range(1, hours):
        prev_soc = state_of_charge[hour-1]
        net_load = load_kwh[hour] - pv_production_kwh[hour]
        current_price = spot_prices[hour]
        
        max_charge = min(
            battery_charge_rate_kw,
            (battery_capacity_kwh * (100 - prev_soc) / 100)
        )
        max_discharge = min(
            battery_charge_rate_kw,
            (battery_capacity_kwh * prev_soc / 100)
        )
        
        if current_price <= charge_threshold and prev_soc < 90:
            charge_power = min(max_charge, battery_charge_rate_kw)
            power_from_grid[hour] = net_load + charge_power
            state_of_charge[hour] = prev_soc + (charge_power / battery_capacity_kwh * 100)
            
        elif current_price >= discharge_threshold and prev_soc > 10:
            discharge_power = min(max_discharge, net_load)
            power_from_grid[hour] = net_load - discharge_power
            state_of_charge[hour] = prev_soc - (discharge_power / battery_capacity_kwh * 100)
            
        else:
            power_from_grid[hour] = net_load
            state_of_charge[hour] = prev_soc
        
        state_of_charge[hour] = max(0, min(100, state_of_charge[hour]))
    
    return state_of_charge, power_from_grid
