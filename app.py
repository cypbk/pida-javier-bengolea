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
import plotly.graph_objs as go
import numpy as np

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
        page_icon=':chart_with_downwards_trend:', 
        layout="wide"
    )
        
    def load_data(self):
        self.set_accidentes = pd.read_csv('data/generated/conjunto.csv')
        self.set_accidentes['fecha_hora'] = pd.to_datetime(self.set_accidentes['fecha_hora'])
        
        
    def run(self):
        class KPI():
          def __init__(self,nombre, descripcion, current_value, reference_value, increasing_method=False):
            self.nombre = nombre
            self.descripcion = descripcion
            self.reference_value = reference_value
            self.current_value = current_value
            self.increasing_method = increasing_method
            self.figure = go.Figure()
            self.intervalo = 'semestre'
            self.porc_objetivo = .1
            self.valor_objetivo = 1
            self.color = 'red'
            # self.compute_delta_percentage()

          def compute_delta_percentage(self):
            self.delta_percentage = ((self.current_value - self.reference_value) / self.reference_value) * 100
            self.increasing = np.sign(self.delta_percentage)
            self.color = 'red' if self.increasing == 1 else 'green'

          
          def get_figure(self):
            self.compute_delta_percentage()
            self.figure.add_trace(go.Indicator(
              mode="number+delta",
              value=self.current_value,
              title={"text": self.nombre, 'font':{'color':'black', 'size':22}},  # Description at the bottom of the KPI
              number={'prefix': "", 'font': {'color': self.color},'valueformat': '.3f'},  # Darker green text color
              delta={'position': "bottom", 'reference': self.reference_value, 'relative': True, 
              'font': {'color': self.color}, 'increasing': {'color': "red"},'decreasing': {'color': "green"},
              'valueformat': '.2%'
              },  # Darker green delta color
              domain={'x': [0.0, 1], 'y': [0, 1]},
              # domain = {'row': 0, 'column': 0}
            ))
            self.figure.add_shape(type="rect",
              x0=0, y0=-0.02, x1=1, y1=0.05,  # Adjust y0 and y1 to position the line
              line=dict(color=self.color, width=1.5),
              fillcolor=self.color,  # Change to "darkgreen" for a darker shade
              opacity=1,
              xref="paper", yref="paper"
              )
            self.figure.update_layout(margin=dict(t=10, b=10,l=10,r=10), paper_bgcolor="white", plot_bgcolor="white", showlegend=False, height=200, width=200)
            return self.figure


        # self.show_title()
        self.load_data()
        st.markdown('''<style>div.block-container{padding-top: 1rem}        </style>''', unsafe_allow_html=True)
        st.header(" :bar_chart: Análisis de Accidentes Viales")  

        data = self.set_accidentes.query("data_geo").copy()
        data['cruce_st'] = data['es_cruce'].map({False:'Calle', True:'Esquina'})

        with st.sidebar:
          st.title("Consultora SigVa")
          
          comunas_numeric = self.set_accidentes.query('data_geo')['comuna'].apply(pd.to_numeric, errors='coerce').dropna()
          comunas = pd.Series(comunas_numeric.unique()).sort_values().astype(int).astype(str)
          comuna = st.selectbox("Comuna", comunas)

          fatalidad = st.selectbox('Fatalidad', ['FATAL', 'NO FATAL'])

          intervalo_select = st.selectbox('Intervalo', ['Anual', 'Semestral', 'Mensual'], index=1)

          min_year, max_year = st.slider('Elegir años entre',
                              min_value=data['fecha_hora'].dt.to_period('Y').min().year,
                              max_value=data['fecha_hora'].dt.to_period('Y').max().year,
                              value=(data['fecha_hora'].dt.to_period('Y').min().year, data['fecha_hora'].dt.to_period('Y').max().year))


        
        container_KPI = st.container()

        with container_KPI:

          df_pob_comunas = pd.read_csv('data/generated/data_comunas_pob.csv')
          # df_pob_comunas['comuna'] = df_pob_comunas['comuna'].astype(int)
          poblacion = df_pob_comunas['poblacion'].sum()

          data = self.set_accidentes.copy()
          # data = data[~data['comuna'].isin(['SD', 'No Especificada'])].query("gravedad == 'FATAL'")
          data = data.query("gravedad == 'FATAL'")
          # data['comuna'] = data['comuna'].astype(int)
          # data_merged = pd.merge(df_pob_comunas, data, left_on='comuna', right_on='comuna') 
          data_merged = data
          data_merged['anio'] = data_merged['fecha_hora'].dt.year
          data_merged['mes'] = data_merged['fecha_hora'].dt.month
          data_merged['mes'] = pd.to_datetime(data_merged['anio'].astype(str)+'-'+data_merged['mes'].astype(str)+"-1")
          data_merged['dia'] = data_merged['fecha_hora'].dt.day
          data_merged['semestre'] = ((data_merged['fecha_hora'].dt.month-1)//6)+1
          data_merged['semestre'] = pd.to_datetime(data_merged['anio'].astype(str)+'-'+(data_merged['semestre']*6).astype(str)+"-1")
          summary_df = data_merged.groupby('semestre').agg({'n_victimas': 'sum'}).reset_index()
          summary_df['n_victimas'] = summary_df['n_victimas'].astype(float)
          
          summary_df['tasa'] = (summary_df['n_victimas']/poblacion) * 100000.0
          summary_df['tasa_deseada'] = summary_df['tasa'].shift(1) * .9
          summary_df['diff'] = summary_df['tasa'].pct_change()*100

          # st.dataframe(summary_df)
          # st.plotly_chart(px.bar(summary_df, x='semestre', y='diff'))

          summary_cl = data_merged.query("victima == 'MOTO'").groupby('anio').agg({'n_victimas': 'sum'}).reset_index()
          summary_cl['tasa'] = (summary_cl['n_victimas']/poblacion) * 100000.0
          summary_cl['tasa_deseada'] = summary_cl['tasa'].shift(1) * .93
          summary_cl['diff'] = summary_cl['tasa'].pct_change()*100
          # st.dataframe(summary_cl)          
          # st.plotly_chart(px.bar(summary_cl, x='anio', y='diff'))

          dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
          dias_dict = {0: '01-Lunes', 1: '02-Martes', 2: '03-Miércoles', 3: '04-Jueves', 4: '05-Viernes', 5: '06-Sábado', 6: '07-Domingo'}

          data_3_k = self.set_accidentes.copy()
          data_3_k = data_3_k.query("gravedad == 'FATAL'")
          data_3_k['anio'] = data_3_k['fecha_hora'].dt.year
          data_3_k['mes'] = data_3_k['fecha_hora'].dt.month
          data_3_k['mes'] = pd.to_datetime(data_3_k['anio'].astype(str)+'-'+data_3_k['mes'].astype(str)+"-1")
          data_3_k['dia'] = data_3_k['fecha_hora'].dt.day
          data_3_k['dia_semana'] = data_3_k['fecha_hora'].dt.day_of_week
          data_3_k['dia_semana_st'] = data_3_k['fecha_hora'].dt.day_of_week.map(dias_dict)
          data_3_k['dia_semana_st'] = data_3_k['dia_semana_st'].str[3:]
          # st.dataframe(data_3_k)     
          data_3_k['hora'] = data_3_k['fecha_hora'].dt.hour
          data_3_k['semestre'] = ((data_3_k['fecha_hora'].dt.month-1)//6)+1
          data_3_k['semestre'] = pd.to_datetime(data_3_k['anio'].astype(str)+'-'+(data_3_k['semestre']*6).astype(str)+"-1")
          data_3_k = data_3_k.query("dia_semana_st in ['Sábado', 'Domingo'] and hora in [6,7,8,9,10,11,12]")
          # filtro1 = (data_3_k['dia_semana_st'] == 'Sábado') & data_3_k['hora'].isin([6, 7, 8, 9, 10, 11, 12])
          # filtro2 = (data_3_k['dia_semana_st'] == 'Domingo') & data_3_k['hora'].isin([0, 1, 2, 3, 4, 5])
          # data_3_k = data_3_k[filtro1 | filtro2]
          # data_3_k = data_3_k.query("victima = 'PEATON' and es_cruce")
          data_3_k = data_3_k.groupby('semestre').agg({'n_victimas': 'sum'}).reset_index()
          data_3_k['tasa'] = (data_3_k['n_victimas']/poblacion) * 100000.0
          data_3_k['tasa_deseada'] = data_3_k['tasa'].shift(1) * .9
          data_3_k['diff'] = data_3_k['tasa'].pct_change()*100

          
          # st.dataframe(data_3_k)          
          # st.plotly_chart(px.bar(data_3_k, x='semestre', y='diff'))

          kp1_tasa_homicidios = KPI(nombre="Tasa de Homicidios", descripcion="Objetivo reducción 10% intersemestre", reference_value=summary_df.iloc[-1]['tasa_deseada'], current_value=summary_df.iloc[-1]['tasa'])
          kp1_tasa_hm_moto = KPI(nombre="Tasa de Homicidios Motociclistas", descripcion="Objetivo reducción 7% interanual", reference_value=summary_cl.iloc[-1]['tasa_deseada'], current_value=summary_cl.iloc[-1]['tasa'])
          kp1_tasa_hm_horas_max = KPI(nombre="Tasa de Homicidios Horas Max", descripcion="Objetivo reducción 10% intersemestre", reference_value=data_3_k.iloc[-1]['tasa_deseada'], current_value=data_3_k.iloc[-1]['tasa'])

          kpi_cl1, kpi_cl2, kpi_cl3 = st.columns([.33,.33,.33])

          with kpi_cl1:
            st.plotly_chart(kp1_tasa_homicidios.get_figure(), use_container_width=True, height=150)
            with st.expander('Indicador'):
              st.write("Indicador 1")
          with kpi_cl2:
            st.plotly_chart(kp1_tasa_hm_moto.get_figure(), use_container_width=True)
          with kpi_cl3:
            st.plotly_chart(kp1_tasa_hm_horas_max.get_figure(), use_container_width=True)

        col1, col2, col3, col4 = st.columns([.2,.2,.2,.4])
        
        # tab1, tab2 = st.tabs(["🔍 Filtros", "🗃 Datos"])

        # with tab1:
        with col1:
          # comunas_numeric = data['comuna'].apply(pd.to_numeric, errors='coerce').dropna()
          # comunas = pd.Series(comunas_numeric.unique()).sort_values().astype(int).astype(str)

          # comuna = st.selectbox("Comuna", comunas)
          pass
        with col2:
          pass
        with col3:
          pass
          # intervalo_select = st.selectbox('Intervalo', ['Anual', 'Semestral', 'Mensual'])
        with col4:
          pass
          # min_year, max_year = st.slider('Elegir años entre',
          #                     min_value=data['fecha_hora'].dt.to_period('Y').min().year,
          #                     max_value=data['fecha_hora'].dt.to_period('Y').max().year,
          #                     value=(data['fecha_hora'].dt.to_period('Y').min().year, data['fecha_hora'].dt.to_period('Y').max().year))

        if fatalidad == 'FATAL':
            fatalidad = ['FATAL']
        if fatalidad == 'NO FATAL':
            fatalidad = ['GRAVE', 'NO_GRAVE']

        if comuna != 'Todas':
            data = data.query(f"gravedad in ['GRAVE','FATAL'] and comuna == ['{comuna}']")
        else:
            data = data.query(f"gravedad in ['GRAVE','FATAL']")

        tiempo_container = st.container()
               
        with tiempo_container:
          tab_tiempo_gr, tab_kpi_1, tab_kpi_2, tab_kpi_3 = st.tabs(['Histórico', 'Tasa Homicidios', 'Tasa Homicidios Motociclistas', 'Tasa Homicidios Horas Máximas'])

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
            grouped_data = grouped_data.query(f"gravedad in {fatalidad}").groupby([intervalo])['n_victimas'].sum().reset_index()

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
                color='n_accidentes',
                color_continuous_scale=["lightgreen", "yellow", "red"],
                        text='text',
                labels={'fecha_hora': 'Fecha', 'n_accidentes': 'Nro Accidentes', 'anio': 'Año', 'semestre':'Semestre', 'mes':'Mes'},
                template='seaborn')

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

            fig.update_layout(paper_bgcolor="#fafafa")
            
            padding = 0.1
            fig.update_layout(yaxis=dict(range=[0, grouped_data['n_accidentes'].max() * (1 + padding)]),showlegend=False)
            
            #col_gr_1, col_gr_2 = st.columns((2))
            
            #with col_gr_1:
            st.subheader("Histórico de Accidentes ")
            st.plotly_chart(fig, use_container_width=True, height=30)
            #with col_gr_2:
            #  st.plotly_chart(showPiePx(self.set_accidentes.query(f'gravedad == {fatalidad} and fecha_hora.dt.year <= {max_year}')['victima']), use_container_width=True, height=30)
          with tab_kpi_1:
            st.subheader('Tasa Homicidios')
            summary_df['text'] = summary_df['tasa'].apply(
                lambda x: f"{'{:.2f}'.format(x)}" if x > 0 else f"{round(x,2)}")

            summary_df['text'] = summary_df['text'].apply(lambda st: (str(st) + '% ↓') if float(st) < 0.0 else ' = 'if float(st) == 0.0 else(str(st) + '% ↑'))
            fig = px.bar(summary_df, x=intervalo, y='tasa',
                color='tasa',
                text='tasa',
                color_continuous_scale=["lightgreen", "yellow", "red"],
                        
                labels={'fecha_hora': 'Fecha', 'tasa': 'Tasa', 'anio': 'Año', 'semestre':'Semestre', 'mes':'Mes'},
                template='seaborn')

            fig.update_xaxes(ticks="inside", ticklabelmode='period')
            fig.update_traces(textposition='outside', textfont=dict(size=14, color='black', family='Arial'))
            diff_values = grouped_data['diff'].values
            fig.update_layout(paper_bgcolor="#fafafa")
            fig.update_traces(texttemplate='%{text:.3f}', textposition='outside')
            
            padding = 0.1

            st.plotly_chart(fig, use_container_width=True)
          with tab_kpi_2:
            st.subheader('Tasa Homicidios Motociclistas')            
            fig = px.bar(summary_cl, x="anio", y='tasa',
                color='tasa',
                text='tasa',
                color_continuous_scale=["lightgreen", "yellow", "red"],
                        
                labels={'fecha_hora': 'Fecha', 'tasa': 'Tasa', 'anio': 'Año', 'semestre':'Semestre', 'mes':'Mes'},
                template='seaborn')

            fig.update_xaxes(ticks="inside", ticklabelmode='period')
            fig.update_traces(textposition='outside', textfont=dict(size=14, color='black', family='Arial'))
            diff_values = grouped_data['diff'].values
            fig.update_layout(paper_bgcolor="#fafafa")
            fig.update_traces(texttemplate='%{text:.3f}', textposition='outside')
            
            padding = 0.1
            fig.update_layout(yaxis=dict(range=[0, summary_cl['tasa'].max() * (1 + padding)]),showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
          with tab_kpi_3:
            st.subheader('Tasa Homicidios Horas Pico')
            fig = px.bar(data_3_k, x="semestre", y='tasa',
                color='tasa',
                text='tasa',
                color_continuous_scale=["lightgreen", "yellow", "red"],
                        
                labels={'fecha_hora': 'Fecha', 'tasa': 'Tasa', 'anio': 'Año', 'semestre':'Semestre', 'mes':'Mes'},
                template='seaborn')

            fig.update_xaxes(ticks="inside", ticklabelmode='period')
            fig.update_traces(textposition='outside', textfont=dict(size=14, color='black', family='Arial'))
            diff_values = grouped_data['diff'].values
            fig.update_layout(paper_bgcolor="#fafafa")
            fig.update_traces(texttemplate='%{text:.3f}', textposition='outside')
            
            padding = 0.1
            fig.update_layout(yaxis=dict(range=[0, data_3_k['tasa'].max() * (1 + padding)]),showlegend=False)
            st.plotly_chart(fig, user_container_width=True)            
        
        # st.markdown("</div>", unsafe_allow_html=True)
        st.subheader(':arrow_right: Por Tiempo de ocurrencia 	:clock12: ')
        tab_dias, tab_horas, tab_dias_horas, tab_mes = st.tabs(['Dias de la Semana', 'Hora del Día', 'Cruzando Días Horas', 'Por Mes'])
        
        with tab_dias:
          st.subheader("Por día de la semana")
          grouped_data = self.set_accidentes.copy().query(f"gravedad == {fatalidad}")      
          grouped_data_dias = grouped_data.groupby(grouped_data['fecha_hora'].dt.dayofweek)['n_victimas'].count().reset_index()
          dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
          dias_dict = {0: '01-Lunes', 1: '02-Martes', 2: '03-Miércoles', 3: '04-Jueves', 4: '05-Viernes', 5: '06-Sábado', 6: '07-Domingo'}
          grouped_data_dias['dia_semana'] = grouped_data_dias['fecha_hora'].map(dias_dict)
          grouped_data_dias.drop(columns=['fecha_hora'], inplace=True)
          grouped_data_dias.columns = ['nro_accidentes', 'dia_semana']
          grouped_data_dias = grouped_data_dias.sort_values(by='nro_accidentes', ascending=True)
      
          fig = px.bar(grouped_data_dias, x='nro_accidentes', y='dia_semana', 
                      # title='Accidentes por Día de la Semana',
                      color='nro_accidentes',
                      color_continuous_scale=["#A1FFA1", "yellow", "red"],
                      labels={'dia_semana': 'Dia de la Semana', 'nro_accidentes': 'Accidentes'}
                      #  ,              category_orders={'Day of Week': day_names}
                      )
          fig.update_xaxes(ticks="outside")
          
          # fig.update_layout(width=500, height=300)
          col1, col2 = st.columns([.7,.3])
          with col1:
            st.plotly_chart(fig, use_container_width=True)
          with col2:
            '''
            :eye-in-speech-bubble: Insight:
            Vemos que los domingos y los lunes hay una mayor ocurrencia
            de los siniestros.
            '''

        with tab_horas:
          st.subheader("Por Hora del día")
          gd_hora = grouped_data.groupby(grouped_data['fecha_hora'].dt.hour)['n_victimas'].sum().reset_index()


          gd_hora.columns = ['hora', 'n_victimas']
          gd_hora['hora'] = gd_hora['hora'].astype(str)+" hs."

          # # Sort the data in descending order
          gd_hora = gd_hora.sort_values(by='n_victimas', ascending=True)
  

          # Create a stacked bar plot using Plotly Express
          fig = px.bar(gd_hora, x='n_victimas', y='hora', 
                      # title='Accidentes por Hora del Día',
                      color='n_victimas',
                      color_continuous_scale=["#A1FFA1", "yellow", "red"],
                      labels={'hora': 'Hora del día', 'nro_accidentes': 'Accidentes'},
                      orientation='h'
                      ,              category_orders={'Hora del día': 'hora'}
                      )

          # Show the plot
          
          col1, col2 = st.columns([.7,.3])
          with col1:
            st.plotly_chart(fig, use_container_width=True)
          with col2:
            '''
            :eye-in-speech-bubble: Insight:
            La mayoría de los siniestros ocurren a altas horas de la noche y llegando a la mañana.
            '''
        with tab_dias_horas:
          st.subheader("Cruzando datos")

          cross_data = self.set_accidentes.copy().query(f"gravedad == {fatalidad}")
          cross_data['hora'] = cross_data['fecha_hora'].dt.hour
          cross_data['dia_semana'] = cross_data['fecha_hora'].dt.day_of_week
          cross_data['dia_semana'] = cross_data['dia_semana'].map(dias_dict)
          cross_data['hora'] = cross_data['hora']//6
          cuartos = {0: '00 a 06 hs',1: '06 a 12 hs',2: '12 a 18 hs',3: '18 a 00 hs'}
          cross_data['hora'] = cross_data['hora'].map(cuartos)
          
          cross_tab = pd.crosstab(cross_data['hora'], cross_data['dia_semana'])

          cross_tab = cross_tab.reset_index()
          cross_tab.index = cross_tab['hora']
          cross_tab.drop('hora', axis=1, inplace=True)


          # Create a heatmap using Plotly
          fig = px.imshow(cross_tab, 
                          labels=dict(x="Day of the Week", y="Hora", color="Count"),
                          x=cross_tab.columns.str[3:],
                          y=cross_tab.index,
                          color_continuous_scale=["lightgreen", "yellow", "red"])

          # Customize layout
          fig.update_layout(
            # title='Cross-tabulation of Hour and Day of the Week',
                          xaxis_title='Dia de la semana',
                          yaxis_title='Cuarto')

          col1, col2 = st.columns([.7,.3])
          with col1:
            st.plotly_chart(fig, use_container_width=True)
          with col2:
            '''
            :eye-in-speech-bubble: Insight:
            La mayoría de los siniestros ocurren a altas horas de la noche y llegando a la mañana, principalmente los sábados y domingos.
            '''
          

        with tab_mes:
          st.subheader("Por Mes")
          gd_mes = grouped_data.groupby(grouped_data['fecha_hora'].dt.month)['n_victimas'].sum().reset_index()

          meses = {
            1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio",
            7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12:"Diciembre"
          }

          gd_mes.columns = ['mes', 'n_victimas']
          gd_mes['mes'] = gd_mes['mes'].map(meses)
          gd_mes = gd_mes.sort_values(by='n_victimas', ascending=True)
          fig = px.bar(gd_mes, x='n_victimas', y='mes', 
                      # title='Accidentes por Hora del Día',
                      color='n_victimas',
                      color_continuous_scale=["#A1FFA1", "yellow", "red"],
                      labels={'mes': 'MEs', 'n_victimas': 'Victimas'},
                      orientation='h',
                      category_orders={'Hora del día': 'mes'})

          col1, col2 = st.columns([.7,.3])
          with col1:
            st.plotly_chart(fig, use_container_width=True)
          with col2:
            '''
            :eye-in-speech-bubble: Insight:
            La mayoría de los siniestros ocurren en Agosto, Noviembre, Diciembre y Enero, en fechas de fin de año y año nuevo.
            '''
    
        st.subheader(':arrow_right: Geográficamente 	:world_map: ')

        tab_mapa, tab_grafico = st.tabs(['Mapa', 'Gráfico'])

        with tab_mapa:
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


          CENTER = (data['latitud'].median(),data['longitud'].median())
          mapa = folium.Map(CENTER, zoom_start = 11.2)
          
          dic_color = {'GRAVE': '#ffb777', 'FATAL':'#ffb09c'}
          data['cruce_st'] = data['es_cruce'].map({False:'Calle', True:'Esquina'})

          for i in data.index:
              registro = data.loc[i,:]
              color = dic_color[registro.loc['gravedad']]
              
              acc = (registro['latitud'], registro['longitud'])
              folium.Marker(location = acc, 

                            icon=BeautifyIcon(icon=mapa_icono[registro['victima']],background_color=color, fill_opacity=0, text_color='black'),
                            popup=f"{registro['victima']}<br>{registro['cruce_st']}").add_to(mapa)
          
          col1, col2 = st.columns(2)
          with col1:
            st.subheader(f"Comuna: {comuna}")
            st_folium(mapa, width=500, height=500)
          with col2:
            data_all = self.set_accidentes.copy().query("data_geo and gravedad == 'FATAL'")
            media_latitud = data_all['latitud'].fillna(data_all['latitud'].median()).mean()
            media_longitud = data_all['longitud'].fillna(data_all['longitud'].median()).mean()

            st.subheader(f"Por densidad")
            mymap = folium.Map(location=(media_latitud, media_longitud), zoom_start=12)
            radius = 1500  # Adjust as needed

            
            folium.Circle(
            location=(media_latitud, media_longitud),
            radius=radius,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.3
            ).add_to(mymap)

            folium.Circle(
                location=(media_latitud, media_longitud),
                radius=1,
                color='red',
                fill=True,
                fill_color='red',
                fill_opacity=0.3
            ).add_to(mymap)
            
            # st_folium(mymap, width=500, height=500)

        
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
            # folium.GeoJson(geojson_data).add_to(m)                
            
          
            # st_folium(m)

            geojson_file = "comunas.geojson"

            # Load the GeoJSON data
            with open(geojson_file) as f:
                geojson_data = json.load(f)

            # Create a folium map centered at a default location
            m = folium.Map(location=[ -34.6 ,-58.45], zoom_start=11)

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
            st_folium(m, height=500, width=500)

        # with tab_grafico:
        st.subheader("Por Comuna")
        data = self.set_accidentes.copy()#.query(f"gravedad == {fatalidad}")      
        gd_comunas = data.groupby('comuna')['n_victimas'].sum().reset_index()
        gd_comunas = gd_comunas.query("comuna not in ['SD','No Especificada', '0']")
        gd_comunas['comuna'] = "Comuna: "+gd_comunas['comuna'].astype('str')+" "

        gd_comunas = gd_comunas.sort_values(by='n_victimas', ascending=True)
    
        fig = px.bar(gd_comunas, x='n_victimas', y='comuna', 
                    # title='Accidentes por Día de la Semana',
                    color='n_victimas',
                    color_continuous_scale=["#A1FFA1", "yellow", "red"],
                    labels={'comuna': 'Comuna', 'n_victimas': 'Victimas'}
                    #  ,              category_orders={'Day of Week': day_names}
                    )
        fig.update_xaxes(ticks="outside")
        
        # fig.update_layout(width=500, height=300)
        col1, col2 = st.columns([.7,.3])
        with col1:
          st.plotly_chart(fig, use_container_width=True)
        with col2:
          '''
          :eye-in-speech-bubble: Insight:
          Las comunas 1, 15, 4, 9 son las más afectadas.
          '''

        st.subheader("Por Victima")
        clave = 'victima'
        data = self.set_accidentes.copy().query(f"gravedad == {fatalidad}")
        gd_comunas = data.groupby(clave)['n_victimas'].sum().reset_index()
        gd_comunas = gd_comunas.query(f"{clave} not in ['SD','No Especificada', '0']")
        gd_comunas[clave] = ""+gd_comunas[clave].astype('str')+" "

        gd_comunas = gd_comunas.sort_values(by='n_victimas', ascending=True)
    
        fig = px.bar(gd_comunas, x='n_victimas', y=clave, 
                    # title='Accidentes por Día de la Semana',
                    text='n_victimas',
                    color='n_victimas',
                    color_continuous_scale=["#A1FFA1", "yellow", "red"],
                    labels={clave: 'Tipo Víctima', 'n_victimas': 'Victimas'}
                    #  ,              category_orders={'Day of Week': day_names}
                    )
        fig.update_xaxes(ticks="outside")
        fig.update_traces(textposition='inside')
        
        # fig.update_layout(width=500, height=300)
        col1, col2 = st.columns([.7,.3])
        with col1:
          st.plotly_chart(fig, use_container_width=True)
        with col2:
          '''
          :eye-in-speech-bubble: Insight:
          Las motocicletas son las más expuestas, seguidos de los peatones.
          '''
        st.subheader("Por Acusado")
        clave = 'acusado'
        data = self.set_accidentes.copy().query(f"gravedad == {fatalidad}")
        gd_comunas = data.groupby(clave)['n_victimas'].sum().reset_index()
        gd_comunas = gd_comunas.query(f"{clave} not in ['SD','No Especificada', '0']")
        gd_comunas[clave] = ""+gd_comunas[clave].astype('str')+" "

        gd_comunas = gd_comunas.sort_values(by='n_victimas', ascending=True)
    
        fig = px.bar(gd_comunas, x='n_victimas', y=clave, 
                    # title='Accidentes por Día de la Semana',
                    text='n_victimas',
                    color='n_victimas',
                    color_continuous_scale=["#A1FFA1", "yellow", "red"],
                    labels={clave: 'Acusados', 'n_victimas': 'Victimas'}
                    #  ,              category_orders={'Day of Week': day_names}
                    )
        fig.update_xaxes(ticks="outside")
        fig.update_traces(textposition='inside')
        
        # fig.update_layout(width=500, height=300)
        col1, col2 = st.columns([.7,.3])
        with col1:
          st.plotly_chart(fig, use_container_width=True)
        with col2:
          '''
          :eye-in-speech-bubble: Insight:
          Vemos que los automóviles son los que más se involucran en estos siniestros.
          '''

        st.subheader("Por Tipo de Calle")
        clave = 'tipo_calle'
        data = self.set_accidentes.copy().query(f"gravedad == {fatalidad}")
       
        col1, col2 = st.columns([.7,.3])
        with col1:
          st.plotly_chart(showPiePx(data[clave]), use_container_width=True)
        with col2:
          '''
          :eye-in-speech-bubble: Insight:
          Los accidentes fatales preponderan en las Avenidas y los no Fatales están muy cercano en importancia
          en las calles, lo que significa que la gente se accidenta más levemente en las calles, lo que es coherente.
          '''

        st.subheader("Por Tipo de Cruce")        
        data = data.query('info_cruce')['es_cruce'].map({False: 'Calle', True:'Esquina'})
        
        col1, col2 = st.columns([.7,.3])
        with col1:
          st.plotly_chart(showPiePx(data), use_container_width=True)
        with col2:
          '''
          :eye-in-speech-bubble: Insight:
          Vemos la abrumadora preponderancia de las intersecciones en la accidentología, en una proporcion de 3 por cada 4.
          Lo que es coherente por la complejidad de estos cruces.
          '''        
    def show_title(self):
        st.title(self.app_title)

app = App()
app.run()


