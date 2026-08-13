import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_option_menu import option_menu

# ── CONFIGURACIÓN ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DengueWatch Argentina", 
    page_icon="🦟", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CARGA DE DATOS CON CACHE ───────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_datos():
    pred = pd.read_csv("datos/predicciones.csv")
    hist = pd.read_csv("datos/dataset_provincial_escalado.csv")
    riesgo = pd.read_csv("datos/riesgo_departamental.csv")
    riesgo["depto_id_norm"] = riesgo["depto_id_norm"].astype(int)

    with open("datos/departamentos_argentina.geojson", encoding="utf-8") as f:
        geo_dept = json.load(f)
    with open("datos/provincias_argentina.geojson", encoding="utf-8") as f:
        geo_prov = json.load(f)

    return pred, hist, riesgo, geo_dept, geo_prov


pred, hist, riesgo, geo_dept, geo_prov = cargar_datos()
PROVINCIAS = sorted(pred["provincia"].unique())

# ── ESTILOS GLOBALES ──────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

#MainMenu, footer { visibility: hidden; }
header { visibility: visible !important; background: transparent !important; }

/* Botón flotante al costado para abrir el menú */
[data-testid="stSidebarCollapseButton"], [data-testid="stHeader"] button {
    visibility: visible !important;
    display: flex !important;
    color: #58a6ff !important;
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
}

.block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }

