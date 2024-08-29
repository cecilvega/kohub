import pandas as pd
import streamlit as st
from pathlib import Path
from common import *
from utils import *
import os
import sys
import plotly.express as px
from plotly import graph_objects as go
from azure.storage.blob import BlobServiceClient
from io import BytesIO
from kverse.assets.pool import *
from pages.planification.utils.vis_px_timeline import plot_pool_px_timeline
from pages.planification.utils.vis_timeline import plot_pool_timeline, plot_component_arrival_timeline
from pages.planification.utils.preprocessing import modify_dataframe
from datetime import datetime, date, timedelta


# st.set_page_config(page_title="DevOps", page_icon=":bar_chart:", layout="wide")
styler()

available_components = [
    "blower",
    "cilindro_direccion",
    "motor_traccion",
    "suspension_trasera",
    "conjunto_masa_suspension",
    "cilindro_levante",
    "modulo_potencia",
]


st.markdown(
    """
## Estado de los Componentes

Actualización 28 Agosto y 29 Agosto vamos a estar haciendo muchas modificaciones.

| Componente | Estado |
|------------|--------|
| Blower | ✅ Próximamente |
| Cilindro Dirección | ✅ Próximamente |
| Suspensión Trasera | ✅ Próximamente |
| CMSD | ✅ Próximamente |
| Motor Tracción | ✅ Próximamente |
| Cilindro Levante | ✅ Próximamente |
| Módulo Potencia | ✅ Funcionando |
---

"""
)


@st.cache_data(ttl=timedelta(hours=1))
def fetch_and_clean_data():
    cc_df = read_cc()
    pool_proj_df = read_base_pool_proj()
    arrivals_df = read_pool_component_arrivals()
    allocation = ComponentAllocation(cc_df, pool_proj_df, arrivals_df)
    df = allocation.generate_pool_projection()
    return df


df = fetch_and_clean_data()

# Drop missing components
df = df.dropna(subset=["arrival_date"]).reset_index(drop=True)

component = st.selectbox(
    "Selección de Componente",
    options=(
        "blower",
        "cilindro_direccion",
        "suspension_trasera",
        "conjunto_masa_suspension",
        "motor_traccion",
        "cilindro_levante",
        "modulo_potencia",
    ),
    index=6,
)

tab1, tab2 = st.tabs(["📈 Forma 1", "🗃 Forma 2"])

with tab2:

    timeline3 = plot_component_arrival_timeline(df)
    # timeline2 = plot_pool_timeline(df.loc[df["arrival_date"].dt.date.between(d[0], d[1])])

with tab1:

    df = df.loc[df["component"] == component].reset_index(drop=True)
    # df = df.assign(pool_slot=df["pool_slot"].astype(str))

    # df['reversed_slot'] = df['pool_slot'].max() - df['pool_slot'] + 1
    # Date slider
    min_date = df["changeout_date"].min().date()
    max_date = df["arrival_date"].max().date()
    current_date = datetime.now().date()
    # Filter and sort data
    filtered_df = df[df["arrival_date"].dt.date > current_date].sort_values(
        ["pool_slot", "arrival_date"], ascending=[True, False]
    )
    # Use drop_duplicates to keep only the first occurrence for each pool_number
    filtered_df = filtered_df.drop_duplicates(subset="pool_slot", keep="first")
    filtered_df = filtered_df.sort_values("arrival_date").reset_index(drop=True)
    # Display upcoming arrivals using columns and metrics
    st.subheader("Próximas llegadas de componente")
    if not filtered_df.empty:
        columns = st.columns(4)
        for i, (_, row) in enumerate(filtered_df.iterrows()):
            with columns[i % 4]:
                days_until_arrival = (row["arrival_date"].date() - current_date).days
                if row["pool_changeout_type"] == "E":
                    days_until_arrival = "?"
                    row["arrival_week"] = "?"
                # repair_days = row["ohv_normal"] if row["pool_type"] == "P" else row["ohv_unplanned"]
                # repair_color = "normal" if row["pool_type"] == "P" else "inverse"

                st.metric(
                    label=f"Equipo {row['equipo']}",
                    value=f"{days_until_arrival} días restantes",
                    # delta=f"{repair_days} days repair",
                    # delta_color=repair_color,
                )
                st.write(f"Semana estimada de llegada: {row['arrival_week']}")
                st.write(f"Fecha cambio componente: {row['changeout_date'].date()}")
                map_dict = {"I": "Imprevisto", "P": "Planificado", "E": "Esperando"}
                st.write(f"Tipo de cambio: {map_dict[row['pool_changeout_type']]}")
                st.write("---")
    else:
        st.write("No upcoming arrivals for the selected date.")

    df = modify_dataframe(df)

    # TODO: Cambiar a fecha móvil
    today = datetime.now()
    jan_1 = date(today.year, 1, 1)
    dec_31 = date(today.year, 12, 31)

    d = st.date_input(
        "Select your vacation for next year",
        (jan_1, max_date),
        min_date,
        max_date,
        format="MM.DD.YYYY",
    )

    # st.subheader("Selected item")
    # st.write(timeline2)

    fig = plot_pool_px_timeline(df.loc[df["arrival_date"].dt.date.between(d[0], d[1])])

    st.plotly_chart(fig, use_container_width=True)

    # st.dataframe(df.loc[df["component_code"] == "mp"])
