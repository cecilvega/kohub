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
from planification.pool import *
from datetime import datetime, date, timedelta


# st.set_page_config(page_title="DevOps", page_icon=":bar_chart:", layout="wide")
styler()

available_components = ["bp", "cd", "mt", "st", "cms", "cl", "mp"]


st.markdown(
    """
## Estado de los Componentes

| Componente | Estado | 
|------------|--------|
| Blower | 🔜 Próximamente |
| Cilindro Dirección | 🔜 Próximamente |
| Suspensión Trasera | 🔜 Próximamente |
| CMSD | 🔜 Próximamente |
| Motor Tracción | 🔜 Próximamente |
| Cilindro Levante | 🔜 Próximamente |
| Módulo Potencia | ✅ Funcionando |
---

"""
)


@st.cache_data(ttl=timedelta(hours=1))
def fetch_and_clean_data():
    cc_df = read_cc()

    pool_proj_df = read_base_pool_proj()
    cc_df = cc_df.loc[cc_df["component_code"].isin(available_components)].reset_index(drop=True)
    pool_proj_df = pool_proj_df.loc[pool_proj_df["component_code"].isin(available_components)].reset_index(drop=True)

    df = generate_pool_projection(cc_df, pool_proj_df, available_components)
    return df


df = fetch_and_clean_data()

# Drop missing components
df = df.dropna(subset=["arrival_date"]).reset_index(drop=True)

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
    index=6,
)

df = df.loc[df["componente"] == componente].reset_index(drop=True)
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
            if row["pool_changeout_type"] == "U":
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
            map_dict = {"I": "Imprevisto", "P": "Planificado", "U": "Pendiente"}
            st.write(f"Tipo de cambio: {map_dict[row['pool_changeout_type']]}")
            st.write("---")
else:
    st.write("No upcoming arrivals for the selected date.")


