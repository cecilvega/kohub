import pandas as pd
import openpyxl
import re
from datetime import datetime
from pathlib import Path
import os
from io import BytesIO
from azure.storage.blob import BlobServiceClient


def data_fixes(df):
    # Mal puesta la fecha de inicio de cambio de motor de tracción en el pool slot 6
    df.loc[
        (df["pool_slot"] == "6")
        & (df["component_code"] == "mt")
        & (df["equipo"] == "856")
        & (df["component_serial"] == "#WX14020007T"),
        "changeout_week",
    ] = "2024-W21"
    return df


def read_archived_pool_proj():
    blob_service_client = BlobServiceClient(
        account_url=os.environ["AZURE_ACCOUNT_URL"],
        credential=os.environ["AZURE_SAS_TOKEN"],
    )

    container_client = blob_service_client.get_container_client(os.environ["AZURE_CONTAINER_NAME"])
    blob_list = container_client.list_blobs(
        name_starts_with=f"{os.environ['AZURE_PREFIX']}/PLANIFICACION/POOL/ARCHIVED_PLAN"
    )
    blob_list = [f.name for f in blob_list]
    frames = []
    for file in blob_list:

        # Read the Excel file
        blob_client = blob_service_client.get_blob_client(
            container=os.environ["AZURE_CONTAINER_NAME"],
            blob=file,
        )
        blob_data = blob_client.download_blob()
        blob_data = BytesIO(blob_data.readall())
        wb = openpyxl.load_workbook(blob_data, data_only=True)

        sheet = wb.active

        # Create a DataFrame from the Excel data
        data = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            data.append(row)

        df = pd.DataFrame(data, columns=[cell.value for cell in sheet[1]])
        df.set_index(df.columns[0], inplace=True)

        # Process the dataframe
        changeouts_df = (
            df.apply(lambda x: get_weeks_and_comments(x, sheet), axis=1)
            .explode(["weeks", "comments"])
            .rename(columns={"weeks": "changeout_week"})
            .pipe(idx_to_pool_slot)
        )

        # Extract information from comments
        changeouts_df[["equipo", "component_serial"]] = changeouts_df["comments"].apply(
            lambda x: pd.Series(extract_info(x))
        )

        changeouts_df = changeouts_df.drop(columns=["comments"]).assign(
            changeout_date=changeouts_df["changeout_week"].map(lambda x: datetime.strptime(x + "-1", "%Y-W%W-%w"))
        )
        arrivals_df = (
            df.apply(lambda x: get_end_week(x, sheet), axis=1)
            .explode(["weeks", "pool_changeout_type"])
            .rename(columns={"weeks": "arrival_week"})
            .pipe(idx_to_pool_slot)
        )
        arrivals_df = arrivals_df.assign(
            arrival_date=arrivals_df["arrival_week"].map(lambda x: datetime.strptime(x + "-1", "%Y-W%W-%w"))
        )

        df = pd.merge_asof(
            changeouts_df.sort_values("changeout_date"),
            arrivals_df.sort_values("arrival_date"),
            by="pool_slot",
            left_on="changeout_date",
            right_on="arrival_date",
            direction="forward",
        ).assign(component_code=file.split("-")[-1].split(".")[0])
        frames.append(df)

    df = pd.concat(frames)
    df = data_fixes(df)
    return df
