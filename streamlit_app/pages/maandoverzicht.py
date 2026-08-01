import streamlit as st
import pandas as pd
import altair as alt
import utils
import os
import pytz
import calendar
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")
st.title("Maandoverzicht")

# Rerun the page every 60s so it picks up new data as soon as the
# 3-minute get_data() cache (see utils.py) expires, without needing
# a manual refresh.
st_autorefresh(interval=60_000, key="maandoverzicht_autorefresh")

current_dir = os.path.dirname(__file__)
asset_path = os.path.join(current_dir, "..", "assets")
discharge_csv_path = os.path.join(asset_path, 'LiPo_smooth_discharge_curve.csv')
discharge_curve = pd.read_csv(discharge_csv_path)
df = utils.get_data(discharge_curve)
utils.show_last_datapoint_caption(df)
st.caption(
    "Max/Gemiddelde/Min zijn allemaal berekend op de avg-metingen (elk al een "
    "5-minuten-gemiddelde): het hoogste, het gemiddelde, en het laagste van die dag."
    " Enkel de windstoot werd berekend op basis van de maximale snelheid in het archive interval(5 min)"
)

tz = pytz.timezone('Europe/Brussels')
now_local = datetime.now(tz)

sensor_years = sorted(df['received_at'].dt.tz_convert(tz).dt.year.unique().tolist()) if not df.empty else []

# #--------------------- temperatuur per dag -----------------------------
st.subheader("Temperatuur per dag")
if not sensor_years:
    st.info("Geen live sensordata beschikbaar.")
else:
    default_year_index = sensor_years.index(now_local.year) if now_local.year in sensor_years else len(sensor_years) - 1

    col_year, col_month = st.columns(2)
    with col_year:
        selected_year = st.selectbox("Jaar", sensor_years, index=default_year_index, key="maandoverzicht_temp_year")
    with col_month:
        selected_month = st.selectbox(
            "Maand", list(range(1, 13)),
            format_func=lambda m: calendar.month_name[m],
            index=now_local.month - 1,
            key="maandoverzicht_temp_month",
        )

    daily_temp = utils.compute_daily_temperature_stats(df, selected_year, selected_month)
    daily_temp_present = daily_temp[daily_temp['has_data']].copy()

    if daily_temp_present.empty:
        st.warning("Geen data voor deze maand")
    else:
        daily_temp_present['date_str'] = pd.to_datetime(daily_temp_present['date']).dt.strftime('%d %b')

        daily_temp_melted = daily_temp_present.melt(
            id_vars=['day', 'date', 'date_str'], value_vars=['avg_max', 'avg_avg', 'avg_min'],
            var_name='Variable', value_name='Value'
        )
        series_labels = {'avg_max': 'Max', 'avg_avg': 'Gemiddelde', 'avg_min': 'Min'}
        daily_temp_melted['Variable'] = daily_temp_melted['Variable'].map(series_labels)

        temp_color_scale = alt.Scale(
            domain=['Max', 'Gemiddelde', 'Min'],
            range=['#16A34A', '#2563EB', '#DC2626']
        )

        # Same "snap to nearest day, one combined tooltip, dashed rule +
        # highlighted points" hover pattern used by the charts on Grafieken.
        base = alt.Chart(daily_temp_melted).encode(
            x=alt.X('day:O', title='Dag', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('Value:Q', title='°C'),
            color=alt.Color('Variable:N', scale=temp_color_scale, title=None,
                             legend=alt.Legend(orient='bottom'))
        )

        main_line = base.mark_line(strokeWidth=2, point=True)

        nearest = alt.selection_point(on='mouseover', nearest=True, fields=['day'],
                                      encodings=['x'], empty=False)

        selectors = alt.Chart(daily_temp_present).mark_rule().encode(
            x='day:O',
            opacity=alt.value(0),
            tooltip=[
                alt.Tooltip('date_str:N', title='Datum'),
                alt.Tooltip('avg_max:Q', title='Max', format='.1f'),
                alt.Tooltip('avg_avg:Q', title='Gemiddelde', format='.1f'),
                alt.Tooltip('avg_min:Q', title='Min', format='.1f'),
            ]
        ).add_params(nearest)

        rules = alt.Chart(daily_temp_melted).mark_rule(color='#A1A6B4', strokeDash=[4, 4]).encode(
            x='day:O',
        ).transform_filter(nearest)

        points = base.mark_point(size=30).encode(
            opacity=alt.condition(nearest, alt.value(1), alt.value(0))
        )

        temp_month_chart = alt.layer(main_line, selectors, rules, points).properties(
            width='container', height=350
        )

        st.altair_chart(temp_month_chart, use_container_width=True)

    # #--------------------- overzichtstabel -----------------------------
    st.subheader(f"Overzicht {calendar.month_name[selected_month]} {selected_year}")

    pressure_df = df.copy()
    if not pressure_df.empty:
        pressure_df["bmp_pressure_avg"] = pressure_df["bmp_pressure_avg"] / 100

    # (label, source df, column, unit, show_gem, show_min)
    rows_config = [
        ("Temperatuur", df, "sht_temperature_avg", "°C", True, True),
        ("Luchtvochtigheid", df, "sht_humidity_avg", "%", True, True),
        ("Luchtdruk", pressure_df, "bmp_pressure_avg", "hPa", True, True),
        ("Zon", df, "light_intensity_avg", "W/m²", True, False),
        ("Wind", df, "wind_speed_kmh_avg", "km/h", True, False),
        ("Windstoot", df, "wind_speed_kmh_max", "km/h", False, False),
    ]

    table_rows = []
    for label, source_df, col, unit, show_gem, show_min in rows_config:
        stats = utils.compute_monthly_stats(source_df, selected_year, selected_month, col)
        max_str = f"{stats['max']:.1f} {unit} ({stats['max_date'].strftime('%d-%m')})" if stats['max'] is not None else "-"
        min_str = (
            f"{stats['min']:.1f} {unit} ({stats['min_date'].strftime('%d-%m')})"
            if show_min and stats['min'] is not None else "-"
        )
        row = {
            "Sensor": label,
            "Gem": f"{stats['mean']:.1f} {unit}" if show_gem and stats['mean'] is not None else "-",
            "Max": max_str,
            "Min": min_str,
        }
        table_rows.append(row)

    daily_rain = utils.compute_daily_rain(df, selected_year, selected_month)
    table_rows.append({
        "Sensor": "Neerslag totaal",
        "Gem": f"{daily_rain['rain_mm'].sum():.1f} mm",
        "Max": "-",
        "Min": "-",
    })

    table_df = pd.DataFrame(table_rows).set_index("Sensor")
    table_df.index.name = None
    styled_table = table_df.style.set_table_styles([
        {'selector': 'th, td', 'props': [('border', '2px solid #d3d2ca')]},
        {'selector': 'th', 'props': [('background-color', '#ecebe3')]},
    ])
    st.table(styled_table)
