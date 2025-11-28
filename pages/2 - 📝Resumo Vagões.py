import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re
from datetime import datetime
import plotly.graph_objects as go
from numpy.random import default_rng as rng
from concurrent.futures import ThreadPoolExecutor
import os
import glob
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

st.sidebar.markdown("### 2 - 📝Resumo Vagões.py")

# app.py
warnings.filterwarnings("ignore")


MONGO_URI = "mongodb+srv://int_dados:e7bUe2bXbKDu3Xzr@rumo-dev2.hbdcrld.mongodb.net/?authSource=admin"
DB_NAME = "supervisorio"


st.set_page_config(layout="wide")

# =============================
# Carregar Parquet
# =============================

# Caminho da pasta onde estão os parquet
CAMINHO = r"./temp"   # ajuste se necessário

# Lista todos os arquivos .parquet da pasta
arquivos_parquet = glob.glob(os.path.join(CAMINHO, "*.parquet"))

dfs = {}  # dicionário para armazenar cada dataframe

for arquivo in arquivos_parquet:
    nome = os.path.basename(arquivo).replace(".parquet", "")
    dfs[nome] = pd.read_parquet(arquivo)
    print(f"Carregado: {nome}  →  {dfs[nome].shape}")

# DataFrames individuais
df_164 = dfs["df_164"]
df_trkv = dfs["df_trkv"]
df_WCM = dfs["df_WCM"]
df_z369 = dfs["df_z369"]
df_z851 = dfs["df_z851"]
df_z1568 = dfs["df_z1568"]

# =============================
# funções Gerais
# =============================


def salvar_parquet(df, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path, index=False, engine="pyarrow")


def salvar_tudo_threadpool(dfs, paths):
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(salvar_parquet, df, path)
            for df, path in zip(dfs, paths)
        ]

        # Espera todas concluírem
        for future in futures:
            future.result()


