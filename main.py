from datetime import datetime, timezone
import pandas as pd
import requests


def get_fastest_lap_telemetry(
    year=2023, circuit_name="Miami", driver_number=1, session_name="Qualifying"
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

  df_laps = pd.DataFrame(r_laps).dropna(
      subset=["lap_duration", "date_start"]
  )
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

  # 4. Calcular el tiempo de inicio y fin con Pandas (maneja husos horarios sin fallos)
  dt_start = pd.to_datetime(date_start_str)
  dt_end = dt_start + pd.Timedelta(seconds=lap_duration)

  # Convertir a cadenas ISO simples compatibles con OpenF1
  start_iso = dt_start.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"
  end_iso = dt_end.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"

  print("Descargando coordenadas de posición (/location)...")

  # Intento 1: Filtrar por rango de tiempo en la API
  location_url = (
      f"{base_url}/location?session_key={session_key}&driver_number={driver_number}"
      f"&date>={start_iso}&date<={end_iso}"
  )
  r_loc = requests.get(location_url).json()

  # Intento 2: Fallback trayendo los datos del piloto y filtrando localmente
  if not r_loc or (isinstance(r_loc, dict) and "detail" in r_loc):
    print(
        "-> Filtro por URL no devolvió puntos. Aplicando descarga directa por"
        " sesión y filtrado local..."
    )
    fallback_url = (
        f"{base_url}/location?session_key={session_key}&driver_number={driver_number}"
    )
    r_loc = requests.get(fallback_url).json()

    if not r_loc or (isinstance(r_loc, dict) and "detail" in r_loc):
      raise ValueError("No se encontraron coordenadas en /location.")

    # Convertir a DataFrame y filtrar localmente por el tiempo de la vuelta
    df_loc_all = pd.DataFrame(r_loc)
    df_loc_all["date_dt"] = pd.to_datetime(df_loc_all["date"])

    df_location = df_loc_all[
        (df_loc_all["date_dt"] >= dt_start) & (df_loc_all["date_dt"] <= dt_end)
    ].copy()
  else:
    if isinstance(r_loc, dict):
      r_loc = [r_loc]
    df_location = pd.DataFrame(r_loc)
    df_location["date_dt"] = pd.to_datetime(df_location["date"])

  if df_location.empty:
    raise ValueError(
        "No se encontraron coordenadas GPS en el rango de tiempo de la vuelta."
    )

  # 5. Normalizar el tiempo (t = 0.0s en el primer punto de la vuelta)
  start_timestamp = df_location["date_dt"].min()
  df_location["time_seconds"] = (
      df_location["date_dt"] - start_timestamp
  ).dt.total_seconds()

  df_telemetry = df_location[
      ["driver_number", "time_seconds", "x", "y", "z", "date"]
  ].sort_values("time_seconds")

  return df_telemetry


if __name__ == "__main__":
  try:
    # Probamos con Max Verstappen (#1) en Miami 2024


    df_telemetry = get_fastest_lap_telemetry(
        year=2023,
        circuit_name="Monte Carlo",
        driver_number=1,
        session_name="Qualifying",
    )

    print("\n--- ¡Telemetría obtenida con éxito! ---")
    print(df_telemetry.head(10))
    print(f"\nTotal puntos GPS recuperados: {len(df_telemetry)}")

    # Guardar a archivo CSV para usar en la animación de pantalla
    df_telemetry.to_csv("fastest_lap_miami.csv", index=False)
    print("Guardado en 'fastest_lap_miami.csv'")

  except Exception as e:
    print(f"\nError: {e}")