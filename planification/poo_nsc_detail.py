import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import calendar

# Sample data (you'll need to replace this with your actual data)
months = list(calendar.month_abbr)[1:]
nsc_acordadas = [7, 6, 3, 6, 8, 5, 4, 0, 0, 0, 0, 0]
nsc_realizadas = [6, 7, 6, 6, 3, 1, 0, 0, 0, 0, 0, 0]
mcoe_plan = [6, 3, 5, 10, 6, 4, 10, 8, 8, 10, 8, 8]
mcoe_ajuste = [6, 5, 4, 6, 7, 5, 8, 5, 5, 6, 4, 0]
cambios_planificados = [3, 1, 1, 1, 6, 3, 0, 0, 0, 0, 0, 0]
cambios_imprevistos = [4, 2, 6, 7, 1, 0, 0, 0, 0, 0, 0, 0]

# Streamlit app
st.title("Operations Dashboard")

# NSC Component
st.header("NSC: Entregas acordadas (MEL & KCH) v/s entregas realizadas Week +4 (Mensual)")
col1, col2 = st.columns([3, 1])

with col1:
    fig_nsc = go.Figure()
    fig_nsc.add_trace(go.Bar(x=months, y=nsc_acordadas, name="Acordadas", marker_color='gray'))
    fig_nsc.add_trace(go.Bar(x=months, y=nsc_realizadas, name="Realizadas", marker_color='blue'))
    fig_nsc.update_layout(barmode='group', height=400)
    st.plotly_chart(fig_nsc, use_container_width=True)

with col2:
    st.metric("NSC Componente", "74%", delta="-21%")
    st.caption("Meta: 95%")

# MCoE Demand
st.header("Demanda MCoE: Plan 12M v/s ajuste +4Week (Mensual)")
col3, col4 = st.columns([3, 1])

with col3:
    fig_mcoe = go.Figure()
    fig_mcoe.add_trace(go.Bar(x=months, y=mcoe_plan, name="Plan 12M", marker_color='lightsalmon'))
    fig_mcoe.add_trace(go.Bar(x=months, y=mcoe_ajuste, name="Ajuste +4", marker_color='darkorange'))
    fig_mcoe.update_layout(barmode='group', height=400)
    st.plotly_chart(fig_mcoe, use_container_width=True)

with col4:
    st.metric("Nivel Ajuste MCoE", "71%", delta="29%", delta_color="inverse")
    st.caption("Meta: 100%")

# Cambios Realizados
st.header("Cambios Realizados: Planificados v/s Imprevistos")
col5, col6 = st.columns([3, 1])

with col5:
    fig_cambios = go.Figure()
    fig_cambios.add_trace(go.Bar(x=months, y=cambios_planificados, name="Planificado", marker_color='green'))
    fig_cambios.add_trace(go.Bar(x=months, y=cambios_imprevistos, name="Imprevisto", marker_color='red'))
    fig_cambios.update_layout(barmode='stack', height=400)
    st.plotly_chart(fig_cambios, use_container_width=True)

with col6:
    # Pie chart for Plan v/s Imprevisto
    labels = ['Planificado', 'Imprevisto']
    values = [15, 20]  # These should be calculated based on your data
    fig_pie = px.pie(values=values, names=labels, hole=0.3)
    st.plotly_chart(fig_pie, use_container_width=True)
    st.caption("Plan v/s Imprevisto")
