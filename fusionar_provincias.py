import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from collections import defaultdict

with open('datos/departamentos_argentina.geojson', encoding='utf-8') as f:
    geo = json.load(f)

# Agrupar departamentos por provincia
provincias = defaultdict(list)
prov_codes = {}
for f in geo['features']:
    prov = f['properties']['provincia']
    prov_codes[prov] = f['properties']['prov_code']
    try:
        geom = shape(f['geometry'])
        if geom.is_valid:
            provincias[prov].append(geom)
    except:
        continue

# Fusionar y guardar
features = []
for prov_name, geoms in provincias.items():
    try:
        merged = unary_union(geoms)
        features.append({
            'type': 'Feature',
            'properties': {
                'provincia': prov_name,
                'prov_code': prov_codes[prov_name]
            },
            'geometry': mapping(merged)
        })
        print(f'✓ {prov_name}')
    except Exception as e:
        print(f'✗ {prov_name}: {e}')

geo_prov = {'type': 'FeatureCollection', 'features': features}
with open('datos/provincias_argentina.geojson', 'w', encoding='utf-8') as f:
    json.dump(geo_prov, f, ensure_ascii=False)

print(f'\nListo — {len(features)} provincias guardadas')