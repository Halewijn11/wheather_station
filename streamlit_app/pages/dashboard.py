import streamlit as st
import pandas as pd
import utils
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_autorefresh import st_autorefresh
import altair as alt
import numpy as np
import os
import pytz
from datetime import datetime
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

try:
    ventilator_df = utils.get_ventilator_data()
except Exception:
    ventilator_df = pd.DataFrame()

latest_rpm = None
datapoint_col, rpm_col, refresh_col = st.columns([2, 2, 1], vertical_alignment="top")
with datapoint_col:
    utils.show_last_datapoint_caption(df)
    now_local = datetime.now(pytz.timezone('Europe/Brussels'))
    st.caption(f"Last refresh: {now_local.strftime('%d %b %H:%M:%S')}")
with rpm_col:
    if not ventilator_df.empty:
        latest_rpm = ventilator_df["rpm"].iloc[-1]
        latest_rpm_time = ventilator_df["received_at"].iloc[-1]
        st.caption(f"Last Fan RPM: {latest_rpm:.0f} at {utils.local_datetime_str(latest_rpm_time)}")
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
        utils.get_calibration_log.clear()
    except AttributeError:
        pass
    st.success("Data refreshed!")


# Create the dropdown (selectbox)
selected_label = utils.get_shared_time_range_selection("Select Time Range:", df=df)

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
show_dew_point = st.session_state.get("temp_show_dew_point", False)

current_temp = None
current_heat_index = None
heat_index_24h_ago_val = None
current_dew_point = None
dew_point_24h_ago_val = None
if not df.empty:
    # Sourced from the full unfiltered df, not time_window_df, so "Current"
    # is the true latest reading rather than the last (possibly resampled/
    # averaged-over-hours) row of whatever period is selected above.
    current_temp = df["sht_temperature_avg"].iloc[-1]
    current_humidity_now = df["sht_humidity_avg"].iloc[-1]
    current_heat_index = utils.compute_heat_index_series(current_temp, current_humidity_now)
    current_dew_point = utils.compute_dew_point_series(current_temp, current_humidity_now)
    if pd.notna(current_heat_index) and temp_24h_ago_val is not None and humidity_24h_ago_val is not None:
        heat_index_24h_ago_val = utils.compute_heat_index_series(temp_24h_ago_val, humidity_24h_ago_val)
    if pd.notna(current_dew_point) and temp_24h_ago_val is not None and humidity_24h_ago_val is not None:
        dew_point_24h_ago_val = utils.compute_dew_point_series(temp_24h_ago_val, humidity_24h_ago_val)

if not time_window_df.empty:
    time_window_df["heat_index_avg"] = utils.compute_heat_index_series(
        time_window_df["sht_temperature_avg"], time_window_df["sht_humidity_avg"]
    )
    time_window_df["dew_point_avg"] = utils.compute_dew_point_series(
        time_window_df["sht_temperature_avg"], time_window_df["sht_humidity_avg"]
    )


def _delta_caption(current_val, ago_val, label):
    if current_val is None or ago_val is None or pd.isna(current_val) or pd.isna(ago_val):
        return None
    delta = current_val - ago_val
    arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "▶")
    arrow_color = "#16A34A" if delta > 0 else ("#DC2626" if delta < 0 else "#6B7280")
    return f"{label} {delta:+.1f}°C <span style='color:{arrow_color}'>{arrow}</span>"


low_fan_rpm = latest_rpm is not None and pd.notna(latest_rpm) and latest_rpm < 1100

temp_chart = utils.TimeSeriesDashboardItem(
    metric_title="Current T",
    unit="°C",
    y_col_main="sht_temperature_avg",
    y_col_main_label="average",
    main_color="#DC2626" if low_fan_rpm else "#2563EB"
)
if low_fan_rpm:
    st.caption(f"⚠️ Fan RPM ({latest_rpm:.0f}) is onder de 1100 RPM-drempel.")
if show_temp_max:
    temp_chart.add_extra_series(col_name="sht_temperature_max", label="max", color="#16A34A")
if show_temp_min:
    temp_chart.add_extra_series(col_name="sht_temperature_min", label="min", color="#DC2626")
