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


# #--------------------- calculate some metrics -----------------------------
google_sheet_df = utils.get_google_sheet_df()
df = utils.tidy_google_sheet_df(google_sheet_df)
last_measurement_string =  utils.get_last_measurement_string(df)
time_window_df = df.tail(50)
time_window_df.to_csv('delete.csv')
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


# Layout
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
    