import streamlit as st

home = st.Page("Home.py", title="Home", icon=":material/dashboard:", default=True)
pool_proyection = st.Page("pool/pool_projection.py", title="Proyección Pool", icon=":material/dashboard:")
pool_nsc_detail = st.Page("pool/poo_nsc_detail.py", title="NSC Detalle", icon=":material/dashboard:")
pool_nsc_general = st.Page("pool/pool_nsc_general.py", title="NSC General", icon=":material/dashboard:")

hr_3d = st.Page("hr/3d.py", title="3D", icon=":material/dashboard:")

pg = st.navigation(
    {
        "Landing": [home],
        "Planificación": [pool_proyection, pool_nsc_general, pool_nsc_detail],
        "Recursos Humanos": [hr_3d],
    }
)
pg.run()
