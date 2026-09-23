import folium
from branca.element import JavascriptLink, CssLink, Element
import xml.etree.ElementTree as ET
import os
import base64
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    kml_path = os.path.join(script_dir, 'batavia.kml')
    tree = ET.parse(kml_path)
    root = tree.getroot()

    href = root.find('.//{*}GroundOverlay/{*}Icon/{*}href').text
    image_filename = os.path.basename(href)
    img_path = os.path.join(script_dir, image_filename)

    north = float(root.find('.//{*}north').text)
    south = float(root.find('.//{*}south').text)
    east = float(root.find('.//{*}east').text)
    west = float(root.find('.//{*}west').text)
    
    bounds = [[south, west], [north, east]]
    center = [(north + south) / 2, (east + west) / 2]

    with open(img_path, "rb") as f:
        encoded_image = base64.b64encode(f.read()).decode('utf-8')
    img_data_uri = f"data:image/jpeg;base64,{encoded_image}"

    m = folium.Map(location=center, zoom_start=16, tiles=None, width='100%', height='100%')
    
    # Get the internal names Folium assigns to the map and layers
    map_name = m.get_name()

    google_sat = folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google",
        name="Modern Jakarta",
        overlay=True,
        control=True
    )
    google_sat.add_to(m)
    right_layer_name = google_sat.get_name()

    hist_layer = folium.raster_layers.ImageOverlay(
        name="Historical Batavia",
        image=img_data_uri,
        bounds=bounds,
        opacity=0.85,
        control=True,
        zindex=1
    )
    hist_layer.add_to(m)
    left_layer_name = hist_layer.get_name()

    # --- THE FIX: Raw JavaScript for the Swipe Slider ---
    m.get_root().header.add_child(
        JavascriptLink("https://cdn.jsdelivr.net/npm/leaflet-side-by-side@2.2.0/leaflet-side-by-side.js")
    )
    m.get_root().header.add_child(
        CssLink("https://cdn.jsdelivr.net/npm/leaflet-side-by-side@2.2.0/leaflet-side-by-side.css")
    )
    
    # Raw JS to initialize the slider perfectly
    slider_js = f"""
    <script>
        window.onload = function() {{
            setTimeout(function() {{
                try {{
                    var map = {map_name};
                    var leftLayer = {left_layer_name};
                    var rightLayer = {right_layer_name};
                    
                    // Add the side-by-side slider
                    L.control.sideBySide(leftLayer, rightLayer).addTo(map);
                }} catch (e) {{
                    console.error("Slider initialization failed:", e);
                }}
            }}, 500); // Wait 500ms to ensure Leaflet is fully loaded
        }};
    </script>
    """
    m.get_root().html.add_child(Element(slider_js))

    # --- Opacity Slider UI ---
    opacity_html = """
    <div style="position: fixed; top: 10px; left: 50px; z-index: 9999; background: white; padding: 10px 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.3); font-family: sans-serif; font-size: 14px;">
        <label for="opacitySlider" style="font-weight: bold; display: block; margin-bottom: 5px;">1746 Map Opacity: <span id="opacityValue">85%</span></label>
        <input type="range" id="opacitySlider" min="0" max="100" value="85" style="width: 200px;">
    </div>
    """
    m.get_root().html.add_child(Element(opacity_html))

    # Raw JS for the Opacity Slider
    opacity_js = """
    <script>
        document.getElementById('opacitySlider').addEventListener('input', function(e) {
            var opacity = e.target.value / 100;
            document.getElementById('opacityValue').innerText = e.target.value + '%';
            var layers = document.querySelectorAll('.leaflet-image-layer');
            layers.forEach(function(layer) {
                layer.style.opacity = opacity;
            });
        });
    </script>
    """
    m.get_root().html.add_child(Element(opacity_js))

    folium.LayerControl(collapsed=False).add_to(m)

    return m._repr_html_()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
