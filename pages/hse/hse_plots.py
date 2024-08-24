import os
from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st
from plotly import graph_objects as go
from azure.storage.blob import BlobServiceClient


def load_old_format(file):
    blob_service_client = BlobServiceClient(
        account_url=os.environ["AZURE_ACCOUNT_URL"],
        credential=os.environ["AZURE_SAS_TOKEN"],
    )
    blob_client = blob_service_client.get_blob_client(
        container=os.environ["AZURE_CONTAINER_NAME"],
        blob=file,
    )
    blob_data = blob_client.download_blob()
    blob_data = BytesIO(blob_data.readall())
    df = (
        pd.read_excel(blob_data)
        .rename(
            columns={
                "RUT/PASS": "Rut/Passport",
                "Estado Informe Final 3D": "Estado Informe Final",
                "Categoría Final 3D": "Resultado Final",
            }
        )
        .dropna(subset=["Estado Informe Final"])
        .reset_index(drop=True)
    )
    df = df.assign(
        adherence=df["Estado Informe Final"].map(
            lambda x: {
                "NO APLICA 3D": "VIGENTE",
                "SIN 3D": "NO VIGENTE",
                "No Vigente": "NO VIGENTE",
            }.get(x, x)
        )
    )
    return df


def load_new_format(file):
    blob_service_client = BlobServiceClient(
        account_url=os.environ["AZURE_ACCOUNT_URL"],
        credential=os.environ["AZURE_SAS_TOKEN"],
    )
    blob_client = blob_service_client.get_blob_client(
        container=os.environ["AZURE_CONTAINER_NAME"],
        blob=file,
    )
    blob_data = blob_client.download_blob()
    blob_data = BytesIO(blob_data.readall())
    adherence_df = pd.read_excel(
        blob_data,
        skiprows=7,
        sheet_name="3D",
        usecols="B:K",
    )
    adherence_df = adherence_df.assign(
        adherence=adherence_df["Estado Informe Final"].map(
            lambda x: {
                "NO APLICA 3D": "VIGENTE",
                "SIN 3D": "NO VIGENTE",
                "No Vigente": "NO VIGENTE",
            }.get(x, x)
        )
    ).dropna(subset=["Rut/Passport"])
    performance_df = (
        pd.read_excel(
            blob_data,
            skiprows=7,
            sheet_name="3D",
            usecols="M:V",
        )
        .rename(columns={"Rut/Passport.1": "Rut/Passport"})
        .drop(
            columns=[
                "Nombre.1",
                "Nombre Empleador.1",
                "SAP Empleador.1",
                "Contratista o Subcontratista?.1",
            ]
        )
        .dropna(subset=["Rut/Passport"])
    )
    df = pd.merge(
        adherence_df,
        performance_df,
        on="Rut/Passport",
        how="outer",
    )
    assert df["Estado Informe Final"].isnull().sum() == 0
    return df


def generate_3d_dashboard(df: pd.DataFrame):

    total_contrato = df.__len__()

    adherencia_3d = round(
        df.loc[df["Estado Informe Final"].isin(["VIGENTE", "NO APLICA 3D"])].__len__() / total_contrato * 100,
        1,
    )
    estado_final_3d = ["COMPETENTE", "COMPETENTE CON OBSERVACIONES", "CON OBSERVACIONES"]
    supervisor_df = df.loc[(df["Perfil 3D"] == "SUPERVISOR") & (df["Resultado Final"].isin(estado_final_3d))]
    desempeno_supervisores = (
        supervisor_df.loc[supervisor_df["Resultado Final"] == "COMPETENTE"].__len__() / supervisor_df.__len__() * 100
    )
    tecnico_df = df.loc[(df["Perfil 3D"] == "TÉCNICO") & (df["Resultado Final"].isin(estado_final_3d))]
    desempeno_tecnicos = (
        tecnico_df.loc[tecnico_df["Resultado Final"] == "COMPETENTE"].__len__() / tecnico_df.__len__() * 100
    )

    # Title
    st.title("Dashboard 3D")

    # Create columns
    col1, col2 = st.columns((1, 2))

    # Function to create donut chart
    def create_donut_chart(value, title, color):
        fig = go.Figure(
            go.Pie(labels=["", title], values=[100 - value, value], hole=0.7, marker_colors=["#d1d4d3", color])
        )
        fig.update_layout(
            annotations=[dict(text=f"{round(value,0)}%", x=0.5, y=0.5, font_size=20, showarrow=False)],
            showlegend=False,
            width=300,
            height=300,
            margin=dict(l=0, r=0, t=0, b=0),
        )
        return fig

    # Adherencia 3D
    with col1:
        st.subheader("Adherencia 3D")
        st.plotly_chart(create_donut_chart(adherencia_3d, "Adherencia 3D", "#140a9a"), use_container_width=True)
        st.markdown(
            "**Adherencia**: mide el % de personas con diagnóstico *Vigente* y eximidos (**No Aplica 3D**), con respecto al total del contrato"
        )
        fig_bar = px.bar(
            df.groupby(["adherence", "Estado Informe Final"]).size().reset_index(name="count"),
            x="count",
            y="adherence",
            color="Estado Informe Final",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Desempeño 3D
    with col2:
        st.subheader("Desempeño 3D")
        subcol1, subcol2 = st.columns(2)
        st.markdown(
            "**Desempeño**: Mide el % de resultados Competentes, en comparación con el total de personas que deben ser evaluadas según su perfil",
            unsafe_allow_html=True,
        )
        with subcol1:
            st.markdown("**Supervisores**")
            st.plotly_chart(
                create_donut_chart(desempeno_supervisores, "Desempeño 3D", "#7030a0"), use_container_width=True
            )

        with subcol2:
            st.markdown("**Técnicos**")
            st.plotly_chart(create_donut_chart(desempeno_tecnicos, "Desempeño 3D", "#7030a0"), use_container_width=True)
        barplot_df = df.groupby("Resultado Final").size().reset_index(name="count")
        fig = px.bar(barplot_df, x="Resultado Final", y="count")  # , title="Wide-Form Input"
        st.plotly_chart(fig, use_container_width=True)

        # st.dataframe(
        #     df.loc[(df["Perfil 3D"] == "SUPERVISOR") & (df["Categoría Final 3D"] != "PENDIENTE")]
        #     .groupby("Categoría Final 3D")[["Nombre Colaborador"]]
        #     .count()
        # )

    st.dataframe(df)
