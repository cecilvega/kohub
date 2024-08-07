import streamlit as st


import streamlit as st
import os
import hmac
import hashlib
import time
from collections import defaultdict

#
# def get_password_hash(password):
#     """Generate a SHA-256 hash of the password."""
#     return hashlib.sha256(password.encode()).hexdigest()
#
#
# def check_password():
#     """Returns `True` if the user had a correct password."""
#
#     def password_entered():
#         """Checks whether a password entered by the user is correct."""
#         user = st.session_state["username"]
#         stored_hash = os.environ.get(f"PASSWORD_{user.upper()}")
#         st.write(get_password_hash(st.session_state["password"]))
#         st.write(stored_hash)
#         st.write(stored_hash == get_password_hash(st.session_state["password"]))
#         if stored_hash and hmac.compare_digest(get_password_hash(st.session_state["password"]), stored_hash):
#             st.session_state["password_correct"] = True
#             del st.session_state["password"]  # Don't store the password.
#             del st.session_state["username"]
#         else:
#             st.session_state["password_correct"] = False
#             st.error("Incorrect username or password")
#
#     if st.session_state.get("password_correct", False):
#         return True
#
#     # Show inputs for username + password.
#     st.text_input("Username", key="username")
#     st.text_input("Password", type="password", key="password")
#     st.button("Log in", on_click=password_entered)
#
#     # Return True if the username + password is validated.
#     if st.session_state.get("password_correct", False):
#         return True
#
#     return False


# Main app logic
# if check_password():
#     st.write("Here goes your normal Streamlit app...")
#     st.button("Log out", on_click=lambda: st.session_state.clear())
home = st.Page("Home.py", title="Home", default=True)  # icon=":material/dashboard:"
pool_proyection = st.Page("planification/pool_projection.py", title="Proyección Pool")  # , icon=":material/dashboard:"
pool_nsc_detail = st.Page("planification/poo_nsc_detail.py", title="NSC Detalle")  # , icon=":material/dashboard:"
pool_nsc_general = st.Page("planification/pool_nsc_general.py", title="NSC General")  # , icon=":material/dashboard:"

hsec_3d = st.Page("hsec/3d.py", title="3D")  # , icon=":material/dashboard:"

pg = st.navigation(
    {
        "Landing": [home],
        "Planificación": [pool_proyection, pool_nsc_general, pool_nsc_detail],
        "HSEC": [hsec_3d],
    }
)
pg.run()
