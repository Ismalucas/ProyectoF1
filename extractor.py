import os
import requests
import pandas as pd
from datetime import timedelta

BASE_OPENF1 = "https://api.openf1.org/v1"

class F1DataExtractor:
    def __init__(self, session_key=9090, driver_number=1, circuit_key=22, year=2023):
        self.session_key = session_key
        self.driver_number = driver_number
        self.circuit_key = circuit_key
        self.year = year

    def get_qualy_laps(self, max_lap_time=75.0):
        """Obtiene únicamente las 10 vueltas rápidas lanzadas"""
        url = f"{BASE_OPENF1}/laps?session_key={self.session_key}&driver_number={self.driver_number}"
        res = requests.get(url).json()
        
        if isinstance(res, dict):
            res = [res]

        laps_data = []
        for lap in res:
            laps_data.append({
                'lap_number': lap.get('lap_number'),
                'lap_duration': lap.get('lap_duration'),
                'duration_sector_1': lap.get('duration_sector_1'),
                'duration_sector_2': lap.get('duration_sector_2'),
                'duration_sector_3': lap.get('duration_sector_3'),
                'st_speed': lap.get('st_speed'),
                'date_start': lap.get('date_start'),
                'is_pit_out_lap': lap.get('is_pit_out_lap')
            })
        
        df = pd.DataFrame(laps_data)
        df = df.dropna(subset=['lap_duration', 'duration_sector_1', 'duration_sector_2', 'duration_sector_3'])

        if max_lap_time:
            df = df[df['lap_duration'] <= max_lap_time]

        return df.reset_index(drop=True)

    def get_full_session_telemetry(self, laps_df, margin_seconds=3):
        """Extrae la telemetría y posición para cada una de las vueltas"""
        all_telemetry = []

        for _, lap in laps_df.iterrows():
            lap_num = lap['lap_number']
            date_start_str = lap['date_start']
            duration = lap['lap_duration']

            print(f"Procesando Vuelta {lap_num} (Tiempo: {duration}s)...")

            if not date_start_str or pd.isna(duration):
                continue

            try:
                # 1. Parsing robusto de la fecha de inicio usando ISO8601 flexible
                dt_start = pd.to_datetime(date_start_str, format='ISO8601', utc=True)
                dt_end = dt_start + timedelta(seconds=duration)
                
                dt_query_start = dt_start - timedelta(seconds=margin_seconds)
                dt_query_end = dt_end + timedelta(seconds=margin_seconds)

                # Convertir a cadena limpia en ISO8601 para OpenF1
                str_start = dt_query_start.isoformat().replace('+00:00', 'Z')
                str_end = dt_query_end.isoformat().replace('+00:00', 'Z')

                url_car = f"{BASE_OPENF1}/car_data?session_key={self.session_key}&driver_number={self.driver_number}&date>={str_start}&date<={str_end}"
                url_loc = f"{BASE_OPENF1}/location?session_key={self.session_key}&driver_number={self.driver_number}&date>={str_start}&date<={str_end}"

                car_res = requests.get(url_car).json()
                loc_res = requests.get(url_loc).json()

                if isinstance(car_res, dict): car_res = [car_res] if car_res else []
                if isinstance(loc_res, dict): loc_res = [loc_res] if loc_res else []

                df_car = pd.DataFrame(car_res)
                df_loc = pd.DataFrame(loc_res)

                if df_car.empty or df_loc.empty:
                    print(f"  ⚠️ Telemetría vacía para la vuelta {lap_num}")
                    continue

                req_car = {'date', 'brake', 'n_gear', 'speed', 'throttle'}
                req_loc = {'date', 'x', 'y', 'z'}

                if not req_car.issubset(df_car.columns) or not req_loc.issubset(df_loc.columns):
                    print(f"  ⚠️ Faltan columnas en la respuesta de la vuelta {lap_num}")
                    continue

                df_car = df_car[['date', 'brake', 'n_gear', 'speed', 'throttle']]
                df_loc = df_loc[['date', 'x', 'y', 'z']]

                # 2. Conversión a datetime con formato flexible ISO8601
                df_car['date_dt'] = pd.to_datetime(df_car['date'], format='ISO8601', utc=True)
                df_loc['date_dt'] = pd.to_datetime(df_loc['date'], format='ISO8601', utc=True)

                # Sincronización por proximidad temporal
                merged = pd.merge_asof(
                    df_car.sort_values('date_dt'),
                    df_loc.sort_values('date_dt'),
                    on='date_dt',
                    direction='nearest'
                )
                
                merged['lap_number'] = lap_num
                all_telemetry.append(merged)
                print(f"  ✅ Vuelta {lap_num} extraída correctamente ({len(merged)} puntos)")

            except Exception as e:
                print(f"  ❌ Error en vuelta {lap_num}: {e}")

        if all_telemetry:
            return pd.concat(all_telemetry, ignore_index=True)
        return pd.DataFrame()

    def export_to_csv(self, output_dir="data"):
        os.makedirs(output_dir, exist_ok=True)
        
        print("Obteniendo resumen de vueltas...")
        laps_df = self.get_qualy_laps(max_lap_time=75.0)
        laps_path = os.path.join(output_dir, "monaco_2023_ver_laps.csv")
        laps_df.to_csv(laps_path, index=False)
        print(f"Vueltas guardadas en: {laps_path} ({len(laps_df)} vueltas válidas)\n")

        print("Obteniendo y sincronizando telemetría...")
        telemetry_df = self.get_full_session_telemetry(laps_df)
        telemetry_path = os.path.join(output_dir, "monaco_2023_ver_telemetry.csv")
        telemetry_df.to_csv(telemetry_path, index=False)
        print(f"\nTelemetría total guardada en: {telemetry_path}")

if __name__ == "__main__":
    extractor = F1DataExtractor()
    extractor.export_to_csv()