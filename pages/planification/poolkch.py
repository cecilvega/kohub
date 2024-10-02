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
from kverse.assets.pool.blocked_lanes import read_blocked_lanes
from pages.planification.utils.vis_timeline import plot_component_arrival_timeline
from pages.planification.utils.preprocessing import modify_dataframe
from datetime import datetime, date, timedelta


# st.set_page_config(page_title="DevOps", page_icon=":bar_chart:", layout="wide")
styler()

current_date = datetime.now().date()


@st.cache_data(ttl=timedelta(hours=1))
def fetch_arrivals(ttl=timedelta(hours=1)):
    return read_component_arrivals()


@st.cache_data(ttl=timedelta(hours=1))
def fetch_and_clean_data():
    cc_df = read_cc()
    pool_proj_df = read_base_pool_proj()
    arrivals_df = read_component_arrivals()
    blocked_lanes = read_blocked_lanes()
    allocation = ComponentAllocation(cc_df, pool_proj_df, arrivals_df, blocked_lanes)
    df = allocation.generate_pool_projection()
    return df


df = fetch_and_clean_data()
arrivals_df = fetch_arrivals()

# Drop missing components
df = df.dropna(subset=["arrival_date"]).reset_index(drop=True)

options_display = {
    "blower_parrilla": "Blower Parrilla",
    "cilindro_direccion": "Cilindro de Dirección",
    "suspension_trasera": "Suspensión Trasera",
    "suspension_delantera": "Suspensión Delantera",
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


# Filtro especial para ver cuales están confirmados
confirmed_filter = st.sidebar.toggle = st.toggle("Ver Confirmados")

plot_df = comp_df.loc[
    (comp_df["pool_slot"].isin(pool_slots_filter)) & (comp_df["arrival_date"].dt.date.between(d[0], d[1]))
]
# if confirmed_filter:
#
#     plot_df = plot_df.loc[(plot_df["confirmed"] == 1) | (plot_df["confirmed"].isnull())]

## Number of colors does not need to match the number of options
colorize_multiselect_options(colors)

fig = plot_pool_px_timeline(plot_df, by_confirmed=confirmed_filter)

st.plotly_chart(fig, use_container_width=True)


st.title("Entregas confirmadas")


timeline = plot_component_arrival_timeline(arrivals_df)
if timeline:
    st.markdown(f"Fecha llegada: {timeline['start']}<br>Serie Componente: {timeline['group']}", unsafe_allow_html=True)
