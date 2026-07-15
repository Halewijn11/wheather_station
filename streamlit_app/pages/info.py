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
- Span ≤ 48u → raw data
- 48u < span ≤ 7d → resample 30min
- 7d < span ≤ 30d → resample 1h
- span > 30d → resample 3h
""")

# st.markdown("check out this [link](%s)" % url)
# st.markdown("check out this [link](%s)" % url)
# """
# [**Vega-Lite examples.**](https://vega.github.io/vega-lite/examples/)
# """

