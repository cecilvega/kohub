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
from azure.storage.blob import BlobServiceClient
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="DevOps", page_icon=":bar_chart:", layout="wide")
styler()

# st.metric(label="Temperature", value="70 °F", delta="1.2 °F")


with st.expander("Report month"):
    this_year = datetime.now().year
    this_month = max(datetime.now().month - 1, 1)
    report_year = st.selectbox("", range(this_year, this_year - 5, -1))
    month_abbr = calendar.month_abbr[1:]
    report_month_str = st.radio("", month_abbr, index=this_month - 1, horizontal=True)
    report_month = month_abbr.index(report_month_str) + 1
st.text(f"{report_year} {report_month_str}")
partition_date = datetime.strptime(f"{report_year} {report_month_str}", "%Y %b").strftime("y=%Y/m=%m")
st.text(partition_date)

# blob_service_client = BlobServiceClient(
#     account_url=os.environ["AZURE_ACCOUNT_URL"],
#     credential=os.environ["AZURE_SAS_TOKEN"],
# )
#
# container_client = blob_service_client.get_container_client(os.environ["AZURE_CONTAINER_NAME"])
# blob_list = container_client.list_blobs(name_starts_with=f"{os.environ['AZURE_PREFIX']}/HSEC/{partition_date}")
# blob_list = [f.name for f in blob_list]
# assert blob_list.__len__() <= 1, "There should be only one file per month"
# file = blob_list[0]
#
# blob_client = blob_service_client.get_blob_client(
#     container=os.environ["AZURE_CONTAINER_NAME"],
#     blob=file,
# )
# blob_data = blob_client.download_blob()
# blob_data = BytesIO(blob_data.readall())
# df = pd.read_excel(blob_data)

adherencia_df = pd.read_excel(
    "/home/cecilvega/Downloads/KOMATSU CHILE S A_Detalle Cumplimiento Empresa Programa FLP_Julio 2024.xlsx",
    skiprows=7,
    sheet_name="3D",
    usecols="B:K",
)

desempeno_df = (
    pd.read_excel(
        "/home/cecilvega/Downloads/KOMATSU CHILE S A_Detalle Cumplimiento Empresa Programa FLP_Julio 2024.xlsx",
        skiprows=7,
        sheet_name="3D",
        usecols="M:V",
    )
    .rename(columns={"Rut/Passport.1": "Rut/Passport"})
    .drop(columns=["Nombre.1", "Nombre Empleador.1", "SAP Empleador.1", "Contratista o Subcontratista?.1"])
    .dropna(subset=["Rut/Passport"])
)

# df = pd.merge(adherencia_df, desempeno_df, on="Rut/Passport", how="outer").reset_index(drop=True)


# adherencia_df = df.loc[df["Estado Informe Final 3D"].isin(["VIGENTE", "NO APLICA 3D"])]

total_contrato = adherencia_df.__len__()
st.write(adherencia_df.__len__())

adherencia_3d = round(
    adherencia_df.loc[adherencia_df["Estado Informe Final"].isin(["VIGENTE", "NO APLICA 3D"])].__len__()
    / total_contrato
    * 100,
    1,
)


# Fake data
supervisor_df = desempeno_df.loc[desempeno_df["Perfil 3D"] == "SUPERVISOR"]
desempeno_supervisores = (
    supervisor_df.loc[supervisor_df["Resultado Final"] == "COMPETENTE"].__len__() / supervisor_df.__len__() * 100
)
tecnico_df = desempeno_df.loc[desempeno_df["Perfil 3D"] == "TÉCNICO"]
desempeno_tecnicos = (
    tecnico_df.loc[tecnico_df["Resultado Final"] == "COMPETENTE"].__len__() / tecnico_df.__len__() * 100
)

sin_3d_no_vigente = 67
vigente_no = 36
competente = 15
col = 2


# Title
st.title("Dashboard 3D")


# Create columns
col1, col2 = st.columns((1, 2))


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
    fig_bar = go.Figure(
        go.Bar(
            x=["Sin 3D / No Vigente", "Vigente / No"],
            y=[total_contrato - adherencia_3d, adherencia_df.__len__()],
            marker_color=["red", "green"],
        )
    )
    st.plotly_chart(fig_bar, use_container_width=True)
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
    barplot_df = (
        df.loc[(df["Categoría Final 3D"] != "PENDIENTE")]
        .groupby("Categoría Final 3D")[["Nombre Colaborador"]]
        .count()
        .reset_index()
        .rename(columns={"Nombre Colaborador": "count"})
    )
    fig = px.bar(barplot_df, x="Categoría Final 3D", y="count")  # , title="Wide-Form Input"
    st.plotly_chart(fig, use_container_width=True)

    # st.dataframe(
    #     df.loc[(df["Perfil 3D"] == "SUPERVISOR") & (df["Categoría Final 3D"] != "PENDIENTE")]
    #     .groupby("Categoría Final 3D")[["Nombre Colaborador"]]
    #     .count()
    # )


st.dataframe(df.head(3))


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


# # Metrics in gauges
# with col1:
#     st.subheader("Key Metrics")
#     mean_error = df["Error"].mean()
#     st.plotly_chart(
#         create_gauge_chart(mean_error, "Mean Error", df["Error"].min(), df["Error"].max()), use_container_width=True
#     )
