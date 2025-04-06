
import streamlit as st
import ee
import folium
import json
import pandas as pd
from streamlit_folium import st_folium
from datetime import date

st.set_page_config(layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

USER_CREDENTIALS = {
    "admin": "demo123",
    "engineer": "build2024"
}

def login():
    with st.form("Login"):
        st.subheader("🔐 Login to continue")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        if submit:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state.logged_in = True
            else:
                st.error("Invalid credentials")

if not st.session_state.logged_in:
    login()
    st.stop()

try:
    service_account_info = json.loads(st.secrets["earthengine"])
    credentials = ee.ServiceAccountCredentials(email=service_account_info["client_email"], key_data=service_account_info)
    ee.Initialize(credentials)
    st.session_state['ee_initialized'] = True
except Exception as e:
    st.error("Earth Engine authentication failed. Please check your service account configuration.")
    st.stop()

st.title("🛰️ Land Suitability Screening Portal")

st.sidebar.header("Date Range Selection")
start_date = st.sidebar.date_input("Start Date", date(2023, 11, 1))
end_date = st.sidebar.date_input("End Date", date(2023, 12, 1))

st.sidebar.markdown("## 1. Draw or Upload AOI")
m = folium.Map(location=[1.3, 103.8], zoom_start=11)
folium.plugins.Draw(export=True).add_to(m)
folium.LayerControl().add_to(m)
st_data = st_folium(m, width=700, height=500)

if st_data and st_data.get("last_active_drawing"):
    coords = st_data["last_active_drawing"]["geometry"]["coordinates"][0]
    aoi = ee.Geometry.Polygon(coords)

    with st.spinner("Running satellite analysis..."):
        try:
            s1 = ee.ImageCollection('COPERNICUS/S1_GRD')                 .filterBounds(aoi).filterDate(str(start_date), str(end_date))                 .select(['VV', 'VH']).mean()

            s2 = ee.ImageCollection('COPERNICUS/S2_SR')                 .filterBounds(aoi).filterDate(str(start_date), str(end_date))                 .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))                 .select(['B4', 'B8', 'B11']).median()

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

            score = bare.And(dry).multiply(0.3)                 .add(flat.multiply(0.2))                 .add(no_flood.multiply(0.2))                 .add(near_road.multiply(0.15))                 .add(ee.Image.constant(no_protected).multiply(0.15))                 .rename('suitability_score')

            score_viz = score.visualize(min=0, max=1, palette=["red", "yellow", "green"])
            center = aoi.centroid().coordinates().getInfo()[::-1]
            m2 = folium.Map(location=center, zoom_start=13)
            folium.TileLayer(
                tiles=score_viz.getMapId()['tile_fetcher'].url_format,
                attr='Google Earth Engine', name='Suitability',
                overlay=True
            ).add_to(m2)
            folium.LayerControl().add_to(m2)

            st.subheader("📊 Suitability Map")
            st_folium(m2, width=1000, height=600)

            stats = {
                "Soil Score (Bare & Dry)": bare.And(dry).reduceRegion(**{
                    'reducer': ee.Reducer.mean(),
                    'geometry': aoi,
                    'scale': 30
                }).getInfo(),
                "Flatness Score": flat.reduceRegion(**{
                    'reducer': ee.Reducer.mean(),
                    'geometry': aoi,
                    'scale': 30
                }).getInfo()
            }

            df = pd.DataFrame.from_dict(stats, orient='index', columns=['Mean Value'])
            st.subheader("📄 Summary Statistics")
            st.dataframe(df)
            csv = df.to_csv().encode('utf-8')
            st.download_button("Download CSV Summary", csv, "summary.csv", "text/csv")

        except Exception as e:
            st.error(f"Analysis failed: {e}")
else:
    st.warning("Draw a polygon on the map to define your Area of Interest.")
