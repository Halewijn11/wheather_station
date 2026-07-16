import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import utils
import os
import calendar
import pytz
from datetime import datetime

st.set_page_config(layout="wide")
st.title("Zon")

current_dir = os.path.dirname(__file__)
asset_path = os.path.join(current_dir, "..", "assets")
discharge_csv_path = os.path.join(asset_path, 'LiPo_smooth_discharge_curve.csv')
discharge_curve = pd.read_csv(discharge_csv_path)
df = utils.get_data(discharge_curve)
utils.show_last_datapoint_caption(df)
st.caption("Geschatte zonne-instraling per m², per dag. Zelfde berekening als 'Energie vandaag' op het dashboard.")

tz = pytz.timezone('Europe/Brussels')
now_local = datetime.now(tz)

years = list(range(2025, now_local.year + 1))
default_year_index = years.index(now_local.year) if now_local.year in years else len(years) - 1

col_year, col_month = st.columns(2)
with col_year:
    selected_year = st.selectbox("Jaar", years, index=default_year_index)
with col_month:
    selected_month = st.selectbox(
        "Maand", list(range(1, 13)),
        format_func=lambda m: calendar.month_name[m],
        index=now_local.month - 1,
    )

daily = utils.compute_daily_solar_energy(df, selected_year, selected_month)
daily_present = daily[daily['has_data']].copy()

if daily_present.empty:
    st.warning("Geen data voor deze maand")
else:
    daily_present['status'] = daily_present['is_partial'].map({True: 'Vandaag (tot nu)', False: 'Volledige dag'})
    daily_present['date_str'] = pd.to_datetime(daily_present['date']).dt.strftime('%d %b')

    color_scale = alt.Scale(domain=['Volledige dag', 'Vandaag (tot nu)'], range=['#F59E0B', '#FDE68A'])

    chart = alt.Chart(daily_present).mark_bar().encode(
        x=alt.X('day:O', title='Dag', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('kwh_per_m2:Q', title='kWh/m²'),
        color=alt.Color('status:N', scale=color_scale, title=None, legend=alt.Legend(orient='bottom')),
        tooltip=[
            alt.Tooltip('date_str:N', title='Datum'),
            alt.Tooltip('kwh_per_m2:Q', title='kWh/m²', format='.2f'),
            alt.Tooltip('mj_per_m2:Q', title='MJ/m²', format='.1f'),
        ]
    ).properties(width='container', height=350)

    st.altair_chart(chart, use_container_width=True)

    if daily_present['is_partial'].any():
        st.caption("Vandaag is nog niet volledig; de staaf toont de instraling tot nu toe.")

st.subheader("Zon per maand")

light_col = 'light_intensity_avg'
work = df.dropna(subset=['received_at', light_col]).copy() if not df.empty and light_col in df.columns else pd.DataFrame()

if not work.empty:
    work['local_dt'] = work['received_at'].dt.tz_convert(tz)
    work['year'] = work['local_dt'].dt.year
    work['month'] = work['local_dt'].dt.month
    wh_totals = (work[light_col] * (5 / 60)).groupby([work['year'], work['month']]).sum()
    monthly_counts = work.groupby(['year', 'month']).size()
    table_years = sorted(work['year'].unique())
else:
    wh_totals = pd.Series(dtype=float)
    monthly_counts = pd.Series(dtype=int)
    table_years = []

months = list(range(1, 13))
month_labels = [calendar.month_abbr[m] for m in months]
current_year, current_month = now_local.year, now_local.month


def cell_kwh(year, month):
    if (year, month) in monthly_counts.index and monthly_counts.loc[(year, month)] > 0:
        wh = wh_totals.loc[(year, month)]
        return (0.0 if pd.isna(wh) else float(wh) / 1000), True
    return 0.0, False


def fmt_kwh(value, partial):
    text = f"{value:.2f}"
    return text + "*" if partial else text


table_rows, value_rows = [], []
for y in table_years:
    row = {"Jaar": y}
    value_row = {"Jaar": y}
    year_total, year_has_data, year_partial = 0.0, False, False
    for m, label in zip(months, month_labels):
        val, present = cell_kwh(y, m)
        is_current = (y == current_year and m == current_month)
        row[label] = fmt_kwh(val, is_current) if present else ""
        value_row[label] = val if present else float("nan")
        if present:
            year_has_data = True
            year_total += val
            if is_current:
                year_partial = True
    row["Totaal"] = fmt_kwh(year_total, year_partial) if year_has_data else ""
    value_row["Totaal"] = float("nan")
    table_rows.append(row)
    value_rows.append(value_row)

# "Totaal" row: per-month sum across all years
total_row = {"Jaar": "Totaal"}
grand_total, grand_has_data = 0.0, False
for m, label in zip(months, month_labels):
    month_total, month_has_data, month_partial = 0.0, False, False
    for y in table_years:
        val, present = cell_kwh(y, m)
        if present:
            month_has_data = True
            month_total += val
            if y == current_year and m == current_month:
                month_partial = True
    if month_has_data:
        total_row[label] = fmt_kwh(month_total, month_partial)
        grand_total += month_total
        grand_has_data = True
    else:
        total_row[label] = ""
total_row["Totaal"] = fmt_kwh(grand_total, current_year in table_years) if grand_has_data else ""
table_rows.append(total_row)
value_rows.append({"Jaar": "Totaal", **{label: float("nan") for label in month_labels}, "Totaal": float("nan")})

if not table_years:
    st.info("Geen live sensordata beschikbaar.")
else:
    table_df = pd.DataFrame(table_rows).set_index("Jaar")
    values_df = pd.DataFrame(value_rows).set_index("Jaar")

    # --- Color scale: sequential pale yellow (low) -> dark amber (high) --------
    LIGHT = (254, 243, 199)  # #FEF3C7
    DARK = (180, 83, 9)      # #B45309

    def lerp(c1, c2, t):
        return tuple(a + (b - a) * t for a, b in zip(c1, c2))

    def rgb_to_hex(rgb):
        return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, round(c))) for c in rgb))

    def value_to_color(v, low, high):
        if high <= low:
            frac = 0.5
        else:
            frac = (v - low) / (high - low)
            frac = max(0.0, min(1.0, frac))
        return rgb_to_hex(lerp(LIGHT, DARK, frac))

    month_cells = values_df.drop(index="Totaal", columns="Totaal")
    data_min = float(month_cells.min().min())
    data_max = float(month_cells.max().max())
    if data_max <= data_min:
        data_max = data_min + 1.0

    low, high = st.slider(
        "Kleurbereik (licht → donker), kWh/m²",
        min_value=float(np.floor(data_min)),
        max_value=float(np.ceil(data_max)),
        value=(float(np.floor(data_min)), float(np.ceil(data_max))),
        step=0.5,
    )

    def style_row(row):
        styles = []
        for col in table_df.columns:
            if row.name == "Totaal" or col == "Totaal":
                styles.append("")
                continue
            v = values_df.loc[row.name, col]
            styles.append("" if pd.isna(v) else f"background-color: {value_to_color(v, low, high)}")
        return styles

    styled = table_df.style.apply(style_row, axis=1)
    table_height = (len(table_df) + 1) * 35 + 3
    st.dataframe(styled, use_container_width=True, height=table_height)
    st.caption("Waarden in kWh/m². * = lopende maand, nog niet volledig. Schatting op basis van de lichtsensor (geen gekalibreerde pyranometer).")
