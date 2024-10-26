import matplotlib.pyplot as plt
from heatingModule import BuildingHeatLoss, HeatingSystem

def main():
    # Create a sample building
    building = BuildingHeatLoss(
        length=8,
        width=6,
        wall_height=2.4,
        glazing_ratio=0.15,
        num_windows=4,
        num_doors=1,
        roof_type="gable",
        roof_pitch=35
    )

    # Sample data for 24 hours
    temperatures_outside = [5, 4, 3, 2, 1, 0, 1, 2, 4, 6, 8, 10, 12, 13, 14, 15, 14, 13, 11, 9, 8, 7, 6, 5]
    temperature_setpoints = [20] * 24  # Constant setpoint of 20°C

    # Simulation parameters
    initial_temperature_inside = 18  # °C
    COP = 3.5
    min_Q_heating = 0  # kW
    max_Q_heating = 5  # kW 

    # Create HeatingSystem instance
    heating_system = HeatingSystem(building, COP, min_Q_heating, max_Q_heating)

    # Run simulation
    temperatures_inside, energy_consumption, Q_heating, Q_loss = heating_system.simulate_heating(
        temperatures_outside,
        temperature_setpoints,
        initial_temperature_inside
    )

    # Plotting
    hours = list(range(25))  # 0 to 24

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12))

    # Temperature plot
    ax1.plot(hours, temperatures_inside, label='Inside Temperature')
    ax1.plot(hours[:-1], temperatures_outside, label='Outside Temperature')
    ax1.plot(hours[:-1], temperature_setpoints, label='Setpoint', linestyle='--')
    ax1.set_xlabel('Hour')
    ax1.set_ylabel('Temperature (°C)')
    ax1.set_title('Temperature Variation')
    ax1.legend()
    ax1.grid(True)

    # Energy consumption plot
    ax2.bar(hours[:-1], energy_consumption)
    ax2.set_xlabel('Hour')
    ax2.set_ylabel('Energy Consumption (Wh)')
    ax2.set_title('Hourly Energy Consumption')
    ax2.grid(True)

    # Heat flow plot
    ax3.plot(hours[:-1], Q_heating, label='Heat Pump Output')
    ax3.plot(hours[:-1], Q_loss, label='Heat Loss')
    ax3.set_xlabel('Hour')
    ax3.set_ylabel('Heat Flow (W)')
    ax3.set_title('Heat Pump Output vs. Heat Loss')
    ax3.legend()
    ax3.grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()