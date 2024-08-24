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
    ):
        self.cc_df = cc_df
        self.pool_proj_df = pool_proj_df
        self.missing_cc_df = None
        self.pool_slots_df = None

    def add_arrival_date(self, df: pd.DataFrame) -> pd.DataFrame:
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
        df["arrival_date"] = df["changeout_date"] + pd.to_timedelta(df["ovh_days"], "D")
        df.loc[df["pool_changeout_type"] == "E", "arrival_date"] = df["changeout_date"] + pd.to_timedelta(200, "D")
        df["arrival_week"] = df["arrival_date"].dt.strftime("%G-W%V")

        return df.drop(columns=["ovh_days"])

    def find_available_pool_slot(self, pool_slots_df: pd.DataFrame, changeout: pd.Series) -> pd.DataFrame:
        """
        Find available pool slots for a given changeout.

        Args:
            pool_slots_df (pd.DataFrame): DataFrame containing pool slot information.
            changeout (pd.Series): Series containing changeout information.

        Returns:
            pd.DataFrame: DataFrame of available pool slots.
        """
        return (
            pool_slots_df[
                (pool_slots_df["component_code"] == changeout["component_code"])
                & (pool_slots_df["changeout_date"] < changeout["changeout_date"])
            ]
            .sort_values("changeout_date")
            .drop_duplicates(subset=["pool_slot", "component_code"], keep="last")
        )

    def find_most_time_unchanged_slot(self, df: pd.DataFrame, changeout_date: pd.Timestamp) -> pd.Series:
        """
        Find the slot that has been unchanged for the longest time.

        Args:
            df (pd.DataFrame): DataFrame containing slot information.
            changeout_date (pd.Timestamp): Date of the changeout.

        Returns:
            pd.Series: Series containing information about the most time unchanged slot.
        """
        df["days_unchanged"] = (changeout_date - df["arrival_date"]).dt.days
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
        return df.sort_values(["equipo", "changeout_date", "component_code", "position", "subcomponent_priority"])

    def allocate_components(self, cc_df: pd.DataFrame, pool_slots_df: pd.DataFrame) -> pd.DataFrame:
        """
        Allocate components to available pool slots.

        Args:
            cc_df (pd.DataFrame): DataFrame containing component changeout information.
            pool_slots_df (pd.DataFrame): DataFrame containing pool slot information.

        Returns:
            pd.DataFrame: Updated pool slots DataFrame with allocated components.
        """
        cc_df = cc_df.sort_values("changeout_date")

        for _, changeout in cc_df.iterrows():
            latest_events = self.find_available_pool_slot(pool_slots_df, changeout)

            available_slots_df = latest_events[
                (
                    (latest_events["changeout_date"] < changeout["changeout_date"])
                    & (latest_events["arrival_date"] < changeout["changeout_date"])
                )
                | (latest_events["arrival_date"] < changeout["changeout_date"])
            ]

            if not available_slots_df.empty:
                available_slot = self.find_most_time_unchanged_slot(available_slots_df, changeout["changeout_date"])
            else:
                available_slot = self.find_most_time_unchanged_slot(latest_events, changeout["changeout_date"])

            new_row = changeout.copy()
            new_row["pool_slot"] = available_slot["pool_slot"]

            new_row = pd.DataFrame([new_row])
            new_row = self.add_arrival_date(new_row)

            pool_slots_df = pd.concat([pool_slots_df, new_row], ignore_index=True)
            pool_slots_df = pool_slots_df.sort_values("changeout_date")

        return pool_slots_df

    def generate_pool_projection(self) -> pd.DataFrame:
        """
        Generate pool projection based on component changeouts and available pool slots.

        Returns:
            pd.DataFrame: Generated pool projection.
        """
        cc_df = self.priority_sort(self.cc_df)
        cc_df = cc_df.drop_duplicates(subset=["equipo", "component_code", "position", "changeout_date"])

        cc_df = cc_df[cc_df["component_code"].isin([c.code for c in self.COMPONENT_CODES])]
        pool_proj_df = self.pool_proj_df[
            self.pool_proj_df["component_code"].isin([c.code for c in self.COMPONENT_CODES])
        ]

        merge_columns = ["equipo", "component_code", "component_serial", "changeout_week"]

        pool_slots_df = pd.merge(pool_proj_df, cc_df, on=merge_columns, how="left", suffixes=("_proj", ""))

        pool_slots_df["pool_changeout_type"] = pool_slots_df["pool_changeout_type"].fillna(
            pool_slots_df["pool_changeout_type_proj"]
        )
        pool_slots_df = pool_slots_df.drop(columns="pool_changeout_type_proj")

        pool_slots_df["changeout_date"] = pool_slots_df["changeout_date"].fillna(pool_slots_df["changeout_date_proj"])
        pool_slots_df = pool_slots_df.drop(columns="changeout_date_proj")

        missing_cc_df = cc_df[cc_df["changeout_date"] >= pd.Timestamp(2024, 5, 1)]
        missing_cc_df = missing_cc_df[missing_cc_df["pool_changeout_type"] != "N"]

        missing_cc_df = pd.merge(
            missing_cc_df, pool_proj_df[merge_columns], on=merge_columns, how="left", indicator=True
        )
        missing_cc_df = missing_cc_df[missing_cc_df["_merge"] == "left_only"].drop(columns="_merge")
        missing_cc_df["pool_changeout_type"] = missing_cc_df["pool_changeout_type"].fillna("P")

        self.missing_cc_df = missing_cc_df
        self.pool_slots_df = pool_slots_df

        df = self.allocate_components(missing_cc_df, pool_slots_df)

        df[["changeout_date", "arrival_date"]] = df[["changeout_date", "arrival_date"]].apply(pd.to_datetime)

        df["componente"] = df["component_code"].map({c.code: c.name for c in self.COMPONENT_CODES})

        return df


