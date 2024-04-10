import streamlit as st


st.set_page_config(page_title="Stream Media")

st.camera_input("Capture")

st.image(image="https://upload.wikimedia.org/wikipedia/en/thumb/c/cc/Chelsea_FC.svg/1200px-Chelsea_FC.svg.png", width=600)

st.balloons()

st.sidebar.title("Menu")
st.write("Hello")

st.echo()
with st.echo():
    st.write('Code will be executed and printed')
    
st.snow()
st.toast('Mr Stay-Puft')
st.error('Error message')
st.warning('Warning message')
st.info('Info message')
st.success('Success message')