
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

from start_code_2024.ui.batteryOptimizer.optimize_battery_schedule import optimize_battery_schedule

def plot_result(spot_prices, load, pv_production, grid_power, soc):
    # Create time array for x-axis
    hours = list(range(24))
    
    # Create figure with subplots
    fig = plt.figure(figsize=(15, 10))
    gs = GridSpec(3, 1, height_ratios=[1, 1, 1], hspace=0.3)
    
    # Plot 1: Spot Price
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(hours, spot_prices, 'r-', label='Spot Price', marker='o')
    ax1.set_ylabel('Price ($/kWh)')
    ax1.set_title('24-Hour Battery Optimization Results')
    ax1.legend()
    ax1.grid(True)
    
    # Plot 2: Load and PV Production
    ax2 = fig.add_subplot(gs[1])
    ax2.plot(hours, load, 'b-', label='Load', marker='o')
    ax2.plot(hours, pv_production, 'g-', label='PV Production', marker='o')
    ax2.plot(hours, grid_power, 'r-', label='Grid Power', marker='o')
    ax2.set_ylabel('Power (kW)')
    ax2.legend()
    ax2.grid(True)
    
    # Plot 3: Battery State of Charge
    ax3 = fig.add_subplot(gs[2])
    ax3.plot(hours, soc, 'b-', label='State of Charge', marker='o')
    ax3.set_xlabel('Hour of Day')
    ax3.set_ylabel('Battery SOC (%)')
    ax3.set_ylim(0, 100)
    ax3.legend()
    ax3.grid(True)
    
    plt.show()

def main():
    # Example data for a 24-hour period
    battery_capacity = 13.5  # kWh (Tesla Powerwall size)
    charge_rate = 2.0  # kW
    initial_soc = 50  # Start at 50% charge
    
    # Generate example spot prices with peak in morning and evening
    spot_prices = [
        0.10, 0.09, 0.08, 0.08, 0.09, 0.15,  # 00:00 - 05:00
        0.20, 0.25, 0.22, 0.18, 0.15, 0.12,  # 06:00 - 11:00
        0.11, 0.10, 0.12, 0.14, 0.18, 0.25,  # 12:00 - 17:00
        0.28, 0.22, 0.18, 0.15, 0.12, 0.11   # 18:00 - 23:00
    ]
    
    # Generate example load profile
    predicted_load = [
        0.8, 0.6, 0.5, 0.4, 0.4, 0.6,  # Night/early morning
        1.2, 2.0, 2.5, 2.0, 1.8, 1.5,  # Morning peak
        1.3, 1.2, 1.4, 1.6, 2.0, 2.8,  # Afternoon/evening
        3.0, 2.5, 2.0, 1.5, 1.2, 1.0   # Evening/night
    ]
    
    # Generate example PV production
    predicted_pv_production = [
        0.0, 0.0, 0.0, 0.0, 0.0, 0.1,  # Night/dawn
        0.3, 1.0, 2.5, 3.8, 4.5, 4.8,  # Morning/noon
        4.6, 4.2, 3.5, 2.5, 1.2, 0.3,  # Afternoon/dusk
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0   # Night
    ]
    
    # Run optimization
    soc, grid_power = optimize_battery_schedule(
        battery_capacity,
        charge_rate,
        spot_prices,
        predicted_load,
        predicted_pv_production,
        initial_soc
    )

    # Uncomment line below for plot
    # plot_result(spot_prices, load, pv_production, grid_power, soc)
    
  

if __name__ == "__main__":
    main()