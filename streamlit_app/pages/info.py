#here maybe past some links etc

import streamlit as st
import pandas as pd
import utils

url = "https://docs.google.com/spreadsheets/d/1zPwrfEDDBZVqb3mwbBCHdeCaGAHnUresvGlHDXuD_qI/edit?usp=sharing"
st.write("The raw data of this project can be found back [in this google sheet](%s)." % url)
# st.markdown("check out this [link](%s)" % url)
# """
# [**Vega-Lite examples.**](https://vega.github.io/vega-lite/examples/)
# """


# #--------------------- battery status -----------------------------
col_icon, col_text, buffer = st.columns([2, 3, 20])
battery_voltage = 3.3
smooth_discharge_df = pd.read_csv('NiM_smooth_discharge_curve.csv')
battery_percentage = utils.calculate_stage_of_charge(smooth_discharge_df, 3, battery_voltage)
img_filepath = utils.get_battery_icon_filepath(battery_percentage, './assets/', flat = True)

col1,col2, buffer = st.columns([7, 20,30])
with col1:
    st.image(img_filepath, width=100) 

with col2:
    # Adjust the 'px' value (e.g., 25px) to move the text lower or higher
    st.markdown(
        f"""
        <div style="margin-top: 4px; font-size: 20px; font-weight: bold;">
            {int(battery_percentage)}%
        </div>
        """, 
        unsafe_allow_html=True
    )

    # Adding a tiny bit of padding-top with HTML to align vertically with the icon center
    # st.markdown(f"<div style='padding-top: 5px;'><b>{battery_percentage}%</b></div>", unsafe_allow_html=True)



# battery_voltage = 3.7
# smooth_discharge_df = pd.read_csv('NiM_smooth_discharge_curve.csv')
# battery_percentage = utils.calculate_stage_of_charge(smooth_discharge_df, 3, battery_voltage)
# st.subheader("Battery status")
# col1, col2 = st.columns([1, 1])
# with col1:
#     st.metric("Battery voltage", f"{battery_voltage:.2f} V")
# with col2:
#     st.metric("Battery percentage", f"{battery_percentage:.1f} %")