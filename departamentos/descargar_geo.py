import json, urllib.request, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://raw.githubusercontent.com/gonzalogacc/arg-geojson/main/provincias.geojson"
try:
    with urllib.request.urlopen(url, context=ctx) as r:
        data = r.read().decode('utf-8')
    with open('provincias.geojson', 'w', encoding='utf-8') as f:
        f.write(data)
    print("✓ Descargado correctamente")
except Exception as e:
    print(f"Error: {e}")