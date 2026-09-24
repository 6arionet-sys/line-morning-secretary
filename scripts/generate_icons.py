import os
import urllib.request
import re
import resvg_py

ICONS = [
    ("fish_on.png", "fish", "#2E8BC0"),
    ("fish_off.png", "fish", "#DDDDDD"),
    ("sunny.png", "sun", "#E08A2E"),
    ("cloudy.png", "cloud", "#8A94A6"),
    ("rainy.png", "cloud-rain", "#2E6FB5"),
    ("snowy.png", "snowflake", "#5BA4CF"),
    ("umbrella.png", "umbrella", "#2E6FB5"),
    ("umbrella_small.png", "umbrella", "#6B7280"),
    ("umbrella_off.png", "umbrella-off", "#C9A27A"),
    ("hanger.png", "hanger", "#FFFFFF"),
    ("home.png", "home", "#FFFFFF"),
    ("calendar.png", "calendar", "#185FA5"),
    ("wind.png", "wind", "#5F7A8A"),
    ("wave.png", "ripple", "#2E8BC0"),
    ("dir_n.png", "arrow-down", "#5F7A8A"),
    ("dir_ne.png", "arrow-down-left", "#5F7A8A"),
    ("dir_e.png", "arrow-left", "#5F7A8A"),
    ("dir_se.png", "arrow-up-left", "#5F7A8A"),
    ("dir_s.png", "arrow-up", "#5F7A8A"),
    ("dir_sw.png", "arrow-up-right", "#5F7A8A"),
    ("dir_w.png", "arrow-right", "#5F7A8A"),
    ("dir_nw.png", "arrow-down-right", "#5F7A8A"),
    ("flame.png", "flame", "#D9622B"),
    ("trash.png", "trash", "#6B6B6B"),
    ("recycle.png", "recycle", "#2E8B57"),
    ("bottle.png", "bottle", "#2E8BC0"),
    ("box.png", "box", "#A0703C"),
    ("sofa.png", "sofa", "#7A5C99"),
]

output_dir = os.path.join(os.path.dirname(__file__), "..", "icons")
os.makedirs(output_dir, exist_ok=True)

headers = {'User-Agent': 'Mozilla/5.0'}

for filename, tabler_name, color in ICONS:
    url = f"https://raw.githubusercontent.com/tabler/tabler-icons/main/icons/outline/{tabler_name}.svg"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            svg_text = resp.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching {tabler_name}: {e}")
        continue
    
    # Replace stroke="currentColor" with stroke="{color}"
    svg_text = re.sub(r'stroke="[^"]*"', f'stroke="{color}"', svg_text)
    # Ensure width and height are 96
    svg_text = re.sub(r'width="[^"]*"', 'width="96"', svg_text)
    svg_text = re.sub(r'height="[^"]*"', 'height="96"', svg_text)
    
    png_data = resvg_py.svg_to_bytes(svg_text)
    out_file = os.path.join(output_dir, filename)
    with open(out_file, "wb") as f:
        f.write(png_data)
    print(f"Generated {filename}")

print("All icons generated successfully!")
