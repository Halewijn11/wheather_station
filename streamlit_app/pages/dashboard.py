import streamlit as st
import pandas as pd
import utils
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_autorefresh import st_autorefresh
import altair as alt
import numpy as np
import os
from streamlit_gsheets import GSheetsConnection

debug = 0
cached_time = 0
time_window_hours = 1
time_window_filtering_mode = 'last_session'

# Rerun the page every 60s so it picks up new data as soon as the
# 3-minute get_data() cache (see utils.py) expires, without needing
# a manual "Refresh Data" click.
st_autorefresh(interval=60_000, key="dashboard_autorefresh")





st.title("Grafieken")

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

st.header('Affligem, Belgium')

datapoint_col, refresh_col = st.columns([3, 1], vertical_alignment="center")
with datapoint_col:
    utils.show_last_datapoint_caption(df)
with refresh_col:
    refresh_clicked = st.button("Refresh Data")

if refresh_clicked:
    # .clear() occasionally hits Streamlit's cache-storage internals before
    # they're fully initialized (seen right after a cold start on Streamlit
    # Cloud) and raises AttributeError. Not clearing is harmless here since
    # the cache has a 3min TTL anyway, so don't let it crash the page.
    try:
        utils.get_data.clear()
        utils.get_forecast_df.clear()
    except AttributeError:
        pass
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
    sum_cols=['rain_mm', 'wind_pulses_total'],
    cumulative_cols=['rain_mm']
)


# #--------------------- temperature -----------------------------
st.subheader("Temperature")
temp_24h_ago_val, _ = utils.value_at_offset(df, "sht_temperature_avg", 24 * 3600)
humidity_24h_ago_val, _ = utils.value_at_offset(df, "sht_humidity_avg", 24 * 3600)

# Read toggle state up front to decide which series to add; the checkboxes
# themselves are declared later, via extra_controls, inside the chart's
# second column (above the chart).
show_temp_max = st.session_state.get("temp_show_max", False)
show_temp_min = st.session_state.get("temp_show_min", False)
show_heat_index = st.session_state.get("temp_show_heat_index", False)

current_temp = None
current_heat_index = None
heat_index_24h_ago_val = None
if not time_window_df.empty:
    current_temp = time_window_df["sht_temperature_avg"].iloc[-1]
    time_window_df["heat_index_avg"] = utils.compute_heat_index_series(
        time_window_df["sht_temperature_avg"], time_window_df["sht_humidity_avg"]
    )
    current_heat_index = time_window_df["heat_index_avg"].iloc[-1]
    if pd.notna(current_heat_index) and temp_24h_ago_val is not None and humidity_24h_ago_val is not None:
        heat_index_24h_ago_val = utils.compute_heat_index_series(temp_24h_ago_val, humidity_24h_ago_val)


def _delta_caption(current_val, ago_val, label):
    if current_val is None or ago_val is None or pd.isna(current_val) or pd.isna(ago_val):
        return None
    delta = current_val - ago_val
    arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "▶")
    arrow_color = "#16A34A" if delta > 0 else ("#DC2626" if delta < 0 else "#6B7280")
    return f"{label} {delta:+.1f}°C <span style='color:{arrow_color}'>{arrow}</span>"


temp_chart = utils.TimeSeriesDashboardItem(
    metric_title="Current T",
    unit="°C",
    y_col_main="sht_temperature_avg",
    y_col_main_label="average",
    main_color="#2563EB" # Reddish
)
if show_temp_max:
    temp_chart.add_extra_series(col_name="sht_temperature_max", label="max", color="#16A34A")
if show_temp_min:
    temp_chart.add_extra_series(col_name="sht_temperature_min", label="min", color="#DC2626")
if show_heat_index:
    temp_chart.add_extra_series(col_name="heat_index_avg", label="heat index", color="#EA580C")

def _render_temp_toggles():
    temp_toggle_max, temp_toggle_min, temp_toggle_hi = st.columns(3)
    with temp_toggle_max:
        st.checkbox("Max", value=show_temp_max, key="temp_show_max")
    with temp_toggle_min:
        st.checkbox("Min", value=show_temp_min, key="temp_show_min")
    with temp_toggle_hi:
        st.checkbox("Heat Index", value=show_heat_index, key="temp_show_heat_index")

