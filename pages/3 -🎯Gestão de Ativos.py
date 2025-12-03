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

with open("css/style.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

pipeline1 = [ {
      "$project": {
        "Documento": 0,
        "DT_HR_RET": 0,
        "ESCOPO": 0,
        "HORA FIM": 0,
        "HORA INICIO": 0,
        "PMV": 0,
        "DISPONIBILIDADE": 0,
        "SEQUENCIAL": 0,
        "VAGAO": 0,
        "data_sincronizacao": 0,
        "DATA FIM": 0,
        "DATA INICIO": 0,
        "DATAREC": 0,
        "dt_modificacao":0
      }
    },
    {
      "$sort": {
        "dt_inicio_trated": -1
      }
    }
  ]

pipeline2 =[
    {
        '$project': {
            'Documento': 0, 
            'DT_HR_RET': 0, 
            'ESCOPO': 0, 
            'HORA FIM': 0, 
            'HORA INICIO': 0, 
            'PMV': 0,  
            'SEQUENCIAL': 0, 
            'VAGAO': 0, 
            'data_sincronizacao': 0, 
            'DATA FIM': 0, 
            'DATA INICIO': 0, 
            'DATAREC': 0,
            "dt_modificacao":0
        }
    }
]
# Função para conectar e buscar dados

@st.cache_data(ttl=600)
def function_to_get_data(MONGO_URI, DB_NAME, COLLECTION_NAME,PIPELINE):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    docs = list(collection.aggregate(PIPELINE))
    if docs:
        # Converter lista de documentos para DataFrame, removendo coluna _id
        df = pd.DataFrame(docs).drop(columns=['_id',''], errors='ignore')
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

df_ret = function_to_get_data(MONGO_URI,DB_NAME,"z1568_Liberacoes_Retencoes_full", pipeline2)
df_1 = function_to_get_data(MONGO_URI,DB_NAME,"z1568_Liberacoes_Retencoes_full", pipeline2)
df_1 = df_1.drop(['dt_fim_trated', 'DATA_ABERTURA_INT','dt_modificacao_trated'], axis=1)
df5=df_1
#df3 = df_ret.groupby("RETENCAO")["RETENCAO"].value_counts()
df4 = df_ret["RETENCAO"].value_counts().get('RETIDO',0)
df_1 = df_1[(df_1['dt_inicio_trated'] >= '2023-01-01')]
df_1['mes'] = df_1['dt_inicio_trated'].dt.to_period('M')
df_1 = df_1.groupby(["mes"],as_index=False)["mes"].value_counts()
df_1['mes'] = df_1['mes'].dt.to_timestamp()
df_ret = df_ret[(df_ret['RETENCAO'] == 'RETIDO') & (df_ret['DISPONIBILIDADE'] != 'RETIDO')]
st.dataframe(df_ret)
#st.dataframe(df3)
st.metric(value = df4, label='Vagões Retidos')
#st.dataframe(df_1)
st.title("Vagões Retidos Por Mês")
st.line_chart(df_1, x='mes', y='count', x_label="Mês", y_label="Total")
df5['mes'] = df5['dt_inicio_trated'].dt.to_period('M')
df5['mes'] = df5['mes'].dt.to_timestamp()
df5 = df5[(df5['dt_inicio_trated'] >= '2023-01-01')]
df5 = df5.groupby(["mes", "GRUPO_AVARIA"],as_index=False)["mes"].value_counts()

st.dataframe(df5)
st.line_chart(df5, x='mes', y= 'count', color='GRUPO_AVARIA')
st.bar_chart(df5,x='mes', y= 'count', color='GRUPO_AVARIA', stack=False )