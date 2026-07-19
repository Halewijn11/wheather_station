import pandas as pd
import streamlit as st
import altair as alt
from astral import LocationInfo
from astral.sun import sun
from datetime import date, timedelta
import numpy as np
# from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import os
import pytz
import calendar
import uuid
from pandas.tseries.frequencies import to_offset

CUSTOM_RANGE_LABEL = "Custom Range"
TIME_OPTIONS = [
    "Last Hour",
    "Last 24 Hours",
    "Last 7 Days",
    "Since Midnight",
    "This Week",
    "This Month",
    CUSTOM_RANGE_LABEL,
]
DEFAULT_TIME_RANGE = "Since Midnight"
TIME_RANGE_STATE_KEY = "selected_time_range"

# Views short enough that the axis date is just clutter (single day, or a
# rolling 24h window rarely worth calling out a day change for).
NO_DATE_AXIS_LABELS = {"Since Midnight", "Last 24 Hours"}


def axis_date_format(window_label):
    return '%H:%M' if window_label in NO_DATE_AXIS_LABELS else '%d %b %H:%M'

# Shared (cross-page) storage for the custom range picker: Europe/Brussels-local,
# tz-aware datetimes. CUSTOM_RANGE_VALID_KEY records whether From < To.
CUSTOM_RANGE_FROM_KEY = "custom_range_from_dt"
CUSTOM_RANGE_TO_KEY = "custom_range_to_dt"
CUSTOM_RANGE_VALID_KEY = "custom_range_valid"


def get_shared_time_range_selection(label="Select Time Range:"):
    # Persist one stable value in session state and rehydrate the widget from it.
    # This avoids page-switch widget cleanup resetting the selected option.
    if TIME_RANGE_STATE_KEY not in st.session_state or st.session_state[TIME_RANGE_STATE_KEY] not in TIME_OPTIONS:
        st.session_state[TIME_RANGE_STATE_KEY] = DEFAULT_TIME_RANGE

    selected = st.selectbox(
        label,
        options=TIME_OPTIONS,
        index=TIME_OPTIONS.index(st.session_state[TIME_RANGE_STATE_KEY]),
    )

    st.session_state[TIME_RANGE_STATE_KEY] = selected

    if selected == CUSTOM_RANGE_LABEL:
        _render_custom_range_pickers()

    return selected


def _render_custom_range_pickers():
    """Renders the From/To date+time pickers for Custom Range and stores the
    resulting Europe/Brussels-local datetimes in session state, shared across
    pages the same way the selected label itself is shared."""
    tz = pytz.timezone('Europe/Brussels')
    now_local = datetime.now(tz)
    today_local = now_local.date()

    if CUSTOM_RANGE_FROM_KEY not in st.session_state:
        st.session_state[CUSTOM_RANGE_FROM_KEY] = now_local - timedelta(hours=24)
    if CUSTOM_RANGE_TO_KEY not in st.session_state:
        st.session_state[CUSTOM_RANGE_TO_KEY] = now_local

    default_from = st.session_state[CUSTOM_RANGE_FROM_KEY]
    default_to = st.session_state[CUSTOM_RANGE_TO_KEY]

    from_col, to_col = st.columns(2)
    with from_col:
        from_date = st.date_input("From date", value=default_from.date(), max_value=today_local)
        from_time = st.time_input("From time", value=default_from.time())
    with to_col:
        to_date = st.date_input("To date", value=default_to.date(), max_value=today_local)
        to_time = st.time_input("To time", value=default_to.time())

    from_dt_local = tz.localize(datetime.combine(from_date, from_time))
    to_dt_local = tz.localize(datetime.combine(to_date, to_time))

    st.session_state[CUSTOM_RANGE_FROM_KEY] = from_dt_local
    st.session_state[CUSTOM_RANGE_TO_KEY] = to_dt_local

    if from_dt_local >= to_dt_local:
        st.session_state[CUSTOM_RANGE_VALID_KEY] = False
        st.warning("'From' must be before 'To'.")
        st.stop()

    st.session_state[CUSTOM_RANGE_VALID_KEY] = True

def get_google_sheet_df(sheet_id = "1yW0NiWeuWjEp08eymjFQ62CqKhSegNa_FXcgl68Kf4Q", sheet_gid=None, base_url="https://docs.google.com/spreadsheets/d/"):
    # Construct the base export URL
    url = f"{base_url}{sheet_id}/export?format=csv"
    
    # Append the specific gid if provided
    if sheet_gid:
        url += f"&gid={sheet_gid}"
    print(url)
    df = pd.read_csv(url)
    return df

def get_full_payload_colname(col_name):
    return f"uplink_message_decoded_payload_{col_name}"

# def get_metadata_google_sheet_col_name(col_name):
#     return f"uplink_message_decoded_payload{col_name}"
def filter_by_recency(df, window_label=None, hours=0, minutes=0, seconds=0, 
                      time_colname = 'seconds_since_now', 
                      colname_unit = 'seconds', mode = 'live'):
    """
    Filters the dataframe to only include rows from 'now' back to a specific duration.
    Also supports semantic window labels (Since Midnight, This Week, This Month, This Year).
    """
    if df.empty:
        return df

    tz = pytz.timezone('Europe/Brussels')
    now = datetime.now(tz)

    # 0. Custom Range: filter directly on absolute received_at bounds,
    # bypassing the seconds_since_now / mode logic entirely.
    if window_label == CUSTOM_RANGE_LABEL:
        if not st.session_state.get(CUSTOM_RANGE_VALID_KEY, False):
            return df.iloc[0:0]
        start_utc = pd.Timestamp(st.session_state[CUSTOM_RANGE_FROM_KEY]).tz_convert('UTC')
        end_utc = pd.Timestamp(st.session_state[CUSTOM_RANGE_TO_KEY]).tz_convert('UTC')
        mask = (df['received_at'] >= start_utc) & (df['received_at'] <= end_utc)
        return df.loc[mask].copy()

    # 1. Handle semantic window labels
    if window_label:
        if window_label == "Last Hour":
            total_window_seconds = 3600
        elif window_label == "Last 24 Hours":
            total_window_seconds = 24 * 3600
        elif window_label == "Last 7 Days":
            total_window_seconds = 7 * 24 * 3600
        elif window_label == "Since Midnight":
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            total_window_seconds = (now - midnight).total_seconds()
        elif window_label == "This Week":
            # Monday is 0, Sunday is 6
            days_since_monday = now.weekday()
            monday_midnight = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            total_window_seconds = (now - monday_midnight).total_seconds()
        elif window_label == "This Month":
            first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            total_window_seconds = (now - first_of_month).total_seconds()
        elif window_label == "This Year":
            first_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            total_window_seconds = (now - first_of_year).total_seconds()
        else:
            total_window_seconds = (hours * 3600) + (minutes * 60) + seconds
    else:
        # Default to provided hours/mins/secs
        total_window_seconds = (hours * 3600) + (minutes * 60) + seconds
    
    # 2. Filter the dataframe
    if mode == 'live':
        mask = df[time_colname] <= total_window_seconds
        filtered_df = df.loc[mask].copy()
        return filtered_df
    elif mode == 'last_session': 
        latest_recorded_second = df['seconds_since_now'].min()
        limit = latest_recorded_second + total_window_seconds
        mask = df[time_colname] <= limit
        filtered_df = df.loc[mask].copy()
        return filtered_df
    
    return df


def value_at_offset(frame, col, seconds_ago, time_colname='seconds_since_now'):
    """Finds the row whose recency is closest to `seconds_ago` and returns (value, received_at)."""
    valid = frame.dropna(subset=[col, time_colname])
    if valid.empty:
        return None, None
    idx = (valid[time_colname] - seconds_ago).abs().idxmin()
    return valid.loc[idx, col], valid.loc[idx, "received_at"]


def compute_todays_solar_energy(df, col='light_intensity_avg', interval_minutes=5):
    """
    Rough estimate of today's solar irradiation energy per m², integrating the
    light sensor's average W/m² reading over its own nominal reporting interval.
    Each record only contributes for its own interval, so a reporting gap
    (LoRaWAN dropout, etc.) contributes nothing rather than assuming full power
    through the gap. Not a calibrated pyranometer reading - light_intensity is
    an empirically-scaled light sensor, so this is an estimate.
    Resets at local midnight. Returns (kwh_per_m2, mj_per_m2).
    """
    if df.empty or col not in df.columns:
        return 0.0, 0.0

    tz = pytz.timezone('Europe/Brussels')
    midnight_local = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    midnight_utc = midnight_local.astimezone(pytz.UTC)

    today = df[(df['received_at'] >= midnight_utc) & df[col].notna()]
    if today.empty:
        return 0.0, 0.0

    wh_per_m2 = (today[col] * (interval_minutes / 60)).sum()
    kwh_per_m2 = wh_per_m2 / 1000
    mj_per_m2 = wh_per_m2 * 3600 / 1_000_000
    return kwh_per_m2, mj_per_m2


