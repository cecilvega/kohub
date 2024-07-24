import streamlit as st
from pathlib import Path
from common import *
import hmac


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""

        # st.secrets["password"]
        if hmac.compare_digest(st.session_state["password"], "derek"):

            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input("Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


if not check_password():
    st.stop()  # Do not continue if check_password is not True.


st.set_page_config(page_title="BHP Escondida MEL", page_icon=":bar_chart:", layout="wide")

# Custom CSS to match BHP colors
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FFFFFF;
    }
    .stButton>button {
        color: #FFFFFF;
        background-color: #12257E;
        border-radius: 5px;
    }
    .stTextInput>div>div>input {
        color: #808080;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("**BHP Escondida MEL**")

styler()
st.title("**Escondida MEL**")
# st.title("Advanced Analytics")
logo_path = Path("__file__").absolute().parent / "images/komatsu.png"
bhp_logo_path = Path("__file__").absolute().parent / "images/bhp-logo.png"
# dalle_path = Path("__file__").absolute().parent / "images/bhp-komatsu.png"
from PIL import Image

st.write(Path("__file__").absolute().parents[1])
st.sidebar.image(Image.open(logo_path), caption="BHP Escondida")
st.sidebar.image(Image.open(bhp_logo_path), caption=".")
# st.image(Image.open(dalle_path).resize((800, 600)), caption="BHP Escondida")


st.subheader("MEL (Mine Equipment Lifecycle) Overview")
st.write(
    """
    The MEL dashboard offers real-time insights into equipment performance, 
    maintenance schedules, and operational efficiency at Escondida.
    """
)

st.subheader("Future Developments")
st.write(
    """
    We are continually improving this dashboard to provide more value to BHP. 
    Upcoming features will include predictive maintenance algorithms and 
    integration with additional data sources.
    """
)

c1, c2, c3 = st.columns(3)
with c1:
    st.info("****", icon="💡")
with c2:
    st.info("****", icon="💻")
with c3:
    st.info("****", icon="🧠")
