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
    if os.environ.get("USERNAME") in ["cecilvega", "U1309565"]:
        blob_data = "DATA/pool_proj.csv"
    else:
        blob_service_client = BlobServiceClient(
            account_url=os.environ["AZURE_ACCOUNT_URL"],
            credential=os.environ["AZURE_SAS_TOKEN"],
        )
        blob_client = blob_service_client.get_blob_client(
            container=os.environ["AZURE_CONTAINER_NAME"],
            blob=f"{os.environ['AZURE_PREFIX']}/PLANIFICACION/POOL/pool_proj.csv",
        )
        blob_data = blob_client.download_blob().readall()
        blob_data = StringIO(blob_data.decode("latin-1"))

    df = pd.read_csv(blob_data)
    df = df.assign(
        equipo=df["equipo"].astype(str),
        # arrival_date=lambda x: np.where(
        #     x["arrival_week"].notnull(), x["arrival_week"].map(lambda x: datetime.strptime(x + "-1", "%Y-W%W-%w"))
        # ),
    )
    df.loc[df["arrival_week"].notnull(), "arrival_date"] = df.loc[df["arrival_week"].notnull()]["arrival_week"].map(
        lambda x: datetime.strptime(x + "-1", "%Y-W%W-%w")
    )
    df = df.assign(
        component=lambda x: x["component_code"]
        .str.strip(" ")
        .map(
            lambda x: {
                "bp": "blower",
                "cd": "cilindro_direccion",
                "st": "suspension_trasera",
                "cms": "conjunto_masa_suspension",
                "mt": "motor_traccion",
                "cl": "cilindro_direccion",
                "mp": "modulo_potencia",
            }[x]
        ),
    )
    return df


def get_weeks_and_comments(row, sheet):
    weeks = []
    comments = []
    row_idx = int(row.name.strip("N°"))
    col_idx = 1

    for col, value in row.items():
        # print(row_idx)
        if value == 1:
            weeks.append(col)
            cell = sheet[row_idx][col_idx]
            comments.append(cell.comment.text if cell.comment else "")
        col_idx += 1
    return pd.Series({"weeks": weeks, "comments": comments})


def idx_to_pool_slot(df):
    df = (
        df.rename_axis("pool_slot").reset_index().assign(pool_slot=lambda x: x["pool_slot"].str.strip("N°").astype(int))
    )
    return df


def extract_info(comment):
    equipo_match = re.search(r"Equipo:\s*(\d+)", comment)
    ns_match = re.search(r"NS:\s*(#+\w*-?\w*)", comment)
    ns = ns_match.group(1) if ns_match else None
    if ns:
        ns = re.sub(r"^#+", "#", ns)
    equipo = equipo_match.group(1) if equipo_match else None

    return equipo, ns


def get_end_week(row, sheet):
    weeks = []
    pool_changeout_types = []
    row_idx = int(row.name.strip("N°"))
    breakdown_colours = ["FFEDBFBB", "FFC5E0B4", "FFE88880"]

    for col_idx in range(0, row.__len__()):
        if col_idx > 2:
            prev_cell = sheet[row_idx][col_idx - 1]
            cell = sheet[row_idx][col_idx]
            if (
                (prev_cell.fill.fgColor.rgb != cell.fill.fgColor.rgb)
                & (prev_cell.value is None)
                & (prev_cell.fill.fgColor.rgb in breakdown_colours)
            ) | (
                (prev_cell.fill.start_color.theme != cell.fill.start_color.theme)
                & (prev_cell.value is None)
                & (prev_cell.fill.start_color.theme == 9)
            ):
                # | (
                #     (prev_cell.fill.fgColor.tint != cell.fill.fgColor.tint)
                #     & (prev_cell.fill.fgColor.tint != 0)
                #     & (prev_cell.value is None)
                #     # & (prev_cell.fill.fgColor.rgb in ["FFC5E0B4", "FFE88880"])
                # ):
                weeks.append(list(row.keys())[col_idx - 2])
                if prev_cell.fill.fgColor.rgb in breakdown_colours:
                    pool_changeout_types.append("I")
                else:
                    pool_changeout_types.append("P")

    return pd.Series({"weeks": weeks, "pool_changeout_type": pool_changeout_types})


