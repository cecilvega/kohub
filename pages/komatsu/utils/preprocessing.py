import pandas as pd
import numpy as np


# Create 'prorrata_cost' column
def calculate_prorrata_cost(row):
    condition = (row["prorrata_component_hours"] >= row["mtbo_85_pct"]) & (
        row["prorrata_component_hours"] <= row["mtbo_105_pct"]
    )

    if condition:
        return row["standard_overhaul_cost"] * (
            1 + ((row["prorrata_component_hours"] - row["mtbo_85_pct"]) / row["mtbo_100_pct"])
        )
    else:
        return row["standard_overhaul_cost"] * (row["prorrata_component_hours"] / row["mtbo_85_pct"])


def enrich_cc(cc_df, standard_overhauls_df):
    df = cc_df.copy()
    df = df.assign(prorrata_year=df["changeout_date"].apply(lambda x: x.year if x.month >= 4 else x.year - 1))
    df = df.loc[df["prorrata_year"] >= 2024].reset_index(drop=True)

    prorrata_by_subcomponents = ["mp"]
    subcomponent_df = df.loc[df["component"].isin(prorrata_by_subcomponents)].merge(
        standard_overhauls_df,
        how="left",
        on=["prorrata_year", "component", "subcomponent"],
    )
    componrent_df = df.loc[~df["component"].isin(prorrata_by_subcomponents)].merge(
        standard_overhauls_df.drop(columns=["subcomponent"]),
        how="left",
        on=["prorrata_year", "component"],
    )
    df = pd.concat([subcomponent_df, componrent_df])
    df = df.assign(mtbo_85_pct=df["mtbo_100_pct"] * 0.85, mtbo_105_pct=df["mtbo_100_pct"] * 1.05)
    # Create 'prorrata_component_hours' column
    df["prorrata_component_hours"] = np.where(
        df["component_hours"] > df["mtbo_105_pct"],
        df["mtbo_105_pct"],
        df["component_hours"],
    )
    df["prorrata_cost"] = df.apply(calculate_prorrata_cost, axis=1)
    return df
    # Handle any potential errors by replacing them with 0
