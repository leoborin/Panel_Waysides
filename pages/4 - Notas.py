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

#df2 = df.groupby(['mes','DESC STATUS','dt_abertura_trated'])['DESC STATUS'].count()
df2 = df2.groupby(['mes', 'DESC STATUS'],as_index=False)['DESC STATUS'].value_counts()
#df2 = df2.groupby('mes')['DESC STATUS'].count()
#df2 = df2.groupby('DESC STATUS')['mes'].count()
#df2 = df2['DESC STATUS'].value_counts()

data = {
    'Produto': ['A', 'B', 'A', 'B', 'A'],
    'Quantidade': [10, 20, 15, 25, 10],
    'Receita': [100, 200, 150, 250, 100]
}
df3 = pd.DataFrame(data)

st.dataframe(df)
st.dataframe(df2)
st.dataframe(df3)
total_quantidade_por_produto = df3.groupby('Produto')['Quantidade'].sum()
st.dataframe(total_quantidade_por_produto)
df2 = df2[df2['DESC STATUS'] == 'Mensagem pendente']
df4 = df2[df2['DESC STATUS'] == 'Mensagem encerrada']
st.bar_chart(df2, x='mes', y='count', color='DESC STATUS',stack=False)
st.bar_chart(df4, x='mes', y='count', color='DESC STATUS',stack=False)
st.line_chart(df2, x='mes', y='count', color='DESC STATUS')
st.bar_chart(df2, y='count')
st.bar_chart(df2, y='DESC STATUS')

# Gráfico interativo
#fig = px.bar(df2, x="mes", y="count", color="DESC STATUS", barmode="group",title="Relação de Mensagens por Mês e Tipo")

# Exibir no Streamlit
#st.plotly_chart(df2, x="mes", y="count", color="DESC STATUS")

#st.bar_chart(df2, x='DESC STATUS', y='dt_abertura_trated')