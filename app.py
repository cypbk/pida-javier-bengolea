import streamlit as st
import pandas as pd
import math
from pathlib import Path
from streamlit_folium import st_folium
import folium
from folium.plugins import BeautifyIcon
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import locale
from shapely.geometry import shape
import json

# Set locale to Spanish
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

def showPie(columna, excluir=["SD"], max=15):
  for substring in excluir:
    columna = columna[~columna.str.contains(substring)]
  
  count_values = pd.Series(columna).value_counts()
  count_2 = count_values.copy()
  
  if max > count_values.shape[0]:
    max = count_values.shape[0]
  
  if len(count_values) > max:
      count_values = count_2.iloc[:max]
      count_values['Otros'] = count_2.iloc[max:].sum()
      
  if 'Otros' not in count_values.index:
    count_values['Otros'] = 0
  
  datos = pd.DataFrame({"valor":count_values.index, "ocurrencia": count_values.values})

  plt.title(columna.name)
  plt.pie(datos["ocurrencia"], labels=datos['valor'], autopct='%1.1f%%')
  plt.show()
 
def concatenar(data_1, data_2,  axis=1):
  return pd.concat([data_1, data_2], axis=axis)

def contar_nulos(data):
  return data.isna().sum()

def mapear(columna: pd.Series, mapa={'NO': 0, 'SI':1}):
  return columna.map(mapa)

def showPiePx(columna, max=15, pref="", title="", excluir=["SD"]):
  for substring in excluir:
    columna = columna[~columna.str.contains(substring)]
  
  count_values = pd.Series(columna).value_counts()
  count_2 = count_values.copy()
  
  if max > count_values.shape[0]:
    max = count_values.shape[0]
  
  if len(count_values) > max:
      count_values = count_2.iloc[:max]
      count_values['Otros'] = count_2.iloc[max:].sum()
      
#   if 'Otros' not in count_values.index:
#     count_values['Otros'] = 0
  
  datos = pd.DataFrame({"valor":count_values.index, "ocurrencia": count_values.values})

     
  # Plot pie chart using Plotly Express
  fig = px.pie(datos, values='ocurrencia', names='valor', title=title)
  fig.update_traces(textposition='outside', textinfo='percent+label')
  return fig


