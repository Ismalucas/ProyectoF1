import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import numpy as np
import pandas as pd

# 1. Cargar los datos del archivo CSV generado por main.py
CSV_FILE = 'fastest_lap_miami.csv'

try:
  df = pd.read_csv(CSV_FILE)
except FileNotFoundError:
  print(
      f"Error: No se encontró el archivo '{CSV_FILE}'. Ejecuta primero"
      ' main.py.'
  )
  exit()

# Extraer coordenadas X e Y
x_coords = df['x'].values
y_coords = df['y'].values
time_seconds = df['time_seconds'].values

# 2. Configurar la figura y el estilo visual (Estilo Dark/F1)
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(10, 7))
plt.subplots_adjust(bottom=0.2)  # Dejar espacio inferior para el botón

# Dibujar el trazado completo del circuito de fondo (Línea gris)
ax.plot(x_coords, y_coords, color='#444444', linewidth=3, label='Circuito')
ax.set_title(
    f'Simulación Vuelta Rápida - Piloto #{df["driver_number"].iloc[0]}',
    fontsize=14,
    color='white',
    pad=15,
)
ax.set_xlabel('X (coordenadas)', color='gray')
ax.set_ylabel('Y (coordenadas)', color='gray')
ax.axis('equal')  # Mantener la proporción geométrica real del circuito
ax.grid(True, linestyle='--', alpha=0.2)

# Elementos dinámicos de la animación:
# - Coche (Punto rojo brillante)
# - Estela/Trazada recorrida (Línea cian)
# - Etiqueta de tiempo en pantalla
(car_dot,) = ax.plot([], [], 'ro', markersize=9, label='Monoplaza')
(trail_line,) = ax.plot(
    [], [], color='#00E5FF', linewidth=2.5, alpha=0.8, label='Trazada'
)
time_text = ax.text(
    0.02,
    0.95,
    '',
    transform=ax.transAxes,
    color='white',
    fontsize=12,
    bbox=dict(boxstyle='round', facecolor='#222222', alpha=0.8),
)

# Variable global para controlar la animación
anim = None


# 3. Funciones de actualización de la animación
def init():
  """Inicializa los elementos limpios antes de empezar."""
  car_dot.set_data([], [])
  trail_line.set_data([], [])
  time_text.set_text('')
  return car_dot, trail_line, time_text


def update(frame):
  """Actualiza la posición del coche en cada fotograma."""
  # Posición actual
  cx = x_coords[frame]
  cy = y_coords[frame]

  # Actualizar punto del coche
  car_dot.set_data([cx], [cy])

  # Actualizar la estela recorrida hasta el fotograma actual
  trail_line.set_data(x_coords[: frame + 1], y_coords[: frame + 1])

  # Actualizar tiempo en pantalla
  current_time = time_seconds[frame]
  time_text.set_text(f'Tiempo: {current_time:.2f} s')

  return car_dot, trail_line, time_text


# 4. Configurar el Botón de Control
ax_button = plt.axes([0.4, 0.05, 0.2, 0.075])  # [left, bottom, width, height]
btn_start = Button(
    ax_button,
    'Iniciar Simulación',
    color='#1f77b4',
    hovercolor='#2ca02c',
)


def start_simulation(event):
  """Función invocada al hacer clic en el botón."""
  global anim
  if anim is None:
    # Crear la animación a 30 FPS aproximadamente (interval=30 ms)
    anim = animation.FuncAnimation(
        fig,
        update,
        frames=len(df),
        init_func=init,
        interval=30,
        blit=True,
        repeat=False,
    )
    plt.draw()


# Conectar el botón con la función
btn_start.on_clicked(start_simulation)

ax.legend(loc='lower right')
plt.show()