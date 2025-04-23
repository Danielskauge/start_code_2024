# EnergyOptAI 🌞

> Built at Start Code Hackathon 2024 - Smart energy optimization for a sustainable future

EnergyOptAI is an advanced building energy system simulator that helps property owners optimize their energy usage through AI-powered predictions and real-time price optimization. It combines solar generation, battery storage, and consumption patterns to reduce costs and carbon footprint.

## 🚀 Key Features

- **Smart Energy Simulation**: Advanced modeling of building energy consumption using the CREST model and Markov chains
- **Solar Generation Forecasting**: Precise solar panel output prediction based on weather, location, and panel specifications
- **Battery Optimization**: AI-powered battery charge/discharge scheduling using spot price optimization
- **Real-time Price Integration**: Dynamic optimization based on current electricity spot prices
- **Interactive Visualization**: Rich data visualization for energy flows and cost savings

## 🛠️ Technical Stack

- **Core Engine**: Python-based simulation engine with modular architecture
- **Optimization**: Linear programming for battery charge/discharge scheduling
- **Data Sources**: 
  - Weather API integration for solar forecasting
  - Real-time electricity spot price data
  - Building-specific consumption patterns
- **Visualization**: Interactive dashboards for energy flow analysis


## 💡 Usage

Basic simulation:
```python
from src.simulation import simulate_building
from src.building import Building

# Configure your building
building = Building(
    solar_capacity=10.0,  # kW
    battery_capacity=13.5,  # kWh
    location=(60.472024, 8.468946)  # Oslo
)

# Run simulation
results = simulate_building(building, days=7)
```

## 🎯 Impact

- **Cost Reduction**: Saves costs on electricity bills through smart battery optimization
- **Grid Load**: Reduces peak load on the power grid
- **Green Energy**: Maximizes utilization of solar energy
- **ROI Analysis**: Helps property owners make data-driven decisions on energy investments
