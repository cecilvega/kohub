# Libraries
import os
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from common import *
from utils import *
from datetime import datetime, time, date, timedelta

import pandas as pd

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parents[2] / "dags"))
from data_science_tools.config import Config
import resources.tidypolars as tp
import polars as pl
from operations.assets.lr.transmute import *

st.set_page_config(page_title="Komtrax 2", page_icon=":bar_chart:", layout="wide")

styler()

st.title("KomtraxPlus LoggerData")
c1, c2 = st.columns([1, 2])
with c1:
    # with st.sidebar.expander("Filtros Equipos"):
    site_filters = select_site_filters()
with c2:
    machine_filters = select_machine_options(site_filters)


# df_usage = select_usage(ttf_threshold)
# df_op = select_op()
# df_lr = select_lr()


date_filters = select_date_filters(df_usage)

df = select_fleet_dataset(df_lr, df_usage, df_op)


with st.expander("Files", expanded=False):
    st.write("as")


#
# st.dataframe(df.head(3))
# st.write(df.shape)
subtab_overview, subtab_classifier, subtab_feature_importance = st.tabs(
    ["**Summary**", "**xgboost**", "**Feature Importance**"]
)

with subtab_overview:
    st.subheader("Over Time")
    c1, c2 = st.columns(2)
    features = Config("features")

    with c1:
        source_filter = st.selectbox(
            "**Select your desired columns:**",
            options=list(features.config_yaml.keys()),
            # default="eg1_total",
            key="source_options",
        )
    with c2:
        feature_filter = st.selectbox(
            "**Select your desired columns:**",
            options=[c for c in list(getattr(features, source_filter).keys()) if c in df.columns],
            # default="eg1_total",
            key="feature_options",
        )

    c1, c2 = st.columns(2)

    with c1:
        fig = px.line(
            df,
            x="metric_datetime",
            y=feature_filter,
            color="machine_id",
            title="Daily Transferred Volume",
        )
        fig.update_layout(legend_title=None, xaxis_title=None, yaxis_title="Volume [USD]")
        st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)

    # with c2:
    #     fig = px.line(
    #         df,
    #         x="rul",
    #         y=feature_filter,
    #         color="machine_id",
    #         title="Daily Transferred Volume",
    #     )
    #     fig.update_layout(legend_title=None, xaxis_title=None, yaxis_title="Volume [USD]")
    #     st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)

