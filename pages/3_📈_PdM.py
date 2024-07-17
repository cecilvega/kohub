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
from data_science_tools.models.feature_inspector import *
from pages.pdm.subtab_details import PdMDetailsTab
from pages.pdm.subtab_overview import PdMOverviewTab
from data_science_tools.inference.dl_predict import predict_rul


st.set_page_config(page_title="Wheel Motor", page_icon=":bar_chart:", layout="wide")
styler()
ds = pdm_dataset()


with st.expander("Machine Filters", expanded=False):
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
        df_breakdowns = ds.df_breakdowns.filter(pl.col("breakdown").is_in(failure_filter)).sort("equipment")

    with c2:
        machine_options = select_machine_options(df_breakdowns, site_filters)

df_usage = ds.df_usage.filter((pl.col("machine_id").is_in(machine_options)))
df = ds.mutate().join(ds.df_breakdowns.select(["machine_id", "asset_id"]), how="left", on="machine_id")

data = (
    ds.mutate()
    .filter(pl.col("machine_id").is_in(machine_options))
    .join(ds.df_breakdowns.select(["machine_id", "asset_id"]), how="left", on="machine_id")
    .pipe(preprocess)
    .reset_index(drop=True)
)
split = {None: None, 1: "val", 0: "test"}[failure_filter[0]]
df_rul = predict_rul(ds, "test").reset_index(drop=True)

df_ranking = (
    df_rul.groupby(by=["equipment"])
    .tail(5)
    .groupby(["equipment"])[["rul_pred", "smr"]]
    .mean()
    .reset_index()
    .assign(rul_pred=lambda x: x["rul_pred"].round(0).astype(int), smr=lambda x: x["smr"].round(0).astype(int))
    .assign(
        rul_colour=lambda x: 1 / np.clip(x["rul_pred"], 0, 10000),
        smr_colour=lambda x: np.clip(x["smr"], 0, 20000),
    )
)


subtab_overview, subtab_details = st.tabs(["**Overview**", "**Details**"])


PdMDetailsTab(
    subtab=subtab_details, machine_options=machine_options, failure_filter=failure_filter, ds=ds, theme=theme_plotly
)(df, df_usage, df_rul)

PdMOverviewTab(
    subtab=subtab_overview, machine_options=machine_options, failure_filter=failure_filter, ds=ds, theme=theme_plotly
)(df_ranking)

# single_machine = st.selectbox(
#     "Focus on a particular Machine",
#     machine_filters,
#     format_func=lambda x: df_breakdowns.to_pandas().set_index("machine_id")["equipment"].to_dict()[x],
#     key="single_machine_options",
#     index=0,
# )


#
# machine_filters = [single_machine] if single_machine is not None else machine_options
# if machine_filters.__len__() == 1:
#     plot_colour = "label"
# else:
#     plot_colour = "asset_id"


# date_filters = select_date_filters(df_usage)


# # Inference
# st.subheader("Prediction")
# fig = px.line(
#     data,
#     x="metric_datetime",
#     y="label_pred",
#     color=plot_colour,
#     title="Time Series Plot",
# )
# fig.update_layout(legend_title=None, xaxis_title=None, yaxis_title="Failure Probability")
# fig.add_shape(
#     type="line",
#     x0=data["metric_datetime"].min(),
#     y0=0.5,
#     x1=data["metric_datetime"].max(),
#     y1=0.5,
#     line=dict(
#         dash="dash",
#         color="Red",
#     ),
#     xref="x",
#     yref="y",
# )
#
# st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)
