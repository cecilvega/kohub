import pandas as pd
import streamlit as st
from pathlib import Path
from common import *
from utils import *
import os
import sys
import plotly.express as px
from plotly import graph_objects as go
import numpy as np
import calendar

st.set_page_config(page_title="DevOps", page_icon=":bar_chart:", layout="wide")
styler()


st.metric(label="Temperature", value="70 °F", delta="1.2 °F")

with st.expander("Report month"):
    this_year = datetime.now().year
    this_month = datetime.now().month
    report_year = st.selectbox("", range(this_year, this_year - 5, -1))
    month_abbr = calendar.month_abbr[1:]
    report_month_str = st.radio("", month_abbr, index=this_month - 1, horizontal=True)
    report_month = month_abbr.index(report_month_str) + 1
st.text(f"{report_year} {report_month_str}")
# Fake data
adherencia_3d = 35
desempeno_supervisores = 50
desempeno_tecnicos = 88

sin_3d_no_vigente = 67
vigente_no = 36
competente = 15
col = 2


# Title
st.title("Dashboard 3D")


# Create columns
col1, col2 = st.columns(2)


# Function to create donut chart
def create_donut_chart(value, title, color):
    fig = go.Figure(go.Pie(labels=["", title], values=[100 - value, value], hole=0.7, marker_colors=["#f0f0f0", color]))
    fig.update_layout(
        annotations=[dict(text=f"{value}%", x=0.5, y=0.5, font_size=20, showarrow=False)],
        showlegend=False,
        width=300,
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig


# Adherencia 3D
with col1:
    st.subheader("Adherencia 3D")
    st.plotly_chart(create_donut_chart(adherencia_3d, "Adherencia 3D", "#4169E1"), use_container_width=True)

# Desempeño 3D
with col2:
    st.subheader("Desempeño 3D")
    subcol1, subcol2 = st.columns(2)
    with subcol1:
        st.markdown("**Supervisores**")
        st.plotly_chart(create_donut_chart(desempeno_supervisores, "Desempeño 3D", "#8A2BE2"), use_container_width=True)
    with subcol2:
        st.markdown("**Técnicos**")
        st.plotly_chart(create_donut_chart(desempeno_tecnicos, "Desempeño 3D", "#8A2BE2"), use_container_width=True)

# Bar chart
st.subheader("Desglose de Desempeño")
fig_bar = go.Figure(
    go.Bar(
        x=["Sin 3D / No Vigente", "Vigente / No", "COMPETENTE", "COL"],
        y=[sin_3d_no_vigente, vigente_no, competente, col],
        marker_color=["red", "green", "blue", "orange"],
    )
)
fig_bar.update_layout(xaxis_title="Categoría", yaxis_title="Porcentaje", height=400)
st.plotly_chart(fig_bar, use_container_width=True)

# Add text below the charts
st.markdown(
    """
    <style>
    .small-font {
        font-size:10px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="small-font">Adherencia: mide el % de personas con diagnóstico Vigente y excluidos (No Aplica 3D), con respecto al total del contrato</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="small-font">Desempeño: Mide el % de resultados Competentes, en comparación con el total de personas que deben ser evaluadas según su perfil</p>',
    unsafe_allow_html=True,
)


# @st.experimental_memo
# def get_chart_26647117():
#     import plotly.express as px
#
#     df = px.data.gapminder().query("country == 'Canada'")
#     fig = px.bar(df, x='year', y='pop',
#                  hover_data=['lifeExp', 'gdpPercap'], color='lifeExp',
#                  labels={'pop':'population of Canada'}, height=400)
#
#     tab1, tab2 = st.tabs(["Streamlit theme (default)", "Plotly native theme"])
#     with tab1:
#         st.plotly_chart(fig, theme="streamlit")
#     with tab2:
#         st.plotly_chart(fig, theme=None)
#
# get_chart_26647117()


# Generate fake data
np.random.seed(42)
dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
actual_values = np.random.normal(100, 15, len(dates))
predicted_values = actual_values + np.random.normal(0, 10, len(dates))
error = predicted_values - actual_values

df = pd.DataFrame({"Date": dates, "Actual": actual_values, "Predicted": predicted_values, "Error": error})

# Title
st.title("Data Comparison and Error Analysis Dashboard")

# Create columns
col1, col2 = st.columns(2)


# Function to create gauge chart
def create_gauge_chart(value, title, min_val, max_val):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": title},
            gauge={
                "axis": {"range": [min_val, max_val]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [min_val, (max_val - min_val) / 3], "color": "lightgray"},
                    {"range": [(max_val - min_val) / 3, 2 * (max_val - min_val) / 3], "color": "gray"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": (max_val - min_val) * 0.8,
                },
            },
        )
    )
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
    return fig


# Metrics in gauges
with col1:
    st.subheader("Key Metrics")
    mean_error = df["Error"].mean()
    st.plotly_chart(
        create_gauge_chart(mean_error, "Mean Error", df["Error"].min(), df["Error"].max()), use_container_width=True
    )
