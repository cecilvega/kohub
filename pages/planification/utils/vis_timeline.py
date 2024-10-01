import plotly.express as px
from datetime import datetime


import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from streamlit_timeline import st_timeline
import streamlit as st
from datetime import timedelta


def validate_input(df):
    """Validate the input DataFrame."""
    required_columns = [
        "pool_slot",
        "changeout_date",
        "arrival_date",
        "pool_changeout_type",
        "equipo",
        "component_serial",
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")


def prepare_data(df):
    """Prepare the data for plotting."""
    df = df.sort_values(["pool_slot", "changeout_date"])

    # df = df.drop(columns=["subcomponent_priority"])
    return df


def plot_pool_timeline(df):

    validate_input(df)
    df = prepare_data(df)

    # Create items for the timeline
    items = []
    for _, row in df.iterrows():
        content = f"{row['equipo']} - {row['component_serial']}"
        if row["pool_changeout_type"] == "A":
            content += f" ({(row['arrival_date'] - row['changeout_date']).days}d)"

        item = {
            "id": str(len(items) + 1),
            "content": content,
            "start": row["changeout_date"].strftime("%Y-%m-%d"),
            "end": row["arrival_date"].strftime("%Y-%m-%d"),
            "group": str(row["pool_slot"]),
            "style": f"background-color: {get_color(row['pool_changeout_type'])};",
        }
        items.append(item)

    # Create groups for the timeline
    groups = [{"id": str(slot), "content": f"Pool {slot}"} for slot in sorted(df["pool_slot"].unique())]

    # Set up options for the timeline
    options = {
        "selectable": True,
        "multiselect": False,
        # "zoomable": True,
        "stack": False,
        "height": 500,
        "margin": {"item": 10},
        "groupHeightMode": "fixed",
        "orientation": {"axis": "top", "item": "top"},
        "format": {
            "minorLabels": {"week": "w"},
            "majorLabels": {"week": "MMMM YYYY"},
        },
        "showCurrentTime": True,
    }

    # Create and return the timeline
    timeline = st_timeline(items=items, groups=groups, options=options)
    return timeline


def get_color(change_type):
    """Return color based on pool_changeout_type."""
    color_map = {
        "REPROGRAMADO": "#942d00",  # Red
        "REAL": "#007569",  # Green
        # "E": "#a5abaf",  # Gray
        # "R": "#ffc82f",  # Orange
        "PROYECTADO": "#140a9a",  # Blue
    }
    return color_map.get(change_type, "#000000")  # Default to black if not found


def plot_component_arrival_timeline(df):

    df = df.assign(
        component=df["component"].map(
            lambda x: {
                "blower_parrilla": "Blower Parrilla",
                "cilindro_direccion": "Cilindro de Dirección",
                "suspension_trasera": "Suspensión Trasera",
                "suspension_delantera": "Suspensión Delantera",
                "motor_traccion": "Motor de Tracción",
                "cilindro_levante": "Cilindro de Levante",
                "modulo_potencia": "Módulo de Potencia",
            }[x]
        )
    )
    df["label"] = df.groupby(["component", "arrival_date"])["arrival_date"].transform("count").astype(str)
    df["label"] = df["arrival_date"].dt.strftime("%Y-%m-%d") + " (" + df["label"] + ")"

    # TODO: RETOMAR
    # proj_df = df.loc[
    #     (df["arrival_type"] == "PROYECTADO") & (df["arrival_date"] >= (datetime.now() - timedelta(days=7)))
    # ].sort_values("arrival_date")
    # columns = st.columns(4)
    # for i, (_, row) in enumerate(proj_df.iterrows()):
    #     with columns[i % 4]:
    #         days_until_arrival = (row["arrival_date"].date() - datetime.now().date()).days
    #         # if row["pool_changeout_type"] == "E":
    #         #     days_until_arrival = "?"
    #         #     row["arrival_week"] = "?"
    #         # repair_days = row["ohv_normal"] if row["pool_type"] == "P" else row["ohv_unplanned"]
    #         # repair_color = "normal" if row["pool_type"] == "P" else "inverse"
    #
    #         st.metric(
    #             label=f"{row['component']}",
    #             value=f"{days_until_arrival} días restantes",
    #             # delta=f"{repair_days} days repair",
    #             # delta_color=repair_color,
    #         )
    #         st.write(f"Semana estimada de llegada: {row['arrival_week']}")
    #         # st.write(f"Fecha cambio componente: {row['changeout_date'].date()}")
    #         # map_dict = {"I": "Imprevisto", "P": "Planificado", "E": "Esperando"}
    #         # st.write(f"Tipo de cambio: {map_dict[row['pool_changeout_type']]}")
    #         st.write("---")

    # Create items for the timeline
    items = []
    for _, row in df.iterrows():
        item = {
            "id": str(len(items) + 1),
            "content": f"{row['label']}",
            "start": row["arrival_date"].strftime("%Y-%m-%d"),
            "group": row["component"],
            "style": f"background-color: {get_color(row['arrival_type'])};color: white;",
        }
        items.append(item)

    # Create groups for the timeline
    groups = [{"id": str(code), "content": code} for code in sorted(df["component"].unique())]

    # Set up options for the timeline
    options = {
        "selectable": True,
        "multiselect": False,
        "zoomable": True,
        "stack": False,
        "height": "450px",  # Increased height to accommodate more component codes
        "margin": {"item": 10},
        "groupHeightMode": "fixed",
        "orientation": {"axis": "top", "item": "top"},
        "format": {
            "minorLabels": {"week": "w"},
            "majorLabels": {"week": "MMMM YYYY"},
        },
    }

    # Create and return the timeline
    timeline = st_timeline(items=items, groups=groups, options=options)
    return timeline
