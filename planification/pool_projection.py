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

st.set_page_config(page_title="DevOps", page_icon=":bar_chart:", layout="wide")
styler()


df = read_archived_pool_proj()
df = df.assign(
    componente=df["component"].map(
        lambda x: {
            "bl": "Blower",
            "cd": "Cilindro Dirección",
            "st": "Suspensión Trasera",
            "cms": "CMSD",
            "mt": "Motor Tracción",
            "cl": "Cilindro Levante",
            "mp": "Módulo Potencia",
        }[x]
    )
)
df[["changeout_date", "arrival_date"]] = df[["changeout_date", "arrival_date"]].apply(
    lambda x: pd.to_datetime(x, format="%Y-%m-%d")
)


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

df = df.loc[df["componente"] == componente].reset_index(drop=True)
df = df.assign(pool_slot=df["pool_slot"].astype(str))


# Date slider
min_date = df["changeout_date"].min().date()
max_date = df["arrival_date"].max().date()
current_date = st.slider(
    "Select Date", min_value=min_date, max_value=max_date, value=datetime.now().date(), format="YYYY-MM-DD"
)

# Filter and sort data
filtered_df = df[df["arrival_date"].dt.date > current_date].sort_values("arrival_date")

# Use drop_duplicates to keep only the first occurrence for each pool_number
filtered_df = filtered_df.drop_duplicates(subset="pool_slot", keep="first")

# Display upcoming arrivals using columns and metrics
st.subheader("Upcoming Component Arrivals")
if not filtered_df.empty:
    columns = st.columns(4)
    for i, (_, row) in enumerate(filtered_df.iterrows()):
        with columns[i % 4]:
            days_until_arrival = (row["arrival_date"].date() - current_date).days
            # repair_days = row["ohv_normal"] if row["pool_type"] == "P" else row["ohv_unplanned"]
            # repair_color = "normal" if row["pool_type"] == "P" else "inverse"

            st.metric(
                label=f"Pool {row['pool_slot']} - Equipment {row['equipo']}",
                value=f"{days_until_arrival} days until arrival",
                # delta=f"{repair_days} days repair",
                # delta_color=repair_color,
            )
            st.write(f"Arrival Date: {row['arrival_date'].date()}")
            st.write(f"Original Change Date: {row['changeout_date'].date()}")
            st.write(f"Pool Type: {row['pool_changeout_type']}")
            st.write("---")
else:
    st.write("No upcoming arrivals for the selected date.")


def plot_pool_timeline(df):
    # Create the Gantt chart
    pool_numbers = sorted(df["pool_slot"].unique())
    grid_positions = [-0.5] + [i + 0.5 for i in range(len(pool_numbers))]
    fig = px.timeline(
        df,
        x_start="changeout_date",
        x_end="arrival_date",
        y="pool_slot",
        color="pool_changeout_type",
        color_discrete_map={"I": "red", "P": "green"},
        hover_data=["pool_slot", "changeout_date", "arrival_date", "equipo", "component_serial"],
        height=500,
        title="Cambios Reales Ejecutados",
    )

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
            title="Component",
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
            y=row["pool_slot"],
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


# blob_service_client = BlobServiceClient(
#     account_url=os.environ["AZURE_ACCOUNT_URL"],
#     credential=os.environ["AZURE_SAS_TOKEN"],
# )
#
# blob_client = blob_service_client.get_blob_client(
#     container=os.environ["AZURE_CONTAINER_NAME"],
#     blob=f"{os.environ['AZURE_PREFIX']}/pool-consolidated.csv",
# )
# blob_data = blob_client.download_blob()
# blob_data = BytesIO(blob_data.readall())
# df = pd.read_csv(blob_data)

fig = plot_pool_timeline(df)

st.plotly_chart(fig, use_container_width=True)
