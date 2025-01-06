import pandas as pd
import openpyxl
import re
from datetime import datetime
from pathlib import Path
import os
from io import BytesIO, StringIO
from azure.storage.blob import BlobServiceClient
from kverse.assets.pool.utils import extract_info, idx_to_pool_slot, get_weeks_and_comments, get_end_week
import numpy as np


def read_base_pool_proj():
    # if os.environ.get("USERNAME") in ["cecilvega", "U1309565", "andmn"]:
    #     blob_data = "DATA/pool_proj.csv"
    # else:
    # blob_service_client = BlobServiceClient.from_connection_string(os.environ["AZURE_CONN_STR"])
    # blob_client = blob_service_client.get_blob_client(
    #     container="kdata-raw",
    #     blob=f"PLANIFICACION/POOL/ESCONDIDA/pool_proj.csv",
    # )
    # blob_data = blob_client.download_blob().readall()
    # blob_data = StringIO(blob_data.decode("latin-1"))
    blob_data = "DATA/PLAN/pool_proj.csv"
    df = pd.read_csv(blob_data)
    df = df.assign(
        equipo=df["equipo"].astype(str),
    )
    df.loc[df["arrival_week"].notnull(), "arrival_date"] = df.loc[df["arrival_week"].notnull()]["arrival_week"].map(
        lambda x: datetime.strptime(x + "-1", "%Y-W%W-%w")
    )

    return df