if show_heat_index:
    temp_chart.add_extra_series(col_name="heat_index_avg", label="heat index", color="#EA580C")
if show_dew_point:
    temp_chart.add_extra_series(col_name="dew_point_avg", label="dew point", color="#0891B2")

def _render_temp_toggles():
    temp_toggle_max, temp_toggle_min, temp_toggle_hi, temp_toggle_dp = st.columns(4)
    with temp_toggle_max:
        st.checkbox("Max", value=show_temp_max, key="temp_show_max")
    with temp_toggle_min:
        st.checkbox("Min", value=show_temp_min, key="temp_show_min")
    with temp_toggle_hi:
        st.checkbox("Heat Index", value=show_heat_index, key="temp_show_heat_index")
    with temp_toggle_dp:
        st.checkbox("Dew Point", value=show_dew_point, key="temp_show_dew_point")

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

    if current_dew_point is not None and pd.notna(current_dew_point):
        st.metric("Current Dew Point", f"{current_dew_point:.1f} °C")
        dp_delta_caption = _delta_caption(current_dew_point, dew_point_24h_ago_val, "24h ago")
        if dp_delta_caption:
            st.caption(dp_delta_caption, unsafe_allow_html=True)

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
       show_min_line=True, min_line_label="min",
       min_max_df=filtered_df, min_col='sht_humidity_avg', max_col='sht_humidity_avg',
       current_val=df["sht_humidity_avg"].iloc[-1] if not df.empty else None)

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

    pressure_filtered_df = filtered_df.copy()
    pressure_filtered_df["bmp_pressure_avg"] = pressure_filtered_df["bmp_pressure_avg"] / 100

    utils.TimeSeriesDashboardItem(
        metric_title="Current",
        unit="hPa",
        y_col_main="bmp_pressure_avg",
        main_color="#2563EB" # Blue
    ).plot(time_window_df, format=".1f", prediction_df=forecast_df, prediction_col='pressure', max_line_label="max",
           show_min_line=True, min_line_label="min",
           min_max_df=pressure_filtered_df, min_col='bmp_pressure_avg', max_col='bmp_pressure_avg',
           compare_val=pressure_24h_ago_val, compare_label="24h ago",
           current_val=df["bmp_pressure_avg"].iloc[-1] / 100 if not df.empty else None)

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
        latest_light_val = df[light_avg_col].iloc[-1] if not df.empty else time_window_df[light_avg_col].iloc[-1]
        st.metric("Current", f"{latest_light_val:.1f} W/m²")

        energy_kwh, energy_mj = utils.compute_todays_solar_energy(df, col=light_avg_col)
        st.caption(f"Energie vandaag: {energy_kwh:.2f} kWh/m² ")

    with col2:
        show_light_toa = st.checkbox("Show TOA", value=st.session_state.get("light_show_toa", True), key="light_show_toa")

        time_window_df = time_window_df.copy()
        time_window_df["toa_w_m2"] = utils.toa_irradiance_series(time_window_df["received_at"])
        toa_color = "#F97316"  # matches the forecast reference-line color used elsewhere

        value_vars = ["average", "max"] + (["TOA"] if show_light_toa else [])
        color_domain = ["average", "max"] + (["TOA"] if show_light_toa else [])
        color_range = [light_avg_color, light_max_color] + ([toa_color] if show_light_toa else [])

        light_melted = time_window_df[["received_at", light_avg_col, light_max_col, "toa_w_m2"]].rename(
            columns={light_avg_col: "average", light_max_col: "max", "toa_w_m2": "TOA"}
        ).melt(id_vars=["received_at"], value_vars=value_vars,
               var_name="Variable", value_name="Value")

        y_min = float(light_melted["Value"].min())
        y_max = float(light_melted["Value"].max())
        # Also widen the domain for the raw (unresampled) max, so it doesn't
        # get clamped off the visible chart (and its label along with it).
        if not filtered_df.empty and light_max_col in filtered_df:
            raw_max = filtered_df[light_max_col].max()
            if pd.notna(raw_max):
                y_max = max(y_max, float(raw_max))
        padding = (y_max - y_min) * 0.1 if y_max != y_min else 1
        y_domain = [y_min - padding, y_max + padding]

        color_scale = alt.Scale(domain=color_domain, range=color_range)

        base = alt.Chart(light_melted).encode(
            x=alt.X("received_at:T", title=None, axis=alt.Axis(labelExpr=utils.DATE_AT_MIDNIGHT_LABEL_EXPR)),
            y=alt.Y("Value:Q", title="W/m²", scale=alt.Scale(domain=y_domain, clamp=True)),
            color=alt.Color("Variable:N", scale=color_scale, title=None,
                             legend=alt.Legend(orient="bottom"))
        )

        max_area = base.transform_filter(alt.datum.Variable == "max").mark_area(opacity=0.4)
        avg_line = base.transform_filter(alt.datum.Variable == "average").mark_line(strokeWidth=1)
        toa_line = None
        if show_light_toa:
            toa_line = base.transform_filter(alt.datum.Variable == "TOA").mark_line(
                strokeWidth=2, strokeDash=[6, 3], opacity=0.8
            )

        nearest = alt.selection_point(on='mouseover', nearest=True, fields=["received_at"],
                                      encodings=['x'], empty=False)

        tooltip_list = [
            alt.Tooltip("received_at:T", title="Time", format='%d %b %H:%M'),
            alt.Tooltip(f"{light_avg_col}:Q", title="average", format='.2f'),
            alt.Tooltip(f"{light_max_col}:Q", title="max", format='.2f'),
        ]
        if show_light_toa:
            tooltip_list.append(alt.Tooltip("toa_w_m2:Q", title="TOA", format='.1f'))

        selectors = alt.Chart(time_window_df).mark_rule().encode(
            x="received_at:T",
            opacity=alt.value(0),
            tooltip=tooltip_list
        ).add_params(nearest)

        rules = alt.Chart(light_melted).mark_rule(color='#A1A6B4', strokeDash=[4, 4]).encode(
            x="received_at:T",
        ).transform_filter(nearest)

        points = base.mark_point(size=30).encode(
            opacity=alt.condition(nearest, alt.value(1), alt.value(0))
        )

        day_lines = utils.day_boundary_chart(utils.get_day_boundaries(time_window_df["received_at"]))

        # Full-width horizontal reference line through the max area's peak,
        # labeled with the max value just above it. Sourced from filtered_df
        # (raw, unresampled data) so it isn't smoothed down by resampling on
        # longer time windows.
        light_max_idx = filtered_df[light_max_col].idxmax() if not filtered_df.empty else None
        light_max_peak = filtered_df[light_max_col].max() if not filtered_df.empty else None
        light_max_line = None
        light_max_label = None
        if pd.notna(light_max_peak):
            light_max_line = alt.Chart(pd.DataFrame({'y': [light_max_peak]})).mark_rule(
                color='#EF4444', strokeDash=[4, 4], strokeWidth=1, opacity=0.6
            ).encode(y=alt.Y('y:Q', scale=alt.Scale(domain=y_domain, clamp=True)))

            light_max_time = filtered_df.loc[light_max_idx, "received_at"]
            light_max_label_df = pd.DataFrame({
                "received_at": [time_window_df["received_at"].min()],
                'y': [light_max_peak],
                'label': [f"max {light_max_peak:.1f} W/m² at {utils.local_datetime_str(light_max_time)}"],
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
            + [max_area, avg_line]
            + ([toa_line] if toa_line is not None else [])
            + [selectors, rules, points]
        )

        light_chart = alt.layer(*light_layers).properties(
            width='container', height=280
        ).add_params(
            alt.selection_interval(bind='scales', zoom=False)
        )

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
).plot(time_window_df, format=".0f", max_line_col="wind_speed_kmh_max",
       min_max_df=filtered_df, max_col="wind_speed_kmh_max",
       current_val=df["wind_speed_kmh_avg"].iloc[-1] if not df.empty else None)

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
    show_max_line=False,
    current_val=df["wind_direction"].iloc[-1] if not df.empty else None
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
rain_col1, rain_col2 = st.columns([1, 2])
with rain_col1:
    current_rain = df["rain_mm"].iloc[-1] if not df.empty else None
    if current_rain is not None and pd.notna(current_rain):
        st.metric("Current", f"{current_rain:.1f} mm")

