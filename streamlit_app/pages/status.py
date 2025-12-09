import streamlit as st
import importlib
import utils
import pandas as pd
from streamlit_extras.metric_cards import style_metric_cards
importlib.reload(utils)

st.title("Status")

# Apply custom CSS to metric cards
# style_metric_cards(
#     font_size_value="16px",       # <--- make value font smaller
#     font_size_label="12px"        # optional: smaller label
# )


# #--------------------- calculate some metrics -----------------------------
google_sheet_df = utils.get_google_sheet_df()
df = utils.tidy_google_sheet_df(google_sheet_df)
last_measurement_string =  utils.get_last_measurement_string(df)

# #--------------------- building the streamlit app -----------------------------
# --- Top row ---
# top_cols = st.columns(3)
# top_cols[0].metric(
#     label="avg income/month",
#     value=last_measurement_string,
#     border=True,
#     key = "last_measurement_time_card"
# )

st.info(f"Time since last measurement: **{last_measurement_string}**")