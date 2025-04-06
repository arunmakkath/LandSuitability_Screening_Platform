
# 🛰️ Land Suitability Screening Platform

This repository contains a prototype Earth Observation platform to help construction firms evaluate land parcels for structural viability and regulatory risks using open satellite data.

## 📁 Repository Structure

- `notebooks/`: Jupyter notebook for multi-layer suitability analysis (soil, slope, flood, etc.)
- `streamlit_app/`: Lightweight Streamlit web interface for interactive land screening.
- `scripts/`: GeoTIFF export script for Google Earth Engine.
- `docs/`: Pitch deck and product narrative.

## 🔍 Features

- Composite scoring based on:
  - Soil moisture and NDVI (Sentinel-1/2)
  - Topography & slope (SRTM DEM)
  - Flood risk (JRC)
  - Zoning/infrastructure (OpenStreetMap)
  - Environmental protection zones (WDPA)
- Earth Engine-backed analytics.
- No-GIS-required Streamlit interface.
- GeoTIFF export for GIS tools.

## 🚀 Getting Started

### 1. Setup

```bash
pip install earthengine-api streamlit folium geemap
earthengine authenticate
```

### 2. Run Streamlit App

```bash
cd streamlit_app
streamlit run app.py
```

### 3. Export Suitability Map as GeoTIFF

```bash
cd scripts
python export_geotiff.py
```

---

Built for internal exploration at GrabInfra | 2025.
