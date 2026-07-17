import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json

# ── CONFIGURACIÓN ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Vigilancia de Dengue — Argentina",
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

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
.main-header {
    background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
    border: 0.5px solid #21262d;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
}
.header-left { display: flex; align-items: center; gap: 12px; }
.header-title { font-size: 20px; font-weight: 700; color: #e6edf3; margin: 0; }
.header-sub { font-size: 12px; color: #6e7681; margin: 2px 0 0; }
.live-badge {
    background: rgba(63,185,80,0.12);
    color: #3fb950;
    border: 0.5px solid rgba(63,185,80,0.3);
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 500;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}
.national-card {
    background: #161b22;
    border: 0.5px solid #21262d;
    border-radius: 10px;
    padding: 14px 18px;
    flex: 1;
    min-width: 140px;
}
.nc-label { font-size: 11px; color: #6e7681; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.nc-val { font-size: 22px; font-weight: 700; color: #e6edf3; }
.nc-sub { font-size: 11px; color: #8b949e; margin-top: 2px; }
.nc-up { color: #f85149; }
.nc-down { color: #3fb950; }
.cards-row { display: flex; gap: 10px; margin-bottom: 1.2rem; flex-wrap: wrap; }
</style>

<div class="main-header">
    <div class="header-left">
        <span style="font-size:32px">🦟</span>
        <div>
            <div class="header-title">DengueWatch Argentina</div>
            <div class="header-sub">Sistema de monitoreo y predicción epidemiológica · PI Ingeniería Biomédica</div>
        </div>
    </div>
    <span class="live-badge">● SISTEMA ACTIVO</span>
</div>
""", unsafe_allow_html=True)

# ── CARDS NACIONALES ──────────────────────────────────────────────────────────
# Calcular métricas nacionales con la semana más reciente disponible
ultima_semana = riesgo[riesgo['anio'] == riesgo['anio'].max()]['semana'].max()
ultimo_anio = riesgo['anio'].max()
datos_recientes = riesgo[(riesgo['anio'] == ultimo_anio) & (riesgo['semana'] == ultima_semana)]
datos_anterior = riesgo[(riesgo['anio'] == ultimo_anio) & (riesgo['semana'] == ultima_semana - 1)]

casos_recientes = int(datos_recientes['casos_dengue'].sum())
casos_anterior = int(datos_anterior['casos_dengue'].sum())
variacion = casos_recientes - casos_anterior
variacion_pct = (variacion / casos_anterior * 100) if casos_anterior > 0 else 0

deptos_alto = (datos_recientes['nivel_mult'] == 'alto').sum()
prov_mas_afectada = datos_recientes.groupby('provincia')['casos_dengue'].sum().idxmax()
alerta = "🔴 ALERTA" if deptos_alto > 150 else "🟡 ATENCIÓN" if deptos_alto > 80 else "🟢 NORMAL"

st.markdown(f"""
<div class="cards-row">
    <div class="national-card">
        <div class="nc-label">Casos esta semana</div>
        <div class="nc-val">{casos_recientes:,}</div>
        <div class="nc-sub {'nc-up' if variacion > 0 else 'nc-down'}">
            {'▲' if variacion > 0 else '▼'} {abs(int(variacion)):,} vs semana anterior
        </div>
    </div>
    <div class="national-card">
        <div class="nc-label">Departamentos en alerta</div>
        <div class="nc-val" style="color:#f85149">{deptos_alto}</div>
        <div class="nc-sub">de 527 departamentos</div>
    </div>
    <div class="national-card">
        <div class="nc-label">Provincia más afectada</div>
        <div class="nc-val" style="font-size:16px">{prov_mas_afectada}</div>
        <div class="nc-sub">Semana {ultima_semana} / {ultimo_anio}</div>
    </div>
    <div class="national-card">
        <div class="nc-label">Estado del sistema</div>
        <div class="nc-val" style="font-size:16px">{alerta}</div>
        <div class="nc-sub">{deptos_alto} deptos. en riesgo alto</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab_pred, tab_mapa = st.tabs(["📈 Predicciones provinciales", "🗺️ Mapa de riesgo departamental"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: PREDICCIONES PROVINCIALES
# ══════════════════════════════════════════════════════════════════════════════
with tab_pred:

    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 1, 1])
    with col_ctrl1:
        prov_sel = st.selectbox("Provincia", PROVINCIAS)
    with col_ctrl2:
        horizonte_sel = st.radio("Horizonte", ["t+2 (2 semanas)", "t+4 (4 semanas)"], horizontal=True)
    with col_ctrl3:
        anio_sel = st.radio("Año de prueba", [2024, 2025], horizontal=True)

    horizonte_key = "t+2" if "t+2" in horizonte_sel else "t+4"

    # Datos históricos 2019-2023
    hist_prov = hist[
        (hist['provincia'] == prov_sel) &
        (hist['anio'].isin([2019, 2020, 2021, 2022, 2023]))
    ][['anio', 'semana', 'casos_dengue']].copy()

    # Predicciones
    pred_prov = pred[
        (pred['provincia'] == prov_sel) &
        (pred['horizonte'] == horizonte_key) &
        (pred['anio'] == anio_sel)
    ].copy()

    # ── Métricas ──────────────────────────────────────────────────────────────
    if len(pred_prov) > 0:
        mae_prov = abs(pred_prov['casos_real'] - pred_prov['pred']).mean()
        casos_pico_real = pred_prov['casos_real'].max()
        casos_pico_pred = pred_prov['pred'].max()
        semana_pico_real = pred_prov.loc[pred_prov['casos_real'].idxmax(), 'semana_epi']
        semana_pico_pred = pred_prov.loc[pred_prov['pred'].idxmax(), 'semana_epi']

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("MAE promedio", f"{mae_prov:,.0f} casos")
        m2.metric("Pico real", f"{casos_pico_real:,.0f} casos", f"Semana {semana_pico_real}")
        m3.metric("Pico predicho", f"{casos_pico_pred:,.0f} casos", f"Semana {semana_pico_pred}")
        m4.metric("Error en pico", f"{abs(casos_pico_real - casos_pico_pred):,.0f} casos")

    st.markdown("---")

    # ── Gráfico ───────────────────────────────────────────────────────────────
    fig = go.Figure()

    colores_hist = {
        2019: 'rgba(150,150,150,0.3)',
        2020: 'rgba(133,183,235,0.4)',
        2021: 'rgba(93,202,165,0.4)',
        2022: 'rgba(150,150,150,0.25)',
        2023: 'rgba(239,159,39,0.5)',
    }

    for anio_h, grp in hist_prov.groupby('anio'):
        fig.add_trace(go.Scatter(
            x=grp['semana'],
            y=grp['casos_dengue'],
            mode='lines',
            name=str(anio_h),
            line=dict(color=colores_hist.get(anio_h, 'rgba(150,150,150,0.3)'), width=1.2),
            hovertemplate=f"{anio_h} — Sem %{{x}}: %{{y:,.0f}} casos<extra></extra>"
        ))

    if len(pred_prov) > 0:
        fig.add_trace(go.Scatter(
            x=pred_prov['semana_epi'],
            y=pred_prov['casos_real'],
            mode='lines+markers',
            name=f'Real {anio_sel}',
            line=dict(color='#58a6ff', width=2.5),
            marker=dict(size=5),
            hovertemplate=f"Real {anio_sel} — Sem %{{x}}: %{{y:,.0f}} casos<extra></extra>"
        ))

        fig.add_trace(go.Scatter(
            x=pred_prov['semana_epi'],
            y=pred_prov['pred'],
            mode='lines+markers',
            name=f'Predicción GRU ({horizonte_key})',
            line=dict(color='#f85149', width=2.5, dash='dash'),
            marker=dict(size=5, symbol='diamond'),
            hovertemplate=f"Predicción — Sem %{{x}}: %{{y:,.0f}} casos<extra></extra>"
        ))

    fig.update_layout(
        paper_bgcolor='#0d1117',
        plot_bgcolor='#161b22',
        font_color='#c9d1d9',
        height=450,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(
            bgcolor='rgba(22,27,34,0.8)',
            bordercolor='#21262d',
            borderwidth=1,
            font=dict(size=11)
        ),
        xaxis=dict(
            title='Semana epidemiológica',
            gridcolor='#21262d',
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            title='Casos notificados',
            gridcolor='#21262d',
            tickfont=dict(size=10)
        ),
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Ver tabla de predicciones"):
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

    # Estado de navegación
    if 'provincia_seleccionada' not in st.session_state:
        st.session_state.provincia_seleccionada = None

    # ── Controles ─────────────────────────────────────────────────────────────
    col_m1, col_m2 = st.columns([1, 1])
    with col_m1:
        anio_mapa = st.selectbox("Año", sorted(riesgo['anio'].unique(), reverse=True), key='anio_mapa')
    with col_m2:
        semanas_disp = sorted(riesgo[riesgo['anio'] == anio_mapa]['semana'].unique())
        semana_mapa = st.slider(
            "Semana epidemiológica",
            min_value=int(min(semanas_disp)),
            max_value=int(max(semanas_disp)),
            value=int(max(semanas_disp)),
            key='semana_mapa'
        )

    # Filtrar datos
    riesgo_filtrado = riesgo[
        (riesgo['anio'] == anio_mapa) &
        (riesgo['semana'] == semana_mapa)
    ].copy()
    riesgo_filtrado['depto_id_norm'] = riesgo_filtrado['depto_id_norm'].astype(int)
    riesgo_filtrado['nivel_num'] = riesgo_filtrado['nivel_mult'].map(
        {'bajo': 1, 'medio': 2, 'alto': 3}
    ).fillna(1)
    riesgo_filtrado['nivel_label'] = riesgo_filtrado['nivel_mult'].str.capitalize()

    # ── VISTA PROVINCIAL (sin provincia seleccionada) ─────────────────────────
    if st.session_state.provincia_seleccionada is None:

        st.markdown("""
        <p style='color:#6e7681; font-size:12px; margin-bottom:8px;'>
        🖱️ Pasá el mouse para ver casos · Hacé click en una provincia para ver sus departamentos
        </p>""", unsafe_allow_html=True)

        # Agregar casos por provincia
        casos_prov = riesgo_filtrado.groupby('provincia').agg(
           casos_totales=('casos_dengue', 'sum'),
           deptos_alto=('nivel_mult', lambda x: (x == 'alto').sum()),
           deptos_total=('depto_id_norm', 'count')
        ).reset_index()

        # Métricas
        ma, mm, mb, mt = st.columns(4)
        n_alto = (riesgo_filtrado['nivel_mult'] == 'alto').sum()
        n_medio = (riesgo_filtrado['nivel_mult'] == 'medio').sum()
        n_bajo = (riesgo_filtrado['nivel_mult'] == 'bajo').sum()
        ma.metric("🔴 Riesgo alto", f"{n_alto} deptos.")
        mm.metric("🟡 Riesgo medio", f"{n_medio} deptos.")
        mb.metric("🟢 Riesgo bajo", f"{n_bajo} deptos.")
        mt.metric("Total", f"527 deptos.")

        # Mapa provincial
        fig_prov = px.choropleth(
            casos_prov,
            geojson=geo_prov,
            locations='provincia',
            featureidkey='properties.provincia',
            color='casos_totales',
            color_continuous_scale=[
                [0.0, '#161b22'],
                [0.1, '#1a3a1a'],
                [0.3, '#3fb950'],
                [0.6, '#d29922'],
                [1.0, '#f85149'],
            ],
            hover_name='provincia',
            hover_data={
                'casos_totales': True,
                'deptos_alto': True,
                'provincia': False
            },
            labels={
                'casos_totales': 'Casos totales',
                'deptos_alto': 'Deptos. en alerta'
            }
        )
        fig_prov.update_geos(
            visible=True,
            fitbounds="locations",
            showland=True, landcolor='#161b22',
            showocean=True, oceancolor='#0d1117',
            showcountries=True, countrycolor='#30363d',
            showcoastlines=False,
            bgcolor='#0d1117'
        )
        fig_prov.update_layout(
            paper_bgcolor='#0d1117',
            plot_bgcolor='#0d1117',
            font_color='#c9d1d9',
            margin=dict(l=0, r=0, t=10, b=0),
            height=650,
            coloraxis_colorbar=dict(
                title="Casos",
                tickfont=dict(color='#c9d1d9'),
            )
        )
        st.plotly_chart(fig_prov, use_container_width=True)

        # Selector para entrar a una provincia
        st.markdown("---")
        col_sel, col_btn = st.columns([3, 1])
        with col_sel:
            prov_elegida = st.selectbox(
                "O seleccioná una provincia directamente:",
                ["— Elegí una provincia —"] + sorted(casos_prov['provincia'].tolist())
            )
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Ver departamentos →", use_container_width=True):
                if prov_elegida != "— Elegí una provincia —":
                    st.session_state.provincia_seleccionada = prov_elegida
                    st.rerun()

    # ── VISTA DEPARTAMENTAL (provincia seleccionada) ──────────────────────────
    else:
        prov_actual = st.session_state.provincia_seleccionada

        # Botón volver
        col_back, col_title = st.columns([1, 4])
        with col_back:
            if st.button("← Volver al mapa"):
                st.session_state.provincia_seleccionada = None
                st.rerun()
        with col_title:
            st.markdown(f"""
            <div style='display:flex; align-items:center; gap:8px; padding-top:6px;'>
                <span style='color:#6e7681; font-size:13px;'>Argentina</span>
                <span style='color:#6e7681;'>›</span>
                <span style='color:#e6edf3; font-weight:500; font-size:15px;'>{prov_actual}</span>
            </div>
            """, unsafe_allow_html=True)

        # Filtrar departamentos de la provincia
        riesgo_prov = riesgo_filtrado[
            riesgo_filtrado['provincia'] == prov_actual
        ].copy()

        # Métricas de la provincia
        casos_prov_total = int(riesgo_prov['casos_dengue'].sum())
        n_alto_p = (riesgo_prov['nivel_mult'] == 'alto').sum()
        n_medio_p = (riesgo_prov['nivel_mult'] == 'medio').sum()
        n_bajo_p = (riesgo_prov['nivel_mult'] == 'bajo').sum()

        ma, mm, mb, mt = st.columns(4)
        ma.metric("Casos totales", f"{casos_prov_total:,}")
        mm.metric("🔴 Alto", f"{n_alto_p} deptos.")
        mb.metric("🟡 Medio", f"{n_medio_p} deptos.")
        mt.metric("🟢 Bajo", f"{n_bajo_p} deptos.")

        # Mapa departamental de la provincia
        geo_prov_filtrado = {
            'type': 'FeatureCollection',
            'features': [
                f for f in geo_dept['features']
                if f['properties']['provincia'] == prov_actual
            ]
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
            visible=True,
            fitbounds="locations",
            showland=True, landcolor='#161b22',
            showocean=True, oceancolor='#0d1117',
            showcountries=True, countrycolor='#30363d',
            showcoastlines=False,
            bgcolor='#0d1117'
        )
        fig_dept.update_layout(
            paper_bgcolor='#0d1117',
            plot_bgcolor='#0d1117',
            font_color='#c9d1d9',
            margin=dict(l=0, r=0, t=10, b=0),
            height=600,
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_dept, use_container_width=True)

        # Leyenda
        st.markdown("""
        <div style='display:flex; gap:20px; font-size:12px; color:#8b949e; margin-top:-8px;'>
            <span>🟢 Riesgo bajo</span>
            <span>🟡 Riesgo medio</span>
            <span>🔴 Riesgo alto</span>
        </div>
        """, unsafe_allow_html=True)

        # Tabla de departamentos
        with st.expander("Ver tabla de departamentos"):
            tabla_dept = riesgo_prov[[
                'depto_nombre', 'nivel_mult', 'casos_dengue',
                'factor_clima', 'score_terreno'
            ]].copy()
            tabla_dept.columns = [
                'Departamento', 'Nivel de riesgo', 'Casos',
                'Factor climático', 'Score estructural'
            ]
            tabla_dept = tabla_dept.sort_values('Casos', ascending=False)
            st.dataframe(tabla_dept, use_container_width=True, hide_index=True)