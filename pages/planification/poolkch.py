import pandas as pd
import streamlit as st
from pathlib import Path
from common import *
from utils import *
import os
import sys
import plotly.express as px
from plotly import graph_objects as go
from azure.storage.blob import BlobServiceClient
from io import BytesIO
from kverse.assets.pool import *
from pages.planification.utils.visualizations import plot_pool_timeline
from datetime import datetime, date, timedelta


# st.set_page_config(page_title="DevOps", page_icon=":bar_chart:", layout="wide")
styler()

available_components = ["bp", "cd", "mt", "st", "cms", "cl", "mp"]


st.markdown(
    """
## Estado de los Componentes

| Componente | Estado | 
|------------|--------|
| Blower | 🔜 Próximamente |
| Cilindro Dirección | 🔜 Próximamente |
| Suspensión Trasera | 🔜 Próximamente |
| CMSD | 🔜 Próximamente |
| Motor Tracción | 🔜 Próximamente |
| Cilindro Levante | 🔜 Próximamente |
| Módulo Potencia | ✅ Funcionando |
---

"""
)


@st.cache_data(ttl=timedelta(hours=1))
def fetch_and_clean_data():
    cc_df = read_cc()
    pool_proj_df = read_base_pool_proj()
    arrivals_df = read_pool_component_arrivals()
    allocation = ComponentAllocation(cc_df, pool_proj_df, arrivals_df)
    df = allocation.generate_pool_projection()
    return df


df = fetch_and_clean_data()

# Drop missing components
df = df.dropna(subset=["arrival_date"]).reset_index(drop=True)

componente = st.selectbox(
    "Selección de Componente",
    options=(
        "Blower",
        "Cilindro Dirección",
        "Suspensión Trasera",
        "CMSD",
        "Motor Tracción",
        "Cilindro Levante",
        "Módulo Potencia",
    ),
    index=6,
)

df = df.loc[df["componente"] == componente].reset_index(drop=True)
# df = df.assign(pool_slot=df["pool_slot"].astype(str))

# df['reversed_slot'] = df['pool_slot'].max() - df['pool_slot'] + 1
# Date slider
min_date = df["changeout_date"].min().date()
max_date = df["arrival_date"].max().date()
current_date = datetime.now().date()
# Filter and sort data
filtered_df = df[df["arrival_date"].dt.date > current_date].sort_values(
    ["pool_slot", "arrival_date"], ascending=[True, False]
)
# Use drop_duplicates to keep only the first occurrence for each pool_number
filtered_df = filtered_df.drop_duplicates(subset="pool_slot", keep="first")
filtered_df = filtered_df.sort_values("arrival_date").reset_index(drop=True)
# Display upcoming arrivals using columns and metrics
st.subheader("Próximas llegadas de componente")
if not filtered_df.empty:
    columns = st.columns(4)
    for i, (_, row) in enumerate(filtered_df.iterrows()):
        with columns[i % 4]:
            days_until_arrival = (row["arrival_date"].date() - current_date).days
            if row["pool_changeout_type"] == "E":
                days_until_arrival = "?"
                row["arrival_week"] = "?"
            # repair_days = row["ohv_normal"] if row["pool_type"] == "P" else row["ohv_unplanned"]
            # repair_color = "normal" if row["pool_type"] == "P" else "inverse"

            st.metric(
                label=f"Equipo {row['equipo']}",
                value=f"{days_until_arrival} días restantes",
                # delta=f"{repair_days} days repair",
                # delta_color=repair_color,
            )
            st.write(f"Semana estimada de llegada: {row['arrival_week']}")
            st.write(f"Fecha cambio componente: {row['changeout_date'].date()}")
            map_dict = {"I": "Imprevisto", "P": "Planificado", "E": "Esperando"}
            st.write(f"Tipo de cambio: {map_dict[row['pool_changeout_type']]}")
            st.write("---")
else:
    st.write("No upcoming arrivals for the selected date.")


def modify_dataframe(df):
    # Sort the dataframe
    df = df.sort_values(["pool_slot", "changeout_date"])

    # Create new dataframes for overlaps and gaps
    overlaps = []
    gaps = []

    # Iterate through the dataframe
    for i in range(len(df) - 1):
        current_row = df.iloc[i]
        next_row = df.iloc[i + 1]

        # Check for overlaps
        if (
            current_row["pool_slot"] == next_row["pool_slot"]
            and current_row["arrival_date"] > next_row["changeout_date"]
        ):

            overlap_start = next_row["changeout_date"]
            overlap_end = min(current_row["arrival_date"], next_row["arrival_date"])

            overlaps.append(
                {
                    "pool_slot": current_row["pool_slot"],
                    "changeout_date": overlap_start,
                    "arrival_date": overlap_end,
                    "equipo": next_row["equipo"],
                    "component_serial": next_row["component_serial"],
                    "pool_changeout_type": "A",  # A for Ahead of schedule
                    "component_code": current_row["component_code"],
                    "componente": current_row["componente"],
                    "subcomponente": current_row["subcomponente"],
                    "position": current_row["position"],
                }
            )

        # Check for gaps
        if current_row["pool_slot"] == next_row["pool_slot"]:
            gap_start = current_row["arrival_date"]
            gap_end = next_row["changeout_date"]

            if gap_start < gap_end:
                gaps.append(
                    {
                        "pool_slot": current_row["pool_slot"],
                        "changeout_date": gap_start,
                        "arrival_date": gap_end,
                        "pool_changeout_type": "R",  # R for Ready
                        "component_code": current_row["component_code"],
                        "componente": current_row["componente"],
                        "subcomponente": current_row["subcomponente"],
                        "position": current_row["position"],
                    }
                )

    # Create dataframes from the new rows and concatenate with the original
    overlaps_df = pd.DataFrame(overlaps)
    gaps_df = pd.DataFrame(gaps)
    result_df = pd.concat([df, overlaps_df, gaps_df], ignore_index=True)

    # Sort the final dataframe
    result_df = result_df.sort_values(["pool_slot", "changeout_date"])

    # Forward fill component_code, componente, subcomponente, and position
    result_df[["component_code", "componente", "subcomponente", "position"]] = result_df.groupby("pool_slot")[
        ["component_code", "componente", "subcomponente", "position"]
    ].ffill()
    result_df[["changeout_date", "arrival_date"]] = result_df[["changeout_date", "arrival_date"]].apply(
        lambda x: pd.to_datetime(x, format="%Y-%m-%dT00:00:00.000")
    )

    # Generate changeout_week and arrival_week
    result_df["changeout_week"] = result_df["changeout_date"].dt.strftime("%Y-W%V")
    result_df["arrival_week"] = result_df["arrival_date"].dt.strftime("%Y-W%V")
    return result_df


df = modify_dataframe(df)


# TODO: Cambiar a fecha móvil
today = datetime.now()
jan_1 = date(today.year, 1, 1)
dec_31 = date(today.year, 12, 31)

d = st.date_input(
    "Select your vacation for next year",
    (jan_1, max_date),
    min_date,
    max_date,
    format="MM.DD.YYYY",
)

fig = plot_pool_timeline(df.loc[df["arrival_date"].dt.date.between(d[0], d[1])])


st.plotly_chart(fig, use_container_width=True)

# st.dataframe(df.loc[df["component_code"] == "mp"])
