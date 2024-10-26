# gui.py

import dash
from dash import html, dcc, callback_context
import dash_leaflet as dl
import plotly.graph_objs as go
import logging
from dash.dependencies import Input, Output, State, ALL
from datetime import datetime

# Import the simulation function
from simulation import run_simulation

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class EnergySimulationDashboard:
    def __init__(self):
        self.app = dash.Dash(__name__)
        self.apartments = []
        self.selected_location = None
        self.focused_apartment = None

        # Initialize layout and callbacks
        self.setup_layout()
        self.setup_callbacks()

    def setup_layout(self):
        """Setup the dashboard layout."""
        self.app.index_string = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            {%metas%}
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Energy Simulation Dashboard</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            {%favicon%}
            {%css%}
        </head>
        <body class="bg-gray-900 text-white">
            <div id="react-entry-point">{%app_entry%}</div>
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
        </html>
        '''

        # Define the main layout structure
        self.app.layout = html.Div(className="flex h-screen bg-gray-900 text-white", children=[
            self.create_sidebar(),
            self.create_main_content()
        ])

    def create_sidebar(self):
        """Create sidebar with map and settings."""
        return html.Div(
            className="sticky top-0 w-1/4 h-screen p-4 bg-gray-800 shadow-lg border-r border-gray-700 flex flex-col space-y-4",
            children=[
                html.H2("Map & Settings", className="text-2xl font-bold text-green-300 mb-2 uppercase tracking-wide"),
                self.create_map_container(),
                self.create_settings_panel()
            ]
        )

    def create_map_container(self):
        """Create the map component."""
        return html.Div(
            className="h-1/2 rounded-lg overflow-hidden shadow-lg bg-gray-900 border border-gray-800",
            children=[
                dl.Map(
                    center=[60.472, 8.4689],
                    zoom=5,
                    children=[
                        dl.TileLayer(url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"),
                        dl.LayerGroup(id="layer")
                    ],
                    style={'width': '100%', 'height': '100%'},
                    id="map"
                )
            ]
        )

    def create_settings_panel(self):
        """Create the settings panel with input controls."""
        return html.Div(
            className="flex-1 p-4 bg-gray-800 rounded-lg border border-gray-700 shadow-inner overflow-y-auto",
            children=[
                html.H3("Building Settings", className="text-lg font-semibold text-green-200 mb-2"),
                html.Label("Number of Residents:", className="text-gray-300 text-sm"),
                dcc.Input(
                    id="input-residents",
                    type="number",
                    value=2,
                    min=1,
                    max=10,
                    step=1,
                    className="w-full p-2 mb-2 bg-gray-600 rounded",
                    style={'color': 'black'}
                ),
                html.Label("Building Size (m²):", className="text-gray-300 text-sm"),
                dcc.Input(
                    id="input-size",
                    type="number",
                    value=50,
                    min=20,
                    max=200,
                    step=5,
                    className="w-full p-2 mb-2 bg-gray-600 rounded",
                    style={'color': 'black'}
                ),
                html.Label("Number of Floors:", className="text-gray-300 text-sm"),
                dcc.Input(
                    id="input-floors",
                    type="number",
                    value=2,
                    min=1,
                    max=10,
                    step=1,
                    className="w-full p-2 mb-2 bg-gray-600 rounded",
                    style={'color': 'black'}
                ),
                html.Label("Year Built:", className="text-gray-300 text-sm"),
                dcc.Input(
                    id="input-year-built",
                    type="number",
                    value=2010,
                    min=1900,
                    max=datetime.now().year,
                    step=1,
                    className="w-full p-2 mb-2 bg-gray-600 rounded",
                    style={'color': 'black'}
                ),
                html.Label("Heating Type:", className="text-gray-300 text-sm"),
                dcc.Dropdown(
                    id="input-heating-type",
                    options=[
                        {'label': 'Heat Pump', 'value': 'heat_pump'},
                        {'label': 'Electric Heater', 'value': 'electric_heater'},
                        {'label': 'Gas Heater', 'value': 'gas_heater'}
                    ],
                    value='heat_pump',
                    className="w-full mb-2 bg-gray-600 rounded",
                    style={'color': 'black'}
                ),
                html.Button(
                    "Add Building",
                    id="add-location-btn",
                    className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded transition duration-300 mt-2",
                    disabled=True
                )
            ]
        )

    def create_main_content(self):
        """Create the main content area for displaying simulation results."""
        return html.Div(
            className="flex-1 p-4 bg-gray-800 rounded-lg shadow-lg overflow-y-auto space-y-4",
            children=[
                html.H2("Electricity Demand Simulation", className="text-2xl font-semibold text-green-300 mb-2"),
                html.Button(
                    "Back to All Buildings",
                    id="back-btn",
                    className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded transition duration-300 mb-2",
                    style={"display": "none"}  # Hidden by default
                ),
                html.Div(id="forecast-info", className="space-y-4"),
                html.Div(id="gallery", className="flex flex-wrap gap-4 mt-2")
            ]
        )

    def create_gallery_card(self, apartment):
        """Create a smaller card for gallery view with detailed information."""
        demand = apartment.get('demand') or {}
        summary = demand.get('summary', {})
        total_consumption = summary.get('total_consumption', 'N/A')
        max_grid_power = summary.get('max_grid_power', 'N/A')
        avg_spot_price = summary.get('average_spot_price', 'N/A')

        return html.Div(
            className="w-56 h-72 bg-gradient-to-br from-gray-700 to-gray-600 p-4 rounded-lg border border-gray-600 shadow-md flex flex-col items-center justify-between cursor-pointer hover:bg-gray-600 transition duration-300",
            children=[
                html.H3(
                    apartment["name"],
                    className="text-lg font-semibold text-green-400 text-center mb-2"
                ),
                html.P(
                    f"Demand: {total_consumption} kWh",
                    className="text-sm text-pink-300 text-center"
                ),
                html.P(
                    f"Location: ({apartment['lat']:.2f}, {apartment['lon']:.2f})",
                    className="text-xs text-green-300 text-center"
                ),
                html.Div(
                    className="mt-auto text-xs text-gray-400",
                    children=[
                        html.P(f"Residents: {apartment['residents']}"),
                        html.P(f"Size: {apartment['size']} m²"),
                        html.P(f"Max Grid Power: {max_grid_power} kW"),
                        html.P(f"Avg Spot Price: €{avg_spot_price}")
                    ]
                )
            ],
            n_clicks=0,
            id={"type": "gallery-card", "index": self.apartments.index(apartment)}
        )

    def create_forecast_card(self, simulation_results, location_name):
        """Create a forecast card displaying weather and demand details."""
        timestamps = simulation_results["timeseries"]["timestamps"]
        consumption = simulation_results["timeseries"]["consumption"]
        solar_generation = simulation_results["timeseries"]["solar_generation"]
        battery_soc = simulation_results["timeseries"]["battery"]["soc"]
        grid_power = simulation_results["timeseries"]["grid_power"]
        spot_prices = simulation_results["timeseries"]["spot_prices"]

        demand_graph = dcc.Graph(
            figure={
                "data": [
                    go.Scatter(x=timestamps, y=consumption, mode="lines", name="Consumption (kWh)", line=dict(width=3)),
                    go.Scatter(x=timestamps, y=solar_generation, mode="lines", name="Solar Generation (kWh)", line=dict(width=3, dash='dot')),
                    go.Scatter(x=timestamps, y=grid_power, mode="lines", name="Grid Power (kWh)", line=dict(width=3, dash='dash')),
                ],
                "layout": {
                    "title": {"text": "Energy Demand and Supply", "font": {"size": 16, "color": "white"}},
                    "xaxis": {"title": "Time", "showgrid": False, "tickangle": 45, "color": "white"},
                    "yaxis": {"title": "kWh", "showgrid": True, "gridcolor": "gray", "color": "white"},
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "font": {"color": "white"},
                    "hovermode": "x",
                },
            },
            className="mt-2",
        )

        battery_graph = dcc.Graph(
            figure={
                "data": [
                    go.Scatter(x=timestamps, y=battery_soc, mode="lines", name="Battery SOC (%)", line=dict(width=3)),
                ],
                "layout": {
                    "title": {"text": "Battery State of Charge", "font": {"size": 16, "color": "white"}},
                    "xaxis": {"title": "Time", "showgrid": False, "tickangle": 45, "color": "white"},
                    "yaxis": {"title": "SOC (%)", "showgrid": True, "gridcolor": "gray", "color": "white"},
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "font": {"color": "white"},
                    "hovermode": "x",
                },
            },
            className="mt-2",
        )

        spot_price_graph = dcc.Graph(
            figure={
                "data": [
                    go.Scatter(x=timestamps, y=spot_prices, mode="lines", name="Spot Prices (€)", line=dict(width=3)),
                ],
                "layout": {
                    "title": {"text": "Spot Prices", "font": {"size": 16, "color": "white"}},
                    "xaxis": {"title": "Time", "showgrid": False, "tickangle": 45, "color": "white"},
                    "yaxis": {"title": "Price (€)", "showgrid": True, "gridcolor": "gray", "color": "white"},
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "font": {"color": "white"},
                    "hovermode": "x",
                },
            },
            className="mt-2",
        )

        return html.Div(
            className="bg-gradient-to-br from-gray-800 to-gray-700 p-4 rounded-lg border border-gray-600 shadow-md",
            children=[
                html.H3(f"{location_name}", className="text-lg font-semibold text-green-400 mb-2"),
                demand_graph,
                battery_graph,
                spot_price_graph
            ],
        )

    def setup_callbacks(self):
        """Setup dashboard callbacks."""
        @self.app.callback(
            [
                Output("layer", "children"),
                Output("add-location-btn", "disabled"),
                Output("forecast-info", "children"),
                Output("gallery", "children"),
                Output("back-btn", "style"),
            ],
            [
                Input("map", "click_lat_lng"),
                Input("add-location-btn", "n_clicks"),
                Input({"type": "gallery-card", "index": ALL}, "n_clicks"),
                Input("back-btn", "n_clicks")
            ],
            [
                State("input-residents", "value"),
                State("input-size", "value"),
                State("input-floors", "value"),
                State("input-year-built", "value"),
                State("input-heating-type", "value")
            ]
        )
        def handle_interactions(
            click_lat_lng, n_clicks, gallery_clicks, back_n_clicks,
            residents, size, floors, year_built, heating_type
        ):
            # Initialize outputs
            markers = [
                dl.Marker(position=(apt["lat"], apt["lon"]),
                          children=[dl.Tooltip(f"{apt['name']}")])
                for apt in self.apartments
            ]
            forecast_cards = []
            gallery_cards = []
            disable_add_location = True
            show_back_btn = {"display": "none"}
            ctx = callback_context

            def is_triggered_by(prop):
                return any(prop in trigger["prop_id"] for trigger in ctx.triggered)

            # Add logging to debug
            logger.info(f"Triggered by: {ctx.triggered}")
            logger.info(f"click_lat_lng: {click_lat_lng}")

            if is_triggered_by("map") and click_lat_lng:
                # Check if click_lat_lng is a dict or list/tuple
                if isinstance(click_lat_lng, dict):
                    lat = click_lat_lng['lat']
                    lon = click_lat_lng['lng']
                elif isinstance(click_lat_lng, (list, tuple)):
                    lat = click_lat_lng[0]
                    lon = click_lat_lng[1]
                else:
                    lat = lon = None  # Handle unexpected format

                if lat is not None and lon is not None:
                    self.selected_location = {'lat': lat, 'lon': lon}
                    preview_marker = dl.Marker(
                        position=(lat, lon),
                        children=[dl.Tooltip("Selected Location")]
                    )
                    markers.append(preview_marker)
                    disable_add_location = False

            elif is_triggered_by("add-location-btn") and self.selected_location:
                lat = self.selected_location["lat"]
                lon = self.selected_location["lon"]
                location_name = f"Building {len(self.apartments) + 1}"

                # Store the apartment data with parameters
                self.apartments.append({
                    "lat": lat,
                    "lon": lon,
                    "name": location_name,
                    "residents": residents,
                    "size": size,
                    "floors": floors,
                    "year_built": year_built,
                    "heating_type": heating_type,
                    "demand": None  # Initialize demand as None
                })
                self.selected_location = None
                markers = [
                    dl.Marker(position=(apt["lat"], apt["lon"]),
                              children=[dl.Tooltip(f"{apt['name']}")])
                    for apt in self.apartments
                ]
                disable_add_location = True

            elif is_triggered_by("gallery-card"):
                clicked_indices = [i for i, clicked in enumerate(gallery_clicks) if clicked]
                if clicked_indices:
                    clicked_index = clicked_indices[0]
                    self.focused_apartment = self.apartments[clicked_index]

                    # Run the simulation if it hasn't been run yet
                    if not self.focused_apartment.get('demand'):
                        try:
                            simulation_results = run_simulation(
                                lat=self.focused_apartment['lat'],
                                lon=self.focused_apartment['lon'],
                                num_occupants=self.focused_apartment['residents'],
                                floor_area=self.focused_apartment['size'],
                                num_floors=self.focused_apartment['floors'],
                                year_built=self.focused_apartment['year_built'],
                                heating_type=self.focused_apartment['heating_type']
                            )
                            # Store simulation results
                            self.focused_apartment['demand'] = simulation_results
                        except Exception as e:
                            logger.error(f"Simulation failed: {e}")
                            # Display error message to the user
                            forecast_cards = [
                                html.Div(
                                    f"Simulation failed: {e}",
                                    className="text-red-500 font-bold text-center mt-4"
                                )
                            ]
                            return markers, disable_add_location, forecast_cards, gallery_cards, {"display": "block"}

                    forecast_cards = [
                        self.create_forecast_card(
                            self.focused_apartment["demand"],
                            self.focused_apartment["name"]
                        )
                    ]
                    show_back_btn = {"display": "block"}

            elif is_triggered_by("back-btn"):
                self.focused_apartment = None

            if not self.focused_apartment:
                forecast_cards = []
                gallery_cards = [
                    self.create_gallery_card(apt) for apt in self.apartments
                ]
                show_back_btn = {"display": "none"}

            return markers, disable_add_location, forecast_cards, gallery_cards, show_back_btn

    def run(self):
        """Run the dashboard server."""
        self.app.run_server(debug=True)

if __name__ == "__main__":
    dashboard = EnergySimulationDashboard()
    dashboard.run()
