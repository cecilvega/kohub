import streamlit as st
import os
import hmac
import hashlib
import time
from collections import defaultdict


st.set_page_config(layout="wide", page_icon="🚜")  # page_title="DevOps", page_icon=":bar_chart:",
if "role" not in st.session_state:
    st.session_state.role = None
ROLES = {"Komatsu": ["derek"], "BHP": ["mel"]}


def get_password_hash(password):
    """Generate a SHA-256 hash of the password."""
    return hashlib.sha256(password.encode()).hexdigest()


def check_user_role(user, role):
    if role not in ROLES:
        return False
    return user in ROLES[role]


def password_entered(role: str):
    """Checks whether a password entered by the user is correct."""
    user = st.session_state["username"]
    if check_user_role(user, role):
        stored_hash = os.environ.get(f"PASSWORD_{user.upper()}")
        if stored_hash and hmac.compare_digest(get_password_hash(st.session_state["password"]), stored_hash):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
            del st.session_state["username"]
    else:
        st.session_state["password_correct"] = False
        st.error("Incorrect username or password")


def check_password():
    """Returns `True` if the user had a correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        user = st.session_state["username"]
        stored_hash = os.environ.get(f"PASSWORD_{user.upper()}")
        st.write(get_password_hash(st.session_state["password"]))
        st.write(stored_hash)
        st.write(stored_hash == get_password_hash(st.session_state["password"]))
        if stored_hash and hmac.compare_digest(get_password_hash(st.session_state["password"]), stored_hash):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False
            st.error("Incorrect username or password")

    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password")
    st.button("Log in", on_click=password_entered)

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    return False


def login():

    st.header("Log in")
    role = st.selectbox("Choose your role", [None, *list(ROLES.keys())])
    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password")
    # For debugging purposes skip login
    if os.environ.get("USERNAME") == "cecilvega":
        st.session_state.logged_in = True
        st.session_state.role = "Komatsu"
        st.rerun()
    if st.button("Log in"):
        password_entered(role)

        # Return True if the username + password is validated.
        if st.session_state.get("password_correct", False):
            st.session_state.logged_in = True
            st.session_state.role = role
            st.rerun()


def logout():
    st.session_state.role = None
    st.session_state.logged_in = False
    st.rerun()


role = st.session_state.role

logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
settings = st.Page("settings.py", title="Settings", icon=":material/settings:")

bhp_home = st.Page(
    "bhp/home.py",
    title="Home",
    icon=":material/healing:",
    default=(role == "BHP"),
)
komatsu_home = st.Page(
    "komatsu/inicio.py",
    title="Inicio",
    icon=":material/person_add:",
    default=(role == "Komatsu"),
)


pool_proyection = st.Page("planification/poolkch.py", title="Pool KCH")  # , icon=":material/dashboard:"
hse_3d = st.Page("hse/3d.py", title="3D")  # , icon=":material/dashboard:"

# settings
account_pages = [logout_page]
bhp_pages = [bhp_home, pool_proyection]
komatsu_pages = [komatsu_home, hse_3d]

st.title("MEL")
st.logo(
    "images/komatsu.png",
    icon_image="images/komatsu.png",
)

page_dict = {}
if st.session_state.role in ["BHP", "Komatsu"]:
    page_dict["BHP"] = bhp_pages
if st.session_state.role == "Komatsu":
    page_dict["Komatsu"] = komatsu_pages

if len(page_dict) > 0:
    pg = st.navigation({"Account": account_pages} | page_dict)
else:
    pg = st.navigation([st.Page(login)])


pg.run()

# from collections import defaultdict
#
# home = st.Page("../komatsu/inicio.py", title="Home", default=True)  # icon=":material/dashboard:"
# pool_proyection = st.Page(
#     "../planification/poolkch.py", title="Proyección Pool"
# )  # , icon=":material/dashboard:"
# pool_nsc_detail = st.Page("../planification/poo_nsc_detail.py", title="NSC Detalle")  # , icon=":material/dashboard:"
# pool_nsc_general = st.Page("../planification/pool_nsc_general.py", title="NSC General")  # , icon=":material/dashboard:"
#
# hsec_3d = st.Page("../hse/3d.py", title="3D")  # , icon=":material/dashboard:"
#
# pg = st.navigation(
#     {
#         "Landing": [home],
#         "Planificación": [pool_proyection, pool_nsc_general, pool_nsc_detail],
#         "HSEC": [hsec_3d],
#     }
# )
#
# pg.run()
