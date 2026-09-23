import folium
from folium.plugins import SideBySideLayers
import xml.etree.ElementTree as ET
import os
import base64
from flask import Flask

# Initialize the Flask Web App
app = Flask(__name__)

@app.route('/')
def home():
    # Find the folder where this script is running
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Read the Google Earth KML file
    kml_path = os.path.join(script_dir, 'batavia.kml')
    tree = ET.parse(kml_path)
    root = tree.getroot()

    # Find the image name inside the KML
    href = root.find('.//{*}GroundOverlay/{*}Icon/{*}href').text
    image_filename = os.path.basename(href)
    img_path = os.path.join(script_dir, image_filename)

    # Find the North, South, East, West boundaries
    north = float(root.find('.//{*}north').text)
    south = float(root.find('.//{*}south').text)
    east = float(root.find('.//{*}east').text)
    west = float(root.find('.//{*}west').text)
    
    bounds = [[south, west], [north, east]]
    center = [(north + south) / 2, (east + west) / 2]

    # 2. Convert the image to Base64 so it works 100% on the web
    with open(img_path, "rb") as f:
        encoded_image = base64.b64encode(f.read()).decode('utf-8')
    img_data_uri = f"data:image/jpeg;base64,{encoded_image}"

    # 3. Create the map!
    m = folium.Map(location=center, zoom_start=16, tiles=None)

    # Google Satellite (Right Side)
    google_sat = folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google",
        name="Modern Jakarta",
        overlay=False,
        control=True
    )
    google_sat.add_to(m)

    # Historical Map (Left Side)
    hist_layer = folium.raster_layers.ImageOverlay(
        name="Historical Batavia",
        image=img_data_uri,
        bounds=bounds,
        opacity=0.85,
        control=True
    )
    hist_layer.add_to(m)

    # 4. The Swipe Slider
    try:
        SideBySideLayers(left_layers=[hist_layer], right_layers=[google_sat]).add_to(m)
    except TypeError:
        try:
            SideBySideLayers([hist_layer], [google_sat]).add_to(m)
        except TypeError:
            SideBySideLayers(hist_layer, google_sat).add_to(m)

    # Opacity Controls
    folium.LayerControl(collapsed=False).add_to(m)

    # 5. Return the map HTML directly to the user's browser
    return m._repr_html_()

# This is required for Render to run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
