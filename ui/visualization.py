import dash
from dash import html, dcc, callback_context
import dash_leaflet as dl
import plotly.graph_objs as go
import logging
from dash.dependencies import Input, Output, ALL
from model import get_heating_simulation, get_location_name

logger = logging.getLogger(__name__)

class EnergySimulationDashboard:
    def __init__(self):
        self.app = dash.Dash(__name__)
        self.apartments = []
        self.selected_location = None
        self.expanded_view = False
        self.current_apartment = None  # New property to track current apartment

        # Initialize layout and callbacks
        self.setup_layout()
        self.setup_callbacks()

    def setup_layout(self):
        """Setup the dashboard layout."""
        self.app.index_string = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Energy Simulation Dashboard</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        </head>
        <body class="bg-gray-900 text-white">
            <div id="react-entry-point">{%app_entry%}</div>
            <footer>{%config%}{%scripts%}{%renderer%}</footer>
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
            className="sticky top-0 w-1/4 h-screen p-4 bg-gray-800 shadow-lg border-r border-gray-600 flex flex-col space-y-6",
            children=[
                html.H2("Map & Settings", className="text-2xl font-bold text-green-300 mb-2 uppercase tracking-wide"),
                self.create_map_container(),
                self.create_settings_panel()
            ]
        )

    def create_map_container(self):
        """Create the map component."""
        return html.Div(
            className="h-1/2 rounded-lg overflow-hidden shadow-md bg-gray-900 border border-gray-700",
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
            className="flex-1 p-4 bg-gray-700 rounded-lg border border-gray-600 shadow-inner overflow-y-auto",
            children=[
                html.H3("Apartment Settings", className="text-lg font-semibold text-green-200 mb-2"),
                html.Label("Number of Residents:", className="text-gray-300 text-sm"),
                dcc.Input(
                    id="input-residents",
                    type="number",
                    value=2,
                    min=1,
                    max=10,
                    step=1,
                    className="w-full p-1 mb-4",
                    style={'color': 'black'}
                ),
                html.Label("Apartment Size (m²):", className="text-gray-300 text-sm"),
                dcc.Input(
                    id="input-size",
                    type="number",
                    value=50,
                    min=20,
                    max=200,
                    step=5,
                    className="w-full p-1 mb-4",
                    style={'color': 'black'}
                ),
                # Add inputs for building parameters
                html.H3("Building Parameters", className="text-lg font-semibold text-green-200 mb-2"),
                html.Label("Building Length (m):", className="text-gray-300 text-sm"),
                dcc.Input(
                    id="input-length",
                    type="number",
                    value=10,
                    min=5,
                    max=50,
                    step=1,
                    className="w-full p-1 mb-4",
                    style={'color': 'black'}
                ),
                html.Label("Building Width (m):", className="text-gray-300 text-sm"),
                dcc.Input(
                    id="input-width",
                    type="number",
                    value=8,
                    min=5,
                    max=50,
                    step=1,
                    className="w-full p-1 mb-4",
                    style={'color': 'black'}
                ),
                html.Label("Wall Height (m):", className="text-gray-300 text-sm"),
                dcc.Input(
                    id="input-wall-height",
                    type="number",
                    value=2.5,
                    min=2,
                    max=5,
                    step=0.1,
                    className="w-full p-1 mb-4",
                    style={'color': 'black'}
                ),
                html.Label("Glazing Ratio:", className="text-gray-300 text-sm"),
                dcc.Input(
                    id="input-glazing-ratio",
                    type="number",
                    value=0.15,
                    min=0.05,
                    max=0.5,
                    step=0.01,
                    className="w-full p-1 mb-4",
                    style={'color': 'black'}
                ),
                html.Label("Number of Windows:", className="text-gray-300 text-sm"),
                dcc.Input(
                    id="input-num-windows",
                    type="number",
                    value=4,
                    min=0,
                    max=20,
                    step=1,
                    className="w-full p-1 mb-4",
                    style={'color': 'black'}
                ),
                html.Label("Number of Doors:", className="text-gray-300 text-sm"),
                dcc.Input(
                    id="input-num-doors",
                    type="number",
                    value=1,
                    min=0,
                    max=5,
                    step=1,
                    className="w-full p-1 mb-4",
                    style={'color': 'black'}
                ),
                html.Label("Roof Type:", className="text-gray-300 text-sm"),
                dcc.Dropdown(
                    id="input-roof-type",
                    options=[
                        {'label': 'Flat', 'value': 'flat'},
                        {'label': 'Gable', 'value': 'gable'},
                        {'label': 'Hip', 'value': 'hip'},
                        {'label': 'Shed', 'value': 'shed'}
                    ],
                    value='gable',
                    className="w-full p-1 mb-4",
                    style={'color': 'black'}
                ),
                html.Label("Roof Pitch (degrees):", className="text-gray-300 text-sm"),
                dcc.Input(
                    id="input-roof-pitch",
                    type="number",
                    value=35,
                    min=0,
                    max=60,
                    step=1,
                    className="w-full p-1 mb-4",
                    style={'color': 'black'}
                ),
                # Occupant Profile Input
                html.H3("Occupant Profile", className="text-lg font-semibold text-green-200 mb-2"),
                html.Label("Number of Occupants per Hour (comma-separated):", className="text-gray-300 text-sm"),
                dcc.Textarea(
                    id="input-occupant-profile",
                    value="2,2,2,2,2,2,0,0,0,0,2,2,4,4,4,4,4,4,4,4,4,4,2,2",
                    style={'width': '100%', 'height': '100px', 'color': 'black'},
                    className="mb-4"
                ),
                html.Button(
                    "Add Location",
                    id="add-location-btn",
                    className="bg-green-500 text-white font-bold py-2 px-4 rounded mt-4",
                    disabled=True
                ),
                html.Button(
                    "Run Simulation",
                    id="run-simulation-btn",
                    className="bg-yellow-500 text-white font-bold py-2 px-4 rounded mt-4",
                    disabled=True  # Initially disabled
                )
            ]
        )

    def create_main_content(self):
        """Create the main content area for displaying simulation results."""
        return html.Div(
            className="flex-1 p-6 bg-gray-800 rounded-lg shadow-lg overflow-y-auto space-y-6",
            children=[
                html.H2("Electricity Demand Simulation", className="text-2xl font-semibold text-green-300 mb-4"),
                html.Button(
                    "Switch to Gallery View" if self.expanded_view else "Switch to Card View",
                    id="toggle-view-btn",
                    className="bg-blue-500 text-white font-bold py-2 px-4 rounded mb-4"
                ),
                html.Div(id="forecast-info", className="space-y-4"),
                html.Div(id="gallery", className="flex flex-wrap gap-4 mt-4")
            ]
        )

    def create_forecast_card(self, apartment):
        """Create a forecast card displaying simulation results."""
        simulation = apartment['simulation']
        location_name = apartment['name']
        energy_consumption = simulation['energy_consumption']
        hours = list(range(24))

        # Create energy consumption graph
        energy_graph = dcc.Graph(
            figure={
                "data": [
                    go.Bar(
                        x=hours,
                        y=energy_consumption,
                        name="Energy Consumption",
                        marker=dict(color="green")
                    ),
                ],
                "layout": go.Layout(
                    title="Hourly Energy Consumption",
                    xaxis={"title": "Hour"},
                    yaxis={"title": "Energy Consumption (kWh)"},
                    legend={"x": 0, "y": 1},
                    hovermode="closest",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font={"color": "white"},
                ),
            },
            className="mt-4",
        )

        return html.Div(
            className="bg-gray-700 p-6 rounded-lg border border-gray-600 shadow-sm",
            children=[
                html.H3(f"{location_name}", className="text-lg font-semibold text-green-400"),
                energy_graph,
            ],
        )

    def create_gallery_card(self, apartment):
        """Create a smaller card for gallery view with a house icon."""
        return html.Div(
            className="w-52 h-60 bg-gray-700 p-4 rounded-lg border border-gray-600 shadow-sm flex flex-col items-center justify-center cursor-pointer hover:bg-gray-600 transition duration-300",
            children=[
                html.H3(
                    apartment["name"],
                    className="text-sm font-semibold text-green-400 text-center mb-2"
                ),
                html.Div(
                    className="flex justify-center items-center h-10 mb-2",
                    children=[
                        html.Img(
                            src="https://cdn-icons-png.flaticon.com/512/25/25694.png",
                            className="w-6 h-6"
                        )
                    ]
                ),
                html.P(
                    f"Energy Consumption: {sum(apartment['simulation']['energy_consumption']):.2f} kWh",
                    className="text-xs text-pink-300 text-center mt-2"
                ),
                html.Div(
                    className="mt-auto text-xs text-gray-400",
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
                Output("input-occupant-profile", "value"),
                Output("map", "clickData")
            ],
            [
                Input("map", "clickData"),
                Input("add-location-btn", "n_clicks"),
                Input("run-simulation-btn", "n_clicks"),
                Input("toggle-view-btn", "n_clicks"),
                Input({"type": "gallery-card", "index": ALL}, "n_clicks"),
                # Add Inputs for all input fields
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
                Input("input-occupant-profile", "value"),
            ],
            []
        )
        def handle_callbacks(
            click_data, add_n_clicks, run_n_clicks, toggle_n_clicks, gallery_clicks,
            residents, size, length, width, wall_height,
            glazing_ratio, num_windows, num_doors, roof_type, roof_pitch,
            occupant_profile_input
        ):
            # Initialize variables
            markers = [dl.Marker(position=(apt["lat"], apt["lon"]),
                                 children=[dl.Tooltip(f"{apt['name']}")])
                       for apt in self.apartments]
            forecast_cards = []
            disable_add_location = True
            disable_run_simulation = True
            toggle_button_text = "Switch to Gallery View" if self.expanded_view else "Switch to Card View"
            ctx = callback_context

            # Helper function to identify the triggered input
            def is_triggered_by(prop):
                return any(prop in triggered_id for triggered_id in ctx.triggered_prop_ids)

            # Parse occupant profile
            try:
                occupant_profile = [int(x.strip()) for x in occupant_profile_input.split(',')]
                if len(occupant_profile) != 24:
                    occupant_profile = [0] * 24
            except:
                occupant_profile = [0] * 24

            try:
                if is_triggered_by("map") and click_data and "latlng" in click_data:
                    # Map click handling
                    self.selected_location = click_data["latlng"]
                    preview_marker = dl.Marker(
                        position=(self.selected_location["lat"], self.selected_location["lng"]),
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
                    }
                    heating_params = {
                        'COP': 3.5,
                        'min_Q_heating': 0,
                        'max_Q_heating': 5,
                        'temperature_setpoint': 20,
                        'initial_temperature_inside': 18
                    }

                    simulation_results = get_heating_simulation(
                        lat, lon, building_params, heating_params, occupant_profile=occupant_profile
                    )

                    if 'error' not in simulation_results:
                        apartment = {
                            "id": len(self.apartments),  # Unique ID
                            "lat": lat, "lon": lon, "name": location_name,
                            "residents": residents, "size": size,
                            "building_params": building_params,
                            "heating_params": heating_params,
                            "occupant_profile": occupant_profile,
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
                        forecast_cards = [self.create_forecast_card(apartment)]
                    else:
                        pass  # Handle error

                elif is_triggered_by("gallery-card"):
                    # Gallery card click handling
                    # Find which gallery card was clicked
                    for i, n_clicks in enumerate(gallery_clicks):
                        if n_clicks and n_clicks > 0:
                            self.current_apartment = self.apartments[i]
                            # Reset the n_clicks to prevent multiple triggers
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
                        occupant_profile = self.current_apartment.get('occupant_profile', [0]*24)
                        occupant_profile_input = ','.join(map(str, occupant_profile))
                        disable_run_simulation = False
                        forecast_cards = [self.create_forecast_card(self.current_apartment)]
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
                        occupant_profile_input = dash.no_update
                        disable_run_simulation = True

                elif is_triggered_by("toggle-view-btn"):
                    self.expanded_view = not self.expanded_view
                    self.current_apartment = None if not self.expanded_view else self.current_apartment

                else:
                    # Enable the "Run Simulation" button if there's a current apartment
                    disable_run_simulation = False if self.current_apartment else True
                    if self.current_apartment:
                        # Update apartment parameters
                        building_params = {
                            'length': length,
                            'width': width,
                            'wall_height': wall_height,
                            'glazing_ratio': glazing_ratio,
                            'num_windows': num_windows,
                            'num_doors': num_doors,
                            'roof_type': roof_type,
                            'roof_pitch': roof_pitch,
                        }
                        self.current_apartment['building_params'] = building_params
                        self.current_apartment['residents'] = residents
                        self.current_apartment['size'] = size
                        self.current_apartment['occupant_profile'] = occupant_profile

                        # Re-run simulation
                        heating_params = self.current_apartment.get('heating_params', {})
                        simulation_results = get_heating_simulation(
                            self.current_apartment['lat'], self.current_apartment['lon'],
                            building_params, heating_params, occupant_profile=occupant_profile
                        )
                        self.current_apartment['simulation'] = simulation_results
                        forecast_cards = [self.create_forecast_card(self.current_apartment)]
                    else:
                        forecast_cards = []

                # Update gallery and forecast cards
                if self.expanded_view and self.current_apartment:
                    forecast_cards = [self.create_forecast_card(self.current_apartment)]
                    gallery_cards = []
                elif self.expanded_view:
                    forecast_cards = [
                        self.create_forecast_card(apt)
                        for apt in self.apartments
                    ]
                    gallery_cards = []
                else:
                    forecast_cards = []
                    gallery_cards = [self.create_gallery_card(apt) for apt in self.apartments]

                return (
                    markers,
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
                    occupant_profile_input,
                    None  # Reset map clickData
                )

            except Exception as e:
                logger.error(f"Callback error: {e}")
                # Return defaults in case of error
                return markers, True, True, forecast_cards, [], toggle_button_text, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, None

    def run(self):
        """Run the dashboard server."""
        self.app.run_server(debug=True)

# Instantiate and run the dashboard
if __name__ == "__main__":
    dashboard = EnergySimulationDashboard()
    dashboard.run()
