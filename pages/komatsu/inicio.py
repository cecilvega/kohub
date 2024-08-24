import streamlit as st
from pathlib import Path
from common import *

from PIL import Image


styler()


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
