from typing import List
from ui.heatModule.buildingHeatLoss import BuildingHeatLoss

class HeatingSystem:
    def __init__(self, building: BuildingHeatLoss, COP: float, min_Q_heating: float, max_Q_heating: float, controller:str = "PID"):
        self.building = building
        self.COP = COP
        self.min_Q_heating = min_Q_heating
        self.max_Q_heating = max_Q_heating
        self.dt = 1
        self.controller = controller

        # PID controller
        self.integral = 0
        self.previous_error = 0

        self.Kp = 10.0  
        self.Ki = 0.05  
        self.Kd = 5.0   

    def heat_control(self, temperature_setpoint: float, temperature_inside: float):
        if self.controller == "PID":
            error = temperature_setpoint - temperature_inside
            self.integral += error * self.dt

            derivative = (error - self.previous_error) / self.dt
            output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
            Q_heating = max(min(output, self.max_Q_heating), self.min_Q_heating)
            
            self.previous_error = error
        elif self.controller == "on_off":
            if temperature_inside < temperature_setpoint:
                Q_heating = self.max_Q_heating
            else:
                Q_heating = 0
        else:
            raise ValueError(f"Invalid controller: {self.controller}")
        return Q_heating

    def heat_pump(self, temperature_setpoint: float, temperature_inside: float, temperature_outside: float, internal_heat_gain: float = 0, dt: float = 1):
        delta_T = temperature_inside - temperature_outside
        Q_loss = self.building.calculate_total_heat_loss(delta_T)
        Q_heating = self.heat_control(temperature_setpoint, temperature_inside)

        # Adjust net heat flow with internal gains
        Q_net = Q_heating - Q_loss + internal_heat_gain
        dT = (Q_net * self.dt) / self.building.calculate_thermal_mass()
        new_temperature = temperature_inside + dT
        E_electrical = Q_heating / self.COP

        return E_electrical, new_temperature, Q_heating, Q_loss

    def simulate_heating(self, temperatures_outside: List[float], temperature_setpoints: List[float], initial_temperature_inside: float, internal_heat_gains: List[float] = None):
        # Ensure we have 24 hours of data
        assert len(temperatures_outside) == 24, "Must provide 24 hours of outside temperatures"
        assert len(temperature_setpoints) == 24, "Must provide 24 hours of temperature setpoints"

        # Ensure internal_heat_gains is provided
        if internal_heat_gains is None:
            internal_heat_gains = [0] * 24

        temperatures_inside = [initial_temperature_inside]
        energy_consumption_per_hour = []
        Q_heating_per_hour = []
        Q_loss_per_hour = []

        for hour in range(24):
            E_electrical, new_temperature, Q_heating, Q_loss = self.heat_pump(
                temperature_setpoints[hour],
                temperatures_inside[-1],
                temperatures_outside[hour],
                internal_heat_gain=internal_heat_gains[hour]
            )
            
            temperatures_inside.append(new_temperature)
            energy_consumption_per_hour.append(E_electrical)
            Q_heating_per_hour.append(Q_heating)
            Q_loss_per_hour.append(Q_loss)

        return temperatures_inside, energy_consumption_per_hour, Q_heating_per_hour, Q_loss_per_hour