def compute_daily_solar_energy(df, year, month, col='light_intensity_avg', interval_minutes=5):
    """
    Same estimate as compute_todays_solar_energy, broken down per calendar day
    (Europe/Brussels local) for the given year/month. Returns a DataFrame with
    one row per day of the month: date, day, kwh_per_m2, mj_per_m2, has_data
    (False if the sensor reported nothing that day), is_partial (True for
    today, if it falls within the requested month).
    """
    tz = pytz.timezone('Europe/Brussels')
    days_in_month = calendar.monthrange(year, month)[1]
    today_local_date = datetime.now(tz).date()
    month_start = pd.Timestamp(year, month, 1).date()
    month_end = pd.Timestamp(year, month, days_in_month).date()

    if not df.empty and col in df.columns:
        work = df.dropna(subset=['received_at', col]).copy()
        work['local_date'] = work['received_at'].dt.tz_convert(tz).dt.date
        work = work[(work['local_date'] >= month_start) & (work['local_date'] <= month_end)]
        wh_by_day = (work[col] * (interval_minutes / 60)).groupby(work['local_date']).sum()
    else:
        wh_by_day = pd.Series(dtype=float)

    rows = []
    for day in range(1, days_in_month + 1):
        date = pd.Timestamp(year, month, day).date()
        has_data = date in wh_by_day.index
        wh_per_m2 = float(wh_by_day.loc[date]) if has_data else 0.0
        rows.append({
            'date': date,
            'day': day,
            'kwh_per_m2': wh_per_m2 / 1000,
            'mj_per_m2': wh_per_m2 * 3600 / 1_000_000,
            'has_data': has_data,
            'is_partial': date == today_local_date,
        })
    return pd.DataFrame(rows)


def compute_daily_rain(df, year, month, col='rain_mm'):
    """
    Total rainfall (mm) per calendar day (Europe/Brussels local) for the given
    live-sensor year/month. rain_mm is already a per-record amount, so daily
    total is a plain sum (no time-weighting, unlike the solar energy estimate).
    Returns a DataFrame with one row per day: date, day, rain_mm, has_data
    (False if the sensor reported nothing that day), is_partial (True for
    today, if it falls within the requested month).
    """
    tz = pytz.timezone('Europe/Brussels')
    days_in_month = calendar.monthrange(year, month)[1]
    today_local_date = datetime.now(tz).date()
    month_start = pd.Timestamp(year, month, 1).date()
    month_end = pd.Timestamp(year, month, days_in_month).date()

    if not df.empty and col in df.columns:
        work = df.dropna(subset=['received_at', col]).copy()
        work['local_date'] = work['received_at'].dt.tz_convert(tz).dt.date
        work = work[(work['local_date'] >= month_start) & (work['local_date'] <= month_end)]
        mm_by_day = work.groupby('local_date')[col].sum()
    else:
        mm_by_day = pd.Series(dtype=float)

    rows = []
    for day in range(1, days_in_month + 1):
        date = pd.Timestamp(year, month, day).date()
        has_data = date in mm_by_day.index
        rows.append({
            'date': date,
            'day': day,
            'rain_mm': float(mm_by_day.loc[date]) if has_data else 0.0,
            'has_data': has_data,
            'is_partial': date == today_local_date,
        })
    return pd.DataFrame(rows)


def filter_data(df, window_hours=1, mode='live'):
    if df.empty:
        return df
        
    if mode == 'live':
        # Your original logic: filter by actual recency
        total_seconds = window_hours * 3600
        return df[df['seconds_since_now'] <= total_seconds].copy()
        
    elif mode == 'last_session':
        # Show the most recent 'window' of data available, 
        # regardless of how long ago it happened.
        latest_recorded_second = df['seconds_since_now'].min() # assuming 0 is 'now'
        limit = latest_recorded_second + (window_hours * 3600)
        return df[df['seconds_since_now'] <= limit].copy()

def tidy_google_sheet_df(google_sheet_df, discharge_curve, num_batteries=1, voltage_col='voltage_bat'):
    df = google_sheet_df.copy()
    #formatting
    df['received_at'] =pd.to_datetime(df['received_at'], utc=True).dt.floor('s').dt.floor('s')

    #enriching the data
    df['received_at_td_seconds'] = df['received_at'].diff().dt.total_seconds() #td stands for time difference
    df['received_at_td_minutes'] = df['received_at_td_seconds']/60
    now = pd.Timestamp.now(tz='UTC')
    df['seconds_since_now'] = (now - df['received_at']).dt.total_seconds()
    df['battery_percentage'] = df.apply(
    lambda row: calculate_stage_of_charge(discharge_curve, num_batteries, row[voltage_col])
    if pd.notnull(row[voltage_col]) else np.nan,
    axis=1
    )

    # Sensor noise shows up as tiny non-zero readings at night; treat anything below 1 as 0.
    for col in ('light_intensity_avg', 'light_intensity_max', 'light_intensity_min'):
        if col in df.columns:
            df.loc[df[col] < 1, col] = 0

    return df

@st.cache_data(ttl = 3*60)
def show_last_datapoint_caption(df):
    """Renders 'Last datapoint on: ...' (Europe/Brussels local time) as a caption."""
    last_datapoint = df['received_at'].max()
    if pd.notna(last_datapoint):
        ts = pd.Timestamp(last_datapoint)
        if ts.tzinfo is None:
            ts = ts.tz_localize('UTC')
        local = ts.tz_convert('Europe/Brussels')
        st.caption(f"Last datapoint on: {local.strftime('%a')} {local.day} {local.strftime('%b')} {local.strftime('%H:%M')}")
    else:
        st.caption("Last datapoint on: N/A")


def get_data(discharge_curve, num_batteries=1, voltage_col='voltage_bat'):
    export_url = "https://docs.google.com/spreadsheets/d/1yW0NiWeuWjEp08eymjFQ62CqKhSegNa_FXcgl68Kf4Q/export?format=csv&gid=0"
    google_sheet_df = pd.read_csv(export_url)
    df = tidy_google_sheet_df(google_sheet_df, discharge_curve, num_batteries=num_batteries, voltage_col=voltage_col)
    return df

@st.cache_data(ttl=5*60)
def get_forecast_df():
    sheet_id = "1ZMczLO4qHjzeHy8-fJdS5QZ2bOlziQlb_0pUwslPZl0"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    df = pd.read_csv(url)
    df['fetched_at'] = pd.to_datetime(df['fetched_at'], utc=True)
    df['forecast_for'] = pd.to_datetime(df['forecast_for'], utc=True)
    # Keep only the rows from the latest fetch batch
    latest_fetch = df['fetched_at'].max()
    df = df[df['fetched_at'] == latest_fetch].copy()
    # Rename to match the x-axis convention used throughout the dashboard
    df = df.rename(columns={'forecast_for': 'received_at'})
    df = df.sort_values('received_at').reset_index(drop=True)
    return df

