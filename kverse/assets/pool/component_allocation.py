# Standard library imports
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

# Third-party imports
import pandas as pd
import numpy as np
from dataclasses import dataclass

# Constants
DATE_FORMAT = "%Y-W%W-%w"
CHANGEOUT_START_DATE = pd.Timestamp(2024, 6, 1)


@dataclass(frozen=True)
class ComponentCode:
    code: str
    name: str
    planned_ovh_days: int
    unplanned_ovh_days: int

    def __str__(self) -> str:
        return self.code


class ComponentType(Enum):
    BP = ComponentCode("blower_parrilla", "Blower", 51, 101)
    CD = ComponentCode("cilindro_direccion", "Cilindro Dirección", 46, 96)
    ST = ComponentCode("suspension_trasera", "Suspensión Trasera", 65, 125)
    CMS = ComponentCode("conjunto_masa_suspension_delantera", "CMSD", 64, 124)
    MT = ComponentCode("motor_traccion", "Motor Tracción", 74, 134)
    CL = ComponentCode("cilindro_levante", "Cilindro Levante", 75, 135)
    MP = ComponentCode("modulo_potencia", "Módulo Potencia", 110, 170)

    @classmethod
    def get_all_codes(cls) -> List[str]:
        return [component.value.code for component in cls]


def find_available_pool_slot(component_df: pd.DataFrame, changeout: pd.Series) -> pd.DataFrame:

    df = component_df.sort_values(["pool_slot", "changeout_date"]).drop_duplicates(subset=["pool_slot"], keep="last")
    df = (
        df[
            (df["changeout_date"] < changeout["changeout_date"])
            & (df["arrival_date"].notnull())
            & (df["arrival_date"] < changeout["changeout_date"] - pd.Timedelta(days=0))
        ]
        .sort_values("changeout_date")
        .drop_duplicates(subset=["pool_slot", "component"], keep="last")
    )

    # assert not df.empty, changeout

    # df = pool_slots_df.copy()

    # df = (
    #     df.loc[(df["arrival_date"].isnull()) & (df["arrival_date_proj"] < changeout["changeout_date"])]
    #     .drop(columns=["arrival_date"])
    #     .sort_values("changeout_date")
    #     .reset_index(drop=True)
    # )

    return df


def add_arrival_date_proj(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add projected arrival date to the DataFrame based on component code and changeout type.

    Args:
        df (DataFrame): Input DataFrame containing component information.

    Returns:
        DataFrame: DataFrame with added projected arrival date information.

    Raises:
        ValueError: If required columns are missing in the input DataFrame.
    """
    required_columns = {"component", "changeout_date", "pool_changeout_type", "subcomponent"}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"Missing required columns: {required_columns}")

    def get_ovh_days(row: pd.Series) -> int:
        component = next(c for c in ComponentType if c.value.code == row["component"])
        if component == ComponentType.MP:
            if row["subcomponent"] in ["alternador_principal", "radiador"]:
                return 64 if row["pool_changeout_type"] == "P" else 114
        return (
            component.value.planned_ovh_days
            if row["pool_changeout_type"] == "P"
            else component.value.unplanned_ovh_days
        )

    df = df.copy()
    df["ovh_days"] = df.apply(get_ovh_days, axis=1)
    df["arrival_date_proj"] = df["changeout_date"] + pd.to_timedelta(df["ovh_days"], unit="D")
    df.loc[df["pool_changeout_type"] == "E", "arrival_date_proj"] = df["changeout_date"] + pd.to_timedelta(200, "D")
    df["arrival_week_proj"] = df["arrival_date_proj"].dt.strftime("%G-W%V")

    return df.drop(columns=["ovh_days"])


def priority_sort(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort the DataFrame based on component and subcomponent priorities.

    Args:
        df (DataFrame): Input DataFrame to be sorted.

    Returns:
        DataFrame: Sorted DataFrame.

    Raises:
        ValueError: If required columns are missing in the input DataFrame.
    """
    required_columns = {"component", "subcomponent", "equipo", "changeout_date", "position"}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"Missing required columns: {required_columns}")

    priority_map = {
        ComponentType.MT.value.code: {"MOTOR TRACCIÓN": 1},
        ComponentType.CMS.value.code: {"Suspension Delantera": 1},
        ComponentType.MP.value.code: {"MOTOR": 1, "Alternador Principal": 2, "Radiador": 3},
    }
    default_priority = 999

    def get_priority(row: pd.Series) -> int:
        component_priorities = priority_map.get(row["component"], {})
        return next(
            (
                priority
                for subcomponent, priority in component_priorities.items()
                if subcomponent in row["subcomponent"]
            ),
            default_priority,
        )

    df = df.copy()
    df["subcomponent_priority"] = df.apply(get_priority, axis=1)
    return (
        df.sort_values(["equipo", "changeout_date", "component", "position", "subcomponent_priority"])
        .reset_index(drop=True)
        .drop(columns=["subcomponent_priority"])
    )


