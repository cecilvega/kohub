import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional
import pandas as pd
import numpy as np
from enum import Enum
from typing import Dict, List
from dataclasses import dataclass


@dataclass(frozen=True)
class ComponentCode:
    code: str
    name: str
    planned_ovh_days: int
    unplanned_ovh_days: int

    def __str__(self):
        return self.code


def find_available_pool_slot(pool_slots_df: pd.DataFrame, changeout: pd.Series) -> pd.DataFrame:
    """
    Find available pool slots for a given changeout.

    Args:
        pool_slots_df (pd.DataFrame): DataFrame containing pool slot information.
        changeout (pd.Series): Series containing changeout information.

    Returns:
        pd.DataFrame: DataFrame of available pool slots.
    """
    df = (
        pool_slots_df.loc[pool_slots_df["component_code"] == changeout["component_code"]]
        .sort_values(["pool_slot", "changeout_date"])
        .drop_duplicates(subset=["pool_slot"], keep="last")
    )
    df = (
        df[
            (df["component_code"] == changeout["component_code"])
            & (df["changeout_date"] < changeout["changeout_date"])
            & (df["arrival_date"].notnull())
            & (df["arrival_date"] < changeout["changeout_date"] - pd.Timedelta(days=0))
        ]
        .sort_values("changeout_date")
        .drop_duplicates(subset=["pool_slot", "component_code"], keep="last")
    )
    # df = pool_slots_df.copy()

    # df = (
    #     df.loc[(df["arrival_date"].isnull()) & (df["arrival_date_proj"] < changeout["changeout_date"])]
    #     .drop(columns=["arrival_date"])
    #     .sort_values("changeout_date")
    #     .reset_index(drop=True)
    # )

    return df


