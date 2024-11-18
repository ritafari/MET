import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
import os
import pickle
import re
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap


mtr_data = pd.read_csv("mtr_data.csv")
ip_info = pd.read_csv("ip_info.csv")

# Count occurrences of "Sarahs-MacBook-Pro.local" for Lyon's hops
lyon_hop_count = mtr_data[mtr_data["Hop IP"] == "Sarahs-MacBook-Pro.local"].shape[0]

# Merge mtr_data with ip_info on "Hop IP" to get geographic details for each hop
mtr_data_with_location = mtr_data.merge(ip_info, left_on="Hop IP", right_on="Host/IP", how="left")

# Load or create a cache for coordinates
cache_file = "city_coords_cache.pkl"
if os.path.exists(cache_file):
    with open(cache_file, "rb") as f:
        city_coords = pickle.load(f)
else:
    city_coords = {}

# check that  Coordinates column exists and contains tuple data
def get_coordinates(city, region, country):
    key = (city, region, country)
    if key not in city_coords:
        city_coords[key] = (None, None)  # Default if no data, in case coordinates not available
    return city_coords[key]

lyon_coords = (45.7640, 4.8357)

# Add Coordinates column by looking up each city's coordinates
mtr_data_with_location["Coordinates"] = mtr_data_with_location.apply(
    lambda x: get_coordinates(x["City"], x["Region"], x["Country"]), axis=1
)

# Filter rows with invalid coordinates
mtr_data_with_location = mtr_data_with_location[
    mtr_data_with_location["Coordinates"].apply(lambda x: isinstance(x, tuple) and len(x) == 2)
]

# Remove non-numeric latency values and convert the column to float
def clean_latency(value):
    try:
        return float(re.sub(r'[^\d.]', '', str(value))) if pd.notnull(value) else None
    except ValueError:
        return None

mtr_data_with_location["Latency"] = mtr_data_with_location["Latency"].apply(clean_latency)

# Group by city, region, and country with coordinates to count hops in each city
city_hop_counts = mtr_data_with_location.groupby(["City", "Region", "Country", "Coordinates"]).size().reset_index(
    name="Hop Count"
)

# Add Lyon with its hop count
lyon_entry = pd.DataFrame([{
    "City": "Lyon",
    "Region": "Auvergne-Rhône-Alpes",
    "Country": "France",
    "Coordinates": (45.7640, 4.8357),
    "Hop Count": lyon_hop_count
}])
city_hop_counts = pd.concat([city_hop_counts, lyon_entry], ignore_index=True)

# Define a colormap for latency with a green-to-red gradient
latency_cmap = LinearSegmentedColormap.from_list("LatencyGradient", ["green", "yellow", "red"])


def create_map(llcrnrlat, urcrnrlat, llcrnrlon, urcrnrlon, title, filename, figsize=(14, 10)):
    fig, ax = plt.subplots(figsize=figsize)
    m = Basemap(projection='cyl', llcrnrlat=llcrnrlat, urcrnrlat=urcrnrlat, llcrnrlon=llcrnrlon, urcrnrlon=urcrnrlon,
                resolution='l', ax=ax)
    m.drawcoastlines()
    m.drawcountries()
    m.fillcontinents(color="lightgrey", lake_color="lightblue")
    m.drawmapboundary(fill_color="lightblue")

    # Define color and size based on hop count
    def get_color_and_size(hop_count):
        if hop_count < 100:
            return 'blue', 8
        elif 100 <= hop_count < 500:
            return 'purple', 10
        else:
            return 'red', 12

    # Plot each city with a marker size based on hop count
    for _, row in city_hop_counts.iterrows():
        lat, lon = row["Coordinates"]
        if lat is None or lon is None:
            continue  # Skip any entries with invalid coordinates
        color, size = get_color_and_size(row["Hop Count"])
        x, y = m(lon, lat)
        m.plot(x, y, 'o', markersize=size, color=color, alpha=0.7)

    # Draw connections between cities for each Target IP with varying line colors by latency
    for target_ip in mtr_data_with_location["Target IP"].unique():
        route_data = mtr_data_with_location[mtr_data_with_location["Target IP"] == target_ip]

        # Start with Lyon's coordinates as the origin of each route
        lyon_coord = (45.7640, 4.8357)
        route_coords = [lyon_coord]  # Lyon is the starting point of each route
        route_latencies = []  # Will hold latency values for the connections

        # Find the first valid hop after Lyon and add it to the route
        for _, hop_row in route_data.iterrows():
            if hop_row["Hop IP"] == "Sarahs-MacBook-Pro.local":
                continue  # Skip Lyon itself in the route data

            hop_coord = hop_row["Coordinates"]
            if hop_coord != (None, None):  # If we have valid coordinates
                route_coords.append(hop_coord)
                route_latencies.append(hop_row["Latency"])
                break  # Connect Lyon only to the first valid hop

        # Now add the remaining hops in the route
        for _, hop_row in route_data.iterrows():
            hop_coord = hop_row["Coordinates"]
            if hop_coord and hop_coord != (None, None) and hop_coord not in route_coords:
                route_coords.append(hop_coord)
                route_latencies.append(hop_row["Latency"])

        # Draw connections between hops
        if len(route_coords) > 1:
            for i in range(len(route_coords) - 1):
                start_coord = route_coords[i]
                end_coord = route_coords[i + 1]
                latency_value = route_latencies[i] if i < len(route_latencies) else 0

                start_lat, start_lon = start_coord
                end_lat, end_lon = end_coord
                norm_latency = min((latency_value - 1) / (300 - 1), 1)  # Normalize to [0,1] range
                path_color = latency_cmap(norm_latency)

                # Plot the line between consecutive points in the route
                m.plot([start_lon, end_lon], [start_lat, end_lat], latlon=True, color=path_color, linewidth=1,
                       alpha=0.7)

    # legend for hop count
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Hop Count < 100', markerfacecolor='blue', markersize=8),
        Line2D([0], [0], marker='o', color='w', label='Hop Count 100-500', markerfacecolor='purple', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Hop Count > 500', markerfacecolor='red', markersize=12)
    ]
    plt.legend(handles=legend_elements, loc='lower left', title="Hop Count", fontsize=8)

    # colorbar for latency gradient focusing on 1-300 ms
    sm = plt.cm.ScalarMappable(cmap=latency_cmap, norm=plt.Normalize(1, 300))
    sm.set_array([])  # Required for colorbar with ScalarMappable
    cbar = fig.colorbar(sm, ax=ax, shrink=0.5, aspect=10, pad=0.02)
    cbar.set_label('Latency (ms)', fontsize=8)
    cbar.ax.tick_params(labelsize=8)

    plt.title(title)
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()

# Europe map centered around France
create_map(40, 60, -10, 20, "Network Pathways and Hop Counts by City (Europe - Centered Around France)", "network_pathways_europe_centered_france.png")

# world map
create_map(-30, 60, -130, 30, "Network Pathways and Hop Counts by City (Focused World)", "network_pathways_focused_world.png", figsize=(20, 15))