def busca_dados(vagao):
    def busca_z1568(vagao):
        # Conexão com o MongoDB
        vagao = int(vagao)
        client = MongoClient(
            MONGO_URI)

        # Definição do filtro
        filter = {}

        # Consulta
        cursor = client[DB_NAME]['z1568_Liberacoes_Retencoes_full'].find(
            filter)

        # Converter o cursor em lista e depois em DataFrame
        df = pd.DataFrame(list(cursor))

        # (Opcional) Remover a coluna _id, se não for necessária
        if '_id' in df.columns:
            df.drop('_id', axis=1, inplace=True)

        return df

    def busca_z851(vagao):
        # Conexão com o MongoDB
        vagao = int(vagao)
        client = MongoClient(
            MONGO_URI)

        # Definição do filtro
        filter = {}

        # Consulta
        cursor = client[DB_NAME]['CadastroVagoes_full'].find(filter)

        # Converter o cursor em lista e depois em DataFrame
        df = pd.DataFrame(list(cursor))

        # (Opcional) Remover a coluna _id, se não for necessária
        if '_id' in df.columns:
            df.drop('_id', axis=1, inplace=True)

        return df

    def busca_wcm(vagao):
        vagao = int(vagao)
        from datetime import datetime, timedelta
        print("Buscando WCM...")
        df_WCM = pd.read_parquet("./temp/df_WCM.parquet")

        # df_WCM['json_trem_TrainTime'] = df_WCM.to_datetime(df['json_trem_TrainTime'], errors='coerce')
        # data_mais_recente = df['sua_coluna'].max()

        df_WCM['json_trem_TrainTime_dt'] = pd.to_datetime(
            df_WCM['json_trem_TrainTime'],  errors='coerce')
        data_mais_recente = df_WCM['json_trem_TrainTime_dt'].max()

        print(data_mais_recente)

        # Conexão com o MongoDB
        client = MongoClient(
            MONGO_URI)

        data_limite = data_mais_recente

        pipeline = [
            # 1️⃣ Filtra pelo timestamp dos últimos 7 dias
            {
                "$match": {
                    "timestamp": {"$gte": data_limite}
                }
            },

            # 2️⃣ Mantém apenas o json_documents
            {
                "$project": {
                    "json_documents": 1,
                    "_id": 0
                }
            },

            # 3️⃣ Explode os documentos internos
            {
                "$unwind": "$json_documents"
            },

            # 4️⃣ Filtra os que possuem identificação de veículo não vazia
            {
                "$match": {
                    "json_documents.json_Identificação do veículo": {
                        "$exists": True,
                        "$ne": ""
                    }
                }
            }
        ]

        # Executa a agregação
        result = client[DB_NAME]['WCM'].aggregate(pipeline)

        # Converte o resultado em DataFrame
        df = pd.DataFrame(list(result))

        # Se quiser expandir o dicionário 'json_documents' em colunas separadas:
        if not df.empty and 'json_documents' in df.columns:
            df = pd.json_normalize(df['json_documents'])

        df_final = pd.concat([df_WCM, df], ignore_index=True).drop_duplicates()

        return df_final

    def busca_z369(vagao):
        # Conexão com o MongoDB
        client = MongoClient(
            MONGO_URI)

        vagao_str = str(vagao)

        # Definição do filtro
        filter = {"STATUS": "MSPN"}

        # Consulta
        cursor = client[DB_NAME]['z369_trated'].find(filter)

        # Converter o cursor em lista e depois em DataFrame
        df = pd.DataFrame(list(cursor))

        # (Opcional) Remover a coluna _id, se não for necessária
        if '_id' in df.columns:
            df.drop('_id', axis=1, inplace=True)

        return df

    def busca_TRKV(vagao):
        # Conexão com o MongoDB
        print("Buscando TRKV...")
        df_trkv = pd.read_parquet("./temp/df_trkv.parquet")

        data_mais_recente = df_trkv['data_sincronizacao'].max()
        print(data_mais_recente)

        vagao = int(vagao)
        client = MongoClient(MONGO_URI)

        # Definição do filtro
        filter = {'CarIDNumber': {'$ne': 0},
                  "data_sincronizacao": {"$gte": data_mais_recente}}
        # filter = { }

        # Consulta
        cursor = client[DB_NAME]['TRKV_treated'].find(filter)

        # Converter o cursor em lista e depois em DataFrame
        df = pd.DataFrame(list(cursor))

        # (Opcional) Remover a coluna _id, se não for necessária
        if '_id' in df.columns:
            df.drop('_id', axis=1, inplace=True)

        df_final = pd.concat(
            [df_trkv, df], ignore_index=True).drop_duplicates()

        return df_final

    def busca_Tela164(vagao):
        from pymongo import MongoClient
        import pandas as pd

        # Garantir que o vagao é string (Mongo armazena como string)
        vagao = str(vagao)

        # Conexão com o MongoDB
        client = MongoClient(MONGO_URI)

        # Filtro usando o parâmetro recebido
        filter_query = {}

        # Consulta com limit = 1
        cursor = client[DB_NAME]['tela164_full'].find(filter_query, limit=1)

        # Converter cursor para DataFrame
        df = pd.DataFrame(list(cursor))

        # Remover coluna _id se existir
        if '_id' in df.columns:
            df.drop('_id', axis=1, inplace=True)

        return df

    def busca_SAT_TAREFAS_full(vagao):
        from pymongo import MongoClient
        import pandas as pd

        # Garantir que o vagao é string (Mongo armazena como string)
        vagao = str(vagao)

        # Conexão com o MongoDB
        client = MongoClient(MONGO_URI)

        # Filtro usando o parâmetro recebido
        filter_query = {'EQUNR': re.compile(f"{vagao}")}

        # Consulta com limit = 1
        cursor = client[DB_NAME]['SAT_TAREFAS_full'].find(
            filter_query)

        # Converter cursor para DataFrame
        df = pd.DataFrame(list(cursor))

        # Remover coluna _id se existir
        if '_id' in df.columns:
            df.drop('_id', axis=1, inplace=True)

        return df

    def medir_tempo(func, *args, **kwargs):
        inicio = time.time()
        resultado = func(*args, **kwargs)
        fim = time.time()
        print(f"{func.__name__} executou em {fim - inicio:.2f} segundos")
        return resultado

    def exec_parallel(vagao):
        funcoes = [
            busca_wcm,
            busca_z369,
            busca_TRKV,
            busca_z851,
            busca_z1568,
            busca_Tela164
        ]

        resultados = {}

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(medir_tempo, f, vagao): f.__name__
                for f in funcoes
            }

            for future in as_completed(futures):
                nome = futures[future]
                try:
                    resultados[nome] = future.result()
                except Exception as e:
                    print(f"Erro na função {nome}: {e}")
                    resultados[nome] = None

        return resultados

    result = exec_parallel(vagao)

    df_WCM = result["busca_wcm"]
    df_z369 = result["busca_z369"]
    df_trkv = result["busca_TRKV"]
    df_z851 = result["busca_z851"]
    df_z1568 = result["busca_z1568"]
    df_164 = result["busca_Tela164"]
    #

    print(len(df_WCM))
    print(len(df_z369))
    print(len(df_trkv))
    print(len(df_z851))
    print(len(df_z1568))
    print(len(df_164))

    # st.success("Função executada com sucesso!")

    return df_WCM, df_z369, df_trkv, df_z851, df_z1568, df_164


