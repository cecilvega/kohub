import streamlit as st
from pathlib import Path
from common import *
from PIL import Image

st.header("BHP 1")
st.write(f"You are logged in as {st.session_state.role}.")

logo_path = Path("__file__").absolute().parent / "images/bhp-logo.png"

st.sidebar.image(Image.open(logo_path))
