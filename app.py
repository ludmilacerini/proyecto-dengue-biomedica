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

# ── LIMPIEZA DE DATOS Y AÑOS ─────────────────────────────────────────────────
for df in [pred, hist, riesgo]:
    if "anio" in df.columns:
        df["anio"] = pd.to_numeric(df["anio"], errors="coerce").fillna(0).astype(int)

ANIOS_DISPONIBLES = sorted(
    [a for a in (set(pred["anio"]) | set(hist["anio"]) | set(riesgo["anio"])) if a > 2000],
    reverse=True
)

if "casos_dengue" in riesgo.columns:
    riesgo["casos_dengue"] = pd.to_numeric(riesgo["casos_dengue"], errors="coerce").fillna(0)
if "casos_real" in pred.columns:
    pred["casos_real"] = pd.to_numeric(pred["casos_real"], errors="coerce").fillna(0)

PROVINCIAS = sorted(pred["provincia"].unique())

# Tabla base de departamentos para proyecciones futuras
deptos_base = riesgo[["depto_id_norm", "depto_nombre", "provincia", "score_terreno", "factor_clima"]].drop_duplicates(subset=["depto_id_norm"]).copy()

# ── ESTILOS GLOBALES ──────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

#MainMenu, footer { visibility: hidden; }
header { visibility: visible !important; background: transparent !important; }

[data-testid="stSidebarCollapseButton"], [data-testid="stHeader"] button {
    visibility: visible !important;
    display: flex !important;
    color: #58a6ff !important;
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
}

.block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }

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

# ── CÁLCULO INTELIGENTE DE CARDS NACIONALES ──────────────────────────────────
riesgo_con_casos = riesgo[riesgo["casos_dengue"] > 0]
if not riesgo_con_casos.empty:
    ultimo_anio = int(riesgo_con_casos["anio"].max())
    ultima_semana = int(riesgo_con_casos[riesgo_con_casos["anio"] == ultimo_anio]["semana"].max())
else:
    ultimo_anio = int(riesgo["anio"].max())
    ultima_semana = int(riesgo[riesgo["anio"] == ultimo_anio]["semana"].max())

datos_rec = riesgo[(riesgo["anio"] == ultimo_anio) & (riesgo["semana"] == ultima_semana)]
datos_ant = riesgo[(riesgo["anio"] == ultimo_anio) & (riesgo["semana"] == max(ultima_semana - 1, 1))]

casos_rec = int(datos_rec["casos_dengue"].sum())
casos_ant = int(datos_ant["casos_dengue"].sum())
variacion = casos_rec - casos_ant

