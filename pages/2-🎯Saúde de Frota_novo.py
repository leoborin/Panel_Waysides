import streamlit as st
from pymongo import MongoClient
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image


# Configurações MongoDB
MONGO_URI = "mongodb+srv://int_dados:e7bUe2bXbKDu3Xzr@rumo-dev2.hbdcrld.mongodb.net/?authSource=admin"
DB_NAME = "supervisorio"

st.set_page_config(layout="wide")
logo = Image.open("assets/logo.png")
st.logo(logo, size='large')
st.title("Saúde Frota")
st.header("Gestão de Ativos")


# Função para conectar e buscar dados
DB_NAME= "supervisorio"
COLLECTION_NAME="zCadVagoes_resumos"

@st.cache_data(ttl=600)
def function_to_get_data(MONGO_URI, DB_NAME, COLLECTION_NAME):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    # Buscar últimos 5 documentos ordenados por timestamp decrescente
    docs = list(collection.find().sort("timestamp", -1))
    if docs:
        # Converter lista de documentos para DataFrame, removendo coluna _id
        df = pd.DataFrame(docs).drop(columns=['_id', "TRKV_info"], errors='ignore')
        if 'json_documents' in df.columns:
            df['json_documents'] = df['json_documents'].fillna('').astype(str)
        return df
    else:
        return pd.DataFrame()  # DataFrame vazio

df = function_to_get_data(MONGO_URI, DB_NAME, COLLECTION_NAME)
df.info()
df.describe()
print(df)