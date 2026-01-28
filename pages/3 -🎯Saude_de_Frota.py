import streamlit as st
from pymongo import MongoClient
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import math


# Configurações MongoDB
MONGO_URI = st.secrets.database_dev.MONGO_URI
DB_NAME = st.secrets.database_dev.DB_NAME
MONGO_URI_PRD = st.secrets.database_prod.MONGO_URI_PRD
DB_NAME_PRD = st.secrets.database_prod.DB_NAME_PRD


st.set_page_config(layout="wide")
logo = Image.open("assets/logo.png")
st.logo(logo, size='large')
with open("css/style.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
st.title("Saúde Frota -  Visão Macro")
variavel_ativo =""


# Função para conectar e buscar dados
DB_NAME= "inteligencia_MR"
COLLECTION_NAME="SAP_z851_CadastroVagoes"

@st.cache_data(ttl=600)
def function_to_get_data(MONGO_URI_PRD, DB_NAME_PRD, COLLECTION_NAME):
    client = MongoClient(MONGO_URI_PRD)
    db = client[DB_NAME_PRD]
    collection = db[COLLECTION_NAME]
    # Buscar últimos 5 documentos ordenados por timestamp decrescente
    docs = list(collection.find().sort("timestamp", -1).limit(10000))
    if docs:
        # Converter lista de documentos para DataFrame, removendo coluna _id
        df = pd.DataFrame(docs).drop(columns=['_id'], errors='ignore')
        if 'json_documents' in df.columns:
            df['json_documents'] = df['json_documents'].fillna('').astype(str)
        return df
    else:
        return pd.DataFrame()  # DataFrame vazio
    
@st.cache_data(ttl=600)
def function_to_get_data_pipeline(MONGO_URI_PRD, DB_NAME_PRD, COLLECTION_NAME, pipeline):
    client = MongoClient(MONGO_URI_PRD)
    db = client[DB_NAME_PRD]
    collection = db[COLLECTION_NAME]
    docs = list(collection.aggregate(pipeline))
    if docs:
        # Converter lista de documentos para DataFrame, removendo coluna _id
        df = pd.DataFrame(docs)
        if 'json_documents' in df.columns:
            df['json_documents'] = df['json_documents'].fillna('').astype(str)
        return df
    else:
        return pd.DataFrame()  # DataFrame vazio

df = function_to_get_data(MONGO_URI_PRD, DB_NAME_PRD, "SAP_z851_CadastroVagoes")
#df = df.groupby(["STATUS"]).value_counts()
df2 = df
df2 = df2.groupby(['MODELO', 'STATUS'],as_index=False)['STATUS'].value_counts()
df["count"] = df["STATUS"].value_counts()
retidos = df["STATUS"].value_counts()
retidos_metric = (retidos[1]*100)/(retidos[0]+retidos[1])
st.metric(value=str(retidos_metric)+"%", label="% da FROTA RETIDA")
df2 = df2[df2["MODELO"].isin(["GRANELEIROS", "FECHADOS", "PLATAFORMAS", "TANQUES"])]

st.header("Quantos vagões temos em cada Status por frota?")
st.bar_chart(df2, x="MODELO", y= "count", color="STATUS", stack=False, y_label="Total")
pipeline =[
    {
        '$match': {
            'MODELO': {
                '$in': [
                    'GRANELEIROS', 'FECHADOS', 'PLATAFORMAS', 'TANQUES'
                ]
            },
            'TP NOTA': {
                '$in': [
                    'M1', 'M2'
                ]
            }
        }
    },
    {
        '$group': {
            '_id': '$ATIVO', 
            'totalNotes': {
                '$sum': 1
            }
        }
    }
]

pipeline1=[
    {
        '$match': {
            'MODELO': {
                '$in': [
                    'GRANELEIROS', 'FECHADOS', 'PLATAFORMAS', 'TANQUES'
                ]
            }
        }
    },{
        '$group': {
            '_id': {
                'ATIVO': '$ATIVO', 
                'TP NOTA': '$TP NOTA'
            }, 
            'NOTAS_COUNT': {
                '$sum': 1
            }
        }
    }, {
        '$project': {
            '_id': 0, 
            'ATIVO': '$_id.ATIVO', 
            'TP NOTA': '$_id.TP NOTA', 
            'NOTAS_COUNT': 1
        }
    }
]

col1, col2 = st.columns(2)
with col1:
    #st.header("Ranking Vagões com mais Notas abertas")
    st.markdown("<h1 style='font-size:29px;'>Ranking Vagões com mais Notas M1 e M2 abertas</h1>", unsafe_allow_html=True)
    df_notas1 = function_to_get_data_pipeline(MONGO_URI_PRD, DB_NAME_PRD, "SAP_z369_notas",pipeline).sort_values("totalNotes", ascending=False).reset_index(drop=True)
    df_notas1.rename(columns={'_id': 'ATIVOS', 'totalNotes': 'Total de Notas Abertas por ATIVO'}, inplace=True)
    st.dataframe(df_notas1)

with col2:
    df_notas2 = function_to_get_data_pipeline(MONGO_URI_PRD, DB_NAME_PRD, "SAP_z369_notas",pipeline1)
    df_notas2 = df_notas2[df_notas2["TP NOTA"] == "M2"].sort_values("NOTAS_COUNT", ascending=False).reset_index(drop=True)
    #df_notas2 = df_notas2[["ATIVO", "TP NOTA", "NOTAS_COUNT"]]
    df_notas2 = df_notas2[["ATIVO", "NOTAS_COUNT"]]
    df_notas2.rename(columns={'TP NOTA': 'TIPO DE NOTA', 'NOTAS_COUNT': 'Total de Notas M2 Abertas'}, inplace=True)
    st.markdown("<h1 style='font-size:30px;'>Ranking Vagões com mais Notas M2</h1>", unsafe_allow_html=True)
    #st.header("Ranking Vagões com mais Notas M2")
    event = st.dataframe(df_notas2,
                            key="data",
                            on_select="rerun",
                            selection_mode=["multi-cell"])
    
# Supondo que event.selection.cells seja uma lista de listas
if event.selection.cells and len(event.selection.cells) > 0:
    primeira_linha = event.selection.cells[0]
    # Verifica se a linha tem pelo menos 2 colunas
    if len(primeira_linha) > 1:
        if primeira_linha[1] == "ATIVO":
            st.write(df_notas2.loc[event.selection.cells[0][0],event.selection.cells[0][1]])
            variavel_ativo = df_notas2.loc[event.selection.cells[0][0],event.selection.cells[0][1]]
        #Evento para mudar de tela e pegar valor do campo clicado
        #if variavel_ativo != "" and event.selection.cells[0][1] == "ATIVO":
            #st.switch_page("pages/1-📊Consulta Master.py")
            #st.rerun()

st.title("TRKV-Última medição valida de cada vagão ")
pipelineTRKV =[
    {
        '$addFields': {
            'timestr_dt': {
                '$dateFromString': {
                    'dateString': '$timestr', 
                    'format': '%d/%m/%Y %H:%M:%S', 
                    'timezone': 'America/Sao_Paulo', 
                    'onError': None, 
                    'onNull': None
                }
            }
        }
    }, {
        '$match': {
            '$expr': {
                '$or': [
                    
                    {"$ne": ["$A#L_1", math.nan]},
                    {"$ne": ["$A#L_2", math.nan]},
                    {"$ne": ["$A#R_1", math.nan]},
                    {"$ne": ["$A#R_2", math.nan]},
                    {"$ne": ["$B#L_1", math.nan]},
                    {"$ne": ["$B#L_2", math.nan]},
                    {"$ne": ["$B#R_1", math.nan]},
                    {"$ne": ["$B#R_2", math.nan]}

                ]
            }
        }
    }, {
        '$group': {
            '_id': '$concatenatedCarID', 
            'latest': {
                '$top': {
                    'sortBy': {
                        'timestr_dt': -1, 
                        '_id': -1
                    }, 
                    'output': '$$ROOT'
                }
            }
        }
    }, {
        '$replaceRoot': {
            'newRoot': '$latest'
        }
    }
]

pipeline3=[
    {
        '$match': {
            'DATAENCERRAMENTO': ''
        }
    }, {
        '$group': {
            '_id': '$ATIVO'
        }
    }
]
df_notas3 = function_to_get_data_pipeline(MONGO_URI_PRD, DB_NAME_PRD, "SAP_z369_notas",pipeline3)

df_TRKV = function_to_get_data_pipeline(MONGO_URI_PRD, DB_NAME_PRD, "TRKV_treated", pipelineTRKV)
df_TRKV = df_TRKV.drop(columns=['_id', 'CarIDInitial','CarIDNumber', 'CarSequenceNumber','TruckFields', 'TruckIDs','TruckValues','Header_TrainSequenceNumber_int','CarType','timestr'], errors='ignore')
df_TRKV = df_TRKV.sort_values("timestr_dt", ascending=False).set_index('concatenatedCarID').reset_index()
df_TRKV['media_A#L_1'] = df_TRKV['A#L_1'].dropna().mean()
df_TRKV['media_A#L_2'] = df_TRKV['A#L_2'].dropna().mean()
df_TRKV['media_A#R_1'] = df_TRKV['A#R_1'].dropna().mean()
df_TRKV['media_A#R_2'] = df_TRKV['A#R_2'].dropna().mean()
df_TRKV['media_B#L_1'] = df_TRKV['B#L_1'].dropna().mean()
df_TRKV['media_B#L_2'] = df_TRKV['B#L_2'].dropna().mean()
df_TRKV['media_B#R_1'] = df_TRKV['B#R_1'].dropna().mean()
df_TRKV['media_B#R_2'] = df_TRKV['B#R_2'].dropna().mean()

#df_TRKV['MAX_A#L_1'] = df_TRKV['A#L_1'].dropna().max()
#df_TRKV['MAX_A#L_2'] = df_TRKV['A#L_2'].dropna().max()
#df_TRKV['MAX_A#R_1'] = df_TRKV['A#R_1'].dropna().max()
#df_TRKV['MAX_A#R_2'] = df_TRKV['A#R_2'].dropna().max()
##df_TRKV['MAX_B#L_1'] = df_TRKV['B#L_1'].dropna().max()
#df_TRKV['MAX_B#L_2'] = df_TRKV['B#L_2'].dropna().max()
#df_TRKV['MAX_B#R_1'] = df_TRKV['B#R_1'].dropna().max()
#df_TRKV['MAX_B#R_2'] = df_TRKV['B#R_2'].dropna().max()
df_TRKV.rename(columns={'concatenatedCarID': 'ATIVO'}, inplace=True)
#df_TRKV['MIN_A#L_1'] = df_TRKV['A#L_1'].dropna().min()
#df_TRKV['MIN_A#L_2'] = df_TRKV['A#L_2'].dropna().min()
#df_TRKV['MIN_A#R_1'] = df_TRKV['A#R_1'].dropna().min()
#df_TRKV['MIN_A#R_2'] = df_TRKV['A#R_2'].dropna().min()
#df_TRKV['MIN_B#L_1'] = df_TRKV['B#L_1'].dropna().min()
#df_TRKV['MIN_B#L_2'] = df_TRKV['B#L_2'].dropna().min()
#df_TRKV['MIN_B#R_1'] = df_TRKV['B#R_1'].dropna().min()
#df_TRKV['MIN_B#R_2'] = df_TRKV['B#R_2'].dropna().min()
st.dataframe(df_TRKV)

#filtro1 =df_TRKV['A#L_1']> 40 | df_TRKV['A#L_2']> 40 | df_TRKV['A#R_1']> 40  | df_TRKV['A#R_2']> 40
#filtro2 =df_TRKV['B#L_1']> 40 | df_TRKV['B#L_2']> 40 | df_TRKV['B#R_1']> 40  | df_TRKV['B#R_2']> 40

#df[df['salario1']>5000]
#Combinando filtros para dataframe
limite_TRKV = 60
filtro1=df_TRKV['A#L_1']> limite_TRKV
filtro2=df_TRKV['A#L_2']> limite_TRKV
filtro3=df_TRKV['A#R_1']> limite_TRKV
filtro4=df_TRKV['A#R_2']> limite_TRKV
filtro5=df_TRKV['B#L_1']> limite_TRKV
filtro6=df_TRKV['B#L_2']> limite_TRKV
filtro7=df_TRKV['B#R_1']> limite_TRKV
filtro8=df_TRKV['B#R_2']> limite_TRKV
#df[filtro1 & filtro2]

df_TRKV = df_TRKV[filtro1 | filtro2 | filtro3 | filtro4 | filtro5 | filtro6 | filtro7 | filtro8]
st.header("TRKV - Vagões com cunha maior que 60 e se possue nota aberta")


#df_TRKV['Possui Nota Aberta'] = df_TRKV['ATIVO'].isin(df_notas3['_id']).map({True: 'Sim', False:'Não'})
df_TRKV['Possui Nota Aberta'] = df_TRKV['ATIVO'].isin(df_notas3['_id']).map({True: 'Sim', False:'Não'})
st.dataframe(df_TRKV.reset_index(drop=True).drop(columns=['media_A#L_1','media_A#L_2','media_A#R_1','media_A#R_2','media_B#L_1','media_B#L_2','media_B#R_1','media_B#R_2','data_sincronizacao']))




#df_notas3.rename(columns={'_id': 'ATIVOS', 'totalNotes': 'Total de Notas Abertas por ATIVO'}, inplace=True)
#st.dataframe(df_notas3)



st.header("TRKV ALTO com Nota aberta")
df_TRKV_filtrado = df_TRKV[df_TRKV['ATIVO'].isin(df_notas3['_id'])]
st.dataframe(df_TRKV_filtrado.reset_index(drop=True).drop(columns=['media_A#L_1','media_A#L_2','media_A#R_1','media_A#R_2','media_B#L_1','media_B#L_2','media_B#R_1','media_B#R_2','data_sincronizacao']))

st.header("TRKV - Vagões que nunca foram lidos")
df_vagoes_sem_leitura = df[~df['EQUNR'].isin(df_TRKV['ATIVO'])]
df_vagoes_sem_leitura = df_vagoes_sem_leitura.drop(columns=['Atualizacao', 'DATA_DE_FABRICACAO', 'DATA_FIM', 'DATA_FIM_trated', 'DATA_GARANTIA','DATA_GARANTIA_trated'])
df_vagoes_sem_leitura = df_vagoes_sem_leitura[df_vagoes_sem_leitura['MODELO'].isin(['GRANELEIROS', 'FECHADOS', 'PLATAFORMAS', 'TANQUES']) ]
df_vagoes_sem_leitura = df_vagoes_sem_leitura[df_vagoes_sem_leitura['MALHA'] == 'N']
df_vagoes_sem_leitura = df_vagoes_sem_leitura[df_vagoes_sem_leitura['BITOLA'] == 'L']
st.dataframe(df_vagoes_sem_leitura.reset_index(drop=True))
count = df_vagoes_sem_leitura['EQUNR'].count()
st.metric(label= 'Vagões sem leitura no TRKV', value=count)

df_vagoes_sem_leitura = df_vagoes_sem_leitura.groupby(["MODELO"], as_index=False)['EQUNR'].count()
#df_vagoes_sem_leitura['count1'] = df_vagoes_sem_leitura['MODELO'].count()
st.header('Vagões sem nenhuma leitura no TRKV por categoria:')
N_COLS = 4
cols = st.columns(N_COLS)
for i, row in df_vagoes_sem_leitura.iterrows(): 
    col = cols[i % N_COLS]
    # Formatação do delta em %
    #delta_pct = f"{row['delta']*100:.1f}%"
    # Se quiser colorir positivo/negativo corretamente, use delta diretamente como string com sinal
    col.metric(
        label=row["MODELO"],
        value=row["EQUNR"]
        #delta=delta_pct if row["delta"] >= 0 else f"-{abs(row['delta']*100):.1f}%"
    )
#st.title("WCM - qual a ultima medição valida de cada vagão ")







#st.title("Quantos vagões temos acima xx de cunha")









#st.title("Quantos vagões temos com impacto acima de 200 ")







#st.title("Quantos vagões temos rodando com nota crítica")








#st.title("Quantas notas temos aberta de cada tipo por vagão")








#st.title("Quantas MC eu fiz no vagão depois da RG")
