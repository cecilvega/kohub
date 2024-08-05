import pandas as pd
from datetime import datetime
import numpy as np


def add_arrival_date(df: pd.DataFrame):
    df = df.assign(
        ohv_normal=df["component_code"].map(
            lambda x: {
                "bp": 51,
                "cd": 46,
                "st": 65,
                "cms": 64,
                "mt": 74,
                "cl": 75,
                "mp": 64,
            }[x]
        ),
        ohv_unplanned=df["component_code"].map(
            lambda x: {
                "bp": 101,
                "cd": 96,
                "st": 125,
                "cms": 124,
                "mt": 134,
                "cl": 135,
                "mp": 114,
            }[x]
        ),
    )
    df = df.assign(
        arrival_date=df["changeout_date"]
        + np.where(
            df["pool_changeout_type"] == "P",
            pd.to_timedelta(df["ohv_normal"], "D"),
            pd.to_timedelta(df["ohv_unplanned"], "D"),
        )
    )
    df = df.assign(arrival_week=df["arrival_date"].dt.strftime("%G-W%V")).drop(columns=["ohv_normal", "ohv_unplanned"])
    return df


def find_available_pool_slot(pool_slots_df, changeout_date):
    # Group by pool_slot and find the latest event for each
    latest_events = (
        pool_slots_df.groupby("pool_slot")[["pool_slot", "changeout_date", "arrival_date"]]
        .apply(
            lambda x: x.loc[
                (x["changeout_date"].idxmax() if not x["changeout_date"].isna().all() else x["arrival_date"].idxmax())
            ]
        )
        .reset_index(drop=True)
    )

    # Filter for available slots
    available_slots = latest_events[
        ((latest_events["changeout_date"] < changeout_date) & (latest_events["arrival_date"] < changeout_date))
        | (latest_events["arrival_date"] < changeout_date)
    ]

    if available_slots.empty:
        return None

    return available_slots  # .loc[available_slots["days_unchanged"].idxmax()]


def find_most_time_unchanged_slot(df, changeout_date):
    # Find the slot with the most time unchanged
    df["days_unchanged"] = (changeout_date - df["arrival_date"]).dt.days
    return df.loc[df["days_unchanged"].idxmax()]


def allocate_components(cc_df, pool_slots_df):
    # Sort cc_df by changeout_date
    cc_df = cc_df.sort_values("changeout_date")

    for _, changeout in cc_df.iterrows():
        available_slots_df = find_available_pool_slot(pool_slots_df, changeout["changeout_date"])
        print(changeout)
        available_slot = find_most_time_unchanged_slot(available_slots_df, changeout["changeout_date"])
        if available_slot is None:
            print(f"Unable to find an available pool slot for changeout on {changeout['changeout_date']}")
            # return pool_slots_df
        # Add new row to pool_slots_df
        new_row = changeout.copy()
        new_row["pool_slot"] = available_slot["pool_slot"]
        new_row["arrival_date"] = pd.NaT  # This will be set when the component returns

        new_row = pd.DataFrame([new_row])
        new_row = add_arrival_date(new_row)

        pool_slots_df = pd.concat([pool_slots_df, new_row], ignore_index=True)

        # Sort the dataframe to maintain chronological order
        pool_slots_df = pool_slots_df.sort_values("changeout_date")
    return pool_slots_df


def generate_pool_projection(cc_df, pool_proj_df):
    merge_columns = ["equipo", "component_code", "component_serial", "changeout_week"]

    pool_slots_df = pd.merge(
        pool_proj_df,  # .query("component_code == 'mt'"),
        cc_df,
        on=merge_columns,
        how="left",
        suffixes=("_proj", ""),
    )
    pool_slots_df = pool_slots_df.assign(
        pool_changeout_type=np.where(
            pool_slots_df["pool_changeout_type"].isnull(),
            pool_slots_df["pool_changeout_type_proj"],
            pool_slots_df["pool_changeout_type"],
        ),
    ).drop(columns="pool_changeout_type_proj")
    # assert pool_slots_df["changeout_date"].notnull().all()
    pool_slots_df = pool_slots_df.dropna(subset=["changeout_date"])
    # New changes that were not added into the pool
    new_cc_df = (
        pd.merge(
            cc_df.loc[cc_df["changeout_date"] >= datetime(2024, 6, 1)],
            pool_proj_df[merge_columns],
            on=merge_columns,
            how="left",
            indicator=True,
        )
        .query("_merge == 'left_only'")
        .drop(columns="_merge")
        .assign(pool_changeout_type=lambda x: x["pool_changeout_type"].fillna("P"))
    )

    df = allocate_components(new_cc_df, pool_slots_df)
    return df
