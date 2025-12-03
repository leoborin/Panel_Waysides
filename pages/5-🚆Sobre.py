import numpy as np
import plotly.express as px
import pandas as pd
import streamlit as st
from pymongo import MongoClient
import matplotlib.pyplot as plt
from PIL import Image

with open("css/style.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
st.title("BI em desenvolvimento")
st.header("Centralização de dados")

if st.button("snow"):
    st.snow()

#st.button("snow",on_click= st.write("teste"))

df = pd.DataFrame({
        "NOTA": ["NOTA-123", "NOTA-124"],
        "Inicio": ["2024-01-01", "2024-01-01"],
        "Fim": ["2024-02-01", None],
        "Tipo": ["M1", "M2"]
    })

# Converte datas
df["Inicio"] = pd.to_datetime(df["Inicio"])
df["Fim"] = pd.to_datetime(df["Fim"])

# Cria Fim_Aux: se Fim for nulo -> usa data atual
df["Fim_Aux"] = df["Fim"].fillna(pd.Timestamp.now())

# Timeline usando Fim_Aux para x_end
fig = px.timeline(
    df,
    x_start="Inicio",
    x_end="Fim_Aux",
    y="NOTA",
    color="Tipo",
    text="NOTA",
    hover_data={
        "Fim_Aux": False,   # não mostrar no hover
        "Fim": True,        # mostrar o Fim original
        "Inicio": True,
        "Tipo": True,
    }
)

fig.update_yaxes(autorange="reversed")

st.plotly_chart(fig, width='stretch')
st.dataframe(df)
