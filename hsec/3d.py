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
from hsec.hsec_plots import generate_3d_dashboard

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
# st.text(f"{report_year} {report_month_str}")
partition_date = datetime.strptime(f"{report_year} {report_month_str}", "%Y %b").strftime("y=%Y/m=%m")
# st.text(partition_date)

blob_service_client = BlobServiceClient(
    account_url=os.environ["AZURE_ACCOUNT_URL"],
    credential=os.environ["AZURE_SAS_TOKEN"],
)

container_client = blob_service_client.get_container_client(os.environ["AZURE_CONTAINER_NAME"])
blob_list = container_client.list_blobs(name_starts_with=f"{os.environ['AZURE_PREFIX']}/HSEC/{partition_date}")
blob_list = [f.name for f in blob_list]
# assert blob_list.__len__() <= 1, "There should be only one file per month"
file = blob_list[0]
file1 = blob_list[1]

# df = pd.read_excel(blob_data)
tab1, tab2 = st.tabs(["Opción 1", "Opción 2"])
with tab1:
    st.write(f"Opción 1: {file}")
    generate_3d_dashboard(file)
with tab2:
    st.write(f"Opción 2: {file1}")
    generate_3d_dashboard(file1)

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
# np.random.seed(42)
# dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
# actual_values = np.random.normal(100, 15, len(dates))
# predicted_values = actual_values + np.random.normal(0, 10, len(dates))
# error = predicted_values - actual_values
#
# df = pd.DataFrame({"Date": dates, "Actual": actual_values, "Predicted": predicted_values, "Error": error})

# Title
# st.title("Data Comparison and Error Analysis Dashboard")

# Create columns
# col1, col2 = st.columns(2)


# Function to create gauge chart
# def create_gauge_chart(value, title, min_val, max_val):
#     fig = go.Figure(
#         go.Indicator(
#             mode="gauge+number",
#             value=value,
#             title={"text": title},
#             gauge={
#                 "axis": {"range": [min_val, max_val]},
#                 "bar": {"color": "darkblue"},
#                 "steps": [
#                     {"range": [min_val, (max_val - min_val) / 3], "color": "lightgray"},
#                     {"range": [(max_val - min_val) / 3, 2 * (max_val - min_val) / 3], "color": "gray"},
#                 ],
#                 "threshold": {
#                     "line": {"color": "red", "width": 4},
#                     "thickness": 0.75,
#                     "value": (max_val - min_val) * 0.8,
#                 },
#             },
#         )
#     )
#     fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
#     return fig


# # Metrics in gauges
# with col1:
#     st.subheader("Key Metrics")
#     mean_error = df["Error"].mean()
#     st.plotly_chart(
#         create_gauge_chart(mean_error, "Mean Error", df["Error"].min(), df["Error"].max()), use_container_width=True
#     )