def resample_data(df, sum_cols=None, cumulative_cols=None):
    # Ensure the index is datetime for resampling
    df = df.copy()
    df.set_index('received_at', inplace=True)

    # Resolution decision is based purely on the actual span of the data
    # passed in, not on which window label produced it.
    span = df.index.max() - df.index.min() if not df.empty else pd.Timedelta(0)

    # Raw data below 48h: the sensor already reports on a ~5min cadence, so
    # resampling a short window adds cost without adding legibility.
    if span <= pd.Timedelta(hours=48):
        if cumulative_cols:
            for col in cumulative_cols:
                if col in df.columns:
                    target_colname = f"{col}_cumulated"
                    df[target_colname] = df[col].fillna(0).groupby(df.index.tz_convert('Europe/Brussels').date).cumsum()
        return df.reset_index()

    # Define resolution based on the data span, coarsening as the range grows.
    if span <= pd.Timedelta(days=7):
        resample_rate = '30min'
    elif span <= pd.Timedelta(days=30):
        resample_rate = '1h'
    else:
        resample_rate = '3h'

    # Validate frequency to catch invalid aliases early.
    to_offset(resample_rate)
    
    # Resample numeric columns only, then reset index to keep 'received_at'
    # Default to mean for most variables (temp, humidity, etc.)
    # label='right' labels the bucket with the end of the interval, 
    # which reduces the "offset" perceived in the graphs
    resampled_df = df.select_dtypes(include=['number']).resample(resample_rate).mean()
    
    # Drop empty buckets (NaN rows) to remove "holes" in the line charts
    resampled_df = resampled_df.dropna(how='all')
    
    # Override specific columns with sum if they exist
    if sum_cols:
        for col in sum_cols:
            if col in df.columns:
                resampled_df[col] = df[col].resample(resample_rate).sum()

    # Calculate cumulative values for specific columns
    if cumulative_cols:
        for col in cumulative_cols:
            if col in resampled_df.columns:
                target_colname = f"{col}_cumulated"
                # Group by date so the cumsum resets to 0 at midnight each day
                resampled_df[target_colname] = resampled_df[col].fillna(0).groupby(resampled_df.index.tz_convert('Europe/Brussels').date).cumsum()

    # Averaging already-clamped raw readings can produce small non-zero values
    # again (e.g. a 5min bucket mixing 0s with values just above 1); reapply the clamp.
    for col in ('light_intensity_avg', 'light_intensity_max', 'light_intensity_min'):
        if col in resampled_df.columns:
            resampled_df.loc[resampled_df[col] < 1, col] = 0

    return resampled_df.reset_index()



def format_timedelta(td):
    if pd.isnull(td):
        return ""

    total_seconds = int(td.total_seconds())

    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)

    parts = []
    if days > 0:
        parts.append(f"{days} day" + ("s" if days != 1 else ""))
    if hours > 0:
        parts.append(f"{hours} hour" + ("s" if hours != 1 else ""))
    if minutes > 0:
        parts.append(f"{minutes} minute" + ("s" if minutes != 1 else ""))
    if seconds > 0 and total_seconds < 60:  # only show seconds if < 1 minute
        parts.append(f"{seconds} second" + ("s" if seconds != 1 else ""))

    # join only the non-zero parts, smallest representation possible
    return ", ".join(parts)

def get_last_measurement_string(df):
    last_time = df['received_at'].max()
    now = pd.Timestamp.now(tz='UTC')
    now - last_time
    return format_timedelta(now - last_time)

# Function to load CSS from the 'assets' folder
def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)



def draw_histogram(df, metric_name):
    # Ensure we don't have nulls for the main metric
    clean_df = df.dropna(subset=[metric_name])

    st.altair_chart(
        alt.Chart(clean_df, height=200, width=200)
        .mark_bar(binSpacing=0)
        .encode(
            alt.X(
                metric_name,
                type="quantitative",
            ).bin(maxbins=20),
            alt.Y("count()").axis(None),
        )
    )


import base64
import struct

def decode_heltec_payload(b64_string):
    # Decode Base64 to bytes
    data = base64.b64decode(b64_string)
    
    # Check if we have the expected 12 bytes
    if len(data) != 12:
        return f"Error: Expected 12 bytes, got {len(data)}"

    # '>HHHHHH' means: Big Endian, 6 Unsigned Shorts (2 bytes each)
    # Based on your Arduino: Hum(Avg, Min, Max), Temp(Avg, Min, Max)
    vals = struct.unpack('>HHHHHH', data)
    
    return {
        "humidity_avg": vals[0] / 100.0,
        "humidity_min": vals[1] / 100.0,
        "humidity_max": vals[2] / 100.0,
        "temp_avg":     vals[3] / 100.0,
        "temp_min":     vals[4] / 100.0,
        "temp_max":     vals[5] / 100.0
    }

def get_sunrise_sunset(latitude=50.924503, longitude=4.112950):
    city = LocationInfo(
        name="Affligem",
        region="Belgium",
        timezone="Europe/Brussels",
        latitude=latitude,
        longitude=longitude
    )

    s = sun(city.observer, date=date.today(), tzinfo=city.timezone)

    sunrise_str = s["sunrise"].strftime("%H:%M")
    sunset_str = s["sunset"].strftime("%H:%M")

    return sunrise_str, sunset_str

def get_solar_noon(latitude=50.924503, longitude=4.112950):
    """
    Calculates the exact time of solar noon for the current date.
    """
    city = LocationInfo(
        name="Affligem",
        region="Belgium",
        timezone="Europe/Brussels",
        latitude=latitude,
        longitude=longitude
    )

    # Calculate sun events for today
    s = sun(city.observer, date=date.today(), tzinfo=city.timezone)

    # Extract noon and format it
    # s["noon"] returns a datetime object
    solar_noon_str = s["noon"].strftime("%H:%M")
    
    return solar_noon_str


# --- TOA (top-of-atmosphere) solar irradiance -------------------------------
# Spencer (1971) approximations for solar declination and the earth-sun
# distance (eccentricity) correction. This is the theoretical clear-sky
# irradiance with no atmosphere - a reference to compare the actual sensor
# reading against, not a replacement for it.
TOA_SOLAR_CONSTANT = 1361.0  # W/m^2


def _toa_dag_van_jaar(datum):
    return datum.timetuple().tm_yday


def _toa_excentriciteitscorrectie(n):
    gamma = 2 * math.pi * (n - 1) / 365
    return (1.000110
            + 0.034221 * math.cos(gamma)
            + 0.001280 * math.sin(gamma)
            + 0.000719 * math.cos(2 * gamma)
            + 0.000077 * math.sin(2 * gamma))


def _toa_zonsdeclinatie(n):
    gamma = 2 * math.pi * (n - 1) / 365
    return (0.006918
            - 0.399912 * math.cos(gamma)
            + 0.070257 * math.sin(gamma)
            - 0.006758 * math.cos(2 * gamma)
            + 0.000907 * math.sin(2 * gamma)
            - 0.002697 * math.cos(3 * gamma)
            + 0.001480 * math.sin(3 * gamma))


def _toa_tijdsvergelijking(n):
    B = math.radians(360.0 / 364.0 * (n - 81))
    return 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)


def _toa_uurhoek(uur_utc, lengtegraad, n):
    EoT = _toa_tijdsvergelijking(n)
    zonnetijd = uur_utc + lengtegraad * 4.0 / 60.0 + EoT / 60.0
    return 15.0 * (zonnetijd - 12.0)


def toa_irradiance(datum_utc, latitude, longitude):
    """
    Instantaneous top-of-atmosphere solar irradiance (W/m^2) for a UTC
    datetime and location. Clear-sky, no-atmosphere theoretical maximum -
    not what the light sensor actually measures.
    """
    n = _toa_dag_van_jaar(datum_utc)
    uur_utc = datum_utc.hour + datum_utc.minute / 60.0 + datum_utc.second / 3600.0

    E0 = _toa_excentriciteitscorrectie(n)
    delta = _toa_zonsdeclinatie(n)
    h = _toa_uurhoek(uur_utc, longitude, n)

    phi = math.radians(latitude)
    h_rad = math.radians(h)
    cos_tz = math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.cos(h_rad)
    cos_tz = max(cos_tz, 0.0)

    return TOA_SOLAR_CONSTANT * E0 * cos_tz


def toa_daily_total_wh_per_m2(datum_utc, latitude):
    """
    Closed-form total TOA irradiation (Wh/m^2) for the full day (sunrise to
    sunset) of datum_utc's date, at the given latitude (longitude-independent).
    """
    n = _toa_dag_van_jaar(datum_utc)
    E0 = _toa_excentriciteitscorrectie(n)
    delta = _toa_zonsdeclinatie(n)
    phi = math.radians(latitude)

    tan_product = max(min(math.tan(phi) * math.tan(delta), 1), -1)
    hs = math.acos(-tan_product)

    H0 = (86400 / math.pi) * TOA_SOLAR_CONSTANT * E0 * (
        math.cos(phi) * math.cos(delta) * math.sin(hs) + hs * math.sin(phi) * math.sin(delta)
    )
    return H0 / 3600.0  # J/m^2 per day -> Wh/m^2


def toa_energy_wh_per_m2(start_utc, end_utc, latitude, longitude, step_minutes=5):
    """
    Numerically integrates toa_irradiance() from start_utc to end_utc (both
    tz-aware UTC datetimes) into a total energy per m^2 (Wh), using the same
    rectangle-rule approach as compute_todays_solar_energy.
    """
    if end_utc <= start_utc:
        return 0.0
    total_wh = 0.0
    t = start_utc
    step = timedelta(minutes=step_minutes)
    while t < end_utc:
        total_wh += toa_irradiance(t, latitude, longitude) * (step_minutes / 60)
        t += step
    return total_wh


