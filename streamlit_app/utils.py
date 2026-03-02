import pandas as pd
import streamlit as st
import altair as alt
from astral import LocationInfo
from astral.sun import sun
from datetime import date, timedelta
import numpy as np
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import os
import pytz

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
def filter_by_recency(df, window_label=None, hours=0, minutes=0, seconds=0, 
                      time_colname = 'seconds_since_now', 
                      colname_unit = 'seconds', mode = 'live'):
    """
    Filters the dataframe to only include rows from 'now' back to a specific duration.
    Also supports semantic window labels (Since Midnight, This Week, This Month).
    """
    if df.empty:
        return df

    tz = pytz.timezone('Europe/Brussels')
    now = datetime.now(tz)
    
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

def tidy_google_sheet_df(google_sheet_df, discharge_curve, num_batteries = 1):
    df = google_sheet_df.copy()
    #formatting
    df['received_at'] =pd.to_datetime(df['received_at'], utc=True).dt.floor('s').dt.floor('s')

    #enriching the data
    df['received_at_td_seconds'] = df['received_at'].diff().dt.total_seconds() #td stands for time difference
    df['received_at_td_minutes'] = df['received_at_td_seconds']/60
    now = pd.Timestamp.now(tz='UTC')
    df['seconds_since_now'] = (now - df['received_at']).dt.total_seconds()
    df['battery_percentage'] = df.apply(
    lambda row: calculate_stage_of_charge(discharge_curve, num_batteries, row['voltage_avg']) 
    if pd.notnull(row['voltage_avg']) else np.nan, 
    axis=1
    )

    return df

@st.cache_data(ttl = 3*60)
def get_data(discharge_curve):
    url = "https://docs.google.com/spreadsheets/d/1OW-KdOF9BSuR66o9qbumSkNck3TlXb1himbQnLeFvVE/edit?gid=0#gid=0"
    # Note: Ensure st.connection is available here
    conn = st.connection("gsheets", type=GSheetsConnection)
    google_sheet_df = conn.read(spreadsheet=url, ttl=0) 
    
    # Assuming tidy_google_sheet_df is also in this utils.py file
    df = tidy_google_sheet_df(google_sheet_df, discharge_curve)
    return df

def resample_data(df, window_label):
    # Ensure the index is datetime for resampling
    df = df.copy()
    df.set_index('received_at', inplace=True)
    
    # Define resolution based on selection
    if window_label == "Last Hour":
        return df.reset_index() # Raw data (no change)
    elif window_label in ["Last 24 Hours", "Since Midnight"]:
        resample_rate = '5min'
    elif window_label in ["This Week", "Last 7 Days"]:
        resample_rate = '1H'
    elif window_label == "This Month":
        resample_rate = '3H' # Larger window, larger step
    else:
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
        # Collect all columns and their intended labels
        cols = [self.y_col_main] + [s['col'] for s in self.extra_y_series]
        labels = [self.y_col_main_label] + [s['label'] for s in self.extra_y_series]
        colors = [self.main_color] + [s['color'] for s in self.extra_y_series if s['color']]
        
        # Melt dataframe for Altair
        df_plot = df.copy()
        # Rename columns to labels before melting for easier Altair logic
        rename_dict = {self.y_col_main: self.y_col_main_label}
        for s in self.extra_y_series:
            rename_dict[s['col']] = s['label']
        
        df_plot = df_plot.rename(columns=rename_dict)
        melted = df_plot.melt(id_vars=[x_col], value_vars=labels, 
                             var_name='Variable', value_name='Value')
        return melted, labels, colors

    def plot(self, df, x_col='received_at', height=200, chart_type='line', y_label=None):
        if df.empty:
            st.warning(f"No data for {self.metric_title}")
            return

        col1, col2 = st.columns([1, 2])
        
        latest_val = df[self.y_col_main].iloc[-1]
        with col1:
            st.metric(self.metric_title, f"{latest_val:.1f} {self.unit}")

        with col2:
            melted_df, labels, colors = self._prepare_data(df, x_col)
            
            # 1. Base Encoding
            # Calculate Y-axis domain
            y_min = float(melted_df['Value'].min())
            y_max = float(melted_df['Value'].max())
            padding = (y_max - y_min) * 0.1 if y_max != y_min else 1
            y_domain = [y_min - padding, y_max + padding]

            color_scale = alt.Undefined
            if any(colors):
                # Only apply custom scale if colors are provided
                color_scale = alt.Scale(domain=labels, range=colors)

            base = alt.Chart(melted_df).encode(
                x=alt.X(f"{x_col}:T", title=None),
                y=alt.Y("Value:Q", title=y_label or self.unit, 
                        scale=alt.Scale(domain=y_domain, clamp=True)),
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
                main_mark = base.mark_area(opacity=0.4)
            else:
                main_mark = base.mark_line(strokeWidth=2)

            # 3. Interactivity (The Snapping Hover)
            nearest = alt.selection_point(on='mouseover', nearest=True, fields=[x_col], 
                                          encodings=['x'], empty=False)

            # Build the multiline tooltip list (Show ALL variables in one box)
            tooltip_list = [alt.Tooltip(f"{x_col}:T", title="Time", format='%H:%M')]
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
            points = base.mark_point(size=60).encode(
                opacity=alt.condition(nearest, alt.value(1), alt.value(0))
            )

            chart = alt.layer(main_mark, selectors, rules, points).properties(
                width='container', height=height
            ).interactive()

            st.altair_chart(chart, use_container_width=True)


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