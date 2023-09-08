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

def download_and_convert_to_gdf(url, knots):
    """
    Download a shapefile from the given URL, unzip it, and convert it to a GeoDataFrame.
    Only processes shapefiles containing the text "64knt".
    """
    # Download the ZIP file
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(path="tmp_shapefile")

    # Find the .shp file in the extracted files containing "64knt" for 64 knots (Hurricane Wind Speed)
    shapefile_path = None
    for filename in os.listdir("tmp_shapefile"):
        if filename.endswith(".shp") and knots in filename:
            shapefile_path = os.path.join("tmp_shapefile", filename)
            break

    # If no matching .shp file was found, return an empty GeoDataFrame
    if shapefile_path is None:
        return gpd.GeoDataFrame()

    # Load the matching shapefile into a GeoDataFrame
    gdf = gpd.read_file(shapefile_path)

    # Clean up the temporary directory
    for filename in os.listdir("tmp_shapefile"):
        os.remove(os.path.join("tmp_shapefile", filename))
    os.rmdir("tmp_shapefile")

    return gdf

    
def check_point(lat, lon, knots):

    # Load the GeoDataFrame from NOAA
    gdf = download_and_convert_to_gdf("https://www.nhc.noaa.gov/gis/forecast/archive/wsp_120hr5km_latest.zip", knots)
  
    point = Point(lon, lat)
    
    # Check if the point is within any shape in the dataframe
    contains_point = gdf[gdf.contains(point)]
    
    if not contains_point.empty:
        return contains_point['PERCENTAGE'].values[0]
    else:
        return 'Not Applicable'

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
    # Exclude assets with missing lat/lon values
    df = df.dropna(subset=['Latitude', 'Longitude'])
    df = df.loc[(df.Latitude != 'N/A') & (df.Longitude != 'N/A')]

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
        get_fill_color=[255,0,0],  # Assuming you have R, G, B columns for colors
        get_line_color=[0, 0, 0],
    )

    # Customize tooltip to show the property address and probability
    tooltip = {
        "html": "<b>Address:</b> {Address} <br> <b>Probability:</b> {Probability}",
        "style": {"backgroundColor": "steelblue", "color": "white"},
    }

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
    )

    st.pydeck_chart(r)


def main():
    st.title("Real Estate Hurricane Risk")
    st.header("Hurricane-Force Wind Speed Probabilities")
    st.write("Five Day Forecast")

    # Input box to accept a list of addresses
    addresses = st.text_area("Enter a list of addresses (each address on a separate line). Limit of 50.")

    if st.button("Process Addresses"):
        address_list = addresses.split("\n")
        results = []

        knot_values = ["34knt", "50knt", "64knt"]

        for address in address_list[:50]:
            lat, lon = address_to_lat_lon(address)
            result_dict = {
                "Address": address,
                "Latitude": lat if lat else "N/A",
                "Longitude": lon if lon else "N/A"
            }

            if lat and lon:
                for knot in knot_values:
                    probability = check_point(lat, lon, knot)
                    result_dict[f"Probability_{knot}"] = probability
            else:
                for knot in knot_values:
                    result_dict[f"Probability_{knot}"] = "Unable to fetch coordinates"

            
            results.append(result_dict)

        # Display the results in a table
        df = pd.DataFrame(results)
        df.rename(columns={
                            'Probability_34knt':'Tropical Storm Force (>= 39mph)',
                            'Probability_50knt':'>= 58 mph',
                            'Probability_64knt':'Hurricane Force (>= 74 mph)'
            }, inplace=True)
        st.table(df)

        plot_map_with_hover(df)

        st.write("""
            Please refer to the NHC NOAA website for additional information (https://www.nhc.noaa.gov).
        These represent probabilities of sustained (1-minute average) surface wind speeds equal to or exceeding 64 kt (74 mph). These wind speed probabilities are based on the official National Hurricane Center (NHC) track, intensity, and wind radii forecasts, and on NHC forecast error statistics for those forecast variables during recent years. Each probability provides cumulative probabilities that wind speeds of at least 74 mph will occur during cumulative time periods at each specific point on the map. The cumulative periods begin at the start of the forecast period and extend through the entire 5-day forecast period at cumulative 12-hour intervals (i.e., 0-12 h, 0-24 h, 0-36 h, ... , 0-120 h). To assess the overall risk of experiencing winds of at least 74 mph at any location, the 120-h graphics are recommended.

It is important for users to realize that wind speed probabilities that might seem relatively small at their location might still be quite significant, since they indicate that there is a chance that a damaging or even extreme event could occur that warrants preparations to protect lives and property.
""")

        st.write("Source: https://www.nhc.noaa.gov")

        st.markdown(
                """
                ---
                **Disclaimer:** 
                - The data presented in this application is based on sources believed to be accurate. However, the creator does not guarantee the accuracy of this data. 
                - The information provided is for informational purposes only and should not be solely relied upon. Users are advised to conduct their own independent research and due diligence.
                - Forecasts and data may change at any time and might not necessarily be reflected in this application.
                ---
                """
            )




if __name__ == "__main__":
    main()
