import streamlit as st
from pathlib import Path
from common import *
import pandas as pd
from PIL import Image
from kverse.assets.pool import *
from pages.komatsu.utils.preprocessing import enrich_cc
from datetime import timedelta

styler()


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
st.dataframe(df, use_container_width=True)