class App:
    def __init__(self):
        self.app_title = 'Análisis de Accidentes Viales'
        st.set_page_config(
        page_title='PI Data Analytics 📊',
        page_icon=':chart_with_downwards_trend:', # This is an emoji shortcode. Could be a URL too.
    )
        
    def load_data(self):
        self.set_accidentes = pd.read_csv('data/generated/conjunto.csv')
        self.set_accidentes['fecha_hora'] = pd.to_datetime(self.set_accidentes['fecha_hora'])
        
        
        
    def run(self):
        self.show_title()
        self.load_data()
        st.header("Análisis de datos")  

        data = self.set_accidentes.query("data_geo").copy()
        data['cruce_st'] = data['es_cruce'].map({False:'Calle', True:'Esquina'})
        

        col1, col2, col3, col4 = st.columns([.2,.2,.2,.4])
        
        # tab1, tab2 = st.tabs(["🔍 Filtros", "🗃 Datos"])

        # with tab1:
        with col1:
          comunas_numeric = data['comuna'].apply(pd.to_numeric, errors='coerce').dropna()
          comunas = pd.Series(comunas_numeric.unique()).sort_values().astype(int).astype(str)

          comuna = st.selectbox("Comuna", comunas)
        with col2:
          fatalidad = st.selectbox('Fatalidad', ['FATAL', 'NO FATAL'])
        with col3:
          intervalo_select = st.selectbox('Intervalo', ['Anual', 'Semestral', 'Mensual'])
        with col4:
          min_year, max_year = st.slider('Elegir años entre',
                              min_value=data['fecha_hora'].dt.to_period('Y').min().year,
                              max_value=data['fecha_hora'].dt.to_period('Y').max().year,
                              value=(data['fecha_hora'].dt.to_period('Y').min().year, data['fecha_hora'].dt.to_period('Y').max().year))

        if fatalidad == 'FATAL':
            fatalidad = ['FATAL']
        if fatalidad == 'NO FATAL':
            fatalidad = ['GRAVE', 'NO_GRAVE']

        if comuna != 'Todas':
            data = data.query(f"gravedad in ['GRAVE','FATAL'] and comuna == ['{comuna}']")
        else:
            data = data.query(f"gravedad in ['GRAVE','FATAL']")

        tiempo_container = st.container()
        
        st.markdown(
        """
        <div style='border: 1px solid lightgray; border-radius: 5px; padding: 10px; background-color: lightgray;'>
        """,  unsafe_allow_html=True
        )
        
        with tiempo_container:
          tab_tiempo_gr, tab_tiempo_da = st.tabs(['Gráfico', 'Datos'])

          with tab_tiempo_gr:
            grouped_data = self.set_accidentes.copy()
            grouped_data['fecha_hora'] = pd.to_datetime(grouped_data['fecha_hora'])
            grouped_data['anio'] = grouped_data['fecha_hora'].dt.year
            grouped_data['mes'] = grouped_data['fecha_hora'].dt.month
            grouped_data['mes'] = pd.to_datetime(grouped_data['anio'].astype(str)+'-'+grouped_data['mes'].astype(str)+"-1")
            grouped_data['dia'] = grouped_data['fecha_hora'].dt.day
            grouped_data['semestre'] = ((grouped_data['fecha_hora'].dt.month-1)//6)+1
            grouped_data['semestre'] = pd.to_datetime(grouped_data['anio'].astype(str)+'-'+(grouped_data['semestre']*6).astype(str)+"-1")
            intervalo_dict = dict(zip(['Anual', 'Semestral', 'Mensual'], ['anio', 'semestre', 'mes']))

            grouped_data = grouped_data.query(f"anio >= {min_year} and anio <= {max_year}")
            intervalo = intervalo_dict[intervalo_select]
            grouped_data = grouped_data.query(f"gravedad in {fatalidad}").groupby([intervalo])['n_victimas'].count().reset_index()

            grouped_data.index = grouped_data[intervalo]
            grouped_data.rename({'n_victimas': 'n_accidentes'}, axis=1, inplace=True)
            grouped_data.drop(intervalo, axis=1,inplace=True)
            grouped_data.reset_index(inplace=True)

            grouped_data['diff'] = grouped_data['n_accidentes'].pct_change()*100
            grouped_data['diff'].fillna(0, inplace=True)

            grouped_data['text'] = grouped_data['diff'].apply(
                lambda x: f"{'{:.2f}'.format(x)}" if x > 0 else f"{round(x,2)}")

            grouped_data['text'] = grouped_data['text'].apply(lambda st: (str(st) + '% ↓') if float(st) < 0.0 else ' = 'if float(st) == 0.0 else(str(st) + '% ↑'))


            fig = px.bar(grouped_data, x=intervalo, y='n_accidentes',
                title='Accidentes el tiempo',
                color='n_accidentes',
                color_continuous_scale=["lightgreen", "yellow", "red"],
                        text='text',
                labels={'fecha_hora': 'Fecha', 'n_accidentes': 'Nro Accidentes'})

            fig.update_xaxes(ticks="inside", ticklabelmode='period')
            fig.update_traces(textposition='outside', textfont=dict(size=14, color='black', family='Arial'))
            diff_values = grouped_data['diff'].values

            def inv(n):
                if n == ' = ':
                    return 0
                if n[-3:] in ['% ↑', '% ↓']:
                    return n[0:-3]

                return n

            for trace in fig.data:
                trace.update(
                    textfont_color=['green' if float(inv(text)) < 0.0 else 'red' if float(inv(text)) > 0.0 else 'white' for text in
                                    trace.text])
            
            st.plotly_chart(fig, width=400, height=30)

          with tab_tiempo_da:
            st.dataframe(grouped_data)
        st.markdown("</div>", unsafe_allow_html=True)
        tab_dias_gr, tab_dias_da = st.tabs(['Gráfico', 'Datos'])
        
        with tab_dias_gr:
          grouped_data = self.set_accidentes.copy().query(f"gravedad == {fatalidad}")      
          grouped_data_dias = grouped_data.groupby(grouped_data['fecha_hora'].dt.dayofweek)['n_victimas'].count().reset_index()
          dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
          dias_dict = {0: '01-Lunes', 1: '02-Martes', 2: '03-Miércoles', 3: '04-Jueves', 4: '05-Viernes', 5: '06-Sábado', 6: '07-Domingo'}
          grouped_data_dias['dia_semana'] = grouped_data_dias['fecha_hora'].map(dias_dict)
          grouped_data_dias.drop(columns=['fecha_hora'], inplace=True)
          grouped_data_dias.columns = ['nro_accidentes', 'dia_semana']
          grouped_data_dias = grouped_data_dias.sort_values(by='nro_accidentes', ascending=True)
      


          # Create a stacked bar plot using Plotly Express
          fig = px.bar(grouped_data_dias, x='nro_accidentes', y='dia_semana', 
                      title='Accidentes por Día de la Semana',
                      color='nro_accidentes',
                      color_continuous_scale=["#A1FFA1", "yellow", "red"],
                      labels={'dia_semana': 'Dia de la Semana', 'nro_accidentes': 'Accidentes'}
                      #  ,              category_orders={'Day of Week': day_names}
                      )
          fig.update_xaxes(ticks="outside")
          
          fig.update_layout(width=500, height=300)
          st.plotly_chart(fig)

        with tab_dias_da:
          st.dataframe(grouped_data_dias)
        
        gd_hora = grouped_data.groupby(grouped_data['fecha_hora'].dt.hour)['n_victimas'].count().reset_index()


        gd_hora.columns = ['hora', 'nro_accidentes']
        gd_hora['hora'] = gd_hora['hora'].astype(str)+" hs."

        # # Sort the data in descending order
        gd_hora = gd_hora.sort_values(by='nro_accidentes', ascending=True)
 

        # Create a stacked bar plot using Plotly Express
        fig = px.bar(gd_hora, x='nro_accidentes', y='hora', 
                    title='Accidentes por Hora del Día',
                    color='nro_accidentes',
                    color_continuous_scale=["#A1FFA1", "yellow", "red"],
                    labels={'hora': 'Hora del día', 'nro_accidentes': 'Accidentes'},
                    orientation='h'
                     ,              category_orders={'Hora del día': 'hora'}
                    )

        # Show the plot
        st.plotly_chart(fig)
        
        cross_data = self.set_accidentes.copy().query(f"gravedad == {fatalidad}")
        cross_data['hora'] = cross_data['fecha_hora'].dt.hour
        cross_data['dia_semana'] = cross_data['fecha_hora'].dt.day_of_week
        cross_data['dia_semana'] = cross_data['dia_semana'].map(dias_dict)
        cross_data['hora'] = cross_data['hora']//6
        cuartos = {0: '00 a 06 hs',1: '06 a 12 hs',2: '12 a 18 hs',3: '18 a 00 hs'}
        cross_data['hora'] = cross_data['hora'].map(cuartos)
        
        cross_tab = pd.crosstab(cross_data['hora'], cross_data['dia_semana'])

# Display the cross-tabulation in a DataFrame using Streamlit
        # st.dataframe(cross_tab)
        # st.dataframe(cross_tab)
        
                # Create a heatmap using Seaborn

        # Reset index to make 'hour' a column
        cross_tab = cross_tab.reset_index()
        cross_tab.index = cross_tab['hora']
        cross_tab.drop('hora', axis=1, inplace=True)

        st.dataframe(cross_tab)

        # Create a heatmap using Plotly
        fig = px.imshow(cross_tab, 
                        labels=dict(x="Day of the Week", y="Hora", color="Count"),
                        x=cross_tab.columns.str[3:],
                        y=cross_tab.index,
                        color_continuous_scale=["lightgreen", "yellow", "red"])

        # Customize layout
        fig.update_layout(title='Cross-tabulation of Hour and Day of the Week',
                        xaxis_title='Dia de la semana',
                        yaxis_title='Cuarto')

        # Display the heatmap
        st.plotly_chart(fig)
        
        with st.expander("Ver GeoGráfico"):
          mapa_icono = {'SD': 'times',
          'MOTO': 'motorcycle',
          'PEATON': 'male',
          'CICLISTA': 'bicycle',
          'AUTO': 'car',
          'TRANSPORTE PUBLICO': 'bus',
          'CAMIONETA': 'car',
          'TAXI': 'taxi',
          'MOVIL': 'id-badge',
          'CAMION': 'truck',
          'MIXTO': 'times',
          'BICICLETA': 'bicycle',
          'MONOPATIN': 'times',
          'OTRO': 'times',
          'UTILITARIO': 'truck',
          'CARGAS': 'truck',
          'PASAJEROS': 'male',
          'OBJETO FIJO': 'times',
          'PEATON_MOTO': 'male'}



        
          CENTER = (data['latitud'].mean(skipna=True),data['longitud'].mean(skipna=True))

          mapa = folium.Map(CENTER, zoom_start = 12)
          
          dic_color = {'GRAVE': '#ffb777', 'FATAL':'red'}

          for i in data.index:
              registro = data.loc[i,:]
              color = dic_color[registro.loc['gravedad']]
              
              acc = (registro['latitud'], registro['longitud'])
              folium.Marker(location = acc, 

                            icon=BeautifyIcon(icon=mapa_icono[registro['victima']],background_color=color, fill_opacity=0, text_color='black'),
                            popup=f"{registro['victima']}<br>{registro['cruce_st']}").add_to(mapa)
          
          # tab_geo_grafico, tab_geo_datos = st.tabs(['Grafico', 'Datos'])
          # with tab_geo_grafico:
          st_folium(mapa, width=500, height=500)
          # with tab_geo_datos:
          # st.dataframe(data)
        

        
        mymap = folium.Map(location=[CENTER[0], CENTER[1]], zoom_start=10)
        radius = 1000  # Adjust as needed

        
        folium.Circle(
        location=CENTER,
        radius=radius,
        color='blue',
        fill=True,
        fill_color='blue',
        fill_opacity=0.3
    ).add_to(mymap)
        
        st_folium(mymap)

        
        def get_feature_centroid(feature):
          """Calculate the centroid of a GeoJSON feature using Shapely."""
          geometry = feature.get('geometry')
          if geometry:
              shapely_geometry = shape(geometry)
              return shapely_geometry.centroid
          else:
              return None

        # Load the GeoJSON file
        geojson_file = "comunas.geojson"
        
        with open(geojson_file) as f:
          geojson_data = json.load(f)


        # Create a folium map
        m = folium.Map(location=CENTER, zoom_start=12)

        # Add the GeoJSON data to the map
        folium.GeoJson(geojson_data).add_to(m)                
        
       
        st_folium(m)

        geojson_file = "comunas.geojson"

        # Load the GeoJSON data
        with open(geojson_file) as f:
            geojson_data = json.load(f)

        # Create a folium map centered at a default location
        m = folium.Map(location=[ -34.570327148316984 ,-58.379518280482237], zoom_start=10)

        # Define a list of "COMUNA" names and their associated numerical values
        comunas_data = {
    1: 90,
    2: 25,
    3: 45,
    4: 76,
    5: 22,
    6: 21,
    7: 60,
    8: 65,
    9: 73,
    10: 29,
    11: 32,
    12: 37,
    13: 40,
    14: 35,
    15: 44}
        
        # st.write(type(self.set_accidentes.comuna))

        # Create a Choropleth layer
        folium.Choropleth(
            geo_data=geojson_data,
            name='choropleth',
            data=comunas_data,
            columns=['COMUNA', 'Value'],
            key_on='feature.properties.COMUNAS',
            fill_color='YlOrRd',  # You can adjust the colormap here
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name='Value'
        ).add_to(m)

        # Add Layer control to toggle the visibility of layers
        folium.LayerControl().add_to(m)

        # Display the map using Streamlit
        st_folium(m)

    def show_title(self):
        st.title(self.app_title)

app = App()
app.run()

import streamlit as st
import folium
import json

def main():
    st.title("Choropleth Map with Folium")

    # Load GeoJSON file containing the boundaries of each "COMUNA"


if __name__ == "__main__":
    main()
