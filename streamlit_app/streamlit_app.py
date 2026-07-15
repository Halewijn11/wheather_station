import streamlit as st
import importlib
import utils
importlib.reload(utils)
import pandas as pd

# --- PAGE SETUP ---
dashboard_page = st.Page(
    "pages/dashboard.py",
    title="Weather dashboard",
    icon=":material/bar_chart:",
    default=True,
)
overlay_page = st.Page(
    "pages/overlay.py",
    title="Overlay",
    icon=":material/layers:",
)
today_page = st.Page(
    "pages/today.py",
    title="Today",
    icon=":material/today:",
)
regen_page = st.Page(
    "pages/regen.py",
    title="Regen",
    icon=":material/rainy:",
)
zon_page = st.Page(
    "pages/zon.py",
    title="Zon",
    icon=":material/wb_sunny:",
)
status_page = st.Page(
    "pages/status.py",
    title="Status",
    icon=":material/memory:",
)

info_page = st.Page(
    "pages/info.py",
    title="info",
    icon=":material/info:",
)


# project_2_page = st.Page(
#     "views/chatbot.py",
#     title="Chat Bot",
#     # icon=":material/smart_toy:",
# )

# --- NAVIGATION SETUP [WITHOUT SECTIONS] ---
pg = st.navigation(pages=[dashboard_page, overlay_page, today_page, regen_page, zon_page, status_page, info_page])

# --- RUN NAVIGATION ---
pg.run()