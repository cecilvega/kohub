import streamlit as st
import os
import hmac
import hashlib
import time
from collections import defaultdict
import yaml

st.set_page_config(layout="wide", page_icon="🚜")  # page_title="DevOps", page_icon=":bar_chart:",
if "role" not in st.session_state:
    st.session_state.role = None

from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import (
    CredentialsError,
    ForgotError,
    Hasher,
    LoginError,
    RegisterError,
    ResetError,
    UpdateError,
)
from io import StringIO
from azure.storage.blob import BlobServiceClient

from datetime import timedelta


@st.cache_data(ttl=timedelta(hours=1))
def fetch_config():

    blob_service_client = BlobServiceClient.from_connection_string(os.environ["AZURE_CONN_STR"])
    blob_client = blob_service_client.get_blob_client(
        container="kdata-raw",
        blob="CONFIG/config.yaml",
    )
    blob_data = blob_client.download_blob().readall().decode("utf-8")
    config = yaml.load(blob_data, Loader=SafeLoader)

    return config


config = fetch_config()
authenticator = stauth.Authenticate(
    config["credentials"], config["cookie"]["name"], config["cookie"]["key"], config["cookie"]["expiry_days"]
)


def logout():
    # st.session_state.role = None
    # st.session_state.logged_in = False
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()


def login():
    pass


# logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
settings = st.Page("settings.py", title="Settings", icon=":material/settings:")


pool_projection = st.Page("pages/planification/poolkch.py", title="Pool KCH")  # , icon=":material/dashboard:"
spence = st.Page("pages/reliability/Spence.py", title="Spence")

planification_home = st.Page(
    "pages/planification/planification_komatsu.py",
    title="Información",
    icon=":material/person_add:",
)


st.logo("images/komatsu.png", icon_image="images/komatsu.png")

# Check if the user just logged out
if st.session_state.get("just_logged_out", False):
    st.session_state.just_logged_out = False
    st.rerun()

page_dict = {}
try:
    authenticator.login()
except LoginError as e:
    st.error(e)
if st.session_state["authentication_status"]:
    # st.write("___")
    # st.write(f'Welcome *{st.session_state["username"]}*')
    # st.title("Some content")
    # st.write("___")
    st.session_state.logged_in = True

    if "komatsu" in st.session_state.roles:
        komatsu_home = st.Page(
            "pages/home/home_komatsu.py",
            title="Inicio",
            icon=":material/person_add:",
        )
        bhp_home = st.Page(
            "pages/home/home_mel.py",
            title="Inicio (MEL)",
            icon=":material/healing:",
        )
        page_dict["Inicio"] = [komatsu_home, bhp_home]
        page_dict["Planificación"] = [pool_projection, planification_home]
        page_dict["Confiabilidad"] = [spence]
    else:
        bhp_home = st.Page(
            "pages/home/home_mel.py",
            title="Inicio",
            icon=":material/healing:",
        )
        if "spence" in st.session_state.roles:
            page_dict["Inicio"] = [bhp_home]
        if "mel" in st.session_state.roles:
            page_dict["Inicio"] = [bhp_home]
            page_dict["Planificación"] = [pool_projection]

    authenticator.logout(location="sidebar", callback=lambda x: logout)


elif st.session_state["authentication_status"] is False:
    st.error("Username/password is incorrect")
    st.stop()
elif st.session_state["authentication_status"] is None:
    st.warning("Please enter your username and password")

if len(page_dict) > 0:
    pg = st.navigation(page_dict)
else:
    pg = st.navigation([st.Page(login)])


# EXTRA:
css = """
<style>
    .stSlider [data-testid="stTickBar"] {
        display: none;
    }
    .stSlider label {
        display: block;
        text-align: center;
    }
</style>
"""

st.markdown(css, unsafe_allow_html=True)

pg.run()
