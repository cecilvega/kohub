import streamlit as st
from pathlib import Path
from common import *


st.set_page_config(page_title="Cross Chain Monitoring Tool", page_icon=":bar_chart:", layout="wide")

styler()
st.title("**Advanced Analytics - LATAM**")
# st.title("Advanced Analytics")
logo_path = Path("__file__").absolute().parent / "images/komatsu.png"
dalle_path = Path("__file__").absolute().parent / "images/dalle.png"
from PIL import Image

st.write(Path("__file__").absolute().parents[1])
st.sidebar.image(Image.open(logo_path), caption="Sunrise by the mountains")
st.image(Image.open(dalle_path).resize((600, 600)), caption="Sunrise by the mountains")


st.write(
    """
    
    """
)

st.subheader("Methodology")
st.write(
    """
    
    """
)

st.subheader("Future Works")
st.write(
    """
    
    """
)

c1, c2, c3 = st.columns(3)
with c1:
    st.info("****", icon="💡")
with c2:
    st.info("****", icon="💻")
with c3:
    st.info("****", icon="🧠")
