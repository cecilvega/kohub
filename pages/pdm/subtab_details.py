import plotly.express as px
import streamlit as st
import polars as pl
from data_science_tools.config import Config
from data_science_tools.inference.dl_predict import predict_rul
import shap
from data_science_tools.preprocessing import *
from data_science_tools.models.feature_inspector import *
import matplotlib.pyplot as plt


class PdMDetailsTab:
    def __init__(self, subtab, machine_options, failure_filter, ds, theme):
        self.subtab = subtab
        self.machine_options = machine_options
        self.ds = ds
        self.df_breakdowns = ds.df_breakdowns.filter(pl.col("breakdown").is_in(failure_filter)).sort("equipment")
        self.theme = theme

    def get_machine_filter(self):
        machine_filter = st.selectbox(
            "Focus on a particular Machine",
            self.machine_options,
            format_func=lambda x: self.df_breakdowns.to_pandas().set_index("machine_id")["equipment"].to_dict()[x],
            key="single_machine_options",
            index=0,
        )
        return machine_filter

    def plot_feature_importance(self, machine_filter):
        df = self.ds.mutate()
        df = df.filter(pl.col("machine_id") == machine_filter).sort("metric_datetime")
        df = df.pipe(preprocess)
        clf = CLF()
        clf.load_model()
        X = df.tail(30).pipe(get_dataset)[0]
        explainer = shap.Explainer(clf.model, X)
        shap_values = explainer(X)

        # Plot the summary plot
        # st.set_option("deprecation.showPyplotGlobalUse", False)
        plt.figure(figsize=(2.5, 2.5), dpi=600)
        shap.plots.beeswarm(shap_values, max_display=20, show=False)
        st.pyplot(plt.gcf())

    def __call__(self, df, df_usage, df_rul):
        with self.subtab:
            machine_filter = self.get_machine_filter()
            df_machine = self.ds.df_machines.filter(pl.col("machine_id") == machine_filter)
            site_name, equipment = df_machine["site_name"][0], df_machine["equipment"][0]

            st.write("You selected:", f"equipment {equipment} of {site_name}")

            c1, c2 = st.columns(2)

            st.subheader("RUL")
            with c1:
                df_rul_plot = df_rul.loc[df_rul["machine_id"] == machine_filter].sort_values(["metric_datetime"])
                fig = px.line(
                    df_rul_plot,
                    x="metric_datetime",
                    y="rul_pred",
                    # color="rul_pred",
                    # color="equipment",
                    # custom_data=["equipment"],
                    title=f"RUL {site_name}, {equipment} ({df_rul_plot['rul_pred'][-5:].mean():.0f} hours)",
                )
                fig.update_layout(legend_title=None, xaxis_title=None, yaxis_title="RUL", hovermode="x unified")
                fig.update_traces(hovertemplate="%{customdata}: %{y:,.0f}<extra></extra>")
                st.plotly_chart(fig, use_container_width=True, theme=self.theme)
            # fig = px.line(
            #     df_usage.to_pandas(),
            #     x="usage_date",
            #     y="rul",
            #     color="asset_id",
            #     custom_data=["machine_id"],
            #     title="RUL by failed machine",
            #     log_y=True,
            # )
            # fig.update_layout(legend_title=None, xaxis_title=None, yaxis_title="Horas", hovermode="x unified")
            # fig.update_traces(hovertemplate="%{customdata}: %{y:,.0f}<extra></extra>")
            # st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)

            with c2:
                self.plot_feature_importance(machine_filter)

            st.subheader("Variables Over Time")

            c1, c2 = st.columns((1, 3))

            with c1:
                features = Config().features
                source_filter = st.selectbox(
                    "**Select your desired columns:**",
                    options=list(features.keys()),
                    key="machine_source_options",
                )
                feature_filter = st.selectbox(
                    "**Select your desired columns:**",
                    options=list(features[source_filter].keys()),
                    key="machine_feature_options",
                )
            with c2:
                fig = px.line(
                    df.filter(pl.col("machine_id").is_in([machine_filter])).to_pandas(),
                    x="metric_datetime",
                    y=feature_filter,
                    # color=plot_colour,
                    title="Time Series Plot",
                )
                fig.update_layout(legend_title=None, xaxis_title=None, yaxis_title=feature_filter)
                st.plotly_chart(fig, use_container_width=True, theme=self.theme)

            fig = px.scatter(
                df_usage.filter(pl.col("machine_id").is_in([machine_filter])).to_pandas(),
                x="usage_date",
                y="smr",
                # color="asset_id",
                custom_data=["equipment"],
                title="SMR",
            )
            fig.update_layout(legend_title=None, xaxis_title=None, yaxis_title="Horas", hovermode="x unified")
            fig.update_traces(hovertemplate="%{customdata}: %{y:,.0f}<extra></extra>")
            st.plotly_chart(fig, use_container_width=True, theme=self.theme)
