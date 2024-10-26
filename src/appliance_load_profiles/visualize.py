"""
Visualize some generated appliance load profiles.
"""

import matplotlib.pyplot as plt
import numpy as np
from appliance import (
    DishWasherStatistics,
    WashingMachineStatistics,
    TumbleDryerStatistics,
    OvenStatistics
)

dish_washer = DishWasherStatistics()
washing_machine = WashingMachineStatistics()
tumble_dryer = TumbleDryerStatistics()
oven = OvenStatistics()

# Generate appliance load profiles
resolution = 60
occupancy = np.zeros(24*60//resolution)
occupancy[6*60//resolution:7*60//resolution] = 1
occupancy[17*60//resolution:] = 1


dish_washer_profile = dish_washer.sample_load_profile(resolution, occupancy)
washing_machine_profile = washing_machine.sample_load_profile(
    resolution, occupancy)
tumble_dryer_profile = tumble_dryer.sample_load_profile(resolution, occupancy)
oven_profile = oven.sample_load_profile(resolution, occupancy)

hours = np.arange(0, 24)
plt.suptitle("Appliance Load Profiles")
plt.subplot(2, 2, 1)
plt.bar(hours, dish_washer_profile, label="Dish Washer")
plt.title("Dish Washer load profile")
plt.xlabel("Time (60 minute intervals)")
plt.ylabel("Power Consumption (kW)")
plt.grid()

plt.subplot(2, 2, 2)
plt.bar(hours, washing_machine_profile, label="Washing Machine")
plt.title("Washing Machine load profile")
plt.xlabel("Time (60 minute intervals)")
plt.ylabel("Power Consumption (kW)")
plt.grid()

plt.subplot(2, 2, 3)
plt.bar(hours, tumble_dryer_profile, label="Tumble Dryer")
plt.title("Tumble Dryer load profile")
plt.xlabel("Time (60 minute intervals)")
plt.ylabel("Power Consumption (kW)")
plt.grid()

plt.subplot(2, 2, 4)
plt.bar(hours, oven_profile, label="Oven")
plt.title("Oven load profile")
plt.xlabel("Time (60 minute intervals)")
plt.ylabel("Power Consumption (kW)")
plt.grid()

plt.tight_layout()
plt.show()

total_profile = dish_washer_profile + \
    washing_machine_profile + tumble_dryer_profile + oven_profile
plt.bar(hours, total_profile, label="Total")
plt.title("Total load profile")
plt.xlabel("Time (60 minute intervals)")
plt.ylabel("Power Consumption (kW)")
plt.grid()
plt.show()
