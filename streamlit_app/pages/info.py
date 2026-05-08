#here maybe past some links etc

import streamlit as st
import pandas as pd
import utils
import os

url = "https://docs.google.com/spreadsheets/d/1zPwrfEDDBZVqb3mwbBCHdeCaGAHnUresvGlHDXuD_qI/edit?usp=sharing"
gs_url = "https://docs.google.com/spreadsheets/d/1OW-KdOF9BSuR66o9qbumSkNck3TlXb1himbQnLeFvVE/edit?gid=0#gid=0"
st.write("The raw data of this project can be found back [in this google sheet](%s)." % gs_url)

github_url = "https://github.com/Halewijn11/wheather_station"
st.write("The source code for this project is available on [GitHub](%s)." % github_url)
# st.markdown("check out this [link](%s)" % url)
# """
# [**Vega-Lite examples.**](https://vega.github.io/vega-lite/examples/)
# """

