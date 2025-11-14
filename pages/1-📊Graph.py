import numpy as np
import plotly.express as px
import pandas as pd
import streamlit as st
from pymongo import MongoClient
import matplotlib.pyplot as plt
from PIL import Image


# Configurações MongoDB
MONGO_URI = "mongodb+srv://int_dados:e7bUe2bXbKDu3Xzr@rumo-dev2.hbdcrld.mongodb.net/?authSource=admin"
DB_NAME = "supervisorio"

st.set_page_config(layout="wide")

# Função para conectar e buscar dados

@st.cache_data(ttl=600)
def function_to_get_data(MONGO_URI, DB_NAME, COLLECTION_NAME, lines=5):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    # Buscar últimos 5 documentos ordenados por timestamp decrescente
    docs = list(collection.find().sort("timestamp", -1).limit(lines))
    

    if docs:
        # Converter lista de documentos para DataFrame, removendo coluna _id
        df = pd.DataFrame(docs).drop(columns=['_id'], errors='ignore')
        if 'json_documents' in df.columns:
            df['json_documents'] = df['json_documents'].fillna('').astype(str)
        return df
    else:
        return pd.DataFrame()  # DataFrame vazio

@st.cache_data(ttl=600)
def function_to_get_data_from_z369(MONGO_URI, DB_NAME, COLLECTION_NAME, lines=10000):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    # Buscar últimos documentos ordenados por timestamp decrescente
    docs = collection.find().sort("dt_abertura_trated", -1).limit(lines)
    

    if docs:
        # Converter lista de documentos para DataFrame, removendo coluna _id
        df = pd.DataFrame(docs).drop(columns=['_id'], errors='ignore')
        if 'json_documents' in df.columns:
            df['json_documents'] = df['json_documents'].fillna('').astype(str)
        return df
    else:
        return pd.DataFrame()  # DataFrame vazio


@st.cache_data
def get_latest_documents():
    COLLECTION_NAME = "TRKV"
    df_trkv = function_to_get_data(
        MONGO_URI, DB_NAME, COLLECTION_NAME, lines=5)

    COLLECTION_NAME = "WCM"
    df_WCM = function_to_get_data(
        MONGO_URI, DB_NAME, COLLECTION_NAME, lines=5)
    
    COLLECTION_NAME = "z369_full"
    df_Z369 = function_to_get_data(
        MONGO_URI, DB_NAME, COLLECTION_NAME)

    return df_trkv, df_WCM, df_Z369

logo = Image.open("assets/logo.png")
st.logo(logo, size='large')
st.header("Sobre o Aplicativo")
st.write("Este é um app para consulta de dados no MongoDB com Streamlit v3.")
st.markdown("---")

    # Gera dados de exemplo
dados = np.random.randn(10)
df = pd.DataFrame({
        "x": list(range(10)),
        "y": dados,
        "categoria": [f"L{i}" for i in range(10)]
    })

    # Cria layout 2x2a
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
        st.subheader("Gráfico 1 - Linha 📈")
        fig1 = px.line(df, x="x", y="y", markers=True, title="Série temporal")
        st.plotly_chart(fig1, use_container_width=True)

with col2:
        st.subheader("Gráfico 2 - Barras 📊")
        fig2 = px.bar(df, x="categoria", y="y",
                      title="Distribuição por categoria")
        st.plotly_chart(fig2, use_container_width=True)

with col3:
        st.subheader("Gráfico 3 - Histograma 📦")
        fig3 = px.histogram(df, x="y", nbins=5,
                            title="Distribuição dos valores")
        st.plotly_chart(fig3, use_container_width=True)

with col4:
        st.subheader("Gráfico 4 - Pizza 🥧")
        fig4 = px.pie(df.head(5), values="y", names="categoria",
                      title="Top 5 categorias")
        st.plotly_chart(fig4, use_container_width=True)
