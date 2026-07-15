import streamlit as st
import pandas as pd
import numpy as np
import utils
import os
import pytz
import calendar
from datetime import datetime

st.set_page_config(layout="wide")
st.title("Regen")

# Historical monthly totals (mm) from before the sensor's own logging started,
# transcribed from an older record. '---' months (no data yet, device/station
# not yet active) are simply omitted here.
HISTORICAL_RAIN_MM = {
    2011: {8: 46.6, 9: 51.4, 10: 45.0, 11: 7.8, 12: 128.8},
    2012: {1: 65.0, 2: 22.0, 3: 27.4, 4: 65.4, 5: 53.4, 6: 97.0, 7: 96.2, 8: 25.0, 9: 38.8, 10: 93.8, 11: 33.0, 12: 142.8},
    2013: {1: 40.0, 2: 38.8, 3: 33.0, 4: 20.6, 5: 93.0, 6: 61.6, 7: 77.0, 8: 38.0, 9: 99.6, 10: 118.0, 11: 118.2, 12: 81.8},
    2014: {1: 46.6, 2: 80.4, 3: 24.4, 4: 5.4, 5: 67.6, 6: 53.6, 7: 137.0, 8: 123.6, 9: 20.0, 10: 73.1, 11: 55.4, 12: 65.6},
    2015: {1: 90.3, 2: 49.8, 3: 47.0, 4: 19.0, 5: 49.6, 6: 33.0, 7: 42.6, 8: 29.4, 9: 54.4, 10: 31.8, 11: 69.8, 12: 42.4},
    2016: {1: 109.8, 2: 69.0, 3: 68.4, 4: 50.6, 5: 70.4, 6: 78.0, 7: 20.6, 8: 25.2, 9: 10.4, 10: 41.8, 11: 71.2, 12: 17.6},
    2017: {1: 54.0, 2: 60.0, 3: 38.0, 4: 24.2, 5: 31.4, 6: 25.6, 7: 54.6, 8: 59.0, 9: 55.4, 10: 34.6, 11: 76.2, 12: 102.4},
    2018: {1: 61.8, 2: 20.0, 3: 52.6, 4: 30.6, 5: 28.0, 6: 13.2, 7: 5.6, 8: 60.6, 9: 39.4, 10: 44.2, 11: 27.8, 12: 67.2},
    2019: {1: 53.2, 2: 41.6, 3: 59.8, 4: 23.2, 5: 35.6, 6: 59.2, 7: 31.2, 8: 36.4, 9: 36.0, 10: 65.8, 11: 57.4, 12: 61.8},
    2020: {1: 31.2, 2: 85.8, 3: 54.0, 4: 23.0, 5: 22.0, 6: 52.8, 7: 31.6, 8: 61.6, 9: 91.6, 10: 73.6, 11: 28.8, 12: 62.6},
    2021: {1: 77.4, 2: 41.2, 3: 34.0, 4: 22.6, 5: 84.8, 6: 69.0, 7: 56.8, 8: 75.6, 9: 23.2, 10: 77.2, 11: 22.2, 12: 80.8},
    2022: {1: 43.0, 2: 69.4, 3: 1.4, 4: 23.8, 5: 84.0, 6: 86.2, 7: 9.0, 8: 5.4, 9: 151.6, 10: 54.2, 11: 76.6, 12: 95.8},
    2023: {1: 96.2, 2: 10.2, 3: 120.2, 4: 76.6, 5: 72.0, 6: 41.4, 7: 117.0, 8: 110.8, 9: 69.8, 10: 125.2, 11: 166.4, 12: 101.8},
    2024: {1: 84.4, 2: 116.2, 3: 82.6, 4: 79.4, 5: 106.6, 6: 85.4, 7: 85.2, 8: 95.0, 9: 100.8, 10: 64.6, 11: 81.2, 12: 68.4},
    2025: {1: 122.0, 2: 45.6, 3: 6.8, 4: 9.4, 5: 27.0, 6: 37.8, 7: 82.0, 8: 18.8, 9: 58.6, 10: 104.0, 11: 78.0, 12: 32.2},
}

current_dir = os.path.dirname(__file__)
asset_path = os.path.join(current_dir, "..", "assets")
discharge_csv_path = os.path.join(asset_path, 'LiPo_smooth_discharge_curve.csv')
discharge_curve = pd.read_csv(discharge_csv_path)
df = utils.get_data(discharge_curve)

tz = pytz.timezone('Europe/Brussels')
work = df.dropna(subset=['received_at']).copy() if not df.empty else df

if not work.empty and 'rain_mm' in work.columns:
    work['local_dt'] = work['received_at'].dt.tz_convert(tz)
    work['year'] = work['local_dt'].dt.year
    work['month'] = work['local_dt'].dt.month
    monthly_totals = work.groupby(['year', 'month'])['rain_mm'].sum(min_count=1)
    monthly_counts = work.groupby(['year', 'month']).size()
    sensor_years = set(work['year'].unique())
