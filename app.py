import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import numpy as np

# ── CONFIGURACIÓN ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DengueWatch Argentina",
    page_icon="🦟",
    layout="wide"
)

# ── CARGA DE DATOS ─────────────────────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    pred = pd.read_csv('datos/predicciones.csv')
    hist = pd.read_csv('datos/dataset_provincial_escalado.csv')
    riesgo = pd.read_csv('datos/riesgo_departamental.csv')
    riesgo['depto_id_norm'] = riesgo['depto_id_norm'].astype(int)
    with open('datos/departamentos_argentina.geojson', encoding='utf-8') as f:
        geo_dept = json.load(f)
    with open('datos/provincias_argentina.geojson', encoding='utf-8') as f:
        geo_prov = json.load(f)
    return pred, hist, riesgo, geo_dept, geo_prov

pred, hist, riesgo, geo_dept, geo_prov = cargar_datos()
PROVINCIAS = sorted(pred['provincia'].unique())

# ── ESTILOS GLOBALES ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Ocultar decoración de Streamlit */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }

/* Header */
.dw-header {
    background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
    border: 1px solid #21262d;
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
    animation: blink 2.5s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.5} }

/* Cards nacionales */
.cards-row { display: flex; gap: 10px; margin-bottom: 1rem; }
.nc {
    flex: 1;
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 14px 18px;
    min-width: 130px;
    transition: border-color 0.2s;
}
.nc:hover { border-color: #388bfd; }
.nc-label { font-size: 10px; color: #6e7681; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
.nc-val { font-size: 24px; font-weight: 700; color: #e6edf3; line-height: 1.1; }
.nc-val-sm { font-size: 16px; font-weight: 600; color: #e6edf3; line-height: 1.2; }
.nc-sub { font-size: 11px; color: #8b949e; margin-top: 4px; }
.nc-up { color: #f85149 !important; }
.nc-down { color: #3fb950 !important; }
.nc-alert-rojo { color: #f85149 !important; }
.nc-alert-amarillo { color: #d29922 !important; }
.nc-alert-verde { color: #3fb950 !important; }

/* Separador */
.dw-divider { height: 1px; background: #21262d; margin: 0.8rem 0; }

/* Leyenda mapa */
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

/* Breadcrumb */
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

/* Hint text */
.hint { font-size: 12px; color: #6e7681; margin-bottom: 10px; }

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: transparent;
    border-bottom: 1px solid #21262d;
    padding-bottom: 0;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 500;
    color: #8b949e;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    color: #e6edf3 !important;
    background: #161b22 !important;
    border: 1px solid #21262d !important;
    border-bottom: 1px solid #0d1117 !important;
}
</style>
""", unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
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
""", unsafe_allow_html=True)

# ── CARDS NACIONALES ──────────────────────────────────────────────────────────
ultimo_anio = riesgo['anio'].max()
ultima_semana = riesgo[riesgo['anio'] == ultimo_anio]['semana'].max()
datos_rec = riesgo[(riesgo['anio'] == ultimo_anio) & (riesgo['semana'] == ultima_semana)]
datos_ant = riesgo[(riesgo['anio'] == ultimo_anio) & (riesgo['semana'] == max(ultima_semana - 1, 1))]

casos_rec = int(datos_rec['casos_dengue'].sum())
casos_ant = int(datos_ant['casos_dengue'].sum())
variacion = casos_rec - casos_ant

deptos_alto = int((datos_rec['nivel_mult'] == 'alto').sum())
prov_max = datos_rec.groupby('provincia')['casos_dengue'].sum()
prov_top = prov_max.idxmax() if prov_max.max() > 0 else "Sin datos"

if deptos_alto > 150:
    alerta_txt = "🔴 ALERTA"
    alerta_cls = "nc-alert-rojo"
elif deptos_alto > 80:
    alerta_txt = "🟡 ATENCIÓN"
    alerta_cls = "nc-alert-amarillo"
else:
    alerta_txt = "🟢 NORMAL"
    alerta_cls = "nc-alert-verde"

var_cls = "nc-up" if variacion > 0 else "nc-down"
var_icon = "▲" if variacion > 0 else "▼"

st.markdown(f"""
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
""", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab_pred, tab_mapa = st.tabs(["📈  Predicciones provinciales", "🗺️  Mapa de riesgo departamental"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: PREDICCIONES PROVINCIALES
# ══════════════════════════════════════════════════════════════════════════════
with tab_pred:

    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([3, 2, 2])
    with col_ctrl1:
        prov_sel = st.selectbox("Provincia", PROVINCIAS, label_visibility="visible")
    with col_ctrl2:
        horizonte_sel = st.radio("Horizonte de predicción", ["t+2 (2 semanas)", "t+4 (4 semanas)"], horizontal=True)
    with col_ctrl3:
        anio_sel = st.radio("Año de evaluación", [2024, 2025], horizontal=True)

    horizonte_key = "t+2" if "t+2" in horizonte_sel else "t+4"

    hist_prov = hist[
        (hist['provincia'] == prov_sel) &
        (hist['anio'].isin([2019, 2020, 2021, 2022, 2023]))
    ][['anio', 'semana', 'casos_dengue']].copy()

    pred_prov = pred[
        (pred['provincia'] == prov_sel) &
        (pred['horizonte'] == horizonte_key) &
        (pred['anio'] == anio_sel)
    ].copy()

    # Métricas
    if len(pred_prov) > 0:
        mae_prov = abs(pred_prov['casos_real'] - pred_prov['pred']).mean()
        pico_real = pred_prov['casos_real'].max()
        pico_pred = pred_prov['pred'].max()
        sem_pico_real = pred_prov.loc[pred_prov['casos_real'].idxmax(), 'semana_epi']
        sem_pico_pred = pred_prov.loc[pred_prov['pred'].idxmax(), 'semana_epi']
        error_pico = abs(pico_real - pico_pred)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("MAE promedio", f"{mae_prov:,.0f} casos")
        m2.metric("Pico real", f"{pico_real:,.0f} casos", f"Semana {sem_pico_real}")
        m3.metric("Pico predicho", f"{pico_pred:,.0f} casos", f"Semana {sem_pico_pred}")
        m4.metric("Error en pico", f"{error_pico:,.0f} casos")

    st.markdown('<div class="dw-divider"></div>', unsafe_allow_html=True)

    # Título del gráfico
    st.markdown(f"<div style='font-size:13px; color:#8b949e; margin-bottom:4px;'>Casos semanales · <b style='color:#e6edf3'>{prov_sel}</b> · {anio_sel} vs histórico</div>", unsafe_allow_html=True)

    # Gráfico
    fig = go.Figure()

    colores_hist = {
        2019: 'rgba(180,180,180,0.25)',
        2020: 'rgba(133,183,235,0.35)',
        2021: 'rgba(93,202,165,0.35)',
        2022: 'rgba(180,180,180,0.2)',
        2023: 'rgba(239,159,39,0.45)',
    }

    for anio_h, grp in hist_prov.groupby('anio'):
        fig.add_trace(go.Scatter(
            x=grp['semana'], y=grp['casos_dengue'],
            mode='lines', name=str(anio_h),
            line=dict(color=colores_hist.get(anio_h, 'rgba(150,150,150,0.25)'), width=1.2),
            hovertemplate=f"{anio_h} — Sem %{{x}}: %{{y:,.0f}} casos<extra></extra>"
        ))

    if len(pred_prov) > 0:
        # Área sombreada debajo de la curva real
        fig.add_trace(go.Scatter(
            x=pred_prov['semana_epi'], y=pred_prov['casos_real'],
            mode='lines', name=f'Real {anio_sel}',
            fill='tozeroy', fillcolor='rgba(88,166,255,0.07)',
            line=dict(color='#58a6ff', width=2.5),
            hovertemplate=f"Real {anio_sel} — Sem %{{x}}: %{{y:,.0f}} casos<extra></extra>"
        ))
        fig.add_trace(go.Scatter(
            x=pred_prov['semana_epi'], y=pred_prov['pred'],
            mode='lines+markers', name=f'Predicción GRU ({horizonte_key})',
            line=dict(color='#f85149', width=2, dash='dash'),
            marker=dict(size=4, symbol='diamond', color='#f85149'),
            hovertemplate=f"Predicción — Sem %{{x}}: %{{y:,.0f}} casos<extra></extra>"
        ))

        # Línea vertical en el pico real
        fig.add_vline(
            x=sem_pico_real,
            line_dash='dot', line_color='rgba(88,166,255,0.3)', line_width=1,
            annotation_text=f"Pico sem. {sem_pico_real}",
            annotation_font_size=10, annotation_font_color='#58a6ff',
            annotation_position='top right'
        )

    fig.update_layout(
        paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        font_color='#c9d1d9', height=460,
        margin=dict(l=10, r=10, t=20, b=40),
        legend=dict(
            bgcolor='rgba(22,27,34,0.9)', bordercolor='#30363d',
            borderwidth=1, font=dict(size=11), orientation='v',
            x=1.01, y=1, xanchor='left'
        ),
        xaxis=dict(
            title='Semana epidemiológica', gridcolor='#1c2128',
            tickfont=dict(size=10), showgrid=True,
            zeroline=False, range=[0, 53]
        ),
        yaxis=dict(
            title='Casos notificados', gridcolor='#1c2128',
            tickfont=dict(size=10), showgrid=True, zeroline=False
        ),
        hovermode='x unified',
        hoverlabel=dict(bgcolor='#161b22', bordercolor='#30363d', font_size=12)
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Ver tabla de predicciones semana a semana"):
        if len(pred_prov) > 0:
            tabla = pred_prov[['semana_epi', 'casos_real', 'pred']].copy()
            tabla.columns = ['Semana', 'Casos reales', 'Predicción GRU']
            tabla['Error absoluto'] = abs(tabla['Casos reales'] - tabla['Predicción GRU']).round(0)
            tabla = tabla.set_index('Semana')
            st.dataframe(tabla.style.format({
                'Casos reales': '{:,.0f}',
                'Predicción GRU': '{:,.0f}',
                'Error absoluto': '{:,.0f}'
            }), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: MAPA DE RIESGO DEPARTAMENTAL
# ══════════════════════════════════════════════════════════════════════════════
with tab_mapa:

    if 'provincia_seleccionada' not in st.session_state:
        st.session_state.provincia_seleccionada = None

    # Controles compactos
    col_m1, col_m2 = st.columns([1, 3])
    with col_m1:
        anio_mapa = st.selectbox(
            "Año", sorted(riesgo['anio'].unique(), reverse=True),
            key='anio_mapa', label_visibility="visible"
        )
    with col_m2:
        semanas_disp = sorted(riesgo[riesgo['anio'] == anio_mapa]['semana'].unique())
        semana_mapa = st.slider(
            "Semana epidemiológica",
            min_value=int(min(semanas_disp)),
            max_value=int(max(semanas_disp)),
            value=int(max(semanas_disp)),
            key='semana_mapa'
        )

    # Filtrar
    riesgo_filtrado = riesgo[
        (riesgo['anio'] == anio_mapa) &
        (riesgo['semana'] == semana_mapa)
    ].copy()
    riesgo_filtrado['depto_id_norm'] = riesgo_filtrado['depto_id_norm'].astype(int)
    riesgo_filtrado['nivel_num'] = riesgo_filtrado['nivel_mult'].map({'bajo': 1, 'medio': 2, 'alto': 3}).fillna(1)
    riesgo_filtrado['nivel_label'] = riesgo_filtrado['nivel_mult'].str.capitalize()

    # ── VISTA PROVINCIAL ──────────────────────────────────────────────────────
    if st.session_state.provincia_seleccionada is None:

        # Métricas
        n_alto = int((riesgo_filtrado['nivel_mult'] == 'alto').sum())
        n_medio = int((riesgo_filtrado['nivel_mult'] == 'medio').sum())
        n_bajo = int((riesgo_filtrado['nivel_mult'] == 'bajo').sum())
        total_casos = int(riesgo_filtrado['casos_dengue'].sum())

        ma, mm, mb, mt = st.columns(4)
        ma.metric("🔴 Riesgo alto", f"{n_alto} deptos.")
        mm.metric("🟡 Riesgo medio", f"{n_medio} deptos.")
        mb.metric("🟢 Riesgo bajo", f"{n_bajo} deptos.")
        mt.metric("🦟 Casos totales", f"{total_casos:,}")

        st.markdown('<div class="hint">🖱️ Pasá el mouse sobre una provincia para ver sus casos · Seleccioná una provincia abajo para ver sus departamentos</div>', unsafe_allow_html=True)

        # Agregado provincial
        casos_prov = riesgo_filtrado.groupby('provincia').agg(
            casos_totales=('casos_dengue', 'sum'),
            deptos_alto=('nivel_mult', lambda x: (x == 'alto').sum()),
            deptos_total=('depto_id_norm', 'count')
        ).reset_index()

        # Escala de color: usar log para que semanas de baja actividad muestren diferencias
        casos_prov['casos_log'] = np.log1p(casos_prov['casos_totales'])
        max_log = casos_prov['casos_log'].max()

        fig_prov = px.choropleth(
            casos_prov,
            geojson=geo_prov,
            locations='provincia',
            featureidkey='properties.provincia',
            color='casos_log',
            color_continuous_scale=[
                [0.0,  '#1c2128'],
                [0.15, '#1a3a2a'],
                [0.35, '#3fb950'],
                [0.60, '#d29922'],
                [0.80, '#e85b30'],
                [1.0,  '#f85149'],
            ],
            range_color=[0, max_log if max_log > 0 else 1],
            hover_name='provincia',
            hover_data={
                'casos_totales': True,
                'deptos_alto': True,
                'casos_log': False,
                'provincia': False
            },
            labels={'casos_totales': 'Casos totales', 'deptos_alto': 'Deptos. en alerta alta'}
        )
        fig_prov.update_geos(
            visible=True, fitbounds="locations",
            showland=True, landcolor='#1c2128',
            showocean=True, oceancolor='#0d1117',
            showcountries=True, countrycolor='#30363d',
            showcoastlines=False, bgcolor='#0d1117'
        )
        fig_prov.update_layout(
            paper_bgcolor='#0d1117', plot_bgcolor='#0d1117',
            font_color='#c9d1d9',
            margin=dict(l=0, r=0, t=10, b=0),
            height=640,
            coloraxis_colorbar=dict(
            title="Casos<br>(log)",
            tickfont=dict(color='#8b949e', size=10),
            thickness=12, len=0.6,
            tickvals=[0, max_log * 0.33, max_log * 0.66, max_log] if max_log > 0 else [0, 1],
            ticktext=['0', 'Bajo', 'Medio', 'Alto'] if max_log > 0 else ['0', '1'],
            )
        )
        st.plotly_chart(fig_prov, use_container_width=True)

        st.markdown('<div class="dw-divider"></div>', unsafe_allow_html=True)
        col_sel, col_btn = st.columns([4, 1])
        with col_sel:
            prov_elegida = st.selectbox(
                "Ver departamentos de:",
                ["— Elegí una provincia —"] + sorted(casos_prov['provincia'].tolist()),
                label_visibility="visible"
            )
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Ver departamentos →", type="primary", use_container_width=True):
                if prov_elegida != "— Elegí una provincia —":
                    st.session_state.provincia_seleccionada = prov_elegida
                    st.rerun()

    # ── VISTA DEPARTAMENTAL ───────────────────────────────────────────────────
    else:
        prov_actual = st.session_state.provincia_seleccionada

        # Breadcrumb + botón volver
        col_back, col_bread = st.columns([1, 5])
        with col_back:
            if st.button("← Volver", use_container_width=True):
                st.session_state.provincia_seleccionada = None
                st.rerun()
        with col_bread:
            st.markdown(f"""
            <div class="breadcrumb">
                <span class="bread-inactive">Argentina</span>
                <span class="bread-sep">›</span>
                <span class="bread-active">{prov_actual}</span>
            </div>
            """, unsafe_allow_html=True)

        riesgo_prov = riesgo_filtrado[riesgo_filtrado['provincia'] == prov_actual].copy()

        # Métricas provincia
        casos_prov_total = int(riesgo_prov['casos_dengue'].sum())
        n_alto_p = int((riesgo_prov['nivel_mult'] == 'alto').sum())
        n_medio_p = int((riesgo_prov['nivel_mult'] == 'medio').sum())
        n_bajo_p = int((riesgo_prov['nivel_mult'] == 'bajo').sum())

        ma, mm, mb, mt = st.columns(4)
        ma.metric("🦟 Casos totales", f"{casos_prov_total:,}")
        mm.metric("🔴 Riesgo alto", f"{n_alto_p} deptos.")
        mb.metric("🟡 Riesgo medio", f"{n_medio_p} deptos.")
        mt.metric("🟢 Riesgo bajo", f"{n_bajo_p} deptos.")

        # Leyenda
        st.markdown("""
        <div class="map-legend">
            <span><span class="leg-dot" style="background:#3fb950"></span>Riesgo bajo</span>
            <span><span class="leg-dot" style="background:#d29922"></span>Riesgo medio</span>
            <span><span class="leg-dot" style="background:#f85149"></span>Riesgo alto</span>
            <span style="color:#30363d; margin-left:4px;">· basado en índice climático + estructural</span>
        </div>
        """, unsafe_allow_html=True)

        geo_prov_filtrado = {
            'type': 'FeatureCollection',
            'features': [f for f in geo_dept['features'] if f['properties']['provincia'] == prov_actual]
        }

        fig_dept = px.choropleth(
            riesgo_prov,
            geojson=geo_prov_filtrado,
            locations='depto_id_norm',
            featureidkey='properties.depto_id',
            color='nivel_num',
            color_continuous_scale=[
                [0.0, '#3fb950'],
                [0.5, '#d29922'],
                [1.0, '#f85149'],
            ],
            range_color=[1, 3],
            hover_name='depto_nombre',
            hover_data={
                'nivel_label': True,
                'casos_dengue': True,
                'factor_clima': ':.3f',
                'score_terreno': ':.3f',
                'nivel_num': False,
                'depto_id_norm': False,
            },
            labels={
                'nivel_label': 'Nivel de riesgo',
                'casos_dengue': 'Casos',
                'factor_clima': 'Factor climático',
                'score_terreno': 'Score estructural'
            }
        )
        fig_dept.update_geos(
            visible=True, fitbounds="locations",
            showland=True, landcolor='#1c2128',
            showocean=True, oceancolor='#0d1117',
            showcountries=True, countrycolor='#30363d',
            showcoastlines=False, bgcolor='#0d1117'
        )
        fig_dept.update_layout(
            paper_bgcolor='#0d1117', plot_bgcolor='#0d1117',
            font_color='#c9d1d9',
            margin=dict(l=0, r=0, t=10, b=0),
            height=620,
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_dept, use_container_width=True)

        with st.expander("📋 Ver tabla de departamentos"):
            tabla_dept = riesgo_prov[['depto_nombre','nivel_mult','casos_dengue','factor_clima','score_terreno']].copy()
            tabla_dept.columns = ['Departamento','Nivel de riesgo','Casos','Factor climático','Score estructural']
            tabla_dept = tabla_dept.sort_values('Casos', ascending=False)
            st.dataframe(tabla_dept, use_container_width=True, hide_index=True)