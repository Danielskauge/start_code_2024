import dash
from dash import html, dcc, callback_context
import dash_leaflet as dl
import plotly.graph_objs as go
import logging
from dash.dependencies import Input, Output, State, ALL
from simulation import get_simulation_results
from fetchers import get_location_name
import numpy as np
import requests  # Import to handle API requests

logger = logging.getLogger(__name__)

external_stylesheets = [
    "https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css"
]


class EnergySimulationDashboard:
    def __init__(self):
        self.app = dash.Dash(
            __name__, external_stylesheets=external_stylesheets)
        self.apartments = []
        self.selected_location = None
        self.expanded_view = False
        self.current_apartment = None
        self.client_locations = []

        # Initialize layout and callbacks
        self.setup_layout()
        self.setup_callbacks()
        self.fetch_client_data()

    def setup_layout(self):
        """Setup the dashboard layout."""
        self.app.index_string = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            {%metas%}
            <title>Energy Simulation Dashboard</title>
            {%favicon%}
            {%css%}
        </head>
        <body class="bg-gray-900 text-white">
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
        </html>
        '''

        # Define the main layout structure
        self.app.layout = html.Div(className="flex flex-col lg:flex-row h-screen bg-gray-900 text-white", children=[
            self.create_sidebar(),
            self.create_main_content()
        ])

    def create_sidebar(self):
        """Create sidebar with map and settings."""
        return html.Div(
className="lg:w-1/3 bg-gray-800 shadow-lg border-r border-gray-700 flex flex-col",
            children=[
                    html.Div(
                        className="p-4 border-b border-gray-700",
                        children=[
                            html.H2(
                                "Energy Simulation", className="text-2xl font-bold text-green-300 mb-2"),
                            html.P("Configure your settings and visualize energy consumption.",
                                   className="text-gray-400 text-sm"),
                            html.A(
                                [html.I(className="fas fa-external-link-alt mr-2"),
                                 "Go to Dashboard"],
                                href="https://dashboard.vps2.martindata.no/",
                                target="_blank",
                                className="w-full bg-green-500 text-white font-bold py-2 px-4 rounded mt-4 flex items-center justify-center"
                            ),
                        ]
                ),
                html.Div(
                    className="flex-1 overflow-y-auto",
                    children=[
                        self.create_map_container(),
                        self.create_settings_panel()
                    ]
                )
            ]
        )

    def fetch_client_data(self):
        """Fetch client data from the external API and create cards."""
        try:
            response = requests.get("https://dashboard.vps2.martindata.no/get_clients")
            if response.status_code == 200:
                self.client_locations = response.json()
                for client in self.client_locations:
                    # Create an apartment-like object for each client location
                    lat = float(client["latitude"])
                    lon = float(client["longitude"])
                    location_name = client["Name"]

                    # Set up default parameters for the simulation
                    building_params = {
                        'length': 10,
                        'width': 8,
                        'wall_height': 2.5,
                        'glazing_ratio': 0.15,
                        'num_windows': 4,
                        'num_doors': 1,
                        'roof_type': 'gable',
                        'roof_pitch': 35,
                        'solar_panel_peak_power': 5,
                        'solar_panel_azimuth': 180,
                        'solar_panel_efficiency': 0.2,
                        'solar_panel_temp_coefficient': -0.4
                    }
                    heating_params = {
                        'COP': 3.5,
                        'min_Q_heating': 0,
                        'max_Q_heating': 5,
                        'temperature_setpoint': 20,
                        'initial_temperature_inside': 18
                    }
                    battery_params = {
                        'capacity': 13.5,
                        'charge_rate': 5,
                        'initial_soc': 50
                    }
                    # Placeholder simulation result (can be updated upon user request)
                    simulation_results = get_simulation_results(
                        lat, lon, building_params, heating_params,
                        occupant_profile=[2 if 6 <= i < 8 or 18 <= i < 22 else 0 for i in range(24)],
                        battery_params=battery_params,
                        include_appliances=True
                    )

                    # Create a new apartment entry for the fetched client
                    apartment = {
                        "id": len(self.apartments),  # Unique ID
                        "lat": lat, "lon": lon, "name": location_name,
                        "residents": 2, "size": 50,
                        "building_params": building_params,
                        "heating_params": heating_params,
                        "battery_params": battery_params,
                        "occupant_profile": [2 if 6 <= i < 8 or 18 <= i < 22 else 0 for i in range(24)],
                        "include_appliances": True,
                        "simulation": simulation_results
                    }

                    self.apartments.append(apartment)
            else:
                logger.error(f"Failed to fetch client data: {response.status_code}")
        except Exception as e:
            logger.exception("Error fetching client data.")

    def create_map_container(self):
        """Create the map component."""
        return html.Div(
            className="p-4",
            children=[
                html.H3("Select Location",
                        className="text-lg font-semibold text-green-200 mb-2"),
                html.Div(
                    className="h-64 rounded-lg overflow-hidden shadow-md bg-gray-900 border border-gray-700",
                    children=[
                        dl.Map(
                            center=[60.472, 8.4689],
                            zoom=5,
                            children=[
                                dl.TileLayer(
                                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"),
                                dl.LayerGroup(id="layer"),
                                dl.LayerGroup(id="client-layer")
                            ],
                            style={'width': '100%', 'height': '100%'},
                            id="map"
                        )
                    ]
                ),
                html.Button(
                    [html.I(className="fas fa-map-marker-alt mr-2"),
                     "Add Location"],
                    id="add-location-btn",
                    className="w-full bg-green-500 text-white font-bold py-2 px-4 rounded mt-4 flex items-center justify-center",
                    disabled=True
                )
            ]
        )

    def create_settings_panel(self):
        """Create the settings panel with input controls."""
        return html.Div(
            className="p-4",
            children=[
                html.H3(
                    "Settings", className="text-lg font-semibold text-green-200 mb-2"),
                dcc.Tabs(id='settings-tabs', value='tab-apartment', children=[
                    dcc.Tab(label='Apartment', value='tab-apartment', className='custom-tab', selected_className='custom-tab--selected',    style={'backgroundColor': '#2d3748', 'color': 'white'},
    selected_style={'backgroundColor': '#1a202c', 'color': 'white'}, children=[
                        html.Div([
                            html.Label("Number of Residents:",
                                       className="text-gray-300 text-sm mt-2"),
                            dcc.Slider(
                                id="input-residents",
                                min=1,
                                max=10,
                                step=1,
                                value=2,
                                marks={i: str(i) for i in range(1, 11)},
                                tooltip={"placement": "bottom",
                                         "always_visible": True},
                                className="mb-4"
                            ),
                            html.Label("Apartment Size (m²):",
                                       className="text-gray-300 text-sm"),
                            dcc.Input(
                                id="input-size",
                                type="number",
                                value=50,
                                min=20,
                                max=200,
                                step=5,
                                className="w-full p-2 mb-4 bg-gray-800 border border-gray-600 rounded text-white",
                                style={'color': 'white'}
                            ),
                            # New Slider for max_Q_heating
                            html.Label("Max Heating Capacity (kW):",
                                       className="text-gray-300 text-sm mt-2"),
                            dcc.Slider(
                                id="input-max-Q-heating",
                                min=1,
                                max=10,
                                step=0.5,
                                value=5,
                                marks={i: f"{i} kW" for i in range(1, 11)},
                                tooltip={"placement": "bottom",
                                         "always_visible": True},
                                className="mb-4"
                            ),
                        ])
                    ]),
                    dcc.Tab(label='Building', value='tab-building', className='custom-tab', selected_className='custom-tab--selected',     style={'backgroundColor': '#2d3748', 'color': 'white'},
    selected_style={'backgroundColor': '#1a202c', 'color': 'white'},children=[
                        html.Div([
                            html.Label("Building Length (m):",
                                       className="text-gray-300 text-sm mt-2"),
                            dcc.Input(
                                id="input-length",
                                type="number",
                                value=10,
                                min=5,
                                max=50,
                                step=1,
                                className="w-full p-2 mb-4 bg-gray-800 border border-gray-600 rounded",
                                style={'backgroundColor': '#2d3748',
                                       'color': 'white'}
                            ),
                            html.Label("Building Width (m):",
                                       className="text-gray-300 text-sm"),
                            dcc.Input(
                                id="input-width",
                                type="number",
                                value=8,
                                min=5,
                                max=50,
                                step=1,
                                className="w-full p-2 mb-4 bg-gray-800 border border-gray-600 rounded",
                                style={'backgroundColor': '#2d3748',
                                       'color': 'white'}
                            ),
                            html.Label("Wall Height (m):",
                                       className="text-gray-300 text-sm"),
                            dcc.Input(
                                id="input-wall-height",
                                type="number",
                                value=2.5,
                                min=2,
                                max=5,
                                step=0.1,
                                className="w-full p-2 mb-4 bg-gray-800 border border-gray-600 rounded",
                                style={'backgroundColor': '#2d3748',
                                       'color': 'white'}
                            ),
                            html.Label("Glazing Ratio:",
                                       className="text-gray-300 text-sm"),
                            dcc.Slider(
                                id="input-glazing-ratio",
                                min=0.05,
                                max=0.5,
                                step=0.01,
                                value=0.15,
                                marks={
                                    i/100: f"{i}%" for i in range(5, 51, 5)},
                                tooltip={"placement": "bottom",
                                         "always_visible": True},
                                className="mb-4"
                            ),
                            html.Label("Number of Windows:",
                                       className="text-gray-300 text-sm"),
                            dcc.Input(
                                id="input-num-windows",
                                type="number",
                                value=4,
                                min=0,
                                max=20,
                                step=1,
                                className="w-full p-2 mb-4 bg-gray-800 border border-gray-600 rounded",
                                style={'backgroundColor': '#2d3748',
                                       'color': 'white'}
                            ),
                            html.Label("Number of Doors:",
                                       className="text-gray-300 text-sm"),
                            dcc.Input(
                                id="input-num-doors",
                                type="number",
                                value=1,
                                min=0,
                                max=5,
                                step=1,
                                className="w-full p-2 mb-4 bg-gray-800 border border-gray-600 rounded",
                                style={'backgroundColor': '#2d3748',
                                       'color': 'white'}
                            ),
                            html.Label(
                                "Roof Type:", className="text-gray-300 text-sm"),
                            dcc.Dropdown(
                                id="input-roof-type",
                                options=[
                                    {'label': 'Flat', 'value': 'flat'},
                                    {'label': 'Gable', 'value': 'gable'},
                                    {'label': 'Hip', 'value': 'hip'},
                                    {'label': 'Shed', 'value': 'shed'}
                                ],
                                value='gable',
                                className="w-full p-2 mb-4 bg-gray-800 border border-gray-600 rounded",
                                style={'backgroundColor': '#2d3748',
                                       'color': 'white'}
                            ),
                            html.Label("Roof Pitch (degrees):",
                                       className="text-gray-300 text-sm"),
                            dcc.Slider(
                                id="input-roof-pitch",
                                min=0,
                                max=60,
                                step=1,
                                value=35,
                                marks={i: str(i) for i in range(0, 61, 10)},
                                tooltip={"placement": "bottom",
                                         "always_visible": True},
                                className="mb-4"
                            ),
                        ])
                    ]),
                    dcc.Tab(label='Solar', value='tab-solar', className='custom-tab', selected_className='custom-tab--selected',    style={'backgroundColor': '#2d3748', 'color': 'white'},
    selected_style={'backgroundColor': '#1a202c', 'color': 'white'}, children=[
                        html.Div([
                            html.Label("Solar Panel Peak Power (kW):",
                                       className="text-gray-300 text-sm mt-2"),
                            dcc.Input(
                                id="input-solar-peak-power",
                                type="number",
                                value=5,
                                min=0,
                                max=20,
                                step=0.1,
                                className="w-full p-2 mb-4 bg-gray-800 border border-gray-600 rounded",
                                style={'backgroundColor': '#2d3748',
                                       'color': 'white'}
                            ),
                            html.Label("Solar Panel Azimuth Angle (degrees):",
                                       className="text-gray-300 text-sm"),
                            dcc.Slider(
                                id="input-solar-azimuth",
                                min=0,
                                max=360,
                                step=1,
                                value=180,
                                marks={i: str(i) for i in range(0, 361, 45)},
                                tooltip={"placement": "bottom",
                                         "always_visible": True},
                                className="mb-4"
                            ),
                            html.Label("Solar Panel Efficiency:",
                                       className="text-gray-300 text-sm"),
                            dcc.Input(
                                id="input-solar-efficiency",
                                type="number",
                                value=0.2,
                                min=0.1,
                                max=0.3,
                                step=0.01,
                                className="w-full p-2 mb-4 bg-gray-800 border border-gray-600 rounded",
                                style={'backgroundColor': '#2d3748',
                                       'color': 'white'}
                            ),
                            html.Label("Solar Panel Temperature Coefficient (%/°C):",
                                       className="text-gray-300 text-sm"),
                            dcc.Input(
                                id="input-solar-temp-coefficient",
                                type="number",
                                value=-0.4,
                                min=-1,
                                max=0,
                                step=0.01,
                                className="w-full p-2 mb-4 bg-gray-800 border border-gray-600 rounded",
                                style={'backgroundColor': '#2d3748',
                                       'color': 'white'}
                            ),
                        ])
                    ]),
                    dcc.Tab(label='Battery', value='tab-battery', className='custom-tab', selected_className='custom-tab--selected',    style={'backgroundColor': '#2d3748', 'color': 'white'},
    selected_style={'backgroundColor': '#1a202c', 'color': 'white'}, children=[
                        html.Div([
                            html.Label("Battery Capacity (kWh):",
                                       className="text-gray-300 text-sm mt-2"),
                            dcc.Input(
                                id="input-battery-capacity",
                                type="number",
                                value=13.5,
                                min=0,
                                max=50,
                                step=0.1,
                                className="w-full p-2 mb-4 bg-gray-800 border border-gray-600 rounded",
                                style={'backgroundColor': '#2d3748',
                                       'color': 'white'}
                            ),
                            html.Label("Battery Charge Rate (kW):",
                                       className="text-gray-300 text-sm"),
                            dcc.Input(
                                id="input-battery-charge-rate",
                                type="number",
                                value=5,
                                min=0,
                                max=20,
                                step=0.1,
                                className="w-full p-2 mb-4 bg-gray-800 border border-gray-600 rounded",
                                style={'backgroundColor': '#2d3748',
                                       'color': 'white'}
                            ),
                            html.Label("Initial Battery State of Charge (%):",
                                       className="text-gray-300 text-sm"),
                            dcc.Slider(
                                id="input-battery-initial-soc",
                                min=0,
                                max=100,
                                step=1,
                                value=50,
                                marks={i: str(i) for i in range(0, 101, 10)},
                                tooltip={"placement": "bottom",
                                         "always_visible": True},
                                className="mb-4"
                            ),
                        ])
                    ]),
                    dcc.Tab(label='Occupancy', value='tab-occupant', className='custom-tab', selected_className='custom-tab--selected',    style={'backgroundColor': '#2d3748', 'color': 'white'},
    selected_style={'backgroundColor': '#1a202c', 'color': 'white'}, children=[
                        html.Div([
                            html.Label(
                                "Occupant Profile:", className="text-gray-300 text-sm mt-2 mb-2"),
                            html.Div(
                                id='occupancy-sliders',
                                children=[
                                    html.Div([
                                        html.Label(
                                            f"{hour}:00", className="text-gray-300 text-xs text-center"),
                                        dcc.Slider(
                                            id={'type': 'occupancy-slider',
                                                'index': hour},
                                            min=0,
                                            max=4,
                                            step=1,
                                            value=2 if 6 <= hour < 8 or 18 <= hour < 22 else 0,
                                            marks=None,
                                            tooltip={"placement": "bottom",
                                                     "always_visible": False},
                                            className="mb-2"
                                        )
                                    ], className="w-1/4 px-1")
                                    for hour in range(24)
                                ],
                                className="flex flex-wrap"
                            ),
                            html.Div(
                                className="flex justify-between mt-2 text-xs text-gray-400",
                                children=[
                                    html.Span(
                                        "Adjust the number of occupants per hour."),
                                    html.Span("Max occupants: 4")
                                ]
                            ),
                            html.Label("Include Appliances:",
                                       className="text-gray-300 text-sm mt-4"),
                            dcc.Checklist(
                                id="include-appliances",
                                options=[{'label': 'Yes', 'value': 'yes'}],
                                value=['yes'],
                                className="mb-4",
                                style={'color': 'white'}
                            ),
                        ])
                    ]),
                ], className="custom-tabs", parent_className='custom-tabs-container'),
                html.Button(
                    [html.I(className="fas fa-play mr-2"), "Run Simulation"],
                    id="run-simulation-btn",
                    className="w-full bg-green-500 text-white font-bold py-2 px-4 rounded mt-4 flex items-center justify-center",
                    disabled=True
                ),
                html.Div(id="error-message",
                         className="text-red-500 text-sm mt-2")
            ]
        )

    def create_main_content(self):
        """Create the main content area for displaying simulation results."""
        return html.Div(
            className="flex-1 p-6 bg-gray-900 overflow-y-auto",
            children=[
                html.Div(
                    className="flex justify-between items-center mb-4",
                    children=[
                        html.H2("Energy Consumption",
                                className="text-2xl font-semibold text-green-300"),
                        html.Button(
                            [html.I(className="fas fa-th-large mr-2"),
                             "Toggle View"],
                            id="toggle-view-btn",
                            className="bg-green-500 text-white font-bold py-2 px-4 rounded flex items-center"
                        ),
                    ]
                ),
                html.Div(
                    id="forecast-info",
                    className="gap-6"
                ),
                html.Div(
                    id="gallery",
                    className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 mt-4"
                )
            ]
        )

    def create_forecast_card(self, apartment, expanded=False):
        """Create a forecast card displaying simulation results."""
        simulation = apartment['simulation']
        location_name = apartment['name']
        energy_consumption_heating = simulation['energy_consumption_heating']
        appliance_consumptions = simulation['energy_consumption_appliances']
        total_energy_consumption = simulation['total_energy_consumption']
        PV_energy_production = simulation['PV_energy_production']
        spot_prices = simulation['spot_price']
        battery_soc = simulation['state_of_charge']
        hours = list(range(24))

        # Create energy consumption graph
        data = [
            go.Bar(
                x=hours,
                y=energy_consumption_heating,
                name="Heating",
                marker=dict(color="#48bb78")
            ),
        ]

        # Define colors for appliances
        appliance_colors = {
            'Dish Washer': '#4299e1',
            'Washing Machine': '#ed8936',
            'Tumble Dryer': '#9f7aea',
            'Oven': '#f56565'
        }

        # Add individual appliance consumptions
        for appliance_name, color in appliance_colors.items():
            data.append(
                go.Bar(
                    x=hours,
                    y=appliance_consumptions[appliance_name],
                    name=f"{appliance_name}",
                    marker=dict(color=color)
                )
            )

        figure = {
            "data": data,
            "layout": go.Layout(
                title="Hourly Energy Consumption",
                xaxis={"title": "Hour"},
                yaxis={"title": "Energy (kWh)"},
                legend={"x": 0, "y": 1, "bgcolor": 'rgba(1,1,1,1)'},
                barmode='stack',
                hovermode="x unified",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font={"color": "white"},
            ),
        }

        energy_graph = dcc.Graph(
            figure=figure,
            className="mt-4",
            config={'displayModeBar': False}
        )

        # PV Production Graph
        pv_figure = {
            "data": [
                go.Scatter(
                    x=hours,
                    y=PV_energy_production,
                    name="PV Production",
                    line=dict(color="#FFD700")  # Gold color
                )
            ],
            "layout": go.Layout(
                title="PV Energy Production",
                xaxis={"title": "Hour"},
                yaxis={"title": "Energy (kWh)"},
                hovermode="x unified",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font={"color": "white"},
            ),
        }

        pv_graph = dcc.Graph(
            figure=pv_figure,
            className="mt-4",
            config={'displayModeBar': False}
        )

        # Battery SOC Graph
        soc_figure = {
            "data": [
                go.Scatter(
                    x=hours,
                    y=battery_soc,
                    name="Battery SOC",
                    line=dict(color="#00BFFF")  # Deep Sky Blue color
                )
            ],
            "layout": go.Layout(
                title="Battery State of Charge",
                xaxis={"title": "Hour"},
                yaxis={"title": "State of Charge (%)"},
                hovermode="x unified",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font={"color": "white"},
            ),
        }

        soc_graph = dcc.Graph(
            figure=soc_figure,
            className="mt-4",
            config={'displayModeBar': False}
        )

        # Spot Price Graph
        price_figure = {
            "data": [
                go.Scatter(
                    x=hours,
                    y=spot_prices,
                    name="Spot Price",
                    line=dict(color="#FF69B4")  # Hot Pink color
                )
            ],
            "layout": go.Layout(
                title="Spot Prices",
                xaxis={"title": "Hour"},
                yaxis={"title": "Price (NOK/kWh)"},
                hovermode="x unified",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font={"color": "white"},
            ),
        }

        price_graph = dcc.Graph(
            figure=price_figure,
            className="mt-4",
            config={'displayModeBar': False}
        )

        # Combine all graphs
        graphs = [energy_graph, pv_graph, soc_graph, price_graph]

        # Create settings summary
        building_params = apartment['building_params']
        occupants_per_hour = apartment['occupant_profile']
        include_appliances = apartment['include_appliances']

        settings_summary = html.Div(
            className="mt-4",
            children=[
                html.H4("Settings Summary",
                        className="text-md font-semibold text-green-300 mb-2"),
                html.Div(
                    className="grid grid-cols-2 gap-4 text-sm",
                    children=[
                        html.Div([
                            html.P(f"Residents: {apartment['residents']}"),
                            html.P(f"Size: {apartment['size']} m²"),
                            html.P(f"Length: {building_params['length']} m"),
                            html.P(f"Width: {building_params['width']} m"),
                            html.P(
                                f"Wall Height: {building_params['wall_height']} m"),
                        ]),
                        html.Div([
                            html.P(
                                f"Glazing Ratio: {building_params['glazing_ratio']:.2f}"),
                            html.P(
                                f"Windows: {building_params['num_windows']}"),
                            html.P(f"Doors: {building_params['num_doors']}"),
                            html.P(
                                f"Roof Type: {building_params['roof_type'].capitalize()}"),
                            html.P(
                                f"Roof Pitch: {building_params['roof_pitch']}°"),
                        ]),
                    ]
                ),
            ]
        )

        card_class = "bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-lg"
        if expanded:
            card_class += " w-full"

        return html.Div(
            className=card_class,
            children=[
                html.H3(f"{location_name}",
                        className="text-xl font-semibold text-green-400"),
                *graphs,  # Unpack the list of graphs
                settings_summary,
            ],
        )

    def create_gallery_card(self, apartment):
        """Create a smaller card for gallery view with a house icon."""
        total_energy = sum(apartment['simulation']['total_energy_consumption'])
        total_pv = sum(apartment['simulation']['PV_energy_production'])
        return html.Div(
            className="bg-gray-800 p-4 rounded-lg border border-gray-700 shadow-lg flex flex-col items-center cursor-pointer hover:bg-gray-700 transition duration-300",
            children=[
                html.Div(
                    className="bg-green-500 text-white rounded-full w-16 h-16 flex items-center justify-center",
                    children=[
                        html.I(className="fas fa-home text-2xl")
                    ]
                ),
                html.H3(
                    apartment["name"],
                    className="text-md font-semibold text-green-400 text-center mt-2"
                ),
                html.P(
                    f"Total Energy: {total_energy:.2f} kWh",
                    className="text-lg font-bold text-pink-300 text-center mt-1"
                ),
                html.P(
                    f"Total PV: {total_pv:.2f} kWh",
                    className="text-lg font-bold text-yellow-300 text-center"
                ),
                html.Div(
                    className="mt-auto text-xs text-gray-400 text-center",
                    children=[
                        html.P(f"Residents: {apartment['residents']}"),
                        html.P(f"Size: {apartment['size']} m²")
                    ]
                )
            ],
            n_clicks=0,
            id={"type": "gallery-card", "index": apartment["id"]}
        )

    def setup_callbacks(self):
        """Setup dashboard callbacks."""
        @self.app.callback(
            [
                Output("layer", "children"),
                Output("client-layer", "children"),
                Output("add-location-btn", "disabled"),
                Output("run-simulation-btn", "disabled"),
                Output("forecast-info", "children"),
                Output("gallery", "children"),
                Output("toggle-view-btn", "children"),
                Output("input-residents", "value"),
                Output("input-size", "value"),
                Output("input-length", "value"),
                Output("input-width", "value"),
                Output("input-wall-height", "value"),
                Output("input-glazing-ratio", "value"),
                Output("input-num-windows", "value"),
                Output("input-num-doors", "value"),
                Output("input-roof-type", "value"),
                Output("input-roof-pitch", "value"),
                Output("input-solar-peak-power", "value"),
                Output("input-solar-azimuth", "value"),
                Output("input-solar-efficiency", "value"),
                Output("input-solar-temp-coefficient", "value"),
                Output("input-battery-capacity", "value"),
                Output("input-battery-charge-rate", "value"),
                Output("input-battery-initial-soc", "value"),
                Output({'type': 'occupancy-slider', 'index': ALL}, 'value'),
                Output("include-appliances", "value"),
                Output("map", "clickData"),
                Output("error-message", "children"),
                Output("forecast-info", "className"),
            ],
            [
                Input("map", "clickData"),
                Input("add-location-btn", "n_clicks"),
                Input("run-simulation-btn", "n_clicks"),
                Input("toggle-view-btn", "n_clicks"),
                Input({"type": "gallery-card", "index": ALL}, "n_clicks"),
                Input({'type': 'occupancy-slider', 'index': ALL}, 'value'),
                Input("input-residents", "value"),
                Input("input-size", "value"),
                Input("input-length", "value"),
                Input("input-width", "value"),
                Input("input-wall-height", "value"),
                Input("input-glazing-ratio", "value"),
                Input("input-num-windows", "value"),
                Input("input-num-doors", "value"),
                Input("input-roof-type", "value"),
                Input("input-roof-pitch", "value"),
                Input("input-solar-peak-power", "value"),
                Input("input-solar-azimuth", "value"),
                Input("input-solar-efficiency", "value"),
                Input("input-solar-temp-coefficient", "value"),
                Input("input-battery-capacity", "value"),
                Input("input-battery-charge-rate", "value"),
                Input("input-battery-initial-soc", "value"),
                Input("include-appliances", "value"),
                Input("input-max-Q-heating", "value")
            ]
        )
        def handle_callbacks(
            click_data, add_n_clicks, run_n_clicks, toggle_n_clicks, gallery_clicks,
            occupancy_slider_values,
            residents, size, length, width, wall_height,
            glazing_ratio, num_windows, num_doors, roof_type, roof_pitch,
            solar_peak_power, solar_azimuth, solar_efficiency, solar_temp_coefficient,
            battery_capacity, battery_charge_rate, battery_initial_soc,
            include_appliances_value, max_Q_heating
        ):
            # Initialize variables
            markers = [dl.Marker(position=(apt["lat"], apt["lon"]),
                                 children=[dl.Tooltip(f"{apt['name']}")])
                       for apt in self.apartments]
            # Add client locations to the map
            client_markers = [
                dl.Marker(
                    position=(float(client["latitude"]), float(client["longitude"])),
                    children=[dl.Tooltip(f"{client['Name']} ({client['IP']})")],
                    icon={"iconUrl": "https://www.startntnu.no/_next/image?url=https%3A%2F%2Fcdn.sanity.io%2Fimages%2F3be0x32v%2Fproduction%2F845d4a14541c8070c7aec2281edd2324e91b169f-1024x1024.png&w=640&q=75", "iconSize": [50, 41], "iconAnchor": [12, 41]}
                )
                for client in self.client_locations
            ]

            forecast_cards = []
            disable_add_location = True
            disable_run_simulation = True
            toggle_button_text = [
                html.I(className="fas fa-th-large mr-2"), "Toggle View"]
            error_message = ""
            ctx = callback_context

            # Helper function to identify the triggered input
            def is_triggered_by(prop):
                return any(prop in triggered_id for triggered_id in ctx.triggered_prop_ids)

            # Occupant profile management
            occupant_profile = occupancy_slider_values

            include_appliances = 'yes' in include_appliances_value if include_appliances_value else False

            try:
                # Input validation
                if not (0.05 <= glazing_ratio <= 0.5):
                    error_message = "Glazing Ratio must be between 0.05 and 0.5."
                    disable_add_location = True
                    return (
                        markers,
                        client_markers,
                        disable_add_location,
                        disable_run_simulation,
                        forecast_cards,
                        [],
                        toggle_button_text,
                        residents,
                        size,
                        length,
                        width,
                        wall_height,
                        glazing_ratio,
                        num_windows,
                        num_doors,
                        roof_type,
                        roof_pitch,
                        solar_peak_power,
                        solar_azimuth,
                        solar_efficiency,
                        solar_temp_coefficient,
                        battery_capacity,
                        battery_charge_rate,
                        battery_initial_soc,
                        occupant_profile,
                        include_appliances_value,
                        None,
                        error_message,
                        "gap-6"
                    )

                if is_triggered_by("map") and click_data and "latlng" in click_data:
                    # Map click handling
                    self.selected_location = click_data["latlng"]
                    preview_marker = dl.Marker(
                        position=(
                            self.selected_location["lat"], self.selected_location["lng"]),
                        children=[dl.Tooltip("Selected Location")]
                    )
                    markers.append(preview_marker)
                    disable_add_location = False

                elif is_triggered_by("add-location-btn") and add_n_clicks and self.selected_location:
                    # Add location handling
                    lat, lon = self.selected_location["lat"], self.selected_location["lng"]
                    location_name = get_location_name(lat, lon)

                    building_params = {
                        'length': length,
                        'width': width,
                        'wall_height': wall_height,
                        'glazing_ratio': glazing_ratio,
                        'num_windows': num_windows,
                        'num_doors': num_doors,
                        'roof_type': roof_type,
                        'roof_pitch': roof_pitch,
                        'solar_panel_peak_power': solar_peak_power,
                        'solar_panel_azimuth': solar_azimuth,
                        'solar_panel_efficiency': solar_efficiency,
                        'solar_panel_temp_coefficient': solar_temp_coefficient
                    }
                    heating_params = {
                        'COP': 3.5,
                        'min_Q_heating': 0,
                        'max_Q_heating': max_Q_heating,
                        'temperature_setpoint': 20,
                        'initial_temperature_inside': 18
                    }
                    battery_params = {
                        'capacity': battery_capacity,
                        'charge_rate': battery_charge_rate,
                        'initial_soc': battery_initial_soc
                    }

                    simulation_results = get_simulation_results(
                        lat, lon, building_params, heating_params,
                        occupant_profile=occupant_profile,
                        battery_params=battery_params,
                        include_appliances=include_appliances
                    )

                    if 'error' not in simulation_results:
                        apartment = {
                            "id": len(self.apartments),  # Unique ID
                            "lat": lat, "lon": lon, "name": location_name,
                            "residents": residents, "size": size,
                            "building_params": building_params,
                            "heating_params": heating_params,
                            "battery_params": battery_params,
                            "occupant_profile": occupant_profile,
                            "include_appliances": include_appliances,
                            "simulation": simulation_results
                        }
                        self.apartments.append(apartment)
                        self.current_apartment = apartment
                        self.selected_location = None
                        markers = [
                            dl.Marker(position=(apt["lat"], apt["lon"]),
                                      children=[dl.Tooltip(f"{apt['name']}")])
                            for apt in self.apartments
                        ]
                        disable_add_location = True
                        disable_run_simulation = False
                        forecast_cards = [self.create_forecast_card(
                            apartment, expanded=True)]
                        self.expanded_view = True  # Show expanded view
                    else:
                        error_message = simulation_results['error']

                elif is_triggered_by("run-simulation-btn") and run_n_clicks:
                    # Run simulation button clicked
                    if self.current_apartment:
                        building_params = {
                            'length': length,
                            'width': width,
                            'wall_height': wall_height,
                            'glazing_ratio': glazing_ratio,
                            'num_windows': num_windows,
                            'num_doors': num_doors,
                            'roof_type': roof_type,
                            'roof_pitch': roof_pitch,
                            'solar_panel_peak_power': solar_peak_power,
                            'solar_panel_azimuth': solar_azimuth,
                            'solar_panel_efficiency': solar_efficiency,
                            'solar_panel_temp_coefficient': solar_temp_coefficient
                        }
                        self.current_apartment['building_params'] = building_params
                        self.current_apartment['residents'] = residents
                        self.current_apartment['size'] = size
                        self.current_apartment['occupant_profile'] = occupant_profile
                        self.current_apartment['include_appliances'] = include_appliances

                        # Update heating_params
                        heating_params = self.current_apartment.get(
                            'heating_params', {})
                        heating_params['max_Q_heating'] = max_Q_heating
                        self.current_apartment['heating_params'] = heating_params

                        # Update battery_params
                        battery_params = {
                            'capacity': battery_capacity,
                            'charge_rate': battery_charge_rate,
                            'initial_soc': battery_initial_soc
                        }
                        self.current_apartment['battery_params'] = battery_params

                        simulation_results = get_simulation_results(
                            self.current_apartment['lat'], self.current_apartment['lon'],
                            building_params, heating_params,
                            occupant_profile=occupant_profile,
                            battery_params=battery_params,
                            include_appliances=include_appliances
                        )
                        self.current_apartment['simulation'] = simulation_results
                        forecast_cards = [self.create_forecast_card(
                            self.current_apartment, expanded=True)]
                        self.expanded_view = True  # Show expanded view
                    else:
                        error_message = "No apartment selected."

                elif is_triggered_by("gallery-card"):
                    # Gallery card click handling
                    for i, n_clicks in enumerate(gallery_clicks):
                        if n_clicks and n_clicks > 0:
                            self.current_apartment = self.apartments[i]
                            gallery_clicks[i] = 0
                            break
                    if self.current_apartment:
                        residents = self.current_apartment['residents']
                        size = self.current_apartment['size']
                        building_params = self.current_apartment['building_params']
                        length = building_params['length']
                        width = building_params['width']
                        wall_height = building_params['wall_height']
                        glazing_ratio = building_params['glazing_ratio']
                        num_windows = building_params['num_windows']
                        num_doors = building_params['num_doors']
                        roof_type = building_params['roof_type']
                        roof_pitch = building_params['roof_pitch']
                        solar_peak_power = building_params['solar_panel_peak_power']
                        solar_azimuth = building_params['solar_panel_azimuth']
                        solar_efficiency = building_params['solar_panel_efficiency']
                        solar_temp_coefficient = building_params['solar_panel_temp_coefficient']
                        battery_params = self.current_apartment['battery_params']
                        battery_capacity = battery_params['capacity']
                        battery_charge_rate = battery_params['charge_rate']
                        battery_initial_soc = battery_params['initial_soc']
                        occupant_profile = self.current_apartment.get(
                            'occupant_profile', [0]*24)
                        include_appliances = self.current_apartment.get(
                            'include_appliances', True)
                        include_appliances_value = [
                            'yes'] if include_appliances else []
                        disable_run_simulation = False
                        forecast_cards = [self.create_forecast_card(
                            self.current_apartment, expanded=True)]
                        self.expanded_view = True  # Switch to expanded view
                    else:
                        # Defaults if apartment not found
                        residents = dash.no_update
                        size = dash.no_update
                        length = dash.no_update
                        width = dash.no_update
                        wall_height = dash.no_update
                        glazing_ratio = dash.no_update
                        num_windows = dash.no_update
                        num_doors = dash.no_update
                        roof_type = dash.no_update
                        roof_pitch = dash.no_update
                        occupant_profile = [0]*24
                        include_appliances_value = dash.no_update
                        disable_run_simulation = True

                elif is_triggered_by("toggle-view-btn"):
                    self.expanded_view = not self.expanded_view
                    self.current_apartment = None if not self.expanded_view else self.current_apartment

                else:
                    # Enable the "Run Simulation" button if there's a current apartment
                    disable_run_simulation = False if self.current_apartment else True

                # Update gallery and forecast cards
                if self.expanded_view and self.current_apartment:
                    forecast_cards = [self.create_forecast_card(
                        self.current_apartment, expanded=True)]
                    gallery_cards = []
                    forecast_info_class = "w-full"
                elif self.expanded_view:
                    forecast_cards = [
                        self.create_forecast_card(apt)
                        for apt in self.apartments
                    ]
                    gallery_cards = []
                    forecast_info_class = "grid grid-cols-1 lg:grid-cols-2 gap-6"
                else:
                    forecast_cards = []
                    gallery_cards = [self.create_gallery_card(
                        apt) for apt in self.apartments]
                    forecast_info_class = "gap-6"

                return (
                    markers,
                    client_markers,
                    disable_add_location,
                    disable_run_simulation,
                    forecast_cards,
                    gallery_cards,
                    toggle_button_text,
                    residents,
                    size,
                    length,
                    width,
                    wall_height,
                    glazing_ratio,
                    num_windows,
                    num_doors,
                    roof_type,
                    roof_pitch,
                    solar_peak_power,
                    solar_azimuth,
                    solar_efficiency,
                    solar_temp_coefficient,
                    battery_capacity,
                    battery_charge_rate,
                    battery_initial_soc,
                    occupant_profile,
                    include_appliances_value,
                    None,  # Reset map clickData
                    error_message,
                    forecast_info_class
                )

            except Exception as e:
                logger.exception(
                    "An error occurred during callback execution.")
                # Return defaults in case of error
                return markers, client_markers, True, True, forecast_cards, [], toggle_button_text, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, [2 if 6 <= i < 8 or 18 <= i < 22 else 0 for i in range(24)], dash.no_update, None, "An error occurred.", "gap-6"

    def run(self):
        """Run the dashboard server."""
        self.app.run_server(debug=True)


# Instantiate and run the dashboard
if __name__ == "__main__":
    dashboard = EnergySimulationDashboard()
    dashboard.run()