temp_metric_col, temp_chart_col = st.columns([1, 2])
with temp_metric_col:
    if current_temp is not None and pd.notna(current_temp):
        st.metric("Current T", f"{current_temp:.1f} °C")
        temp_delta_caption = _delta_caption(current_temp, temp_24h_ago_val, "24h ago")
        if temp_delta_caption:
            st.caption(temp_delta_caption, unsafe_allow_html=True)

    if current_heat_index is not None and pd.notna(current_heat_index):
        st.metric("Current Heat Index", f"{current_heat_index:.1f} °C")
        hi_delta_caption = _delta_caption(current_heat_index, heat_index_24h_ago_val, "24h ago")
        if hi_delta_caption:
            st.caption(hi_delta_caption, unsafe_allow_html=True)

with temp_chart_col:
    temp_chart.plot(time_window_df, prediction_df=forecast_df, prediction_col='temp',
                     min_max_df=filtered_df, min_col='sht_temperature_avg', max_col='sht_temperature_avg',
                     extra_controls=_render_temp_toggles, max_line_label="max",
                     show_min_line=True, min_line_label="min",
                     show_metric=False)

# #--------------------- humidity -----------------------------
st.subheader("Humidity")
utils.TimeSeriesDashboardItem(
    metric_title="Current",
    unit="%",
    y_col_main="sht_humidity_avg",
    y_col_main_label="average",
    main_color="#2563EB" # Blue
).plot(time_window_df, format=".0f", prediction_df=forecast_df, prediction_col='humidity', max_line_label="max",
       show_min_line=True, min_line_label="min")

 # #--------------------- pressure -----------------------------
st.subheader("Pressure")
pressure_24h_ago_val, _ = utils.value_at_offset(df, "bmp_pressure_avg", 24 * 3600)
if pressure_24h_ago_val is not None:
    pressure_24h_ago_val = pressure_24h_ago_val / 100

if not time_window_df.empty:
    time_window_df["bmp_pressure_avg"] = time_window_df["bmp_pressure_avg"] / 100
    if "bmp_pressure_min" in time_window_df.columns:
        time_window_df["bmp_pressure_min"] = time_window_df["bmp_pressure_min"] / 100
    if "bmp_pressure_max" in time_window_df.columns:
        time_window_df["bmp_pressure_max"] = time_window_df["bmp_pressure_max"] / 100

    utils.TimeSeriesDashboardItem(
        metric_title="Current",
        unit="hPa",
        y_col_main="bmp_pressure_avg",
        main_color="#2563EB" # Blue
    ).plot(time_window_df, format=".1f", prediction_df=forecast_df, prediction_col='pressure', max_line_label="max",
           show_min_line=True, min_line_label="min",
           compare_val=pressure_24h_ago_val, compare_label="24h ago")

 # #--------------------- light intensity -----------------------------
st.subheader("Light intensity")
if time_window_df.empty:
    st.warning("No data for Light intensity")