def exibir_data_mais_recente():
    # Conversões sem alterar as colunas originais
    dt_164 = pd.to_datetime(df_164['DT_CARGA'], errors='coerce')
    dt_trkv = pd.to_datetime(df_trkv['data_sincronizacao'], errors='coerce')
    dt_WCM = pd.to_datetime(df_WCM['json_trem_TrainTime'], errors='coerce')
    dt_z369 = pd.to_datetime(df_z369['dt_last_udate_trated'], errors='coerce')
    dt_z851 = pd.to_datetime(df_z851['Atualizacao'], errors='coerce')
    dt_z1568 = pd.to_datetime(df_z1568['dt_fim_trated'], errors='coerce')

    # Datas mais recentes
    data_mais_recente_164 = dt_164.max()
    data_mais_recente_trkv = dt_trkv.max()
    data_mais_recente_WCM = dt_WCM.max()
    data_mais_recente_z369 = dt_z369.max()
    data_mais_recente_z851 = dt_z851.max()
    data_mais_recente_z1568 = dt_z1568.max()

    print("164:", data_mais_recente_164)
    print("TRKV:", data_mais_recente_trkv)
    print("WCM:", data_mais_recente_WCM)
    print("Z369:", data_mais_recente_z369)
    print("Z851:", data_mais_recente_z851)
    print("Z1568:", data_mais_recente_z1568)
    st.markdown("### Datas Mais Recentes nas Bases")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("164", str(data_mais_recente_164.date()))

    with col2:
        st.metric("TRKV", str(data_mais_recente_trkv.date()))

    with col3:
        st.metric("WCM", str(data_mais_recente_WCM.date()))

    with col4:
        st.metric("Z369", str(data_mais_recente_z369.date()))

    with col5:
        st.metric("Z851", str(data_mais_recente_z851.date()))

    with col6:
        st.metric("Z1568", str(data_mais_recente_z1568.date()))


# =============================
# funções de tratamento e concatenação
# =============================


def concatenar_dados_trkv_z851(df_z851, df_trkv):

    df_trkv["max_valor"] = df_trkv[["A#L_1", "A#L_2", "A#R_1",
                                    "A#R_2", "B#L_1", "B#L_2", "B#R_1", "B#R_2"]].max(axis=1)
    df_trkv_filtred = df_trkv[["CarIDInitial",
                               "CarIDNumber", "timestr", "max_valor"]]

    df_trkv_filtred = df_trkv_filtred[df_trkv_filtred["CarIDInitial"].notna()]
    df_trkv_filtred = df_trkv_filtred[df_trkv_filtred["max_valor"].notna()]
    df_trkv_filtred['timestr'] = pd.to_datetime(
        df_trkv_filtred['timestr'], format="%d/%m/%Y %H:%M:%S", errors='coerce')
    df_trkv_filtred['key'] = df_trkv_filtred['CarIDNumber'].astype(int)

    df_z851['key'] = df_z851['EQUNR'].str.replace(
        r'[^0-9]', '', regex=True).astype(int)
    df1 = df_z851
    df2 = df_trkv_filtred

    # 1. Filtra apenas passagens com medição não nula
    df2_filtrado = df2[df2['max_valor'].notnull()].copy()

    # 2. Ordena por equipamento e data (da mais recente para a mais antiga)
    df2_filtrado = df2_filtrado.sort_values(
        ['key', 'timestr'], ascending=[True, True])

    # ============================================================
    # A) PEGAR A ÚLTIMA MEDIÇÃO E A DATA DA ÚLTIMA MEDIÇÃO
    # ============================================================

    # Ordena por data DESC dentro da chave
    df2_desc = df2_filtrado.sort_values(
        ['key', 'timestr'], ascending=[True, False])

    # Pega a última linha por equipamento
    df_last = df2_desc.groupby('key').first().reset_index()

    df_last.rename(columns={
        'max_valor': 'ultima_medicao',
        'timestr': 'data_ultima_medicao'
    }, inplace=True)

    # ============================================================
    # B) PEGAR A MAIOR MEDIÇÃO ENTRE AS 3 ÚLTIMAS PASSAGENS
    # ============================================================

    # Pega rank das 3 últimas (já está ordenado ascendente)
    df2_filtrado['rank'] = df2_filtrado.groupby(
        'key')['timestr'].rank(method='first', ascending=False)

    df_top3 = df2_filtrado[df2_filtrado['rank'] <= 3]

    df_max = df_top3.groupby('key')['max_valor'].max().reset_index()
    df_max.rename(columns={'max_valor': 'max_medicao_ultimas_3'}, inplace=True)

    # ============================================================
    # C) MERGE FINAL
    # ============================================================

    df_final = df1.merge(df_max, on='key', how='left') \
        .merge(df_last[['key', 'ultima_medicao', 'data_ultima_medicao']],
               on='key', how='left')

    # df_final = df_final[["EQUNR", "MODELO", "STATUS", "DATA_DE_FABRICACAO_trated", "DATA_GARANTIA_trated", "ULTIMA_RG",
    #                      "KM_RODADO_DESDE_ULTIMA_RG", "max_medicao_ultimas_3", "ultima_medicao", "data_ultima_medicao", "key"]]

    df_tratado = df_final.rename(columns={
        'max_medicao_ultimas_3': 'TRKV_max_medicao_ultimas_3',
        'ultima_medicao': 'TRKV_ultima_medicao',
        'data_ultima_medicao': 'TRKV_last_timestamp'
    })

    return df_tratado


