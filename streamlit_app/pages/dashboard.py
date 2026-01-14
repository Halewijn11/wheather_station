import streamlit as st
import importlib
import pandas as pd
import utils
importlib.reload(utils)
from streamlit_extras.metric_cards import style_metric_cards
import altair as alt
import numpy as np
import os
from streamlit_gsheets import GSheetsConnection

debug = 0
cached_time = 0
time_window_hours = 1

url = "https://docs.google.com/spreadsheets/d/1OW-KdOF9BSuR66o9qbumSkNck3TlXb1himbQnLeFvVE/edit?gid=0#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)

google_sheet_df = conn.read(spreadsheet=url, ttl=cached_time)
# st.dataframe(google_sheet_df)


st.title("Wheather dashboard")

# #--------------------- general preamble to load data -----------------------------

if debug == True:
    st.write("Available columns in Sheet:", google_sheet_df.columns.tolist()) # Add this line

df = utils.tidy_google_sheet_df(google_sheet_df)
# df  = pd.read_csv('data.csv')
time_window_df = utils.filter_by_recency(df, hours = time_window_hours)

# 1. Get the directory that this specific file (dashboard.py) is in
current_dir = os.path.dirname(__file__)

# #--------------------- sunset and sunrise -----------------------------
sunrise_str, sunset_str = utils.get_sunrise_sunset()
# 1. We keep your column structure to limit the width
col1, col2, col3, col4, buffer = st.columns([6, 9, 6, 9, 30])

with col1:
    img_path = os.path.join(current_dir, "..", "assets", "sunrise.png")
    st.image(img_path, width=50)
with col2:
    # Use <br> instead of \n\n to remove the paragraph gap
    st.markdown(f"**Sunrise**<br>{sunrise_str}", unsafe_allow_html=True)

with col3:
    img_path = os.path.join(current_dir, "..", "assets", "sunset.png")
    st.image(img_path, width=50)
with col4:
    # Applying the same fix here
    st.markdown(f"**Sunset**<br>{sunset_str}", unsafe_allow_html=True)

with buffer:
    pass
# #--------------------- temperature -----------------------------
utils.plot_metric_with_graph(
    time_window_df = time_window_df,
    y_variable_colname = 'sht_temperature_avg',
    y_variable_unit = '°C',
    y_variable_prefix_text = 'Temperature',
    y_label = "Temp (°C)",
    x_label = 'x_label'
)

# #--------------------- humidity -----------------------------


utils.plot_metric_with_graph(
    time_window_df = time_window_df,
    y_variable_colname = 'sht_humidity_avg',
    y_variable_unit = '%',
    y_variable_prefix_text = 'Humidity',
    y_label = "Humidity (%)",
    x_label = 'received at'
)


 # #--------------------- pressure -----------------------------

utils.plot_metric_with_graph(
    time_window_df = time_window_df,
    y_variable_colname = 'bmp_pressure_avg',
    y_variable_unit = 'hPa',
    y_variable_prefix_text = 'Pressure',
    y_label = "Pressure (hPa)",
    x_label = 'received at'
)



# # pressure_colname = utils.get_full_payload_colname('pressure')
# pressure_colname = 'pressure'
# col1, col2 = st.columns([1, 1])
# latest = np.round(time_window_df[pressure_colname].iloc[-1]/100,1)
# with col1:
#     st.metric("Pressure", f"{latest:.1f} hPa")

# with col2:
#     spark = alt.Chart(time_window_df.tail(50)).mark_line().encode(
#         x=alt.X("received_at", axis=None),
#         y=alt.Y(
#             pressure_colname,
#             axis=alt.Axis(
#                     labels=True,
#                     ticks=True,
#                     title="Pressure (hPa)",
#                 ),
#             scale=alt.Scale(domain=[
#                 time_window_df[pressure_colname].min(),
#                 time_window_df[pressure_colname].max()
#             ])
#         ),
#                 tooltip=[
#         alt.Tooltip("received_at:T", title="Time"),
#         alt.Tooltip(pressure_colname, title="hPa", format=".1f")
#     ]
#     ).properties(height=100)
#     st.altair_chart(spark, use_container_width=True)
    