import streamlit as st
import pandas as pd
import utils
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


# 1. Get the directory that this specific file (dashboard.py) is in
current_dir = os.path.dirname(__file__)
asset_path = os.path.join(current_dir, "..", "assets")

discharge_csv_path = os.path.join(asset_path, 'LiPo_smooth_discharge_curve.csv')
discharge_curve = pd.read_csv(discharge_csv_path)
df = utils.get_data(discharge_curve)


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
text_width = 15
buffer_width = 20

col1, col2, col3, col4, col5, col6, col7, col8 ,buffer = st.columns([icon_width, text_width,
                                                         icon_width, text_width,
                                                         icon_width, text_width,
                                                        icon_width, text_width,
                                                         buffer_width])

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

# --- Moon Phase ---
with col7:
    # moon_icon_path comes directly from your utils function
    img_path = os.path.join(asset_path, 'solar_noon.png')
    sunrise_str, sunset_str = utils.get_sunrise_sunset()
    solar_noon_str = utils.get_solar_noon()
    # st.write(f"DEBUG: Looking for image at: {moonphase_image_filepath}")
    st.image(img_path, width=50)
with col8:
    st.markdown(f"**Solar noon**<br> {solar_noon_str}", unsafe_allow_html=True)

with buffer:
    pass


# #--------------------- button for time window -----------------------------

last_datapoint = df['received_at'].max()
if pd.notna(last_datapoint):
    last_datapoint_ts = pd.Timestamp(last_datapoint)
    if last_datapoint_ts.tzinfo is None:
        last_datapoint_ts = last_datapoint_ts.tz_localize('UTC')
    last_datapoint_local = last_datapoint_ts.tz_convert('Europe/Brussels')
    last_datapoint_str = f"{last_datapoint_local.strftime('%a')} {last_datapoint_local.day} {last_datapoint_local.strftime('%b')} {last_datapoint_local.strftime('%H:%M')}"
    st.caption(f"Last datapoint on: {last_datapoint_str}")
else:
    st.caption("Last datapoint on: N/A")
    
if st.button("Refresh Data"):
    utils.get_data.clear()
    st.success("Data refreshed!")


# Create the dropdown (selectbox)
selected_label = utils.get_shared_time_range_selection("Select Time Range:")

# Filter by the label defined in our config
filtered_df = utils.filter_by_recency(df, window_label=selected_label, mode=time_window_filtering_mode)

# 3. Apply the resolution defined in our config
time_window_df = utils.resample_data(
    filtered_df, 
    selected_label, 
    sum_cols=['rain_pulses', 'wind_pulses_total'],
    cumulative_cols=['rain_pulses']
)


# #--------------------- temperature -----------------------------
utils.TimeSeriesDashboardItem(
    metric_title="Temperature", 
    unit="°C", 
    y_col_main="sht_temperature_avg", 
    y_col_main_label="average",
    main_color="#2563EB" # Reddish
).add_extra_series(
    col_name="sht_temperature_max", 
    label="max", 
    color="#93C5FD" # Salmon
).add_extra_series(
    col_name="sht_temperature_min",
    label="min",
    color="#1D4ED8"
).plot(time_window_df)

# #--------------------- humidity -----------------------------
utils.TimeSeriesDashboardItem(
    metric_title="Humidity", 
    unit="%", 
    y_col_main="sht_humidity_avg", 
    y_col_main_label="average",
    main_color="#2563EB" # Blue
).add_extra_series(
    col_name="sht_humidity_max",
    label="max",
    color="#93C5FD"
).add_extra_series(
    col_name="sht_humidity_min",
    label="min",
    color="#1D4ED8"
).plot(time_window_df, format=".0f")

 # #--------------------- pressure -----------------------------
if not time_window_df.empty:
    time_window_df["bmp_pressure_avg"] = time_window_df["bmp_pressure_avg"] / 100
    if "bmp_pressure_min" in time_window_df.columns:
        time_window_df["bmp_pressure_min"] = time_window_df["bmp_pressure_min"] / 100
    if "bmp_pressure_max" in time_window_df.columns:
        time_window_df["bmp_pressure_max"] = time_window_df["bmp_pressure_max"] / 100

utils.TimeSeriesDashboardItem(
    metric_title="Pressure", 
    unit="hPa", 
    y_col_main="bmp_pressure_avg", 
    main_color="#2563EB" # Blue
).add_extra_series(
    col_name="bmp_pressure_max",
    label="max",
    color="#1D4ED8"
).add_extra_series(
    col_name="bmp_pressure_min",
    label="min",
    color="#93C5FD"
).plot(time_window_df, format=".0f")

 # #--------------------- light intensity -----------------------------
utils.TimeSeriesDashboardItem(
    metric_title="Light intensity", 
    unit="W/m²", 
    y_col_main="light_intensity_avg", 
    main_color="#2563EB" # Gold
).add_extra_series(
    col_name="light_intensity_max",
    label="max",
    color="#93C5FD"
).add_extra_series(
    col_name="light_intensity_min",
    label="min",
    color="#1D4ED8"
).plot(time_window_df)

 # #--------------------- wind speed -----------------------------
utils.TimeSeriesDashboardItem(
    metric_title="Wind speed",
    unit="km/h",
    y_col_main="wind_speed_kmh_avg",
    y_col_main_label="average",
    main_color="#1E90FF" # Grey
).add_extra_series(
    col_name="wind_speed_kmh_max",
    label="max",
    color="#93C5FD"
).plot(time_window_df, format=".0f")

 # #--------------------- wind direction -----------------------------
utils.TimeSeriesDashboardItem(
    metric_title="Wind direction", 
    unit="°", 
    y_col_main="wind_direction", 
    main_color="#1E90FF" # Purple
).plot(time_window_df, y_limits=[0, 360], format=".0f", chart_type='scatter')

 # #--------------------- rain pulses -----------------------------
utils.TimeSeriesDashboardItem(
    metric_title="Rain pulses", 
    unit="", 
    y_col_main="rain_pulses", 
    y_col_main_label="rain pulses",
    main_color="#93C5FD" # Turquoise
).add_extra_series(
    col_name="rain_pulses_cumulated",
    label="cummulated rain pulses",
    color="#00CED1"
).plot(time_window_df,format=".0f")

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
