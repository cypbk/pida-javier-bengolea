import streamlit as st
import psycopg2
import pandas as pd

def connect_to_db():
    conn = psycopg2.connect(
        host="localhost",
        database="warehouse",
        user="airflow_user",
        password="airflow_pass",
        port=5433
    )
    return conn

def run_query(query):
    conn = connect_to_db()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

st.set_page_config(
    page_title='Data Warehouse',
    page_icon=':chart_with_upwards_trend:', 
    layout="wide"
)

st.markdown('''<style>div.block-container{padding-top: 1rem}        </style>''', unsafe_allow_html=True)
st.header(" Data Warehouse :bar_chart:")  

query_1 = "select * from restaurantes"
query_2 = "select * from reviews"
query_3 = "select * from estados"

# Button to run the query
if st.button('Leer Datos'):
    try:
        df_restaurantes = run_query(query_1)
        df_reviews = run_query(query_2)
        df_estados = run_query(query_3)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.header('Restaurantes')
            f'''Cantidad de restaurantes {df_restaurantes.shape[0]}'''
            st.write(df_restaurantes)
        
        with col2:
            st.header('Reviews')
            f'''Cantidad de Reviews {df_reviews.shape[0]}'''
            st.write(df_reviews)

        with col3:
            st.header('Estados')
            f'''Cantidad de Estados {df_estados.shape[0]}'''    
            st.write(df_estados)
    except Exception as e:
        st.error(f"Error: {e}")
        # st.warning('Please enter a SQL query.')



# Input for SQL query
# query = st.text_area('Enter your SQL query here')

# # Button to run the query
# if st.button('Run Query'):
#     if query:
#         try:
#             df = run_query(query)
#             st.write(df)
#         except Exception as e:
#             st.error(f"Error: {e}")
#     else:
#         st.warning('Please enter a SQL query.')