def get_toa_solar_stats(latitude=50.924503, longitude=4.112950):
    """
    Returns today's TOA solar stats for the given location:
      - toa_now_w_m2: instantaneous TOA irradiance right now
      - toa_daily_total_wh_m2: full-day (sunrise-sunset) TOA total
      - toa_so_far_wh_m2: TOA total integrated from sunrise to now (0 before sunrise)
    """
    tz = pytz.timezone('Europe/Brussels')
    now_local = datetime.now(tz)
    now_utc = now_local.astimezone(pytz.UTC)

    city = LocationInfo(name="Affligem", region="Belgium", timezone="Europe/Brussels",
                         latitude=latitude, longitude=longitude)
    s = sun(city.observer, date=now_local.date(), tzinfo=city.timezone)
    sunrise_utc = s["sunrise"].astimezone(pytz.UTC)

    return {
        'toa_now_w_m2': toa_irradiance(now_utc, latitude, longitude),
        'toa_daily_total_wh_m2': toa_daily_total_wh_per_m2(now_utc, latitude),
        'toa_so_far_wh_m2': toa_energy_wh_per_m2(sunrise_utc, now_utc, latitude, longitude) if now_utc > sunrise_utc else 0.0,
    }


def toa_irradiance_series(timestamps_utc, latitude=50.924503, longitude=4.112950):
    """
    Vectorized convenience wrapper: computes toa_irradiance() for each
    timestamp in a tz-aware (UTC) pandas Series, returning a Series aligned
    to the same index - a smooth theoretical reference curve to compare
    against the actual (cloud/atmosphere-attenuated) sensor reading.
    """
    return timestamps_utc.apply(lambda t: toa_irradiance(t.to_pydatetime(), latitude, longitude))


def calculate_stage_of_charge(discharge_curve, num_batteries, readout_voltage):
    # 1. Calculate voltage per individual cell
    voltage_per_cell = readout_voltage / num_batteries
    
    # 2. Extract columns for readability
    # Ensure they are sorted by voltage for the interpolation to work
    df_sorted = discharge_curve.sort_values('voltage')
    voltages = df_sorted['voltage'].values
    soc_values = df_sorted['stage_of_charge'].values
    
    # 3. Perform linear interpolation
    # np.interp(x_to_find, x_values, y_values)
    soc = np.interp(voltage_per_cell, voltages, soc_values)
    
    return int(soc)

def get_battery_icon_filepath(percentage, image_repo = './', flat = False):
    # 1. Check for NaN or None before doing any math
    if pd.isna(percentage):
        return image_repo + "battery_unknown.png"
    # Ensure percentage is an integer
    p = int(percentage)
    insert = ''
    if flat: 
        insert = '_flat'
    
    if p >= 90:
        return image_repo + f"battery{insert}_full.png"
    elif p >= 70:
        return image_repo + f"battery{insert}_high.png"
    elif p >= 45:
        return image_repo + f"battery{insert}_mid_high.png"
    elif p >= 25:
        return image_repo + f"battery{insert}_low.png"
    elif p >= 10:
        return image_repo + f"battery{insert}_low.png"
    else:
        return image_repo + f"battery{insert}_empty.png"
    


def get_moonphase_filepath(image_repo = './'):
    # Reference New Moon (Jan 6, 2000)
    diff = datetime.now() - datetime(2000, 1, 6, 18, 14)
    days = diff.total_seconds() / 86400
    lunation = days % 29.530588853
    phase_index = int((lunation / 29.53) * 8) % 8
    
    # List matches the order of the lunar cycle
    phases = [
        "new_moon", 
        "waxing_crescent", 
        "first_quarter", 
        "waxing_gibbous",
        "full_moon", 
        "waning_gibbous", 
        "last_quarter", 
        "waning_crescent"
    ]
        
    # Convert "New Moon" -> "new_moon.png"
    # filename = phase_name.lower().replace(" ", "_") + ".png"
    filepath = os.path.join(image_repo, f"{phases[phase_index]}.png")
    
    return filepath, phase_index

def plot_data(df, 
              y_variable_colname, 
              x_variable_colname='received_at',
              chart_type='line',
              x_label = None,
              y_label = None):
    """
    df: The dataframe from Snowflake
    y_col: The column name for the values (Y-axis)
    x_col: The column name for the labels (X-axis)
    chart_type: 'line', 'bar', or 'area'
    """
    x_label if x_label else x_variable_colname
    y_label if x_label else y_variable_colname

    # Create a subset of the dataframe for the chart
    chart_df = df[[x_variable_colname, y_variable_colname]].set_index(x_variable_colname)

    if chart_type == 'line':
        return st.line_chart(chart_df, x_label=x_label,y_label=y_label)
    elif chart_type == 'bar':
        return st.bar_chart(chart_df,x_label=x_label,y_label=y_label)
    elif chart_type == 'area':
        return st.area_chart(chart_df,x_label=x_label,y_label=y_label)
    

import altair as alt
import streamlit as st

def plot_data_altair(df, y_variable_colname, x_variable_colname='received_at', 
              chart_type='line', x_label=None, y_label=None, 
              x_limits=None, y_limits=None, show_ticks=True):
    
    # 1. Map the chart type to Altair marks
    if chart_type == 'bar':
        mark = alt.Chart(df).mark_bar()
    elif chart_type == 'area':
        mark = alt.Chart(df).mark_area(opacity=0.5)
    else:
        mark = alt.Chart(df).mark_line()

    # 2. Build the X and Y encoding with logic for labels, limits, and ticks
    x_axis = alt.X(
        f"{x_variable_colname}:T", # :T tells Altair it's a temporal (time) column
        title=x_label if x_label else x_variable_colname,
        scale=alt.Scale(domain=x_limits) if x_limits else alt.Undefined,
        axis=alt.Axis(ticks=show_ticks, labels=show_ticks, format='%H:%M')
    )

    y_axis = alt.Y(
        f"{y_variable_colname}:Q", # :Q stands for Quantitative (numbers)
        title=y_label if y_label else y_variable_colname,
        scale=alt.Scale(domain=y_limits) if y_limits else alt.Undefined,
        axis=alt.Axis(ticks=show_ticks, labels=show_ticks)
    )

    # 3. Combine into a chart object
    chart = mark.encode(x=x_axis, y=y_axis).interactive()

    return st.altair_chart(chart, use_container_width=True)


import altair as alt
import streamlit as st


def plot_data_altair_hover(df, y_variable_colname, x_variable_colname='received_at', 
                          chart_type='line', x_label=None, y_label=None, 
                          x_limits=None, y_limits='auto', show_ticks=True):
    
    # 1. HANDLE Y-LIMITS
    if y_limits == 'auto':
        y_min = float(df[y_variable_colname].min())
        y_max = float(df[y_variable_colname].max())
        padding = (y_max - y_min) * 0.1 if y_max != y_min else 1
        y_domain = [y_min - padding, y_max + padding]
    elif isinstance(y_limits, list):
        y_domain = y_limits
    else:
        y_domain = alt.Undefined

    # 2. HANDLE X-LIMITS
    # Ensure we only use x_limits if it's a list/sequence
    x_domain = x_limits if isinstance(x_limits, list) else alt.Undefined

    # 3. Base Chart Encoding
    base = alt.Chart(df).encode(
        x=alt.X(f"{x_variable_colname}:T", 
                title=x_label or x_variable_colname,
                scale=alt.Scale(domain=x_domain),
            axis=alt.Axis(ticks=show_ticks, labels=show_ticks, format='%H:%M')),
        y=alt.Y(f"{y_variable_colname}:Q", 
                title=y_label or y_variable_colname,
                scale=alt.Scale(domain=y_domain, clamp=True),
                axis=alt.Axis(ticks=show_ticks, labels=show_ticks))
    )

    # 4. Define the Mark
    if chart_type == 'bar':
        main_chart = base.mark_bar()
    elif chart_type == 'area':
        main_chart = base.mark_area(opacity=0.5)
    else:
        main_chart = base.mark_line()

    # 5. HOVER INTERACTIVITY
    nearest = alt.selection_point(nearest=True, on='mouseover', 
                                  fields=[x_variable_colname], empty=False)

    selectors = alt.Chart(df).mark_point().encode(
        x=f"{x_variable_colname}:T",
        opacity=alt.value(0),
    ).add_params(nearest)

    rules = alt.Chart(df).mark_rule(color='#A1A6B4').encode(
        x=f"{x_variable_colname}:T",
    ).transform_filter(nearest)

    # To show both X and Y in tooltip, use the base encoding for points
    points = base.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip(f"{x_variable_colname}:T", title=x_label or "Time", format='%Y-%m-%d %H:%M'),
            alt.Tooltip(f"{y_variable_colname}:Q", title=y_label or "Value", format='.2f')
        ]
    )

    # 6. Layer and Return
    layered_chart = alt.layer(
        main_chart, selectors, points, rules
    ).properties(width='container').interactive()

    return st.altair_chart(layered_chart, use_container_width=True)


