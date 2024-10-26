import pytest
from appliance_load_profiles.appliance import ApplianceStatistics
import numpy as np

mean_cycle_length = 10
min_cycle_length = 0
mean_time_between_restart = 10
appliance = ApplianceStatistics(
    name="test",
    mean_cycle_length=mean_cycle_length,
    min_cycle_length=min_cycle_length,
    mean_time_between_restart=mean_time_between_restart
)
occupancy = np.array([1]*24*60)
sum_on_time = 0
resolution = 15
num_times_on = 0
sum_off_time = 0
num_times_off = 0
for _ in range(int(1e5)):
    usage_profile = appliance.sample_usage_profile(resolution, occupancy)
    sum_on_time += np.sum(usage_profile)*resolution
    # Count the number of times the appliance turns on, which is
    # the number of times the difference between two consecutive
    # elements is -1. I.e. it goes from 0 to 1
    num_times_on += np.sum(np.diff(usage_profile) == 1)
    sum_off_time += np.sum((1-usage_profile)*resolution)
    # Count the number of times the appliance turns off, which is
    # the number of times the difference between two consecutive
    # elements is 1. I.e. it goes from 1 to 0
    num_times_off += np.sum(np.diff(usage_profile) == -1)


def test_appliance_samples_cycle_length():
    assert pytest.approx(sum_on_time/num_times_on,
                         5) == appliance.mean_cycle_length


def test_appliance_samples_time_between_restart():
    assert pytest.approx(sum_off_time/num_times_off,
                         5) == appliance.mean_time_between_restart
