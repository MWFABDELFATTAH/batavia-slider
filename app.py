import folium
from folium.plugins import SideBySideLayers
import webbrowser
import os
import xml.etree.ElementTree as ET
import base64

# 1. Define paths
KML_FILE = "batavia.kml"
IMAGE_FILE = "" # Will find it from the KML
OUTPUT_HTML = "batavia_slider.html"

def build_slider():
    # Find the folder where this script is running
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. Read the Google Earth KML file to get the exact map boundaries
    kml_path = os.path.join(script_dir, KML_FILE)
    tree = ET.parse(kml_path)
    root = tree.getroot()

    # Find the image name inside the KML
    href = root.find('.//{*}GroundOverlay/{*}Icon/{*}href').text
    IMAGE_FILE = os.path.basename(href)
    img_path = os.path.join(script_dir, IMAGE_FILE)

    # Find the North, South, East, West boundaries
    north = float(root.find('.//{*}north').text)
    south = float(root.find('.//{*}south').text)
    east = float(root.find('.//{*}east').text)
    west = float(root.find('.//{*}west').text)
    
    bounds = [[south, west], [north, east]]
    center = [(north + south) / 2, (east + west) / 2]

    print(f"Found map! Centered at {center}")

    # 3. Convert the image to Base64 so it works 100% offline in the browser
    with open(img_path, "rb") as f:
        encoded_image = base64.b64encode(f.read()).decode('utf-8')
    img_data_uri = f"data:image/jpeg;base64,{encoded_image}"

    # 4. Create the map!
    m = folium.Map(location=center, zoom_start=16, tiles=None)

    # Google Satellite (Right Side)
    google_sat = folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google",
        name="Modern Jakarta (Satellite)",
        overlay=False,
        control=True
    )
    google_sat.add_to(m)

    # 1746 Map (Left Side)
    hist_layer = folium.raster_layers.ImageOverlay(
        name="1746 Batavia",
        image=img_data_uri,
        bounds=bounds,
        opacity=0.85,
        control=True
    )
    hist_layer.add_to(m)

    # The Swipe Slider!
       # This smart block tries different commands depending on your Python version
    try:
        SideBySideLayers(left_layers=[hist_layer], right_layers=[google_sat]).add_to(m)
    except TypeError:
        try:
            SideBySideLayers([hist_layer], [google_sat]).add_to(m)
        except TypeError:
            SideBySideLayers(hist_layer, google_sat).add_to(m)
    
    # Opacity Controls
    folium.LayerControl(collapsed=False).add_to(m)

    # 5. Save and Open
    output_path = os.path.join(script_dir, OUTPUT_HTML)
    m.save(output_path)
    print(f"Success! Opening map slider in your browser...")
    webbrowser.open("file://" + output_path)

if __name__ == "__main__":
    build_slider()