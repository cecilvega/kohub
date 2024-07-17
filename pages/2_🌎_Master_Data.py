import streamlit as st

from common import *
from utils import *
from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parents[2] / "dags"))
import resources.tidypolars as tp

styler()

df_machines = tp.machines(columns=["model", "serial", "site_name", "machine_name"])
