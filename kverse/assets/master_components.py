import pandas as pd


def master_components():
    df = pd.DataFrame(
        [
            {"component_code": "mp", "component": "modulo_potencia", "subcomponent": ""},
            {"component_code": "mt", "component": "motor_traccion", "subcomponent": ""},
            {"component_code": "bp", "component": "blower_parrilla", "subcomponent": ""},
            {"component_code": "cl", "component": "cilindro_levante", "subcomponent": ""},
            {"component_code": "st", "component": "suspension_trasera", "subcomponent": ""},
            {"component_code": "sd", "component": "suspension_delantera", "subcomponent": ""},
            {"component_code": "cd", "component": "cilindro_direccion", "subcomponent": ""},
            {"component_code": "ap", "component": "modulo_potencia", "subcomponent": "alternador_principal"},
        ]
    )
    return df
