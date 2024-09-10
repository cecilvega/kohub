import streamlit as st
from pathlib import Path
from common import *
import pandas as pd
from PIL import Image
from kverse.assets.pool import *
from pages.komatsu.utils.preprocessing import enrich_cc
from datetime import timedelta

styler()

options_display = {
    "blower": "Blower",
    "cilindro_direccion": "Cilindro de Dirección",
    "suspension_trasera": "Suspensión Trasera",
    "conjunto_masa_suspension": "Conjunto Masa Suspensión",
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


def read_standard_overhauls():
    df = pd.read_excel("DATA/standard_overhaul_costs.xlsx")[
        [
            "prorrata_year",
            "component",
            "subcomponent",
            "standard_overhaul_cost",
            "mtbo_100_pct",
        ]
    ]
    return df


@st.cache_data(ttl=timedelta(hours=1))
def fetch_and_clean_cc_data():
    cc_df = read_cc()

    standard_overhauls_df = read_standard_overhauls()
    df = enrich_cc(cc_df, standard_overhauls_df)
    return df


df = fetch_and_clean_cc_data()
df = df.loc[df["component"] == component].reset_index(drop=True)
st.dataframe(df, use_container_width=True)
