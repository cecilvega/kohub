import streamlit as st
import pandas as pd
from PIL import Image
import base64


# Function to load an image and convert to base64
def img_to_base64(img_path):
    with open(img_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


# Sample data
data = {
    "Componente": [
        "Blower Parrilla",
        "Cilindro Dirección",
        "Suspensión Trasera",
        "Suspensión Delantera",
        "Motor Tracción",
        "Cilindro Levante",
        "Módulo Potencia",
    ],
    "Imagen": [
        "images/blower.png",
        "images/cilindro_direccion.png",
        "images/suspension_trasera.png",
        "images/suspension_delantera.png",
        "images/motor_traccion.png",
        "images/cilindro_levante.png",
        "images/modulo_potencia.png",
    ],
    "Capacidad del Pool": [2, 5, 2, 4, 1, 1, 1],
    "Entregas Acordadas MEL": [4, 5, 1, 2, 2, 1, 0],
    "Entregas Realizadas": [3, 1, 2, 2, 2, 0, 0],
    "Diferencia Entregas": [-1, -4, 1, 0, 0, -1, 0],
    "NSC MEL": ["75%", "20%", "200%", "100%", "100%", "0%", "(En blanco)"],
    "Entregas v/s capacidad": [1, -4, 0, -2, 1, -1, 0],
    "PMF KCH": ["150%", "19%", "119%", "56%", "200%", "0%", "0%"],
}

df = pd.DataFrame(data)

# Streamlit app
st.set_page_config(layout="wide")

# Title and main image
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    st.image("images/960e.png", width=300)  # Replace with actual image path
with col2:
    st.title("960E Component Performance Dashboard")

# KPI Metrics
col4, col5 = st.columns(2)
with col4:
    st.metric("NSC POOL COMPONENTES", "67%", delta="-28%")
    st.caption("Meta: 95%")
with col5:
    st.metric("PERFORMANCE POOL", "63%", delta="-32%")
    st.caption("Meta: 95%")

# Main table
st.subheader("DETALLE ENTREGA COMPONENTES MEL")
st.markdown(
    """
    <style>
    .dataframe {font-size: 12px !important;}
    </style>
    """,
    unsafe_allow_html=True,
)


# Function to color cells based on conditions
def color_cells(val):
    if isinstance(val, str):
        if "%" in val:
            num = float(val.strip("%"))
            if num >= 100:
                return "background-color: lightgreen"
            elif num < 95:
                return "background-color: lightcoral"
    elif isinstance(val, (int, float)):
        if val > 0:
            return "color: green"
        elif val < 0:
            return "color: red"
    return ""


# Apply styling and display the table
styled_df = df.style.applymap(color_cells)
st.dataframe(styled_df, use_container_width=True)

# Note: You'll need to replace placeholder image paths with actual image paths
# and adjust the data and styling as needed to match your exact requirements.
