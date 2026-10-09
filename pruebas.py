from datetime import datetime, timezone
import pandas as pd
import requests
import json
from urllib.request import urlopen

url = "https://api.openf1.org/v1/meetings?year=2023"
response = urlopen(url)
meetings = json.loads(response.read().decode('utf-8'))


def get_fastest_lap_telemetry_with_margin(
    year=2024,
    circuit_name="Miami",
    driver_number=1,
    session_name="Qualifying",
    margin_seconds=5,  # 👈 Margen en segundos antes y después de la vuelta
):
  base_url = "https://api.openf1.org/v1"

  # 1. Obtener Meeting
  print(f"Buscando Gran Premio de {circuit_name} ({year})...")
  r_meet = requests.get(
      f"{base_url}/meetings",
      params={"year": year, "circuit_short_name": circuit_name},
  ).json()
  if not r_meet or "detail" in r_meet:
    raise ValueError(f"No se encontró el GP de {circuit_name} ({year}).")
  meeting_key = r_meet[0]["meeting_key"]

  # 2. Obtener Sesión
  print(f"Buscando la sesión '{session_name}'...")
  r_sess = requests.get(
      f"{base_url}/sessions",
      params={"meeting_key": meeting_key, "session_name": session_name},
  ).json()
  if not r_sess or "detail" in r_sess:
    raise ValueError(f"No se encontró la sesión '{session_name}'.")
  session_key = r_sess[0]["session_key"]

  # 3. Obtener Vueltas y buscar la más rápida
  print(
      f"Buscando vueltas del piloto #{driver_number} (session_key:"
      f" {session_key})..."
  )
  r_laps = requests.get(
      f"{base_url}/laps",
      params={"session_key": session_key, "driver_number": driver_number},
  ).json()
  if not r_laps or "detail" in r_laps:
    raise ValueError(
        f"No hay registros de vueltas para el piloto #{driver_number}."
    )

  df_laps = pd.DataFrame(r_laps).dropna(subset=["lap_duration", "date_start"])
  if df_laps.empty:
    raise ValueError("No hay vueltas completadas con tiempo válido.")

  fastest_lap = df_laps.loc[df_laps["lap_duration"].idxmin()]
  lap_num = fastest_lap["lap_number"]
  lap_duration = fastest_lap["lap_duration"]
  date_start_str = fastest_lap["date_start"]

  print(
      f"-> Vuelta rápida: Lap #{lap_num} | Tiempo: {lap_duration}s | Inicio:"
      f" {date_start_str}"
  )

  # 4. Amplitud del rango temporal con MARGEN antes y después
  dt_lap_start = pd.to_datetime(date_start_str, format="ISO8601", utc=True)
  dt_lap_end = dt_lap_start + pd.Timedelta(seconds=lap_duration)

  # Extendemos los límites con el margen
  dt_query_start = dt_lap_start - pd.Timedelta(seconds=margin_seconds)
  dt_query_end = dt_lap_end + pd.Timedelta(seconds=margin_seconds)

  print(
      f"Descargando /location con un margen de ±{margin_seconds} segundos..."
  )

  # Descarga directa por sesión y filtrado local robusto
  fallback_url = (
      f"{base_url}/location?session_key={session_key}&driver_number={driver_number}"
  )
  r_loc = requests.get(fallback_url).json()

  if not r_loc or (isinstance(r_loc, dict) and "detail" in r_loc):
    raise ValueError("No se encontraron coordenadas en /location.")

  df_loc_all = pd.DataFrame(r_loc)
  df_loc_all["date_dt"] = pd.to_datetime(
      df_loc_all["date"], format="ISO8601", utc=True
  )

  # Filtrar el rango ampliado
  df_location = df_loc_all[
      (df_loc_all["date_dt"] >= dt_query_start)
      & (df_loc_all["date_dt"] <= dt_query_end)
  ].copy()

  if df_location.empty:
    raise ValueError(
        "No se encontraron coordenadas GPS en el rango ampliado."
    )

  # 5. Normalizar el tiempo haciendo que t = 0.0s sea el INICIO EXACTO DE LA VUELTA
  # Los valores negativos (< 0.0s) corresponden a los segundos previos
  # Los valores mayores a lap_duration corresponden a los segundos posteriores
  df_location["time_seconds"] = (
      df_location["date_dt"] - dt_lap_start
  ).dt.total_seconds()

  # Etiquetar fases
  def get_phase(t):
    if t < 0:
      return "Pre-Vuelta"
    elif t <= lap_duration:
      return "Vuelta Rápida"
    else:
      return "Post-Vuelta"

  df_location["lap_phase"] = df_location["time_seconds"].apply(get_phase)

  df_telemetry = df_location[
      ["driver_number", "time_seconds", "x", "y", "z", "lap_phase", "date"]
  ].sort_values("time_seconds")

  return df_telemetry, lap_duration


if __name__ == "__main__":
  try:
    for meeting in meetings:
      print(f"Circuito: {meeting.get('circuit_short_name')} | Evento: {meeting.get('meeting_official_name')}")
    

    margin = 3  # Segundos extra antes y después
    df_telemetry, duration = get_fastest_lap_telemetry_with_margin(
        year=2024,
        circuit_name="Miami",
        driver_number=1,
        session_name="Qualifying",
        margin_seconds=margin,
    )

    print("\n--- Puntos de entrada (Pre-Vuelta) ---")
    print(df_telemetry[df_telemetry["time_seconds"] < 2])

    print("\n--- Puntos de salida (Post-Vuelta) ---")
    print(df_telemetry[df_telemetry["time_seconds"] > duration -2])

    print(f"\nTotal puntos recuperados con ±{margin}s: {len(df_telemetry)}")

  except Exception as e:
    print(f"\nError: {e}")