class ComponentAllocation:
    def __init__(
        self,
        cc_df: pd.DataFrame,
        pool_proj_df: pd.DataFrame,
        arrivals_df: pd.DataFrame,
    ):
        self.cc_df = self._preprocess_cc_df(cc_df)
        self.pool_proj_df = self._preprocess_pool_proj_df(pool_proj_df)
        self.arrivals_df = self._preprocess_arrivals_df(arrivals_df)
        self.missing_cc_df = None
        self.pool_slots_df = None

    def _preprocess_cc_df(self, cc_df: pd.DataFrame) -> pd.DataFrame:
        cc_df = priority_sort(cc_df)
        return cc_df.drop_duplicates(subset=["equipo", "component", "position", "changeout_date"])[
            cc_df["component"].isin(ComponentType.get_all_codes())
        ].reset_index(drop=True)

    def _preprocess_pool_proj_df(self, pool_proj_df: pd.DataFrame) -> pd.DataFrame:
        return pool_proj_df[pool_proj_df["component"].isin(ComponentType.get_all_codes())].reset_index(drop=True)

    def _preprocess_arrivals_df(self, arrivals_df: pd.DataFrame) -> pd.DataFrame:
        df = arrivals_df.copy()
        df = df.loc[df["arrival_date"] >= CHANGEOUT_START_DATE].reset_index(drop=True)
        merge_columns = ["component", "arrival_week"]
        df = pd.merge(
            df.drop(columns=["arrival_date"]),
            self.pool_proj_df[merge_columns],
            on=merge_columns,
            how="left",
            indicator=True,
        )
        df = df.loc[df["_merge"] == "left_only"].drop(columns="_merge")
        df["arrival_date"] = df["arrival_week"].apply(lambda x: datetime.strptime(f"{x}-1", DATE_FORMAT))
        df["pool_slot"] = None
        return df

    def find_most_time_unchanged_slot(self, df: pd.DataFrame, changeout_date: pd.Timestamp) -> pd.Series:
        """
        Find the slot that has been unchanged for the longest time.

        Args:
            df (DataFrame): DataFrame containing slot information.
            changeout_date (pd.Timestamp): Date of the changeout.

        Returns:
            Series: Series containing information about the most time unchanged slot.

        Raises:
            ValueError: If the input DataFrame is empty.
        """
        if df.empty:
            raise ValueError("Input DataFrame is empty")

        df = df.assign(days_unchanged=(changeout_date - df["arrival_date"]).dt.days)
        return df.loc[df["days_unchanged"].idxmax()]

    def add_arrival_date2(self, df: pd.DataFrame, component: str) -> pd.DataFrame:

        earliest_arrival = self.arrivals_df[
            (self.arrivals_df["pool_slot"].isnull()) & (self.arrivals_df["component"] == component)
        ]["arrival_date"].min()

        if pd.isnull(earliest_arrival):
            return df

        earliest_arrival_df = self.arrivals_df.loc[
            (self.arrivals_df["arrival_date"] == earliest_arrival) & (self.arrivals_df["component"] == component)
        ]
        # Unir las fechas de llegada a los cambios del pool sin llegadas confirmadas.
        unconfirmed_df = (
            df.loc[df["component"] == component]
            .sort_values(["pool_slot", "changeout_date"])
            .drop_duplicates(subset=["pool_slot"], keep="last")
            .sort_values("arrival_date_proj")
        )
        unconfirmed_df = unconfirmed_df.loc[unconfirmed_df["confirmed"] == False].reset_index(drop=True)[
            ["component", "arrival_date_proj", "changeout_date", "pool_slot"]
        ]

        earliest_arrival_df = pd.merge_asof(
            earliest_arrival_df[["component", "arrival_date"]].rename(
                columns={"arrival_date": "earliest_arrival_date"}
            ),
            unconfirmed_df,
            by="component",
            left_on="earliest_arrival_date",
            right_on="arrival_date_proj",
            direction="nearest",
        )

        for _, row in earliest_arrival_df.iterrows():
            mask = (df["changeout_date"] == row["changeout_date"]) & (df["component"] == row["component"])
            df.loc[mask, "arrival_date"] = earliest_arrival
            df.loc[mask, "confirmed"] = True
            self.arrivals_df.loc[
                (self.arrivals_df["arrival_date"] == earliest_arrival)
                & (self.arrivals_df["component"] == row["component"]),
                "pool_slot",
            ] = row["pool_slot"]

        return df

    def add_arrival_date(self, component_df: pd.DataFrame, component_arrival_df: pd.DataFrame) -> pd.DataFrame:
        # Unir las fechas de llegada a los cambios del pool sin llegadas confirmadas.
        # unconfirmed_df = (
        #     component_df.sort_values(["pool_slot", "changeout_date"])
        #     .drop_duplicates(subset=["pool_slot"], keep="last")
        #     .sort_values("arrival_date_proj")
        # )
        # Buscar todas las asignaciones de pool con llegadas no confirmadas
        unconfirmed_df = (
            component_df.loc[component_df["confirmed"] == False]
            .sort_values("arrival_date_proj")
            .reset_index(drop=True)[["component", "arrival_date_proj", "changeout_date", "pool_slot"]]
        )
        self.unconfirmed_df = unconfirmed_df

        # La unión se efectua encontrando la fecha más cercana
        component_arrival_df = pd.merge_asof(
            component_arrival_df[["component", "arrival_date"]],
            unconfirmed_df,
            by="component",
            left_on="arrival_date",
            right_on="arrival_date_proj",
            direction="nearest",
        )

        self.component_arrival_df = component_arrival_df

        for _, row in component_arrival_df.iterrows():
            mask = (component_df["changeout_date"] == row["changeout_date"]) & (
                component_df["component"] == row["component"]
            )
            component_df.loc[mask, "arrival_date"] = row["arrival_date"]
            component_df.loc[mask, "confirmed"] = True
            self.arrivals_df.loc[
                (self.arrivals_df["arrival_date"] == row["arrival_date"])
                & (self.arrivals_df["component"] == row["component"]),
                "pool_slot",
            ] = row["pool_slot"]

        return component_df

    def allocate_components(self) -> pd.DataFrame:
        """
        Allocate components to available pool slots.

        Returns:
            DataFrame: Updated pool slots DataFrame with allocated components.

        Raises:
            ValueError: If no available slots are found for a component.
        """
        cc_df = self.missing_cc_df.sort_values(["component", "changeout_date"]).reset_index(drop=True)
        frames = []
        for component in cc_df["component"].unique():
            component_df = self.pool_slots_df.loc[self.pool_slots_df["component"] == component]

            print(f"#########\nAsignando pool a {component}:")

            # Encontrar semanas por donde va a ir iterando el algoritmo dado un componente
            weeks = (
                pd.concat(
                    [
                        self.missing_cc_df.loc[self.missing_cc_df["component"] == component]["changeout_week"],
                        self.arrivals_df.loc[self.arrivals_df["component"] == component]["arrival_week"],
                    ]
                )
                .drop_duplicates()
                .reset_index(drop=True)
                .to_list()
            )
            weeks = sorted(weeks)
            for week in weeks:
                print(f"\n{week}")
                week_arrivals_df = self.arrivals_df.loc[
                    (self.arrivals_df["arrival_week"] == week) & (self.arrivals_df["component"] == component)
                ].reset_index(drop=True)
                week_cc_df = cc_df.loc[
                    (cc_df["changeout_week"] == week) & (cc_df["component"] == component)
                ].reset_index(drop=True)
                if week_arrivals_df.shape[0] == 0:
                    print(f"Sin llegadas de componente")
                else:

                    print(
                        f"Se agrega llegada componente {component} con fecha: {week_arrivals_df['arrival_date'].to_list()}"
                    )
                    component_df = component_df.pipe(self.add_arrival_date, week_arrivals_df)

                if week_cc_df.shape[0] == 0:
                    print(f"No existen cambios de componente para la semana {week}, componente {component}")
                else:

                    # Proceder con agregar el componente
                    for _, changeout in week_cc_df.iterrows():
                        print(
                            f"Se agrega cambio de componente con fecha: {changeout['changeout_date'].strftime('%Y-%m-%d')}, "
                            f"equipo: {changeout['equipo']}, serie: {changeout['component_serial']}"
                        )
                        try:
                            # 1. Verifica si el componente sujeto a cambio tiene disponibilidad en el pool
                            available_slots_df = find_available_pool_slot(component_df, changeout)
                            new_row = changeout.copy()
                            new_row["confirmed"] = False
                            available_slot = self.find_most_time_unchanged_slot(
                                available_slots_df, changeout["changeout_date"]
                            )
                            new_row["pool_slot"] = available_slot["pool_slot"]

                            new_row = pd.DataFrame([new_row])
                            new_row = add_arrival_date_proj(new_row)
                            component_df = pd.concat([component_df, new_row], ignore_index=True)
                            component_df = component_df.sort_values("changeout_date")
                        except Exception as e:
                            print(f"No se pudo agregar componente. \nError: {e}")
                            continue
                print("\n")
            frames.append(component_df)

        #
        # for component in cc_df["component"].unique():

        #     for _, changeout in cc_df.loc[cc_df["component"] == component].iterrows():
        #         # 1. Verifica si el componente sujeto a cambio tiene disponibilidad en el pool
        #         available_slots_df = find_available_pool_slot(df, changeout)
        #         new_row = changeout.copy()
        #         new_row["confirmed"] = False
        #         # 2. Si no existe ningún puesto disponible, asignar una fecha de llegada real
        #         if available_slots_df.empty:
        #             df = self.add_arrival_date(df, changeout["component"])
        #             available_slots_df = find_available_pool_slot(df, changeout)
        #
        #             if available_slots_df.empty:
        #                 raise ValueError(f"No available slots found for component: {changeout['component']}")
        #
        #         available_slot = self.find_most_time_unchanged_slot(available_slots_df, changeout["changeout_date"])
        #
        #         new_row["pool_slot"] = available_slot["pool_slot"]
        #         # Si agrego una nueva componente al pool, debiese estar la llegada real del componente
        #
        #         new_row = pd.DataFrame([new_row])
        #         new_row = add_arrival_date_proj(new_row)
        #
        #         df = pd.concat([df, new_row], ignore_index=True)
        #         df = df.sort_values("changeout_date")
        #     while self.arrivals_df.loc[self.arrivals_df["component"] == component, "pool_slot"].isna().any():
        #         df = self.add_arrival_date(df, changeout["component"])

        df = pd.concat(frames)
        return df

    def get_base_pool_slots(self) -> pd.DataFrame:
        # proyección en base a un archivo base para darle forma al gráfico de timeline
        merge_columns = ["equipo", "component", "component_serial", "changeout_week"]

        df = pd.merge(self.pool_proj_df, self.cc_df, on=merge_columns, how="left", suffixes=("_proj", ""))

        df["pool_changeout_type"] = df["pool_changeout_type"].fillna(df["pool_changeout_type_proj"])
        df = df.drop(columns="pool_changeout_type_proj")

        df["changeout_date"] = df["changeout_date"].fillna(df["changeout_date_proj"])

        df = df.drop(columns="changeout_date_proj").reset_index(drop=True)

        df = add_arrival_date_proj(df)
        # Para componentes en espera, forzar una fecha de proyección más grande con el fin de blockearlos esa linea del pool
        df = df.assign(
            arrival_date=np.where(df["pool_changeout_type"] == "E", df["arrival_date_proj"], df["arrival_date"])
        )

        # Los que no fecha llegada asignada en la planilla base son proyecciones, no llegadas reales
        df = df.assign(confirmed=np.where(df["arrival_date"].isnull(), False, True))

        return df

    def get_missing_changeouts(self) -> pd.DataFrame:

        merge_columns = ["equipo", "component", "component_serial", "changeout_week"]
        df = self.cc_df[self.cc_df["changeout_date"] >= CHANGEOUT_START_DATE]
        df = df[df["pool_changeout_type"] != "N"]

        df = pd.merge(df, self.pool_proj_df[merge_columns], on=merge_columns, how="left", indicator=True)
        df = df[df["_merge"] == "left_only"].drop(columns="_merge")
        df["pool_changeout_type"] = df["pool_changeout_type"].fillna("P")
        return df

    def generate_pool_projection(self) -> pd.DataFrame:
        """
        Generate pool projection based on component changeouts and available pool slots.

        Returns:
            DataFrame: Generated pool projection.

        Raises:
            ValueError: If component allocation fails.
        """
        self.missing_cc_df = self.get_missing_changeouts()
        self.pool_slots_df = self.get_base_pool_slots()

        df = self.allocate_components()

        df[["changeout_date", "arrival_date"]] = df[["changeout_date", "arrival_date"]].apply(pd.to_datetime)

        df["componente"] = df["component"].map({c.value.code: c.value.name for c in ComponentType})
        df = df.reset_index(drop=True)
        df = df.assign(arrival_date=np.where(df["arrival_date"].isnull(), df["arrival_date_proj"], df["arrival_date"]))
        return df
