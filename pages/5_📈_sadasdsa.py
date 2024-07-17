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
from data_science_tools.inference.dl_predict import predict_rul
from data_science_tools.rul_datasets.reader import PdMReader

st.set_page_config(page_title="Wheel Motor", page_icon=":bar_chart:", layout="wide")
styler()

site_filters = select_site_filters()
fill_missing = st.sidebar.toggle("Fill missing data", value=True)
split_filter = st.sidebar.radio(
    "Filter train data",
    options=["val", "test"],
    format_func=lambda x: {"val": "Validation", "test": "Test"}[x],
)


ds = pdm_dataset()

df_breakdowns = ds.df_breakdowns
# if filter_train is not None:
#     df_breakdowns = df_breakdowns.filter(pl.col("train") == filter_train)
st.subheader("Machine Filters")
machine_options = select_machine_options(df_breakdowns, site_filters)

single_machine = st.sidebar.selectbox(
    "Focus on a particular Machine",
    machine_options,
    format_func=lambda x: df_breakdowns.to_pandas().set_index("machine_id")["asset_id"].to_dict()[x],
    key="single_machine_options",
    index=None,
)

machine_filters = [single_machine] if single_machine is not None else machine_options

subtab_inference, subtab_overview = st.tabs(["**Inference**", "**Overview**"])


with subtab_inference:
    c1, c2 = st.columns(2)

    st.subheader("RUL")

    df = predict_rul(ds, split_filter)
    st.dataframe(df.head(3))
    with c1:
        pass
        fig = px.line(
            df,
            x="metric_datetime",
            y="rul_pred",
            color="equipment",
            custom_data=["equipment"],
            title="RUL by failed machine",
            # log_y=True,
        )
        fig.update_layout(legend_title=None, xaxis_title=None, yaxis_title="Horas", hovermode="x unified")
        fig.update_traces(hovertemplate="%{customdata}: %{y:,.0f}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)

    # with c2:
    #     fig = px.line(
    #         df_usage.to_pandas(),
    #         x="usage_date",
    #         y="smr",
    #         color="asset_id",
    #         custom_data=["machine_id"],
    #         title="SMR by machine",
    #         # log_y=True,
    #     )
    #     fig.update_layout(legend_title=None, xaxis_title=None, yaxis_title="Horas", hovermode="x unified")
    #     fig.update_traces(hovertemplate="%{customdata}: %{y:,.0f}<extra></extra>")
    #     st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)


# with subtab_explanation:
#     import shap
#
#     df = ds.mutate()
#     data = df.pipe(preprocess)
#     X_train, y_train = data.query("train").pipe(get_dataset)
#     X_val, y_val = data.query("~train").pipe(get_dataset)
#     clf = CLF()
#     clf.train(X_train, y_train, X_val, y_val)
#
#     data = pd.concat([data, pd.DataFrame({"label_pred": clf.model.predict_proba(X_train)[:, 1]})], axis=1)
#
#     # Initialize the SHAP explainer
#     explainer = shap.Explainer(clf.model)
#
#     # Compute SHAP values for the training data
#     shap_values = explainer.shap_values(X_train)
#
#     # Plot the summary plot
#     st.set_option("deprecation.showPyplotGlobalUse", False)
#
#     shap.summary_plot(shap_values, X_train, show=False)
#     st.pyplot(bbox_inches="tight")
#     # st.pyplot(bbox_inches="tight", dpi=300, pad_inches=0)
#     plt.clf()
#
#     # expectation = explainer.expected_value
#     # import streamlit.components.v1 as components
#
#     # def st_shap(plot, height=None):
#     #     shap_html = f"<head>{shap.getjs()}</head><body>{plot.html()}</body>"
#     #
#     #     components.html(shap_html, height=height)
#     #
#     # st_shap(shap.force_plot(explainer.expected_value, shap_values[0:500], X[0:500]))
#
# # shap.force_plot(
# #     explainer.expected_value,
# #     shap_values[0, :],
# #     X.iloc[0, :],
# #     # figsize=(16, 5),
# # )
