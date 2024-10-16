import streamlit as st
from pathlib import Path
from common import *
from PIL import Image
import base64
from streamlit_mermaid import st_mermaid

# st.header("Información Área Planificación")

root_path = Path("__file__").absolute().parent
# logo_path = root_path / "images/bhp-logo.png"
news_path = root_path / "pages/maintenance/news.md"


# Example: path to the file
with open(news_path, "r", encoding="utf-8-sig") as f:
    readme_lines = f.readlines()

readme_buffer = []
images = [{"image": "Pasted image 20241015203159.png", "size": 300}]
in_mermaid_block = False
mermaid_buffer = []

for line in readme_lines:
    # Check if it's the start of a Mermaid block
    if line.strip().startswith("```mermaid"):
        in_mermaid_block = True
        mermaid_buffer.clear()
        continue

    # Check if it's the end of a Mermaid block
    if in_mermaid_block:
        if line.strip().startswith("```"):
            in_mermaid_block = False
            st.markdown(" ".join(readme_buffer[:-1]))  # Render text before the mermaid
            st_mermaid("\n".join(mermaid_buffer), height=500)  # Render the Mermaid diagram
            readme_buffer.clear()
            continue
        else:
            mermaid_buffer.append(line)
            continue

    # Check for images in the current line
    readme_buffer.append(line)
    for image in images:
        if image["image"] in line:
            st.markdown(" ".join(readme_buffer[:-1]))  # Render text before the image
            st.image(str(root_path / "images" / image["image"]), width=image["size"])  # Render the image
            readme_buffer.clear()

# Render remaining text
st.markdown(" ".join(readme_buffer))

# with open(news_path, "r", encoding="utf-8-sig") as f:
#     readme_lines = f.readlines()
#     readme_buffer = []
#     images = [{"image": "Pasted image 20241015203159.png", "size": 300}]
#     for line in readme_lines:
#         readme_buffer.append(line)
#         for image in images:
#             if image["image"] in line:
#                 st.markdown(" ".join(readme_buffer[:-1]))
#                 st.image(str(root_path / "images" / image["image"]), width=image["size"])
#                 readme_buffer.clear()
#     st.markdown(" ".join(readme_buffer))


# st.markdown(news_path.read_text(encoding="utf-8-sig"), unsafe_allow_html=True)
