import streamlit as st
import importlib
import utils
import pandas as pd
import altair as alt
from streamlit_extras.metric_cards import style_metric_cards
import os
from streamlit_gsheets import GSheetsConnection

importlib.reload(utils)

st.title("Status")

debug = 0
cached_time = 0
time_window_hours = 1
time_window_filtering_mode = 'last_session'


# Apply custom CSS to metric cards
# style_metric_cards(
#     font_size_value="16px",       # <--- make value font smaller
#     font_size_label="12px"        # optional: smaller label
# )

# #--------------------- general preamble to load data -----------------------------

# url = "https://docs.google.com/spreadsheets/d/1OW-KdOF9BSuR66o9qbumSkNck3TlXb1himbQnLeFvVE/edit?gid=0#gid=0"
# conn = st.connection("gsheets", type=GSheetsConnection)
# google_sheet_df = conn.read(spreadsheet=url, ttl=cached_time)

# if debug == True:
#     st.write("Available columns in Sheet:", google_sheet_df.columns.tolist()) # Add this line
current_dir = os.path.dirname(__file__)
asset_path = os.path.join(current_dir, "..", "assets")
discharge_csv_path = os.path.join(asset_path, 'LiPo_smooth_discharge_curve.csv')
discharge_curve = pd.read_csv(discharge_csv_path)

df = utils.get_data(discharge_curve)
# df  = pd.read_csv('data.csv')

# --- NEW: Time Window Selection ---
time_options = {
    "Last Hour": 1,
    "Last 24 Hours": 24,
    "Last Week": 168
}

selected_label = st.selectbox(
    "Select Time Range:",
    options=list(time_options.keys()),
    index=0 
)

time_window_hours = time_options[selected_label]

# Now filter your data using this dynamic variable
time_window_df = utils.filter_by_recency(df, hours=time_window_hours)


# #--------------------- sample the dataframe to a lower resolution -----------------------------


# 2. Filter by the number of hours defined in our config
filtered_df = utils.filter_by_recency(df, hours = time_window_hours, mode = time_window_filtering_mode)

# 3. Apply the resolution defined in our config
time_window_df = utils.resample_data(filtered_df, selected_label)

# #--------------------- calculate some metrics -----------------------------
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


# #--------------------- battery status -----------------------------
col_icon, col_text, buffer = st.columns([2, 3, 20])
#get the battery voltage from the last record
battery_percentage = time_window_df['battery_percentage'].iloc[-1]
img_filepath = utils.get_battery_icon_filepath(battery_percentage, asset_path + '/', flat = True)

col1,col2, buffer = st.columns([7, 20,30])
with col1:
    st.image(img_filepath, width=100) 

with col2:
    # Adjust the 'px' value (e.g., 25px) to move the text lower or higher
    st.markdown(
        f"""
        <div style="margin-top: 4px; font-size: 20px; font-weight: bold;">
            {int(battery_percentage)}%
        </div>
        """, 
        unsafe_allow_html=True
    )

# #--------------------- power -----------------------------
utils.plot_metric_with_graph(
    time_window_df = time_window_df,
    y_variable_colname = 'power_avg',
    y_variable_unit = 'mW',
    y_variable_prefix_text = 'avg power',
    y_label = "power (mW)",
    x_label = 'received at'
)

# #--------------------- battery_percentage -----------------------------
utils.plot_metric_with_graph(
    time_window_df = time_window_df,
    y_variable_colname = 'battery_percentage',
    y_variable_unit = '%',
    y_variable_prefix_text = 'battery percentage',
    y_label = "battery percentage (%)",
    x_label = 'received at'
)

# #--------------------- battery_voltage -----------------------------
utils.plot_metric_with_graph(
    time_window_df = time_window_df,
    y_variable_colname = 'voltage_avg',
    y_variable_unit = 'V',
    y_variable_prefix_text = 'avg voltage',
    y_label = "voltage (V)",
    x_label = 'received at'
)

# #--------------------- snr -----------------------------
utils.plot_metric_with_graph(
    time_window_df = time_window_df,
    y_variable_colname = 'snr',
    y_variable_unit = 'snr',
    y_variable_prefix_text = 'snr',
    y_label = "snr",
    x_label = 'received at'
)

# #--------------------- rssi -----------------------------
utils.plot_metric_with_graph(
    time_window_df = time_window_df,
    y_variable_colname = 'rssi',
    y_variable_unit = 'dBm',
    y_variable_prefix_text = 'rssi',
    y_label = "rssi (dBm)",
    x_label = 'received at'
)

