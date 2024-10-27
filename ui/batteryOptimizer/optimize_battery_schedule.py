
def optimize_battery_schedule(battery_capacity_kWh, battery_charge_rate_kW, spot_price, load_kWh, pv_production_kWh, init_battery_soc):
    """
    Optimizes battery charging/discharging schedule based on spot prices.
    
    Args:
        battery_capacity_kWh (float): Total battery capacity in kWh
        battery_charge_rate_kW (float): Maximum charge/discharge rate in kW
        spot_price (list): Hourly spot prices
        load_kWh (list): Hourly load demand in kWh
        pv_production_kWh (list): Hourly PV production in kWh
        init_battery_soc (float): Initial battery state of charge (%)
    
    Returns:
        tuple: Lists of hourly state of charge (%) and grid power (kW)
    """
    # [Previous function implementation goes here]
    hours = len(spot_price)
    state_of_charge = [0] * hours  # % of battery capacity
    power_from_grid = [0] * hours  # kW (positive = charging, negative = discharging)
    
    # Calculate price thresholds for charging/discharging
    avg_price = sum(spot_price) / len(spot_price)
    charge_threshold = avg_price * 0.9  # Charge when price is below 90% of average
    discharge_threshold = avg_price * 1.1  # Discharge when price is above 110% of average
    
    # Initialize first hour with provided initial SOC
    net_load = load_kWh[0] - pv_production_kWh[0]
    state_of_charge[0] = init_battery_soc
    
    # Determine first hour operation based on initial conditions
    if spot_price[0] <= charge_threshold and init_battery_soc < 90:
        max_charge = min(
            battery_charge_rate_kW,
            (battery_capacity_kWh * (100 - init_battery_soc) / 100)
        )
        charge_power = min(max_charge, battery_charge_rate_kW)
        power_from_grid[0] = net_load + charge_power
        state_of_charge[0] = init_battery_soc + (charge_power / battery_capacity_kWh * 100)
        
    elif spot_price[0] >= discharge_threshold and init_battery_soc > 10:
        max_discharge = min(
            battery_charge_rate_kW,
            (battery_capacity_kWh * init_battery_soc / 100)
        )
        discharge_power = min(max_discharge, net_load)
        power_from_grid[0] = net_load - discharge_power
        state_of_charge[0] = init_battery_soc - (discharge_power / battery_capacity_kWh * 100)
        
    else:
        power_from_grid[0] = net_load
        state_of_charge[0] = init_battery_soc
    
    for hour in range(1, hours):
        prev_soc = state_of_charge[hour-1]
        net_load = load_kWh[hour] - pv_production_kWh[hour]
        current_price = spot_price[hour]
        
        max_charge = min(
            battery_charge_rate_kW,
            (battery_capacity_kWh * (100 - prev_soc) / 100)
        )
        max_discharge = min(
            battery_charge_rate_kW,
            (battery_capacity_kWh * prev_soc / 100)
        )
        
        if current_price <= charge_threshold and prev_soc < 90:
            charge_power = min(max_charge, battery_charge_rate_kW)
            power_from_grid[hour] = net_load + charge_power
            state_of_charge[hour] = prev_soc + (charge_power / battery_capacity_kWh * 100)
            
        elif current_price >= discharge_threshold and prev_soc > 10:
            discharge_power = min(max_discharge, net_load)
            power_from_grid[hour] = net_load - discharge_power
            state_of_charge[hour] = prev_soc - (discharge_power / battery_capacity_kWh * 100)
            
        else:
            power_from_grid[hour] = net_load
            state_of_charge[hour] = prev_soc
        
        state_of_charge[hour] = max(0, min(100, state_of_charge[hour]))
    
    return state_of_charge, power_from_grid