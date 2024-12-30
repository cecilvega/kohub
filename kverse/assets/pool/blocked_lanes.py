import os
from io import BytesIO

import pandas as pd
from azure.storage.blob import BlobServiceClient
from kverse.assets.master_components import master_components
import unicodedata
import re
from datetime import datetime, timedelta
import openpyxl


def read_blocked_lanes():

    # blob_service_client = BlobServiceClient.from_connection_string(os.environ["AZURE_CONN_STR"])
    #
    # blob_client = blob_service_client.get_blob_client(
    #     container="kdata-raw",
    #     blob=f"PLANIFICACION/POOL/ESCONDIDA/COMPONENTES EN ESPERA APROBACION.xlsx",
    # )
    # blob_data = blob_client.download_blob()
    # blob_data = BytesIO(blob_data.readall())
    blob_data = "DATA/PLAN/COMPONENTES EN ESPERA APROBACION.xlsx"
    df = (
        pd.read_excel(blob_data)
        .rename(
            columns={
                "Componente": "component",
                "Equipo": "equipo",
                "Pool": "pool_slot",
                "Fecha Cambio": "changeout_date",
                "Fecha Aprobación": "arrival_date",
            }
        )
        .assign(equipo=lambda x: x["equipo"].astype(str))
        .dropna(subset=["pool_slot"])
    )
    return df
