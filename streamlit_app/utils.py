import pandas as pd
import streamlit as st
import altair as alt

def get_google_sheet_df(base_url = "https://docs.google.com/spreadsheets/d/",
                sheet_id = "1zPwrfEDDBZVqb3mwbBCHdeCaGAHnUresvGlHDXuD_qI"): 
    df = pd.read_csv(f"{base_url}{sheet_id}/export?format=csv")
    return df

def get_full_payload_colname(col_name):
    return f"uplink_message_decoded_payload_{col_name}"

# def get_metadata_google_sheet_col_name(col_name):
#     return f"uplink_message_decoded_payload{col_name}"
def filter_by_recency(df, hours=0, minutes=0, seconds=0, 
                      time_colname = 'seconds_since_now', 
                      colname_unit = 'seconds'):
    """
    Filters the dataframe to only include rows from 'now' back to a specific duration.
    """
    # 1. Calculate the total window in minutes
    total_window_seconds = (hours * 3600) + (minutes*60) + (seconds)
    
    # 2. Filter the dataframe
    # We want rows where the 'minutes_since_now' is less than or equal to our window

    mask = df[time_colname] <= total_window_seconds
    filtered_df = df.loc[mask].copy()
    
    return filtered_df

def tidy_google_sheet_df(google_sheet_df, 
                         payload_data_col_name_list = ['pressure', 'temperature', 'fan_rpm'],
                         data_cols = ['received_at'],
                         lora_signal_quality_cols = ['uplink_message_rx_metadata_0_rssi', 'uplink_message_rx_metadata_0_snr', 'uplink_message_rx_metadata_0_channel_rssi']):
    cols = []
    payload_data_full_col_name_list = [get_full_payload_colname(payload_data_col_name) for payload_data_col_name in payload_data_col_name_list]
    cols.extend(data_cols)
    cols.extend(payload_data_full_col_name_list)
    cols.extend(lora_signal_quality_cols)
    df = google_sheet_df.copy()
    df = df[cols]

    #formatting
    df['received_at'] =pd.to_datetime(df['received_at'], utc=True).dt.floor('s').dt.floor('s')

    #enriching the data
    df['received_at_td_seconds'] = df['received_at'].diff().dt.total_seconds() #td stands for time difference
    df['received_at_td_minutes'] = df['received_at_td_seconds']/60
    now = pd.Timestamp.now(tz='UTC')
    df['seconds_since_now'] = (now - df['received_at']).dt.total_seconds()
    return df

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
