# start_code_2024

# Building Energy System Simulator

A Python simulator for building energy systems with solar panels and battery storage. Simulates power consumption, solar generation, and optimizes battery usage based on spot prices.

## Installation


## Checks
- [x] Check that im using api within terms of service
- [x] Look at weather data, check that all calculations are correct
- [ ] Check that CREST model is correct, wrt markov probabilities


- simplify occupancy profiles, into one value per hour, but night, day, evening, morning
- occupancy profiles should be specific to building type
- input to simulate_consumption should be a building object, a time range, and weather data for that time range. is_weekend should be calculated from the timestamps within the simulation.


## TODOs

- Make UI
    - 

- check that this can run in a docker container
- add grid tariff of the building to the pricing calculation
- add functionality for running a simulation with settings from a json file
- 

- improve solar simulation accuracy
- Calcuation of saved costs with battery optimization vs not
    - add to export
- Ingegrate with martins code
- UI
    - Cration of a building
    - Selection of user scenario
    - Selection of simulation parameters 
    - Running the simulation
    - Visualizing with graphs
        - Simulated data
        - Optimization results
        - Spot prices
        - Consumption
        - Solar generation
        - Battery state of charge
- Improved battery optimization algorithm

### Core Functionality & Correctness
- [ ] Implement proper solar angle calculations based on latitude/longitude
- [ ] Add temperature effects on solar panel efficiency
- [ ] Include battery charging/discharging efficiency losses
- [ ] Add proper error handling for API calls
- [ ] Validate CREST model parameters against real consumption data
- [ ] Add input validation and bounds checking
- [ ] Implement proper weather API parsing instead of synthetic data
- [ ] Add tests for core calculations

### Optimization & Performance
- [ ] Implement proper battery optimization using linear programming
- [ ] Add multi-day forecasting and optimization
- [ ] Cache weather API results
- [ ] Parallelize simulations for parameter sweeps
- [ ] Profile and optimize computation bottlenecks

### Features & Enhancements
- [ ] Add GUI for parameter adjustment
- [ ] Implement real-time spot price API integration
- [ ] Add export of simulation results to CSV/Excel
- [ ] Create more sophisticated consumption profiles
- [ ] Add solar panel shading model
- [ ] Include battery degradation model
- [ ] Add economic analysis (ROI, payback period)
- [ ] Create configuration file support
- [ ] Add logging system

### Documentation & Analysis
- [ ] Add detailed API documentation
- [ ] Create example notebooks
- [ ] Add performance benchmarks
- [ ] Document model assumptions and limitations
- [ ] Add validation against real building data
- [ ] Create user guide with typical usage patterns