deptos_alto = int((datos_rec["nivel_mult"] == "alto").sum())
prov_max = datos_rec.groupby("provincia")["casos_dengue"].sum()
prov_top = prov_max.idxmax() if (not prov_max.empty and prov_max.max() > 0) else "Sin datos"

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
# VISTA 1: MAPA DE RIESGO
# ══════════════════════════════════════════════════════════════════════════════
if menu_seleccionado == "Mapa de riesgo":
    if "provincia_seleccionada" not in st.session_state:
        st.session_state.provincia_seleccionada = None

    with st.container(border=True):
        col_m1, col_m2 = st.columns([1, 3])
        with col_m1:
            anio_mapa = st.selectbox(
                "📅 Año epidemiológico",
                ANIOS_DISPONIBLES,
                key="anio_mapa",
            )
        with col_m2:
            semanas_r = riesgo[riesgo["anio"] == anio_mapa]["semana"].dropna().unique()
            semanas_p = pred[pred["anio"] == anio_mapa]["semana_epi"].dropna().unique()
            semanas_disp = sorted(set(semanas_r) | set(semanas_p))

            if len(semanas_disp) > 0:
                min_sem = int(min(semanas_disp))
                max_sem = int(max(semanas_disp))
                def_sem = max_sem
            else:
                min_sem = 1
                max_sem = 52
                def_sem = 1

            semana_mapa = st.slider(
                "📅 Semana Epidemiológica",
                min_value=min_sem,
                max_value=max_sem,
                value=def_sem,
                key="sem_mapa"
            )

    # Filtrar datos o generar proyecciones
    riesgo_filtrado = riesgo[
        (riesgo["anio"] == anio_mapa) & (riesgo["semana"] == semana_mapa)
    ].copy()

    es_proyeccion = False

    if riesgo_filtrado.empty or riesgo_filtrado["casos_dengue"].sum() == 0:
        pred_sem = pred[(pred["anio"] == anio_mapa) & (pred["semana_epi"] == semana_mapa)]
        if pred_sem.empty:
            pred_sem = pred[pred["anio"] == anio_mapa]
        
        if not pred_sem.empty:
            es_proyeccion = True
            prov_pred_map = pred_sem.groupby("provincia")["pred"].mean().to_dict()

            df_proj = deptos_base.copy()
            df_proj["anio"] = anio_mapa
            df_proj["semana"] = semana_mapa
            df_proj["pred_prov"] = df_proj["provincia"].map(prov_pred_map).fillna(0)

            def_denom = df_proj.groupby("provincia")["score_terreno"].transform("sum").replace(0, 1)
            df_proj["casos_dengue"] = np.round(df_proj["pred_prov"] * (df_proj["score_terreno"] / def_denom))

            def clasificar_riesgo(row):
                c = row["casos_dengue"]
                sc = row["score_terreno"]
                if c > 15 or (c > 3 and sc > 0.6):
                    return "alto"
                elif c > 1 or sc > 0.35:
                    return "medio"
                else:
                    return "bajo"

            df_proj["nivel_mult"] = df_proj.apply(clasificar_riesgo, axis=1)
            riesgo_filtrado = df_proj

    if es_proyeccion:
        st.info(f"🔮 **Mapa de Proyección Predictiva ({anio_mapa})**: Estimación de riesgo basada en el modelo para la Semana {semana_mapa}.")

    riesgo_filtrado["depto_id_norm"] = riesgo_filtrado["depto_id_norm"].astype(int)

    # ──────────────────────────────────────────────────────────────────────────
    # VISTA NACIONAL EN FOLIUM (ESTÉTICA HOMOGÉNEA)
    # ──────────────────────────────────────────────────────────────────────────
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

        st.markdown(
            """
        <div style="background: #161b22; padding: 12px 16px; border-radius: 10px; border: 1px solid #30363d; margin-top: 10px; margin-bottom: 10px;">
            <span style="font-size: 14px; color: #58a6ff; font-weight: 600;">🔎 Explorador Departamental</span>
            <p style="font-size: 11px; color: #8b949e; margin: 2px 0 6px 0;">Hacé clic sobre una provincia en el mapa o seleccionala en el desplegable para hacer zoom en sus departamentos.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        provincias_filtradas = [
            p for p in sorted(casos_prov["provincia"].tolist()) if "Tierra del Fuego" not in p
        ]

        def seleccionar_provincia():
            if st.session_state.prov_selector_mapa != "— Seleccioná una provincia —":
                st.session_state.provincia_seleccionada = st.session_state.prov_selector_mapa

        st.selectbox(
            "Seleccionar provincia:",
            ["— Seleccioná una provincia —"] + provincias_filtradas,
            key="prov_selector_mapa",
            on_change=seleccionar_provincia,
            label_visibility="collapsed",
        )

        st.markdown(
            """
        <div class="map-legend">
            <span><span class="leg-dot" style="background:#16a34a"></span>Bajo</span>
            <span><span class="leg-dot" style="background:#eab308"></span>Medio</span>
            <span><span class="leg-dot" style="background:#f97316"></span>Alto</span>
            <span><span class="leg-dot" style="background:#dc2626"></span>Muy Alto</span>
            <span style="color:#30363d; margin-left:4px;">· hacé clic en cualquier provincia para ver departamentos</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Mapa Folium Argentina
        m_nac = folium.Map(
            location=[-38.416097, -63.616672],
            zoom_start=4,
            tiles='CartoDB positron',
            scrollWheelZoom=True
        )

        casos_dict = dict(zip(casos_prov["provincia"], casos_prov["casos_totales"]))
        alto_dict = dict(zip(casos_prov["provincia"], casos_prov["deptos_alto"]))
        total_dict = dict(zip(casos_prov["provincia"], casos_prov["deptos_total"]))

        max_casos = casos_prov["casos_totales"].max()

        def get_prov_color(c):
            if max_casos == 0 or c == 0:
                return "#16a34a"
            r = c / max_casos
            if r < 0.15:
                return "#22c55e"
            elif r < 0.40:
                return "#eab308"
            elif r < 0.70:
                return "#f97316"
            else:
                return "#dc2626"

        for feat in geo_prov['features']:
            prov_nombre = feat['properties'].get('provincia') or feat['properties'].get('PROVINCIA')
            if not prov_nombre or prov_nombre not in provincias_filtradas:
                continue

            c_tot = int(casos_dict.get(prov_nombre, 0))
            d_alto = int(alto_dict.get(prov_nombre, 0))
            d_tot = int(total_dict.get(prov_nombre, 0))
            color = get_prov_color(c_tot)

            folium.GeoJson(
                feat,
                style_function=lambda x, c=color: {
                    'fillColor': c,
                    'color': '#64748b',
                    'weight': 1.2,
                    'fillOpacity': 0.75
                },
                highlight_function=lambda x: {
                    'fillOpacity': 0.95,
                    'weight': 2.5,
                    'color': '#1a56db'
                },
                tooltip=folium.Tooltip(
                    f"<b>{prov_nombre}</b><br>"
                    f"🦠 Casos estimados: <b>{c_tot:,}</b><br>"
                    f"🔴 Deptos. en riesgo alto: <b>{d_alto}</b> / {d_tot}",
                    sticky=True
                ),
            ).add_to(m_nac)

        map_output = st_folium(m_nac, height=580, use_container_width=True, key="folium_mapa_nacional")

        # Clic directo en el mapa para ir a la provincia
        if map_output and map_output.get("last_active_drawing"):
            props = map_output["last_active_drawing"]["properties"]
            clicked_prov = props.get("provincia") or props.get("PROVINCIA")
            if clicked_prov and clicked_prov in provincias_filtradas and clicked_prov != st.session_state.provincia_seleccionada:
                st.session_state.provincia_seleccionada = clicked_prov
                st.rerun()

    # ──────────────────────────────────────────────────────────────────────────
    # VISTA PROVINCIAL EN FOLIUM (ZOOM DETALLADO)
    # ──────────────────────────────────────────────────────────────────────────
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
        
        # 1. Obtener casos de riesgo_prov o buscar directamente en pred si viene en 0
        casos_prov_totales = int(riesgo_prov["casos_dengue"].sum()) if "casos_dengue" in riesgo_prov.columns else 0

        if casos_prov_totales == 0:
            pred_prov_val = pred[
                (pred["provincia"] == prov_actual) & 
                (pred["anio"] == anio_mapa) & 
                (pred["semana_epi"] == semana_mapa)
            ]
            if not pred_prov_val.empty and "pred" in pred_prov_val.columns:
                casos_prov_totales = int(pred_prov_val["pred"].sum())

        # 2. Conteo de departamentos por nivel de riesgo
        n_alto_p = int((riesgo_prov["nivel_mult"] == "alto").sum())
        n_medio_p = int((riesgo_prov["nivel_mult"] == "medio").sum())
        n_bajo_p = int((riesgo_prov["nivel_mult"] == "bajo").sum())

        # 3. Renderizado dinámico (4 columnas si hay casos > 0, 3 columnas si es 0)
        if casos_prov_totales > 0:
            mc, ma, mm, mb = st.columns(4)
            mc.metric("🦠 Casos estimados prov.", f"{casos_prov_totales:,}")
            ma.metric("🔴 Riesgo alto", f"{n_alto_p} deptos.")
            mm.metric("🟡 Riesgo medio", f"{n_medio_p} deptos.")
            mb.metric("🟢 Riesgo bajo", f"{n_bajo_p} deptos.")
        else:
            ma, mm, mb = st.columns(3)
            ma.metric("🔴 Riesgo alto", f"{n_alto_p} deptos.")
            mm.metric("🟡 Riesgo medio", f"{n_medio_p} deptos.")
            mb.metric("🟢 Riesgo bajo", f"{n_bajo_p} deptos.")

        st.markdown(
            """
        <div class="map-legend">
            <span><span class="leg-dot" style="background:#16a34a"></span>Riesgo bajo</span>
            <span><span class="leg-dot" style="background:#d97706"></span>Riesgo medio</span>
            <span><span class="leg-dot" style="background:#dc2626"></span>Riesgo alto</span>
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

        m_dept = folium.Map(location=[centro_lat, centro_lon], zoom_start=zoom, tiles='CartoDB positron', scrollWheelZoom=True)

        for feat in features_prov:
            did = str(feat['properties']['depto_id'])
            nivel = riesgo_dict.get(did, 'bajo')
            color = color_map.get(nivel, '#16a34a')
            nombre = nombre_dept_dict.get(did, feat['properties']['nombre'])
            clima = clima_dict.get(did, 0)
            nbi = nbi_dict.get(did, 0)

            folium.GeoJson(
                feat,
                style_function=lambda x, c=color: {'fillColor': c, 'color': '#64748b', 'weight': 1, 'fillOpacity': 0.75},
                highlight_function=lambda x: {'fillOpacity': 0.95, 'weight': 2.5, 'color': '#1a56db'},
                tooltip=folium.Tooltip(
                    f"<b>{nombre}</b><br>"
                    f"Nivel de Riesgo: <b>{nivel.capitalize()}</b><br>"
                    f"Factor climático: {clima:.3f}<br>"
                    f"Score estructural: {nbi:.3f}", 
                    sticky=True
                ),
            ).add_to(m_dept)

        st_folium(m_dept, height=550, use_container_width=True, returned_objects=[])

        with st.expander("📋 Ver clasificación de riesgo por departamento"):
            tabla_dept = riesgo_prov[["depto_nombre", "nivel_mult", "factor_clima", "score_terreno"]].copy()
            tabla_dept["nivel_mult"] = tabla_dept["nivel_mult"].str.capitalize()
            tabla_dept.columns = ["Departamento", "Nivel de riesgo", "Factor climático", "Score estructural"]
            tabla_dept = tabla_dept.sort_values("Departamento")
            st.dataframe(tabla_dept, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# VISTA 2: MONITOREO DEL MODELO
# ══════════════════════════════════════════════════════════════════════════════
elif menu_seleccionado == "Monitoreo del modelo":
    st.subheader("📊 Monitoreo y Evaluación del Modelo Predictivo")

    anios_pred = ANIOS_DISPONIBLES

    with st.container(border=True):
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([3, 2, 2])
        with col_ctrl1:
            prov_sel = st.selectbox("Provincia", PROVINCIAS, key="prov_pred_sel")
        with col_ctrl2:
            horizonte_sel = st.radio("Horizonte de predicción", ["t+2 (2 semanas)", "t+4 (4 semanas)"], horizontal=True, key="horiz_pred_sel")
        with col_ctrl3:
            anio_sel = st.selectbox("Año de predicción", anios_pred, index=0, key="anio_pred_sel")

    horizonte_key = "t+2" if "t+2" in horizonte_sel else "t+4"

    pred_prov = pred[
        (pred["provincia"] == prov_sel)
        & (pred["horizonte"] == horizonte_key)
        & (pred["anio"] == anio_sel)
    ].copy()

    pico_real = "N/A"
    pico_pred = "N/A"
    sem_pico_real = None
    sem_pico_pred = None
    dif_semanas = "N/A"
    r2 = "N/A"
    has_real = False
    has_pred = False

    if len(pred_prov) > 0:
        has_real = pred_prov["casos_real"].notna().any() and not np.isnan(pred_prov["casos_real"].max())
        has_pred = pred_prov["pred"].notna().any() and not np.isnan(pred_prov["pred"].max())

        if has_real:
            pico_real = pred_prov["casos_real"].max()
            sem_pico_real = int(pred_prov.loc[pred_prov["casos_real"].idxmax(), "semana_epi"])

        if has_pred:
            pico_pred = pred_prov["pred"].max()
            sem_pico_pred = int(pred_prov.loc[pred_prov["pred"].idxmax(), "semana_epi"])

        if sem_pico_real is not None and sem_pico_pred is not None:
            dif_semanas = abs(sem_pico_real - sem_pico_pred)

        if has_real and has_pred:
            valid_mask = pred_prov["casos_real"].notna() & pred_prov["pred"].notna()
            real_valid = pred_prov.loc[valid_mask, "casos_real"]
            pred_valid = pred_prov.loc[valid_mask, "pred"]
            
            if len(real_valid) > 0:
                ss_res = np.sum((real_valid - pred_valid) ** 2)
                ss_tot = np.sum((real_valid - real_valid.mean()) ** 2)
                r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                r2 = max(0, r2)

        is_mega_brote = isinstance(pico_real, (int, float)) and pico_real > 10000
        has_good_r2 = isinstance(r2, (int, float)) and r2 > 0.6

        if is_mega_brote:
            chip_txt = "🟡 Mega-brote — Magnitud subestimada"
            chip_bg = "rgba(210, 153, 34, 0.15)"
            chip_border = "#d29922"
            chip_color = "#f0b429"
        elif has_good_r2:
            chip_txt = "🟢 Transmisión media / alta — Buen ajuste"
            chip_bg = "rgba(63, 185, 80, 0.15)"
            chip_border = "#3fb950"
            chip_color = "#3fb950"
        elif has_pred and not has_real:
            chip_txt = "🔮 Proyección Futura — Alerta Temprana"
            chip_bg = "rgba(163, 113, 247, 0.15)"
            chip_border = "#a371f7"
            chip_color = "#d2a8ff"
        else:
            chip_txt = "🔵 Transmisión baja / Dinámica local"
            chip_bg = "rgba(88, 166, 255, 0.15)"
            chip_border = "#58a6ff"
            chip_color = "#58a6ff"

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

        if isinstance(dif_semanas, (int, float)):
            if dif_semanas == 0:
                msg_pico = f"🎯 <b>Pico exacto</b> coincidente en la <b>Semana {sem_pico_real}</b>."
            elif dif_semanas == 1:
                msg_pico = f"🎯 <b>Anticipación efectiva del pico:</b> Detección oportuna con solo <b>1 semana de diferencia</b> (Real SE {sem_pico_real}, Predicho SE {sem_pico_pred})."
            else:
                msg_pico = f"⏱️ <b>Desfasaje del pico:</b> {int(dif_semanas)} semanas de diferencia entre real (SE {sem_pico_real}) y predicho (SE {sem_pico_pred})."
            st.info(msg_pico)
        elif has_pred and not has_real:
            st.info(f"🔮 <b>Proyección epidemiológica para {anio_sel}:</b> Modelo activo sin registros reales de contraste.")

        fig = go.Figure()
        if has_real:
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
        if has_pred:
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

        if isinstance(r2, (int, float)):
            str_r2 = f"{r2:.2f}"
            sub_r2 = f"Explica el {r2 * 100:.0f}% de la variación"
        else:
            str_r2 = "N/A"
            sub_r2 = "Sin datos de comparación"

        if isinstance(pico_real, (int, float)) and pico_real > 0:
            str_pico_real = f"{int(pico_real):,} casos"
            sub_pico_real = f"Semana {int(sem_pico_real)}" if isinstance(sem_pico_real, (int, float)) else "Sin semana"
        else:
            str_pico_real = "Sin registros"
            sub_pico_real = "N/A"

        if isinstance(pico_pred, (int, float)) and pico_pred > 0:
            str_pico_pred = f"{int(pico_pred):,} casos"
            sub_pico_pred = f"Semana {int(sem_pico_pred)}" if isinstance(sem_pico_pred, (int, float)) else "Sin semana"
        else:
            str_pico_pred = "N/A"
            sub_pico_pred = "Sin registros"

        if isinstance(dif_semanas, (int, float)):
            str_dif = f"{int(dif_semanas)} sem"
            sub_dif = "Desfasaje entre picos"
        else:
            str_dif = "N/A"
            sub_dif = "Sin comparación"

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Ajuste de Curva (R²)", str_r2, sub_r2)
        m2.metric("Pico Real", str_pico_real, sub_pico_real)
        m3.metric("Pico Predicho", str_pico_pred, sub_pico_pred)
        m4.metric("Diferencia de Picos", str_dif, sub_dif)
    else:
        st.warning(f"No hay registros o predicciones disponibles para {prov_sel} en el año {anio_sel}.")