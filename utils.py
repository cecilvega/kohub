import pandas as pd
import openpyxl
import re
from datetime import datetime
from pathlib import Path
import os
from io import BytesIO
from azure.storage.blob import BlobServiceClient


# Function to get weeks and comments where value is 1
def get_weeks_and_comments(row, sheet):
    weeks = []
    comments = []
    row_idx = int(row.name.strip("N°"))
    col_idx = 1
    for col, value in row.items():
        if value == 1:
            weeks.append(col)
            cell = sheet[row_idx + 1][col_idx]
            comments.append(cell.comment.text if cell.comment else "")
        col_idx += 1
    return pd.Series({"weeks": weeks, "comments": comments})


def get_end_week(row, sheet):
    weeks = []
    pool_changeout_types = []
    row_idx = int(row.name.strip("N°"))
    for col_idx in range(0, row.__len__()):
        if col_idx > 2:
            prev_cell = sheet[row_idx + 1][col_idx - 1]
            cell = sheet[row_idx + 1][col_idx]
            if (
                (prev_cell.fill.fgColor.rgb != cell.fill.fgColor.rgb)
                & (prev_cell.value is None)
                & (prev_cell.fill.fgColor.rgb in ["FFEDBFBB", "FFC5E0B4", "FFE88880"])
                # & (prev_cell.fill.fgColor.rgb in ["FFC5E0B4", "FFE88880"])
            ):
                weeks.append(list(row.keys())[col_idx - 2])
                if prev_cell.fill.fgColor.rgb in ["FFEDBFBB", '"FFE88880"']:
                    pool_changeout_types.append("I")
                else:
                    pool_changeout_types.append("P")

    return pd.Series({"weeks": weeks, "pool_changeout_type": pool_changeout_types})


def idx_to_pool_slot(df):
    df = (
        df.reset_index()
        .rename(columns={"index": "pool_slot"})
        .assign(pool_slot=lambda x: x["pool_slot"].str.strip("N°"))
    )
    return df


# Function to extract information from comments
def extract_info(comment):
    equipo_match = re.search(r"Equipo:\s*(\d+)", comment)
    ns_match = re.search(r"NS:\s*(#\w*-?\w*)", comment)

    equipo = equipo_match.group(1) if equipo_match else None
    ns = ns_match.group(1) if ns_match else None

    return equipo, ns


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
        ).assign(component=file.split("-")[-1].split(".")[0])
        frames.append(df)
    df = pd.concat(frames)
    return df
