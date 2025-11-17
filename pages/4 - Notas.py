import streamlit as st
from pymongo import MongoClient
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import plotly.express as px
# Configurações MongoDB
MONGO_URI = "mongodb+srv://int_dados:e7bUe2bXbKDu3Xzr@rumo-dev2.hbdcrld.mongodb.net/?authSource=admin"
DB_NAME = "supervisorio"
COLLECTION_NAME = "z369_full"

st.set_page_config(layout="wide")

#-------------------------------------------------------------------------------------
#Importar DADOS
@st.cache_data(ttl=600)
def function_to_get_total_ativos_por_tipo(MONGO_URI, DB_NAME, COLLECTION_NAME):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    pipeline = [
    {
        '$project': {
            'DESC STATUS': 1, 
            'dt_abertura_trated': 1
        }
    }
]

    # Buscar últimos documentos ordenados por timestamp decrescente
    docs = collection.aggregate(pipeline)#.find().sort("dt_abertura_trated", -1).limit(lines)
    #print(docs)

    if docs:
        # Converter lista de documentos para DataFrame, removendo coluna _id
        df = pd.DataFrame(docs).drop(columns=['_id'], errors='ignore')
        if 'json_documents' in df.columns:
            df['json_documents'] = df['json_documents'].fillna('').astype(str)
        return df
    else:
        return pd.DataFrame()  # DataFrame vazio

#-----------------------------------------------------------------------------------------
    
st.title("Gestão de Ativos - Vagões")
#Importando para dataframe
df= function_to_get_total_ativos_por_tipo(MONGO_URI, DB_NAME, "z369_full")
#Criando coluna mes
#df['mes'] = df['dt_abertura_trated'].dt.to_period('M')
df["mes"] = pd.to_datetime(df["dt_abertura_trated"], format="%Y-%m")
df = df.sort_values("mes")
df['mes'] = df['mes'].dt.to_period('M')
df['mes'] = df['mes'].dt.to_timestamp()
df2 = df
#Modelando tabela para calculo
#df['lag_1'] = df['DESC STATUS'].shift(1)
#df['lag_2'] = df['mes'].shift(1)

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

#df2 = df.groupby(['mes','DESC STATUS','dt_abertura_trated'])['DESC STATUS'].count()
df2 = df2.groupby(['mes', 'DESC STATUS'],as_index=False)['DESC STATUS'].value_counts()
#df2 = df2.groupby('mes')['DESC STATUS'].count()
#df2 = df2.groupby('DESC STATUS')['mes'].count()
#df2 = df2['DESC STATUS'].value_counts()
df_Z369= function_to_get_data_from_z369(MONGO_URI, DB_NAME, "z369_full")
df_Z369_1= function_to_get_data_from_z369(MONGO_URI, DB_NAME, "z369_full")
df_Z369_1['mes'] = df_Z369_1['data_sincronizacao'].dt.to_period('M')
cont1 = df_Z369['DESC STATUS'].value_counts()
col5, col6, col7 = st.columns(3)
with col5: 
    col5 = st.metric(label ='Total de Notas fechadas',value = cont1['Mensagem encerrada'])
with col6:
    col6 = st.metric(label ='Total de Notas pendentes',value = cont1['Mensagem pendente'])
with col7:
    col7 = st.metric(label ='Total de Notas em processamento',value = cont1['Mensagem em processamento'])

st.dataframe(df)
st.dataframe(df2)
df2 = df2[df2['DESC STATUS'] == 'Mensagem pendente']
df4 = df2[df2['DESC STATUS'] == 'Mensagem encerrada']
st.bar_chart(df2, x='mes', y='count', color='DESC STATUS',stack=False)
st.bar_chart(df4, x='mes', y='count', color='DESC STATUS',stack=False)
st.line_chart(df2, x='mes', y='count', color='DESC STATUS')
st.bar_chart(df2, y='count')
st.bar_chart(df2, y='DESC STATUS')


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
# Gráfico interativo
#fig = px.bar(df2, x="mes", y="count", color="DESC STATUS", barmode="group",title="Relação de Mensagens por Mês e Tipo")

# Exibir no Streamlit
#st.plotly_chart(df2, x="mes", y="count", color="DESC STATUS")

#st.bar_chart(df2, x='DESC STATUS', y='dt_abertura_trated')