def tratar_WCM(df_WCM):

    # Garantir datetime
    df_WCM['json_trem_TrainTime'] = pd.to_datetime(
        df_WCM['json_trem_TrainTime'], errors='coerce'
    )

    # Criar coluna somente com a data
    df_WCM['Data'] = df_WCM['json_trem_TrainTime'].dt.date

    # Agrupamento por veículo + data
    df_WCM_max = (
        df_WCM.groupby(
            ['json_Identificação do veículo', 'Data'],
            as_index=False
        )['json_Força de pico de impacto da roda (kN)']
        .max()
        .rename(columns={
            'json_Força de pico de impacto da roda (kN)': 'Maior_Impacto_kN'
        })
        .sort_values(by=['json_Identificação do veículo', 'Data'])
    )
    df_WCM_max['key'] = df_WCM_max['json_Identificação do veículo'].str.split(
    ).str[-1].astype(int)

    return df_WCM_max


def concatenar_dados_new1_wcm_trated(df_new1, wcm_trated):

    wcm_trated_filtred = wcm_trated[wcm_trated["json_Identificação do veículo"].notna(
    )]
    wcm_trated_filtred = wcm_trated_filtred[wcm_trated_filtred["Maior_Impacto_kN"].notna(
    )]
    # wcm_trated_filtred['Data'] = pd.to_datetime(wcm_trated_filtred['Data'], format="%d/%m/%Y %H:%M:%S", errors='coerce')
    # wcm_trated_filtred['key'] = wcm_trated_filtred['key'].astype(int)

    df1 = df_new1
    df2 = wcm_trated_filtred

    # 1. Filtra apenas passagens com medição não nula
    df2_filtrado = df2[df2["Maior_Impacto_kN"].notnull()].copy()

    # 2. Ordena por equipamento e data (da mais recente para a mais antiga)
    df2_filtrado = df2_filtrado.sort_values(
        ['key', 'Data'], ascending=[True, True])

    # ============================================================
    # A) PEGAR A ÚLTIMA MEDIÇÃO E A DATA DA ÚLTIMA MEDIÇÃO
    # ============================================================

    # Ordena por data DESC dentro da chave
    df2_desc = df2_filtrado.sort_values(
        ['key', 'Data'], ascending=[True, False])

    # Pega a última linha por equipamento
    df_last = df2_desc.groupby('key').first().reset_index()

    df_last.rename(columns={
        'Maior_Impacto_kN': 'ultima_medicao',
        'Data': 'data_ultima_medicao'
    }, inplace=True)

    # ============================================================
    # B) PEGAR A MAIOR MEDIÇÃO ENTRE AS 3 ÚLTIMAS PASSAGENS
    # ============================================================

    # Pega rank das 3 últimas (já está ordenado ascendente)
    df2_filtrado['rank'] = df2_filtrado.groupby(
        'key')['Data'].rank(method='first', ascending=False)

    df_top3 = df2_filtrado[df2_filtrado['rank'] <= 3]

    df_max = df_top3.groupby('key')['Maior_Impacto_kN'].max().reset_index()
    df_max.rename(
        columns={'Maior_Impacto_kN': 'max_medicao_ultimas_3'}, inplace=True)

    # ============================================================
    # C) MERGE FINAL
    # ============================================================

    df_final = df1.merge(df_max, on='key', how='left') \
        .merge(df_last[['key', 'ultima_medicao', 'data_ultima_medicao']],
               on='key', how='left')
    df_final['VAGAO'] = df_final['EQUNR']
    df_final = df_final[["EQUNR", "VAGAO", "MODELO", "STATUS", "DATA_DE_FABRICACAO_trated", "DATA_GARANTIA_trated", "ULTIMA_RG",
                         "KM_RODADO_DESDE_ULTIMA_RG", "max_medicao_ultimas_3", "ultima_medicao", "data_ultima_medicao", "key"]]

    df_tratado = df_final.rename(columns={
        'max_medicao_ultimas_3': 'WCM_max_medicao_ultimas_3',
        'ultima_medicao': 'WCM_ultima_medicao',
        'data_ultima_medicao': 'WCM_last_timestamp'
    })

    return df_tratado


