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


st.header("🤖 Chat Bot")
st.write("Converse com o assistente! (Protótipo)")

    # Mantém o histórico do chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

    # Exibe o histórico de conversas
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
    else:
            st.chat_message("assistant").write(msg["content"])

    # Campo de entrada de texto
user_input = st.chat_input("Digite sua mensagem...")

if user_input:
        # Adiciona a mensagem do usuário
    st.session_state.chat_history.append(
            {"role": "user", "content": user_input})

        # Resposta simulada (pode substituir por chamada a modelo de IA)
    resposta = f"Você disse: '{user_input}'. vagão mais crítico é o HPT 4463877 com a pontuação 398. Esta é uma resposta simulada do bot 😊"

        # Adiciona resposta no histórico
    st.session_state.chat_history.append(
            {"role": "assistant", "content": resposta})

        # Exibe a resposta imediatamente
    st.chat_message("assistant").write(resposta)
        