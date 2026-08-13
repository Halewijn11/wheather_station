#here maybe past some links etc

import streamlit as st
import pandas as pd
import utils
import os

url = "https://docs.google.com/spreadsheets/d/1yW0NiWeuWjEp08eymjFQ62CqKhSegNa_FXcgl68Kf4Q/edit?gid=0#gid=0"
gs_url = "https://docs.google.com/spreadsheets/d/1yW0NiWeuWjEp08eymjFQ62CqKhSegNa_FXcgl68Kf4Q/edit?gid=0#gid=0"
st.write("The raw data of this project can be found back [in this google sheet](%s)." % gs_url)

github_url = "https://github.com/Halewijn11/wheather_station"
st.write("The source code for this project is available on [GitHub](%s)." % github_url)

st.subheader("Opstarten local")
st.code(
    'cd "C:\\Users\\u0045990\\Documents\\PlatformIO\\Projects\\wheather_station\\streamlit_app"\n'
    '& "C:\\Users\\u0045990\\AppData\\Local\\anaconda3\\Scripts\\streamlit.exe" run streamlit_app.py',
    language="powershell"
)

st.subheader("(Re)-sampling")
st.markdown("""
- Sample tijd is telkens 5 seconden, dus om 5 seconden meting van bv temp
- de min/max/avg worden dan berekend over alle 5 seconden in het archief interval (5 min).

Welke resolutie in grafiek wordt getoond hangt af van de span van de geselecteerde periode:
- Span ≤ 48u → raw data (geen resampling, elke meting apart)
- 48u < span ≤ 7d → resample naar 30min-interval
- 7d < span ≤ 30d → resample naar 1u-interval
- span > 30d → resample naar 3u-interval

Hoe een datapunt in een grafiek berekend wordt:
- De meeste kolommen (temperatuur, druk, licht, windsnelheid, ...) worden **gemiddeld** (mean) over alle metingen in het archiefinterval.
- `rain_mm` en `wind_pulses_total` worden **opgeteld** (sum) i.p.v. gemiddeld, want dat zijn hoeveelheden per interval, geen momentopnames.
- Alle grfaieken geven de gemiddelde waarde weer van het archive interval, dus gemiddelde over 5 min. ENkel bij de Temp kan je min en max laten tonen
- De cumulatieve regen wordt opnieuw gereset elke lokale (Europe/Brussels) middernacht.
- Helderheidsindex = gemeten energie tot nu / TOA-instraling tot nu (numeriek geïntegreerd sinds zonsopgang), als %
- TOA : Spencer (1971)-benaderingen voor declinatie/excentriciteit
- Heat Index (Grafieken-tab) : NWS-formule (Steadman 1979, Rothfusz-regressie 1990, herzien door NOAA in 1998), berekend uit sht_temperature_avg + sht_humidity_avg. Onder ~26.7°C wordt de eenvoudige middelingsformule gebruikt i.p.v. de volledige regressie (niet betekenisvol/geldig bij lagere temperaturen); erboven de volledige regressie met de officiële correctietermen voor lage (<13%) en hoge (>85%) vochtigheid. Berekening gebeurt intern in °F, weergave in °C.
- Dauwpunt wordt bereken met de formule van Magnus-Tetens.
""")

st.subheader("windroos")
st.markdown("""
data worden in windroos pas opgenomen vanaf wind_max 3 km/h en dit voor beide rozen
""")

st.subheader("Kalibraties")
st.caption(
    "Log van sensorkalibraties, handmatig bijgehouden in het 'Kalibraties'-tabblad "
    "van de Google Sheet (Datum, Kolom, Offset of Factor, Notitie). Per kolom wordt "
    "ofwel Offset (optelling) ofwel Factor (vermenigvuldiging) gebruikt, nooit beide."
)
calibration_log = utils.get_calibration_log()
if calibration_log.empty:
    st.caption("Nog geen kalibraties gelogd.")
else:
    st.dataframe(calibration_log, use_container_width=True, hide_index=True)

# st.markdown("check out this [link](%s)" % url)
# st.markdown("check out this [link](%s)" % url)
# """
# [**Vega-Lite examples.**](https://vega.github.io/vega-lite/examples/)
# """

