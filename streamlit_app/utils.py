import pandas as pd

def get_google_sheet_df(base_url = "https://docs.google.com/spreadsheets/d/",
                sheet_id = "1zPwrfEDDBZVqb3mwbBCHdeCaGAHnUresvGlHDXuD_qI"): 
    df = pd.read_csv(f"{base_url}{sheet_id}/export?format=csv")
    return df

def tidy_google_sheet_df(google_sheet_df, 
                         payload_data_cols = ["uplink_message_decoded_payload_field1", "uplink_message_decoded_payload_field2"],
                         data_cols = ['received_at'],
                         lora_signal_quality_cols = ['uplink_message_rx_metadata_0_rssi', 'uplink_message_rx_metadata_0_snr', 'uplink_message_rx_metadata_0_channel_rssi']):
    cols = []
    cols.extend(data_cols)
    cols.extend(payload_data_cols)
    cols.extend(lora_signal_quality_cols)
    df = google_sheet_df.copy()
    df = df[cols]

    #formatting
    df['received_at'] =pd.to_datetime(df['received_at'], utc=True).dt.floor('s').dt.floor('s')

    #enriching the data
    df['received_at_td'] = df['received_at'].diff().dt.total_seconds()/60 #td stands for time difference
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