with subtab_classifier:
    import xgboost as xgb
    from sklearn.metrics import confusion_matrix, f1_score, accuracy_score
    import seaborn as sns
    import matplotlib.pyplot as plt
    import plotly.figure_factory as ff
    from sklearn.metrics import confusion_matrix
    import numpy as np

    st.subheader("xgboost")

    # Function to generate rolling metrics
    def generate_rolling_features(grouped_data, rolling_columns):
        df = grouped_data.copy()
        for col in rolling_columns:
            # Calculate rolling mean and std dev and store in new columns
            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        {
                            f"{col}_rolling_mean_24h": df[col].rolling(window=4).mean(),
                            f"{col}_rolling_std_24h": df[col].rolling(window=10).std(),
                        }
                    ),
                ],
                axis=1,
            )

        return df

    # Apply the function to each group of machine_id

    data = df.to_pandas().sort_values(by=["machine_id", "metric_datetime"]).reset_index(drop=True)
    # List of columns to generate rolling metrics for
    rolling_columns = [c for c in df.columns if c not in ["machine_id", "metric_datetime", "label", "smr", "cluster"]]
    from sklearn.preprocessing import MinMaxScaler

    scaler = MinMaxScaler()
    data[rolling_columns] = scaler.fit_transform(data[rolling_columns].values)

    data = data.groupby("machine_id").apply(lambda x: generate_rolling_features(x, rolling_columns))
    from sklearn.model_selection import train_test_split

    # Fill NaN values with 0 (resulting from rolling calculations)
    data = data.fillna(0)

    val_machine_ids = ["6462b9f31994b09289cd1056"]
    X_val = data.loc[data["machine_id"].isin(val_machine_ids)].drop(columns=["metric_datetime", "machine_id"])
    y_val = X_val["label"]
    X_val = X_val.drop(columns=["label"])
    X = data.loc[~data["machine_id"].isin(val_machine_ids)].drop(columns=["metric_datetime", "machine_id"])
    y = X["label"]
    # Split data into features and target
    X = X.drop(columns=["label"])

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    st.write(X_train.shape, X_test.shape, X_val.shape)

    # Initialize the XGBoost classifier
    clf = xgb.XGBClassifier(objective="binary:logistic", eval_metric="logloss")

    # Train the classifier
    clf.fit(X_train, y_train)

    # Predict on the test set
    y_pred = clf.predict(X_test)

    # Calculate the F1 score
    f1 = f1_score(y_test, y_pred)
    st.write(f1)

    # Compute the confusion matrix
    import plotly.figure_factory as ff

    z = confusion_matrix(y_test, y_pred)
    # Create labels
    labels = np.unique(y_test + y_pred)
    x = ["Actual No Failure", "Actual Failure"]
    y = ["Predicted No Failure", "Predicted Failure"]

    # change each element of z to type string for annotations
    z_text = [[str(y) for y in x] for x in z]

    # Plot using Plotly
    fig = ff.create_annotated_heatmap(z=z, x=x, y=y)

    fig.update_layout(
        title_text="<i><b>Confusion matrix</b></i>",
    )

    # adjust margins to make room for yaxis title
    fig.update_layout(margin=dict(t=50, l=200))
    # add colorbar
    fig["data"][0]["showscale"] = True
    st.plotly_chart(fig)

    st.subheader("Validation Dataset")
    y_pred_val = clf.predict_proba(X_val)
    # Calculate the F1 score
    # f1 = f1_score(y_val, y_pred_val)

    df_val = pd.concat(
        [
            data.loc[data["machine_id"].isin(val_machine_ids)][["machine_id", "metric_datetime"]].reset_index(
                drop=True
            ),
            pd.DataFrame(y_pred_val - 0.48, columns=["no_failure", "failure"]).assign(label=y_val.to_list()),
        ],
        axis=1,
    )
    fig = px.line(
        df_val,
        x="metric_datetime",
        y="failure",
        color="label",
        title="Probabilidad de falla",
    )
    fig.update_layout(legend_title=None, xaxis_title=None, yaxis_title="Volume [USD]")
    st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)

with subtab_feature_importance:
    import shap

    explainer = shap.Explainer(clf)
    shap_values = explainer(X_test)
    # c1, c2 = st.columns(2)
    # with c1:
    plt.figure(figsize=(2.5, 2.5), dpi=600)
    shap.summary_plot(shap_values, X_test, show=False, plot_type="bar")
    st.pyplot(plt.gcf())
    # with c2:
    plt.figure(figsize=(2.5, 2.5), dpi=600)
    shap.summary_plot(shap_values, X_test, show=False)
    st.pyplot(plt.gcf())

    # Streamlit app
    st.title("SHAP Summary Plot")

    # explain the model's predictions using SHAP
    # (same syntax works for LightGBM, CatBoost, scikit-learn, transformers, Spark, etc.)
    explainer = shap.Explainer(clf)
    shap_values = explainer(X_test)

    # visualize the first prediction's explanation
    plt.figure(figsize=(2.5, 2.5))
    shap.plots.waterfall(shap_values[0])
    st.pyplot(plt.gcf())


# st.subheader("Activity Over Time")
# c1, c2 = st.columns(2)
# features = Config("features")
# with c1:
#     source_filter = st.selectbox(
#         "**Select your desired columns:**",
#         options=list(features.config_yaml.keys()),
#         # default="eg1_total",
#         key="source_options",
#     )
# with c2:
#     feature_filter = st.selectbox(
#         "**Select your desired columns:**",
#         options=list(getattr(features, source_filter).keys()),
#         # default="eg1_total",
#         key="feature_options",
#     )
#
# c1, c2 = st.columns(2)
#
# with c1:
#     fig = px.line(
#         df_op.pipe(_filter_frame, df_usage, date_filters),
#         x="metric_datetime",
#         y=feature_filter,
#         color="asset_id",
#         title="Daily Transferred Volume",
#     )
#     fig.update_layout(legend_title=None, xaxis_title=None, yaxis_title="Volume [USD]")
#     st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)
#
# with c2:
#     fig = px.line(
#         df_op.pipe(_filter_frame, df_usage, date_filters),
#         x="rul",
#         y=feature_filter,
#         color="asset_id",
#         title="Daily Transferred Volume",
#     )
#     fig.update_layout(legend_title=None, xaxis_title=None, yaxis_title="Volume [USD]")
#     st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)
