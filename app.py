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
st.title("Consulta MongoDB via Streamlit v3")

# Cria abas na parte superior
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs(
    ["Verify", "Graph", "Saúde de Frota", "Chat Bot", "Sobre", "Testes de componentes"])

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

with aba3:

    #st.sidebar.markdown("### Portal de BI")
    


    #st.header("Ficha Vagão")
    st.title("Ficha Vagão - Prognósticos Integrado de Vagões")
    st.write("Testes de desenvolvimento de BI para Vagões")
    df_Z369= function_to_get_data_from_z369(MONGO_URI, DB_NAME, "z369_full")
    df_Z369_1= function_to_get_data_from_z369(MONGO_URI, DB_NAME, "z369_full")
    #teste = df_Z369['data_sincronizacao'].drop_duplicates()
    #st.write(teste)
    #contagem_mensal = df_Z369['data_sincronizacao'].dt.to_period('M').value_counts().sort_index()
    df_Z369_1['mes'] = df_Z369_1['data_sincronizacao'].dt.to_period('M')
    #st.write(df_Z369_1.groupby('DESC STATUS').size())
    #st.write(df_Z369_1.groupby('mes').size())
    
    contagens = (pd.crosstab(df_Z369_1['mes'], df_Z369_1['DESC STATUS'])   # linhas=mes, colunas=status
               .reindex(columns=['Mensagem encerrada', 'Mensagem pendente','Mensagem em processamento'], fill_value=0)
               .sort_index())
    #st.write(contagens)
    #3st.dataframe(df_Z369_1)
    #qtd_por_mes = 

    cont1 = df_Z369['DESC STATUS'].value_counts()
    col5, col6, col7 = st.columns(3)
    with col5: 
        col5 = st.metric(label ='Total de Notas fechadas',value = cont1['Mensagem encerrada'], delta = '10%')
    with col6:
        col6 = st.metric(label ='Total de Notas pendentes',value = cont1['Mensagem pendente'], delta = '30%')
    with col7:
        col7 = st.metric(label ='Total de Notas em processamento',value = cont1['Mensagem em processamento'], delta = '-25%')

    st.date_input(label = 'Data de Atualização', value = 'today', disabled = True)

    vagao_input = st.text_input('Escreva um vagão')
    filtro_vagao = df_Z369['ATIVO'] == vagao_input
    st.dataframe(df_Z369[filtro_vagao])

    col1, col2, col3 = st.columns(3)
    with col1:
        col1 = st.selectbox('Selecione um Local', sorted(df_Z369['Local'].drop_duplicates())) 
        filtro1 = df_Z369["Local"]== col1
        df_Z369 = df_Z369[filtro1]
    with col2:
        col2 = st.selectbox('Selecione um Estado', df_Z369['DESC STATUS'].drop_duplicates())
        filtro2 = df_Z369["DESC STATUS"]== col2
        df_Z369 = df_Z369[filtro2]
    with col3:
        col3 = st.selectbox('Selecione uma Nota', sorted(df_Z369['TP NOTA'].drop_duplicates()))
        filtro3 = df_Z369["TP NOTA"]== col3
        df_Z369 = df_Z369[filtro3]
    
    df1 = df_Z369[filtro3]
    
    st.dataframe(df1)


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
        
with aba6:  # Teste de Componentes do STREAMLIT
    import datetime
    st.header("Teste de Componentes do STREAMLIT")
    st.title("Teste Title")
    st.write("Teste Write")
    st.write("""#Teste Write""")

    date= st.date_input("When's your birthday", value="today")
    st.write("Your birthday is:", date)