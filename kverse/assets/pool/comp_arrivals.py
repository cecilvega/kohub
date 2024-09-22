import os
from io import BytesIO

import pandas as pd
from azure.storage.blob import BlobServiceClient
from kverse.assets.master_components import master_components
import unicodedata
import re


def read_component_arrivals():

    blob_service_client = BlobServiceClient.from_connection_string(os.environ["AZURE_CONN_STR"])

    blob_client = blob_service_client.get_blob_client(
        container="kdata-raw",
        blob=f"PLANIFICACION/POOL/ENTREGAS_CONFIRMADAS_COMPONENTES.xlsx",
    )
    blob_data = blob_client.download_blob()
    blob_data = BytesIO(blob_data.readall())

    df = pd.read_excel(blob_data)

    df = (
        df.rename(
            columns={
                "COMPONENTE": "component",
                # "MODELO": "model",
                "SEMANA_LLEGADA": "arrival_week",
                "FECHA_LLEGADA_REAL": "arrival_date",
            }
        )
        .dropna()
        .reset_index(drop=True)
    )
    return df
