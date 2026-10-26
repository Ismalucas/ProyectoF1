import pandas as pd
import numpy as np

# 1. Cargar el CSV de telemetría fixed
tel = pd.read_csv('data/monaco_2023_ver_telemetry_fixed.csv')

# Coordenadas de los 2 puntos de cambio de sector
sector_coords = [
    (-1831, -546),   # Fin Sector 1 / Inicio Sector 2
    (-7212, -5849)   # Fin Sector 2 / Inicio Sector 3
]

# Coordenadas de los microsectores
micro_coords = [
    (-6739, -4572),
    (-3184, -3702),
    (-2624, -1573),
    (-850, -313),
    (531, -2412),
    (-3493, -4314),
    (-6763, -7497),
    (-6850, -8442),
    (-7027, -9028)
]

# Inicializar columna por defecto
tel['point_type'] = 'No'

start_indices = []
end_indices = []
sector_indices = []
micro_indices = []

# 2. Recorrer cada vuelta de cada piloto
for (driver, lap), group in tel.groupby(['driver_number', 'lap_number']):
    # El primer punto de la vuelta es el Inicio y el último es el Fin
    start_indices.append(group.index[0])
    end_indices.append(group.index[-1])
    
    # Buscar los puntos más cercanos para los sectores intermedios
    for cx, cy in sector_coords:
        dists = np.sqrt((group['x'] - cx)**2 + (group['y'] - cy)**2)
        sector_indices.append(dists.idxmin())
        
    # Buscar los puntos más cercanos para los microsectores
    for cx, cy in micro_coords:
        dists = np.sqrt((group['x'] - cx)**2 + (group['y'] - cy)**2)
        micro_indices.append(dists.idxmin())

# 3. Asignar etiquetas aplicando jerarquía
tel.loc[micro_indices, 'point_type'] = 'Microsector'
tel.loc[sector_indices, 'point_type'] = 'Sector'
tel.loc[start_indices, 'point_type'] = 'Inicio'
tel.loc[end_indices, 'point_type'] = 'Fin'

# 4. Sobrescribir directamente el archivo tagged
tel.to_csv('data/monaco_2023_ver_telemetry_tagged.csv', index=False)

print("¡Proceso completado con éxito!")
print(tel['point_type'].value_counts())