wcm_trated = tratar_WCM(df_WCM)
df_new1 = concatenar_dados_trkv_z851(df_z851, df_trkv)
df_new2 = concatenar_dados_new1_wcm_trated(df_new1, wcm_trated)


df_base_concatenada = df_new2

# =====================================================
# TELA PRINCIPAL
# =====================================================

st.title("📝Resumo Vagões")
st.write("---")
exibir_data_mais_recente()
st.write("---")

if st.button("🔄 Atualizar dados (pode demorar um pouco)"):
    with st.spinner("Atualizado bases ... Aguarde..."):
        df_WCM, df_z369, df_trkv, df_z851, df_z1568, df_164 = busca_dados(0)
        print(df_WCM.shape, df_z369.shape, df_trkv.shape,
              df_z851.shape, df_z1568.shape, df_164.shape)
        print("Iniciando salvamento...")
        dfs = [df_WCM, df_z369, df_trkv, df_z851, df_z1568, df_164]

        paths = [
            "./temp/df_WCM.parquet",
            "./temp/df_z369.parquet",
            "./temp/df_trkv.parquet",
            "./temp/df_z851.parquet",
            "./temp/df_z1568.parquet",
            "./temp/df_164.parquet"
        ]

        salvar_tudo_threadpool(dfs, paths)

    st.success("Arquivos salvos com sucesso! ✅")

# =============================
# Filtro – EQUNR
# =============================s
lista_valores = sorted(df_base_concatenada["EQUNR"].unique())

filtro_equnr = st.selectbox(
    "Filtrar por EQUNR:",
    options=["Todos"] + lista_valores,
    index=0
)
# Aplicar filtro
if filtro_equnr != "Todos":
    df_filtrado = df_base_concatenada[df_base_concatenada["EQUNR"]
                                      == filtro_equnr]
else:
    df_filtrado = df_base_concatenada


def create_EQUNR_link(equnr):
    """Cria link com o valor da EQUNR"""
    return f"/Consulta_Master?eqnr={equnr}"


# Cria DataFrame com link
df_filtrado_com_link = df_filtrado.copy()
df_filtrado_com_link['EQUNR_Link'] = df_filtrado_com_link['EQUNR'].apply(
    create_EQUNR_link)

# Reordena: link primeiro, esconde EQUNR original
colunas = ['EQUNR_Link'] + [col for col in df_filtrado_com_link.columns if col !=
                            'EQUNR' and col != 'EQUNR_Link']
df_display = df_filtrado_com_link[colunas]

st.markdown("### Dados Concatenados e Tratados")
st.dataframe(
    df_display,
    use_container_width=True,
    hide_index=True,
    height=600,
    column_config={
        "EQUNR_Link": st.column_config.LinkColumn(
            "Abrir Resumo",
            help="Clique para abrir detalhes do vagão",
            display_text="📝 Resumo Vagão"
        ),
        # Esconde se ainda aparecer
        "EQUNR": st.column_config.Column(width="none")
    }
)

st.write(f"Total de registros: **{df_filtrado.shape[0]}**")
