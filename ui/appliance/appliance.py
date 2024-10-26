import numpy as np
from typing import Union, List, Tuple
MINUTES_IN_A_DAY = 24 * 60


class ApplianceUsageProfile:
    appliance_name: str
    # Time series of appliance usage(1 or 0) for a 24-hour period
    TimeSeries: np.ndarray
    resolution: int  # Resolution of the time series in minutes


class ApplianceStatistics:
    name: str
    mean_cycle_length: int  # Mean cycle length (min)
    min_cycle_length: int  # Minimum cycle length (min)
    # Mean time between event gets restarted(min)
    mean_time_between_restart: float
    min_time_between_restart: int  # Minimum time between restart (min)
    # Average energy consumption per minute (kWh)
    average_load_per_minute: float

    def sample_load_profile(self,
                            resolution: int,
                            occupancy: np.ndarray,
                            inactive_occupancy_times:
                                List[Tuple[int, int]] =
                                [(0, int(60*7), (60*23, 60*24))]) -> np.ndarray:
        """
        Args:
            resolution: Resolution of the load profile in minutes
            occupancy: Occupancy profile for the day. Number of occupants in the house at each time step. 
                Resolution of the occupancy profile should be the same as the resolution of the load profile.
            inactive_occupancy_times: List of tuples of start and end times of inactive occupancy periods(in minutes). 
                I.e when occupants are sleeping.
        """
        activity_mask = np.ones(MINUTES_IN_A_DAY//resolution)
        for start, end in inactive_occupancy_times:
            activity_mask[start//resolution:end//resolution] = 0
        # Mask out the inactive occupancy times
        occupancy = occupancy*activity_mask
        usage_profile = self.sample_usage_profile(resolution, occupancy)
        load_profile = usage_profile*self.average_load_per_minute*resolution
        return load_profile

    def sample_usage_profile(self,
                             resolution: int,
                             occupancy: np.ndarray,
                             seed: Union[int, None] = None) -> np.ndarray:
        if seed is not None:
            np.random.seed(seed)
        else:
            np.random.seed()
        """
        We use the geometric distribution to sample the time between two events.
        A more realistic model would use a CT-Markov process, together with a 
        MCMC method to sample the time series.
        The geometric distribution shares the memoryless property with the exponential
        distribution which is used for the CT-Markov process.
        """
        # Assume the appliance is off at the start
        state = 0
        mean_timesteps_between_restart = max(
            self.mean_time_between_restart/resolution, 1.0)
        # Don't allow a lengths of less than one resolution
        mean_timestep_cycle_length = max(
            self.mean_cycle_length/resolution, 1.0)
        usage_profile = np.zeros(MINUTES_IN_A_DAY//resolution)
        timestep = 0
        # Simulate for additional days for burn-in
        burn_in_days = 14
        while (timestep < (burn_in_days+1)*MINUTES_IN_A_DAY//resolution):
            timestep_local = np.mod(timestep, MINUTES_IN_A_DAY//resolution)
            if state == 0:
                valid_next_on_time = False
                while (not valid_next_on_time):
                    timesteps_until_next_on = np.random.geometric(
                        1.0/mean_timesteps_between_restart)
                    # Only allow the appliance to turn on if the occupancy is 1
                    if (occupancy[np.mod(timestep_local + timesteps_until_next_on,
                                         MINUTES_IN_A_DAY//resolution)] >= 1 and
                            timesteps_until_next_on*resolution >= self.min_time_between_restart):
                        valid_next_on_time = True
                if (timestep >= (burn_in_days)*MINUTES_IN_A_DAY//resolution):
                    usage_profile[timestep_local:
                                  max(timestep_local + timesteps_until_next_on, usage_profile.shape[0]-1)] = 0
                timestep += timesteps_until_next_on
                state = 1
            elif state == 1:
                valid_next_off_time = False
                while (not valid_next_off_time):
                    timesteps_until_next_off = np.random.geometric(
                        1.0/mean_timestep_cycle_length)
                    if (timesteps_until_next_off*resolution >= self.min_cycle_length):
                        valid_next_off_time = True
                timestep += timesteps_until_next_off
                if (timestep >= (burn_in_days)*MINUTES_IN_A_DAY//resolution):
                    usage_profile[timestep_local:
                                  max(timestep_local + timesteps_until_next_off, usage_profile.shape[0]-1)] = 1
                state = 0
        return usage_profile


class DishWasherStatistics(ApplianceStatistics):
    def __init__(self):
        self.name = "Dish Washer"
        self.mean_cycle_length = 90
        self.min_cycle_length = 30
        self.mean_time_between_restart = int(24*1.5*60)
        self.min_time_between_restart = 180
        self.average_load_per_minute = 2000*60/(1e3*3600)


class WashingMachineStatistics(ApplianceStatistics):
    def __init__(self):
        self.name = "Washing Machine"
        self.mean_cycle_length = 120
        self.min_cycle_length = 30
        self.mean_time_between_restart = int(24*1.5*60)
        self.min_time_between_restart = 180
        # average energy consumption per minute (kWh)
        self.average_load_per_minute = 2000*60/(1e3*3600)


class TumbleDryerStatistics(ApplianceStatistics):
    def __init__(self):
        self.name = "Tumble Dryer"
        self.mean_cycle_length = 60
        self.min_cycle_length = 30
        self.mean_time_between_restart = int(24*1.5*60)
        self.min_time_between_restart = 180
        # average energy consumption per minute (kWh)
        self.average_load_per_minute = 2000*60/(1e3*3600)


class OvenStatistics(ApplianceStatistics):
    def __init__(self):
        self.name = "Oven"
        self.mean_cycle_length = 20
        self.min_cycle_length = 0
        self.mean_time_between_restart = 12*60
        self.min_time_between_restart = 0
        # average energy consumption per minute (kWh)
        self.average_load_per_minute = 1000*60/(1e3*3600)


class ShowerStatistics(ApplianceStatistics):
    def __init__(self):
        self.name = "Shower"
        self.mean_cycle_length = 10
        self.min_cycle_length = 5
        self.mean_time_between_restart = int(24*1.5*60)
        self.min_time_between_restart = 0
        self.average_load_per_minute = 2000*60/(1e3*3600)