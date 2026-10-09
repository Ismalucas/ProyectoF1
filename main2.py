import numpy as np
import pandas as pd
import requests

BASE_URL = 'https://api.openf1.org/v1'


def get_all_drivers_fastest_laps(
    year=2024, circuit_name='Miami', session_name='Qualifying'
):
  meet = requests.get(
      f'{BASE_URL}/meetings',
      params={'year': year, 'circuit_short_name': circuit_name},
  ).json()
  meeting_key = meet[0]['meeting_key']

  sess = requests.get(
      f'{BASE_URL}/sessions',
      params={'meeting_key': meeting_key, 'session_name': session_name},
  ).json()
  session_key = sess[0]['session_key']

  drivers_data = requests.get(
      f'{BASE_URL}/drivers', params={'session_key': session_key}
  ).json()
  drivers_df = pd.DataFrame(drivers_data)

  all_telemetry_list = []
  print(f'Procesando y alineando a meta pilotos de {circuit_name}...')

  for _, driver in drivers_df.iterrows():
    drv_num = driver['driver_number']
    drv_code = driver['name_acronym']
    team_color = f"#{driver.get('team_colour', 'FFFFFF')}"

    laps = requests.get(
        f'{BASE_URL}/laps',
        params={'session_key': session_key, 'driver_number': drv_num},
    ).json()
    if not laps or isinstance(laps, dict):
      continue

    df_laps = pd.DataFrame(laps).dropna(subset=['lap_duration', 'date_start'])
    if df_laps.empty:
      continue

    fastest_lap = df_laps.loc[df_laps['lap_duration'].idxmin()]
    dt_start = pd.to_datetime(
        fastest_lap['date_start'], format='ISO8601', utc=True
    )
    dt_end = dt_start + pd.Timedelta(seconds=fastest_lap['lap_duration'])

    loc_data = requests.get(
        f'{BASE_URL}/location?session_key={session_key}&driver_number={drv_num}'
    ).json()
    car_data = requests.get(
        f'{BASE_URL}/car_data?session_key={session_key}&driver_number={drv_num}'
    ).json()

    if (
        not loc_data
        or isinstance(loc_data, dict)
        or not car_data
        or isinstance(car_data, dict)
    ):
      continue

    df_loc = pd.DataFrame(loc_data)
    df_car = pd.DataFrame(car_data)

    df_loc['date_dt'] = pd.to_datetime(
        df_loc['date'], format='ISO8601', utc=True
    )
    df_car['date_dt'] = pd.to_datetime(
        df_car['date'], format='ISO8601', utc=True
    )

    # Recorte ajustado a la vuelta
    df_loc = df_loc[
        (df_loc['date_dt'] >= dt_start) & (df_loc['date_dt'] <= dt_end)
    ].sort_values('date_dt')
    df_car = df_car[
        (df_car['date_dt'] >= dt_start) & (df_car['date_dt'] <= dt_end)
    ].sort_values('date_dt')

    if df_loc.empty or df_car.empty:
      continue

    df_merged = pd.merge_asof(
        df_loc,
        df_car[['date_dt', 'speed', 'throttle', 'brake', 'n_gear']],
        on='date_dt',
        direction='nearest',
    )

    # SINCRONIZACIÓN EXACTA A METRA (t_0 = 0.0s en el primer punto registrado)
    min_time_dt = df_merged['date_dt'].min()
    df_merged['time_sec'] = (
        df_merged['date_dt'] - min_time_dt
    ).dt.total_seconds()

    # Re-muestreo uniforme
    target_time = np.arange(0, fastest_lap['lap_duration'], 0.05)

    interp_df = pd.DataFrame({'time_sec': target_time})
    interp_df['x'] = np.interp(
        target_time, df_merged['time_sec'], df_merged['x']
    )
    interp_df['y'] = np.interp(
        target_time, df_merged['time_sec'], df_merged['y']
    )
    interp_df['speed'] = np.interp(
        target_time, df_merged['time_sec'], df_merged['speed']
    )
    interp_df['throttle'] = np.interp(
        target_time, df_merged['time_sec'], df_merged['throttle']
    )
    interp_df['brake'] = np.interp(
        target_time, df_merged['time_sec'], df_merged['brake']
    )

    interp_df['driver_number'] = drv_num
    interp_df['driver_code'] = drv_code
    interp_df['team_color'] = team_color

    all_telemetry_list.append(interp_df)
    print(f'-> Alineado correctamente: #{drv_num} ({drv_code})')

  full_df = pd.concat(all_telemetry_list, ignore_index=True)
  full_df.to_csv('all_fastest_laps_miami.csv', index=False)
  print("\n¡Datos guardados y alineados a Meta en 'all_fastest_laps_miami.csv'!")


if __name__ == '__main__':
  get_all_drivers_fastest_laps()