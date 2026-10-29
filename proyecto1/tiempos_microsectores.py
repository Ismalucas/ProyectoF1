import pandas as pd

telemetry = pd.read_csv(
    "C:/Users/UNI/Desktop/Master/GitHub/ProyectoF1/data/monaco_2023_ver_telemetry_tagged.csv"
)

print(telemetry.columns.tolist())

print(
    telemetry["point_type"]
    .value_counts()
)

print(telemetry["date_dt"].head())
print(telemetry["date_dt"].dtype)


# =====================================
# Cargar datos
# =====================================

telemetry["date_dt"] = pd.to_datetime(
    telemetry["date_dt"],
    utc=True,
    errors="coerce"
)
telemetry = telemetry.sort_values(
    ["driver_number", "lap_number", "date_dt"]
)

# =====================================
# Construcción de microsectores
# =====================================

rows = []

for (driver, lap), df in telemetry.groupby(
    ["driver_number", "lap_number"]
):

    df = df.sort_values("date_dt")

    markers = df[
        df["point_type"].isin(
            ["Inicio", "Microsector", "Sector", "Fin"]
        )
    ].copy()

    markers = markers.reset_index()

    microsector_id = 1
    sector_id = 1

    for i in range(len(markers) - 1):

        start_idx = markers.loc[i, "index"]
        end_idx = markers.loc[i + 1, "index"]

        start_time = markers.loc[i, "date_dt"]
        end_time = markers.loc[i + 1, "date_dt"]

        segment = df.loc[start_idx:end_idx]

        duration = (
            end_time - start_time
        ).total_seconds()

        avg_speed = segment["speed"].mean()

        rows.append(
            {
                "driver_number": driver,
                "lap_number": lap,
                "sector": sector_id,
                "microsector": microsector_id,
                "segment_time": duration,
                "avg_speed": avg_speed,
                "date_start": start_time,
                "date_end": end_time,
                "start_type": markers.loc[i, "point_type"],
                "end_type": markers.loc[i + 1, "point_type"]
            }
        )

        microsector_id += 1

        if markers.loc[i + 1, "point_type"] == "Sector":
            sector_id += 1

# =====================================
# Resultado
# =====================================

microsectors = pd.DataFrame(rows)

print(microsectors.head())

microsectors.to_csv(
    "data/microsector_times.csv",
    index=False
)


# =====================
# Sectores
# =====================

sectors = (
    microsectors
    .groupby(
        ["driver_number", "lap_number", "sector"],
        as_index=False
    )
    .agg(
        sector_time=("segment_time", "sum"),
        avg_speed=("avg_speed", "mean"),
        date_start=("date_start", "min"),
        date_end=("date_end", "max")
    )
)

# =====================
# Vueltas
# =====================

laps = (
    microsectors
    .groupby(
        ["driver_number", "lap_number"],
        as_index=False
    )
    .agg(
        lap_time=("segment_time", "sum"),
        avg_speed=("avg_speed", "mean"),
        date_start=("date_start", "min"),
        date_end=("date_end", "max")
    )
)

# =====================
# Guardar
# =====================

sectors.to_csv(
    "data/sector_times.csv",
    index=False
)

laps.to_csv(
    "data/lap_times_reconstructed.csv",
    index=False
)

laps.sort_values("lap_time").head(20)

microsectors.groupby(
    ["driver_number", "lap_number"]
).size().describe()

microsectors.groupby(
    ["driver_number", "lap_number"]
).size().value_counts()

laps[
    laps["driver_number"] == 77
].sort_values("lap_time")

microsectors[
    (microsectors["driver_number"] == 1)
    &
    (microsectors["lap_number"] == 17)
]

driver = 77
lap = 18

markers = df[
    df["point_type"].isin(
        ["Inicio","Microsector","Sector","Fin"]
    )
]

print(
    markers[
        ["date_dt","point_type"]
    ]
)

microsectors.groupby(
    ["driver_number", "lap_number"]
)["microsector"].nunique()