with rain_col2:
    if time_window_df.empty:
        st.warning("No data for Rain")
    else:
        rain_bar_color = "#93C5FD"
        rain_cum_color = "#00CED1"

        rain_bars = alt.Chart(time_window_df).mark_bar(color=rain_bar_color).encode(
            x=alt.X("received_at:T", title=None, axis=alt.Axis(labelExpr=utils.DATE_AT_MIDNIGHT_LABEL_EXPR)),
            y=alt.Y("rain_mm:Q", title="rain (mm)", axis=alt.Axis(titleColor=rain_bar_color)),
        )

        rain_cum_line = alt.Chart(time_window_df).mark_line(strokeWidth=2, color=rain_cum_color).encode(
            x=alt.X("received_at:T", title=None),
            y=alt.Y("rain_mm_cumulated:Q", title="cumulated rain (mm)", axis=alt.Axis(titleColor=rain_cum_color)),
        )

        # Full-width horizontal reference line through the cumulated total's
        # peak, labeled with the max value - same style as the max lines on
        # the other charts. Layered together with rain_cum_line (rather than
        # as a separate top-level layer) so it shares its right-hand scale
        # instead of getting its own independent one.
        rain_cum_layers = [rain_cum_line]
        cum_max_idx = time_window_df["rain_mm_cumulated"].idxmax()
        cum_max_peak = time_window_df["rain_mm_cumulated"].max()
        if pd.notna(cum_max_peak):
            rain_cum_max_line = alt.Chart(pd.DataFrame({'y': [cum_max_peak]})).mark_rule(
                color='#EF4444', strokeDash=[4, 4], strokeWidth=1, opacity=0.6
            ).encode(y=alt.Y('y:Q'))

            cum_max_time = time_window_df.loc[cum_max_idx, "received_at"]
            rain_cum_max_label_df = pd.DataFrame({
                "received_at": [time_window_df["received_at"].min()],
                'y': [cum_max_peak],
                'label': [f"max {cum_max_peak:.1f} mm at {utils.local_datetime_str(cum_max_time)}"],
            })
            rain_cum_max_label = alt.Chart(rain_cum_max_label_df).mark_text(
                align='left', baseline='bottom', dy=-2, color='#EF4444', fontSize=11
            ).encode(x=alt.X("received_at:T"), y=alt.Y('y:Q'), text='label:N')

            rain_cum_layers += [rain_cum_max_line, rain_cum_max_label]

        # Snap-to-nearest-x hover with one combined tooltip for both series,
        # same pattern as the other charts - without this, hovering only
        # picks up whichever single mark happens to be under the cursor.
        nearest = alt.selection_point(on='mouseover', nearest=True, fields=['received_at'],
                                      encodings=['x'], empty=False)

        rain_selectors = alt.Chart(time_window_df).mark_rule().encode(
            x='received_at:T',
            opacity=alt.value(0),
            tooltip=[
                alt.Tooltip('received_at:T', title='Time', format='%d %b %H:%M'),
                alt.Tooltip('rain_mm:Q', title='rain (mm)', format='.1f'),
                alt.Tooltip('rain_mm_cumulated:Q', title='cumulated rain (mm)', format='.1f'),
            ]
        ).add_params(nearest)

        rain_hover_rule = alt.Chart(time_window_df).mark_rule(color='#A1A6B4', strokeDash=[4, 4]).encode(
            x='received_at:T',
        ).transform_filter(nearest)

        rain_cum_point = rain_cum_line.mark_point(size=30, color=rain_cum_color).encode(
            opacity=alt.condition(nearest, alt.value(1), alt.value(0))
        )
        rain_cum_layers.append(rain_cum_point)

        rain_chart = alt.layer(
            rain_bars, alt.layer(*rain_cum_layers), rain_hover_rule, rain_selectors
        ).resolve_scale(y='independent').properties(width='container', height=280)
        st.altair_chart(rain_chart, use_container_width=True)

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
    [data-testid="stCaptionContainer"] {
        margin-top: -0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
