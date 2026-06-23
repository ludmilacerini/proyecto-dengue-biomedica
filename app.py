import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Vigilancia de Dengue — Argentina",
    page_icon="🦟",
    layout="wide"
)

st.title("🦟 Vigilancia de Dengue — Argentina")
st.caption("Herramienta de apoyo a la vigilancia epidemiológica")

# --- CONECTAMOS CON TU MAPA ORIGINAL (TUS DATOS REALES) ---
datos = {
    "Buenos Aires": 625, "CABA": 781, "Córdoba": 2706, "Santa Fe": 1733,
    "Mendoza": 234, "Tucumán": 4814, "Salta": 1673, "Chaco": 1897,
    "Corrientes": 892, "Misiones": 1430, "Entre Ríos": 1361,
    "Santiago del Estero": 1773, "San Juan": 262, "San Luis": 716,
    "La Rioja": 3057, "Catamarca": 2528, "Jujuy": 1742, "Neuquén": 25,
    "Río Negro": 13, "Formosa": 1765, "La Pampa": 153, "Chubut": 11,
    "Santa Cruz": 67, "Tierra del Fuego": 86,
}

lats = {
    "Buenos Aires": -36.6,"CABA": -34.6,"Córdoba": -31.4,"Santa Fe": -31.6,
    "Mendoza": -32.9,"Tucumán": -26.8,"Salta": -24.8,"Chaco": -27.5,
    "Corrientes": -27.5,"Misiones": -27.4,"Entre Ríos": -31.7,"Santiago del Estero": -27.8,
    "San Juan": -31.5,"San Luis": -33.3,"La Rioja": -29.4,"Catamarca": -28.5,
    "Jujuy": -24.2,"Neuquén": -39.0,"Río Negro": -40.8,"Formosa": -26.2,
    "La Pampa": -36.6,"Chubut": -43.3,"Santa Cruz": -51.6,"Tierra del Fuego": -54.8,
}

lons = {
    "Buenos Aires": -60.0,"CABA": -58.4,"Córdoba": -64.2,"Santa Fe": -60.7,
    "Mendoza": -68.8,"Tucumán": -65.2,"Salta": -65.4,"Chaco": -59.0,
    "Corrientes": -58.8,"Misiones": -55.9,"Entre Ríos": -60.5,"Santiago del Estero": -64.3,
    "San Juan": -68.5,"San Luis": -66.3,"La Rioja": -66.9,"Catamarca": -65.8,
    "Jujuy": -65.3,"Neuquén": -68.1,"Río Negro": -63.0,"Formosa": -58.2,
    "La Pampa": -64.3,"Chubut": -65.1,"Santa Cruz": -69.2,"Tierra del Fuego": -68.3,
}

provincias = list(datos.keys())
valores = list(datos.values())
lat_list = [lats[p] for p in provincias]
lon_list = [lons[p] for p in provincias]

def color_nivel(v):
    if v < 500: return "#3fb950"
    elif v < 1500: return "#d29922"
    else: return "#f85149"

colores = [color_nivel(v) for v in valores]
niveles = ["Bajo (<500)" if v < 500 else "Medio (500-1500)" if v < 1500 else "Alto (>1500)" for v in valores]

# --- CONTROL DE SELECCIÓN (Hecho de forma simple con un menú desplegable en vez de clicks complejos) ---
st.sidebar.header("⚙️ Filtros")
provincia_seleccionada = st.sidebar.selectbox(
    "Seleccioná una provincia para analizar:",
    ["Ninguna - Ver Mapa General"] + provincias
)

# --- DIBUJAR TU MAPA ORIGINAL ---
fig = go.Figure()

fig.add_trace(go.Scattergeo(
    lat=lat_list,
    lon=lon_list,
    mode='markers+text',
    marker=dict(
        size=[max(15, min(50, v/80)) for v in valores],
        color=colores,
        opacity=0.85,
        line=dict(width=1, color='#0d1117')
    ),
    text=provincias,
    textposition="top center",
    textfont=dict(size=9, color='#c9d1d9'),
    customdata=list(zip(valores, niveles)),
    hovertemplate="<b>%{text}</b><br>Incidencia: %{customdata[0]} / 100k<br>Nivel: %{customdata[1]}<extra></extra>",
))

fig.update_geos(
    scope='south america',
    showland=True, landcolor='#161b22',
    showocean=True, oceancolor='#0d1117',
    showcountries=True, countrycolor='#30363d',
    showsubunits=True, subunitcolor='#30363d',
    center=dict(lat=-38, lon=-63),
    projection_scale=3.2,
)

fig.update_layout(
    paper_bgcolor='#0d1117',
    plot_bgcolor='#0d1117',
    font_color='#c9d1d9',
    margin=dict(l=0, r=0, t=10, b=0),
    height=500,
    showlegend=False,
)

# Mostramos tu mapa en pantalla
st.plotly_chart(fig, use_container_width=True)

# --- BLOQUE INFERIOR: SE DETECTA LA SELECCIÓN DEL SIDEBAR ---
st.markdown("---")

if provincia_seleccionada != "Ninguna - Ver Mapa General":
    st.subheader(f"📈 Análisis Temporal — {provincia_seleccionada}")
    
    # Creamos datos simulados basados en el valor real de la provincia para que el gráfico tenga sentido
    valor_base = datos[provincia_seleccionada]
    semanas = list(range(1, 11))
    casos_reales = [int(valor_base * (0.4 + 0.05 * i)) for i in semanas]
    casos_predichos = [int(valor_base * (0.42 + 0.048 * i)) for i in semanas]

    df_temporal = pd.DataFrame({
        "Semana Epidemiológica": semanas * 2,
        "Cantidad de Casos": casos_reales + casos_predichos,
        "Tipo": ["Casos Históricos"] * 10 + ["Predicción IA"] * 10
    })

    fig_lineas = px.line(
        df_temporal, 
        x="Semana Epidemiológica", 
        y="Cantidad de Casos", 
        color="Tipo",
        color_discrete_sequence=["#58a6ff", "#ff7b72"],
        template="plotly_dark"
    )
    fig_lineas.update_layout(paper_bgcolor='#0d1117', plot_bgcolor='#0d1117')
    
    st.plotly_chart(fig_lineas, use_container_width=True)
else:
    st.info("💡 Seleccioná una provincia en la barra lateral izquierda para ver las curvas temporales y las predicciones de IA simuladas.")