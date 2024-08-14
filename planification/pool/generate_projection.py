import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional


def add_arrival_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add arrival date to the DataFrame based on component code and changeout type.
    """
    OHV_NORMAL: Dict[str, int] = {"bp": 51, "cd": 46, "st": 65, "cms": 64, "mt": 74, "cl": 75, "mp": 64}
    OHV_UNPLANNED: Dict[str, int] = {"bp": 101, "cd": 96, "st": 125, "cms": 124, "mt": 134, "cl": 135, "mp": 114}

    df = df.assign(
        ohv_normal=df["component_code"].map(OHV_NORMAL), ohv_unplanned=df["component_code"].map(OHV_UNPLANNED)
    )

    df["arrival_date"] = df["changeout_date"] + np.where(
        df["pool_changeout_type"] == "P",
        pd.to_timedelta(df["ohv_normal"], "D"),
        pd.to_timedelta(df["ohv_unplanned"], "D"),
    )

    df["arrival_week"] = df["arrival_date"].dt.strftime("%G-W%V")
    return df.drop(columns=["ohv_normal", "ohv_unplanned"])


def find_available_pool_slot(pool_slots_df: pd.DataFrame, changeout_date: pd.Timestamp) -> Optional[pd.DataFrame]:
    """
    Find available pool slots for a given changeout date.
    """
    latest_events = (
        pool_slots_df.groupby("pool_slot")[["pool_slot", "changeout_date", "arrival_date"]]
        .apply(
            lambda x: x.loc[
                x["changeout_date"].idxmax() if not x["changeout_date"].isna().all() else x["arrival_date"].idxmax()
            ]
        )
        .reset_index(drop=True)
    )

    available_slots = latest_events[
        ((latest_events["changeout_date"] < changeout_date) & (latest_events["arrival_date"] < changeout_date))
        | (latest_events["arrival_date"] < changeout_date)
    ]

    return available_slots if not available_slots.empty else None


def find_most_time_unchanged_slot(df: pd.DataFrame, changeout_date: pd.Timestamp) -> pd.Series:
    """
    Find the slot with the most time unchanged.
    """
    df["days_unchanged"] = (changeout_date - df["arrival_date"]).dt.days
    return df.loc[df["days_unchanged"].idxmax()]


def allocate_components(cc_df: pd.DataFrame, pool_slots_df: pd.DataFrame) -> pd.DataFrame:
    """
    Allocate components to available pool slots.
    """
    cc_df = cc_df.sort_values("changeout_date")

    for _, changeout in cc_df.iterrows():
        available_slots_df = find_available_pool_slot(pool_slots_df, changeout["changeout_date"])
        if available_slots_df is None:

            print(
                f"Unable to find an available pool slot for changeout on "
                f"{changeout[['component_code', 'changeout_date', 'equipo', 'component_serial']]}"
            )
            continue

        available_slot = find_most_time_unchanged_slot(available_slots_df, changeout["changeout_date"])
        new_row = changeout.copy()
        new_row["pool_slot"] = available_slot["pool_slot"]
        new_row["arrival_date"] = pd.NaT

        new_row = pd.DataFrame([new_row])
        new_row = add_arrival_date(new_row)

        pool_slots_df = pd.concat([pool_slots_df, new_row], ignore_index=True)
        pool_slots_df = pool_slots_df.sort_values("changeout_date")

    return pool_slots_df


def priority_sort(df):
    priority_map = {
        "mt": {
            "MOTOR TRACCIÓN": 1,
        },
        "cms": {
            "Suspension Delantera": 1,
        },
        "mp": {
            "MOTOR": 1,
            "Alternador Principal": 2,
            "Radiador": 3,
        },  # MOTOR is priority 1
    }
    default_priority = 999  # High number for lowest priority

    def get_priority(row):
        component_priorities = priority_map.get(row["component_code"], {})
        for subcomponent, priority in component_priorities.items():
            if subcomponent in row["subcomponente"]:
                return priority
        return default_priority

    df["subcomponent_priority"] = df.apply(get_priority, axis=1)
    return df


def generate_pool_projection(
    cc_df: pd.DataFrame, pool_proj_df: pd.DataFrame, available_components: list
) -> pd.DataFrame:
    """
    Generate pool projection based on component changeouts and existing pool projections.
    """
    # Assuming cc_df is your original DataFrame
    cc_df = priority_sort(cc_df)

    # Sort the DataFrame by changeout_date, component_code, and priority
    cc_df = cc_df.sort_values(
        ["equipo", "changeout_date", "component_code", "position", "subcomponent_priority"]
    ).drop_duplicates(subset=["equipo", "component_code", "position", "changeout_date"])

    cc_df = cc_df.loc[cc_df["component_code"].isin(available_components)].reset_index(drop=True)
    pool_proj_df = pool_proj_df.loc[pool_proj_df["component_code"].isin(available_components)].reset_index(drop=True)

    merge_columns = ["equipo", "component_code", "component_serial", "changeout_week"]

    pool_slots_df = pd.merge(pool_proj_df, cc_df, on=merge_columns, how="left", suffixes=("_proj", ""))

    pool_slots_df["pool_changeout_type"] = pool_slots_df["pool_changeout_type"].fillna(
        pool_slots_df["pool_changeout_type_proj"]
    )
    pool_slots_df = pool_slots_df.drop(columns="pool_changeout_type_proj")
    pool_slots_df = pool_slots_df.assign(
        changeout_date=np.where(
            pool_slots_df["changeout_date"].isnull(),
            pool_slots_df["changeout_date_proj"],
            pool_slots_df["changeout_date"],
        )
    )
    assert pool_slots_df["changeout_date"].notnull().all()
    # pool_slots_df = pool_slots_df.dropna(subset=["changeout_date"])

    missing_cc_df = cc_df[cc_df["changeout_date"] >= datetime(2024, 6, 1)]
    missing_cc_df = (
        pd.merge(
            missing_cc_df,
            pool_proj_df[merge_columns],
            on=merge_columns,
            how="left",
            indicator=True,
        )
        .query("_merge == 'left_only'")
        .drop(columns="_merge")
        .assign(pool_changeout_type=lambda x: x["pool_changeout_type"].fillna("P"))
    )
    df = allocate_components(missing_cc_df, pool_slots_df).reset_index(drop=True)
    # df = pd.concat([pool_slots_df, df]).reset_index(drop=True)

    df[["changeout_date", "arrival_date"]] = df[["changeout_date", "arrival_date"]].apply(
        lambda x: pd.to_datetime(x, format="%Y-%m-%d")
    )

    df = df.assign(
        componente=df["component_code"].map(
            lambda x: {
                "bp": "Blower",
                "cd": "Cilindro Dirección",
                "st": "Suspensión Trasera",
                "cms": "CMSD",
                "mt": "Motor Tracción",
                "cl": "Cilindro Levante",
                "mp": "Módulo Potencia",
            }[x]
        )
    )
    return df
