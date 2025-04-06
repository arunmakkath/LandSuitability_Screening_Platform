
import streamlit as st
import ee
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

# Authenticate and initialize
if 'ee_initialized' not in st.session_state:
    ee.Authenticate()
    ee.Initialize()
    st.session_state['ee_initialized'] = True

st.title("🛰️ Land Suitability Screening for Construction")

# Sidebar inputs
st.sidebar.header("Select Area of Interest")
min_lon = st.sidebar.number_input("Min Longitude", value=103.6)
min_lat = st.sidebar.number_input("Min Latitude", value=1.2)
max_lon = st.sidebar.number_input("Max Longitude", value=103.8)
max_lat = st.sidebar.number_input("Max Latitude", value=1.4)

aoi = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])

st.sidebar.header("Date Range")
start_date = st.sidebar.date_input("Start Date", value=ee.Date("2023-11-01").format('YYYY-MM-dd').getInfo())
end_date = st.sidebar.date_input("End Date", value=ee.Date("2023-12-01").format('YYYY-MM-dd').getInfo())

if st.sidebar.button("Run Suitability Analysis"):
    with st.spinner("Processing satellite data..."):
        # Sentinel-1 and Sentinel-2
        s1 = ee.ImageCollection('COPERNICUS/S1_GRD')             .filterBounds(aoi).filterDate(str(start_date), str(end_date))             .select(['VV', 'VH']).mean()
        s2 = ee.ImageCollection('COPERNICUS/S2_SR')             .filterBounds(aoi).filterDate(str(start_date), str(end_date))             .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))             .select(['B4', 'B8', 'B11']).median()

        ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI')
        bare = ndvi.lt(0.2).And(s2.select('B11').gt(1000))
        dry = s1.select('VV').lt(-15).And(s1.select('VH').lt(-20))

        dem = ee.Image('USGS/SRTMGL1_003')
        slope = ee.Terrain.slope(dem)
        flat = slope.lt(5)

        flood = ee.Image('JRC/GSW1_3/MaxExtent')
        no_flood = flood.clip(aoi).Not()

        roads = ee.FeatureCollection('users/giswqs/public/osm_roads')
        near_road = roads.distance(1000).lt(1000)

        protected = ee.FeatureCollection('WCMC/WDPA/current/polygons')
        no_protected = protected.geometry().contains(aoi).Not()

        score = bare.And(dry).multiply(0.3)             .add(flat.multiply(0.2))             .add(no_flood.multiply(0.2))             .add(near_road.multiply(0.15))             .add(ee.Image.constant(no_protected).multiply(0.15))

        score_viz = score.visualize(min=0, max=1, palette=["red", "yellow", "green"])

        # Display map
        center = aoi.centroid().coordinates().getInfo()[::-1]
        m = folium.Map(location=center, zoom_start=13)
        folium.TileLayer(
            tiles=score_viz.getMapId()['tile_fetcher'].url_format,
            attr='Google Earth Engine', name='Suitability',
            overlay=True
        ).add_to(m)
        folium.LayerControl().add_to(m)

        st.success("Suitability analysis complete.")
        st_folium(m, width=1200, height=600)
