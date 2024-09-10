import plotly.express as px
from datetime import datetime


import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from streamlit_timeline import st_timeline
import streamlit as st


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
    """
    Create a timeline of pool events using the streamlit_timeline library.

    Parameters:
    df (pandas.DataFrame): Input DataFrame containing pool timeline data.
                           Required columns: pool_slot, changeout_date, arrival_date,
                           pool_changeout_type, equipo, component_serial

    Returns:
    streamlit_timeline object: A Streamlit timeline object representing the pool events.

    Raises:
    ValueError: If required columns are missing from the input DataFrame.
    """

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
        "I": "#ff0000",  # Red
        "P": "#2bb673",  # Green
        "E": "#a5abaf",  # Gray
        "R": "#f37021",  # Orange
        "A": "#00a7e1",  # Blue
    }
    return color_map.get(change_type, "#000000")  # Default to black if not found


def plot_component_arrival_timeline(df):
    """
    Create a timeline of component arrivals using the streamlit_timeline library.

    Parameters:
    df (pandas.DataFrame): Input DataFrame containing component arrival data.
                           Required columns: component_code, pool_slot, arrival_date

    Returns:
    streamlit_timeline object: A Streamlit timeline object representing the component arrivals.

    Raises:
    ValueError: If required columns are missing from the input DataFrame.
    """

    # Get the last arrival for each unique combination of component_code and pool_slot
    df_last_arrivals = df.sort_values("arrival_date").groupby(["component", "pool_slot"]).last().reset_index()
    df_last_arrivals = df_last_arrivals.assign(
        component=df["component"].map(
            lambda x: {
                "blower": "Blower",
                "cilindro_direccion": "Cilindro de Dirección",
                "suspension_trasera": "Suspensión Trasera",
                "conjunto_masa_suspension": "Conjunto Masa Suspensión",
                "motor_traccion": "Motor de Tracción",
                "cilindro_levante": "Cilindro de Levante",
                "modulo_potencia": "Módulo de Potencia",
            }.get(x)
        )
    )
    # Create items for the timeline
    items = []
    for _, row in df_last_arrivals.iterrows():
        item = {
            "id": str(len(items) + 1),
            "content": f"Pool {row['pool_slot']}",
            "start": row["arrival_date"].strftime("%Y-%m-%d"),
            "group": str(row["component"]),
            "style": f"background-color: {get_color(row['pool_changeout_type'])};",
        }
        items.append(item)

    # Create groups for the timeline
    groups = [{"id": str(code), "content": code} for code in sorted(df_last_arrivals["component"].unique())]

    # Set up options for the timeline
    options = {
        "selectable": True,
        "multiselect": False,
        "zoomable": True,
        "stack": False,
        "height": "350px",  # Increased height to accommodate more component codes
        "margin": {"item": 10},
        "groupHeightMode": "fixed",
        "orientation": {"axis": "top", "item": "top"},
        "format": {
            "minorLabels": {"week": "w"},
            "majorLabels": {"week": "MMMM YYYY"},
        },
        # "showCurrentTime": True,
        # "type": "point",  # Use point type for single-date events
    }

    # Create and return the timeline
    timeline = st_timeline(items=items, groups=groups, options=options)
    return timeline
