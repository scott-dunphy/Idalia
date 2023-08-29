# streamlit_app.py

import streamlit as st
import geopandas as gpd
import zipfile
import os
from shapely.geometry import Point
import io
import requests
import pandas as pd
import pydeck as pdk

def check_point(lat, lon):

    # Load the GeoDataFrame from the pickle file
    gdf = pd.read_pickle('geo_dataframe.pkl')
  
    point = Point(lon, lat)
    
    # Check if the point is within any shape in the dataframe
    contains_point = gdf[gdf.contains(point)]
    
    if not contains_point.empty:
        return contains_point['PERCENTAGE'].values[0]
    else:
        return 'Fall Outside the Path'

# Function to extract lat and lon from OpenStreetMap Nominatim API
def address_to_lat_lon(address):
    base_url = "https://nominatim.openstreetmap.org/search.php"
    params = {
        "q": address,
        "format": "jsonv2"
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    if data:
        lat = data[0]['lat']
        lon = data[0]['lon']
        return float(lat), float(lon)
    else:
        return None, None

def plot_map_with_hover(df):
    # Prepare data for pydeck chart
    view_state = pdk.ViewState(
        latitude=df["Latitude"].mean(),
        longitude=df["Longitude"].mean(),
        zoom=4
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        df,
        pickable=True,
        opacity=0.6,
        stroked=True,
        filled=True,
        radius_scale=6,
        radius_min_pixels=5,
        radius_max_pixels=100,
        line_width_min_pixels=1,
        get_position=["Longitude", "Latitude"],
        get_radius=1000,  
        get_fill_color=[255, 0, 0],
        get_line_color=[0, 0, 0],
    )

    # Customize tooltip to show the property address and probability
    tooltip = {
        "html": "<b>Address:</b> {Address} <br> <b>Probability:</b> {Result}",
        "style": {"backgroundColor": "steelblue", "color": "white"},
    }

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
    )

    st.pydeck_chart(r)


def main():
    st.title("Tropical Storm Idalia")
    st.header("Hurricane-Force Wind Speed Probabilities")
    st.write("For the 120 hours (5.00 days) from 1 PM CDT MON AUG 28 to 1 PM CDT SAT SEP 02")

    # Input box to accept a list of addresses
    addresses = st.text_area("Enter a list of addresses (separated by carriage returns)")

    if st.button("Process Addresses"):
        address_list = addresses.split("\n")
        results = []

        for address in address_list[:50]:
            lat, lon = address_to_lat_lon(address)
            if lat and lon:
                result = check_point(lat, lon)
                results.append({
                    "Address": address,
                    "Latitude": lat,
                    "Longitude": lon,
                    "Result": result
                })
            else:
                results.append({
                    "Address": address,
                    "Latitude": "N/A",
                    "Longitude": "N/A",
                    "Result": "Unable to fetch coordinates"
                })

        # Display the results in a table
        df = pd.DataFrame(results)
        st.table(df)

        plot_map_with_hover(df)




if __name__ == "__main__":
    main()