class ComponentAllocation:
    BP = ComponentCode("bp", "Blower", 51, 101)
    CD = ComponentCode("cd", "Cilindro Dirección", 46, 96)
    ST = ComponentCode("st", "Suspensión Trasera", 65, 125)
    CMS = ComponentCode("cms", "CMSD", 64, 124)
    MT = ComponentCode("mt", "Motor Tracción", 74, 134)
    CL = ComponentCode("cl", "Cilindro Levante", 75, 135)
    MP = ComponentCode("mp", "Módulo Potencia", 110, 170)

    COMPONENT_CODES = [BP, CD, ST, CMS, MT, CL, MP]

    def __init__(
        self,
        cc_df: pd.DataFrame,
        pool_proj_df: pd.DataFrame,
        arrivals_df: pd.DataFrame,
    ):

        cc_df = self.priority_sort(cc_df)
        cc_df = cc_df.drop_duplicates(subset=["equipo", "component_code", "position", "changeout_date"])
        cc_df = cc_df[cc_df["component_code"].isin([c.code for c in self.COMPONENT_CODES])]
        pool_proj_df = pool_proj_df[pool_proj_df["component_code"].isin([c.code for c in self.COMPONENT_CODES])]

        # debug_components = ["mp", "cd"]

        self.cc_df = cc_df.reset_index(drop=True)
        self.pool_proj_df = pool_proj_df.reset_index(drop=True)
        self.arrivals_df = arrivals_df.reset_index(drop=True)
        self.arrivals_df = self.get_next_arrivals()
        self.missing_cc_df = None
        self.pool_slots_df = None

    def get_next_arrivals(self):
        df = self.arrivals_df.copy()
        df = df.loc[df["arrival_date"] >= pd.Timestamp(2024, 6, 1)].reset_index(drop=True)
        merge_columns = ["component_code", "arrival_week"]
        df = pd.merge(
            df.drop(columns=["arrival_date"]),
            self.pool_proj_df[merge_columns],
            on=merge_columns,
            how="left",
            indicator=True,
        )
        df = df.loc[df["_merge"] == "left_only"].drop(columns="_merge")
        df = df.assign(
            arrival_date=lambda x: x["arrival_week"].map(lambda x: datetime.strptime(x + "-1", "%Y-W%W-%w")),
        )
        df["pool_slot"] = None
        return df

    def add_arrival_date_proj(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add arrival date to the DataFrame based on component code and changeout type.

        Args:
            df (pd.DataFrame): Input DataFrame containing component information.

        Returns:
            pd.DataFrame: DataFrame with added arrival date information.
        """

        def get_ovh_days(row):
            component = next(c for c in self.COMPONENT_CODES if c.code == row["component_code"])
            if component == self.MP:
                if row["subcomponente"] in ["Alternador Principal", "Radiador"]:
                    return 64 if row["pool_changeout_type"] == "P" else 114
            return component.planned_ovh_days if row["pool_changeout_type"] == "P" else component.unplanned_ovh_days

        df["ovh_days"] = df.apply(get_ovh_days, axis=1)
        df["arrival_date_proj"] = df["changeout_date"] + pd.to_timedelta(df["ovh_days"], "D")
        df.loc[df["pool_changeout_type"] == "E", "arrival_date_proj"] = df["changeout_date"] + pd.to_timedelta(200, "D")
        df["arrival_week_proj"] = df["arrival_date_proj"].dt.strftime("%G-W%V")

        return df.drop(columns=["ovh_days"])

    def find_most_time_unchanged_slot(self, df: pd.DataFrame, changeout_date: pd.Timestamp) -> pd.Series:
        """
        Find the slot that has been unchanged for the longest time.

        Args:
            df (pd.DataFrame): DataFrame containing slot information.
            changeout_date (pd.Timestamp): Date of the changeout.

        Returns:
            pd.Series: Series containing information about the most time unchanged slot.
        """
        df = df.assign(days_unchanged=(changeout_date - df["arrival_date"]).dt.days)

        return df.loc[df["days_unchanged"].idxmax()]

    def priority_sort(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Sort the DataFrame based on component and subcomponent priorities.

        Args:
            df (pd.DataFrame): Input DataFrame to be sorted.

        Returns:
            pd.DataFrame: Sorted DataFrame.
        """
        priority_map = {
            self.MT.code: {"MOTOR TRACCIÓN": 1},
            self.CMS.code: {"Suspension Delantera": 1},
            self.MP.code: {"MOTOR": 1, "Alternador Principal": 2, "Radiador": 3},
        }
        default_priority = 999

        def get_priority(row):
            component_priorities = priority_map.get(row["component_code"], {})
            for subcomponent, priority in component_priorities.items():
                if subcomponent in row["subcomponente"]:
                    return priority
            return default_priority

        df["subcomponent_priority"] = df.apply(get_priority, axis=1)
        df = (
            df.sort_values(["equipo", "changeout_date", "component_code", "position", "subcomponent_priority"])
            .reset_index(drop=True)
            .drop(columns=["subcomponent_priority"])
        )
        return df

    def add_arrival_date(self, df: pd.DataFrame, changeout):
        # Find the earliest unmerged arrival_date
        earliest_arrival = self.arrivals_df[
            (self.arrivals_df["pool_slot"].isnull())
            & (self.arrivals_df["component_code"] == changeout["component_code"])
        ]["arrival_date"].min()
        earliest_arrival_df = self.arrivals_df.loc[
            (self.arrivals_df["arrival_date"] == earliest_arrival)
            & (self.arrivals_df["component_code"] == changeout["component_code"])
        ]

        # Merge asof for this arrival_date
        earliest_arrival_df = pd.merge_asof(
            earliest_arrival_df[["component_code", "arrival_date"]].rename(
                columns={"arrival_date": "earliest_arrival_date"}
            ),
            df.loc[df["component_code"] == changeout["component_code"]]
            .sort_values(["pool_slot", "changeout_date"])
            .drop_duplicates(subset=["pool_slot"], keep="last")
            .sort_values("arrival_date_proj")
            .reset_index(drop=True)[["component_code", "arrival_date_proj", "changeout_date", "pool_slot"]],
            by="component_code",
            left_on="earliest_arrival_date",
            right_on="arrival_date_proj",
            direction="nearest",
        )
        for idx, row in earliest_arrival_df.iterrows():
            mask = (df["changeout_date"] == row["changeout_date"]) & (df["component_code"] == row["component_code"])
            df.loc[mask, "arrival_date"] = earliest_arrival
            df.loc[mask, "merged"] = True

        self.arrivals_df.loc[self.arrivals_df["arrival_date"] == earliest_arrival, "pool_slot"] = earliest_arrival_df[
            "pool_slot"
        ].iloc[0]

        return df

    def allocate_components(self) -> pd.DataFrame:
        """
        Allocate components to available pool slots.

        Args:
            cc_df (pd.DataFrame): DataFrame containing component changeout information.
            pool_slots_df (pd.DataFrame): DataFrame containing pool slot information.

        Returns:
            pd.DataFrame: Updated pool slots DataFrame with allocated components.
        """
        cc_df = self.missing_cc_df.sort_values(["component_code", "changeout_date"]).reset_index(drop=True)
        df = self.pool_slots_df.copy()
        i = 0
        for component in cc_df["component_code"].unique():
            for _, changeout in cc_df.loc[cc_df["component_code"] == component].iterrows():

                if i == 9:
                    return df
                i = i + 1
                print(changeout)
                available_slots_df = find_available_pool_slot(df, changeout)
                # print(available_slots_df)
                if not available_slots_df.empty:
                    # print(available_slots_df)
                    available_slot = self.find_most_time_unchanged_slot(available_slots_df, changeout["changeout_date"])
                    # mask = (
                    #     (df["pool_slot"] == available_slot["pool_slot"])
                    #     & (df["component_code"] == available_slot["component_code"])
                    #     & (df["changeout_date"] == available_slot["changeout_date"])
                    # )
                    # df.loc[mask, "arrival_date"] = df.loc[mask, "arrival_date_proj"]
                else:
                    # print(df)
                    df = self.add_arrival_date(df, changeout)
                    # print(df)
                    available_slots_df = find_available_pool_slot(df, changeout)
                    self.df = df
                    self.changeout = changeout
                    self.available_slots_df = available_slots_df
                    assert not available_slots_df.empty, changeout
                    available_slot = self.find_most_time_unchanged_slot(available_slots_df, changeout["changeout_date"])

                # return df
                new_row = changeout.copy()
                new_row["pool_slot"] = available_slot["pool_slot"]

                new_row = pd.DataFrame([new_row])
                new_row = self.add_arrival_date_proj(new_row)
                # new_row["arrival_date"] = new_row["arrival_date_proj"]

                df = pd.concat([df, new_row], ignore_index=True)
                df = df.sort_values("changeout_date")

        return df

    def get_base_pool_slots(self) -> pd.DataFrame:
        merge_columns = ["equipo", "component_code", "component_serial", "changeout_week"]

        df = pd.merge(self.pool_proj_df, self.cc_df, on=merge_columns, how="left", suffixes=("_proj", ""))

        df["pool_changeout_type"] = df["pool_changeout_type"].fillna(df["pool_changeout_type_proj"])
        df = df.drop(columns="pool_changeout_type_proj")

        df["changeout_date"] = df["changeout_date"].fillna(df["changeout_date_proj"])
        df = df.drop(columns="changeout_date_proj").reset_index(drop=True)
        df = df.pipe(self.add_arrival_date_proj)
        # Para cambios esperando, blockear fecha de llegada con la proyección de alto tiempo
        df = df.assign(
            arrival_date=np.where(df["pool_changeout_type"] == "E", df["arrival_date_proj"], df["arrival_date"])
        )
        df["merged"] = False
        return df

    def get_missing_changeouts(self) -> pd.DataFrame:
        merge_columns = ["equipo", "component_code", "component_serial", "changeout_week"]
        df = self.cc_df[self.cc_df["changeout_date"] >= pd.Timestamp(2024, 6, 1)]
        df = df[df["pool_changeout_type"] != "N"]

        df = pd.merge(df, self.pool_proj_df[merge_columns], on=merge_columns, how="left", indicator=True)
        df = df[df["_merge"] == "left_only"].drop(columns="_merge")
        df["pool_changeout_type"] = df["pool_changeout_type"].fillna("P")
        return df

    def generate_pool_projection(self) -> pd.DataFrame:
        """
        Generate pool projection based on component changeouts and available pool slots.

        Returns:
            pd.DataFrame: Generated pool projection.
        """

        self.missing_cc_df = self.get_missing_changeouts()
        self.pool_slots_df = self.get_base_pool_slots()

        df = self.allocate_components()

        df[["changeout_date", "arrival_date"]] = df[["changeout_date", "arrival_date"]].apply(pd.to_datetime)

        df["componente"] = df["component_code"].map({c.code: c.name for c in self.COMPONENT_CODES})
        df = df.reset_index(drop=True)
        df = df.assign(arrival_date=np.where(df["arrival_date"].isnull(), df["arrival_date_proj"], df["arrival_date"]))
        return df
