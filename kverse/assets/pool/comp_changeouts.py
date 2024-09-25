import os
from io import BytesIO

import pandas as pd
from azure.storage.blob import BlobServiceClient
from kverse.assets.master_components import master_components
import unicodedata
import re
import openpyxl

openpyxl.reader.excel.warnings.simplefilter(action="ignore")


def clean_string(s):
    # Remove accents
    s = str(s)
    if s is not None:

        s = s.lower()
        s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

        # Replace whitespaces with underscore
        s = re.sub(r"\s+", "_", s)

        # Remove all non-alphanumeric characters except underscore
        s = re.sub(r"[^\w]+", "", s)
        s = {"cms": "conjunto_masa_suspension_delantera"}.get(s, s)
    return s


def read_cc():
    if os.environ.get("USERNAME") in ["cecilvega", "U1309565", "andmn"]:
        blob_data = "DATA/PLANILLA DE CONTROL CAMBIO DE COMPONENTES MEL.xlsx"
    else:
        blob_service_client = BlobServiceClient.from_connection_string(os.environ["AZURE_CONN_STR"])

        blob_client = blob_service_client.get_blob_client(
            container="kdata-raw",
            blob=f"PLANIFICACION/POOL/PLANILLA DE CONTROL CAMBIO DE COMPONENTES MEL.xlsx",
        )
        blob_data = blob_client.download_blob()
        blob_data = BytesIO(blob_data.readall())

    df = pd.read_excel(blob_data)
    columns_map = {
        "EQUIPO": "equipo",
        "COMPONENTE": "component",
        "SUB COMPONENTE": "subcomponent",
        "POSICION": "position",
        "N/S RETIRADO": "component_serial",
        "W": "changeout_week",
        "FECHA DE CAMBIO": "changeout_date",
        "HORA CC": "component_hours",
        "TBO": "tbo_hours",
        "TIPO CAMBIO POOL": "pool_changeout_type",
    }

    # df = pd.merge(df, master_components(), validate="1:1")

    df = df.rename(columns=columns_map).assign(  # [list(columns_map.keys())]
        equipo=lambda x: x["equipo"].str.extract(r"(\d+)"),
    )
    df = df.dropna(subset=["component"])
    df = df.assign(
        component_serial=df["component_serial"].str.strip().str.replace("\t", ""),
    )

    clean_columns = ["component", "subcomponent"]

    df[clean_columns] = df[clean_columns].apply(lambda x: x.apply(clean_string))
    df = df.assign()
    df = df.loc[df["component"].isin(master_components()["component"].unique())].reset_index(drop=True)

    df = df.assign(
        changeout_week=lambda x: x["changeout_date"]
        .dt.year.astype(str)
        .str.cat(x["changeout_week"].astype(int).astype(str), sep="-W")
    )

    return df
