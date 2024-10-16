import streamlit as st
from pathlib import Path
from common import *
from PIL import Image
import base64

# st.header("Información Área Planificación")

root_path = Path("__file__").absolute().parent
# logo_path = root_path / "images/bhp-logo.png"
news_path = root_path / "pages/maintenance/news.md"


with open(news_path, "r", encoding="utf-8-sig") as f:
    readme_lines = f.readlines()
    readme_buffer = []
    images = [
        "Pasted image 20241015203159.png",
    ]
    for line in readme_lines:
        readme_buffer.append(line)
        for image in images:
            if image in line:
                st.markdown(" ".join(readme_buffer[:-1]))
                st.image(str(root_path / "images" / image))
                readme_buffer.clear()
    st.markdown(" ".join(readme_buffer))


# st.markdown(news_path.read_text(encoding="utf-8-sig"), unsafe_allow_html=True)
