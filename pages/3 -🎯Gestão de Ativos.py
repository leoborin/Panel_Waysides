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

@st.cache_data(ttl=600)
def function_to_get_total_ativos_por_tipo(MONGO_URI, DB_NAME, COLLECTION_NAME, lines=10000):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
        
    pipeline = [
    {
        '$group': {
            '_id': '$EQUNR', 
            'doc': {
                '$first': '$$ROOT'
            }
        }
    }, {
        '$replaceRoot': {
            'newRoot': '$doc'
        }
    }, {
        '$group': {
            '_id': '$MODELO', 
            'count': {
                '$sum': 1
            }
        }
    }
]
    # Buscar últimos documentos ordenados por timestamp decrescente
    docs = collection.aggregate(pipeline)#.find().sort("dt_abertura_trated", -1).limit(lines)
    print(docs)

    if docs:
        # Converter lista de documentos para DataFrame, removendo coluna _id
        df = pd.DataFrame(docs)
        if 'json_documents' in df.columns:
            df['json_documents'] = df['json_documents'].fillna('').astype(str)
        return df
    else:
        return pd.DataFrame()  # DataFrame vazio

st.title("Gestão de Ativos - Vagões")
ativos_total= function_to_get_total_ativos_por_tipo(MONGO_URI, DB_NAME, "CadastroVagoes_full")

N_COLS = 4
cols = st.columns(N_COLS)

for i, row in ativos_total.iterrows(): 
    col = cols[i % N_COLS]
    # Formatação do delta em %
    #delta_pct = f"{row['delta']*100:.1f}%"
    # Se quiser colorir positivo/negativo corretamente, use delta diretamente como string com sinal
    col.metric(
        label=row["_id"],
        value=row["count"]
        #delta=delta_pct if row["delta"] >= 0 else f"-{abs(row['delta']*100):.1f}%"
    )

st.title("Vagões Retidos")

df_ret = function_to_get_data(MONGO_URI,DB_NAME,"CadastroVagoes_full")