def get_day_boundaries(timestamps, x_col='received_at'):
    """Returns a one-column DataFrame of UTC timestamps marking each Europe/Brussels
    local midnight strictly inside the span of `timestamps` (a UTC-aware Series).
    Empty if the span doesn't cross a local midnight, so callers can skip drawing
    day-separator lines entirely for single-day ranges."""
    timestamps = timestamps.dropna()
    if timestamps.empty:
        return pd.DataFrame({x_col: []})

    tz = pytz.timezone('Europe/Brussels')
    ts_min, ts_max = timestamps.min(), timestamps.max()
    local_min, local_max = ts_min.tz_convert(tz), ts_max.tz_convert(tz)

    if local_min.date() == local_max.date():
        return pd.DataFrame({x_col: []})

    boundaries = []
    day = local_min.date() + timedelta(days=1)
    while day <= local_max.date():
        midnight_utc = tz.localize(datetime.combine(day, datetime.min.time())).astimezone(pytz.UTC)
        if ts_min < midnight_utc < ts_max:
            boundaries.append(midnight_utc)
        day += timedelta(days=1)

    return pd.DataFrame({x_col: pd.to_datetime(boundaries, utc=True)})


# Show only the date (no time) on ticks that land on local midnight; every
# other tick shows just the time. Keeps multi-day axes readable without
# cluttering single-day axes with a repeated date.
DATE_AT_MIDNIGHT_LABEL_EXPR = (
    "(hours(datum.value) == 0 && minutes(datum.value) == 0) "
    "? timeFormat(datum.value, '%d %b') : timeFormat(datum.value, '%H:%M')"
)


def day_boundary_chart(day_boundaries_df, x_col='received_at'):
    """Builds the dashed grey vertical rule layer for day boundaries, or None if empty."""
    if day_boundaries_df.empty:
        return None
    return alt.Chart(day_boundaries_df).mark_rule(
        color='#D1D5DB', strokeDash=[2, 2], opacity=0.7, strokeWidth=3.5
    ).encode(x=alt.X(f"{x_col}:T"))


class TimeSeriesDashboardItem:
    """
    Represent a metric card with an associated time-series plot.
    Highly configurable for multiple Y-variables, specialized labels, and custom colors.
    """
    def __init__(self, metric_title, unit, y_col_main, 
                 y_col_main_label=None, main_color='#1f77b4'):
        self.metric_title = metric_title
        self.unit = unit
        self.y_col_main = y_col_main
        self.y_col_main_label = y_col_main_label or metric_title
        self.main_color = main_color
        
        # Lists for extra configuration
        self.extra_y_series = [] # List of dicts: {'col': str, 'label': str, 'color': str}

    def add_extra_series(self, col_name, label=None, color=None):
        self.extra_y_series.append({
            'col': col_name,
            'label': label or col_name,
            'color': color # If None, Altair default
        })
        return self # Allow chaining

    def _prepare_data(self, df, x_col):
        # 1. Collect all columns and their intended labels
        cols = [self.y_col_main] + [s['col'] for s in self.extra_y_series]
        labels = [self.y_col_main_label] + [s['label'] for s in self.extra_y_series]
        colors = [self.main_color] + [s['color'] for s in self.extra_y_series if s['color']]
        
        # 2. Rename and Melt for Altair
        df_plot = df[ [x_col] + cols ].copy()
        rename_dict = {self.y_col_main: self.y_col_main_label}
        for s in self.extra_y_series:
            rename_dict[s['col']] = s['label']
        
        df_plot = df_plot.rename(columns=rename_dict)
        melted = df_plot.melt(id_vars=[x_col], value_vars=labels, 
                             var_name='Variable', value_name='Value')
        return melted, labels, colors

    def plot(self, df, x_col='received_at', height=280, chart_type='line', y_label=None, y_limits=None, format=".1f", show_dots=False, prediction_df=None, prediction_col=None, y_tick_labels=None, min_max_df=None, min_col=None, max_col=None, show_metric=True, compare_val=None, compare_label=None, window_label=None, extra_controls=None, show_max_line=True, max_line_col=None, max_line_label="max", show_min_line=False, min_line_col=None, min_line_label="min"):
        if df.empty:
            st.warning(f"No data for {self.metric_title}")
            return

        if show_metric:
            col1, col2 = st.columns([1, 2])
            latest_val = df[self.y_col_main].iloc[-1]
            with col1:
                st.metric(self.metric_title, f"{latest_val:{format}} {self.unit}")

                if min_max_df is not None and not min_max_df.empty and min_col and max_col:
                    min_val = min_max_df[min_col].min()
                    max_val = min_max_df[max_col].max()
                    if pd.notna(min_val) and pd.notna(max_val):
                        st.caption(f"min {min_val:{format}}{self.unit} · max {max_val:{format}}{self.unit}")

                if compare_val is not None and pd.notna(compare_val):
                    delta = latest_val - compare_val
                    arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "▶")
                    arrow_color = "#16A34A" if delta > 0 else ("#DC2626" if delta < 0 else "#6B7280")
                    st.caption(
                        f"{compare_label or 'change'} {delta:+{format}}{self.unit} "
                        f"<span style='color:{arrow_color}'>{arrow}</span>",
                        unsafe_allow_html=True
                    )
        else:
            col2 = st.container()

        with col2:
            if extra_controls is not None:
                extra_controls()

            melted_df, labels, colors = self._prepare_data(df, x_col)

            # 1. Base Encoding
            # Calculate Y-axis domain
            if y_limits:
                y_domain = y_limits
            else:
                y_min = float(melted_df['Value'].min())
                y_max = float(melted_df['Value'].max())
                if prediction_df is not None and prediction_col is not None and not prediction_df.empty:
                    y_min = min(y_min, float(prediction_df[prediction_col].min()))
                    y_max = max(y_max, float(prediction_df[prediction_col].max()))
                padding = (y_max - y_min) * 0.1 if y_max != y_min else 1
                y_domain = [y_min - padding, y_max + padding]

            color_scale = alt.Undefined
            if any(colors):
                # Only apply custom scale if colors are provided
                color_scale = alt.Scale(domain=labels, range=colors)

            if y_tick_labels:
                tick_values = list(y_tick_labels.keys())
                label_expr = ' : '.join([f"datum.value === {v} ? '{l}'" for v, l in y_tick_labels.items()]) + " : ''"
                y_encoding = alt.Y("Value:Q", title=y_label or self.unit,
                                   scale=alt.Scale(domain=y_domain, clamp=True),
                                   axis=alt.Axis(values=tick_values, labelExpr=label_expr))
            else:
                y_encoding = alt.Y("Value:Q", title=y_label or self.unit,
                                   scale=alt.Scale(domain=y_domain, clamp=True))

            base = alt.Chart(melted_df).encode(
                x=alt.X(f"{x_col}:T", title=None, axis=alt.Axis(labelExpr=DATE_AT_MIDNIGHT_LABEL_EXPR)),
                y=y_encoding,
                color=alt.Color("Variable:N", 
                                scale=color_scale,
                                title=None, # Remove the "Variable" title from legend
                                legend=alt.Legend(
                                    orient="bottom",
                                    symbolType='stroke', # Use a line/stroke instead of a dot
                                    symbolStrokeWidth=3
                                ) if len(labels) > 1 else None)
            )

            # 2. Mark Type
            if chart_type == 'area':
                main_mark = base.mark_area(opacity=0.4, point=show_dots)
            elif chart_type == 'scatter':
                main_mark = base.mark_point(size=18, filled=True)
            else:
                main_mark = base.mark_line(strokeWidth=2, point=show_dots)

            # 3. Interactivity (The Snapping Hover)
            nearest = alt.selection_point(on='mouseover', nearest=True, fields=[x_col], 
                                          encodings=['x'], empty=False)

            # Build the multiline tooltip list (Show ALL variables in one box)
            tooltip_list = [alt.Tooltip(f"{x_col}:T", title="Time", format='%d %b %H:%M')]
            # Add main series
            tooltip_list.append(alt.Tooltip(f"{self.y_col_main}:Q", title=self.y_col_main_label, format='.2f'))
            # Add extra series values
            for s in self.extra_y_series:
                tooltip_list.append(alt.Tooltip(f"{s['col']}:Q", title=s['label'], format='.2f'))

            # Invisible selectors for better mouse target
            # Note: We use the original 'df' here to have access to all columns at once
            selectors = alt.Chart(df).mark_rule().encode(
                x=f"{x_col}:T",
                opacity=alt.value(0),
                tooltip=tooltip_list
            ).add_params(nearest)

            # Horizontal line for hover
            rules = alt.Chart(melted_df).mark_rule(color='#A1A6B4', strokeDash=[4,4]).encode(
                x=f"{x_col}:T",
            ).transform_filter(nearest)

            # Points appearing on the line(s)
            points = base.mark_point(size=30).encode(
                opacity=alt.condition(nearest, alt.value(1), alt.value(0))
            )

            day_lines = day_boundary_chart(get_day_boundaries(df[x_col]), x_col)

            # Full-width horizontal reference line through the main series' peak,
            # labeled with the max value just above it. Sourced from min_max_df
            # (raw, unresampled data) when available, so the line agrees with the
            # min/max caption in the metric column instead of a resampled mean.
            if show_max_line and min_max_df is not None and not min_max_df.empty and max_col:
                main_max = min_max_df[max_col].max()
            elif show_max_line:
                main_max = df[max_line_col or self.y_col_main].max()
            else:
                main_max = None
            max_line = None
            max_label = None
            if pd.notna(main_max):
                max_line_df = pd.DataFrame({'y': [main_max]})
                max_line = alt.Chart(max_line_df).mark_rule(
                    color='#EF4444', strokeDash=[4, 4], strokeWidth=1, opacity=0.6
                ).encode(y=alt.Y('y:Q', scale=alt.Scale(domain=y_domain, clamp=True)))

                max_label_df = pd.DataFrame({
                    x_col: [df[x_col].min()],
                    'y': [main_max],
                    'label': [f"{max_line_label} {main_max:{format}}{self.unit}"],
                })
                max_label = alt.Chart(max_label_df).mark_text(
                    align='left', baseline='bottom', dy=-2, color='#EF4444', fontSize=11
                ).encode(
                    x=alt.X(f"{x_col}:T"),
                    y=alt.Y('y:Q', scale=alt.Scale(domain=y_domain, clamp=True)),
                    text='label:N'
                )

            # Full-width horizontal reference line through the main series' trough,
            # labeled with the min value just below it. Sourced from min_max_df
            # (raw, unresampled data) when available, so the line agrees with the
            # min/max caption in the metric column instead of a resampled mean.
            if show_min_line and min_max_df is not None and not min_max_df.empty and min_col:
                main_min = min_max_df[min_col].min()
            elif show_min_line:
                main_min = df[min_line_col or self.y_col_main].min()
            else:
                main_min = None
            min_line = None
            min_label = None
            if pd.notna(main_min):
                min_line_df = pd.DataFrame({'y': [main_min]})
                min_line = alt.Chart(min_line_df).mark_rule(
                    color='#3B82F6', strokeDash=[4, 4], strokeWidth=1, opacity=0.6
                ).encode(y=alt.Y('y:Q', scale=alt.Scale(domain=y_domain, clamp=True)))

                min_label_df = pd.DataFrame({
                    x_col: [df[x_col].min()],
                    'y': [main_min],
                    'label': [f"{min_line_label} {main_min:{format}}{self.unit}"],
                })
                min_label = alt.Chart(min_label_df).mark_text(
                    align='left', baseline='top', dy=2, color='#3B82F6', fontSize=11
                ).encode(
                    x=alt.X(f"{x_col}:T"),
                    y=alt.Y('y:Q', scale=alt.Scale(domain=y_domain, clamp=True)),
                    text='label:N'
                )

            layers = (
                ([day_lines] if day_lines is not None else [])
                + ([max_line, max_label] if max_line is not None else [])
                + ([min_line, min_label] if min_line is not None else [])
                + [main_mark, selectors, rules, points]
            )

            if prediction_df is not None and prediction_col is not None and not prediction_df.empty:
                pred_line = alt.Chart(prediction_df).mark_line(
                    strokeWidth=2, strokeDash=[6, 3], opacity=0.8, color='#F97316'
                ).encode(
                    x=alt.X(f"{x_col}:T", title=None, axis=alt.Axis(labelExpr=DATE_AT_MIDNIGHT_LABEL_EXPR)),
                    y=alt.Y(f"{prediction_col}:Q",
                            scale=alt.Scale(domain=y_domain, clamp=True)),
                    tooltip=[
                        alt.Tooltip(f"{x_col}:T", title="Forecast time", format='%d %b %H:%M'),
                        alt.Tooltip(f"{prediction_col}:Q", title="Forecast", format='.1f'),
                    ]
                )
                layers.append(pred_line)

            chart = alt.layer(*layers).properties(
                width='container', height=height
            ).interactive()

            st.altair_chart(chart, use_container_width=True)


