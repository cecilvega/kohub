import pandas as pd
import plotly.express as px
import streamlit as st
import polars as pl
from data_science_tools.config import Config
from data_science_tools.inference.dl_predict import predict_rul


class PdMOverviewTab:
    def __init__(self, subtab, machine_options, failure_filter, ds, theme):
        self.subtab = subtab
        self.machine_options = machine_options
        self.ds = ds
        self.df_breakdowns = ds.df_breakdowns.filter(pl.col("breakdown").is_in(failure_filter)).sort("equipment")
        self.theme = theme

    def plot_data_matrix(self):
        st.subheader("Data Availability")
        features = Config().features

        c1, c2 = st.columns(2)

        with c1:
            source_filter = st.selectbox(
                "**Select your desired columns:**",
                options=list(features.keys()),
                key="source_options",
            )
            data_matrix = self.ds.data_matrix.filter(pl.col("machine_id").is_in(self.machine_options)).to_pandas()

            fig = px.imshow(
                data_matrix.pivot(index="equipment", columns="metric_date", values=source_filter).values,
                x=data_matrix["metric_date"].drop_duplicates().sort_values().to_list(),
                y=data_matrix["equipment"].drop_duplicates().sort_values().to_list(),
                title="Data Avaibility",
                color_continuous_scale="inferno",
                aspect="auto",
            )
            fig.update_layout(
                legend_title=None, xaxis_title=None, yaxis_title=None, coloraxis_colorbar=dict(title="Min/Max")
            )
            fig.update_layout(yaxis={"dtick": 1}, height=800)
            st.plotly_chart(fig, use_container_width=True, theme=self.theme)

    def plot_ranking(self, df_ranking: pd.DataFrame):
        st.subheader("Equipment ranking")
        csv = df_ranking.to_csv(index=False).encode("utf-8")

        st.download_button("Press to Download", csv, "file.csv", "text/csv", key="download-csv")

        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(
                df_ranking.sort_values("rul_pred", ascending=False).reset_index(drop=True),
                x="rul_pred",
                y="equipment",
                color="rul_colour",
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
            st.plotly_chart(fig, use_container_width=True, theme=self.theme)
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
            st.plotly_chart(fig, use_container_width=True, theme=self.theme)

    def __call__(self, df_ranking):
        with self.subtab:
            self.plot_ranking(df_ranking)
            self.plot_data_matrix()
