import streamlit as st
with open("css/style.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


st.markdown(
    "<h1 style='text-align: center;'>Bem-vindo ao Rail Center</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<h1 style='text-align: center;'>Centralização de dados</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<h1 style='text-align: center;'>Equipe de Inteligência de Dados MR</h1>",
    unsafe_allow_html=True
)