else:
    monthly_totals = pd.Series(dtype=float)
    monthly_counts = pd.Series(dtype=int)
    sensor_years = set()

years = sorted(sensor_years | set(HISTORICAL_RAIN_MM.keys()))
months = list(range(1, 13))
month_labels = [calendar.month_abbr[m] for m in months]

now_local = datetime.now(tz)
current_year, current_month = now_local.year, now_local.month


def cell_value(year, month):
    """Returns (value, present). Sensor data takes precedence in the (impossible,
    since ranges don't overlap) case both sources cover the same month."""
    if (year, month) in monthly_counts.index and monthly_counts.loc[(year, month)] > 0:
        total = monthly_totals.loc[(year, month)]
        return (0.0 if pd.isna(total) else float(total)), True
    if year in HISTORICAL_RAIN_MM and month in HISTORICAL_RAIN_MM[year]:
        return HISTORICAL_RAIN_MM[year][month], True
    return 0.0, False


def fmt(value, partial):
    text = f"{value:.1f}"
    return text + "*" if partial else text


table_rows = []
value_rows = []  # parallel raw-numeric rows, used for cell coloring (NaN = no data)
for y in years:
    row = {"Jaar": y}
    value_row = {"Jaar": y}
    year_total, year_has_data, year_partial = 0.0, False, False
    for m, label in zip(months, month_labels):
        val, present = cell_value(y, m)
        is_current = (y == current_year and m == current_month)
        row[label] = fmt(val, is_current) if present else ""
        value_row[label] = val if present else float("nan")
        if present:
            year_has_data = True
            year_total += val
            if is_current:
                year_partial = True
    row["Totaal"] = fmt(year_total, year_partial) if year_has_data else ""
    value_row["Totaal"] = float("nan")
    table_rows.append(row)
    value_rows.append(value_row)

# "Totaal" row: per-month sum across all years
total_row = {"Jaar": "Totaal"}
grand_total, grand_has_data = 0.0, False
for m, label in zip(months, month_labels):
    month_total, month_has_data, month_partial = 0.0, False, False
    for y in years:
        val, present = cell_value(y, m)
        if present:
            month_has_data = True
            month_total += val
            if y == current_year and m == current_month:
                month_partial = True
    if month_has_data:
        total_row[label] = fmt(month_total, month_partial)
        grand_total += month_total
        grand_has_data = True
    else:
        total_row[label] = ""
total_row["Totaal"] = fmt(grand_total, current_year in years) if grand_has_data else ""
table_rows.append(total_row)
value_rows.append({"Jaar": "Totaal", **{label: float("nan") for label in month_labels}, "Totaal": float("nan")})

if not table_rows:
    st.warning("Geen regendata beschikbaar")
else:
    table_df = pd.DataFrame(table_rows).set_index("Jaar")
    values_df = pd.DataFrame(value_rows).set_index("Jaar")

    # --- Color scale: red (low) -> neutral gray (mid) -> blue (high) -----------
    RED = (227, 73, 72)      # #e34948
    NEUTRAL = (240, 239, 236)  # #f0efec
    BLUE = (42, 120, 214)     # #2a78d6

    def lerp(c1, c2, t):
        return tuple(a + (b - a) * t for a, b in zip(c1, c2))

    def rgb_to_hex(rgb):
        return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, round(c))) for c in rgb))

    def value_to_color(v, red_start, blue_start):
        if blue_start <= red_start:
            frac = 0.5
        else:
            frac = (v - red_start) / (blue_start - red_start)
            frac = max(0.0, min(1.0, frac))
        if frac <= 0.5:
            rgb = lerp(RED, NEUTRAL, frac / 0.5)
        else:
            rgb = lerp(NEUTRAL, BLUE, (frac - 0.5) / 0.5)
        return rgb_to_hex(rgb)

    month_cells = values_df.drop(index="Totaal", columns="Totaal")
    data_min = float(month_cells.min().min())
    data_max = float(month_cells.max().max())

    red_start, blue_start = st.slider(
        "Kleurbereik (rood → blauw), mm",
        min_value=float(np.floor(data_min)),
        max_value=float(np.ceil(data_max)),
        value=(float(np.floor(data_min)), float(np.ceil(data_max))),
        step=1.0,
    )

    def style_row(row):
        styles = []
        for col in table_df.columns:
            if row.name == "Totaal" or col == "Totaal":
                styles.append("")
                continue
            v = values_df.loc[row.name, col]
            styles.append("" if pd.isna(v) else f"background-color: {value_to_color(v, red_start, blue_start)}")
        return styles

    styled = table_df.style.apply(style_row, axis=1)
    table_height = (len(table_df) + 1) * 35 + 3  # header row + one row per year, no vertical scroll
    st.dataframe(styled, use_container_width=True, height=table_height)
    st.caption("Waarden in mm. * = lopende maand, nog niet volledig. Data vóór 2026 is historisch, handmatig ingevoerd.")
