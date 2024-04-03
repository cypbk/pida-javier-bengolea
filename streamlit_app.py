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


# st_folium(map, width=700)

'''
## Análisis por Tiempo
'''

import plotly.express as px


# Group data by month, summing 'n_victimas'
grouped_data = data.groupby(data['fecha_hora'])['n_victimas'].count().reset_index()

grouped_data.index = grouped_data['fecha_hora']
grouped_data.rename({'n_victimas': 'n_accidentes'}, axis=1, inplace=True)
grouped_data.drop('fecha_hora', axis=1,inplace=True)

# Create a Streamlit selectbox for selecting the time interval
intervalo_select = st.selectbox('Intervalo', ['Anual', 'Semestral', 'Cuatrimestral', 'Trimestral', 'Bimestral', 'Mensual', 'Quincenal', 'Semanal'])

intervalo_dict = dict(zip(['Anual', 'Semestral', 'Cuatrimestral', 'Trimestral', 'Bimestral', 'Mensual', 'Quincenal', 'Semanal'], ['Y', '6M', '4M', '3M', '2M', 'M', '2W', 'W']))

# st.write(intervalo_dict[intervalo_select])



# st.dataframe(grouped_data.resample("6M").sum())


grouped_data = grouped_data.resample(intervalo_dict[intervalo_select]).count()

# st.dataframe(grouped_data)

# Convert Period objects to strings
grouped_data['fecha_hora'] = grouped_data.index.astype(str)

min_year, max_year = st.slider('Select Year Range', 
                               min_value=data['fecha_hora'].dt.to_period('Y').min().year, 
                               max_value=data['fecha_hora'].dt.to_period('Y').max().year, 
                               value=(data['fecha_hora'].dt.to_period('Y').min().year, data['fecha_hora'].dt.to_period('Y').max().year+1))

# min_year = 2016
# max_year = 2022

datos_filtrados_fecha = grouped_data[(grouped_data['fecha_hora'] >= str(min_year)) & (grouped_data['fecha_hora'] <= str(max_year))]

# Create a line plot using Plotly Express
fig = px.bar(datos_filtrados_fecha, x='fecha_hora', y='n_accidentes', 
              title='Accidentes el tiempo',
              color='n_accidentes', 
              color_continuous_scale=["lightgreen", "yellow", "red"],
              labels={'fecha_hora': 'Fecha', 'n_accidentes': 'Nro Accidentes'})

# # Show the plot
# fig.show()

st.plotly_chart(fig)

# st.sidebar.title("Navigation")
# selection = st.sidebar.radio('Go to', ['Home', 'Page 1', 'Page 2'])


data_by_day = data.groupby(data['fecha_hora'].dt.day_of_week)['n_victimas'].count().reset_index()

grouped_data = data.groupby(data['fecha_hora'].dt.dayofweek)['n_victimas'].count().reset_index()

# Define day names
day_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

# Map day of week to day name
grouped_data['day_of_week'] = grouped_data['fecha_hora'].map(lambda x: day_names[x])

# Drop the 'fecha_hora' column
grouped_data.drop(columns=['fecha_hora'], inplace=True)

# Rename the columns
grouped_data.columns = ['Day of Week', 'Number of Victims']

# Sort the data in descending order
grouped_data = grouped_data.sort_values(by='Day of Week', ascending=True)

# Create a stacked bar plot using Plotly Express
fig = px.bar(grouped_data, x='Day of Week', y='Number of Victims', 
             title='Number of Victims by Day of Week',
             color='Day of Week',
             color_continuous_scale=["#A1FFA1", "yellow", "red"],
             labels={'Number of Victims': 'Number of Victims'},
             category_orders={'Day of Week': day_names})

# Show the plot
st.plotly_chart(fig)

st.dataframe(grouped_data)