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
st.write("Sample tijd is telkens 5 seconden,dus om 5 seconden meting van bv temp, de min/max/avg worden dan berekend over alle 5 seconden intervallen op deze 5 min.")
st.write("Voor de wind is dit wat verschillend: aantal pulsen wordt geteld gedurende 5s, na 5 min wordt dan het 5s met max en min interval als de max en min weergegeven.")
st.write("Voor de wind wordt de gemiddelde snelheid berekend uit het totaal aantal pulsen in 5 min interval.")

st.subheader("Opstarten local")
st.code(
    'cd "C:\\Users\\u0045990\\Documents\\PlatformIO\\Projects\\wheather_station\\streamlit_app"\n'
    '& "C:\\Users\\u0045990\\AppData\\Local\\anaconda3\\Scripts\\streamlit.exe" run streamlit_app.py',
    language="powershell"
)

st.subheader("Resampling")
st.markdown("""
Welke resolutie getoond wordt hangt af van de span van de geselecteerde periode:
- Span ≤ 48u → raw data (geen resampling, elke meting apart)
- 48u < span ≤ 7d → resample naar 30min-interval
- 7d < span ≤ 30d → resample naar 1u-interval
- span > 30d → resample naar 3u-interval

Hoe een datapunt in een grafiek berekend wordt:
- De meeste kolommen (temperatuur, druk, licht, windsnelheid, ...) worden **gemiddeld** (mean) over alle metingen in het archiefinterval.
- `rain_mm` en `wind_pulses_total` worden **opgeteld** (sum) i.p.v. gemiddeld, want dat zijn hoeveelheden per interval, geen momentopnames.
- De cumulatieve regen wordt opnieuw gereset elke lokale (Europe/Brussels) middernacht.
- Helderheidsindex = gemeten energie tot nu / TOA-instraling tot nu (numeriek geïntegreerd sinds zonsopgang), als %
- TOA : Spencer (1971)-benaderingen voor declinatie/excentriciteit        
            
""")

st.subheader("windroos")
st.markdown("""
data worden in windroos pas opgenomen vanaf wind_max 3 km/h en dit voor beide rozen
""")

# st.markdown("check out this [link](%s)" % url)
# st.markdown("check out this [link](%s)" % url)
# """
# [**Vega-Lite examples.**](https://vega.github.io/vega-lite/examples/)
# """

