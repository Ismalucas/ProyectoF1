import pandas as pd
import numpy as np

# 1. Cargar los datasets corregidos
laps = pd.read_csv('data/monaco_2023_ver_laps_fixed.csv')
tel = pd.read_csv('data/monaco_2023_ver_telemetry_fixed.csv')

laps['date_start'] = pd.to_datetime(laps['date_start'], format='ISO8601')
laps['date_end'] = pd.to_datetime(laps['date_end'], format='ISO8601')
tel['date_dt'] = pd.to_datetime(tel['date_dt'], format='ISO8601')

# ==========================================
# 2. LOCALIZACIÓN DE LOS PUNTOS DE SECTORES
# ==========================================
sector2_starts = []
sector3_starts = []

for idx, lap_row in laps.iterrows():
    driver = lap_row['driver_number']
    lap_num = lap_row['lap_number']
    t_start = lap_row['date_start']
    dur_s1 = lap_row['duration_sector_1']
    dur_s2 = lap_row['duration_sector_2']
    
    # Tiempos estimados de fin de sector 1 y fin de sector 2
    t_s2 = t_start + pd.Timedelta(seconds=dur_s1)
    t_s3 = t_s2 + pd.Timedelta(seconds=dur_s2)
    
    sub = tel[(tel['driver_number'] == driver) & (tel['lap_number'] == lap_num)].copy()
    if sub.empty:
        continue
        
    # Encontrar punto de telemetría más cercano a los cambios de sector
    sub['diff_s2'] = (sub['date_dt'] - t_s2).abs().dt.total_seconds()
    sub['diff_s3'] = (sub['date_dt'] - t_s3).abs().dt.total_seconds()
    
    pt_s2 = sub.loc[sub['diff_s2'].idxmin()]
    pt_s3 = sub.loc[sub['diff_s3'].idxmin()]
    
    sector2_starts.append({'x': pt_s2['x'], 'y': pt_s2['y']})
    sector3_starts.append({'x': pt_s3['x'], 'y': pt_s3['y']})

df_s2 = pd.DataFrame(sector2_starts)
df_s3 = pd.DataFrame(sector3_starts)

print("=== MEDIANAS DE LOS LÍMITES DE SECTORES ===")
print(f"Fin Sector 1 / Inicio Sector 2 -> X: {df_s2['x'].median():.2f}, Y: {df_s2['y'].median():.2f}")
print(f"Fin Sector 2 / Inicio Sector 3 -> X: {df_s3['x'].median():.2f}, Y: {df_s3['y'].median():.2f}\n")

# ==========================================
# 3. LOCALIZACIÓN DE LOS MICROSECTORES
# ==========================================
micro_coords = [
    (-6750, -4500),
    (-3200, -3600),
    (-2600, -1600),
    (-850, -300),
    (-520, -2400),
    (-3500, -4300),
    (-6800, -7500),
    (-6850, -8450),
    (-7000, -9000)
]

print("=== MEDIANAS DE LOS PUNTOS DE MICROSECTORES ===")
for mx, my in micro_coords:
    # Calcular distancia euclidiana de cada punto de telemetría al punto de referencia (mx, my)
    tel_copy = tel.copy()
    tel_copy['dist_target'] = np.sqrt((tel_copy['x'] - mx)**2 + (tel_copy['y'] - my)**2)
    
    # Para cada vuelta y piloto, extraer el punto de telemetría más cercano a la referencia
    min_points = tel_copy.sort_values('dist_target').groupby(['driver_number', 'lap_number']).first().reset_index()
    
    med_x = min_points['x'].median()
    med_y = min_points['y'].median()
    print(f"Ref ({mx}, {my}) -> Mediana X: {med_x:.2f}, Y: {med_y:.2f}")