# #--------------------- transmission timegaps -----------------------------
utils.plot_metric_with_graph(
    time_window_df = time_window_df,
    y_variable_colname = 'received_at_td_minutes',
    y_variable_unit = 'minutes',
    y_variable_prefix_text = 'tx timegap',
    y_label = "tx timegap",
    x_label = 'received at'
)



# # for the dbm
# col1, col2 = st.columns([1, 1])
# latest = time_window_df["uplink_message_rx_metadata_0_channel_rssi"].iloc[-1]
# with col1:
#     st.metric("last RSSI", f"{latest:.1f} dBm")

# with col2:
#     spark = alt.Chart(time_window_df.tail(50)).mark_line().encode(
#         x=alt.X("received_at", axis=None),
#         y=alt.Y(
#             "uplink_message_rx_metadata_0_channel_rssi",
#             axis=alt.Axis(
#                     labels=True,
#                     ticks=True,
#                     title="rssi",
#                 ),
#             scale=alt.Scale(domain=[
#                 time_window_df["uplink_message_rx_metadata_0_channel_rssi"].min(),
#                 time_window_df["uplink_message_rx_metadata_0_channel_rssi"].max()
#             ])
#         )
#     ).properties(height=100)
#     st.altair_chart(spark, use_container_width=True)


# #for the snr
# col1, col2 = st.columns([1, 1])
# latest = time_window_df["uplink_message_rx_metadata_0_snr"].iloc[-1]
# with col1:
#     st.metric("last SNR", f"{latest:.1f}")

# with col2:
#     spark = alt.Chart(time_window_df.tail(50)).mark_line().encode(
#         x=alt.X("received_at", axis=None),
#         y=alt.Y(
#             "uplink_message_rx_metadata_0_snr",
#             axis=alt.Axis(
#                     labels=True,
#                     ticks=True,
#                     title="rssi",
#                 ),
#             scale=alt.Scale(domain=[
#                 time_window_df["uplink_message_rx_metadata_0_snr"].min(),
#                 time_window_df["uplink_message_rx_metadata_0_snr"].max()
#             ])
#         )
#     ).properties(height=100)
#     st.altair_chart(spark, use_container_width=True)


# #for the fan speed
# fan_rpm_colname = utils.get_full_payload_colname('fan_rpm')
# col1, col2 = st.columns([1, 1])
# latest = time_window_df[fan_rpm_colname].iloc[-1]
# with col1:
#     st.metric("last fan speed RPM", f"{latest:.1f}")

# with col2:
#     spark = alt.Chart(time_window_df.tail(50)).mark_line().encode(
#         x=alt.X("received_at", axis=None),
#         y=alt.Y(
#             fan_rpm_colname,
#             axis=alt.Axis(
#                     labels=True,
#                     ticks=True,
#                     title="rssi",
#                 ),
#             scale=alt.Scale(domain=[
#                 time_window_df[fan_rpm_colname].min(),
#                 2000
#                 # time_window_df[fan_rpm_colname].max()
#             ])
#         )
#     ).properties(height=100)
#     st.altair_chart(spark, use_container_width=True)

# #histogram of the transmission timegap
# recent_df = utils.filter_by_recency(df, hours = 24)
# transmission_timegap_colname = 'received_at_td_minutes'
# # fan_rpm_colname = utils.get_full_payload_colname('fan_rpm')
# col1, col2 = st.columns([1, 1])
# latest = recent_df[transmission_timegap_colname].iloc[-1]
# latest = pd.to_timedelta(latest, unit="m")
# latest = utils.format_timedelta(latest)
# # latest = utils.format_timedelta(latest)
# # print(latest)
# # utils.format_timedelta()
# with col1:
#     st.metric("last transmission timegap", f"{latest}")

# with col2:
#     spark = alt.Chart(recent_df).mark_point().encode(
#         x=alt.X("received_at", axis=None),
#         y=alt.Y(
#             transmission_timegap_colname,
#             axis=alt.Axis(
#                     labels=True,
#                     ticks=True,
#                     title="timegap (m)",
#                 ),
#             scale=alt.Scale(domain=[
#                 0,
#                 recent_df[transmission_timegap_colname].max()
#             ])
#         )
#     ).properties(height=100)
#     st.altair_chart(spark, use_container_width=True)



# utils.draw_histogram(recent_df, 'received_at_td')


