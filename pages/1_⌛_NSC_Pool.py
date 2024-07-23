import pandas as pd
import streamlit as st
from pathlib import Path
from common import *
from utils import *
import os
import sys
import plotly.express as px
from plotly import graph_objects as go

st.set_page_config(page_title="DevOps", page_icon=":bar_chart:", layout="wide")
styler()


def plot_pool_timeline(df):
    # Create the Gantt chart
    fig = px.timeline(
        df,
        x_start="cc_date",
        x_end="arrival_date",
        y="pool_number",
        color="pool_type",
        color_discrete_map={"I": "red", "P": "green"},
        height=800,
        title="Cambios Reales Ejecutados",
    )

    fig.update_layout(
        xaxis=dict(
            tickformat="W%V",
            # ticktext=[f'W{date.strftime("%V")}' for date in week_ticks],
            # tickvals=week_ticks,
            # tickmode="array",
            ticklabelmode="period",
            tick0="2024-01-01",
            # tickangle=0,
            showgrid=True,
            ticks="inside",
            ticklabelposition="inside",
            # tickson="boundaries",
            side="bottom",
            # minor=dict(ticks="outside", ticklen=40, dtick="M12"),
            # minor=dict(ticks="outside", ticklen=40, dtick="M12"),
            dtick=7 * 24 * 60 * 60 * 1000,
            gridwidth=2,  # Increase grid line width
            # gridcolor="black",  # Change grid color to black
            # overlaying="x",
            # ticklen=10,
            # minor=dict(ticks="outside", ticklen=40, dtick="M12"),
        ),
        xaxis2=dict(
            tickformat="%b-%y",
            # tickvals=month_centers,
            # ticktext=[date.strftime("%b\n%y") for date in month_ticks],
            ticklabelmode="period",
            # tickmode="array",
            tickangle=0,
            overlaying="x",
            side="bottom",
            showgrid=False,
            # dtick="M1",
            # pad=20,
            # margin=dict(pad=20),
        ),
        yaxis=dict(
            title="Component",
            automargin=True,
            showticklabels=True,
            tickmode="array",
            # tickson="boundaries",
            tickvals=df["pool_number"].unique(),
            ticktext=df["pool_number"].unique(),
            # showgrid=True,
            # gridwidth=2,
            # gridcolor="black",  # Change grid color to black
        ),
        # bargap=0.1,
        plot_bgcolor="white",
    )

    # Add vertical lines for months
    # for date in month_ticks:
    #     fig.add_vline(x=date, line_width=1, line_dash="dash", line_color="lightgray")

    # Add equipment numbers over the bars
    for i, row in df.iterrows():
        fig.add_annotation(
            x=row["cc_date"] + (row["arrival_date"] - row["cc_date"]) / 2,
            y=row["pool_number"],
            text=str(row["equipo"]),
            showarrow=False,
            font=dict(size=10, color="black"),
            bgcolor="white",
            opacity=0.8,
        )

    # Update layout for cleanliness
    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=50),
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title="Tipo de Cambio"),
    )
    start_date = df["cc_date"].min()
    end_date = df["cc_date"].max()
    # Add invisible trace to ensure xaxis2 spans the full range
    fig.add_trace(
        go.Scatter(
            x=[start_date, end_date],
            y=[df["pool_number"].iloc[0]] * 2,
            mode="markers",
            marker_opacity=0,
            showlegend=False,
            xaxis="x2",
            opacity=0,
        )
    )

    # Update traces
    fig.update_traces(marker_line_color="rgb(8,48,107)", marker_line_width=1.5, opacity=0.8)
    return fig


componente = st.selectbox(
    "Selección de Componente",
    options=(
        "Blower",
        "Cilindro Dirección",
        "Suspensión Trasera",
        "CMSD",
        "Motor Tracción",
        "Cilindro Levante",
        "Módulo Potencia",
    ),
)


df = pd.read_csv("pool-consolidated.csv")
df[["cc_date", "arrival_date"]] = df[["cc_date", "arrival_date"]].apply(lambda x: pd.to_datetime(x, format="%Y-%m-%d"))
# st.dataframe(df.head(3))
df = df.loc[df["componente"] == componente].reset_index(drop=True)
df = df.assign(pool_number=df["pool_number"].astype(str))
fig = plot_pool_timeline(df)
st.plotly_chart(fig, use_container_width=True)

# with st.expander("Operations"):
#     fig = plot_gantt_by_tag(select_devops_boards(), "Operations")
#     st.pyplot(fig)
#
# with st.expander("Operations"):
#     fig = plot_gantt_by_tag(select_devops_boards(), "Operations")
#     st.pyplot(fig)


# with st.expander("GETTING STARTED"):

# st.write(
#     """
#     ✨ Streamlit Elements &nbsp; [![GitHub][github_badge]][github_link] [![PyPI][pypi_badge]][pypi_link]
#     =====================
#
#     Create a draggable and resizable dashboard in Streamlit, featuring Material UI widgets,
#     Monaco editor (Visual Studio Code), Nivo charts, and more!
#
#     [github_badge]: https://badgen.net/badge/icon/GitHub?icon=github&color=black&label
#     [github_link]: https://github.com/okld/streamlit-elements
#
#     [pypi_badge]: https://badgen.net/pypi/v/streamlit-elements?icon=pypi&color=black&label
#     [pypi_link]: https://pypi.org/project/streamlit-elements
#     """
# )
#
# with st.expander("GETTING STARTED"):
#     st.write((Path(__file__).parent.parent / "README_3.md").read_text())
