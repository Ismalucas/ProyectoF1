import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import pandas as pd

# 1. Cargar archivo de datos
CSV_FILE = 'all_fastest_laps_miami.csv'
try:
  df_all = pd.read_csv(CSV_FILE)
except FileNotFoundError:
  print(
      f"Error: No se encontró '{CSV_FILE}'. Ejecuta primero el script de datos."
  )
  exit()

drivers = list(df_all['driver_code'].unique())

plt.style.use('dark_background')
fig = plt.figure(figsize=(15, 8.5))

# Estructura del grid:
# - Arriba: Circuito (Izquierda) + Telemetría (Derecha)
# - Abajo: Barra completa de controles
gs = fig.add_gridspec(
    2,
    2,
    width_ratios=[3.2, 1],
    height_ratios=[10, 1],
    left=0.03,
    right=0.97,
    top=0.94,
    bottom=0.03,
    wspace=0.1,
    hspace=0.05,
)

ax_map = fig.add_subplot(gs[0, 0])
ax_metrics = fig.add_subplot(gs[0, 1])

# --- 1. CONFIGURACIÓN DEL CIRCUITO ---
x_track = df_all['x'].values
y_track = df_all['y'].values

ax_map.plot(
    x_track,
    y_track,
    color='#333333',
    linewidth=12,
    solid_capstyle='round',
    zorder=1,
)
ax_map.plot(
    x_track,
    y_track,
    color='#1A1A1A',
    linewidth=10,
    solid_capstyle='round',
    zorder=2,
)
ax_map.set_title(
    'F1 QUALIFYING GHOST LAPS SIMULATION',
    color='white',
    fontsize=14,
    fontweight='bold',
)
ax_map.axis('equal')
ax_map.axis('off')

visible_drivers = {code: True for code in drivers}
car_dots = {}

for code in drivers:
  drv_data = df_all[df_all['driver_code'] == code]
  color = drv_data['team_color'].iloc[0]

  (dot,) = ax_map.plot(
      [],
      [],
      'o',
      color=color,
      markersize=9,
      markeredgecolor='white',
      label=code,
      zorder=5,
  )
  car_dots[code] = dot

# --- 2. PANEL DE TELEMETRÍA ---
ax_metrics.axis('off')

# Título y Tiempo en pantalla
ax_metrics.text(
    0.05,
    0.97,
    'TELEMETRÍA EN VIVO',
    color='gray',
    fontsize=10,
    fontweight='bold',
    transform=ax_metrics.transAxes,
)
time_label = ax_metrics.text(
    0.05,
    0.92,
    'TIEMPO: 00:00.00',
    color='#00E5FF',
    fontsize=12,
    fontweight='bold',
    transform=ax_metrics.transAxes,
)

# Botón TOGGLE ALL (Ubicación fija sin pisar pilotos)
ax_toggle_all = fig.add_axes([0.76, 0.86, 0.21, 0.03])
btn_toggle_all = Button(
    ax_toggle_all,
    'DESELECCIONAR TODOS',
    color='#222222',
    hovercolor='#444444',
)
btn_toggle_all.label.set_color('#00E5FF')
btn_toggle_all.label.set_fontsize(7.5)
btn_toggle_all.label.set_fontweight('bold')

all_selected_state = True
driver_row_buttons = {}
metrics_labels = {}

# Posición del primer piloto desplazada hacia abajo
y_start = 0.79
y_step = 0.74 / max(len(drivers), 1)

for i, code in enumerate(drivers):
  team_color = df_all[df_all['driver_code'] == code]['team_color'].iloc[0]
  y_pos = y_start - (i * y_step)

  ax_row = fig.add_axes([0.76, y_pos, 0.21, y_step * 0.85])
  ax_row.set_facecolor('#111111')

  btn = Button(
      ax_row,
      f'{code}: --- km/h | T: --% | B: --%',
      color='#111111',
      hovercolor='#222222',
  )
  btn.label.set_color(team_color)
  btn.label.set_fontsize(8)
  btn.label.set_fontweight('bold')
  btn.label.set_ha('left')
  btn.label.set_x(0.04)

  metrics_labels[code] = btn.label

  def make_toggle(drv_code, button):
    def toggle(event):
      visible_drivers[drv_code] = not visible_drivers[drv_code]
      is_active = visible_drivers[drv_code]
      car_dots[drv_code].set_visible(is_active)
      color_original = df_all[df_all['driver_code'] == drv_code][
          'team_color'
      ].iloc[0]
      button.label.set_color(color_original if is_active else '#444444')
      fig.canvas.draw_idle()

    return toggle

  btn.on_clicked(make_toggle(code, btn))
  driver_row_buttons[code] = btn


def toggle_all_drivers(event):
  global all_selected_state
  all_selected_state = not all_selected_state

  for code in drivers:
    visible_drivers[code] = all_selected_state
    car_dots[code].set_visible(all_selected_state)
    color_original = df_all[df_all['driver_code'] == code]['team_color'].iloc[0]
    metrics_labels[code].set_color(
        color_original if all_selected_state else '#444444'
    )

  btn_toggle_all.label.set_text(
      'DESELECCIONAR TODOS' if all_selected_state else 'SELECCIONAR TODOS'
  )
  fig.canvas.draw_idle()


btn_toggle_all.on_clicked(toggle_all_drivers)

# --- 3. BARRA DE REPRODUCCIÓN ---
current_frame = 0
is_playing = False
step_size = 1  # Control de velocidad por salto de frames
max_frames = int(df_all['time_sec'].max() / 0.05)

# Controles inferiores
ax_play = fig.add_axes([0.03, 0.02, 0.07, 0.04])
ax_reset = fig.add_axes([0.11, 0.02, 0.07, 0.04])
ax_prev = fig.add_axes([0.19, 0.02, 0.05, 0.04])
ax_next = fig.add_axes([0.25, 0.02, 0.05, 0.04])

