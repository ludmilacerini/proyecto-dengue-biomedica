import json

geojson = {
  "type": "FeatureCollection",
  "features": [
    {"type":"Feature","properties":{"nombre":"Buenos Aires"},"geometry":{"type":"Polygon","coordinates":[[[-63.4,-33.3],[-63.4,-34.0],[-62.5,-35.0],[-61.0,-36.0],[-60.0,-37.0],[-58.5,-38.5],[-57.5,-39.5],[-57.0,-40.5],[-57.5,-41.0],[-59.0,-41.5],[-62.0,-41.5],[-65.0,-40.0],[-65.0,-38.0],[-64.0,-37.0],[-64.0,-35.0],[-63.4,-33.3]]]}},
    {"type":"Feature","properties":{"nombre":"Ciudad Autónoma de Buenos Aires"},"geometry":{"type":"Polygon","coordinates":[[[-58.54,-34.52],[-58.33,-34.52],[-58.33,-34.71],[-58.54,-34.71],[-58.54,-34.52]]]}},
    {"type":"Feature","properties":{"nombre":"Córdoba"},"geometry":{"type":"Polygon","coordinates":[[[-63.4,-33.3],[-64.0,-33.0],[-65.0,-33.0],[-66.5,-32.0],[-66.5,-30.0],[-65.5,-28.5],[-65.0,-29.0],[-63.5,-30.5],[-62.5,-32.0],[-63.4,-33.3]]]}},
    {"type":"Feature","properties":{"nombre":"Santa Fe"},"geometry":{"type":"Polygon","coordinates":[[[-62.5,-28.0],[-59.5,-28.0],[-58.5,-26.5],[-59.5,-25.0],[-62.5,-25.0],[-62.5,-28.0]]]}},
    {"type":"Feature","properties":{"nombre":"Mendoza"},"geometry":{"type":"Polygon","coordinates":[[[-66.5,-32.0],[-68.5,-30.5],[-70.5,-32.5],[-70.5,-35.5],[-69.0,-37.0],[-68.0,-36.5],[-65.0,-36.5],[-66.5,-33.0],[-66.5,-32.0]]]}},
    {"type":"Feature","properties":{"nombre":"Tucumán"},"geometry":{"type":"Polygon","coordinates":[[[-64.0,-26.0],[-65.5,-26.0],[-65.5,-27.5],[-65.0,-28.0],[-64.0,-27.5],[-63.5,-27.0],[-64.0,-26.0]]]}},
    {"type":"Feature","properties":{"nombre":"Salta"},"geometry":{"type":"Polygon","coordinates":[[[-63.0,-22.0],[-64.5,-21.8],[-67.5,-22.5],[-67.0,-24.5],[-65.5,-26.5],[-65.0,-25.0],[-63.0,-23.5],[-63.0,-22.0]]]}},
    {"type":"Feature","properties":{"nombre":"Chaco"},"geometry":{"type":"Polygon","coordinates":[[[-58.5,-24.0],[-60.0,-22.5],[-62.5,-22.0],[-62.5,-25.0],[-59.5,-25.0],[-58.5,-26.5],[-58.5,-24.0]]]}},
    {"type":"Feature","properties":{"nombre":"Corrientes"},"geometry":{"type":"Polygon","coordinates":[[[-58.5,-26.5],[-57.5,-25.5],[-56.0,-25.5],[-55.7,-27.5],[-57.0,-28.5],[-58.0,-28.5],[-58.5,-27.5],[-58.5,-26.5]]]}},
    {"type":"Feature","properties":{"nombre":"Misiones"},"geometry":{"type":"Polygon","coordinates":[[[-53.6,-25.5],[-55.7,-25.5],[-56.0,-27.5],[-55.0,-28.2],[-53.6,-27.5],[-53.6,-25.5]]]}},
    {"type":"Feature","properties":{"nombre":"Entre Ríos"},"geometry":{"type":"Polygon","coordinates":[[[-60.5,-30.0],[-59.5,-30.0],[-58.5,-31.5],[-58.0,-33.0],[-59.0,-33.5],[-60.5,-32.5],[-61.0,-31.0],[-60.5,-30.0]]]}},
    {"type":"Feature","properties":{"nombre":"Santiago del Estero"},"geometry":{"type":"Polygon","coordinates":[[[-62.5,-25.0],[-65.0,-25.0],[-65.5,-26.5],[-65.5,-28.5],[-65.0,-29.0],[-63.5,-30.5],[-62.5,-30.0],[-62.5,-25.0]]]}},
    {"type":"Feature","properties":{"nombre":"San Juan"},"geometry":{"type":"Polygon","coordinates":[[[-66.5,-28.0],[-66.5,-30.0],[-67.0,-31.5],[-68.5,-30.5],[-70.5,-30.0],[-70.0,-28.0],[-68.5,-26.0],[-67.0,-27.0],[-66.5,-28.0]]]}},
    {"type":"Feature","properties":{"nombre":"San Luis"},"geometry":{"type":"Polygon","coordinates":[[[-63.4,-33.3],[-65.0,-33.0],[-66.5,-33.0],[-68.5,-32.0],[-68.0,-36.5],[-65.0,-36.5],[-63.4,-35.0],[-63.4,-33.3]]]}},
    {"type":"Feature","properties":{"nombre":"La Rioja"},"geometry":{"type":"Polygon","coordinates":[[[-65.5,-26.5],[-67.0,-27.0],[-68.5,-27.5],[-68.5,-30.5],[-67.0,-31.5],[-66.5,-31.5],[-66.5,-30.0],[-65.5,-28.5],[-65.5,-26.5]]]}},
    {"type":"Feature","properties":{"nombre":"Catamarca"},"geometry":{"type":"Polygon","coordinates":[[[-65.0,-25.0],[-67.0,-25.0],[-68.5,-26.0],[-70.0,-28.0],[-69.5,-29.5],[-68.0,-29.5],[-66.0,-28.0],[-65.5,-26.5],[-65.0,-25.0]]]}},
    {"type":"Feature","properties":{"nombre":"Jujuy"},"geometry":{"type":"Polygon","coordinates":[[[-64.5,-21.8],[-66.0,-21.8],[-67.5,-22.5],[-67.0,-23.5],[-65.5,-23.5],[-64.5,-22.5],[-64.5,-21.8]]]}},
    {"type":"Feature","properties":{"nombre":"Neuquén"},"geometry":{"type":"Polygon","coordinates":[[[-68.0,-36.5],[-69.0,-37.0],[-71.5,-37.5],[-71.5,-40.5],[-68.5,-40.5],[-68.0,-39.5],[-68.0,-36.5]]]}},
    {"type":"Feature","properties":{"nombre":"Río Negro"},"geometry":{"type":"Polygon","coordinates":[[[-62.0,-41.5],[-68.5,-40.5],[-71.5,-40.5],[-71.5,-42.5],[-65.5,-42.5],[-62.0,-43.0],[-62.0,-41.5]]]}},
    {"type":"Feature","properties":{"nombre":"Formosa"},"geometry":{"type":"Polygon","coordinates":[[[-58.5,-22.0],[-62.5,-22.0],[-62.5,-23.5],[-59.0,-23.5],[-58.5,-22.0]]]}},
    {"type":"Feature","properties":{"nombre":"La Pampa"},"geometry":{"type":"Polygon","coordinates":[[[-62.5,-35.0],[-65.0,-36.5],[-68.0,-36.5],[-68.0,-39.5],[-65.0,-40.0],[-62.0,-41.5],[-57.0,-40.5],[-58.5,-38.5],[-60.0,-37.0],[-61.0,-36.0],[-62.5,-35.0]]]}},
    {"type":"Feature","properties":{"nombre":"Chubut"},"geometry":{"type":"Polygon","coordinates":[[[-62.0,-41.5],[-72.0,-42.0],[-72.0,-46.0],[-65.5,-46.0],[-63.0,-45.0],[-62.0,-43.0],[-62.0,-41.5]]]}},
    {"type":"Feature","properties":{"nombre":"Santa Cruz"},"geometry":{"type":"Polygon","coordinates":[[[-62.0,-46.0],[-72.0,-46.0],[-72.5,-52.5],[-65.5,-52.0],[-63.0,-50.0],[-62.0,-48.0],[-62.0,-46.0]]]}},
    {"type":"Feature","properties":{"nombre":"Tierra del Fuego"},"geometry":{"type":"Polygon","coordinates":[[[-63.5,-52.5],[-72.5,-52.5],[-69.5,-55.1],[-66.0,-55.1],[-63.5,-54.0],[-63.5,-52.5]]]}}
  ]
}

with open('provincias.geojson', 'w', encoding='utf-8') as f:
    json.dump(geojson, f)

print("✓ GeoJSON creado correctamente")