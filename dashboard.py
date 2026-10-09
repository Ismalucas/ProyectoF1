import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="F1 Telemetry Analyzer (CSV Mode)", layout="wide")

st.title("🏎️ F1 Telemetry & Performance Analyzer")
st.sidebar.header("Carga de Datos")

DATA_DIR = "data"
LAPS_FILE = os.path.join(DATA_DIR, "monaco_2023_ver_laps.csv")
TELEMETRY_FILE = os.path.join(DATA_DIR, "monaco_2023_ver_telemetry.csv")

# Cargar archivos CSV
if not os.path.exists(LAPS_FILE) or not os.path.exists(TELEMETRY_FILE):
    st.error("No se encontraron los archivos CSV. Ejecuta primero `python extractor.py` para generar los datos.")
else:
    laps_df = pd.read_csv(LAPS_FILE)
    telemetry_df = pd.read_csv(TELEMETRY_FILE)

    st.sidebar.subheader("Piloto: Max Verstappen (1)")
    st.sidebar.text("Sesión: Monaco GP 2023 - Qualy")

    # Selector de vuelta disponible en el CSV
    available_laps = laps_df['lap_number'].dropna().unique()
    lap_selected = st.sidebar.selectbox("Selecciona la vuelta:", available_laps)

    # 1. Mostrar resumen de sectores y tiempos
    lap_info = laps_df[laps_df['lap_number'] == lap_selected].iloc[0]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Tiempo Vuelta", f"{lap_info['lap_duration']}s" if pd.notna(lap_info['lap_duration']) else "N/A")
    col2.metric("Sector 1", f"{lap_info['duration_sector_1']}s" if pd.notna(lap_info['duration_sector_1']) else "N/A")
    col3.metric("Sector 2", f"{lap_info['duration_sector_2']}s" if pd.notna(lap_info['duration_sector_2']) else "N/A")
    col4.metric("Sector 3", f"{lap_info['duration_sector_3']}s" if pd.notna(lap_info['duration_sector_3']) else "N/A")
    col5.metric("Speed Trap", f"{lap_info['st_speed']} km/h" if pd.notna(lap_info['st_speed']) else "N/A")

    # 2. Filtrar telemetría de la vuelta seleccionada del CSV
    lap_telemetry = telemetry_df[telemetry_df['lap_number'] == lap_selected]

    if not lap_telemetry.empty:
        st.subheader(f"Telemetría de la Vuelta {lap_selected} (con +-3s de margen)")
        col_map, col_charts = st.columns([1, 1])

        # Renderizar mapa de trazado
        with col_map:
            st.markdown("**Trazado en Coordenadas ($X$, $Y$)**")
            fig_map, ax_map = plt.subplots(figsize=(6, 6))
            plt.style.use('dark_background')
            ax_map.plot(lap_telemetry['x'], lap_telemetry['y'], color='#E10600', linewidth=2.5)
            ax_map.set_aspect('equal')
            ax_map.axis('off')
            st.pyplot(fig_map)

        # Renderizar gráficos de telemetría sincronizados
        with col_charts:
            st.markdown("**Métricas del Vehículo**")
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 6), sharex=True)
            plt.style.use('dark_background')

            ax1.plot(lap_telemetry['speed'], color='#00FFFF', label='Speed (km/h)')
            ax1.legend(loc='upper right')

            ax2.plot(lap_telemetry['throttle'], color='#00FF00', label='Throttle %')
            ax2.plot(lap_telemetry['brake'], color='#FF0000', label='Brake %')
            ax2.legend(loc='upper right')

            ax3.plot(lap_telemetry['n_gear'], color='#FFD700', label='Gear')
            ax3.legend(loc='upper right')

            plt.tight_layout()
            st.pyplot(fig)
    else:
        st.warning("No hay datos de telemetría registrados para esta vuelta.")