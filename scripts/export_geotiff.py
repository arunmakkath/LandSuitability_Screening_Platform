
import ee
ee.Authenticate()
ee.Initialize()

# Define AOI and date range
aoi = ee.Geometry.Rectangle([103.6, 1.2, 103.8, 1.4])
start_date = '2023-11-01'
end_date = '2023-12-01'

# Sentinel-1 and Sentinel-2 processing
s1 = ee.ImageCollection('COPERNICUS/S1_GRD')     .filterBounds(aoi).filterDate(start_date, end_date)     .select(['VV', 'VH']).mean()

s2 = ee.ImageCollection('COPERNICUS/S2_SR')     .filterBounds(aoi).filterDate(start_date, end_date)     .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))     .select(['B4', 'B8', 'B11']).median()

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

score = bare.And(dry).multiply(0.3)     .add(flat.multiply(0.2))     .add(no_flood.multiply(0.2))     .add(near_road.multiply(0.15))     .add(ee.Image.constant(no_protected).multiply(0.15))     .rename('suitability_score')

# Export to Google Drive
task = ee.batch.Export.image.toDrive(
    image=score,
    description='Suitability_GeoTIFF',
    folder='EarthEngineExports',
    fileNamePrefix='land_suitability_score',
    region=aoi,
    scale=30,
    crs='EPSG:4326',
    maxPixels=1e9
)

task.start()
print("Export started. Check Google Drive > EarthEngineExports folder.")
