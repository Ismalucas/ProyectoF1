import requests
import matplotlib.pyplot as plt

def dibujar_circuito_monaco_con_curvas():
    url_monaco = "https://api.multiviewer.app/api/v1/circuits/22/2023"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url_monaco, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        x_coords = data.get('x', [])
        y_coords = data.get('y', [])
        
        if not x_coords or not y_coords:
            print("No se encontraron las coordenadas.")
            return

        total_puntos = len(x_coords)

        # Diccionario con las curvas de Mónaco y su posición relativa aproximada (% del trazado)
        curvas = {
            "T1: Sainte Dévote": 0.05,
            "T2: Beau Rivage": 0.12,
            "T3: Massenet": 0.18,
            "T4: Casino Square": 0.23,
            "T5: Mirabeau Haute": 0.32,
            "T6: Grand Hôtel Hairpin": 0.38,
            "T7: Mirabeau Bas": 0.43,
            "T8: Portier": 0.48,
            "T9: Le Tunnel": 0.56,
            "T10/11: Nouvelle Chicane": 0.67,
            "T12: Tabac": 0.74,
            "T13/14: Louis Chiron / Piscine": 0.81,
            "T15/16: La Rascasse": 0.90,
            "T17/18: Antony Noghès": 0.96
        }

        # Configuración del gráfico
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # 1. Trazado principal en rojo F1
        ax.plot(x_coords, y_coords, color='#E10600', linewidth=3, label='Circuito de Mónaco')
        
        # 2. Línea de meta
        ax.scatter(x_coords[0], y_coords[0], color='white', s=120, zorder=5, label='Línea de Meta')

        # 3. Dibujar marcas y nombres de cada curva
        for nombre, porcentaje in curvas.items():
            idx = int(total_puntos * porcentaje) % total_puntos
            x, y = x_coords[idx], y_coords[idx]
            
            # Punto indicador en el trazado
            ax.scatter(x, y, color='#FFD700', s=35, zorder=4)
            
            # Etiqueta de texto con puntero
            ax.annotate(
                nombre,
                (x, y),
                xytext=(10, 10),
                textcoords="offset points",
                fontsize=8,
                color='white',
                fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", fc="#1E1E1E", ec="#FFD700", lw=0.8, alpha=0.85),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.1", color="#FFD700", lw=0.8)
            )

        # Ajustes finales
        ax.set_title("Circuit de Monaco - Nombres de las Curvas", fontsize=16, fontweight='bold', pad=20, color='white')
        ax.set_aspect('equal')
        ax.axis('off')
        
        plt.legend(loc='upper right')
        plt.tight_layout()
        plt.show()

    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con la API: {e}")

if __name__ == "__main__":
    dibujar_circuito_monaco_con_curvas()