# Fixed categorical slot order (blue, aqua, yellow, green, violet, red) so a
# variable keeps its color regardless of which other series are toggled on.
OVERLAY_SERIES_COLORS = {
    'sht_temperature_avg': '#2a78d6',
    'sht_humidity_avg': '#1baf7a',
    'bmp_pressure_avg': '#eda100',
    'light_intensity_avg': '#008300',
    'wind_speed_kmh_avg': '#4a3aa7',
    'rain_mm': '#e34948',
    'wind_speed_kmh_max': '#e87ba4',
    'wind_direction': '#eb6834',
}


def plot_normalized_overlay(df, series_config, x_col='received_at', height=420):
    """
    Overlays multiple differently-scaled series on one chart by indexing each to
    0-100% of its own min-max range within `df`. Only the line's vertical
    position is normalized; the tooltip and legend still show real values/units,
    since the normalized percentage alone isn't meaningful.

    series_config: list of dicts with keys 'col', 'label', 'unit', 'color', 'format'.
    """
    if df.empty or not series_config:
        return None

    long_rows = []
    for s in series_config:
        col = s['col']
        if col not in df.columns:
            continue
        series = df[col]
        col_min, col_max = series.min(), series.max()
        span = col_max - col_min
        if pd.isna(span) or span == 0:
            normalized = pd.Series(50.0, index=series.index)
        else:
            normalized = (series - col_min) / span * 100

        long_rows.append(pd.DataFrame({
            x_col: df[x_col],
            'Variable': s['label'],
            'Normalized': normalized,
            'ChartType': s.get('chart_type', 'line'),
        }))

    if not long_rows:
        return None

    melted = pd.concat(long_rows, ignore_index=True)

    color_scale = alt.Scale(
        domain=[s['label'] for s in series_config],
        range=[s['color'] for s in series_config],
    )

    x_encoding = alt.X(f"{x_col}:T", title=None, axis=alt.Axis(labelExpr=DATE_AT_MIDNIGHT_LABEL_EXPR))
    y_encoding = alt.Y("Normalized:Q", title="Genormaliseerd (0-100%)",
                        scale=alt.Scale(domain=[0, 100], clamp=True),
                        axis=alt.Axis(values=[0, 50, 100]))
    color_encoding = alt.Color("Variable:N", scale=color_scale, title=None,
                                legend=alt.Legend(orient="bottom", symbolType='stroke', symbolStrokeWidth=3))

    # Most series are connected lines; series flagged chart_type='scatter'
    # (e.g. wind direction, where a connected line is misleading) render as
    # standalone points instead.
    line_data = melted[melted['ChartType'] != 'scatter']
    point_data = melted[melted['ChartType'] == 'scatter']

    main_layers = []
    if not line_data.empty:
        main_layers.append(
            alt.Chart(line_data).mark_line(strokeWidth=2).encode(x=x_encoding, y=y_encoding, color=color_encoding)
        )
    if not point_data.empty:
        main_layers.append(
            alt.Chart(point_data).mark_point(size=18, filled=True).encode(x=x_encoding, y=y_encoding, color=color_encoding)
        )

    nearest = alt.selection_point(on='mouseover', nearest=True, fields=[x_col],
                                  encodings=['x'], empty=False)

    # Tooltip is built off the original wide df so hovering shows every
    # enabled series' real value (with unit) together in one box.
    tooltip_list = [alt.Tooltip(f"{x_col}:T", title="Time", format='%d %b %H:%M')]
    for s in series_config:
        if s['col'] in df.columns:
            tooltip_list.append(
                alt.Tooltip(f"{s['col']}:Q", title=f"{s['label']} ({s.get('unit', '')})",
                            format=s.get('format', '.2f'))
            )

    selectors = alt.Chart(df).mark_rule().encode(
        x=f"{x_col}:T",
        opacity=alt.value(0),
        tooltip=tooltip_list,
    ).add_params(nearest)

    rules = alt.Chart(melted).mark_rule(color='#A1A6B4', strokeDash=[4, 4]).encode(
        x=f"{x_col}:T",
    ).transform_filter(nearest)

    hover_points = alt.Chart(melted).mark_point(size=30).encode(
        x=x_encoding, y=y_encoding, color=color_encoding,
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    day_lines = day_boundary_chart(get_day_boundaries(df[x_col]), x_col)
    layers = ([day_lines] if day_lines is not None else []) + main_layers + [selectors, rules, hover_points]

    return alt.layer(*layers).properties(width='container', height=height).interactive()


import math

def render_analog_gauge(value, min_val, max_val, unit="", step=10, label_every=2,
                         track_color="#DBEAFE", fill_color="#2563EB",
                         needle_color="#3d3a2a", muted_color="#898781",
                         width=320, height=240, gradient_colors=None):
    """
    Renders a semi-circular analog gauge (barometer-style) as an SVG string.
    value is clamped to [min_val, max_val] for the needle/arc; the raw value is
    still shown as text so an out-of-range reading is visible, not hidden.

    gradient_colors: optional (start_hex, end_hex) tuple. When given, both the
    track and the fill arc are painted with a left-to-right gradient between
    those colors instead of flat track_color/fill_color - e.g. blue (cold) at
    min_val to red (hot) at max_val, so the arc itself encodes where on the
    scale a reading sits, not just the needle.
    """
    if value is None or pd.isna(value):
        return ""

    clamped = min(max(value, min_val), max_val)
    frac = (clamped - min_val) / (max_val - min_val)

    scale = width / 320
    cx, cy, r = width / 2, 150 * scale, 100 * scale
    stroke_w = 20 * scale

    def point(angle_deg, radius):
        rad = math.radians(angle_deg)
        return cx + radius * math.cos(rad), cy - radius * math.sin(rad)

    def arc_path(start_deg, end_deg, radius):
        x1, y1 = point(start_deg, radius)
        x2, y2 = point(end_deg, radius)
        large_arc = 1 if abs(start_deg - end_deg) > 180 else 0
        return f"M {x1:.2f} {y1:.2f} A {radius:.2f} {radius:.2f} 0 {large_arc} 1 {x2:.2f} {y2:.2f}"

    track_path = arc_path(180, 0, r)
    value_angle = 180 - frac * 180
    fill_path = arc_path(180, value_angle, r)

    gradient_defs = ""
    if gradient_colors is not None:
        gradient_id = f"gauge-grad-{uuid.uuid4().hex[:8]}"
        gx1, gy1 = point(180, r)
        gx2, gy2 = point(0, r)
        gradient_defs = (
            f'<defs><linearGradient id="{gradient_id}" gradientUnits="userSpaceOnUse" '
            f'x1="{gx1:.2f}" y1="{gy1:.2f}" x2="{gx2:.2f}" y2="{gy2:.2f}">'
            f'<stop offset="0%" stop-color="{gradient_colors[0]}"/>'
            f'<stop offset="100%" stop-color="{gradient_colors[1]}"/>'
            f'</linearGradient></defs>'
        )
        track_color = f"url(#{gradient_id})"
        fill_color = f"url(#{gradient_id})"

    # Ticks + selective labels (every `label_every`-th tick, to avoid clutter)
    ticks_svg = []
    n_ticks = int(round((max_val - min_val) / step)) + 1
    for i in range(n_ticks):
        tick_val = min_val + i * step
        angle = 180 - ((tick_val - min_val) / (max_val - min_val)) * 180
        x1, y1 = point(angle, r + stroke_w / 2 + 2 * scale)
        x2, y2 = point(angle, r + stroke_w / 2 + 10 * scale)
        ticks_svg.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{muted_color}" stroke-width="{1.5 * scale:.2f}"/>'
        )
        if i % label_every == 0:
            lx, ly = point(angle, r + stroke_w / 2 + 22 * scale)
            ticks_svg.append(
                f'<text x="{lx:.2f}" y="{ly:.2f}" font-size="{11 * scale:.2f}" fill="{muted_color}" '
                f'text-anchor="middle" dominant-baseline="middle" '
                f'font-family="system-ui, sans-serif">{tick_val:g}</text>'
            )

    # Needle (drawn as a tapered arrow/dart shape rather than a plain line).
    # Reaches radius r, the center of the ring (the arc is stroked around r).
    needle_len = r
    nx, ny = point(value_angle, needle_len)

    dx, dy = nx - cx, ny - cy
    seg_len = math.hypot(dx, dy) or 1.0
    ux, uy = dx / seg_len, dy / seg_len
    perp_x, perp_y = -uy, ux
    needle_half_w = 4 * scale
    base_lx, base_ly = cx + perp_x * needle_half_w, cy + perp_y * needle_half_w
    base_rx, base_ry = cx - perp_x * needle_half_w, cy - perp_y * needle_half_w

    track_opacity = 0.3 if gradient_colors is not None else 1

    return f'''
<div style="display:flex; justify-content:flex-start;">
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
     style="width:100%; max-width:{width}px; height:auto; display:block;"
     xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Gauge, current value {value:.1f} {unit}">
  {gradient_defs}
  <path d="{track_path}" fill="none" stroke="{track_color}" stroke-width="{stroke_w}" stroke-linecap="round" stroke-opacity="{track_opacity}"/>
  <path d="{fill_path}" fill="none" stroke="{fill_color}" stroke-width="{stroke_w}" stroke-linecap="round"/>
  {''.join(ticks_svg)}
  <polygon points="{base_lx:.2f},{base_ly:.2f} {nx:.2f},{ny:.2f} {base_rx:.2f},{base_ry:.2f}" fill="{needle_color}"/>
  <circle cx="{cx}" cy="{cy}" r="{7 * scale:.2f}" fill="{needle_color}"/>
  <text x="{cx}" y="{cy + 42 * scale}" font-size="{30 * scale:.2f}" font-weight="600" fill="{needle_color}"
        text-anchor="middle" font-family="system-ui, sans-serif">{value:.1f}</text>
  <text x="{cx}" y="{cy + 62 * scale}" font-size="{13 * scale:.2f}" fill="{muted_color}"
        text-anchor="middle" font-family="system-ui, sans-serif">{unit}</text>
</svg>
</div>
'''


