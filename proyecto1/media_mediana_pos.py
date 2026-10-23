import pandas as pd
import numpy as np

# 1. Cargar los datasets
laps = pd.read_csv('data/monaco_2023_ver_laps.csv')
tel = pd.read_csv('data/monaco_2023_ver_telemetry.csv')

# 2. Convertir las fechas a formato datetime
laps['date_start_dt'] = pd.to_datetime(laps['date_start'], format='ISO8601')
tel['date_dt'] = pd.to_datetime(tel['date_dt'], format='ISO8601')

interp_starts = []

# 3. Interpolar las coordenadas X e Y exactas en el momento de inicio de cada vuelta
for idx, lap_row in laps.iterrows():
    driver = lap_row['driver_number']
    lap_num = lap_row['lap_number']
    t_start = lap_row['date_start_dt']
    
    tel_sub = tel[(tel['driver_number'] == driver) & (tel['lap_number'] == lap_num)].sort_values('date_dt').copy()
    if tel_sub.empty:
        continue
    
    before = tel_sub[tel_sub['date_dt'] <= t_start]
    after = tel_sub[tel_sub['date_dt'] >= t_start]
    
    if before.empty or after.empty:
        continue
    
    p_before = before.iloc[-1]
    p_after = after.iloc[0]
    
    if p_before['date_dt'] == p_after['date_dt']:
        x_start = p_before['x']
        y_start = p_before['y']
    else:
        t_b = p_before['date_dt'].timestamp()
        t_a = p_after['date_dt'].timestamp()
        t_target = t_start.timestamp()
        
        ratio = (t_target - t_b) / (t_a - t_b)
        x_start = p_before['x'] + ratio * (p_after['x'] - p_before['x'])
        y_start = p_before['y'] + ratio * (p_after['y'] - p_before['y'])
    
    interp_starts.append({'x': x_start, 'y': y_start})

df_interp = pd.DataFrame(interp_starts)

# 4. Calcular la media y la mediana de X e Y
mean_x = df_interp['x'].mean()
mean_y = df_interp['y'].mean()
median_x = df_interp['x'].median()
median_y = df_interp['y'].median()

# 5. Mostrar resultados
print(f"--- MEDIA ---")
print(f"X: {mean_x:.2f}")
print(f"Y: {mean_y:.2f}\n")

print(f"--- MEDIANA ---")
print(f"X: {median_x:.2f}")
print(f"Y: {median_y:.2f}")