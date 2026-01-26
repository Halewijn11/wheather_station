import pandas as pd
import streamlit as st
import altair as alt
from astral import LocationInfo
from astral.sun import sun
from datetime import date
import numpy as np
from streamlit_gsheets import GSheetsConnection

def get_google_sheet_df(sheet_id = "1zPwrfEDDBZVqb3mwbBCHdeCaGAHnUresvGlHDXuD_qI", sheet_gid=None, base_url="https://docs.google.com/spreadsheets/d/"):
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
def filter_by_recency(df, hours=0, minutes=0, seconds=0, 
                      time_colname = 'seconds_since_now', 
                      colname_unit = 'seconds', mode = 'live'):
    """
    Filters the dataframe to only include rows from 'now' back to a specific duration.
    """
    # 1. Calculate the total window in minutes
    total_window_seconds = (hours * 3600) + (minutes*60) + (seconds)
    
    # 2. Filter the dataframe
    # We want rows where the 'minutes_since_now' is less than or equal to our window
    if mode == 'live':
        mask = df[time_colname] <= total_window_seconds
        filtered_df = df.loc[mask].copy()
        return filtered_df
    elif mode == 'last_session': 
        latest_recorded_second = df['seconds_since_now'].min() # assuming 0 is 'now'
        limit = latest_recorded_second + (total_window_seconds)
        mask = df[time_colname] <= limit
        filtered_df = df.loc[mask].copy()
        return filtered_df

    # return filtered_df


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

def tidy_google_sheet_df(google_sheet_df):
    df = google_sheet_df.copy()
    #formatting
    df['received_at'] =pd.to_datetime(df['received_at'], utc=True).dt.floor('s').dt.floor('s')

    #enriching the data
    df['received_at_td_seconds'] = df['received_at'].diff().dt.total_seconds() #td stands for time difference
    df['received_at_td_minutes'] = df['received_at_td_seconds']/60
    now = pd.Timestamp.now(tz='UTC')
    df['seconds_since_now'] = (now - df['received_at']).dt.total_seconds()

    return df

@st.cache_data()
def get_data():
    url = "https://docs.google.com/spreadsheets/d/1OW-KdOF9BSuR66o9qbumSkNck3TlXb1himbQnLeFvVE/edit?gid=0#gid=0"
    # Note: Ensure st.connection is available here
    conn = st.connection("gsheets", type=GSheetsConnection)
    google_sheet_df = conn.read(spreadsheet=url, ttl=0) 
    
    # Assuming tidy_google_sheet_df is also in this utils.py file
    df = tidy_google_sheet_df(google_sheet_df)
    return df

def resample_data(df, window_label):
    # Ensure the index is datetime for resampling
    df = df.copy()
    df.set_index('received_at', inplace=True)
    
    # Define resolution based on selection
    if window_label == "Last Hour":
        return df.reset_index() # Raw data (no change)
    elif window_label == "Last 24 Hours":
        resample_rate = '15min'
    else: # Last Week
        resample_rate = '1H'
    
    # Resample numeric columns only, then reset index to keep 'received_at'
    resampled_df = df.select_dtypes(include=['number']).resample(resample_rate).mean()
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

    sunrise_str = s["sunrise"].strftime("%H:%M") + " AM"
    sunset_str = s["sunset"].strftime("%H:%M") + " PM"

    return sunrise_str, sunset_str


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
        axis=alt.Axis(ticks=show_ticks, labels=show_ticks)
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
                axis=alt.Axis(ticks=show_ticks, labels=show_ticks)),
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


import streamlit as st
import altair as alt

def plot_data_altair_final(df, y_variable_colname, x_variable_colname='received_at', 
                          chart_type='line', x_label=None, y_label=None, 
                          x_limits=None, y_limits='auto', show_ticks=True, height = 200):
    
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
    x_domain = x_limits if isinstance(x_limits, list) else alt.Undefined

    # 3. BASE ENCODING
    base = alt.Chart(df).encode(
        x=alt.X(f"{x_variable_colname}:T", 
                title=x_label or x_variable_colname,
                scale=alt.Scale(domain=x_domain),
                axis=alt.Axis(ticks=show_ticks, labels=show_ticks)),
        y=alt.Y(f"{y_variable_colname}:Q", 
                title=y_label or y_variable_colname,
                scale=alt.Scale(domain=y_domain, clamp=True),
                axis=alt.Axis(ticks=show_ticks, labels=show_ticks))
    )

    # 4. MAIN CHART TYPE
    if chart_type == 'bar':
        main_chart = base.mark_bar()
    elif chart_type == 'area':
        main_chart = base.mark_area(opacity=0.5)
    else:
        main_chart = base.mark_line(strokeWidth=2)

    # 5. HOVER INTERACTIVITY LOGIC
    # Create a selection that snaps to the X-axis (time) only
    nearest = alt.selection_point(
        on='mouseover', 
        nearest=True, 
        fields=[x_variable_colname], 
        encodings=['x'], 
        empty=False
    )

    # Invisible selectors (Rule) to capture mouse anywhere on the vertical plane
    # We attach the tooltip HERE so it shows up for the whole vertical area
    selectors = alt.Chart(df).mark_rule().encode(
        x=f"{x_variable_colname}:T",
        opacity=alt.value(0),
        tooltip=[
            alt.Tooltip(f"{x_variable_colname}:T", title=x_label or "Time", format='%Y-%m-%d %H:%M'),
            alt.Tooltip(f"{y_variable_colname}:Q", title=y_label or "Value", format='.2f')
        ]
    ).add_params(nearest)

    # The visible vertical guide line
    rules = alt.Chart(df).mark_rule(color='#A1A6B4', strokeDash=[4,4]).encode(
        x=f"{x_variable_colname}:T",
    ).transform_filter(nearest)

    # The point that appears on the line during hover
    points = base.mark_point(color='red', size=60).encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # 6. LAYER AND RENDER
    # We stack them: line -> selectors -> rules -> points
    layered_chart = alt.layer(
        main_chart, selectors, rules, points
    ).properties(
        width='container',
        height=height,
    ).interactive()

    return st.altair_chart(layered_chart, use_container_width=True)


def plot_metric_with_graph(time_window_df, y_variable_colname, y_variable_unit, 
                           y_variable_prefix_text, y_label, x_label='received at', x_variable_colname = 'received_at'):
    """
    Creates a row with a Streamlit metric on the left and 
    the custom Altair snapping chart on the right.
    """
    col1, col2 = st.columns([1, 2])
    
    # Get the most recent value from the dataframe
    if not time_window_df.empty:
        latest = time_window_df[y_variable_colname].iloc[-1]
    else:
        latest = 0.0

    with col1:
        st.metric(f"{y_variable_prefix_text}", f"{latest:.1f} {y_variable_unit}")

    with col2:
        # Calling your optimized Altair function
        plot_data_altair_final(
            time_window_df, 
            y_variable_colname=y_variable_colname,
            x_label=x_label,
            y_label=y_label,
            x_variable_colname = x_variable_colname
        )


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