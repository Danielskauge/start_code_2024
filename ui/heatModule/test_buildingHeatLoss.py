from buildingHeatLoss import BuildingHeatLoss

def test_real_world_example():
    # Example 1: Small house
    small_house = BuildingHeatLoss(
        length=8,
        width=6,
        wall_height=2.4,
        glazing_ratio=0.15,
        num_windows=4,
        num_doors=1,
        roof_type="gable",
        roof_pitch=35
    )

    # Example 2: Large house
    large_house = BuildingHeatLoss(
        length=15,
        width=12,
        wall_height=2.7,
        glazing_ratio=0.20,
        num_windows=8,
        num_doors=2,
        roof_type="hip",
        roof_pitch=40
    )

    # Test temperature differences
    delta_Ts = [5, 10, 20, 30]  # Different temperature scenarios

    print("\nHeat Loss Comparison (kWh/h):")
    print("-" * 50)
    for delta_T in delta_Ts:
        small_loss = small_house.calculate_total_heat_loss(delta_T)
        large_loss = large_house.calculate_total_heat_loss(delta_T)
        
        print(f"\nTemperature difference: {delta_T}°C")
        print(f"Small house heat loss: {small_loss:.3f} kWh/h")
        print(f"Large house heat loss: {large_loss:.3f} kWh/h")
        print(f"Ratio (large/small): {large_loss/small_loss:.2f}")

    # Detailed breakdown for one scenario
    delta_T = 20
    print("\nDetailed Breakdown (ΔT = 20°C) in kWh/h:")
    print("-" * 50)
    
    for house, name in [(small_house, "Small House"), (large_house, "Large House")]:
        print(f"\n{name}:")
        
        # Transmission losses
        trans = house.calculate_heat_transmission(delta_T)
        print("Transmission Losses:")
        for key, value in trans.items():
            if key != "Q_transmission" and key != "Q_transmission_kWh_h":
                print(f"  {key}: {value/1000:.3f} kWh/h")
            if key == "Q_transmission_kWh_h":
                print(f"  Total: {value:.3f} kWh/h")
                
        # Ventilation losses
        vent = house.calculate_ventilation_heat_loss(delta_T)
        print("Ventilation Losses:")
        print(f"  Ventilation: {vent['Q_ventilation']/3600000:.3f} kWh/h")
        print(f"  Infiltration: {vent['Q_infiltration']/3600000:.3f} kWh/h")
        print(f"  Total: {vent['Q_ventilation_heat_loss_kWh_h']:.3f} kWh/h")
        
        # Thermal bridge losses
        bridge = house.calculate_thermal_bridge_loss(delta_T)
        print("Thermal Bridge Losses:")
        for bridge_type, loss in bridge['breakdown_kWh_h'].items():
            print(f"  {bridge_type}: {loss:.3f} kWh/h")

if __name__ == "__main__":
    test_real_world_example()