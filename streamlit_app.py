import streamlit as st
import pandas as pd
import math
from pathlib import Path


# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='PI Data Analytics 📊',
    page_icon=':chart_with_upwards_trend:', # This is an emoji shortcode. Could be a URL too.
)


# Add some spacing
''
''

'''
# Proyecto Individual :hash::two:
## _Data Analytics_: Siniestros Viales

'''

data = pd.read_excel('data/homicidios.xlsx', sheet_name='HECHOS')

st.dataframe(data, width=600)
