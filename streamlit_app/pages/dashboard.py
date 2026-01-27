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
from datetime import datetime

debug = 0
cached_time = 0
time_window_hours = 1
time_window_filtering_mode = 'last_session'





st.title("Wheather dashboard")

# #--------------------- general preamble to load data -----------------------------
# url = "https://docs.google.com/spreadsheets/d/1OW-KdOF9BSuR66o9qbumSkNck3TlXb1himbQnLeFvVE/edit?gid=0#gid=0"
# conn = st.connection("gsheets", type=GSheetsConnection)
# google_sheet_df = conn.read(spreadsheet=url, ttl=cached_time)

# if debug == True:
#     st.write("Available columns in Sheet:", google_sheet_df.columns.tolist()) # Add this line

# 1. Load the big dataset (cached)
df = utils.get_data()

# 1. Get the directory that this specific file (dashboard.py) is in
current_dir = os.path.dirname(__file__)
asset_path = os.path.join(current_dir, "..", "assets")
# #--------------------- current date -----------------------------
# 1. Get the current date
now = datetime.now()

# 2. Format it (e.g., Wednesday, June 4)
# %A = Weekday, %B = Month, %d = Day
date_string = now.strftime("%A, %B %d")

# 3. Display it in Streamlit
st.header('Affligem, Belgium')

st.write(date_string)

# #--------------------- sunset and sunrise -----------------------------
sunrise_str, sunset_str = utils.get_sunrise_sunset()
# 1. We keep your column structure to limit the width
icon_width = 6
text_width = 9
buffer_width = 30

col1, col2, col3, col4, col5, col6, buffer = st.columns([icon_width, text_width,icon_width, text_width,icon_width, text_width,buffer_width])

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

# --- Moon Phase ---
with col5:
    # moon_icon_path comes directly from your utils function
    moonphase_image_filepath, index = utils.get_moonphase_filepath(image_repo= asset_path)
    # st.write(f"DEBUG: Looking for image at: {moonphase_image_filepath}")
    st.image(moonphase_image_filepath, width=50)
with col6:
    st.markdown(f"**Moon**<br> {index}/8", unsafe_allow_html=True)

with buffer:
    pass


# #--------------------- button for time window -----------------------------
time_options = {
    "Last Hour": 1,
    "Last 24 Hours": 24,
    "Last Week": 168  # 24 * 7
}

# Create the dropdown (selectbox)
selected_label = st.selectbox(
    "Select Time Range:",
    options=list(time_options.keys()),
    index=0  # Default to "Last Hour"
)

# Get the numeric value based on selection
time_window_hours = time_options[selected_label]

# Now filter your data using this dynamic variable
time_window_df = utils.filter_by_recency(df, hours=time_window_hours)


# #--------------------- sample the dataframe to a lower resolution -----------------------------


# 2. Filter by the number of hours defined in our config
filtered_df = utils.filter_by_recency(df, hours = time_window_hours, mode = time_window_filtering_mode)

# 3. Apply the resolution defined in our config
time_window_df = utils.resample_data(filtered_df, selected_label)


# #--------------------- temperature -----------------------------
utils.plot_metric_with_graph(
    time_window_df = time_window_df,
    y_variable_colname = 'sht_temperature_avg',
    y_variable_unit = '°C',
    y_variable_prefix_text = 'Temperature',
    y_label = "Temp (°C)",
    x_label = 'received at'
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


 # #--------------------- light intensity -----------------------------
utils.plot_metric_with_graph(
    time_window_df = time_window_df,
    y_variable_colname = 'light_intensity_avg',
    y_variable_unit = 'W/m²',
    y_variable_prefix_text = 'Light intensity',
    y_label = "Light intensity (W/m²)",
    x_label = 'received at'
)

#  # #--------------------- wind speed -----------------------------
# utils.plot_metric_with_graph(
#     time_window_df = time_window_df,
#     y_variable_colname = 'wind_pulses_total',
#     y_variable_unit = '',
#     y_variable_prefix_text = 'wind pulses',
#     y_label = "Wind pulses",
#     x_label = 'received at'
# )

#  #--------------------- wind direction as a function of tiem -----------------------------
# radial_coords_df = utils.transform_to_radial_cartesian(time_window_df,'received_at', 'wind_direction')
# utils.plot_metric_with_graph(
#     time_window_df = radial_coords_df,
#     y_variable_colname = 'y_radial',
#     y_variable_unit = '°',
#     y_variable_prefix_text = 'wind direction',
#     y_label = "",
#     x_label = '',
#     x_variable_colname = 'x_radial'
# )



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
    