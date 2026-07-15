import streamlit as st
import pandas as pd
import utils
import os

current_dir = os.path.dirname(__file__)
asset_path = os.path.join(current_dir, "..", "assets")
discharge_csv_path = os.path.join(asset_path, 'LiPo_smooth_discharge_curve.csv')
discharge_curve = pd.read_csv(discharge_csv_path)
df = utils.get_data(discharge_curve)

st.title("Dashboard")

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

# #--------------------- sunset and sunrise -----------------------------
sunrise_str, sunset_str = utils.get_sunrise_sunset()
icon_width = 6
text_width = 15
buffer_width = 20

col1, col2, col3, col4, col5, col6, col7, col8, buffer = st.columns([icon_width, text_width,
                                                         icon_width, text_width,
                                                         icon_width, text_width,
                                                        icon_width, text_width,
                                                         buffer_width])

with col1:
    img_path = os.path.join(current_dir, "..", "assets", "sunrise.png")
    st.image(img_path, width=50)
with col2:
    st.markdown(f"**Sunrise**<br>{sunrise_str}", unsafe_allow_html=True)

with col3:
    img_path = os.path.join(current_dir, "..", "assets", "sunset.png")
    st.image(img_path, width=50)
with col4:
    st.markdown(f"**Sunset**<br>{sunset_str}", unsafe_allow_html=True)

# --- Moon Phase ---
with col5:
    moonphase_image_filepath, index = utils.get_moonphase_filepath(image_repo=asset_path)
    st.image(moonphase_image_filepath, width=50)
with col6:
    st.markdown(f"**Moon**<br> {index}/8", unsafe_allow_html=True)

# --- Solar Noon ---
with col7:
    img_path = os.path.join(asset_path, 'solar_noon.png')
    solar_noon_str = utils.get_solar_noon()
    st.image(img_path, width=50)
with col8:
    st.markdown(f"**Solar noon**<br> {solar_noon_str}", unsafe_allow_html=True)

with buffer:
    pass

filtered_df = utils.filter_by_recency(df, window_label="Since Midnight", mode='last_session')

if filtered_df.empty:
    st.warning("No data since midnight.")
    st.stop()


def stat_with_time(frame, col):
    min_idx = frame[col].idxmin()
    max_idx = frame[col].idxmax()
    return {
        "current": frame[col].iloc[-1],
        "min_val": frame.loc[min_idx, col],
        "min_time": frame.loc[min_idx, "received_at"],
        "max_val": frame.loc[max_idx, col],
        "max_time": frame.loc[max_idx, "received_at"],
    }


def local_time_str(ts):
    ts = pd.Timestamp(ts)
    if ts.tzinfo is None:
        ts = ts.tz_localize('UTC')
    return ts.tz_convert('Europe/Brussels').strftime('%H:%M')


# #--------------------- temperature -----------------------------
st.subheader("Temperature")
temp_stats = stat_with_time(filtered_df, "sht_temperature_avg")
temp_24h_ago_val, _ = utils.value_at_offset(df, "sht_temperature_avg", 24 * 3600)

thermo_col, col2, col3, col4 = st.columns([2.7, 1, 1, 1])
with thermo_col:
    st.markdown(
        utils.render_analog_gauge(
            temp_stats['current'], min_val=-10, max_val=40, unit="°C",
            step=10, label_every=1,
            gradient_colors=("#2563EB", "#DC2626"),
            width=300, height=225
        ),
        unsafe_allow_html=True
    )
with col2:
    st.metric("Min", f"{temp_stats['min_val']:.1f} °C")
    st.caption(f"at {local_time_str(temp_stats['min_time'])}")
with col3:
    st.metric("Max", f"{temp_stats['max_val']:.1f} °C")
    st.caption(f"at {local_time_str(temp_stats['max_time'])}")
with col4:
    if temp_24h_ago_val is not None:
        delta = temp_stats['current'] - temp_24h_ago_val
        st.metric("24h ago", f"{delta:+.1f} °C")
    else:
        st.metric("24h ago", "N/A")

# #--------------------- sun -----------------------------
st.subheader("Sun")
sun_stats = stat_with_time(filtered_df, "light_intensity_max")
sun_energy_kwh, sun_energy_mj = utils.compute_todays_solar_energy(df, col="light_intensity_avg")

sun_gauge_col, sun_col2, sun_col3 = st.columns([1.8, 1, 1])
with sun_gauge_col:
    st.markdown(
        utils.render_analog_gauge(
            sun_stats['current'], min_val=0, max_val=1000, unit="W/m²",
            step=100, label_every=2,
            track_color="#FEF3C7", fill_color="#F59E0B",
            width=300, height=225
        ),
        unsafe_allow_html=True
    )
with sun_col2:
    st.metric("Max", f"{sun_stats['max_val']:.0f} W/m²")
    st.caption(f"at {local_time_str(sun_stats['max_time'])}")
with sun_col3:
    st.metric("Energie vandaag", f"{sun_energy_kwh:.2f} kWh/m²")
    st.caption(f"{sun_energy_mj:.1f} MJ/m²")

# #--------------------- pressure -----------------------------
st.subheader("Pressure")
pressure_stats = stat_with_time(filtered_df, "bmp_pressure_avg")
for key in ("current", "min_val", "max_val"):
    pressure_stats[key] = pressure_stats[key] / 100  # Pa -> hPa

gauge_col, p_col2, p_col3 = st.columns([1.8, 1, 1])
with gauge_col:
    st.markdown(
        utils.render_analog_gauge(pressure_stats['current'], min_val=973, max_val=1053, unit="hPa", width=300, height=225),
        unsafe_allow_html=True
    )
with p_col2:
    st.metric("Min", f"{pressure_stats['min_val']:.1f} hPa")
    st.caption(f"at {local_time_str(pressure_stats['min_time'])}")
with p_col3:
    st.metric("Max", f"{pressure_stats['max_val']:.1f} hPa")
    st.caption(f"at {local_time_str(pressure_stats['max_time'])}")

# #--------------------- rain -----------------------------
st.subheader("Rain")


def rain_total(frame, window_label):
    windowed = utils.filter_by_recency(frame, window_label=window_label, mode='last_session')
    if windowed.empty:
        return 0.0
    return windowed["rain_mm"].fillna(0).sum()


rain_col1, rain_col2, rain_col3, rain_col4 = st.columns(4)
with rain_col1:
    st.metric("Today", f"{rain_total(df, 'Since Midnight'):.1f} mm")
with rain_col2:
    st.metric("Last 24h", f"{rain_total(df, 'Last 24 Hours'):.1f} mm")
with rain_col3:
    st.metric("This month", f"{rain_total(df, 'This Month'):.1f} mm")
with rain_col4:
    st.metric("This year", f"{rain_total(df, 'This Year'):.1f} mm")

# #--------------------- wind -----------------------------
def render_wind_rose_section(title, speed_col):
    st.subheader(title)
    rose_df = utils.build_wind_rose_data(filtered_df, direction_col='wind_direction', speed_col=speed_col)
    rose_chart = utils.render_wind_rose_chart(rose_df)

    if rose_chart is None:
        st.warning("No wind data since midnight.")
        return

    rose_col, spacer_col, legend_col, buffer_col = st.columns([1.1, 1, 1, 1])
    with rose_col:
        st.altair_chart(rose_chart, use_container_width=False)
    with legend_col:
        st.markdown(utils.render_wind_rose_legend_html(), unsafe_allow_html=True)


render_wind_rose_section("Wind average", "wind_speed_kmh_avg")
render_wind_rose_section("Wind gusts", "wind_speed_kmh_max")

st.markdown(
    """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
