import streamlit as st
import pandas as pd
import utils
import os

current_dir = os.path.dirname(__file__)
asset_path = os.path.join(current_dir, "..", "assets")
discharge_csv_path = os.path.join(asset_path, 'LiPo_smooth_discharge_curve.csv')
discharge_curve = pd.read_csv(discharge_csv_path)
df = utils.get_data(discharge_curve)

st.title("Today")

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

thermo_col, col1, col2, col3 = st.columns([1.2, 1, 1, 1])
with thermo_col:
    st.markdown(
        utils.render_thermometer(temp_stats['current'], min_val=-10, max_val=40, unit="°C", width=70, height=168),
        unsafe_allow_html=True
    )
with col1:
    st.metric("Current", f"{temp_stats['current']:.1f} °C")
with col2:
    st.metric("Min", f"{temp_stats['min_val']:.1f} °C")
    st.caption(f"at {local_time_str(temp_stats['min_time'])}")
with col3:
    st.metric("Max", f"{temp_stats['max_val']:.1f} °C")
    st.caption(f"at {local_time_str(temp_stats['max_time'])}")

# #--------------------- pressure -----------------------------
st.subheader("Pressure")
pressure_stats = stat_with_time(filtered_df, "bmp_pressure_avg")
for key in ("current", "min_val", "max_val"):
    pressure_stats[key] = pressure_stats[key] / 100  # Pa -> hPa

gauge_col, p_col1, p_col2, p_col3 = st.columns([1.2, 1, 1, 1])
with gauge_col:
    st.markdown(
        utils.render_analog_gauge(pressure_stats['current'], min_val=973, max_val=1053, unit="hPa", width=224, height=168),
        unsafe_allow_html=True
    )
with p_col1:
    st.metric("Current", f"{pressure_stats['current']:.1f} hPa")
with p_col2:
    st.metric("Min", f"{pressure_stats['min_val']:.1f} hPa")
    st.caption(f"at {local_time_str(pressure_stats['min_time'])}")
with p_col3:
    st.metric("Max", f"{pressure_stats['max_val']:.1f} hPa")
    st.caption(f"at {local_time_str(pressure_stats['max_time'])}")

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
