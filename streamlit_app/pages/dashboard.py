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





st.title("Wheather dashboard...")


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
    utils.get_forecast_df.clear()
    st.success("Data refreshed!")


# Create the dropdown (selectbox)
selected_label = utils.get_shared_time_range_selection("Select Time Range:")

# Forecast toggle — only available for the "Since Midnight" view
show_forecast = False
if selected_label == "Since Midnight":
    show_forecast = st.toggle("Show weather forecast", value=False)

forecast_df = pd.DataFrame()
if show_forecast:
    forecast_df = utils.get_forecast_df()

# Filter by the label defined in our config
filtered_df = utils.filter_by_recency(df, window_label=selected_label, mode=time_window_filtering_mode)

# 3. Apply the resolution defined in our config
time_window_df = utils.resample_data(
    filtered_df, 
    selected_label, 
    sum_cols=['rain_mm', 'wind_pulses_total'],
    cumulative_cols=['rain_mm']
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
).plot(time_window_df, prediction_df=forecast_df, prediction_col='temp',
       min_max_df=filtered_df, min_col='sht_temperature_avg', max_col='sht_temperature_avg')

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
).plot(time_window_df, format=".0f", prediction_df=forecast_df, prediction_col='humidity')

 # #--------------------- pressure -----------------------------
if not time_window_df.empty:
    time_window_df["bmp_pressure_avg"] = time_window_df["bmp_pressure_avg"] / 100
    if "bmp_pressure_min" in time_window_df.columns:
        time_window_df["bmp_pressure_min"] = time_window_df["bmp_pressure_min"] / 100
    if "bmp_pressure_max" in time_window_df.columns:
        time_window_df["bmp_pressure_max"] = time_window_df["bmp_pressure_max"] / 100

    latest_pressure = time_window_df["bmp_pressure_avg"].iloc[-1]

    gauge_col, chart_col = st.columns([1, 2])
    with gauge_col:
        st.markdown(
            utils.render_analog_gauge(latest_pressure, min_val=973, max_val=1053, unit="hPa", width=224, height=168),
            unsafe_allow_html=True
        )
    with chart_col:
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
        ).plot(time_window_df, format=".1f", prediction_df=forecast_df, prediction_col='pressure', show_metric=False)

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
    main_color="#1E90FF"
).plot(
    time_window_df,
    chart_type='scatter',
    y_limits=[0, 360],
    format=".0f",
    prediction_df=forecast_df,
    prediction_col='wind_deg',
    y_tick_labels={0: 'N', 45: 'NE', 90: 'E', 135: 'SE', 180: 'S', 225: 'SW', 270: 'W', 315: 'NW', 360: 'N'}
)

 # #--------------------- wind speed forecast -----------------------------
# The sensor records wind pulses (not m/s), so forecast wind speed is shown separately.
if show_forecast and not forecast_df.empty:
    utils.TimeSeriesDashboardItem(
        metric_title="Wind speed (forecast)",
        unit="m/s",
        y_col_main="wind_speed",
        main_color="#F97316"
    ).plot(forecast_df)

 # #--------------------- rain pulses -----------------------------
utils.TimeSeriesDashboardItem(
    metric_title="Rain",
    unit="mm",
    y_col_main="rain_mm",
    y_col_main_label="rain (mm)",
    main_color="#93C5FD" # Turquoise
).add_extra_series(
    col_name="rain_mm_cumulated",
    label="cumulated rain (mm)",
    color="#00CED1"
).plot(time_window_df,format=".1f")

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
