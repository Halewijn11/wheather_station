import streamlit as st
import importlib
import utils
import pandas as pd
import altair as alt
from streamlit_extras.metric_cards import style_metric_cards
importlib.reload(utils)

st.title("Status")

# Apply custom CSS to metric cards
# style_metric_cards(
#     font_size_value="16px",       # <--- make value font smaller
#     font_size_label="12px"        # optional: smaller label
# )

# #--------------------- general preamble to load data -----------------------------

gid = '2078525972'
google_sheet_df = utils.get_google_sheet_df(sheet_gid=gid)
df = utils.tidy_google_sheet_df(google_sheet_df,decoded_payload_data_col_name_list=[])
time_window_df = df.tail(50)

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


# for the dbm
col1, col2 = st.columns([1, 1])
latest = time_window_df["uplink_message_rx_metadata_0_channel_rssi"].iloc[-1]
with col1:
    st.metric("last RSSI", f"{latest:.1f} dBm")

with col2:
    spark = alt.Chart(time_window_df.tail(50)).mark_line().encode(
        x=alt.X("received_at", axis=None),
        y=alt.Y(
            "uplink_message_rx_metadata_0_channel_rssi",
            axis=alt.Axis(
                    labels=True,
                    ticks=True,
                    title="rssi",
                ),
            scale=alt.Scale(domain=[
                time_window_df["uplink_message_rx_metadata_0_channel_rssi"].min(),
                time_window_df["uplink_message_rx_metadata_0_channel_rssi"].max()
            ])
        )
    ).properties(height=100)
    st.altair_chart(spark, use_container_width=True)


#for the snr
col1, col2 = st.columns([1, 1])
latest = time_window_df["uplink_message_rx_metadata_0_snr"].iloc[-1]
with col1:
    st.metric("last SNR", f"{latest:.1f}")

with col2:
    spark = alt.Chart(time_window_df.tail(50)).mark_line().encode(
        x=alt.X("received_at", axis=None),
        y=alt.Y(
            "uplink_message_rx_metadata_0_snr",
            axis=alt.Axis(
                    labels=True,
                    ticks=True,
                    title="rssi",
                ),
            scale=alt.Scale(domain=[
                time_window_df["uplink_message_rx_metadata_0_snr"].min(),
                time_window_df["uplink_message_rx_metadata_0_snr"].max()
            ])
        )
    ).properties(height=100)
    st.altair_chart(spark, use_container_width=True)


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

#histogram of the transmission timegap
recent_df = utils.filter_by_recency(df, hours = 24)
transmission_timegap_colname = 'received_at_td_minutes'
# fan_rpm_colname = utils.get_full_payload_colname('fan_rpm')
col1, col2 = st.columns([1, 1])
latest = recent_df[transmission_timegap_colname].iloc[-1]
latest = pd.to_timedelta(latest, unit="m")
latest = utils.format_timedelta(latest)
# latest = utils.format_timedelta(latest)
# print(latest)
# utils.format_timedelta()
with col1:
    st.metric("last transmission timegap", f"{latest}")

with col2:
    spark = alt.Chart(recent_df).mark_point().encode(
        x=alt.X("received_at", axis=None),
        y=alt.Y(
            transmission_timegap_colname,
            axis=alt.Axis(
                    labels=True,
                    ticks=True,
                    title="timegap (m)",
                ),
            scale=alt.Scale(domain=[
                0,
                recent_df[transmission_timegap_colname].max()
            ])
        )
    ).properties(height=100)
    st.altair_chart(spark, use_container_width=True)



# utils.draw_histogram(recent_df, 'received_at_td')
    