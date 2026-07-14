import streamlit as st
import pandas as pd
import utils
import os

st.title("Overlay")
st.caption("Alle grafieken over elkaar, elke reeks genormaliseerd naar 0-100% van haar eigen bereik. Echte waarden blijven zichtbaar via de tooltip.")

current_dir = os.path.dirname(__file__)
asset_path = os.path.join(current_dir, "..", "assets")
discharge_csv_path = os.path.join(asset_path, 'LiPo_smooth_discharge_curve.csv')
discharge_curve = pd.read_csv(discharge_csv_path)
df = utils.get_data(discharge_curve)

selected_label = utils.get_shared_time_range_selection("Select Time Range:")

filtered_df = utils.filter_by_recency(df, window_label=selected_label, mode='last_session')
time_window_df = utils.resample_data(filtered_df, sum_cols=['rain_mm'])

if not time_window_df.empty and 'bmp_pressure_avg' in time_window_df.columns:
    time_window_df["bmp_pressure_avg"] = time_window_df["bmp_pressure_avg"] / 100

ALL_SERIES = [
    {'col': 'sht_temperature_avg', 'label': 'Temperatuur', 'unit': '°C', 'format': '.1f'},
    {'col': 'sht_humidity_avg', 'label': 'Vochtigheid', 'unit': '%', 'format': '.0f'},
    {'col': 'bmp_pressure_avg', 'label': 'Druk', 'unit': 'hPa', 'format': '.1f'},
    {'col': 'light_intensity_avg', 'label': 'Licht', 'unit': 'W/m²', 'format': '.1f'},
    {'col': 'wind_speed_kmh_avg', 'label': 'Windsnelheid (avg)', 'unit': 'km/h', 'format': '.0f'},
    {'col': 'rain_mm', 'label': 'Regen', 'unit': 'mm', 'format': '.1f'},
    {'col': 'wind_speed_kmh_max', 'label': 'Windsnelheid (max)', 'unit': 'km/h', 'format': '.0f'},
]
for s in ALL_SERIES:
    s['color'] = utils.OVERLAY_SERIES_COLORS[s['col']]

row_size = 4
rows = [ALL_SERIES[i:i + row_size] for i in range(0, len(ALL_SERIES), row_size)]

enabled_series = []
for row in rows:
    toggle_cols = st.columns(row_size)
    for col, s in zip(toggle_cols, row):
        with col:
            default_on = s['col'] == 'sht_temperature_avg'
            if st.checkbox(s['label'], value=default_on, key=f"overlay_toggle_{s['col']}"):
                enabled_series.append(s)

if time_window_df.empty:
    st.warning("No data for the selected time range")
elif not enabled_series:
    st.info("Selecteer minstens één reeks om te tonen.")
else:
    chart = utils.plot_normalized_overlay(time_window_df, enabled_series)
    st.altair_chart(chart, use_container_width=True)
