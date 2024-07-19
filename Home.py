import streamlit as st
from pathlib import Path
from common import *


st.set_page_config(page_title="Cross Chain Monitoring Tool", page_icon=":bar_chart:", layout="wide")

styler()
st.title("**Escondida MEL**")
# st.title("Advanced Analytics")
logo_path = Path("__file__").absolute().parent / "images/komatsu.png"
bhp_logo_path = Path("__file__").absolute().parent / "images/bhp-logo.png"
dalle_path = Path("__file__").absolute().parent / "images/bhp-komatsu.png"
from PIL import Image

st.write(Path("__file__").absolute().parents[1])
st.sidebar.image(Image.open(logo_path), caption=".")
st.sidebar.image(Image.open(bhp_logo_path), caption=".")
st.image(Image.open(dalle_path).resize((800, 600)), caption="...")


st.write(
    """
    
    """
)

st.subheader("MEL")
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
