import streamlit as st
from pymongo import MongoClient
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Configurações MongoDB
MONGO_URI = "mongodb+srv://int_dados:e7bUe2bXbKDu3Xzr@rumo-dev2.hbdcrld.mongodb.net/?authSource=admin"
DB_NAME = "supervisorio"

st.set_page_config(layout="wide")

# Função para conectar e buscar dados


def function_to_get_data(MONGO_URI, DB_NAME, COLLECTION_NAME, lines=5):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    # Buscar últimos 5 documentos ordenados por timestamp decrescente
    docs = list(collection.find().sort("timestamp", -1).limit(lines))
    client.close()

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

    return df_trkv, df_WCM


st.title("Consulta MongoDB via Streamlit v3")

# Cria abas na parte superior
aba1, aba2, aba3, aba4, aba5 = st.tabs(
    ["Verify", "Graph", "Saúde de Frota", "Chat Bot", "Sobre"])

with aba1:
    st.header("Consulta MongoDB")
    if st.button("Carregar últimos 5 documentos"):
        df_WCM, df_trkv = get_latest_documents()

        if df_WCM.empty:
            st.warning("Nenhum documento encontrado em WCM.")
        else:
            st.subheader("Tabela dos documentos carregados [WCM]")
            st.dataframe(df_WCM)

        if df_trkv.empty:
            st.warning("Nenhum documento encontrado em TRKV.")
        else:
            st.subheader("Tabela dos documentos carregados [TRKV]")
            st.dataframe(df_trkv)

# ======= Aba 2 - Sobre =======
with aba2:
    import numpy as np
    import plotly.express as px
    import pandas as pd

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

with aba4:  # Chat Bot
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
