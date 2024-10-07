from common import *
import plotly.express as px
import streamlit as st
import pandas as pd

styler()


# Load and process the data
@st.cache_data
def load_and_process_data():
    df = pd.read_csv("DATA/indisponibilidad_mensual.csv")
    df["Date"] = pd.to_datetime(df["Date"])

    return df


# Load the data
data = load_and_process_data()


# Create a function to style the dataframe
def style_dataframe(df):
    df = df.groupby(["sistema", "modo_falla"]).agg({"indisponibilidad": "sum", "frecuencia": "sum"}).reset_index()

    # Sort the data
    df = df.sort_values(["sistema", "indisponibilidad"], ascending=[True, False])

    # Combine the data
    df = df.sort_values(["sistema", "indisponibilidad"], ascending=[True, False])

    def highlight_total(val):
        return "font-weight: bold" if val == "Total" else ""

    def color_scale_indisponibilidad(val):
        return f"background-color: rgba(0, 0, 255, {val/max(df['indisponibilidad'])})"

    def color_scale_frecuencia(val):
        return f"background-color: rgba(255, 165, 0, {val/max(df['frecuencia'])})"  # Orange color

    styled = (
        df.style.applymap(highlight_total, subset=["modo_falla"])
        .applymap(color_scale_indisponibilidad, subset=["indisponibilidad"])
        .applymap(color_scale_frecuencia, subset=["frecuencia"])
        .format({"indisponibilidad": "{:.2f}", "frecuencia": "{:.0f}"})
        .set_properties(**{"text-align": "left"})
        .set_table_styles(
            [
                {"selector": "th", "props": [("font-weight", "bold"), ("text-align", "left")]},
                {"selector": "td", "props": [("text-align", "left")]},
                {"selector": "", "props": [("border", "1px solid #ddd"), ("font-family", "Arial, sans-serif")]},
                {"selector": "thead", "props": [("background-color", "#f2f2f2")]},
            ]
        )
    )
    return styled


# Display the table
# st.title("Tendencia Estiba por Pala y Operador")
st.dataframe(style_dataframe(data), use_container_width=True, hide_index=True)


sistemas = data["sistema"].unique()
sistemas_filter = st.sidebar.selectbox("Seleccionar de sistema:", sistemas)


# Prepare data for streamgraph
pivot_data = (
    data.loc[(data["sistema"] == sistemas_filter)]
    .pivot_table(values="frecuencia", index="Date", columns="modo_falla", aggfunc="sum")
    .fillna(0)
)


pivot_data = pivot_data.reset_index()
fig = px.line(
    pivot_data,
    x=pivot_data.Date,
    y=pivot_data.columns,
    hover_data={"Date": "|%B %d, %Y"},
    title="Tendencia Frecuencia por sistema y modo falla",
)
fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
# Display the streamgraph
st.plotly_chart(fig, use_container_width=True)


###
# Prepare data for streamgraph
pivot_data = (
    data.loc[(data["sistema"] == sistemas_filter)]
    .pivot_table(values="indisponibilidad", index="Date", columns="modo_falla", aggfunc="sum")
    .fillna(0)
)
import plotly.express as px


pivot_data = pivot_data.reset_index()
fig = px.line(
    pivot_data,
    x=pivot_data.Date,
    y=pivot_data.columns,
    hover_data={"Date": "|%B %d, %Y"},
    title="Tendencia Indisponibilidad por sistema y modo falla",
)
fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
# Display the streamgraph
st.plotly_chart(fig, use_container_width=True)


# options_display = {
#     "blower": "Blower",
#     "cilindro_direccion": "Cilindro de Dirección",
#     "suspension_trasera": "Suspensión Trasera",
#     "conjunto_masa_suspension": "Conjunto Masa Suspensión",
#     "motor_traccion": "Motor de Tracción",
#     "cilindro_levante": "Cilindro de Levante",
#     "modulo_potencia": "Módulo de Potencia",
# }
#
# # Create the selectbox using the dictionary
# component = st.sidebar.selectbox(
#     "Selección de Componente",
#     options=list(options_display.keys()),
#     format_func=lambda x: options_display[x],
#     index=6,
# )
#
#
# def read_standard_overhauls():
#     df = pd.read_excel("DATA/standard_overhaul_costs.xlsx")[
#         [
#             "prorrata_year",
#             "component",
#             "subcomponent",
#             "standard_overhaul_cost",
#             "mtbo_100_pct",
#         ]
#     ]
#     return df
#
#
# @st.cache_data(ttl=timedelta(hours=1))
# def fetch_and_clean_cc_data():
#     cc_df = read_cc()
#
#     standard_overhauls_df = read_standard_overhauls()
#     df = enrich_cc(cc_df, standard_overhauls_df)
#     return df
#
#
# df = fetch_and_clean_cc_data()
# df = df.loc[df["component"] == component].reset_index(drop=True)
# st.dataframe(df, use_container_width=True)