ax_s05 = fig.add_axes([0.32, 0.02, 0.04, 0.04])
ax_s1 = fig.add_axes([0.37, 0.02, 0.04, 0.04])
ax_s2 = fig.add_axes([0.42, 0.02, 0.04, 0.04])
ax_s4 = fig.add_axes([0.47, 0.02, 0.04, 0.04])

btn_play = Button(ax_play, '▶ PLAY', color='#00E5FF', hovercolor='#00B0FF')
btn_reset = Button(
    ax_reset, '↺ REINICIAR', color='#333333', hovercolor='#555555'
)
btn_prev = Button(ax_prev, '◄ -1s', color='#222222', hovercolor='#444444')
btn_next = Button(ax_next, '+1s ►', color='#222222', hovercolor='#444444')

btn_s05 = Button(ax_s05, '0.5x', color='#222222', hovercolor='#444444')
btn_s1 = Button(ax_s1, '1x', color='#00E5FF', hovercolor='#444444')
btn_s2 = Button(ax_s2, '2x', color='#222222', hovercolor='#444444')
btn_s4 = Button(ax_s4, '4x', color='#222222', hovercolor='#444444')

for b in [
    btn_play,
    btn_reset,
    btn_prev,
    btn_next,
    btn_s05,
    btn_s1,
    btn_s2,
    btn_s4,
]:
  b.label.set_fontweight('bold')
  b.label.set_fontsize(8)

btn_play.label.set_color('black')
btn_s1.label.set_color('black')

# --- 4. ANIMACIÓN Y CONTROLES ---


def render_frame(f):
  """Dibuja el fotograma especificado f."""
  current_time = f * 0.05
  time_label.set_text(f'TIEMPO: {current_time:.2f} s')

  for code in drivers:
    if not visible_drivers[code]:
      continue

    drv_df = df_all[df_all['driver_code'] == code]
    frame_data = drv_df[drv_df['time_sec'] >= current_time].head(1)

    if not frame_data.empty:
      row = frame_data.iloc[0]
      car_dots[code].set_data([row['x']], [row['y']])
      metrics_labels[code].set_text(
          f"{code}: {int(row['speed'])} km/h | T:"
          f" {int(row['throttle'])}% | B: {int(row['brake'])}%"
      )


def frame_generator():
  """Generador que permite saltos de velocidad y reinicio continuo."""
  global current_frame
  while True:
    if is_playing:
      current_frame += step_size
      if current_frame >= max_frames:
        current_frame = max_frames
        # Pausa al terminar
        toggle_play(None)
    yield current_frame


def update(frame):
  render_frame(frame)
  return list(car_dots.values()) + [time_label]


anim = animation.FuncAnimation(
    fig,
    update,
    frames=frame_generator,
    interval=50,
    blit=False,
    repeat=False,
    cache_frame_data=False,
)
anim.event_source.stop()


def toggle_play(event):
  global is_playing, current_frame
  if is_playing:
    anim.event_source.stop()
    btn_play.label.set_text('▶ PLAY')
    btn_play.ax.set_facecolor('#00E5FF')
    is_playing = False
  else:
    # Si la simulación terminó, reiniciar al darle a PLAY de nuevo
    if current_frame >= max_frames:
      current_frame = 0

    anim.event_source.start()
    btn_play.label.set_text('⏸ PAUSA')
    btn_play.ax.set_facecolor('#FF3366')
    is_playing = True
  fig.canvas.draw_idle()


def reset_sim(event):
  global current_frame, is_playing
  anim.event_source.stop()
  is_playing = False
  btn_play.label.set_text('▶ PLAY')
  btn_play.ax.set_facecolor('#00E5FF')

  current_frame = 0
  render_frame(0)
  fig.canvas.draw_idle()


def move_step(seconds):
  global current_frame
  # 1 segundo equivale a 20 frames (pasos de 0.05s)
  frame_offset = int(seconds / 0.05)
  current_frame = max(0, min(max_frames, current_frame + frame_offset))
  render_frame(current_frame)
  fig.canvas.draw_idle()


# --- LÓGICA DE VELOCIDAD CORREGIDA (REPAINT GARANTIZADO) ---
def set_speed(mult, step, active_btn):
  global step_size
  step_size = step

  speed_buttons = [btn_s05, btn_s1, btn_s2, btn_s4]

  # 1. Resetear el color interno y del patch de todos los botones
  for btn in speed_buttons:
    btn.color = '#222222'
    btn.hovercolor = '#444444'
    btn.ax.patch.set_facecolor('#222222')
    btn.label.set_color('white')

  # 2. Resaltar únicamente el botón activo
  active_btn.color = '#00E5FF'
  active_btn.hovercolor = '#00B0FF'
  active_btn.ax.patch.set_facecolor('#00E5FF')
  active_btn.label.set_color('black')

  # 3. Redibujar el lienzo completo
  fig.canvas.draw_idle()


# Asignación de eventos on_clicked
btn_s05.on_clicked(lambda e: set_speed(0.5, 1, btn_s05))
btn_s1.on_clicked(lambda e: set_speed(1.0, 1, btn_s1))
btn_s2.on_clicked(lambda e: set_speed(2.0, 2, btn_s2))
btn_s4.on_clicked(lambda e: set_speed(4.0, 4, btn_s4))


btn_play.on_clicked(toggle_play)
btn_reset.on_clicked(reset_sim)

# Botones de salto temporal
btn_prev.on_clicked(lambda e: move_step(-1.0))
btn_next.on_clicked(lambda e: move_step(1.0))


# Renderizar estado inicial t=0
render_frame(0)

plt.show()