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
from pages.planification.utils.vis_px_timeline import plot_pool_px_timeline
from pages.planification.utils.vis_timeline import plot_pool_timeline, plot_component_arrival_timeline
from pages.planification.utils.preprocessing import modify_dataframe
from datetime import datetime, date, timedelta


# st.set_page_config(page_title="DevOps", page_icon=":bar_chart:", layout="wide")
styler()

current_date = datetime.now().date()

available_components = [
    "blower",
    "cilindro_direccion",
    "motor_traccion",
    "suspension_trasera",
    "conjunto_masa_suspension",
    "cilindro_levante",
    "modulo_potencia",
]


@st.cache_data(ttl=timedelta(hours=1))
def fetch_and_clean_data():
    cc_df = read_cc()
    pool_proj_df = read_base_pool_proj()
    arrivals_df = read_component_arrivals()
    allocation = ComponentAllocation(cc_df, pool_proj_df, arrivals_df)
    df = allocation.generate_pool_projection()
    return df


df = fetch_and_clean_data()

# Drop missing components
df = df.dropna(subset=["arrival_date"]).reset_index(drop=True)

options_display = {
    "blower_parilla": "Blower Parrilla",
    "cilindro_direccion": "Cilindro de Dirección",
    "suspension_trasera": "Suspensión Trasera",
    "conjunto_masa_suspension_delantera": "Conjunto Masa Suspensión Delantera",
    "motor_traccion": "Motor de Tracción",
    "cilindro_levante": "Cilindro de Levante",
    "modulo_potencia": "Módulo de Potencia",
}

# Create the selectbox using the dictionary
component = st.sidebar.selectbox(
    "Selección de Componente",
    options=list(options_display.keys()),
    format_func=lambda x: options_display[x],
    index=6,
)


st.title("Proyección de entrega")

st.write("Al hacer click sobre la leyenda, permite remover o activar si se desea ver cierto estado.")

comp_df = df.loc[df["component"] == component].reset_index(drop=True)

# Date slider
min_date = comp_df["changeout_date"].min().date()
max_date = comp_df["arrival_date"].max().date()
# Filter and sort data
today = datetime.now()
jan_1 = date(today.year, 1, 1)
dec_31 = date(today.year, 12, 31)

comp_df = modify_dataframe(comp_df)
pool_slots = comp_df["pool_slot"].drop_duplicates().to_list()


def colorize_multiselect_options(colors: list[str]) -> None:
    rules = ""
    n_colors = len(colors)

    for i, color in enumerate(colors):

        rules += f""".stMultiSelect div[data-baseweb="select"] span[data-baseweb="tag"]:nth-child({n_colors}n+{i+1}){{background-color: {color};}}"""

    st.markdown(f"<style>{rules}</style>", unsafe_allow_html=True)


pool_slots_filter = st.sidebar.multiselect(
    "Seleccionar de asignaciones del pool:", pool_slots, pool_slots, placeholder="hola"
)


st.sidebar.write("Permite filtrar que lineas del pool se desean visualizar.")

d = st.sidebar.date_input(
    "Seleccionar fecha:",
    (jan_1, max_date),
    min_date,
    max_date,
    format="MM.DD.YYYY",
)

colors = (
    comp_df.sort_values(["pool_slot", "arrival_date"])
    .drop_duplicates(subset=["pool_slot"], keep="last")["pool_changeout_type"]
    .map(lambda x: {"I": "#0079ec", "P": "#140a9a", "E": "#a5abaf", "R": "#ffc82f"}[x])
)
plot_df = comp_df.loc[
    (comp_df["pool_slot"].isin(pool_slots_filter)) & (comp_df["arrival_date"].dt.date.between(d[0], d[1]))
]

## Number of colors does not need to match the number of options
colorize_multiselect_options(colors)

fig = plot_pool_px_timeline(plot_df)

st.plotly_chart(fig, use_container_width=True)


st.title("Entregas confirmadas")

filtered_df = df[df["arrival_date"].dt.date > current_date].sort_values(
    ["pool_slot", "arrival_date"], ascending=[True, False]
)
# Use drop_duplicates to keep only the first occurrence for each pool_number
filtered_df = filtered_df.drop_duplicates(subset="pool_slot", keep="first")
filtered_df = filtered_df.sort_values("arrival_date").reset_index(drop=True).head(4)
# Display upcoming arrivals using columns and metrics

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

timeline = plot_component_arrival_timeline(df)