def data_fixes(df):
    # Mal puesta la fecha de inicio de cambio de motor de tracción en el pool slot 6
    df.loc[
        (df["pool_slot"] == "6")
        & (df["component_code"] == "mt")
        & (df["equipo"] == "856")
        & (df["component_serial"] == "#WX14020007T"),
        "changeout_week",
    ] = "2024-W21"

    mask = (df["pool_slot"] == "2") & (df["component_code"] == "bp") & (df["changeout_week"] == "2023-W50")
    df.loc[mask, "equipo"] = "289"
    df.loc[mask, "component_serial"] = "#EE13070558"

    df.loc[
        (df["pool_slot"] == "2")
        & (df["component_code"] == "bp")
        & (df["equipo"] == "864")
        & (df["component_serial"] == "#EE14070950"),
        "changeout_week",
    ] = "2024-W19"

    df.loc[
        (df["pool_slot"] == "13")
        & (df["component_code"] == "bp")
        & (df["equipo"] == "851")
        & (df["component_serial"] == "#EE10040299"),
        "changeout_week",
    ] = "2024-W19"

    df.loc[
        (df["pool_slot"] == "10")
        & (df["component_code"] == "cd")
        & (df["equipo"] == "858")
        & (df["changeout_week"] == "2023-W34"),
        "component_serial",
    ] = "#73-LB36"

    df.loc[
        (df["pool_slot"] == "6")
        & (df["component_code"] == "cd")
        & (df["equipo"] == "870")
        & (df["component_serial"] == "#EMWH340"),
        "changeout_week",
    ] = "2024-W7"

    df.loc[
        (df["pool_slot"] == "7")
        & (df["component_code"] == "cd")
        & (df["equipo"] == "870")
        & (df["component_serial"] == "#EMYK00487"),
        "changeout_week",
    ] = "2024-W7"

    ###

    df = pd.concat(
        [
            df,
            pd.DataFrame.from_dict(
                {
                    "pool_slot": [
                        3
                        # , 7, 4
                    ],
                    "component_code": [
                        "mp"
                        # , "mp", "mp"
                    ],
                    "equipo": [
                        "852"
                        # , "320", "882"
                    ],
                    "changeout_week": [
                        "2024-W18"
                        # , "2024-W31", "2024-W32"
                    ],
                    "component_serial": [
                        "???"
                        # , "#217596-3", "#EE11100947"
                    ],
                    "arrival_week": [
                        "2024-W51"
                        # , "2024-W40", "2024-W46"
                    ],
                    "pool_changeout_type": [
                        "E"
                        # , "I", "I"
                    ],
                }
            ).assign(
                changeout_date=lambda x: x["changeout_week"].map(lambda x: datetime.strptime(x + "-1", "%Y-W%W-%w")),
                # arrival_date=lambda x: x["arrival_week"].map(lambda x: datetime.strptime(x + "-6", "%Y-W%W-%w")),
            ),
        ]
    )

    df = df.assign(arrival_date=df["arrival_week"].map(lambda x: datetime.strptime(x + "-6", "%Y-W%W-%w")))
    return df


def read_base_pool_proj_deprecated():
    blob_service_client = BlobServiceClient(
        account_url=os.environ["AZURE_ACCOUNT_URL"],
        credential=os.environ["AZURE_SAS_TOKEN"],
    )
    blob_client = blob_service_client.get_blob_client(
        container=os.environ["AZURE_CONTAINER_NAME"],
        blob=f"{os.environ['AZURE_PREFIX']}/PLANIFICACION/POOL/2023.01 Pool Componentes MEL Planificadores.xlsx",
    )
    blob_data = blob_client.download_blob()
    blob_data = BytesIO(blob_data.readall())
    start_column = "F"
    end_column = "EF"
    components = {
        "bp": {"start_row": 20, "end_row": 33},
        "cd": {"start_row": 40, "end_row": 56},
        "mt": {"start_row": 98, "end_row": 110},
        "st": {"start_row": 63, "end_row": 75},
        "cms": {"start_row": 80, "end_row": 92},
        "cl": {"start_row": 115, "end_row": 128},
        "mp": {"start_row": 146, "end_row": 153},
    }

    frames = []
    for component in components:

        wb = openpyxl.load_workbook(blob_data, data_only=True)

        sheet = wb["PROYECCIÓN"]

        start_row, end_row = components[component].values()
        # Create a DataFrame from the Excel data
        sheet = sheet[f"{start_column}{start_row}:{end_column}{end_row}"]
        data = []  # .iter_rows(min_row=20, values_only=True)
        for row in sheet:
            data.append([cell.value for cell in row])

        df = pd.DataFrame(data, columns=[cell.value for cell in sheet[1]])
        df.set_index(df.columns[0], inplace=True)
        df = df.iloc[1:]
        # Generate date range
        date_range = pd.date_range(start="2023-07-03", end="2025-12-31", freq="W-MON")

        # Create the list of week strings
        week_list = [f"{date.isocalendar()[0]}-W{date.isocalendar()[1]}" for date in date_range]

        df.columns = week_list[:-1]
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
            arrival_date=arrivals_df["arrival_week"].map(lambda x: datetime.strptime(x + "-6", "%Y-W%W-%w"))
        )

        df = pd.merge_asof(
            changeouts_df.sort_values("changeout_date"),
            arrivals_df.sort_values("arrival_date"),
            by="pool_slot",
            left_on="changeout_date",
            right_on="arrival_date",
            direction="forward",
        ).assign(component_code=component)
        frames.append(df)

    df = pd.concat(frames)
    df = data_fixes(df)

    return df
