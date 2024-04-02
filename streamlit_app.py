import streamlit as st
import pandas as pd
import math
from pathlib import Path
from streamlit_folium import st_folium
import folium


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

# data = pd.read_excel('data/generated/data_hm.xlsx')
data = pd.read_excel('data/generated/data_hm.xlsx', engine='openpyxl')

# https://github.com/javierbengolea/pida-javier-bengolea/blob/main/data/generated/data_hm.xlsx
data.dropna(inplace=True)
data = data.rename({'pos_x': 'lon',  'pos_y': 'lat'}, axis=1)

CENTER = (-34.61963157034328,-58.441545233561044)

map = folium.Map(location=CENTER, zoom_start = 12)

for i in data.index:
    acc = (data.loc[i,'lat'], data.loc[i,'lon'])
    folium.Marker(acc).add_to(map)


st_folium(map, width=700)