/* Header principal */
.dw-header {
    background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
    border: 1px solid #30363d;
    border-radius: 14px;
    padding: 1.1rem 1.5rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.dw-logo { font-size: 28px; margin-right: 12px; }
.dw-title { font-size: 19px; font-weight: 700; color: #e6edf3; line-height: 1.2; }
.dw-sub { font-size: 11px; color: #6e7681; margin-top: 2px; }
.dw-badge {
    background: rgba(63,185,80,0.12);
    color: #3fb950;
    border: 1px solid rgba(63,185,80,0.25);
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.05em;
}

/* Cards */
.cards-row { display: flex; gap: 10px; margin-bottom: 1rem; }
.nc {
    flex: 1;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 14px 18px;
    min-width: 130px;
}
.nc-label { font-size: 10px; color: #6e7681; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
.nc-val { font-size: 24px; font-weight: 700; color: #e6edf3; line-height: 1.1; }
.nc-val-sm { font-size: 16px; font-weight: 600; color: #e6edf3; line-height: 1.2; }
.nc-sub { font-size: 11px; color: #8b949e; margin-top: 4px; }
.nc-up { color: #f85149 !important; }
.nc-down { color: #3fb950 !important; }
.nc-alert-rojo { color: #f85149 !important; }
.nc-alert-amarillo { color: #d29922 !important; }
.nc-alert-verde { color: #3fb950 !important; }

.dw-divider { height: 1px; background: #21262d; margin: 0.8rem 0; }

.map-legend {
    display: flex;
    gap: 18px;
    font-size: 12px;
    color: #8b949e;
    margin: 6px 0 10px;
    align-items: center;
}
.leg-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 5px;
}

.breadcrumb {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    padding: 6px 0;
    margin-bottom: 8px;
}
.bread-inactive { color: #6e7681; }
.bread-sep { color: #30363d; }
.bread-active { color: #e6edf3; font-weight: 600; }
</style>
""",
    unsafe_allow_html=True,
)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="dw-header">
    <div style="display:flex; align-items:center;">
        <span class="dw-logo">🦟</span>
        <div>
            <div class="dw-title">DengueWatch Argentina</div>
            <div class="dw-sub">Sistema de monitoreo y predicción epidemiológica &nbsp;·&nbsp; PI Ingeniería Biomédica &nbsp;·&nbsp; FCEFyN · FCM · UNC</div>
        </div>
    </div>
    <span class="dw-badge">● SISTEMA ACTIVO</span>
</div>
""",
    unsafe_allow_html=True,
)

# ── CÁLCULO DE CARDS NACIONALES ───────────────────────────────────────────────
ultimo_anio = riesgo["anio"].max()
ultima_semana = riesgo[riesgo["anio"] == ultimo_anio]["semana"].max()
datos_rec = riesgo[
    (riesgo["anio"] == ultimo_anio) & (riesgo["semana"] == ultima_semana)
]
datos_ant = riesgo[
    (riesgo["anio"] == ultimo_anio)
    & (riesgo["semana"] == max(ultima_semana - 1, 1))
]

casos_rec = int(datos_rec["casos_dengue"].sum())
casos_ant = int(datos_ant["casos_dengue"].sum())
variacion = casos_rec - casos_ant

deptos_alto = int((datos_rec["nivel_mult"] == "alto").sum())
prov_max = datos_rec.groupby("provincia")["casos_dengue"].sum()
prov_top = prov_max.idxmax() if prov_max.max() > 0 else "Sin datos"

if deptos_alto > 150:
    alerta_txt, alerta_cls = "🔴 ALERTA", "nc-alert-rojo"
elif deptos_alto > 80:
    alerta_txt, alerta_cls = "🟡 ATENCIÓN", "nc-alert-amarillo"
else:
    alerta_txt, alerta_cls = "🟢 NORMAL", "nc-alert-verde"

var_cls = "nc-up" if variacion > 0 else "nc-down"
var_icon = "▲" if variacion > 0 else "▼"

st.markdown(
    f"""
<div class="cards-row">
  <div class="nc">
    <div class="nc-label">Casos esta semana</div>
    <div class="nc-val">{casos_rec:,}</div>
    <div class="nc-sub {var_cls}">{var_icon} {abs(variacion):,} vs semana anterior</div>
  </div>
  <div class="nc">
    <div class="nc-label">Departamentos en alerta</div>
    <div class="nc-val nc-alert-rojo">{deptos_alto}</div>
    <div class="nc-sub">de 527 departamentos</div>
  </div>
  <div class="nc">
    <div class="nc-label">Provincia más afectada</div>
    <div class="nc-val-sm">{prov_top}</div>
    <div class="nc-sub">Semana {ultima_semana} / {ultimo_anio}</div>
  </div>
  <div class="nc">
    <div class="nc-label">Estado del sistema</div>
    <div class="nc-val-sm {alerta_cls}">{alerta_txt}</div>
    <div class="nc-sub">{deptos_alto} deptos. en riesgo alto</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# MENÚ NAVEGABLE AL COSTADO (SIDEBAR MENU)
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 📌 Navegación")
    
    # Menú lateral estilizado con las 2 secciones
    menu_seleccionado = option_menu(
        menu_title=None,
        options=["Mapa de riesgo", "Monitoreo del modelo"],
        icons=["map", "graph-up-arrow"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#0d1117"},
            "icon": {"color": "#58a6ff", "font-size": "16px"},
            "nav-link": {
                "font-size": "14px",
                "text-align": "left",
                "margin": "4px 0",
                "color": "#c9d1d9",
                "--hover-color": "#161b22",
            },
            "nav-link-selected": {
                "background-color": "#21262d",
                "color": "#58a6ff",
                "font-weight": "600",
            },
        },
    )

# ══════════════════════════════════════════════════════════════════════════════
# VISTA 1: MAPA DE RIESGO DEPARTAMENTAL
# ══════════════════════════════════════════════════════════════════════════════
if menu_seleccionado == "Mapa de riesgo":
    if "provincia_seleccionada" not in st.session_state:
        st.session_state.provincia_seleccionada = None

    with st.container(border=True):
        col_m1, col_m2 = st.columns([1, 3])
        with col_m1:
            anio_mapa = st.selectbox(
                "📅 Año epidemiológico",
                sorted(riesgo["anio"].unique(), reverse=True),
                key="anio_mapa",
            )
        with col_m2:
            semanas_disp = sorted(
                riesgo[riesgo["anio"] == anio_mapa]["semana"].unique()
            )
            semana_mapa = st.slider(
                "⏱️ Semana epidemiológica (SE)",
                min_value=int(min(semanas_disp)),
                max_value=int(max(semanas_disp)),
                value=int(max(semanas_disp)),
                key="semana_mapa",
            )

    riesgo_filtrado = riesgo[
        (riesgo["anio"] == anio_mapa) & (riesgo["semana"] == semana_mapa)
    ].copy()
    riesgo_filtrado["depto_id_norm"] = riesgo_filtrado["depto_id_norm"].astype(int)

    def seleccionar_provincia():
        if st.session_state.prov_selector_mapa != "— Seleccioná una provincia —":
            st.session_state.provincia_seleccionada = st.session_state.prov_selector_mapa

    if st.session_state.provincia_seleccionada is None:
        n_alto = int((riesgo_filtrado["nivel_mult"] == "alto").sum())
        n_medio = int((riesgo_filtrado["nivel_mult"] == "medio").sum())
        n_bajo = int((riesgo_filtrado["nivel_mult"] == "bajo").sum())

        ma, mm, mb = st.columns(3)
        ma.metric("🔴 Riesgo alto", f"{n_alto} deptos.")
        mm.metric("🟡 Riesgo medio", f"{n_medio} deptos.")
        mb.metric("🟢 Riesgo bajo", f"{n_bajo} deptos.")

        casos_prov = (
            riesgo_filtrado.groupby("provincia")
            .agg(
                casos_totales=("casos_dengue", "sum"),
                deptos_alto=("nivel_mult", lambda x: (x == "alto").sum()),
                deptos_total=("depto_id_norm", "count"),
            )
            .reset_index()
        )

        casos_prov["casos_log"] = np.log1p(casos_prov["casos_totales"])
        max_log = casos_prov["casos_log"].max()

        st.markdown(
            """
        <div style="background: #161b22; padding: 12px 16px; border-radius: 10px; border: 1px solid #30363d; margin-top: 10px; margin-bottom: 10px;">
            <span style="font-size: 14px; color: #58a6ff; font-weight: 600;">🔎 Explorador Departamental</span>
            <p style="font-size: 11px; color: #8b949e; margin: 2px 0 6px 0;">Selecciona una provincia para ver el mapa detallado de nivel de riesgo por departamento.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        provincias_filtradas = [
            p for p in sorted(casos_prov["provincia"].tolist()) if "Tierra del Fuego" not in p
        ]

        st.selectbox(
            "Seleccionar provincia:",
            ["— Seleccioná una provincia —"] + provincias_filtradas,
            key="prov_selector_mapa",
            on_change=seleccionar_provincia,
            label_visibility="collapsed",
        )

        # Aseguramos el formateo de casos para el cartelito (hover)
        casos_prov["Casos acumulados"] = casos_prov["casos_totales"].apply(lambda x: f"{int(x):,}")

        fig_prov = px.choropleth(
            casos_prov,
            geojson=geo_prov,
            locations="provincia",
            featureidkey="properties.provincia",
            color="casos_log",
            color_continuous_scale=[
                [0.0, "#1c2128"],
                [0.15, "#1a3a2a"],
                [0.35, "#3fb950"],
                [0.60, "#d29922"],
                [0.80, "#e85b30"],
                [1.0, "#f85149"],
            ],
            range_color=[0, max_log if max_log > 0 else 1],
            hover_name="provincia",
            hover_data={
                "Casos acumulados": True,
                "deptos_alto": True,
                "casos_log": False,
                "casos_totales": False,
                "provincia": False,
            },
            labels={
                "deptos_alto": "Deptos. en riesgo alto",
            },
        )
        
        # Personalizamos el cartelito flotante al pasar el mouse
        fig_prov.update_traces(
            hovertemplate="<b>%{hovertext}</b><br>🦠 Casos: <b>%{customdata[0]}</b><br>🔴 Deptos. en riesgo alto: <b>%{customdata[1]}</b><extra></extra>"
        )

        fig_prov.update_geos(
            visible=True, fitbounds="locations", showland=True, landcolor="#1c2128",
            showocean=True, oceancolor="#0d1117", showcountries=True, countrycolor="#30363d",
            showcoastlines=False, bgcolor="#0d1117",
        )
        fig_prov.update_layout(
            paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="#c9d1d9",
            margin=dict(l=0, r=0, t=10, b=0), height=620,
            coloraxis_colorbar=dict(
                title="Riesgo", tickfont=dict(color="#8b949e", size=10), thickness=12, len=0.6,
                tickvals=[0, max_log * 0.33, max_log * 0.66, max_log] if max_log > 0 else [0, 1],
                ticktext=["Bajo", "Medio-Bajo", "Medio-Alto", "Alto"] if max_log > 0 else ["0", "1"],
            ),
        )
        st.plotly_chart(fig_prov, use_container_width=True)

    else:
        prov_actual = st.session_state.provincia_seleccionada
        col_back, col_bread = st.columns([1, 4])
        with col_back:
            if st.button("🗺️ ← Volver al mapa nacional", type="secondary"):
                st.session_state.provincia_seleccionada = None
                st.rerun()
        with col_bread:
            st.markdown(
                f"""
            <div class="breadcrumb" style="padding-top: 10px;">
                <span class="bread-inactive">Argentina</span>
                <span class="bread-sep">›</span>
                <span class="bread-active">{prov_actual}</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

        riesgo_prov = riesgo_filtrado[riesgo_filtrado["provincia"] == prov_actual].copy()
        
        # Cálculo de totales y métricas de la provincia
        casos_prov_totales = int(riesgo_prov["casos_dengue"].sum())
        n_alto_p = int((riesgo_prov["nivel_mult"] == "alto").sum())
        n_medio_p = int((riesgo_prov["nivel_mult"] == "medio").sum())
        n_bajo_p = int((riesgo_prov["nivel_mult"] == "bajo").sum())

        # 1. Tarjetas con Casos Totales + Niveles de Riesgo
        mc, ma, mm, mb = st.columns(4)
        mc.metric("🦠 Casos totales prov.", f"{casos_prov_totales:,}")
        ma.metric("🔴 Riesgo alto", f"{n_alto_p} deptos.")
        mm.metric("🟡 Riesgo medio", f"{n_medio_p} deptos.")
        mb.metric("🟢 Riesgo bajo", f"{n_bajo_p} deptos.")

        st.markdown(
            """
        <div class="map-legend">
            <span><span class="leg-dot" style="background:#3fb950"></span>Riesgo bajo</span>
            <span><span class="leg-dot" style="background:#d29922"></span>Riesgo medio</span>
            <span><span class="leg-dot" style="background:#f85149"></span>Riesgo alto</span>
            <span style="color:#30363d; margin-left:4px;">· basado en índice climático + estructural</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

        features_prov = [
            f for f in geo_dept['features'] 
            if f['properties'].get('provincia') == prov_actual or f['properties'].get('PROVINCIA') == prov_actual
        ]
        
        all_lats, all_lons = [], []
        for feat in features_prov:
            for c in feat['geometry']['coordinates'][0]:
                all_lons.append(c[0])
                all_lats.append(c[1])
        centro_lat = sum(all_lats) / len(all_lats) if all_lats else -38
        centro_lon = sum(all_lons) / len(all_lons) if all_lons else -63

        lat_span = max(all_lats) - min(all_lats) if all_lats else 5
        zoom = 11 if lat_span < 0.3 else 9 if lat_span < 1 else 7 if lat_span < 3 else 6 if lat_span < 6 else 5

        color_map = {'bajo': '#16a34a', 'medio': '#d97706', 'alto': '#dc2626'}
        riesgo_dict = dict(zip(riesgo_prov['depto_id_norm'].astype(str), riesgo_prov['nivel_mult']))
        nombre_dept_dict = dict(zip(riesgo_prov['depto_id_norm'].astype(str), riesgo_prov['depto_nombre']))
        clima_dict = dict(zip(riesgo_prov['depto_id_norm'].astype(str), riesgo_prov['factor_clima']))
        nbi_dict = dict(zip(riesgo_prov['depto_id_norm'].astype(str), riesgo_prov['score_terreno']))
        casos_dict = dict(zip(riesgo_prov['depto_id_norm'].astype(str), riesgo_prov['casos_dengue']))

        m_dept = folium.Map(location=[centro_lat, centro_lon], zoom_start=zoom, tiles='CartoDB positron', scrollWheelZoom=True)

        for feat in features_prov:
            did = str(feat['properties']['depto_id'])
            nivel = riesgo_dict.get(did, 'bajo')
            color = color_map.get(nivel, '#16a34a')
            nombre = nombre_dept_dict.get(did, feat['properties']['nombre'])
            clima = clima_dict.get(did, 0)
            nbi = nbi_dict.get(did, 0)
            casos_depto = int(casos_dict.get(did, 0))

            # 2. Tooltip con la cantidad de casos destacada
            folium.GeoJson(
                feat,
                style_function=lambda x, c=color: {'fillColor': c, 'color': '#64748b', 'weight': 1, 'fillOpacity': 0.75},
                highlight_function=lambda x: {'fillOpacity': 0.95, 'weight': 2.5, 'color': '#1a56db'},
                tooltip=folium.Tooltip(
                    f"<b>{nombre}</b><br>"
                    f"🦠 Casos de Dengue: <b>{casos_depto:,}</b><br>"
                    f"Nivel de Riesgo: <b>{nivel.capitalize()}</b><br>"
                    f"Factor climático: {clima:.3f}<br>"
                    f"Score estructural: {nbi:.3f}", 
                    sticky=True
                ),
            ).add_to(m_dept)

        st_folium(m_dept, height=550, use_container_width=True, returned_objects=[])

        # 3. Tabla de detalle incluyendo la columna de casos
        with st.expander("📋 Ver clasificación de riesgo y casos por departamento"):
            tabla_dept = riesgo_prov[["depto_nombre", "casos_dengue", "nivel_mult", "factor_clima", "score_terreno"]].copy()
            tabla_dept["nivel_mult"] = tabla_dept["nivel_mult"].str.capitalize()
            tabla_dept.columns = ["Departamento", "Casos Dengue", "Nivel de riesgo", "Factor climático", "Score estructural"]
            tabla_dept = tabla_dept.sort_values("Casos Dengue", ascending=False)
            st.dataframe(tabla_dept, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# VISTA 2: MONITOREO DEL MODELO (AL SELECCIONAR DESDE EL MENÚ LATERAL)
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# VISTA 2: MONITOREO DEL MODELO (OPTIMIZADO SEGÚN INTERPRETACIÓN CLÍNICA/EPI)
# ══════════════════════════════════════════════════════════════════════════════
elif menu_seleccionado == "Monitoreo del modelo":
    st.subheader("📊 Monitoreo y Evaluación del Modelo Predictivo")

    # Controles de selección
    with st.container(border=True):
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([3, 2, 2])
        with col_ctrl1:
            prov_sel = st.selectbox("Provincia", PROVINCIAS, key="prov_pred_sel")
        with col_ctrl2:
            horizonte_sel = st.radio("Horizonte de predicción", ["t+2 (2 semanas)", "t+4 (4 semanas)"], horizontal=True, key="horiz_pred_sel")
        with col_ctrl3:
            anio_sel = st.radio("Año de evaluación", [2024, 2025], horizontal=True, key="anio_pred_sel")

    horizonte_key = "t+2" if "t+2" in horizonte_sel else "t+4"

    pred_prov = pred[
        (pred["provincia"] == prov_sel)
        & (pred["horizonte"] == horizonte_key)
        & (pred["anio"] == anio_sel)
    ].copy()

    if len(pred_prov) > 0:
        # Cálculo de métricas epidemiológicas y estadísticas
        pico_real = pred_prov["casos_real"].max()
        pico_pred = pred_prov["pred"].max()
        sem_pico_real = int(pred_prov.loc[pred_prov["casos_real"].idxmax(), "semana_epi"])
        sem_pico_pred = int(pred_prov.loc[pred_prov["pred"].idxmax(), "semana_epi"])
        dif_semanas = abs(sem_pico_real - sem_pico_pred)

        # Cálculo del R² (Coeficiente de Determinación)
        ss_res = np.sum((pred_prov["casos_real"] - pred_prov["pred"]) ** 2)
        ss_tot = np.sum((pred_prov["casos_real"] - pred_prov["casos_real"].mean()) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        r2 = max(0, r2) # Ajuste visual si fuera negativo por baja varianza

        # Clasificación contextual del comportamiento (Chip de contexto)
        if pico_real > 10000:
            chip_txt = "🟡 Mega-brote — Magnitud subestimada"
            chip_bg = "rgba(210, 153, 34, 0.15)"
            chip_border = "#d29922"
            chip_color = "#f0b429"
        elif r2 > 0.6:
            chip_txt = "🟢 Transmisión media / alta — Buen ajuste"
            chip_bg = "rgba(63, 185, 80, 0.15)"
            chip_border = "#3fb950"
            chip_color = "#3fb950"
        else:
            chip_txt = "🔵 Transmisión baja / Dinámica local"
            chip_bg = "rgba(88, 166, 255, 0.15)"
            chip_border = "#58a6ff"
            chip_color = "#58a6ff"

        # Encabezado con Provincia + Chip de Desempeño
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-top: 10px; margin-bottom: 5px;">
                <h3 style="margin: 0; padding: 0;">{prov_sel} ({anio_sel})</h3>
                <span style="background: {chip_bg}; border: 1px solid {chip_border}; color: {chip_color}; 
                             padding: 4px 12px; border-radius: 16px; font-size: 12px; font-weight: 600;">
                    {chip_txt}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 1. INSIGHT DESTACADO (Lo primero que el ojo lee)
        if dif_semanas == 0:
            msg_pico = f"🎯 <b>Pico exacto</b> coincidente en la <b>Semana {sem_pico_real}</b>."
        elif dif_semanas == 1:
            msg_pico = f"🎯 <b>Anticipación efectiva del pico:</b> Detección oportuna con solo <b>1 semana de diferencia</b> (Real SE {sem_pico_real}, Predicho SE {sem_pico_pred})."
        else:
            msg_pico = f"⏱️ <b>Desfasaje del pico:</b> {dif_semanas} semanas de diferencia entre real (SE {sem_pico_real}) y predicho (SE {sem_pico_pred})."

        st.info(msg_pico)

        # 2. EL GRÁFICO COMO ESTRELLA PRINCIPAL (Arriba)
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=pred_prov["semana_epi"],
                y=pred_prov["casos_real"],
                mode="lines",
                name=f"Casos Reales ({anio_sel})",
                fill="tozeroy",
                fillcolor="rgba(88,166,255,0.08)",
                line=dict(color="#58a6ff", width=3),
                hovertemplate="Real — Sem %{x}: %{y:,.0f} casos<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=pred_prov["semana_epi"],
                y=pred_prov["pred"],
                mode="lines+markers",
                name=f"Predicción ({horizonte_key})",
                line=dict(color="#f85149", width=2.5, dash="dash"),
                marker=dict(size=5, symbol="diamond", color="#f85149"),
                hovertemplate="Predicción — Sem %{x}: %{y:,.0f} casos<extra></extra>",
            )
        )

        fig.update_layout(
            paper_bgcolor="#0d1117",
            plot_bgcolor="#161b22",
            font_color="#c9d1d9",
            height=460,
            margin=dict(l=10, r=10, t=10, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(title="Semana epidemiológica", gridcolor="#1c2128", showgrid=True, range=[0, 53]),
            yaxis=dict(title="Casos notificados", gridcolor="#1c2128", showgrid=True),
            hovermode="x unified",
        )

        st.plotly_chart(fig, use_container_width=True)

        # 3. TARJETAS DE MÉTRICAS CONTEXTUALIZADAS (R² + Diagnóstico del Brote)
        pct_cobertura_pico = (pico_pred / pico_real * 100) if pico_real > 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Ajuste de Curva (R²)", f"{r2:.2f}", f"Explica el {r2*100:.0f}% de la variación")
        m2.metric("Pico Real", f"{pico_real:,.0f} casos", f"Semana {sem_pico_real}")
        m3.metric("Pico Predicho", f"{pico_pred:,.0f} casos", f"Semana {sem_pico_pred}")
        m4.metric("Captura de Magnitud", f"{pct_cobertura_pico:.0f}%", f"del volumen en la cresta")

        st.markdown('<div class="dw-divider"></div>', unsafe_allow_html=True)

        # Tabla de detalle desplegable
        with st.expander("📋 Ver tabla de datos semanales y desviación"):
            tabla = pred_prov[["semana_epi", "casos_real", "pred"]].copy()
            tabla.columns = ["Semana EP", "Casos Reales", "Predicción Modelo"]
            tabla["Diferencia (Casos)"] = (tabla["Predicción Modelo"] - tabla["Casos Reales"]).round(0)
            st.dataframe(tabla, use_container_width=True, hide_index=True)
    else:
        st.warning("No hay datos de evaluación disponibles para la selección actual.")