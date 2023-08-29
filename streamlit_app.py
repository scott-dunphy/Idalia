# streamlit_app.py

import streamlit as st
import geopandas as gpd
import zipfile
import os
from shapely.geometry import Point
import io
import requests
import pandas as pd

def check_point(gdf, lat, lon):

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

def main():
    st.title("Geospatial Point Checker")

    uploaded_file = st.file_uploader("Upload a zip containing shapefiles", type=["zip"])

    if uploaded_file is not None:
        gdf = zip_to_gdf(uploaded_file)
        st.write("Shapefiles loaded successfully!")

        # Input box to accept a list of addresses
        addresses = st.text_area("Enter a list of addresses (separated by carriage returns)")

        if st.button("Process Addresses"):
            address_list = addresses.split("\n")
            results = []

            for address in address_list:
                lat, lon = address_to_lat_lon(address)
                if lat and lon:
                    result = check_point(gdf, lat, lon)
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

if __name__ == "__main__":
    main()