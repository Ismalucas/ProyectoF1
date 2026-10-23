import pandas as pd
import numpy as np

# 1. Cargar los archivos originales
laps = pd.read_csv('data/monaco_2023_ver_laps.csv')
tel = pd.read_csv('data/monaco_2023_ver_telemetry.csv')

# Convertir fechas a formato datetime
laps['date_start_dt'] = pd.to_datetime(laps['date_start'], format='ISO8601')
tel['date_dt'] = pd.to_datetime(tel['date_dt'], format='ISO8601')

# Posición de referencia (Mediana)
REF_X = -7667.05
REF_Y = -6535.49
TOLERANCE = 0.15  # Décima y media (0.15 segundos)

updated_laps = []
filtered_telemetry_list = []

for idx, lap_row in laps.iterrows():
    driver = lap_row['driver_number']
    lap_num = lap_row['lap_number']
    t_start_approx = lap_row['date_start_dt']
    lap_dur = lap_row['lap_duration']
    
    # Filtrar telemetría para este piloto y vuelta
    sub = tel[(tel['driver_number'] == driver) & (tel['lap_number'] == lap_num)].sort_values('date_dt').copy()
    if sub.empty:
        continue
    
    # Calcular distancia euclidiana a la referencia
    sub['dist_ref'] = np.sqrt((sub['x'] - REF_X)**2 + (sub['y'] - REF_Y)**2)
    
    # Dividir la vuelta en inicio y fin
    mid_time = t_start_approx + pd.Timedelta(seconds=lap_dur / 2)
    start_half = sub[sub['date_dt'] < mid_time].sort_values('dist_ref')
    end_half = sub[sub['date_dt'] >= mid_time].sort_values('dist_ref')
    
    if len(start_half) < 2 or len(end_half) < 2:
        continue
        
    # Coger las DOS posiciones más cercanas tanto de inicio como de fin
    s1 = start_half.iloc[0]
    s2 = start_half.iloc[1]
    e1 = end_half.iloc[0]
    e2 = end_half.iloc[1]
    
    # 1. Comprobar si con las posiciones más cercanas (s1, e1) la diferencia es <= 0.15s
    dur_primary = (e1['date_dt'] - s1['date_dt']).total_seconds()
    diff_primary = abs(dur_primary - lap_dur)
    
    if diff_primary <= TOLERANCE:
        chosen_start = s1['date_dt']
        chosen_end = e1['date_dt']
        chosen_dur = dur_primary
    else:
        # 2. Si no, buscar entre las 4 combinaciones posibles la más cercana a lap_duration
        pairs = [
            (s1['date_dt'], e1['date_dt']),
            (s1['date_dt'], e2['date_dt']),
            (s2['date_dt'], e1['date_dt']),
            (s2['date_dt'], e2['date_dt'])
        ]
        
        best_pair = None
        min_diff = float('inf')
        
        for st, et in pairs:
            d = (et - st).total_seconds()
            diff = abs(d - lap_dur)
            if diff < min_diff:
                min_diff = diff
                best_pair = (st, et, d)
                
        chosen_start = best_pair[0]
        chosen_end = best_pair[1]
        chosen_dur = best_pair[2]

    # Actualizar datos de la vuelta
    new_lap_row = lap_row.copy()
    new_lap_row['date_start'] = chosen_start.isoformat()
    new_lap_row['date_end'] = chosen_end.isoformat()
    new_lap_row['lap_duration_dif'] = new_lap_row['lap_duration'] - chosen_dur
    if 'date_start_dt' in new_lap_row:
        new_lap_row = new_lap_row.drop('date_start_dt')
        
    updated_laps.append(new_lap_row)
    
    # Filtrar telemetría: conservar solo los datos entre el nuevo inicio y fin
    valid_tel = sub[(sub['date_dt'] >= chosen_start) & (sub['date_dt'] <= chosen_end)].copy()
    if 'dist_ref' in valid_tel.columns:
        valid_tel = valid_tel.drop(columns=['dist_ref'])
        
    filtered_telemetry_list.append(valid_tel)

# 2. Construir los nuevos DataFrames y exportar
df_new_laps = pd.DataFrame(updated_laps)
df_new_tel = pd.concat(filtered_telemetry_list, ignore_index=True)

df_new_laps.to_csv('data/monaco_2023_ver_laps_fixed.csv', index=False)
df_new_tel.to_csv('data/monaco_2023_ver_telemetry_fixed.csv', index=False)

print("¡Proceso completado con éxito!")
print(f"-> Vueltas actualizadas guardadas en: monaco_2023_ver_laps_fixed.csv ({len(df_new_laps)} filas)")
print(f"-> Telemetría filtrada guardada en: monaco_2023_ver_telemetry_fixed.csv ({len(df_new_tel)} filas)")