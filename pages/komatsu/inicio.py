import streamlit as st
from pathlib import Path
from common import *

from PIL import Image


styler()
from pages.planification.utils.vis_px_timeline import validate_input, prepare_data

from streamlit_timeline import st_timeline

items = (
    {
        "id": "1",
        "content": "item1",
        "start": "2022-12-19",
        "end": "2022-12-23",
        "group": "1",
        "style": "color: red; background-color: white;",
    },
    {"id": "2", "content": "item1", "start": "2022-12-19", "end": "2022-12-20", "group": "1"},
    {"id": "3", "content": "item1", "start": "2022-12-20", "end": "2022-12-20", "group": "2"},
    {"id": "4", "content": "item1", "start": "2022-12-20", "end": "2022-12-20", "group": "2"},
)

groups = (
    {"id": "1", "content": "Group 1", "style": "color: black; background-color: white;"},
    {"id": "2", "content": "Group 2", "style": "color: black; background-color: white;"},
)


timeline = st_timeline(
    items=items,
    groups=groups,
    options={
        "selectable": True,
        "multiselect": True,
        "zoomable": True,
        "stack": False,
        "height": 154,
        "margin": {"axis": 5},
        "groupHeightMode": "auto",
        "orientation": {"axis": "top", "item": "top"},
        "format": {
            "minorLabels": {
                "week": "w",
            },
            "majorLabels": {
                "week": "MMMM YYYY",
            },
        },
        # "showWeekScale": True,
    },
    style="color: red",
)


st.subheader("Selected item")
st.write(timeline)

st.title("**BHP Escondida MEL**")

logo_path = Path("__file__").absolute().parent / "images/komatsu.png"


st.sidebar.image(Image.open(logo_path))


st.subheader("...")
st.write(
    """
    ...
    """
)

st.subheader("...")
st.write(
    """
    ...
    """
)

c1, c2, c3 = st.columns(3)
with c1:
    st.info("****", icon="💡")
with c2:
    st.info("****", icon="💻")
with c3:
    st.info("****", icon="🧠")
