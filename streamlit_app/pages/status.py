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

# Apply custom CSS to metric cards
# style_metric_cards(
#     font_size_value="16px",       # <--- make value font smaller
#     font_size_label="12px"        # optional: smaller label
# )

# #--------------------- general preamble to load data -----------------------------

url = "https://docs.google.com/spreadsheets/d/1OW-KdOF9BSuR66o9qbumSkNck3TlXb1himbQnLeFvVE/edit?gid=0#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)
google_sheet_df = conn.read(spreadsheet=url, ttl=cached_time)

if debug == True:
    st.write("Available columns in Sheet:", google_sheet_df.columns.tolist()) # Add this line

df = utils.tidy_google_sheet_df(google_sheet_df)
# df  = pd.read_csv('data.csv')
time_window_df = utils.filter_by_recency(df, hours = time_window_hours)

# 1. Get the directory that this specific file (dashboard.py) is in
current_dir = os.path.dirname(__file__)

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


# #--------------------- rssi -----------------------------
utils.plot_metric_with_graph(
    time_window_df = time_window_df,
    y_variable_colname = 'rssi',
    y_variable_unit = 'dBm',
    y_variable_prefix_text = 'rssi',
    y_label = "rssi (dBm)",
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


