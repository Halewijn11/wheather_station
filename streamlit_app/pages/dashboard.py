import streamlit as st
import importlib
import utils
importlib.reload(utils)
from streamlit_extras.metric_cards import style_metric_cards
import altair as alt
import numpy as np

st.title("Wheather dashboard")

# #--------------------- general preamble to load data -----------------------------

gid = '2078525972'
google_sheet_df = utils.get_google_sheet_df(sheet_gid=gid)
df = utils.tidy_google_sheet_df(google_sheet_df,decoded_payload_data_col_name_list=[])
time_window_df = df.tail(50)

# #--------------------- temperature -----------------------------
# temperature_colname = utils.get_full_payload_colname('temperature')
temperature_colname = 'temp_avg'

col1, col2 = st.columns([1, 1])
latest = time_window_df[temperature_colname].iloc[-1]
with col1:
    st.metric("Temperature", f"{latest:.1f} °C")

with col2:
    spark = alt.Chart(time_window_df.tail(50)).mark_line().encode(
        x=alt.X("received_at", axis=None),
        y=alt.Y(
            temperature_colname,
            axis=alt.Axis(
                    labels=True,
                    ticks=True,
                    title="Temp (°C)",
                ),
            scale=alt.Scale(domain=[
                time_window_df[temperature_colname].min(),
                time_window_df[temperature_colname].max()
            ])
        
        ),
        tooltip=[
        alt.Tooltip("received_at:T", title="Time"),
        alt.Tooltip(temperature_colname, title="Temp (°C)", format=".1f")
    ]
    ).properties(height=100)
    st.altair_chart(spark, use_container_width=True)


# #--------------------- humidity -----------------------------
# pressure_colname = utils.get_full_payload_colname('pressure')
y_variable_colname = 'humidity_avg'
y_variable_name = 'humidity'
y_variable_unuit = '%'
col1, col2 = st.columns([1, 1])
latest = np.round(time_window_df[y_variable_colname].iloc[-1],1)
with col1:
    st.metric(y_variable_name, f"{latest:.1f} {y_variable_unuit}")

with col2:
    spark = alt.Chart(time_window_df.tail(50)).mark_line().encode(
        x=alt.X("received_at", axis=None),
        y=alt.Y(
            y_variable_colname,
            axis=alt.Axis(
                    labels=True,
                    ticks=True,
                    title=f"{y_variable_name} ({y_variable_unuit})",
                ),
            scale=alt.Scale(domain=[
                time_window_df[y_variable_colname].min(),
                time_window_df[y_variable_colname].max()
            ])
        ),
                tooltip=[
        alt.Tooltip("received_at:T", title="Time"),
        alt.Tooltip(y_variable_colname, title="hPa", format=".1f")
    ]
    ).properties(height=100)
    st.altair_chart(spark, use_container_width=True)



# # #--------------------- pressure -----------------------------
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
    