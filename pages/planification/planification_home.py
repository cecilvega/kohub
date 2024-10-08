import streamlit as st
from pathlib import Path
from common import *
from PIL import Image

st.header("Información Área Planificación")

root_path = Path("__file__").absolute().parent
# logo_path = root_path / "images/bhp-logo.png"
news_path = root_path / "pages/planification/news.md"

# st.sidebar.image(Image.open(logo_path))

st.markdown(news_path.read_text(encoding="utf-8-sig"), unsafe_allow_html=True)
