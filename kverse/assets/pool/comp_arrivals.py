import os
from datetime import datetime
from io import BytesIO

import openpyxl
import pandas as pd
from azure.storage.blob import BlobServiceClient
from datetime import timedelta


# Function to get the end date of a week
def get_week_end_date(week_str):
    year, week = week_str.split("-W")
    # Create a datetime object for the first day of the year
    first_day = datetime(int(year), 1, 1)
    # Calculate the start of the week (Monday)
    start_of_week = first_day + timedelta(days=(int(week) - 1) * 7 - first_day.weekday())
    # Calculate the end of the week (Sunday)
    end_of_week = start_of_week + timedelta(days=6)
    return end_of_week.date()


def read_pool_component_arrivals():

    blob_service_client = BlobServiceClient(
        account_url=os.environ["AZURE_ACCOUNT_URL"],
        credential=os.environ["AZURE_SAS_TOKEN"],
    )
    blob_client = blob_service_client.get_blob_client(
        container=os.environ["AZURE_CONTAINER_NAME"],
        blob=f"{os.environ['AZURE_PREFIX']}/PLANIFICACION/POOL/Pool Componente MEL.xlsx",
    )
    blob_data = blob_client.download_blob()
    blob_data = BytesIO(blob_data.readall())
    # Read the Excel file
    wb = openpyxl.load_workbook(blob_data, data_only=False)
    sheet = wb.active

    # Create a DataFrame from the Excel data
    data = []
    for row in sheet.iter_rows(
        min_row=36,
        max_row=43,
        values_only=True,
    ):
        data.append(row)

    df = pd.DataFrame(data, columns=[cell.value for cell in sheet[1]])

    df = df.dropna(how="all", axis=1)
    df.columns = df.iloc[0, :]
    df = df.iloc[1:, 1 : 2 + 52 * 4]

    # Generate date range
    date_range = pd.date_range(start="2022-01-01", end="2025-12-31", freq="W-MON")

    # Create the list of week strings
    week_list = [f"{date.isocalendar()[0]}-W{date.isocalendar()[1]:02d}" for date in date_range]
    week_list = ["componente", *week_list[0 : 4 * 52]]
    df.columns = week_list
    df = df.dropna(how="all", axis=1)

    # Melt the dataframe
    df_melted = df.melt(id_vars=["componente"], var_name="arrival_week", value_name="n_components").dropna()
    # Convert n_components to integer
    df_melted["n_components"] = df_melted["n_components"].astype(int)

    # Apply the expand_rows function and reset the index
    df_melted["arrived_component_idx"] = df_melted.apply(lambda row: list(range(row["n_components"])), axis=1)
    df = df_melted.explode("arrived_component_idx")

    df = df.sort_values(["componente", "arrival_week"]).reset_index(drop=True)
    df = df.assign(
        component_code=lambda x: x["componente"]
        .str.strip(" ")
        .map(
            lambda x: {
                "Blower Parrilla": "bp",
                "Cilindro Dirección": "cd",
                "Suspensión Trasera": "st",
                "Suspensión Delantera": "cms",
                "Motor Tracción": "mt",
                "Cilindro Levante": "cl",
                "Modulo Potencia": "mp",
            }[x]
        ),
    ).drop(columns=["componente"])

    # Apply the function to create a new column
    df["arrival_date"] = pd.to_datetime(df["arrival_week"].apply(get_week_end_date))
    return df
