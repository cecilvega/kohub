import streamlit as st

home = st.Page("Home.py", title="Home", icon=":material/dashboard:", default=True)
pool_proyection = st.Page("planification/pool_projection.py", title="Proyección Pool", icon=":material/dashboard:")
pool_nsc_detail = st.Page("planification/poo_nsc_detail.py", title="NSC Detalle", icon=":material/dashboard:")
pool_nsc_general = st.Page("planification/pool_nsc_general.py", title="NSC General", icon=":material/dashboard:")

hsec_3d = st.Page("hsec/3d.py", title="3D", icon=":material/dashboard:")

pg = st.navigation(
    {
        "Landing": [home],
        "Planificación": [pool_proyection, pool_nsc_general, pool_nsc_detail],
        "HSEC": [hsec_3d],
    }
)
pg.run()