# class ComponentAllocation:
#
#     COMPONENT_NAMES: dict[str, str] = {
#         "bp": "Blower",
#         "cd": "Cilindro Dirección",
#         "st": "Suspensión Trasera",
#         "cms": "CMSD",
#         "mt": "Motor Tracción",
#         "cl": "Cilindro Levante",
#         "mp": "Módulo Potencia",
#     }
#
#     def __init__(
#         self,
#         cc_df: pd.DataFrame,
#         pool_proj_df: pd.DataFrame,
#         available_components: list,
#     ):
#         self.cc_df = cc_df
#         self.pool_proj_df = pool_proj_df
#         self.available_components = available_components
#
#     def add_arrival_date(self, df: pd.DataFrame) -> pd.DataFrame:
#         df = df.assign(
#             ovh_planned=np.select(
#                 [
#                     df["component_code"] == "bp",
#                     df["component_code"] == "cd",
#                     df["component_code"] == "st",
#                     df["component_code"] == "cms",
#                     df["component_code"] == "mt",
#                     df["component_code"] == "cl",
#                     (df["component_code"] == "mp") & (df["subcomponente"] == "MOTOR"),
#                     (df["component_code"] == "mp") & (df["subcomponente"].isin(["Alternador Principal", "Radiador"])),
#                 ],
#                 [
#                     51,
#                     46,
#                     65,
#                     64,
#                     74,
#                     75,
#                     110,
#                     64,
#                 ],
#             ),
#             ovh_unplanned=np.select(
#                 [
#                     df["component_code"] == "bp",
#                     df["component_code"] == "cd",
#                     df["component_code"] == "st",
#                     df["component_code"] == "cms",
#                     df["component_code"] == "mt",
#                     df["component_code"] == "cl",
#                     (df["component_code"] == "mp") & (df["subcomponente"] == "MOTOR"),
#                     (df["component_code"] == "mp") & (df["subcomponente"].isin(["Alternador Principal", "Radiador"])),
#                 ],
#                 [
#                     101,
#                     96,
#                     125,
#                     124,
#                     134,
#                     135,
#                     170,
#                     114,
#                 ],
#             ),
#         )
#
#         df["arrival_date"] = df["changeout_date"] + np.where(
#             df["pool_changeout_type"] == "P",
#             pd.to_timedelta(df["ovh_planned"], "D"),
#             pd.to_timedelta(df["ovh_unplanned"], "D"),
#         )
#
#         df.loc[df["pool_changeout_type"] == "E", "arrival_date"] = df["changeout_date"] + pd.to_timedelta(200, "D")
#
#         df["arrival_week"] = df["arrival_date"].dt.strftime("%G-W%V")
#         return df.drop(columns=["ovh_planned", "ovh_unplanned"])
#
#     def find_available_pool_slot(self, pool_slots_df: pd.DataFrame, changeout: pd.Series) -> pd.DataFrame:
#         latest_events = pool_slots_df.loc[
#             (pool_slots_df["component_code"] == changeout["component_code"])
#             & (pool_slots_df["changeout_date"] < changeout["changeout_date"])
#         ].sort_values("changeout_date")
#         return latest_events.drop_duplicates(subset=["pool_slot", "component_code"], keep="last").reset_index(drop=True)
#
#     def find_most_time_unchanged_slot(self, df: pd.DataFrame, changeout_date: pd.Timestamp) -> pd.Series:
#         df["days_unchanged"] = (changeout_date - df["arrival_date"]).dt.days
#         return df.loc[df["days_unchanged"].idxmax()]
#
#     def allocate_components(self, cc_df: pd.DataFrame, pool_slots_df: pd.DataFrame) -> pd.DataFrame:
#         cc_df = cc_df.sort_values("changeout_date")
#
#         for _, changeout in cc_df.iterrows():
#             latest_events = self.find_available_pool_slot(pool_slots_df, changeout)
#
#             available_slots_df = latest_events[
#                 (
#                     (latest_events["changeout_date"] < changeout["changeout_date"])
#                     & (latest_events["arrival_date"] < changeout["changeout_date"])
#                 )
#                 | (latest_events["arrival_date"] < changeout["changeout_date"])
#             ]
#
#             if not available_slots_df.empty:
#                 available_slot = self.find_most_time_unchanged_slot(available_slots_df, changeout["changeout_date"])
#             else:
#                 available_slot = self.find_most_time_unchanged_slot(latest_events, changeout["changeout_date"])
#
#             new_row = changeout.copy()
#             new_row["pool_slot"] = available_slot["pool_slot"]
#
#             new_row = pd.DataFrame([new_row])
#             new_row = self.add_arrival_date(new_row)
#
#             pool_slots_df = pd.concat([pool_slots_df, new_row], ignore_index=True)
#             pool_slots_df = pool_slots_df.sort_values("changeout_date")
#
#         return pool_slots_df
#
#     def priority_sort(self, df: pd.DataFrame) -> pd.DataFrame:
#         priority_map = {
#             "mt": {"MOTOR TRACCIÓN": 1},
#             "cms": {"Suspension Delantera": 1},
#             "mp": {"MOTOR": 1, "Alternador Principal": 2, "Radiador": 3},
#         }
#         default_priority = 999
#
#         def get_priority(row):
#             component_priorities = priority_map.get(row["component_code"], {})
#             for subcomponent, priority in component_priorities.items():
#                 if subcomponent in row["subcomponente"]:
#                     return priority
#             return default_priority
#
#         df["subcomponent_priority"] = df.apply(get_priority, axis=1)
#         return df
#
#     def generate_pool_projection(self) -> pd.DataFrame:
#         cc_df = self.priority_sort(self.cc_df)
#         cc_df = cc_df.sort_values(
#             [
#                 "equipo",
#                 "changeout_date",
#                 "component_code",
#                 "position",
#                 "subcomponent_priority",
#             ]
#         ).drop_duplicates(subset=["equipo", "component_code", "position", "changeout_date"])
#
#         cc_df = cc_df.loc[cc_df["component_code"].isin(self.available_components)].reset_index(drop=True)
#         pool_proj_df = self.pool_proj_df.loc[
#             self.pool_proj_df["component_code"].isin(self.available_components)
#         ].reset_index(drop=True)
#
#         merge_columns = [
#             "equipo",
#             "component_code",
#             "component_serial",
#             "changeout_week",
#         ]
#
#         pool_slots_df = pd.merge(pool_proj_df, cc_df, on=merge_columns, how="left", suffixes=("_proj", ""))
#
#         pool_slots_df["pool_changeout_type"] = pool_slots_df["pool_changeout_type"].fillna(
#             pool_slots_df["pool_changeout_type_proj"]
#         )
#         pool_slots_df = pool_slots_df.drop(columns="pool_changeout_type_proj")
#         pool_slots_df = pool_slots_df.assign(
#             changeout_date=np.where(
#                 pool_slots_df["changeout_date"].isnull(),
#                 pool_slots_df["changeout_date_proj"],
#                 pool_slots_df["changeout_date"],
#             )
#         ).drop(columns="changeout_date_proj")
#
#         missing_cc_df = cc_df[cc_df["changeout_date"] >= pd.Timestamp(2024, 6, 1)]
#         # Se eliminan componentes con casos especiales que no debiesen aparecer en el pool
#         missing_cc_df = missing_cc_df.loc[missing_cc_df["pool_changeout_type"] != "N"]
#         missing_cc_df = (
#             pd.merge(
#                 missing_cc_df,
#                 pool_proj_df[merge_columns],
#                 on=merge_columns,
#                 how="left",
#                 indicator=True,
#             )
#             .query("_merge == 'left_only'")
#             .drop(columns="_merge")
#             .assign(pool_changeout_type=lambda x: x["pool_changeout_type"].fillna("P"))
#         )
#         df = self.allocate_components(missing_cc_df, pool_slots_df).reset_index(drop=True)
#
#         df[["changeout_date", "arrival_date"]] = df[["changeout_date", "arrival_date"]].apply(
#             lambda x: pd.to_datetime(x, format="%Y-%m-%d")
#         )
#
#         df = df.assign(componente=df["component_code"].map(self.COMPONENT_NAMES))
#         return df
