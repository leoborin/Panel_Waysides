# app.py
import os
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
import pandas as pd
import plotly.express as px
from numpy.random import default_rng as rng
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings("ignore")
# from streamlit_plotly_events import plotly_events


# st.set_page_config(layout="wide")
# st.title("Dashboard com Crossfilter (Plotly)")


# @st.cache_data
# def load_data():
#     # Exemplo: dataset sintético
#     df = pd.DataFrame({
#         "categoria": ["A", "A", "B", "B", "C", "C"] * 5,
#         "data": pd.date_range("2024-01-01", periods=30, freq="D"),
#         "valor": (pd.Series(range(30))*3.5 + 10).sample(30, random_state=42).values
#     })
#     return df


# df = load_data()

# # Estado de filtro: categorias selecionadas
# if "cats" not in st.session_state:
#     st.session_state.cats = []

# col1, col2 = st.columns([1, 2])

# with col1:
#     df_agg = df.groupby("categoria", as_index=False)[
#         "valor"].sum().sort_values("valor", ascending=False)
#     fig_bar = px.bar(df_agg, x="categoria", y="valor",
#                      title="Clique na barra para filtrar")
#     # fig_bar.update_layout(margin=dict(l=10,r=10,t=40,b=10))

#     # Captura eventos de clique/seleção
#     points = plotly_events(
#         fig_bar,
#         click_event=True,
#         select_event=True,
#         hover_event=False,          # desnecessário
#         override_height=400,
#         override_width="100%"
#     )

#     # Extrai categorias clicadas/selecionadas
#     selected_cats = [p.get("x") for p in points] if points else []

#     # Atualiza o filtro (toggle simples)
#     if selected_cats:
#         st.session_state.cats = selected_cats

#     # Botão para limpar filtro
#     if st.button("Limpar filtro", type="secondary"):
#         st.session_state.cats = []

#     # Mostra o estado atual
#     st.caption(
#         f"Filtro categorias: {st.session_state.cats or '— (sem filtro)'}")

# with col2:
#     # Aplica o filtro nas demais views
#     df_f = df[df["categoria"].isin(
#         st.session_state.cats)] if st.session_state.cats else df.copy()

#     # Tabela filtrada
#     st.subheader("Tabela filtrada")
#     st.dataframe(df_f.sort_values(["categoria", "data"]),
#                  use_container_width=True, hide_index=True)

#     # Outro gráfico filtrado (ex.: série temporal)
#     st.subheader("Série temporal filtrada")
#     fig_line = px.line(df_f, x="data", y="valor", color="categoria")
#     if (st.session_state.cats != [] and st.session_state.cats[0] == 'C'):
#         st.session_state.cats = []
#         st.switch_page("pages/1-📊Consulta Master.py")

#         # pg.run()
#     if (st.session_state.cats != [] and st.session_state.cats[0] == 'B'):
#         st.session_state.cats = []
#         st.switch_page("pages/2 - 🤖Chat Bot.py")

# df2 = pd.DataFrame(
#     rng(0).standard_normal((12, 5)), columns=["a", "b", "c", "d", "e"]
# )
# event = st.dataframe(
#     df2,
#     key="data",
#     on_select="rerun",
#     selection_mode=["multi-row", "multi-column", "multi-cell"]
# )

# event.selection

# print(event.selection.cells[0])
# st.write(df2.loc[event.selection.cells[0][0], event.selection.cells[0][1]])


# --------------------------
# Função para salvar parquet
# --------------------------
MONGO_URI = "mongodb+srv://int_dados:e7bUe2bXbKDu3Xzr@rumo-dev2.hbdcrld.mongodb.net/?authSource=admin"
DB_NAME = "supervisorio"


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
        # Conexão com o MongoDB
        client = MongoClient(
            MONGO_URI)
        vagao_str = str(vagao)
        # Pipeline de agregação
        pipeline = [
            {
                '$match': {
                    'json_documents.json_Identificação do veículo': {'$ne': ""}
                }
            },
            {
                '$project': {
                    'json_documents': 1,
                    '_id': 0
                }
            },
            {
                '$unwind': '$json_documents'
            },
            {
                '$match': {
                    'json_documents.json_Identificação do veículo': {'$ne': ""}
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

        return df

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
        vagao = int(vagao)
        client = MongoClient(
            MONGO_URI)

        # Definição do filtro
        filter = {'CarIDNumber': {'$ne': 0}}
        # filter = { }

        # Consulta
        cursor = client[DB_NAME]['TRKV_treated'].find(filter)

        # Converter o cursor em lista e depois em DataFrame
        df = pd.DataFrame(list(cursor))

        # (Opcional) Remover a coluna _id, se não for necessária
        if '_id' in df.columns:
            df.drop('_id', axis=1, inplace=True)

        return df

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

    st.success("Função executada com sucesso!")

    return df_WCM, df_z369, df_trkv, df_z851, df_z1568, df_164

# --------------------------
# BOTÃO NO STREAMLIT
# --------------------------


st.title("Salvar DataFrames em Parquet")

if st.button("💾 Salvar arquivos Parquet"):
    with st.spinner("Salvando arquivos... Aguarde..."):
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
# Carregar Parquet
# =============================
df = pd.read_parquet("./temp/df_zCadVagoes_resumos.parquet")
st.title("Consulta de Dados")

# =============================
# Filtro – EQUNR
# =============================s
lista_valores = sorted(df["EQUNR"].unique())

filtro_equnr = st.selectbox(
    "Filtrar por EQUNR:",
    options=["Todos"] + lista_valores,
    index=0
)

# Aplicar filtro
if filtro_equnr != "Todos":
    df_filtrado = df[df["EQUNR"] == filtro_equnr]
else:
    df_filtrado = df

# =============================
# Exibir tabela
# =============================
st.dataframe(
    df_filtrado,
    use_container_width=True,
    hide_index=True,
    height=600
)

st.write(f"Total de registros: **{df_filtrado.shape[0]}**")