def render_thermometer(value, min_val=-10, max_val=40, unit="°C", width=70, height=168,
                        tube_color="#E5E7EB", fill_color="#DC2626", text_color="#3d3a2a"):
    """
    Renders a vertical thermometer (bulb + tube) as an SVG string.
    value is clamped to [min_val, max_val] for the fill level; the raw value is
    still shown as text so an out-of-range reading is visible, not hidden.
    """
    if value is None or pd.isna(value):
        return ""

    clamped = min(max(value, min_val), max_val)
    frac = (clamped - min_val) / (max_val - min_val)

    scale = height / 168
    tube_r = 8 * scale
    bulb_r = 14 * scale
    cx = width / 2
    bulb_cy = height - 34 * scale
    tube_top_y = 15 * scale
    tube_bottom_y = bulb_cy - bulb_r * 0.4
    tube_height = tube_bottom_y - tube_top_y
    fill_height = tube_height * frac
    fill_top_y = tube_bottom_y - fill_height
    text_y = bulb_cy + bulb_r + 14 * scale

    return f'''
<div style="display:flex; justify-content:center;">
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
     xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Thermometer, current value {value:.1f} {unit}">
  <rect x="{cx - tube_r:.2f}" y="{tube_top_y:.2f}" width="{2 * tube_r:.2f}" height="{tube_height:.2f}"
        rx="{tube_r:.2f}" fill="{tube_color}"/>
  <rect x="{cx - tube_r:.2f}" y="{fill_top_y:.2f}" width="{2 * tube_r:.2f}" height="{fill_height:.2f}"
        rx="{tube_r:.2f}" fill="{fill_color}"/>
  <circle cx="{cx:.2f}" cy="{bulb_cy:.2f}" r="{bulb_r:.2f}" fill="{fill_color}"/>
  <text x="{cx:.2f}" y="{text_y:.2f}" font-size="{13 * scale:.2f}" fill="{text_color}"
        text-anchor="middle" font-family="system-ui, sans-serif">{value:.1f}{unit}</text>
</svg>
</div>
'''