else:
    light_avg_col = "light_intensity_avg"
    light_max_col = "light_intensity_max"
    light_avg_color = "#2563EB"
    light_max_color = "#F59E0B"  # Amber area for max

    col1, col2 = st.columns([1, 2])
    with col1:
        latest_light_val = time_window_df[light_avg_col].iloc[-1]
        st.metric("Current", f"{latest_light_val:.1f} W/m²")

        energy_kwh, energy_mj = utils.compute_todays_solar_energy(df, col=light_avg_col)
        st.caption(f"Energie vandaag: {energy_kwh:.2f} kWh/m² ")

    with col2:
        time_window_df = time_window_df.copy()
        time_window_df["toa_w_m2"] = utils.toa_irradiance_series(time_window_df["received_at"])
        toa_color = "#F97316"  # matches the forecast reference-line color used elsewhere

        light_melted = time_window_df[["received_at", light_avg_col, light_max_col, "toa_w_m2"]].rename(
            columns={light_avg_col: "average", light_max_col: "max", "toa_w_m2": "TOA"}
        ).melt(id_vars=["received_at"], value_vars=["average", "max", "TOA"],
               var_name="Variable", value_name="Value")

        y_min = float(light_melted["Value"].min())
        y_max = float(light_melted["Value"].max())
        padding = (y_max - y_min) * 0.1 if y_max != y_min else 1
        y_domain = [y_min - padding, y_max + padding]

        color_scale = alt.Scale(domain=["average", "max", "TOA"], range=[light_avg_color, light_max_color, toa_color])

        base = alt.Chart(light_melted).encode(
            x=alt.X("received_at:T", title=None, axis=alt.Axis(labelExpr=utils.DATE_AT_MIDNIGHT_LABEL_EXPR)),
            y=alt.Y("Value:Q", title="W/m²", scale=alt.Scale(domain=y_domain, clamp=True)),
            color=alt.Color("Variable:N", scale=color_scale, title=None,
                             legend=alt.Legend(orient="bottom"))
        )

        max_area = base.transform_filter(alt.datum.Variable == "max").mark_area(opacity=0.4)
        avg_line = base.transform_filter(alt.datum.Variable == "average").mark_line(strokeWidth=1)
        toa_line = base.transform_filter(alt.datum.Variable == "TOA").mark_line(
            strokeWidth=2, strokeDash=[6, 3], opacity=0.8
        )

        nearest = alt.selection_point(on='mouseover', nearest=True, fields=["received_at"],
                                      encodings=['x'], empty=False)

        selectors = alt.Chart(time_window_df).mark_rule().encode(
            x="received_at:T",
            opacity=alt.value(0),
            tooltip=[
                alt.Tooltip("received_at:T", title="Time", format='%d %b %H:%M'),
                alt.Tooltip(f"{light_avg_col}:Q", title="average", format='.2f'),
                alt.Tooltip(f"{light_max_col}:Q", title="max", format='.2f'),
                alt.Tooltip("toa_w_m2:Q", title="TOA", format='.1f'),
            ]
        ).add_params(nearest)

        rules = alt.Chart(light_melted).mark_rule(color='#A1A6B4', strokeDash=[4, 4]).encode(
            x="received_at:T",
        ).transform_filter(nearest)

        points = base.mark_point(size=30).encode(
            opacity=alt.condition(nearest, alt.value(1), alt.value(0))
        )

        day_lines = utils.day_boundary_chart(utils.get_day_boundaries(time_window_df["received_at"]))

        # Full-width horizontal reference line through the max area's peak,
        # labeled with the max value just above it.
        light_max_peak = time_window_df[light_max_col].max()
        light_max_line = None
        light_max_label = None
        if pd.notna(light_max_peak):
            light_max_line = alt.Chart(pd.DataFrame({'y': [light_max_peak]})).mark_rule(
                color='#EF4444', strokeDash=[4, 4], strokeWidth=1, opacity=0.6
            ).encode(y=alt.Y('y:Q', scale=alt.Scale(domain=y_domain, clamp=True)))

            light_max_label_df = pd.DataFrame({
                "received_at": [time_window_df["received_at"].min()],
                'y': [light_max_peak],
                'label': [f"max {light_max_peak:.1f} W/m²"],
            })
            light_max_label = alt.Chart(light_max_label_df).mark_text(
                align='left', baseline='bottom', dy=-2, color='#EF4444', fontSize=11
            ).encode(
                x=alt.X("received_at:T"),
                y=alt.Y('y:Q', scale=alt.Scale(domain=y_domain, clamp=True)),
                text='label:N'
            )

        light_layers = (
            ([day_lines] if day_lines is not None else [])
            + ([light_max_line, light_max_label] if light_max_line is not None else [])
            + [max_area, avg_line, toa_line, selectors, rules, points]
        )

        light_chart = alt.layer(*light_layers).properties(
            width='container', height=280
        ).interactive()

        st.altair_chart(light_chart, use_container_width=True)

 # #--------------------- wind speed -----------------------------
st.subheader("Wind speed")
utils.TimeSeriesDashboardItem(
    metric_title="Current",
    unit="km/h",
    y_col_main="wind_speed_kmh_avg",
    y_col_main_label="average",
    main_color="#1E90FF" # Grey
).add_extra_series(
    col_name="wind_speed_kmh_max",
    label="max",
    color="#93C5FD"
).plot(time_window_df, format=".0f", max_line_col="wind_speed_kmh_max")

 # #--------------------- wind direction -----------------------------
st.subheader("Wind direction")
utils.TimeSeriesDashboardItem(
    metric_title="Current",
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
    y_tick_labels={0: 'N', 45: 'NE', 90: 'E', 135: 'SE', 180: 'S', 225: 'SW', 270: 'W', 315: 'NW', 360: 'N'},
    show_max_line=False
)

 # #--------------------- wind speed forecast -----------------------------
# The sensor records wind pulses (not m/s), so forecast wind speed is shown separately.
if show_forecast and not forecast_df.empty:
    st.subheader("Wind speed (forecast)")
    utils.TimeSeriesDashboardItem(
        metric_title="Current",
        unit="m/s",
        y_col_main="wind_speed",
        main_color="#F97316"
    ).plot(forecast_df)

 # #--------------------- rain pulses -----------------------------
st.subheader("Rain")
utils.TimeSeriesDashboardItem(
    metric_title="Current",
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

st.markdown(
    """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 24px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
