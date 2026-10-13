import os
import time
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="F1 Telemetry Simulator - Monaco", layout="wide")

st.title("🏎️ F1 Interactive Telemetry & Circuit Simulator")

DATA_DIR = "data"
LAPS_FILE = os.path.join(DATA_DIR, "monaco_2023_ver_laps.csv")
TELEMETRY_FILE = os.path.join(DATA_DIR, "monaco_2023_ver_telemetry.csv")

if not os.path.exists(LAPS_FILE) or not os.path.exists(TELEMETRY_FILE):
    st.error("Faltan los ficheros CSV. Ejecuta primero `python extractor.py` para generarlos.")
else:
    laps_df = pd.read_csv(LAPS_FILE)
    telemetry_df = pd.read_csv(TELEMETRY_FILE)

    # Sidebar: Configuración
    st.sidebar.header("🎛️ Configuración de Análisis")
    st.sidebar.subheader("Piloto: Max Verstappen (Red Bull)")

    available_laps = laps_df['lap_number'].dropna().unique()
    
    lap_selected_1 = st.sidebar.selectbox("Selecciona la Vuelta Principal (1)", available_laps, index=len(available_laps)-1)
    
    comparar = st.sidebar.checkbox("Comparar con otra vuelta del mismo piloto")
    lap_selected_2 = None
    if comparar:
        other_laps = [l for l in available_laps if l != lap_selected_1]
        lap_selected_2 = st.sidebar.selectbox("Selecciona la Vuelta a Comparar (2)", other_laps)

    LONGITUD_MONACO = 3337.0

    CURVAS_MONACO = {
        "T1 (Sainte Dévote)": 150,
        "T2 (Beau Rivage)": 400,
        "T3 (Massenet)": 600,
        "T4 (Casino Square)": 780,
        "T5 (Mirabeau Haute)": 1050,
        "T6 (Hairpin)": 1250,
        "T7 (Mirabeau Bas)": 1420,
        "T8 (Portier)": 1600,
        "T9 (Tunnel)": 1850,
        "T10-11 (Chicane)": 2200,
        "T12 (Tabac)": 2450,
        "T13-14 (Piscine)": 2700,
        "T15-16 (La Rascasse)": 3000,
        "T17-18 (Noghès)": 3200
    }

    def preparar_datos_vuelta(lap_num):
        lap_info = laps_df[laps_df['lap_number'] == lap_num].iloc[0]
        lap_data = telemetry_df[telemetry_df['lap_number'] == lap_num].copy()
        
        if not lap_data.empty:
            max_dist = lap_data['distance'].max()
            if max_dist > 0:
                lap_data['distance_normalized'] = (lap_data['distance'] / max_dist) * LONGITUD_MONACO
            else:
                lap_data['distance_normalized'] = lap_data['distance']
        return lap_info, lap_data

    lap_info_1, lap_data_1 = preparar_datos_vuelta(lap_selected_1)
    lap_data_2 = pd.DataFrame()
    if comparar and lap_selected_2:
        _, lap_data_2 = preparar_datos_vuelta(lap_selected_2)

    total_puntos = len(lap_data_1)

    # --- INICIALIZACIÓN DE ESTADO PARA EL REPRODUCTOR ---
    if 'playback_state' not in st.session_state:
        st.session_state.playback_state = False
    if 'frame_idx' not in st.session_state:
        st.session_state.frame_idx = 0

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎬 Controles de Simulación")

    col_b1, col_b2, col_b3 = st.sidebar.columns(3)
    if col_b1.button("▶️ Play"):
        st.session_state.playback_state = True
    if col_b2.button("⏸️ Pause"):
        st.session_state.playback_state = False
    if col_b3.button("🔄 Reset"):
        st.session_state.playback_state = False
        st.session_state.frame_idx = 0

    sim_speed = st.sidebar.select_slider("Velocidad", options=[0.5, 1.0, 2.0, 5.0], value=1.0)

    # Slider controlado por el estado de la simulación
    if total_puntos > 0:
        slider_val = st.sidebar.slider(
            "Progreso de Vuelta",
            0, total_puntos - 1,
            st.session_state.frame_idx
        )
        # Si el usuario mueve el slider manualmente, actualizamos el frame
        if slider_val != st.session_state.frame_idx:
            st.session_state.frame_idx = slider_val

    point_1 = lap_data_1.iloc[st.session_state.frame_idx]
    dist_actual = point_1['distance_normalized']

    # --- DASHBOARD EN VIVO (THROTTLE / BRAKE / SPEED / GEAR) ---
    st.markdown("### 🚦 Dashboard de Telemetría en Vivo")
    
    col_v1, col_v2 = st.columns(2) if (comparar and not lap_data_2.empty) else (st.columns(1)[0], None)

    def render_live_telemetry(col, title, point):
        with col:
            st.markdown(f"#### {title}")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Velocidad", f"{int(point['speed'])} km/h")
            m2.metric("Marcha", f"G{int(point['n_gear'])}")
            
            throttle_val = int(point['throttle'])
            brake_val = int(point['brake'])
            
            m3.metric("Throttle", f"{throttle_val}%")
            m4.metric("Brake", f"{brake_val}%")

            st.caption("Acelerador (%)")
            st.progress(min(max(throttle_val / 100.0, 0.0), 1.0))
            st.caption("Freno (%)")
            st.progress(min(max(brake_val / 100.0, 0.0), 1.0))

    render_live_telemetry(col_v1, f"Vuelta {lap_selected_1}", point_1)

    if comparar and not lap_data_2.empty and col_v2:
        idx_2 = (lap_data_2['distance_normalized'] - dist_actual).abs().idxmin()
        point_2 = lap_data_2.loc[idx_2]
        render_live_telemetry(col_v2, f"Vuelta {lap_selected_2} (Comparativa)", point_2)

    # --- GRÁFICAS Y MAPA ---
    st.markdown("---")
    
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"rowspan": 2}, {"type": "xy"}],
               [None, {"type": "xy"}]],
        subplot_titles=("Circuito de Mónaco (Simulación)", "Velocidad (km/h)", "Marcha (Gear)")
    )

    # Trazado del Circuito
    fig.add_trace(
        go.Scatter(x=lap_data_1['x'], y=lap_data_1['y'], mode='lines', line=dict(color='#E10600', width=3), name='Circuito V1'),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=[point_1['x']], y=[point_1['y']], mode='markers+text',
                   marker=dict(color='#00FFFF', size=14, symbol='circle', line=dict(color='white', width=2)),
                   text=[f"V{lap_selected_1}"], textposition="top center", name='Coche 1'),
        row=1, col=1
    )

    if comparar and not lap_data_2.empty:
        fig.add_trace(
            go.Scatter(x=lap_data_2['x'], y=lap_data_2['y'], mode='lines', line=dict(color='#00FF00', width=2, dash='dot'), name='Circuito V2'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=[point_2['x']], y=[point_2['y']], mode='markers+text',
                       marker=dict(color='#00FF00', size=14, symbol='circle', line=dict(color='white', width=2)),
                       text=[f"V{lap_selected_2}"], textposition="top center", name='Coche 2'),
            row=1, col=1
        )

    # Velocidad
    fig.add_trace(
        go.Scatter(x=lap_data_1['distance_normalized'], y=lap_data_1['speed'], mode='lines', line=dict(color='#00FFFF', width=2), name='Vel V1'),
        row=1, col=2
    )
    if comparar and not lap_data_2.empty:
        fig.add_trace(
            go.Scatter(x=lap_data_2['distance_normalized'], y=lap_data_2['speed'], mode='lines', line=dict(color='#00FF00', width=2, dash='dot'), name='Vel V2'),
            row=1, col=2
        )

    # Marchas
    fig.add_trace(
        go.Scatter(x=lap_data_1['distance_normalized'], y=lap_data_1['n_gear'], mode='lines', line=dict(color='#FFD700', width=2), name='Gear V1'),
        row=2, col=2
    )
    if comparar and not lap_data_2.empty:
        fig.add_trace(
            go.Scatter(x=lap_data_2['distance_normalized'], y=lap_data_2['n_gear'], mode='lines', line=dict(color='#FFA500', width=2, dash='dot'), name='Gear V2'),
            row=2, col=2
        )

    for r in [1, 2]:
        fig.add_vline(x=dist_actual, line_width=2, line_dash="solid", line_color="#FF007F", row=r, col=2)

    for nombre_curva, dist_m in CURVAS_MONACO.items():
        for r in [1, 2]:
            fig.add_vline(x=dist_m, line_width=1, line_dash="dash", line_color="gray", opacity=0.4, row=r, col=2)

    fig.update_layout(
        template='plotly_dark',
        height=650,
        showlegend=False,
        margin=dict(l=20, r=20, t=30, b=20)
    )

    fig.update_xaxes(title_text="Distancia (m)", row=1, col=2, range=[0, LONGITUD_MONACO])
    fig.update_xaxes(title_text="Distancia (m)", row=2, col=2, range=[0, LONGITUD_MONACO])
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=1)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x", scaleratio=1, row=1, col=1)

    st.plotly_chart(fig, width='stretch')

    # --- CONTROL AUTOMÁTICO DE REPRODUCCIÓN ---
    if st.session_state.playback_state:
        if st.session_state.frame_idx < total_puntos - 1:
            st.session_state.frame_idx += 1
            time.sleep(0.08 / sim_speed)
            st.rerun()
        else:
            st.session_state.playback_state = False