WIND_SPEED_BINS = [0, 5, 10, 15, 20, np.inf]
# Blue (calm) -> red (strong), ColorBrewer 5-class RdYlBu reversed.
WIND_ROSE_COLORS = ['#2c7bb6', '#abd9e9', '#ffffbf', '#fdae61', '#d7191c']


def _speed_bin_labels(speed_bins):
    labels = []
    for lo, hi in zip(speed_bins[:-1], speed_bins[1:]):
        labels.append(f"{lo:.0f}+ km/h" if np.isinf(hi) else f"{lo:.0f}-{hi:.0f} km/h")
    return labels


def render_wind_rose_legend_html(speed_bins=WIND_SPEED_BINS, colors=WIND_ROSE_COLORS):
    """Standalone color-swatch legend for the wind rose, meant for its own column."""
    labels = _speed_bin_labels(speed_bins)
    rows = "".join(
        f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">'
        f'<span style="width:14px; height:14px; border-radius:3px; background:{color}; display:inline-block;"></span>'
        f'<span style="font-size:13px;">{label}</span>'
        f'</div>'
        for label, color in zip(labels, colors)
    )
    return f'<div style="margin-top:40px;"><b style="font-size:13px;">Wind speed</b><div style="margin-top:8px;">{rows}</div></div>'


def build_wind_rose_data(df, direction_col='wind_direction', speed_col='wind_speed_kmh_avg',
                          n_sectors=16, speed_bins=WIND_SPEED_BINS,
                          gate_col='wind_speed_kmh_max', min_gate_speed=3.0):
    """
    Bins readings into n_sectors compass sectors x speed bands, and returns
    per (sector, speed band) the reading count plus cumulative counts for
    stacking - the inputs a stacked wind rose chart needs.

    A reading is only counted if `gate_col` (the gust/max speed, regardless of
    which column the rose itself displays) is at least `min_gate_speed` - below
    that, the wind vane's direction is effectively noise.
    """
    sector_names = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                     'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    speed_labels = _speed_bin_labels(speed_bins)
    sector_width = 360 / n_sectors

    grid = pd.MultiIndex.from_product([range(n_sectors), speed_labels], names=['sector_idx', 'speed_bin'])
    rose = pd.DataFrame(index=grid).reset_index()
    rose['sector'] = rose['sector_idx'].map(lambda i: sector_names[i])
    center_deg = rose['sector_idx'] * sector_width
    rose['theta_start'] = np.deg2rad(center_deg - sector_width / 2)
    rose['theta_end'] = np.deg2rad(center_deg + sector_width / 2)
    rose['speed_bin'] = pd.Categorical(rose['speed_bin'], categories=speed_labels, ordered=True)

    # Exclude calm/near-calm readings, gated on gust speed rather than the
    # rose's own display column - below min_gate_speed, the wind vane's
    # direction is effectively noise, regardless of avg vs max.
    cols_needed = list(dict.fromkeys([direction_col, speed_col, gate_col]))
    data = df[cols_needed].dropna()
    data = data[data[gate_col] >= min_gate_speed]
    if not data.empty:
        sector_idx = (np.round(data[direction_col] / sector_width) % n_sectors).astype(int)
        speed_bin = pd.cut(data[speed_col], bins=speed_bins, labels=speed_labels, right=False, include_lowest=True)
        counts = data.assign(sector_idx=sector_idx, speed_bin=speed_bin).groupby(['sector_idx', 'speed_bin'], observed=False).size()
        rose = rose.set_index(['sector_idx', 'speed_bin'])
        rose['count'] = counts.reindex(rose.index, fill_value=0).astype(int)
        rose = rose.reset_index()
    else:
        rose['count'] = 0

    rose = rose.sort_values(['sector_idx', 'speed_bin'])
    rose['cum_count'] = rose.groupby('sector_idx')['count'].cumsum()
    rose['cum_count_prev'] = rose['cum_count'] - rose['count']
    return rose.reset_index(drop=True)


def render_wind_rose_chart(rose_df, size=300, speed_bins=WIND_SPEED_BINS):
    """
    Renders a stacked polar wind-rose chart: wedge angle = compass sector,
    wedge radius = cumulative reading count (sqrt-scaled so annulus area
    reflects frequency), color band = wind speed range within that sector.
    """
    if rose_df.empty or rose_df['count'].sum() == 0:
        return None

    speed_labels = _speed_bin_labels(speed_bins)
    max_total = int(rose_df.groupby('sector_idx')['count'].sum().max())
    max_radius = size / 2 - 24
    pos_scale = alt.Scale(domain=[0, size], range=[0, size])

    # Reference rings: 3 evenly spaced count levels, radius uses the same
    # sqrt mapping as the wedges so the rings line up with the stacked data.
    ring_levels = sorted({round(max_total * f) for f in (1 / 3, 2 / 3, 1)} - {0})
    rings_df = pd.DataFrame({'level': ring_levels})
    rings_df['r'] = rings_df['level'].apply(lambda lvl: max_radius * math.sqrt(lvl / max_total))

    rings = alt.Chart(rings_df).mark_arc(fill='#D1D5DB', opacity=0.5).encode(
        x=alt.value(size / 2),
        y=alt.value(size / 2),
        theta=alt.value(0),
        theta2=alt.value(2 * math.pi),
        radius=alt.Radius('r_outer:Q', scale=None),
        radius2=alt.Radius2('r_inner:Q'),
    ).transform_calculate(
        r_outer='datum.r + 1',
        r_inner='max(datum.r - 1, 0)'
    )

    ring_angle = math.radians(45)
    rings_df['label_x'] = size / 2 + rings_df['r'] * math.sin(ring_angle)
    rings_df['label_y'] = size / 2 - rings_df['r'] * math.cos(ring_angle)
    ring_labels = alt.Chart(rings_df).mark_text(fontSize=9, color='#898781', dx=4).encode(
        x=alt.X('label_x:Q', axis=None, scale=pos_scale),
        y=alt.Y('label_y:Q', axis=None, scale=pos_scale),
        text='level:Q'
    )

    wedges = alt.Chart(rose_df).mark_arc(stroke='white', strokeWidth=1, opacity=0.9).encode(
        x=alt.value(size / 2),
        y=alt.value(size / 2),
        theta=alt.Theta('theta_start:Q', scale=None),
        theta2='theta_end:Q',
        radius=alt.Radius('cum_count:Q', scale=alt.Scale(type='sqrt', domain=[0, max_total], range=[0, max_radius])),
        radius2='cum_count_prev:Q',
        color=alt.Color('speed_bin:O', scale=alt.Scale(domain=speed_labels, range=WIND_ROSE_COLORS), legend=None),
        tooltip=[
            alt.Tooltip('sector:N', title='Direction'),
            alt.Tooltip('speed_bin:O', title='Speed range'),
            alt.Tooltip('count:Q', title='Readings'),
        ]
    )

    label_deg = {'N': 0, 'E': 90, 'S': 180, 'W': 270}
    label_r = size / 2 - 10
    labels_df = pd.DataFrame({
        'label': list(label_deg.keys()),
        'x': [size / 2 + label_r * math.sin(math.radians(a)) for a in label_deg.values()],
        'y': [size / 2 - label_r * math.cos(math.radians(a)) for a in label_deg.values()],
    })
    labels = alt.Chart(labels_df).mark_text(fontSize=12, fontWeight='bold', color='#898781').encode(
        x=alt.X('x:Q', axis=None, scale=pos_scale),
        y=alt.Y('y:Q', axis=None, scale=pos_scale),
        text='label:N'
    )

    return alt.layer(rings, wedges, ring_labels, labels).properties(width=size, height=size).configure_view(strokeWidth=0)


def transform_to_radial_cartesian(df, time_col, degree_col):
    """
    Transforms degree data over time into x, y coordinates 
    where time = radius (0 to 1) and degrees = angle.
    """
    # 1. Sort by time to ensure the sequence is correct
    df = df.sort_values(time_col).copy()
    
    # 2. Create the Radius (r)
    # Scales from 0 (first row) to 1 (last row)
    n = len(df)
    if n > 1:
        df['r'] = np.linspace(0, 1, n)
    else:
        df['r'] = 0

    # 3. Convert Degrees to Radians
    # We use (90 - degrees) or simply sin/cos swap to ensure 0 is North
    rad = np.deg2rad(df[degree_col])

    # 4. Calculate X and Y
    # x = r * sin(theta), y = r * cos(theta)
    df['x_radial'] = df['r'] * np.sin(rad)
    df['y_radial'] = df['r'] * np.cos(rad)
    
    return df[['x_radial', 'y_radial']]