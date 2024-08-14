import os

import sys
from pathlib import Path

import streamlit as st

source_path = Path().resolve().parent

import polars as pl
from datetime import timedelta

__all__ = ["styler", "theme_plotly"]

theme_plotly = "streamlit"
# [data-testid="stToolbar"] {visibility: hidden !important;}


def styler():
    logo_path = Path("__file__").absolute().parents[1] / "images/komatsu.png"

    # hide_streamlit_style = """
    #         <style>
    #         footer {visibility: hidden !important;}
    #         </style>
    #         """
    #
    # st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    #
    # with open("style.css") as f:
    #     st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
