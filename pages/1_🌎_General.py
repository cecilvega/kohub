# import os
# import sys
# from pathlib import Path
#
# import plotly.express as px
# import streamlit as st
#
# from common import *
# from utils import *
# import matplotlib.pyplot as plt
#
# sys.path.insert(0, str(Path(os.path.abspath(__file__)).parents[2] / "dags"))
# from data_science_tools.config import Config
# from data_science_tools.preprocessing import *
# from pages.pdm.subtab_details import PdMDetailsTab
# from pages.pdm.subtab_overview import PdMOverviewTab
#
# from pdm.reports.vis import *
# from pdm.reports.utils import *
# import polars as pl
# from pdm.assets.core.transmute import *
#
# st.set_option("deprecation.showPyplotGlobalUse", False)
#
#
# st.set_page_config(page_title="Wheel Motor", page_icon=":bar_chart:", layout="wide")
# styler()
# df = pdm_dataset()
# df_breakdowns = breakdowns_data()
#
# with st.expander("Filters", expanded=True):
#     c1, c2 = st.columns((1, 3))
#
#     st.subheader("RUL")
#     with c1:
#         site_filters = select_site_filters()
#         # filter_failures = st.toggle("Fill missing data", value=None)
#         failure_filter = st.radio(
#             "Filter train data",
#             options=[0, 1, None],
#             format_func=lambda x: {0: "Non Failures", 1: "Failures", None: "All"}[x],
#             index=0,
#         )
#         failure_filter = [0, 1] if failure_filter is None else [failure_filter]
#
#         # fill_missing = st.toggle("Fill missing data", value=True)
#         df_breakdowns = df_breakdowns.filter(pl.col("breakdown").is_in(failure_filter)).sort("equipment")
#
#     with c2:
#         model_options = select_model_filters()
#         # machine_options = select_machine_options(df_breakdowns, site_filters)
#
# df = df.filter(
#     (pl.col("site_name").is_in(site_filters)) & (pl.col("equipment").is_in(df_breakdowns["equipment"].unique()))
# )
#
# model = load_model()
# df_rul = predict_rul(df, model)
# df_ranking = df_rul.pipe(summarise_rul)
#
# # plot_heatmap(data_matrix, "eg")
# with st.expander("Ranking", expanded=True):
#     c1, c2 = st.columns(2)
#     with c1:
#         st.pyplot(plot_ranking(df_ranking))
#
#
# ########################
#
#
# ######
#
# # df_usage = ds.df_usage.filter((pl.col("machine_id").is_in(machine_options)))
# # df = ds.mutate().join(ds.df_breakdowns.select(["machine_id", "asset_id"]), how="left", on="machine_id")
# #
# # data = (
# #     ds.mutate()
# #     .filter(pl.col("machine_id").is_in(machine_options))
# #     .join(ds.df_breakdowns.select(["machine_id", "asset_id"]), how="left", on="machine_id")
# #     .pipe(preprocess)
# #     .reset_index(drop=True)
# # )
# # split = {None: None, 1: "val", 0: "test"}[failure_filter[0]]
# # df_rul = predict_rul(ds, "test").reset_index(drop=True)
# #
# # df_ranking = (
# #     df_rul.groupby(by=["equipment"])
# #     .tail(5)
# #     .groupby(["equipment"])[["rul_pred", "smr"]]
# #     .mean()
# #     .reset_index()
# #     .assign(rul_pred=lambda x: x["rul_pred"].round(0).astype(int), smr=lambda x: x["smr"].round(0).astype(int))
# #     .assign(
# #         rul_colour=lambda x: 1 / np.clip(x["rul_pred"], 0, 10000),
# #         smr_colour=lambda x: np.clip(x["smr"], 0, 20000),
# #     )
# # )
# #
# #
# # subtab_overview, subtab_details = st.tabs(["**Overview**", "**Details**"])
# #
# #
# # PdMDetailsTab(
# #     subtab=subtab_details, machine_options=machine_options, failure_filter=failure_filter, ds=ds, theme=theme_plotly
# # )(df, df_usage, df_rul)
# #
# # PdMOverviewTab(
# #     subtab=subtab_overview, machine_options=machine_options, failure_filter=failure_filter, ds=ds, theme=theme_plotly
# # )(df_ranking)
#
# # %%
