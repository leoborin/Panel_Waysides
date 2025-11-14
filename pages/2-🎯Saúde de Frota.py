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

@st.cache_data(ttl=600)
def function_to_get_total_ativos_por_tipo(MONGO_URI, DB_NAME, COLLECTION_NAME, lines=10000):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
        
    pipeline = [
    {
        '$group': {
            '_id': '$ATIVO', 
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
ativos_total= function_to_get_total_ativos_por_tipo(MONGO_URI, DB_NAME, "z369_full")

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

#ativos_total['ATIVO'] = ativos_total['ATIVO'].fillna()
#st.dataframe(ativos_total)

@st.cache_data
def get_latest_documents():
    COLLECTION_NAME = "TRKV"
    df_trkv = function_to_get_data(
        MONGO_URI, DB_NAME, COLLECTION_NAME, lines=5)

    #COLLECTION_NAME = "WCM"
    #df_WCM = function_to_get_data(
        #MONGO_URI, DB_NAME, COLLECTION_NAME, lines=5)
    
    COLLECTION_NAME = "z369_full"
    df_Z369 = function_to_get_data(
        MONGO_URI, DB_NAME, COLLECTION_NAME, lines=5)

    return df_trkv, df_WCM, df_Z369

logo = Image.open("assets/logo.png")
st.logo(logo, size='large')
#st.sidebar.markdown("### Portal de BI")
    


#st.header("Ficha Vagão")
st.title("Ficha Vagão - Prognósticos Integrado de Vagões")
st.write("Testes de desenvolvimento de BI para Vagões")
st.header("Gestão de Ativos")
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
    col5 = st.metric(label ='Total de Notas fechadas',value = cont1['Mensagem encerrada'])
with col6:
    col6 = st.metric(label ='Total de Notas pendentes',value = cont1['Mensagem pendente'])
with col7:
    col7 = st.metric(label ='Total de Notas em processamento',value = cont1['Mensagem em processamento'])

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