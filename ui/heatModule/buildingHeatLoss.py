import math


class BuildingHeatLoss:
    def __init__(
        self,
        length,
        width,
        wall_height,
        glazing_ratio,
        num_windows,
        num_doors,
        roof_type,
        roof_pitch=0,
        wall_u_value=0.18,
        floor_u_value=0.10,
        roof_u_value=0.13,
        window_u_value=0.8,
        door_u_value=0.8,
        ventilation_rate=0.7,
        air_leakage_rate=0.1,
        wall_material="timber_frame",
        floor_material="timber",
        roof_material="timber_joist",
    ):
        # All u_values is the minimum critera for TEK17
        # https://www.dibk.no/verktoy-og-veivisere/energi/dette-er-energikravene-i-byggteknisk-forskrift

        self.length = length
        self.width = width
        self.roof_height = wall_height
        self.roof_type = roof_type
        self.roof_pitch = roof_pitch

        self.wall_material = wall_material
        self.floor_material = floor_material
        self.roof_material = roof_material

        self.wall_area = 2 * (length + width) * wall_height
        self.wall_u_value = wall_u_value

        self.floor_area = length * width
        self.floor_u_value = floor_u_value

        if roof_type == "flat":
            self.roof_area = length * width
        elif roof_type == "gable":
            pitch_rad = math.radians(roof_pitch)
            roof_width = width / math.cos(pitch_rad)
            self.roof_area = 2 * length * roof_width
        elif roof_type == "shed":
            pitch_rad = math.radians(roof_pitch)
            roof_width = width / math.cos(pitch_rad)
            self.roof_area = length * roof_width
        elif roof_type == "hip":
            pitch_rad = math.radians(roof_pitch)
            roof_width = width / math.cos(pitch_rad)
            roof_length = length / math.cos(pitch_rad)
            self.roof_area = roof_width * roof_length
        else:
            raise ValueError(f"Invalid roof type: {roof_type}")
        self.roof_u_value = roof_u_value

        # Calculate total height including roof
        if roof_type == "flat":
            self.total_height = wall_height
        elif roof_type in ["gable", "hip"]:
            self.total_height = wall_height + (width / 2) * math.tan(
                math.radians(roof_pitch)
            )
        elif roof_type == "shed":
            self.total_height = wall_height + width * math.tan(math.radians(roof_pitch))
        self.total_volume = length * width * self.total_height

        self.glazing_ratio = glazing_ratio
        self.num_windows = num_windows
        self.window_area = self.wall_area * self.glazing_ratio
        self.window_u_value = window_u_value

        self.num_doors = num_doors
        self.door_height = 2.033  # m
        self.door_width = 0.925  # m
        self.door_area = self.door_height * self.door_width
        self.total_door_area = self.num_doors * self.door_area
        self.door_u_value = door_u_value

        self.ventilation_rate = ventilation_rate
        self.air_leakage_rate = air_leakage_rate

        # Initialize thermal bridge properties
        self.thermal_bridge_psi_values = []  # Psi-values for each thermal bridge (W/(m·K))
        self.thermal_bridge_lengths = []

    def calculate_heat_transmission(self, delta_T):
        wall_transmission = self.wall_u_value * self.wall_area * delta_T

        roof_transmission = self.roof_u_value * self.roof_area * delta_T

        door_transmission = self.door_u_value * self.total_door_area * delta_T

        floor_transmission = self.floor_u_value * self.floor_area * delta_T

        # Total transmission in Watts
        Q_transmission = (
            wall_transmission
            + roof_transmission
            + door_transmission
            + floor_transmission
        )

        # Convert total transmission to kWh/h
        Q_transmission_kWh_h = Q_transmission / 1000  # Convert Watts to kW

        return {
            "wall_transmission": wall_transmission,
            "roof_transmission": roof_transmission,
            "door_transmission": door_transmission,
            "floor_transmission": floor_transmission,
            "Q_transmission": Q_transmission,
            "Q_transmission_kWh_h": Q_transmission_kWh_h,  # Total in kWh/h
        }

    def calculate_ventilation_rate(self):
        return self.ventilation_rate * self.floor_area

    def calculate_infiltration_rate(self):
        return self.air_leakage_rate * self.total_volume

    def calculate_ventilation_heat_loss(self, delta_T):
        C_air = 1005  # J/(kg*K)
        rho_air = 1.2  # kg/m³

        # Calculate heat loss in Watts
        Q_ventilation = self.calculate_ventilation_rate() * C_air * rho_air * delta_T
        Q_infiltration = self.calculate_infiltration_rate() * C_air * rho_air * delta_T
        Q_ventilation_heat_loss = Q_ventilation + Q_infiltration  # j/s

        # Convert total heat loss to kWh/h
        Q_ventilation_heat_loss_kWh_h = (
            Q_ventilation_heat_loss / 3600000
        )  # Convert Watts to kW/h

        return {
            "Q_ventilation": Q_ventilation,
            "Q_infiltration": Q_infiltration,
            "Q_ventilation_heat_loss": Q_ventilation_heat_loss,
            "Q_ventilation_heat_loss_kWh_h": Q_ventilation_heat_loss_kWh_h,  # Total in kWh/h
        }

    def estimate_thermal_bridges(self):
        # Calculate window dimensions (assuming square windows)
        window_side_length = math.sqrt(self.window_area / self.num_windows)

        # Define psi values (W/mK) according to TEK17
        psi_values = {
            "window": 0.03,
            "door": 0.03,
            "roof": 0.06,
            "floor": 0.07,
            "corner": 0.04,
        }

        # Calculate lengths and store in dictionary with (psi, length) tuples
        thermal_bridges = {
            "window": (psi_values["window"], 4 * window_side_length * self.num_windows),
            "door": (
                psi_values["door"],
                2 * (self.door_height + self.door_width) * self.num_doors,
            ),
            "floor": (psi_values["floor"], 2 * (self.length + self.width)),
            "corner": (psi_values["corner"], 4 * self.total_height),
        }

        # Calculate roof junction based on roof type
        if self.roof_type == "flat":
            roof_length = 2 * (self.length + self.width)
        elif self.roof_type == "gable":
            roof_length = 2 * (self.length + self.width) + self.length
        elif self.roof_type == "hip":
            roof_length = 2 * (self.length + self.width) + 4 * math.sqrt(
                (self.length / 2) ** 2 + (self.width / 2) ** 2
            )
        elif self.roof_type == "shed":
            roof_length = 2 * (self.length + self.width)

        thermal_bridges["roof"] = (psi_values["roof"], roof_length)

        # Store values for use in other methods
        self.thermal_bridge_lengths = [v[1] for v in thermal_bridges.values()]
        self.thermal_bridge_psi_values = [v[0] for v in thermal_bridges.values()]

        return thermal_bridges

    def calculate_thermal_bridge_loss(self, delta_T):
        thermal_bridges = self.estimate_thermal_bridges()
        Q_thermal_bridge = sum(
            psi * length * delta_T for psi, length in thermal_bridges.values()
        )

        losses = {
            bridge_type: (psi * length * delta_T)
            for bridge_type, (psi, length) in thermal_bridges.items()
        }

        # Convert W to kWh/h
        Q_thermal_bridge_kwh_h = Q_thermal_bridge / 1000
        losses_kwh_h = {k: v / 1000 for k, v in losses.items()}

        return {
            "total_W": Q_thermal_bridge,
            "total_kWh_h": Q_thermal_bridge_kwh_h,
            "breakdown_W": losses,
            "breakdown_kWh_h": losses_kwh_h,
        }

    def calculate_total_heat_loss(self, delta_T):
        Q_transmission = self.calculate_heat_transmission(delta_T)[
            "Q_transmission_kWh_h"
        ]
        Q_ventilation_heat_loss = self.calculate_ventilation_heat_loss(delta_T)[
            "Q_ventilation_heat_loss_kWh_h"
        ]
        Q_thermal_bridge = self.calculate_thermal_bridge_loss(delta_T)["total_kWh_h"]

        Q_total = Q_transmission + Q_ventilation_heat_loss + Q_thermal_bridge
        return Q_total
    
    def calculate_thermal_mass(self):

        # Thermal mass values for different materials
        thermal_mass_values = {
            # Wall materials (kJ/m²K for typical thicknesses)
            'wall': {
                'timber_frame': 110,      # 150mm timber frame with plasterboard
                'brick': 190,             # 220mm solid brick
                'cavity_brick': 150,      # Double brick with cavity
                'concrete_block': 170,    # 200mm concrete block
                'stone': 250,             # 500mm stone wall
                'light_steel': 120,       # Light steel frame with cladding
                'log': 160,               # 200mm solid wood
            },
            
            # Floor materials (kJ/m²K for typical thicknesses)
            'floor': {
                'timber': 70,             # Suspended timber floor
                'concrete_slab': 180,     # 150mm concrete slab
                'concrete_screed': 110,   # 75mm screed on insulation
                'raised_access': 60,      # Raised access floor
            },
            
            # Roof materials (kJ/m²K for typical thicknesses)
            'roof': {
                'timber_joist': 100,      # Traditional timber joist roof
                'concrete_deck': 140,     # Concrete deck flat roof
                'metal_deck': 80,         # Metal deck with insulation
                'green_roof': 170,        # Intensive green roof system
            },
        }

        rho_air = 1.2  # kg/m³
        C_air = 1005  # J/(kg*K)

        wall_thermal_mass = self.wall_area * thermal_mass_values['wall'][self.wall_material] * 1000
        floor_thermal_mass = self.floor_area * thermal_mass_values['floor'][self.floor_material] * 1000
        roof_thermal_mass = self.roof_area * thermal_mass_values['roof'][self.roof_material] * 1000
        air_thermal_mass = self.total_volume * rho_air * C_air


        thermal_mass = air_thermal_mass + wall_thermal_mass + floor_thermal_mass + roof_thermal_mass

        thermal_mass_kwh_k = thermal_mass / 3600000

        return thermal_mass_kwh_k

    def __str__(self):
        return (
            f"House Properties:\n"
            f"  Wall Area: {self.wall_area:.2f} m²\n"
            f"  Floor Area: {self.floor_area:.2f} m²\n"
            f"  Roof Area: {self.roof_area:.2f} m²\n"
            f"  Total Height: {self.total_height:.2f} m\n"
            f"  Window Area: {self.window_area:.2f} m²\n"
            f"  Door Area: {self.total_door_area:.2f} m²\n"
            f"  Total Volume: {self.total_volume:.2f} m³\n"
            f"  Roof Type: {self.roof_type}\n"
            f"  Roof Pitch: {self.roof_pitch}°"
        )

    def update_property(self, property_name, new_value):
        if hasattr(self, property_name):
            setattr(self, property_name, new_value)
            print(f"Updated {property_name} to {new_value}")
        else:
            print(f"Property {property_name} not found")
