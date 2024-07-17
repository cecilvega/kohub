import os
import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

from common import *
from utils import *
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parents[2] / "dags"))
from data_science_tools.config import Config
from data_science_tools.preprocessing import *
from pages.pdm.subtab_details import PdMDetailsTab
from pages.pdm.subtab_overview import PdMOverviewTab

from pdm.reports.vis import *
from pdm.reports.utils import *
import polars as pl
from pdm.assets.core.transmute import *
import numpy as np

st.set_option("deprecation.showPyplotGlobalUse", False)


st.set_page_config(page_title="Wheel Motor", page_icon=":bar_chart:", layout="wide")
styler()
df = pdm_dataset()
df_breakdowns = breakdowns_data()

with st.expander("Filters", expanded=True):
    c1, c2 = st.columns((1, 3))

    st.subheader("RUL")
    with c1:
        site_filters = select_site_filters()
        # filter_failures = st.toggle("Fill missing data", value=None)
        failure_filter = st.radio(
            "Filter train data",
            options=[0, 1, None],
            format_func=lambda x: {0: "Non Failures", 1: "Failures", None: "All"}[x],
            index=0,
        )
        failure_filter = [0, 1] if failure_filter is None else [failure_filter]

        # fill_missing = st.toggle("Fill missing data", value=True)
        df_breakdowns = df_breakdowns.filter(pl.col("breakdown").is_in(failure_filter)).sort("equipment")

    with c2:
        model_options = select_model_filters()
        machine_options = select_machine_options(df_breakdowns, site_filters)

df = df.filter((pl.col("site_name").is_in(site_filters)) & (pl.col("machine_id").is_in(machine_options)))

model = load_model()
df_rul = predict_rul(df, model)
df_ranking = df_rul.pipe(summarise_rul)

# plot_heatmap(data_matrix, "eg")
with st.expander("Ranking", expanded=True):
    c1, c2 = st.columns(2)

    with c1:
        fig = px.bar(
            df_ranking.sort_values("rul_pred", ascending=False).reset_index(drop=True),
            x="rul_pred",
            y="equipment",
            color="rul_pred",
            orientation="h",
            title="<b> Rul by equipment </b>",
            color_continuous_scale="Tealrose",
        )
        fig.update_layout(
            showlegend=False,
            xaxis_title="RUL",
            yaxis_title=None,
            hovermode="x unified",
            # xaxis={"dtick": 1},
        )
        st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)
    with c2:
        fig = px.bar(
            df_ranking.sort_values("smr").reset_index(drop=True),
            x="smr",
            y="equipment",
            color="smr",
            orientation="h",
            title="<b> SMR by equipment </b>",
            color_continuous_scale="Tealrose",
        )
        fig.update_layout(
            showlegend=False,
            xaxis_title="SMR",
            yaxis_title=None,
            hovermode="x unified",
            # xaxis={"dtick": 1},
        )
        st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)
    # with c1:
    #     st.pyplot(plot_ranking(df_ranking))