def plot_pool_timeline(df):
    # Create the Gantt chart
    pool_numbers = sorted(df["pool_slot"].unique())
    grid_positions = [-0.5] + [i + 0.5 for i in range(len(pool_numbers))]
    df = df.drop(columns=["subcomponent_priority"])
    fig = px.timeline(
        df,
        x_start="changeout_date",
        x_end="arrival_date",
        y="pool_slot",
        color="pool_changeout_type",
        color_discrete_map={"I": "red", "P": "green", "U": "gray"},
        hover_data=["pool_slot", "changeout_date", "arrival_date", "equipo", "component_serial"],
        height=500,
        title="Cambios Reales Ejecutados",
    )
    fig.for_each_trace(lambda t: t.update(name={"I": "Imprevisto", "P": "Planificado", "U": "Pendiente"}[t.name]))

    ###
    # Add rectangles for overlapping periods
    df = df.sort_values(["pool_slot", "changeout_date"])
    for i in range(len(df) - 1):
        current_row = df.iloc[i]
        next_row = df.iloc[i + 1]
        if (
            current_row["pool_slot"] == next_row["pool_slot"]
            and current_row["arrival_date"] > next_row["changeout_date"]
        ):

            overlap_start = next_row["changeout_date"]
            overlap_end = min(current_row["arrival_date"], next_row["arrival_date"])
            # Calculate the overlap duration
            # Calculate the overlap duration
            overlap_duration = overlap_end - overlap_start

            # Calculate the midpoint of the overlap period
            overlap_midpoint = overlap_start + (overlap_end - overlap_start) / 2
            fig.add_shape(
                type="rect",
                x0=overlap_start,
                x1=overlap_end,
                y0=current_row["pool_slot"] - 1 - 0.4,
                y1=current_row["pool_slot"] - 1 + 0.4,
                fillcolor="yellow",
                opacity=0.5,
                layer="above",
                line_width=0,
            )
            # Add text to show the overlap duration
            fig.add_annotation(
                x=overlap_midpoint,
                y=current_row["pool_slot"] - 1,  # Position the text above the yellow rectangle
                text=f"{overlap_duration.days} days",
                showarrow=False,
                font=dict(size=15, color="black"),
                bgcolor="white",
                opacity=0.8,
                bordercolor="black",
                borderwidth=1,
            )
    # st.dataframe(df)
    ###

    fig.update_layout(
        xaxis=dict(
            tickformat="W%V",
            ticklabelmode="period",
            tick0="2024-01-01",
            showgrid=True,
            ticks="inside",
            ticklabelposition="inside",
            side="bottom",
            dtick=7 * 24 * 60 * 60 * 1000,
            gridwidth=2,  # Increase grid line width
        ),
        xaxis2=dict(
            tickformat="%b-%y",
            ticklabelmode="period",
            tickangle=0,
            overlaying="x",
            side="bottom",
            showgrid=False,
        ),
        yaxis=dict(
            autorange="reversed",
            title="Asignación de Pool",
            automargin=True,
            showticklabels=True,
            tickmode="array",
            tickvals=df["pool_slot"].unique(),
            ticktext=df["pool_slot"].unique(),
            showgrid=False,
            zeroline=False,
        ),
        # bargap=0.5,
        plot_bgcolor="white",
    )

    # Add custom horizontal lines between categories
    for y in grid_positions:
        fig.add_shape(
            type="line",
            x0=df["changeout_date"].min(),
            x1=df["arrival_date"].max(),
            y0=y,
            y1=y,
            line=dict(color="black", width=1.5),
            layer="below",
        )

    # Add equipment numbers over the bars
    for i, row in df.iterrows():
        fig.add_annotation(
            x=row["changeout_date"] + (row["arrival_date"] - row["changeout_date"]) / 2,
            y=row["pool_slot"] - 1,
            text=str(row["equipo"]),
            showarrow=False,
            font=dict(size=15, color="black"),
            bgcolor="white",
            opacity=0.8,
        )

    # Para evitar que aparezcan en grande
    fig.update_yaxes(type="category", categoryorder="array", categoryarray=pool_numbers)

    # Add a vertical line for the current week
    current_date = datetime.now().date()
    fig.add_vline(x=current_date, line_width=2, line_dash="dash", line_color="black")
    # Add an annotation for the current week line
    fig.add_annotation(
        x=current_date,
        y=-0.1,  # This positions the text at the top of the plot
        text="Hoy",
        font=dict(size=20, color="black"),
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="black",
        ax=50,  # Offset the arrow in x direction
        ay=-30,  # Offset the arrow in y direction
    )

    # Update layout for cleanliness
    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=50),
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title="Tipo de Cambio"),
    )
    start_date = df["changeout_date"].min()
    end_date = df["changeout_date"].max()
    # Add invisible trace to ensure xaxis2 spans the full range
    fig.add_trace(
        go.Scatter(
            x=[start_date, end_date],
            y=[df["pool_slot"].iloc[0]] * 2,
            mode="markers",
            marker_opacity=0,
            showlegend=False,
            xaxis="x2",
            opacity=0,
        )
    )

    # Update traces
    fig.update_traces(marker_line_color="rgb(8,48,107)", marker_line_width=1.5, opacity=0.8)

    # Update traces with custom hover template
    # fig.update_traces(
    #     marker_line_color="rgb(8,48,107)",
    #     marker_line_width=1.5,
    #     opacity=0.8,
    #     hovertemplate="<b>Pool Number:</b> %{y}<br>" +
    #                   "<b>Pool Type:</b> %{marker.color}<br>" +
    #                   "<b>Start Date:</b> %{x[0]|%Y-%m-%d}<br>" +
    #                   "<b>End Date:</b> %{x[1]|%Y-%m-%d}<br>" +
    #                   "<b>Equipment:</b> %{text}<extra></extra>",
    #     text=df['equipo']
    # )
    return fig


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

fig = plot_pool_timeline(df.loc[df["arrival_date"].dt.date.between(d[0], d[1])])


st.plotly_chart(fig, use_container_width=True)

# st.dataframe(df.loc[df["component_code"] == "mp"])
