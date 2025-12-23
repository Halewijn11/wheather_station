import streamlit as st
import importlib
import utils
import pandas as pd
importlib.reload(utils)

# --- PAGE SETUP ---
dashboard_page = st.Page(
    "pages/dashboard.py",
    title="Wheater dashboard",
    icon=":material/bar_chart:",
    default=True,
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
pg = st.navigation(pages=[dashboard_page, status_page, info_page])

# --- RUN NAVIGATION ---
pg.run()