import os
from io import BytesIO

import pandas as pd
from azure.storage.blob import BlobServiceClient


def read_cc():
    blob_service_client = BlobServiceClient(
        account_url=os.environ["AZURE_ACCOUNT_URL"],
        credential=os.environ["AZURE_SAS_TOKEN"],
    )

    blob_client = blob_service_client.get_blob_client(
        container=os.environ["AZURE_CONTAINER_NAME"],
        blob=f"{os.environ['AZURE_PREFIX']}/PLANIFICACION/POOL/PLANILLA DE CONTROL CAMBIO DE COMPONENTES MEL.xlsx",
    )
    blob_data = blob_client.download_blob()
    blob_data = BytesIO(blob_data.readall())
    cc_df = pd.read_excel(blob_data)
    columns_map = {
        "EQUIPO": "equipo",
        "COMPONENTE": "componente",
        "SUB COMPONENTE": "subcomponente",
        "POSICION": "position",
        "N/S RETIRADO": "component_serial",
        "W": "changeout_week",
        "FECHA DE CAMBIO": "changeout_date",
        "HORA CC": "component_hours",
        "TBO": "tbo_hours",
    }
    cc_df = (
        cc_df[list(columns_map.keys())]
        .dropna(subset=["COMPONENTE"])
        .rename(columns=columns_map)
        .assign(
            equipo=lambda x: x["equipo"].str.extract(r"(\d+)"),
            # changeout_week=lambda x: x["FECHA DE CAMBIO"]
            # .dt.year.astype(int)
            # .astype(str)
            # .str.cat(x["changeout_week"].str.zfill(2), sep="-W"),
            component_code=lambda x: x["componente"].map(
                lambda x: {
                    "Blower": "bp",
                    "Cilindro_Dirección": "cd",
                    "Suspensión_Trasera": "st",
                    "CMS": "cms",
                    "Motor_Tracción": "mt",
                    "Cilindro_Levante": "cl",
                    "Módulo_Potencia": "mp",
                }.get(x)
            ),
        )
        .dropna(subset=["component_code"])
    )
    cc_df = cc_df.assign(
        changeout_week=lambda x: x["changeout_date"]
        .dt.year.astype(str)
        .str.cat(x["changeout_week"].astype(str), sep="-W")
    )
    cc_df = cc_df.assign(pool_changeout_type=None)

    return cc_df
