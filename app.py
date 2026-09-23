import folium
from branca.element import Element
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
    map_name = m.get_name()

    google_sat = folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google",
        name="Modern Jakarta",
        overlay=True,
        control=True
    )
    google_sat.add_to(m)

    hist_layer = folium.raster_layers.ImageOverlay(
        name="Historical Batavia",
        image=img_data_uri,
        bounds=bounds,
        opacity=1.0, 
        control=True,
        zindex=1
    )
    hist_layer.add_to(m)

    # --- FIXED 2-AXIS SLIDER ---
    slider_js = f"""
    <script>
    window.onload = function() {{
        setTimeout(function() {{
            var map = {map_name};
            var mapContainer = document.getElementById('{map_name}');
            
            var sliderX = mapContainer.clientWidth / 2;
            var sliderY = mapContainer.clientHeight / 2;

            // Vertical Line
            var sliderV = document.createElement('div');
            sliderV.style.cssText = 'position: absolute; top: 0; bottom: 0; width: 4px; background: rgba(255,255,255,0.8); box-shadow: 0 0 4px rgba(0,0,0,0.8); z-index: 1000; cursor: ew-resize; left: ' + (sliderX - 2) + 'px; pointer-events: auto;';
            mapContainer.appendChild(sliderV);

            // Horizontal Line
            var sliderH = document.createElement('div');
            sliderH.style.cssText = 'position: absolute; left: 0; right: 0; height: 4px; background: rgba(255,255,255,0.8); box-shadow: 0 0 4px rgba(0,0,0,0.8); z-index: 1000; cursor: ns-resize; top: ' + (sliderY - 2) + 'px; pointer-events: auto;';
            mapContainer.appendChild(sliderH);

            function updateClip() {{
                var img = document.querySelector('.leaflet-image-layer');
                if (!img) return;
                
                var imgRect = img.getBoundingClientRect();
                var mapRect = mapContainer.getBoundingClientRect();
                
                var absSliderX = mapRect.left + sliderX;
                var absSliderY = mapRect.top + sliderY;

                // Calculate insets to ONLY show the bottom-right quadrant of the historical map
                var left_inset = Math.max(0, absSliderX - imgRect.left);
                var top_inset = Math.max(0, absSliderY - imgRect.top);
                var right_inset = 0;
                var bottom_inset = 0;

                img.style.clipPath = 'inset(' + top_inset + 'px ' + right_inset + 'px ' + bottom_inset + 'px ' + left_inset + 'px)';
            }}

            function dragStart(e, isVertical) {{
                e.preventDefault();
                e.stopPropagation();
                
                var moveHandler = function(ev) {{
                    var mapRect = mapContainer.getBoundingClientRect();
                    if (isVertical) {{
                        sliderX = ev.clientX - mapRect.left;
                        if (sliderX < 0) sliderX = 0;
                        if (sliderX > mapRect.width) sliderX = mapRect.width;
                        sliderV.style.left = (sliderX - 2) + 'px';
                    }} else {{
                        sliderY = ev.clientY - mapRect.top;
                        if (sliderY < 0) sliderY = 0;
                        if (sliderY > mapRect.height) sliderY = mapRect.height;
                        sliderH.style.top = (sliderY - 2) + 'px';
                    }}
                    updateClip();
                }};
                
                var upHandler = function() {{
                    document.removeEventListener('mousemove', moveHandler);
                    document.removeEventListener('mouseup', upHandler);
                }};
                
                document.addEventListener('mousemove', moveHandler);
                document.addEventListener('mouseup', upHandler);
            }}
            
            sliderV.addEventListener('mousedown', function(e){{ dragStart(e, true); }});
            sliderH.addEventListener('mousedown', function(e){{ dragStart(e, false); }});

            map.on('move zoom viewreset', updateClip);
            window.addEventListener('resize', updateClip);
            
            updateClip();
        }}, 500);
    }};
    </script>
    """
    m.get_root().html.add_child(Element(slider_js))

    # --- OPACITY SLIDER UI ---
    opacity_html = """
    <div style="position: fixed; top: 10px; left: 50px; z-index: 9999; background: white; padding: 10px 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.3); font-family: sans-serif; font-size: 14px;">
        <label for="opacitySlider" style="font-weight: bold; display: block; margin-bottom: 5px;">1746 Map Opacity: <span id="opacityValue">100%</span></label>
        <input type="range" id="opacitySlider" min="0" max="100" value="100" style="width: 200px;">
    </div>
    """
    m.get_root().html.add_child(Element(opacity_html))

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
