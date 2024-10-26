import dash
from dash import html, dcc, callback_context
import dash_leaflet as dl
import plotly.graph_objs as go
import logging
from dash.dependencies import Input, Output, State, ALL
from model import get_hourly_demand_data, get_location_name

logger = logging.getLogger(__name__)

class EnergySimulationDashboard:
    def __init__(self):
        self.app = dash.Dash(__name__)
        self.apartments = []
        self.selected_location = None
        self.expanded_view = False
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
            className="flex-1 p-4 bg-gray-700 rounded-lg border border-gray-600 shadow-inner",
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
                html.Button(
                    "Add Location",
                    id="add-location-btn",
                    className="bg-green-500 text-white font-bold py-2 px-4 rounded mt-4",
                    disabled=True
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

    def create_forecast_card(self, day_data, location_name):
        """Create a forecast card displaying weather and demand details."""
        weather_icon_url = f"http://openweathermap.org/img/wn/{day_data.get('weather_icon', '01d')}@2x.png"
        weather_description = day_data.get("weather_description", "No description")
        temperature = day_data.get("temperature", "N/A")
        humidity = day_data.get("humidity", "N/A")
        wind_speed = day_data.get("wind_speed", "N/A")
        avg_demand = day_data.get("average_demand", "N/A")
        hourly_demand = day_data["hourly_demand"]

        hourly_times = [hour["time"] for hour in hourly_demand]
        hourly_demands = [float(hour["demand"].split(" ")[0]) for hour in hourly_demand]

        demand_graph = dcc.Graph(
            figure={
                "data": [
                    go.Scatter(
                        x=hourly_times,
                        y=hourly_demands,
                        mode="lines+markers",
                        marker=dict(size=6, color="rgba(51,204,204,0.8)"),
                        line=dict(color="rgba(0,128,128,0.8)", width=2),
                        hoverinfo="x+y",
                    )
                ],
                "layout": {
                    "title": "24-Hour Demand Forecast",
                    "xaxis": {"title": "Time", "showgrid": True, "gridcolor": "gray"},
                    "yaxis": {"title": "Demand (kWh)", "showgrid": True, "gridcolor": "gray"},
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "font": {"color": "white"},
                    "hovermode": "closest",
                },
            },
            className="mt-4",
        )

        return html.Div(
            className="bg-gray-700 p-6 rounded-lg border border-gray-600 shadow-sm",
            children=[
                html.Div(
                    className="flex items-center space-x-4 mb-4",
                    children=[
                        html.Img(src=weather_icon_url, className="w-12 h-12"),
                        html.Div(
                            children=[
                                html.H3(f"{location_name}", className="text-lg font-semibold text-green-400"),
                                html.P(weather_description.capitalize(), className="text-sm text-green-300"),
                            ]
                        ),
                    ],
                ),
                html.Div(
                    className="grid grid-cols-2 gap-6 text-sm text-gray-300 mb-4",
                    children=[
                        html.Div([
                            html.P("Temperature:", className="font-semibold text-green-200"),
                            html.P(f"{temperature} °C", className="text-xl font-bold text-yellow-300")
                        ]),
                        html.Div([
                            html.P("Humidity:", className="font-semibold text-green-200"),
                            html.Div(
                                className="relative pt-1",
                                children=[
                                    html.Div(
                                        style={"width": f"{humidity}%", "backgroundColor": "#4fd1c5"},
                                        className="h-2 rounded bg-teal-400",
                                    ),
                                    html.Span(f"{humidity}%", className="text-xs text-gray-400")
                                ]
                            )
                        ]),
                        html.Div([
                            html.P("Wind Speed:", className="font-semibold text-green-200"),
                            html.P(f"{wind_speed} m/s", className="text-xl font-bold text-blue-300")
                        ]),
                        html.Div([
                            html.P("Average Demand:", className="font-semibold text-green-200"),
                            html.P(f"{avg_demand} kWh", className="text-xl font-bold text-pink-300")
                        ]),
                    ],
                ),
                demand_graph
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
                    f"Demand: {apartment['demand'][0].get('average_demand', 'N/A')} kWh",
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
            id={"type": "gallery-card", "index": apartment["name"]}
        )

    def setup_callbacks(self):
        """Setup dashboard callbacks."""
        @self.app.callback(
            [
                Output("layer", "children"),
                Output("add-location-btn", "disabled"),
                Output("forecast-info", "children"),
                Output("gallery", "children"),
                Output("toggle-view-btn", "children")
            ],
            [
                Input("map", "clickData"),
                Input("add-location-btn", "n_clicks"),
                Input("toggle-view-btn", "n_clicks"),
                Input({"type": "gallery-card", "index": ALL}, "n_clicks")
            ],
            [
                State("input-residents", "value"),
                State("input-size", "value")
            ]
        )
        def handle_map_click_or_add_location(
            click_data, n_clicks, toggle_n_clicks, gallery_clicks, residents, size
        ):
            # Default values for outputs
            markers = [
                dl.Marker(position=(apt["lat"], apt["lon"]),
                          children=[dl.Tooltip(f"{apt['name']}")])
                for apt in self.apartments
            ]
            forecast_cards = []
            gallery_cards = [
                self.create_gallery_card(apt) for apt in self.apartments
            ]
            disable_add_location = True
            toggle_button_text = "Switch to Gallery View" if self.expanded_view else "Switch to Card View"
            ctx = callback_context

            # Helper functions to identify the triggered input
            def is_triggered_by(prop):
                return any(prop in triggered_id for triggered_id in ctx.triggered_prop_ids)

            try:
                # Map click handling - enables adding a new location
                if is_triggered_by("map") and click_data and "latlng" in click_data:
                    self.selected_location = click_data["latlng"]
                    preview_marker = dl.Marker(
                        position=(self.selected_location["lat"], self.selected_location["lng"]),
                        children=[dl.Tooltip("Selected Location")]
                    )
                    markers.append(preview_marker)
                    disable_add_location = False

                # Add location handling - store selected location details
                elif is_triggered_by("add-location-btn") and n_clicks and self.selected_location:
                    lat, lon = self.selected_location["lat"], self.selected_location["lng"]
                    location_name = get_location_name(lat, lon)
                    demand_data = get_hourly_demand_data(lat, lon, residents, size)

                    if not isinstance(demand_data, str):  # Check if demand data is valid
                        self.apartments.append({
                            "lat": lat, "lon": lon, "name": location_name,
                            "residents": residents, "size": size, "demand": demand_data
                        })
                        # Update markers and reset selected location
                        self.selected_location = None
                        markers = [
                            dl.Marker(position=(apt["lat"], apt["lon"]),
                                      children=[dl.Tooltip(f"{apt['name']}")])
                            for apt in self.apartments
                        ]
                        disable_add_location = True  # Disable the button after adding

                # Toggle between gallery and expanded views
                elif is_triggered_by("toggle-view-btn"):
                    self.expanded_view = not self.expanded_view
                    self.focused_apartment = None if not self.expanded_view else self.focused_apartment

                # Handle gallery card clicks to focus on a specific apartment
                elif is_triggered_by("gallery-card"):
                    clicked_index = ctx.triggered_prop_ids[0].split(".")[0].split(":")[-1].strip('"')
                    self.focused_apartment = next(
                        (apt for apt in self.apartments if apt["name"] == clicked_index), None
                    )
                    self.expanded_view = True

                # Create forecast cards for expanded view, only showing the focused apartment's details
                if self.expanded_view and self.focused_apartment:
                    forecast_cards = [
                        self.create_forecast_card(
                            self.focused_apartment["demand"][0],
                            self.focused_apartment["name"]
                        )
                    ]
                elif self.expanded_view:
                    # Display all apartments if there's no specific focus (edge case)
                    forecast_cards = [
                        self.create_forecast_card(apt["demand"][0], apt["name"])
                        for apt in self.apartments
                    ]

                # Prepare gallery cards only if not in expanded view
                gallery_cards = [self.create_gallery_card(apt) for apt in self.apartments] if not self.expanded_view else []

                return markers, disable_add_location, forecast_cards, gallery_cards, toggle_button_text

            except KeyError as e:
                logger.error(f"KeyError: Missing data key - {e}")
            except Exception as e:
                logger.error(f"Callback error: {e}")

            # Return defaults in case of error
            return markers, True, forecast_cards, gallery_cards, toggle_button_text

    def run(self):
        """Run the dashboard server."""
        self.app.run_server(debug=True)
