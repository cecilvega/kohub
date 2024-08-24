import plotly.express as px
from datetime import datetime


import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


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
    df = df.drop(columns=["subcomponent_priority"])
    return df


def create_base_chart(df):
    """Create the base Gantt chart."""
    fig = px.timeline(
        df,
        x_start="changeout_date",
        x_end="arrival_date",
        y="pool_slot",
        color="pool_changeout_type",
        color_discrete_map={"I": "#ff0000", "P": "#2bb673", "E": "#a5abaf", "R": "#f37021", "A": "#00a7e1"},
        hover_data=["pool_slot", "changeout_date", "arrival_date", "equipo", "component_serial"],
        height=500,
        title="Actual Changes Executed",
    )
    fig.for_each_trace(
        lambda t: t.update(
            name={"I": "Imprevisto", "P": "Planificando", "E": "Esperando", "R": "Reparado", "A": "Adelantado"}[t.name]
        )
    )
    return fig


def customize_layout(fig, df):
    """Customize the chart layout."""
    pool_numbers = sorted(df["pool_slot"].unique())
    grid_positions = [-0.5] + [i + 0.5 for i in range(len(pool_numbers))]

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
            gridwidth=2,
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
            title="Pool Assignment",
            automargin=True,
            showticklabels=True,
            tickmode="array",
            tickvals=df["pool_slot"].unique(),
            ticktext=df["pool_slot"].unique(),
            showgrid=False,
            zeroline=False,
        ),
        plot_bgcolor="white",
        margin=dict(l=10, r=10, t=50, b=50),
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title="Change Type"),
    )

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

    fig.update_yaxes(type="category", categoryorder="array", categoryarray=pool_numbers)


def add_annotations(fig, df):
    """Add annotations to the chart."""
    for _, row in df.loc[df["pool_changeout_type"].isin(["P", "I", "E"])].iterrows():
        fig.add_annotation(
            x=row["changeout_date"] + (row["arrival_date"] - row["changeout_date"]) / 2,
            y=row["pool_slot"] - 1,
            text=str(row["equipo"]),
            showarrow=False,
            font=dict(size=15, color="black"),
            bgcolor="white",
            opacity=0.8,
        )

    for _, row in df.loc[df["pool_changeout_type"].isin(["A"])].iterrows():
        fig.add_annotation(
            x=row["changeout_date"] + (row["arrival_date"] - row["changeout_date"]) / 2,
            y=row["pool_slot"] - 1,
            text=f"{((row['arrival_date'] - row['changeout_date']).days)}d",
            showarrow=False,
            font=dict(size=15, color="black"),
            bgcolor="white",
            opacity=0.8,
        )

    current_date = datetime.now().date()
    fig.add_vline(x=current_date, line_width=2, line_dash="dash", line_color="black")
    fig.add_annotation(
        x=current_date,
        y=-0.1,
        text="Today",
        font=dict(size=20, color="black"),
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="black",
        ax=50,
        ay=-30,
    )


def add_invisible_trace(fig, df):
    """Add invisible trace to ensure xaxis2 spans the full range."""
    start_date = df["changeout_date"].min()
    end_date = df["changeout_date"].max()
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


def plot_pool_timeline(df):
    """
    Create a Gantt chart of pool timeline using the provided DataFrame.

    Parameters:
    df (pandas.DataFrame): Input DataFrame containing pool timeline data.
                           Required columns: pool_slot, changeout_date, arrival_date,
                           pool_changeout_type, equipo, component_serial

    Returns:
    plotly.graph_objects.Figure: A Plotly figure object representing the Gantt chart.

    Raises:
    ValueError: If required columns are missing from the input DataFrame.
    """

    validate_input(df)
    df = prepare_data(df)
    fig = create_base_chart(df)
    customize_layout(fig, df)
    add_annotations(fig, df)
    add_invisible_trace(fig, df)

    fig.update_traces(marker_line_color="rgb(8,48,107)", marker_line_width=1.5, opacity=0.8)

    return fig
