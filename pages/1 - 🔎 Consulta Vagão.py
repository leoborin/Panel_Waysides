
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
import json
warnings.filterwarnings("ignore")


eqnr = st.query_params.get("eqnr")

# st.write(f"EQNR: '{eqnr}'")

# st.caption(f"🔗 [Voltar à lista principal](/1_Dados_Concatenados)")
with open("css/style.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Configurações MongoDB
MONGO_URI = st.secrets.database_dev.MONGO_URI
DB_NAME = st.secrets.database_dev.DB_NAME
MONGO_URI_PRD = st.secrets.database_prod.MONGO_URI_PRD
DB_NAME_PRD = st.secrets.database_prod.DB_NAME_PRD
cof_Outlier = 0.2

# logo = Image.open("assets/logo.png")
# st.logo(logo, size='large')
# col_logo, col_titulo = st.columns([1, 7])
# with col_logo:
#     st.image("assets/vg666.png", width=100)
# with col_titulo:
#     st.title("Consulta Completa Vagões v0 - Visão Micro")

# st.set_page_config(layout="wide")
# # st.write("POC Testes")

#--------------------------------------------------------------------------------
## Configuração da página e cabeçalho
#--------------------------------------------------------------------------------
st.set_page_config(
    page_title="Saúde da Frota de Vagões",
    page_icon="🚆",
    layout="wide"
)

# Paleta de Cores e CSS (inalterado)
PRIMARY = "#0D3B66"
ACCENT = "#5EA9DD"
CARD_BG = "#F5F8FC"
BORDER = "#DEE6F1"
SUCCESS = "#7FE06C"
WARNING = "#F39C12"
DANGER = "#E74C3C"
TEXT = "#1F2D3D"
MUTED = "#6C7C8C"

st.markdown(f"""
<style>
.topbar {{
  background: {PRIMARY};
  color: #fff;
  border-radius: 12px;
  padding: 14px 18px;
  display: grid;
  grid-template-columns: 1.6fr 1fr 0.6fr;
  align-items: center;
}}
.topbar .title {{
  font-weight: 800;
  font-size: 20px;
}}
.topbar .menu {{
  display: flex;
  gap: 12px;
  justify-content: center;
}}
.topbar .menu .pill {{
  
background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.25);
  color: #fff;
  padding: 10px 18px;       /* Mais espaço interno */
  border-radius: 6px;       /* Cantos levemente arredondados */
  font-size: 14px;          /* Texto maior */
  font-weight: 600;         /* Texto mais forte */
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 160px;         /* Evita texto quebrado */
  justify-content: center;  /* Centraliza ícone e texto */
}}
.topbar .brand {{
  justify-self: end;
  font-weight: 900;
  font-size: 22px;
}}
.section-box {{
  border: 1px solid {BORDER};
  background: #fff;
  border-radius: 12px;
  padding: 12px;
}}
.section-title {{
  font-weight: 800; color: {TEXT}; margin-bottom: 8px;
}}
.caption {{
  color: {MUTED};
  font-size: 12px;
  text-align: center;
  margin-top: 6px;
}}


</style>
""", unsafe_allow_html=True)

st.markdown(
    """
    <style>
        .center-vertical {
            display: flex;
            flex-direction: column;
            justify-content: center;
            height: 100%;
        }
    </style>
    """,
    unsafe_allow_html=True
)

## Topbar
st.markdown("""
<div class="topbar">
  <div class="title">SAÚDE DA FROTA DE VAGÕES</div>
  <div class="menu">
    <div class="pill">🧭 Visão executiva</div>
    <div class="pill">⚠️ Previsões & Riscos</div>
    <div class="pill">🧩 Saúde dos componentes</div>
    <div class="pill">📓 Detalhamento por vagão</div>      
  </div>
  <div class="brand">
    <img src="assets/logoneg.png" alt="Rumo" />
  </div>
</div>
""", unsafe_allow_html=True)

st.write("")

st.subheader("Detalhamento do vagão")

# functions Begin --------------------------------------------------
# main def

# df_trkv_trated, r2, mae, rmse = regrecao()


def tratar_outliers_trkv(df):
    """
    Remove medições anômalas com base nas 3 últimas medições por key.

    - Valor é outlier se:
        valor > max_3 * 1.30
        valor < min_3 * 0.70
    """
    df = df.fillna(0)                     
    df["key"] = df["CarIDNumber"].astype(int)
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],  errors="coerce")
    df = df.sort_values(["key", "timestamp"])

    # Cálculo da força máxima entre os 8 sensores
    sensores = ["A#L_1", "A#L_2", "A#R_1", "A#R_2",
                "B#L_1", "B#L_2", "B#R_1", "B#R_2"]

    df["max_valor"] = df[sensores].max(axis=1)

    
    df["min_3"] = (
        df.groupby("key")["max_valor"]
        .rolling(3).min().shift(1)
        .reset_index(level=0, drop=True)
    )

    df["max_3"] = (
        df.groupby("key")["max_valor"]
        .rolling(3).max().shift(1)
        .reset_index(level=0, drop=True)
    )

    # Regras ±30%
    df["DESCARTAR"] = (
        (df["max_valor"] > df["max_3"] * (1+cof_Outlier)) |
        (df["max_valor"] < df["min_3"] * (1-cof_Outlier)) |
       ( df["max_valor"] == 0)
    )

    df["STATUS_out"] = df["DESCARTAR"].map(
        {True: "DESCARTAR", False: "OK"})
    return df


def busca_dados(vagao):

    def busca_versonota(vagao):
        try:
            vagao = int(vagao)
            client = MongoClient(MONGO_URI_PRD)

            # -----------------------------------------
            # 1) Filtro seguro (busca exata, não parcial)
            # -----------------------------------------

            filter = {'ATIVO_TL': re.compile(f"{vagao}")}

            cursor = client[DB_NAME_PRD]["SAP_verso_nota"].find(filter)

            # -----------------------------------------
            # 2) Converter cursor → DataFrame
            # -----------------------------------------
            df = pd.DataFrame(list(cursor))

            # Se cursor vazio → retorna df vazio
            if df.empty:
                print("versonota: Nenhum registro encontrado → retornando df vazio")
                return pd.DataFrame()

            # -----------------------------------------
            # 4) Remover _id se existir
            # -----------------------------------------
            df.drop(columns=["_id"], errors="ignore", inplace=True)

            return df

        except Exception as e:
            # Captura qualquer erro e retorna df vazio
            print(f"Erro ao consultar versonota: {e}")
            return pd.DataFrame()

    def busca_censo(vagao):
        try:
            vagao = int(vagao)
            client = MongoClient(MONGO_URI_PRD)

            # -----------------------------------------
            # 1) Filtro seguro (busca exata, não parcial)
            # -----------------------------------------

            filter = {'Equipamento': re.compile(f"{vagao}")}

            cursor = client[DB_NAME_PRD]["SAP_censo_trated"].find(filter)

            # -----------------------------------------
            # 2) Converter cursor → DataFrame
            # -----------------------------------------
            df = pd.DataFrame(list(cursor))

            # Se cursor vazio → retorna df vazio
            if df.empty:
                print("censo: Nenhum registro encontrado → retornando df vazio")
                return pd.DataFrame()

            # -----------------------------------------
            # 4) Remover _id se existir
            # -----------------------------------------
            df.drop(columns=["_id"], errors="ignore", inplace=True)

            return df

        except Exception as e:
            # Captura qualquer erro e retorna df vazio
            print(f"Erro ao consultar censo: {e}")
            return pd.DataFrame()

    def busca_TBOGI(vagao):
        try:
            vagao = int(vagao)
            client = MongoClient(MONGO_URI)

            # -----------------------------------------
            # 1) Filtro seguro (busca exata, não parcial)
            # -----------------------------------------
            filter = {'car_num': re.compile(f"{vagao}")}
            cursor = client[DB_NAME]["tbogi_treated"].find(filter)

            # -----------------------------------------
            # 2) Converter cursor → DataFrame
            # -----------------------------------------
            df = pd.DataFrame(list(cursor))

            # Se cursor vazio → retorna df vazio
            if df.empty:
                print("TBOGI: Nenhum registro encontrado → retornando df vazio")
                return pd.DataFrame()

            # -----------------------------------------
            # 3) Criar coluna valor_mod_pd (proteção caso 'tp' não exista)
            # -----------------------------------------
            if "tp" in df.columns:
                df["valor_mod_pd"] = df["tp"].abs()
            else:
                print(
                    "TBOGI: coluna 'tp' não encontrada — adicionando valor_mod_pd = NaN")
                df["valor_mod_pd"] = np.nan

            # -----------------------------------------
            # 4) Remover _id se existir
            # -----------------------------------------
            df.drop(columns=["_id"], errors="ignore", inplace=True)

            return df

        except Exception as e:
            # Captura qualquer erro e retorna df vazio
            print(f"Erro ao consultar TBOGI: {e}")
            return pd.DataFrame()

    def busca_z1568(vagao):
        # Conexão com o MongoDB
        vagao = int(vagao)
        client = MongoClient(
            MONGO_URI_PRD)

        # Definição do filtro
        filter = {'ATIVO': re.compile(f"{vagao}")}

        # Consulta
        cursor = client[DB_NAME_PRD]['SAP_z1568_LiberacoesRetencoes'].find(
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
            MONGO_URI_PRD)

        # Definição do filtro
        filter = {'EQUNR': re.compile(f"{vagao}")}

        # Consulta
        cursor = client[DB_NAME_PRD]['SAP_z851_CadastroVagoes'].find(filter)

        # Converter o cursor em lista e depois em DataFrame
        df = pd.DataFrame(list(cursor))

        # (Opcional) Remover a coluna _id, se não for necessária
        if '_id' in df.columns:
            df.drop('_id', axis=1, inplace=True)

        return df

    def busca_wcm(vagao):
        try:
            # Conexão com o MongoDB
            client = MongoClient(
                MONGO_URI_PRD)
            vagao_str = str(vagao)
            # Pipeline de agregação
            pipeline = [
                {
                    "$match": {
                        "json_documents.json_Identificação do veículo": {
                            "$regex": vagao_str,
                            # ignorar maiúsc/minúsc (opcional)
                            "$options": "i"
                        }
                    }
                },
                {
                    "$project": {
                        "json_documents": 1,
                        "_id": 0
                    }
                },
                {
                    "$unwind": "$json_documents"
                },
                {
                    "$match": {
                        "json_documents.json_Identificação do veículo": {
                            "$regex": vagao_str,
                            # ignorar maiúsc/minúsc (opcional)
                            "$options": "i"
                        }
                    }
                }
            ]

            # Executa a agregação
            result = client[DB_NAME_PRD]['WCM'].aggregate(pipeline)

            # Converte o resultado em DataFrame
            df = pd.DataFrame(list(result))

            # Se quiser expandir o dicionário 'json_documents' em colunas separadas:
            if not df.empty and 'json_documents' in df.columns:
                df = pd.json_normalize(df['json_documents'])
        except Exception as e:
            print(f"Erro ao consultar WCM: {e}")
            df = pd.DataFrame()

        return df

    def busca_z369(vagao):
        try:
            # Conexão com o MongoDB
            client = MongoClient(
                MONGO_URI_PRD)

            vagao_str = str(vagao)

            # Definição do filtro
            filter = {"ATIVO": {"$regex": vagao_str}}

            # Consulta
            cursor = client[DB_NAME_PRD]['SAP_z369_notas'].find(filter)

            # Converter o cursor em lista e depois em DataFrame
            df = pd.DataFrame(list(cursor))

            # (Opcional) Remover a coluna _id, se não for necessária
            if '_id' in df.columns:
                df.drop('_id', axis=1, inplace=True)

            return df
        except Exception as e:
            print(f"Erro ao consultar z369: {e}")
            return pd.DataFrame()

    def busca_TRKV(vagao):
        try:
            # Conexão com o MongoDB
            vagao = int(vagao)
            client = MongoClient(
                MONGO_URI_PRD)

            # Definição do filtro
            filter = {'CarIDNumber': vagao}

            # Consulta
            cursor = client[DB_NAME_PRD]['TRKV_treated'].find(filter)

            # Converter o cursor em lista e depois em DataFrame
            df = pd.DataFrame(list(cursor))
            # print(df[['CarIDNumber', 'timestamp']].head())

            # (Opcional) Remover a coluna _id, se não for necessária
            if '_id' in df.columns:
                df.drop('_id', axis=1, inplace=True)

            return df
        except Exception as e:
            print(f"Erro ao consultar TRKV: {e}")
            return pd.DataFrame()

    def busca_Tela164(vagao):
        try:

            # Garantir que o vagao é string (Mongo armazena como string)
            vagao = str(vagao)

            # Conexão com o MongoDB
            client = MongoClient(MONGO_URI_PRD)

            # Filtro usando o parâmetro recebido
            filter_query = {'VAGAO': re.compile(f"{vagao}")}

            # Consulta com limit = 1
            cursor = client[DB_NAME_PRD]['Translogic_Tela_164_Foto'].find(
                filter_query, limit=1)

            # Converter cursor para DataFrame
            df = pd.DataFrame(list(cursor))

            # Remover coluna _id se existir
            if '_id' in df.columns:
                df.drop('_id', axis=1, inplace=True)

            return df
        except Exception as e:
            print(f"Erro ao consultar Tela164: {e}")
            return pd.DataFrame()

    def busca_SAT_TAREFAS_full(vagao):
        try:
            from pymongo import MongoClient
            import pandas as pd

            # Garantir que o vagao é string (Mongo armazena como string)
            vagao = str(vagao)

            # Conexão com o MongoDB
            client = MongoClient(MONGO_URI_PRD)

            # Filtro usando o parâmetro recebido
            filter_query = {'EQUNR': re.compile(f"{vagao}")}

            # Consulta com limit = 1
            cursor = client[DB_NAME_PRD]['SAT_TAREFAS_full'].find(
                filter_query)

            # Converter cursor para DataFrame
            df = pd.DataFrame(list(cursor))

            # Remover coluna _id se existir
            if '_id' in df.columns:
                df.drop('_id', axis=1, inplace=True)

            return df
        except Exception as e:
            print(f"Erro ao consultar SAT_TAREFAS_full: {e}")
            return pd.DataFrame()

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
            busca_Tela164,
            busca_SAT_TAREFAS_full,
            busca_TBOGI,
            busca_censo,
            busca_versonota
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
    df_SAT_TAREFAS_full = result["busca_SAT_TAREFAS_full"]
    df_busca_TBOGI = result["busca_TBOGI"]
    df_censo = result["busca_censo"]
    df_versonota = result["busca_versonota"]

    print("df_WCM:", len(df_WCM))
    print("df_z369:", len(df_z369))
    # print("df_trkv:", len(df_trkv))
    print("df_z851:", len(df_z851))
    print("df_z1568:", len(df_z1568))
    print("df_164:", len(df_164))
    print("df_SAT_TAREFAS_full:", len(df_SAT_TAREFAS_full))
    print("df_busca_TBOGI:", len(df_busca_TBOGI))
    print("df_censo:", len(df_censo))
    print("df_versonota:", len(df_versonota))
    st.success("Função executada com sucesso!")

    return df_WCM, df_z369, df_trkv, df_z851, df_z1568, df_164, df_SAT_TAREFAS_full, df_busca_TBOGI, df_censo, df_versonota


def tratar_dfs(df_WCM, df_z369, df_trkv, df_busca_TBOGI):
    def tratar_tbogi(df_busca_TBOGI):
        df_resumo = (
            df_busca_TBOGI.groupby("timestamp_received", as_index=False)[
                "valor_mod_pd"]
            .max()
            .rename(columns={"valor_mod_pd": "max_valor_mod_pd"})
            .sort_values(by="timestamp_received")
        )
        return df_resumo

    try:
        df_TBOGI_trated = tratar_tbogi(df_busca_TBOGI)
    except Exception as e:
        print(f"Erro ao tratar df_TBOGI: {e}")
        df_TBOGI_trated = pd.DataFrame()

    def tratar_trkv(df_trkv):

        # print(df_trkv[['CarIDNumber', 'timestamp']].head())
        df_trkv = df_trkv.fillna(0)
        # Criar coluna Data
        df_trkv['Data'] = df_trkv['timestamp'].dt.date

        colunas_impacto = ["A#L_1", "A#L_2", "A#R_1", "A#R_2",
                           "B#L_1", "B#L_2", "B#R_1", "B#R_2"]

        #df_trkv["A#L_1"] = df_trkv["A#L_1"].map('{:.2f}'.format)
        #print("formato coluna")
        #print(df_trkv["A#L_1"])
        df_trkv[colunas_impacto] = df_trkv[colunas_impacto].replace(0, np.nan)

        df_trkv['Maior_Impacto_Linha'] = df_trkv[colunas_impacto].max(axis=1)

        if "STATUS_out" not in df_trkv.columns:
            df_trkv["STATUS_out"] = "OK"

        # 🔥 AGRUPAR POR key + Data (corrige seu problema)
        df_trkv_max = (
            df_trkv.groupby(["key", "Data"], as_index=False)
            .agg({
                "Maior_Impacto_Linha": "max",
                "STATUS_out": lambda x: "DESCARTAR" if "DESCARTAR" in x.values else "OK"
            })
            .rename(columns={"Maior_Impacto_Linha": "TRKV_MAX_Cunha"})
            .sort_values(by=["key", "Data"])
        )
        df_trkv_max = df_trkv_max.fillna(0)
        df_trkv_max["TRKV_MAX_Cunha"] = df_trkv_max["TRKV_MAX_Cunha"].round(2)

        return df_trkv_max[["key", "Data", "TRKV_MAX_Cunha", "STATUS_out"]]
    try:
        df_trkv_trated = tratar_trkv(df_trkv)
    except Exception as e:
        print(f"Erro ao tratar df_trkv: {e}")
        df_trkv_trated = pd.DataFrame()

    def tratar_WCM(df_WCM):
        # Garantir que o campo de tempo esteja em formato datetime
        df_WCM['json_trem_TrainTime'] = pd.to_datetime(
            df_WCM['json_trem_TrainTime'])

        # Criar uma coluna apenas com a data (sem hora)
        df_WCM['Data'] = df_WCM['json_trem_TrainTime'].dt.date

        # Agrupar por dia e pegar o maior valor da força de impacto
        df_WCM_max = (
            df_WCM.groupby('Data', as_index=False)[
                'json_Força de pico de impacto da roda (kN)']
            .max()
            .rename(columns={'json_Força de pico de impacto da roda (kN)': 'Maior_Impacto_kN'})
            # ✅ organiza do mais antigo para o mais recente
            .sort_values(by='Data', ascending=True)
        )
        return df_WCM_max
    try:
        df_wcm_trated = tratar_WCM(df_WCM)
    except Exception as e:
        print(f"Erro ao tratar df_trkv: {e}")
        df_wcm_trated = pd.DataFrame()

    def tratar_z369(df_z369):

        # df_z369['timestamp'] = pd.to_datetime(df_z369['timestamp'])
        # df_z369['Data'] = df_z369['timestamp'].dt.date

        df_z369['Texto_Completo'] = (
            df_z369[['TEXTO', 'TEXTO AVARIA', 'TEXTO CAUSA']]
            .fillna('')  # substitui NaN por vazio
            .agg(' | '.join, axis=1)  # concatena linha a linha
            .str.strip(' | ')  # remove separador no fim se faltar campo
        )

        df_z369_trated = df_z369[['NOTA', 'ATIVO', 'TP NOTA', 'STATUS',
                                  'dt_abertura_trated', 'dt_fechamento_trated', 'Texto_Completo']]

        df_timeline_z369 = df_z369_trated.copy()

        df_timeline_z369 = df_timeline_z369.rename(columns={
            "NOTA": "Evento",
            "TP NOTA": "Tipo_Evento",
            "dt_abertura_trated": "INICIO",
            "dt_fechamento_trated": "FIM"
        })
        df_timeline_z369['Evento'] = "NOTA_" + \
            df_timeline_z369['Evento'].astype(str)

        return df_timeline_z369, df_z369_trated
    try:
        df_timeline_z369, df_z369_trated = tratar_z369(df_z369)
    except Exception as e:
        print(f"Erro ao tratar df_trkv: {e}")
        df_timeline_z369 = pd.DataFrame()
        df_z369_trated = pd.DataFrame()

    return df_trkv_trated, df_wcm_trated, df_timeline_z369, df_z369_trated, df_TBOGI_trated


def inserir_TBOGI_hist(df_TBOGI_trated):
    df_TBOGI_trated_histgeral = df_TBOGI_trated.copy()
    # #print(df_TBOGI_trated)
    # 1) Garantir datetime (com hora) na coluna timestamp_received
    df_TBOGI_trated_histgeral['INICIO'] = pd.to_datetime(
        df_TBOGI_trated_histgeral['timestamp_received'])
    df_TBOGI_trated_histgeral['Tipo_Evento'] = "Passagem TBOGI"
    # + \            df_TBOGI_trated_histgeral['timestamp_received'].astype(str)
    df_TBOGI_trated_histgeral['Evento'] = "TBOGI"

    df_TBOGI_trated_histgeral['Texto_Completo'] = "max_valor_mod_pd = " + \
        df_TBOGI_trated_histgeral['max_valor_mod_pd'].astype(str)

    df_TBOGI_trated_histgeral["timestamp_received"] = pd.to_datetime(
        df_TBOGI_trated_histgeral["timestamp_received"], format="%Y-%m-%d %H:%M")
    df_TBOGI_trated_histgeral["FIM"] = (
        df_TBOGI_trated_histgeral["timestamp_received"] +
        pd.to_timedelta(12, unit="h")
    )
    df_TBOGI_trated_histgeral['Tipo_Evento'] = "TBOGI"

    df_TBOGI_total = df_TBOGI_trated_histgeral[[
        'Evento', 'INICIO', 'FIM', 'Texto_Completo', 'Tipo_Evento']]

    return df_TBOGI_total


def inserir_wcm_hist(df_wcm_trated):
    df_wcm_trated_histgeral = df_wcm_trated.copy()
    # #print(df_wcm_trated)
    # 1) Garantir datetime (com hora) na coluna Data
    df_wcm_trated_histgeral['INICIO'] = pd.to_datetime(
        df_wcm_trated_histgeral['Data'])
    df_wcm_trated_histgeral['Tipo_Evento'] = "Passagem wcm"
    # + \            df_wcm_trated_histgeral['Data'].astype(str)
    df_wcm_trated_histgeral['Evento'] = "wcm"

    df_wcm_trated_histgeral['Texto_Completo'] = "Maior_Impacto_kN = " + \
        df_wcm_trated_histgeral['Maior_Impacto_kN'].astype(str)

    df_wcm_trated_histgeral["Data"] = pd.to_datetime(
        df_wcm_trated_histgeral["Data"], format="%Y-%m-%d %H:%M")
    df_wcm_trated_histgeral["FIM"] = (
        df_wcm_trated_histgeral["Data"] + pd.to_timedelta(12, unit="h")
    )
    df_wcm_trated_histgeral['Tipo_Evento'] = "WCM"

    df_wcm_total = df_wcm_trated_histgeral[[
        'Evento', 'INICIO', 'FIM', 'Texto_Completo', 'Tipo_Evento']]

    return df_wcm_total


def inserir_trkv_hist(df_trkv_trated):
    df_trkv_trated_histgeral = df_trkv_trated.copy()
    print("df_trkv_trated = com erro")
    # print(df_trkv_trated)
    # 1) Garantir datetime (com hora) na coluna Data
    df_trkv_trated_histgeral['INICIO'] = pd.to_datetime(
        df_trkv_trated_histgeral['Data'])
    df_trkv_trated_histgeral['Tipo_Evento'] = "Passagem trkv"
    # + \            df_trkv_trated_histgeral['Data'].astype(str)
    df_trkv_trated_histgeral['Evento'] = "trkv"

    df_trkv_trated_histgeral['Texto_Completo'] = "TRKV_MAX_Cunha = " + \
        df_trkv_trated_histgeral['TRKV_MAX_Cunha'].astype(str)

    df_trkv_trated_histgeral["Data"] = pd.to_datetime(
        df_trkv_trated_histgeral["Data"], format="%Y-%m-%d %H:%M")
    df_trkv_trated_histgeral["FIM"] = (
        df_trkv_trated_histgeral["Data"] + pd.to_timedelta(12, unit="h")
    )
    df_trkv_trated_histgeral['Tipo_Evento'] = "trkv"

    df_trkv_total = df_trkv_trated_histgeral[[
        'Evento', 'INICIO', 'FIM', 'Texto_Completo', 'Tipo_Evento']]

    return df_trkv_total


def inserir_z1568(df_z1568):

    # df_z1568['dt_inicio_trated'] = pd.to_datetime(
    #     df_z1568['dt_inicio_trated'])
    # df_z1568['dt_inicio_trated'] = df_z1568['dt_inicio_trated'].dt.date

    # df_z1568['dt_fim_trated'] = pd.to_datetime(df_z1568['dt_fim_trated'])
    # df_z1568['dt_fim_trated'] = df_z1568['dt_fim_trated'].dt.date

    df_z1568['Texto_Completo'] = (
        df_z1568[['PMV', 'STATUS', 'GRUPO_AVARIA', 'TEXTO']]
        .fillna('')  # substitui NaN por vazio
        .agg(' | '.join, axis=1)  # concatena linha a linha
        .str.strip(' | ')  # remove separador no fim se faltar campo
    )

    df_z1568_trated = df_z1568[['Documento', 'ATIVO', 'ID_Manutecao',
                                'dt_inicio_trated', 'dt_fim_trated', 'Texto_Completo']]

    df_timeline_z1568 = df_z1568_trated.copy()

    df_timeline_z1568 = df_timeline_z1568.rename(columns={
        "Documento": "Evento",
        "ID_Manutecao": "Tipo_Evento",
        "dt_inicio_trated": "INICIO",
        "dt_fim_trated": "FIM"
    })
    df_timeline_z1568["Evento"] = "Doc_Retencao_" + \
        df_timeline_z1568["Evento"].astype(str)

    return df_timeline_z1568


def minha_funcao(texto):
    st.write(f"Você digitou: {texto}")


def tratar_entrada(codigo: str) -> str:
    # Mantém apenas dígitos
    apenas_numeros = "".join(filter(str.isdigit, codigo))

    # Remove zeros à esquerda
    sem_zeros = apenas_numeros.lstrip("0")

    # Garante que não retorne vazio (ex: "000HPT")
    return sem_zeros if sem_zeros else "0"


def busca_z851_se_existe(vagao):
        # Conexão com o MongoDB
        vagao = int(vagao)
        client = MongoClient(
            MONGO_URI_PRD)

        # Definição do filtro
        filter = {'EQUNR': re.compile(f"{vagao}")}

        # Consulta
        cursor1 = client[DB_NAME_PRD]['SAP_z851_CadastroVagoes'].find(filter)
        # Converter o cursor em lista e depois em DataFrame
        df = pd.DataFrame(list(cursor1))
        
        if df.empty:
            #st.write("VAZIO")
            return False
        elif  df['ELIMINADO'][0] == 'X':
                #st.write("ELIMINADO")
                return 'X'  
        else:
            #st.write("tem conteudo")
            return True
            
       

# functions End ----------------------------------------------------
# Tela -----------------------
# Campo de entrada de texto
st.container(height=50, border=False)
vg_entrada = st.text_input("Digite o vagão:", value=eqnr, key='text_input_CM')

# Botão que executa a função
if st.button("Executar função"):
    with st.spinner("🔄 Processando... Aguarde alguns segundos..."):

        vg_entrada = tratar_entrada(vg_entrada)
        minha_funcao(vg_entrada)
        if not busca_z851_se_existe(vg_entrada):
            st.header(f"O Vagão {vg_entrada} não consta na base de dados!")
            st.header("Verifique se foi digitado corretamente!")
        elif busca_z851_se_existe(vg_entrada) == 'X':
            st.header(f"O Vagão {vg_entrada} consta como Eliminado!")
            st.header("Verifique se foi digitado corretamente!")
        else:

            df_WCM, df_z369, df_trkv, df_z851, df_z1568, df_164, df_SAT_TAREFAS_full, df_busca_TBOGI, df_censo, df_versonota = busca_dados(
                vg_entrada)
            print("df_trkv")
            # print(df_trkv)

            try:
                df_trkv = tratar_outliers_trkv(df_trkv)
                print("df_trkv_outliers")
                # print(df_trkv)
            except Exception as e:
                print(f"Erro ao tratar outliers df_trkv: {e}")

            # #print(df_trkv.head())
            df_trkv_trated, df_wcm_trated, df_timeline_z369, df_z369_trated, df_TBOGI_trated = tratar_dfs(
                df_WCM, df_z369, df_trkv, df_busca_TBOGI)
            print("df_trkv_trated")
            # print(df_trkv_trated)


    # ===== CSS Google Material =====


            def resumo_z1568():
                st.markdown("""
                <style>

        /* ===== CARD ===== */
        .card {
            background: #ffffff;
            border-radius: 12px;
            padding: 20px 18px;
            border: 1px solid #ececec;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            transition: 0.18s ease-in-out;
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 90px;

            /* mais espaçamento superior entre as linhas */
            margin-top: 14px;
        }

        .card:hover {
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            transform: translateY(-1px);
        }

        /* ===== TEXTOS ===== */
        .card-title {
            font-size: 12.8px;
            font-weight: 600;
            color: #6d6d6d;
            margin-bottom: 6px;
            letter-spacing: 0.2px;
        }

        .card-value {
            font-size: 19px;
            font-weight: 600;
            color: #1d1d1d;
            line-height: 1.25;
            letter-spacing: 0.1px;
        }

        /* ===== RESPONSIVIDADE ===== */

        @media (max-width: 1200px) {
            .card-value { font-size: 18px; }
        }

        @media (max-width: 900px) {
            .card { padding: 18px; min-height: 80px; }
            .card-value { font-size: 17px; }
        }

        @media (max-width: 600px) {
            .card { padding: 16px; min-height: 70px; }
            .card-title { font-size: 12px; }
            .card-value { font-size: 16px; }
        }

    </style>

                """, unsafe_allow_html=True)

                # ===== Formatando Dados =====
                df_z851_copia = df_z851.copy()
                colunas_data = [
                    'DATA_DE_FABRICACAO_trated',
                    'DATA_GARANTIA_trated',
                    'ULTIMA_RG',
                    'ULTIMA_RI',
                    'ULTIMA_RR'
                ]
                df_z851_copia['DATA_FIM_trated'] = df_z851_copia['DATA_FIM_trated'].fillna(
                    '-')
                # Converte e formata todas as colunas para dd-mm-yyyy
                df_z851_copia[colunas_data] = df_z851_copia[colunas_data].apply(
                    lambda x: pd.to_datetime(
                        x, errors='coerce').dt.strftime('%d-%m-%Y')
                )
                # df_z851_copia['KM_RODADO_DESDE_ULTIMA_RG'] = df_z851_copia['KM_RODADO_DESDE_ULTIMA_RG'].astype(int)

                df_z851_copia['KM_RODADO_DESDE_ULTIMA_RG'] = (
                    df_z851_copia['KM_RODADO_DESDE_ULTIMA_RG']
                    .round()                # arredonda
                    .astype(int)            # converte para int
                    .apply(lambda x: f"{x:,}".replace(",", ".")))

                df_z851_copia.rename(columns={
                    'EQUNR': 'Ativo',
                    'DATA_DE_FABRICACAO_trated': 'Data de Fabricação',
                    'DATA_FIM_trated': 'Data de Desativação',
                    'DATA_GARANTIA_trated': 'Data de Garantia do Ativo',
                    'ULTIMA_RG': 'Última RG',
                    'ULTIMA_RI': 'Última RI',
                    'ULTIMA_RR': 'Última RR',
                    'KM_RODADO_DESDE_ULTIMA_RG': 'KM Rodado desde última RG',
                    'BITOLA': 'Bitola',
                    'MALHA': 'Malha',
                    'MODELO': 'Modelo',
                    'STATUS': 'Status'
                }, inplace=True)

                m_bitola = {'L': 'Larga', 'M': 'Métrica'}
                m_malha = {'N': 'Norte', 'S': 'Sul'}
                m_status = {'1': 'Disponível', '2': 'Retido',
                            '3': 'Indisponível ou Eliminado'}
                m_data_desativacao = {'None': '-'}

                df_z851_copia.replace({
                    'Bitola': m_bitola,
                    'Malha':  m_malha,
                    'Status': m_status,
                    'DATA_FIM_trated': m_data_desativacao
                }, inplace=True)

                row = df_z851_copia.iloc[0]
                campos = [
                    'Ativo',
                    # 'Bitola',
                    # 'Malha',
                    'Data de Fabricação',
                    'Data de Desativação',
                    'Data de Garantia do Ativo',
                    'KM Rodado desde última RG',
                    'Modelo',
                    'Status',
                    'Última RG',
                    'Última RI',
                    'Última RR'
                ]

                # st.subheader("📌 Informações do Vagão")
                st.markdown("<div class='section-title'>Dados gerais do ativo</div>", unsafe_allow_html=True)

                cards_por_linha = 3

                # ===== Renderização =====
                for i in range(0, len(campos), cards_por_linha):
                    cols = st.columns(cards_por_linha)

                    for idx, campo in enumerate(campos[i:i + cards_por_linha]):
                        valor = row[campo]

                        with cols[idx]:
                            st.markdown(
                                f"""
                                <div style="
                                    background-color:{CARD_BG};
                                    border:1px solid {BORDER};
                                    border-radius:10px;
                                    padding:14px;
                                    text-align:center;
                                ">
                                    <div style="font-size:12px;color:{MUTED};font-weight:600;">
                                        {campo}
                                    </div>
                                    <div style="font-size:22px;font-weight:800;color:{TEXT};">
                                        {valor}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

            resumo_z1568()
    # -------------------------------------------------------------------RESUMO


            def resumo_tela164():

                dados = df_164.iloc[0]
                with st.container():
                    st.divider()
                    st.markdown("<div class='section-title'>Dados atuais do ativo</div>", unsafe_allow_html=True)
                    dados['DT_CARGA'] = pd.to_datetime(dados['DT_CARGA']).strftime("%d-%m-%Y-%H:%M:%S")
                    st.write(f"**Data Atualização:** {dados['DT_CARGA']}")
                    dados = dados.astype('string').fillna('-')
                    col1, col2, col3 = st.columns(3)

                    with col1:

                        st.markdown(
                        f"""
                        <div style="
                            background-color:{CARD_BG};
                            border:1px solid {BORDER};
                            border-radius:10px;
                            padding:14px;
                            text-align:center;
                        ">
                            <div style="font-size:12px;color:{MUTED};font-weight:600;">
                                Local:
                            </div>
                            <div style="font-size:22px;font-weight:800;color:{TEXT};">
                                {dados['LOCAL']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                        )
                        st.markdown(
                        f"""
                        <div style="
                            background-color:{CARD_BG};
                            border:1px solid {BORDER};
                            border-radius:10px;
                            padding:14px;
                            text-align:center;
                        ">
                            <div style="font-size:12px;color:{MUTED};font-weight:600;">
                                Trem:
                            </div>
                            <div style="font-size:22px;font-weight:800;color:{TEXT};">
                                {dados['TREM']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                        )
                        st.markdown(
                        f"""
                        <div style="
                            background-color:{CARD_BG};
                            border:1px solid {BORDER};
                            border-radius:10px;
                            padding:14px;
                            text-align:center;
                        ">
                            <div style="font-size:12px;color:{MUTED};font-weight:600;">
                                OS:
                            </div>
                            <div style="font-size:22px;font-weight:800;color:{TEXT};">
                                {dados['NR_OS']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                        )
                        
                    with col2:
                        st.markdown(
                        f"""
                        <div style="
                            background-color:{CARD_BG};
                            border:1px solid {BORDER};
                            border-radius:10px;
                            padding:14px;
                            text-align:center;
                        ">
                            <div style="font-size:12px;color:{MUTED};font-weight:600;">
                                Código da Linha:
                            </div>
                            <div style="font-size:22px;font-weight:800;color:{TEXT};">
                                {dados['COD_LINHA']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                        )
                        st.markdown(
                        f"""
                        <div style="
                            background-color:{CARD_BG};
                            border:1px solid {BORDER};
                            border-radius:10px;
                            padding:14px;
                            text-align:center;
                        ">
                            <div style="font-size:12px;color:{MUTED};font-weight:600;">
                                Recomendação:
                            </div>
                            <div style="font-size:22px;font-weight:800;color:{TEXT};">
                                {dados['DESC_RECOMENDACAO']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                        )
                        st.markdown(
                        f"""
                        <div style="
                            background-color:{CARD_BG};
                            border:1px solid {BORDER};
                            border-radius:10px;
                            padding:14px;
                            text-align:center;
                        ">
                            <div style="font-size:12px;color:{MUTED};font-weight:600;">
                                Lotação:
                            </div>
                            <div style="font-size:22px;font-weight:800;color:{TEXT};">
                                {dados['DESC_LOTACAO']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                        )

                    with col3:
                        st.markdown(
                        f"""
                        <div style="
                            background-color:{CARD_BG};
                            border:1px solid {BORDER};
                            border-radius:10px;
                            padding:14px;
                            text-align:center;
                        ">
                            <div style="font-size:12px;color:{MUTED};font-weight:600;">
                                Situação:
                            </div>
                            <div style="font-size:22px;font-weight:800;color:{TEXT};">
                                {dados['DESC_SITUACAO']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                        )
                        st.markdown(
                        f"""
                        <div style="
                            background-color:{CARD_BG};
                            border:1px solid {BORDER};
                            border-radius:10px;
                            padding:14px;
                            text-align:center;
                        ">
                            <div style="font-size:12px;color:{MUTED};font-weight:600;">
                                Mercadoria:
                            </div>
                            <div style="font-size:22px;font-weight:800;color:{TEXT};">
                                {dados['DSC_MERCADORIA']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                        )
                        st.markdown(
                        f"""
                        <div style="
                            background-color:{CARD_BG};
                            border:1px solid {BORDER};
                            border-radius:10px;
                            padding:14px;
                            text-align:center;
                        ">
                            <div style="font-size:12px;color:{MUTED};font-weight:600;">
                                TU:
                            </div>
                            <div style="font-size:22px;font-weight:800;color:{TEXT};">
                                {dados['TU']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                        )
                    st.write("---")

            resumo_tela164()

            def plotar_gaph_resumo():
                import plotly.express as px
                import pandas as pd
                import streamlit as st

                st.subheader("Linha do Tempo")

                try:
                    df_wcm_timeline = inserir_wcm_hist(df_wcm_trated)
                except Exception as e:
                    print(f"Erro : {e}")
                    df_wcm_timeline = pd.DataFrame()

                try:
                    df_trkv_timeline = inserir_trkv_hist(df_trkv_trated)
                except Exception as e:
                    print(f"Erro : {e}")
                    df_trkv_timeline = pd.DataFrame()

                try:
                    df_z1568_timeline = inserir_z1568(
                        df_z1568).reset_index(drop=True)
                except Exception as e:
                    print(f"Erro : {e}")
                    df_z1568_timeline = pd.DataFrame()

                try:
                    df_TBOGI_timeline = inserir_TBOGI_hist(df_TBOGI_trated)
                except Exception as e:
                    print(f"Erro : {e}")
                    df_TBOGI_timeline = pd.DataFrame()

                # #print(df_z1568_timeline)

                print("validation")

                df_final = pd.concat([df_z1568_timeline, df_timeline_z369, df_wcm_timeline,
                                    df_trkv_timeline, df_TBOGI_timeline], ignore_index=True)
                # #print(df_final)

                df_final["Texto_Label"] = df_final["Tipo_Evento"].apply(
                    lambda x: "" if x in ["WCM", "trkv", "TBOGI"] else x
                )

                df = df_final  # ajustarr
                mapa_traducao = {
                    "M1": "Nota monitorada",
                    "M2": "Nota crítica",
                    "M3": "Nota de retenção",
                    "M4": "Nota da Engenharia",
                    "M5": "Encerramento manutenção corretiva",
                    "M6": "Vagão acidentado/descarrilado",
                    "M7": "Encerramento manutenção preventiva",
                    "M8": "Plano do PCM",
                    "M9": "Vandalismo",
                    "trkv": "Passagem no TruckView",
                    "wcm": "Passagem no Impacto de Rodas",
                    "MC": "Manutenção Corretiva",
                    "RG": "Revisão Geral",
                    "RA": "Revisão Anual"

                }

                df["Tipo_Evento_Traduzido"] = df["Tipo_Evento"].map(
                    mapa_traducao)

                # st.dataframe(df)
                # Converte datas
                # Converte datas
                df["INICIO"] = pd.to_datetime(
                    df["INICIO"], format="%Y-%m-%d %H:%M")
                df["FIM"] = pd.to_datetime(df["FIM"], format="%Y-%m-%d %H:%M")

                df["INICIO_"] = df["INICIO"].dt.strftime("%d/%m/%Y")
                df["FIM_"] = df["FIM"].dt.strftime("%d/%m/%Y")

                df["Fim_Aux"] = df["FIM"].fillna(pd.Timestamp.now())

                # ORDEM ALFABÉTICA DA LEGENDA
                ordem_legenda = sorted(df["Tipo_Evento"].unique())

                # CORES FIXAS
                cores_eventos = {
                    "M1": "#faf74f",
                    "M2": "#d62728",
                    "M3": "#cf8517",
                    "M4": "#67a5bd",
                    "M5": "#6aa02c",
                    "M6": "#75140d",
                    "M7": "#2ca02c",
                    "M8": "#0e9fff",
                    "M9": "#7f7f7f",
                    "trkv": "#c660f5",
                    "wcm": "#ff57f1",
                    "MC": "#4b8d00",
                    "RG": "#2ca02c",
                    "RA": "#2ca02c"
                }

                fig = px.timeline(
                    df,
                    x_start="INICIO",
                    x_end="Fim_Aux",
                    y="Evento",
                    color="Tipo_Evento",
                    text="Texto_Label",
                    hover_data={
                        "Fim_Aux": False,
                        "INICIO_": True,
                        "FIM_": True,
                        "Tipo_Evento": True,
                        "Tipo_Evento_Traduzido": True,
                        "Texto_Completo": True
                    },
                    category_orders={"Tipo_Evento": ordem_legenda},
                    color_discrete_map=cores_eventos
                )

                # Aumentar altura da barra
                fig.update_traces(
                    width=1,              # AUMENTA altura da barra
                    textfont_size=25,
                    textangle=0,
                    # textposition="inside",
                    # insidetextanchor="middle",
                    cliponaxis=True
                )

                fig.update_yaxes(autorange="reversed")
                fig.update_layout(
                    # legenda horizontal abaixo do gráfico
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3)
                )

                st.plotly_chart(fig, width="stretch")

            plotar_gaph_resumo()
# -------------------------------------------------------------------RESUMO

# graficos WCM e TRKV

#       def regrecao():
# -------------------------------------------------------------------Regressão
    # from sklearn.linear_model import LinearRegression
    # from sklearn.metrics import mean_squared_error, mean_absolute_error
    # from sklearn.metrics import root_mean_squared_error
    # import pandas as pd
    # import plotly.graph_objects as go

    # # == == == == == == == == == == == == =
    # # 1. Garantir que Data é datetime
    # # == == == == == == == == == == == == =
    # df_trkv_trated["Data"] = pd.to_datetime(
    #     df_trkv_trated["Data"], errors="coerce")

    # # Remover linhas sem Data ou sem valores
    # df_trkv_trated = df_trkv_trated.dropna(
    #     subset=["Data", "TRKV_MAX_Cunha"])

    # # Ordenar por data (importante!)
    # df_trkv_trated = df_trkv_trated.sort_values("Data")

    # # =========================
    # # 2. Regressão Linear
    # # =========================
    # X = df_trkv_trated["Data"].map(
    #     pd.Timestamp.toordinal).values.reshape(-1, 1)
    # y = df_trkv_trated["TRKV_MAX_Cunha"].values

    # model = LinearRegression()
    # model.fit(X, y)

    # slope = model.coef_[0]
    # intercept = model.intercept_
    # # Predição
    # y_pred = model.predict(X)
    # # ====== MÉTRICAS ======
    # r2 = model.score(X, y)
    # rmse = root_mean_squared_error(y, y_pred)
    # mae = mean_absolute_error(y, y_pred)

    # print(f"R²:   {r2:.4f}")
    # print(f"MAE:  {mae:.4f}")
    # print(f"RMSE: {rmse:.4f}")

    # print(f"Coeficiente angular (slope): {slope:.4f}")

            print("validation2")
            # #print(df_trkv_trated)
            try:
                import numpy as np
                import pandas as pd
                from math import sqrt

                def projetar_regressao(df, slope, intercept, dias_a_frente=30):
                    #Limpar dados com flag "DESCARTAR"
                    df = df[df['STATUS_out'] != 'DESCARTAR']

                    # Converte datas para inteiro ordinal
                    x = pd.to_datetime(df["Data"], errors="coerce").map(
                        pd.Timestamp.toordinal).values
                    x = x[~np.isnan(x)]  # remove valores inválidos

                    ultimo_x = x[-1]

                    # Cria novos pontos no futuro
                    novos_x = np.array(
                        [ultimo_x + i for i in range(1, dias_a_frente + 1)])
                    
                    print(novos_x)
                    # Converte de volta para datas
                    novas_datas = [pd.Timestamp.fromordinal(int(v)) for v in novos_x]

                    # Predição futura
                    novos_y_pred = slope * novos_x + intercept

                    # Retorna um dataframe organizado
                    return pd.DataFrame({
                        "Data": novas_datas,
                        "y_pred": novos_y_pred
                    })

                def regressao_linear_manual(df, col_x="Data", col_y="TRKV_MAX_Cunha"):
                    # ============================
                    # 1) Preparar dados
                    # ============================
                    #Apagar dados que estão com a flag "DESCARTAR"
                    df = df[df['STATUS_out'] != 'DESCARTAR']
                    
                    # df = df[df['STATUS_out'] == "OK"]

                    x_all = pd.to_datetime(df[col_x], errors="coerce").map(
                        pd.Timestamp.toordinal).values
                    y_all = df[col_y].values

                    # Máscara para limpar NaN
                    mask = ~np.isnan(x_all) & ~np.isnan(y_all)
                    x = x_all[mask]
                    y = y_all[mask]

                    n = len(x)
                    print(df)
                    # ============================
                    # 2) Somatórios
                    # ============================
                    sum_x = np.sum(x)
                    sum_y = np.sum(y)
                    sum_xy = np.sum(x * y)
                    sum_x2 = np.sum(x * x)

                    # ============================
                    # 3) Cálculo dos parâmetros
                    # ============================
                    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
                    intercept = (sum_y - slope * sum_x) / n

                    # ============================
                    # 4) Predições
                    # ============================
                    # y_pred → somente dados válidos (para cálculo das métricas)
                    y_pred = slope * x + intercept

                    # y_pred_full → predição para TODAS as linhas originais
                    y_pred_full = slope * x_all + intercept

                    # ============================
                    # 5) Métricas
                    # ============================
                    rmse = sqrt(np.mean((y - y_pred)**2))
                    mae = np.mean(np.abs(y - y_pred))
                    ss_res = np.sum((y - y_pred)**2)
                    ss_tot = np.sum((y - np.mean(y))**2)
                    r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0

                    # ============================
                    # 6) Retorno
                    # ============================
                    return {
                        "slope": slope,
                        "intercept": intercept,
                        "rmse": rmse,
                        "mae": mae,
                        "r2": r2,
                        "y_pred": y_pred,            # somente dados válidos
                        "y_pred_full": y_pred_full   # TODAS as linhas (para plot)
                    }

                resultado = regressao_linear_manual(df_trkv_trated)

                slope = resultado["slope"]
                intercept = resultado["intercept"]
                r2 = resultado["r2"]
                rmse = resultado["rmse"]
                mae = resultado["mae"]
                y_pred = resultado["y_pred_full"]

                df_projecao = projetar_regressao(
                    df_trkv_trated, slope, intercept, dias_a_frente=30)

                print(f"Slope: {slope}")
                print(f"Intercept: {intercept}")
                print(f"R²: {r2}")
                print(f"RMSE: {rmse}")
                print(f"MAE: {mae}")

            except Exception as e:
                print(f"Erro na regressão: {e}")
                slope = 0
                intercept = 0
                r2 = 0
                rmse = 0
                mae = 0
                y_pred = 0


        # -------------------------------------------------------------------Regressão


            def plot_Waysides():
                try:
                    fig_trkv = go.Figure()

                    # -------------------------
                    # 1. Série real
                    # -------------------------
                    fig_trkv.add_trace(go.Scatter(
                        x=df_trkv_trated["Data"],
                        y=df_trkv_trated["TRKV_MAX_Cunha"],
                        mode="lines+markers+text",
                        text=df_trkv_trated["TRKV_MAX_Cunha"].round(1).astype(str),
                        textposition="top center",
                        name="TRKV_MAX_Cunha",
                        marker=dict(size=7),
                        line=dict(color = PRIMARY, width=2)
                    ))

                    # -------------------------
                    # 2. Linha de regressão real
                    # -------------------------
                    fig_trkv.add_trace(go.Scatter(
                        x=df_trkv_trated["Data"],
                        y=y_pred,
                        mode="lines",
                        line=dict(width=2, dash="dash", color=SUCCESS),
                        name=f"Regressão Linear (slope={slope:.4f})"
                    ))

                    # -------------------------
                    # 3. PROJEÇÃO FUTURA
                    # -------------------------
                    fig_trkv.add_trace(go.Scatter(
                        x=df_projecao["Data"],
                        y=df_projecao["y_pred"],
                        mode="lines",
                        line=dict(width=2, dash="dot", color="#5A5555"),
                        name="Projeção Futura (+30 dias)"
                    ))

                    # -------------------------
                    # 4. Alarme MAX
                    # -------------------------
                    MAP_WEDGE = {
                        2: 45,
                        3: 57,
                        4: 64,
                        5: 57,
                    }

                    code = df_trkv["WedgeTypeCode"].iloc[0]

                    # trata NaN e 0 como inválido
                    if pd.isna(code) or code == 0:
                        label = "inválido"
                    else:
                        label = MAP_WEDGE.get(int(code), "inválido")

                    df_trkv_trated['Alarme'] = label
                    fig_trkv.add_trace(go.Scatter(
                        x=df_trkv_trated["Data"],
                        y=df_trkv_trated['Alarme'],
                        mode="lines",
                        line=dict(color=DANGER, width=2, dash="dash"),
                        name=f"Alarme em {label}"
                    ))
                    # Layout
                    fig_trkv.update_layout(
                        #title="TRKV - Regressão + Projeção Futura",
                        xaxis_title="Data",
                        yaxis_title="Valor",
                        template="plotly_white",
                        height=420,
                        margin=dict(t=60, r=30, b=110, l=60),  # MAIS espaço embaixo p/ a legenda
                        # legend=dict(
                        #         orientation="h",   # legenda horizontal
                        #         x=0,               # começa na esquerda
                        #         y=-0.22,           # coloca a legenda abaixo da área do gráfico
                        #         xanchor="left",
                        #         yanchor="top",
                        #         traceorder="normal",
                        #         bgcolor="rgba(0,0,0,0)",  # sem fundo
                        #         font=dict(size=12)
                        #     )
                        legend=dict(
                            orientation="h",      # legenda horizontal
                            yanchor="bottom",
                            y=1.02,               # um pouco acima do gráfico
                            xanchor="center",
                            x=0.5                 # centralizado
                        )

                    )

                    # Range eixo Y
                    #fig_trkv.update_yaxes(range=[10, 90])
                except Exception as e:
                    print(f"Erro ao plotar gráfico TRKV: {e}")
                    fig_trkv = go.Figure()

                # =========================
                # WCM
                # =========================
                try:
                    df_wcm_trated["Alarme"] = 210

                    fig_wcm = go.Figure()

                    # Curva principal
                    fig_wcm.add_trace(go.Scatter(
                        x=df_wcm_trated["Data"],
                        y=df_wcm_trated["Maior_Impacto_kN"],
                        mode="lines+markers+text",
                        text=df_wcm_trated["Maior_Impacto_kN"].round(
                            1).astype(str),
                        textposition="top center",
                        name="Maior_Impacto_kN",
                        marker=dict(size=7),
                        line=dict(color = PRIMARY, width=2)
                    ))

                    # Linha de limite
                    fig_wcm.add_trace(go.Scatter(
                        x=df_wcm_trated["Data"],
                        y=df_wcm_trated["Alarme"],
                        mode="lines",
                        name="Alarme = 210 kN",
                        line=dict(color=DANGER, width=2, dash="dash")
                    ))

                    fig_wcm.update_layout(
                        #title="WCM",
                        xaxis_title="Data",
                        yaxis_title="Valor",
                        template="plotly_white",
                        height=420,
                        margin=dict(t=60, r=30, b=110, l=60),  # MAIS espaço embaixo p/ a legenda
                        legend=dict(
                            orientation="h",      # legenda horizontal
                            yanchor="bottom",
                            y=1.02,               # um pouco acima do gráfico
                            xanchor="center",
                            x=0.5                 # centralizado
                        )
                    )

                    #fig_wcm.update_yaxes(range=[0, 300])
                except Exception as e:
                    print(f"Erro ao plotar gráfico WCM: {e}")
                    fig_wcm = go.Figure()

                # =========================
                # TBOGI
                # =========================
                try:
                    df_TBOGI_trated["Alarme"] = 15
                    df_TBOGI_trated.rename(
                        columns={"timestamp_received": "Data"}, inplace=True)

                    fig_TBOGI = go.Figure()

                    # Curva principal
                    fig_TBOGI.add_trace(go.Scatter(
                        x=df_TBOGI_trated["Data"],
                        y=df_TBOGI_trated["max_valor_mod_pd"],
                        mode="lines+markers+text",
                        text=df_TBOGI_trated["max_valor_mod_pd"].round(
                            1).astype(str),
                        textposition="top center",
                        name="max_valor_mod_pd",
                        marker=dict(size=7),
                        line=dict(color = PRIMARY, width=2)
                    ))

                    # Linha de limite
                    fig_TBOGI.add_trace(go.Scatter(
                        x=df_TBOGI_trated["Data"],
                        y=df_TBOGI_trated["Alarme"],
                        mode="lines",
                        name="Alarme 10 ",
                        line=dict(color=DANGER, width=2, dash="dash")
                    ))

                    fig_TBOGI.update_layout(
                        title="TBOGI",
                        xaxis_title="Data",
                        yaxis_title="Valor",
                        template="plotly_white",
                        height=380
                    )

                    fig_TBOGI.update_yaxes(range=[0, 30])
                except Exception as e:
                    print(f"Erro ao plotar gráfico TBOGI: {e}")
                    fig_TBOGI = go.Figure()
                # =========================
                # STREAMLIT LAYOUT
                # =========================
                st.divider()
                col1, col2 = st.columns(2)

                with col1:
                    # st.subheader("TRKV Cunha Máximo Passagem (mm)")
                    st.markdown("<div class='section-title'>TRKV Cunha Máximo Passagem</div>", unsafe_allow_html=True)
                    MAP_WEDGE = {
                        2: "Ride Control",
                        3: "Barber",
                        4: "Ride Master",
                        5: "Motion Control",
                    }

                    code = df_trkv["WedgeTypeCode"].iloc[0]

                    # trata NaN e 0 como inválido
                    if pd.isna(code) or code == 0:
                        label = "inválido"
                    else:
                        # int() se o dtype vier float
                        label = MAP_WEDGE.get(int(code), "inválido")

                    st.markdown(f'Tipo de Truque:  **{label}** | Regressão + projeção futura')
                    # fig_trkv.update_layout(
                    #     # legenda horizontal abaixo do gráfico
                    #     legend=dict(orientation="h", yanchor="bottom", y=-0.3)
                    # )
                    st.plotly_chart(fig_trkv, width="stretch",
                                    key="plot_trkv")
                    # st.markdown(f'Modelo de cunha {df_trkv["WedgeTypeCode"][0]}')
                    st.markdown(f"""
                    **R²:** `{r2:.4f}`
                    **MAE:** `{mae:.4f}`
                    **RMSE:** `{rmse:.4f}`
                    """)

                    st.dataframe(df_trkv_trated.sort_values(
                        by="Data", ascending=False).reset_index(drop=True), hide_index = True)
                    # st.dataframe(df_trkv_trated.sort_values(
                    #     by="Data", ascending=False).reset_index(drop=True), hide_index = True)
                    
                    # limite = df_trkv_trated['Alarme'].dropna().min()

                    # colunas = ["Data", "TRKV_MAX_Cunha", "STATUS_out"]

                    # df_plot = (
                    #     df_trkv_trated[colunas]
                    #     .sort_values(by="Data", ascending=False)
                    #     .reset_index(drop=True)
                    # )

                    # df_plot["TRKV_MAX_Cunha"] = pd.to_numeric(
                    #     df_plot["TRKV_MAX_Cunha"], errors="coerce"
                    # )

                    # styled_df = df_plot.style.map(
                    #     lambda v: "background-color: #ffcccc"
                    #     if pd.notna(v) and v > limite else "",
                    #     subset=["TRKV_MAX_Cunha"]
                    # )

                    # st.dataframe(styled_df, hide_index=True)

                    # st.dataframe(df_trkv_trated.sort_values(
                    #     by="Data", ascending=False).reset_index(drop=True), hide_index = True)

                with col2:
                    # st.subheader("WCM - Maior Impacto (kN)")
                    st.markdown("<div class='section-title'>WCM - Maior Impacto</div>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.write(" ")
                    #st.write(" ")
                    #st.write(" ")
                    # fig_wcm.update_layout(
                    #     # legenda horizontal abaixo do gráfico
                    #     legend=dict(
                    #         orientation="h",      # legenda horizontal
                    #         yanchor="bottom",
                    #         y=1.02,               # um pouco acima do gráfico
                    #         xanchor="center",
                    #         x=0.5                 # centralizado
                    #     ))
                    st.plotly_chart(fig_wcm, width="stretch", key="plot_wcm")
                    st.markdown(f"""
                    **Alarme Baixo:** `-`
                    **Alarme Médio:** `-`
                    **Alarme Alto:** `-`
                    """)
                    st.dataframe(df_wcm_trated.sort_values(
                        by="Data", ascending=False).reset_index(drop=True), hide_index = True)


                col2_1, col2_2 = st.columns(2)

                with col2_1:
                    st.subheader("TBOGI Módulo Max ()")
                    fig_TBOGI.update_layout(
                        # legenda horizontal abaixo do gráfico
                        legend=dict(orientation="h", yanchor="bottom", y=-0.3)
                    )
                    st.plotly_chart(
                        fig_TBOGI, width="stretch", key="plot_tbogi")
                    st.dataframe(df_TBOGI_trated.sort_values(
                        by="Data", ascending=False).reset_index(drop=True), hide_index = True)

                with col2_2:
                    st.subheader("Detector Acústico")
                    # st.plotly_chart(fig_detector, use_container_width=True, key="plot_detector")

                    # Plota gráfico de linha
        # graficos WCM e TRKV
            try:
                plot_Waysides()
            except Exception as e:
                print(f"Erro ao plotar gráficos Waysides: {e}")

            st.divider()

            # st.divider()

            # st.markdown("<div class='section-title'>Dados do censo</div>", unsafe_allow_html=True)
            # st.dataframe(df_censo, hide_index=True)

            # st.divider()

            # st.markdown("<div class='section-title'>Tarefas de manutenção</div>", unsafe_allow_html=True)
            # df_SAT_TAREFAS_full = df_SAT_TAREFAS_full.drop(['IDTAREFA', 'DH_CRIACAO', 'UNAME_CRIACAO', 'ID', 
            #                     'DHFIM','EQUNR', 'MODELO', 'IDORDEMSERVICOSTATUS_ATUAL', 'TEMPO_PADRAO',
            #                     'HH_APLICADO', 'ID_TAREFA', 'NOME','data_sincronizacao'],axis=1)
            # ordem = ['NUMDOC','dt_inicio_trated', 'dt_fim_trated','Sistema','DESCRICAO_TAREFA', 'DESCRICAO_ECP','Status','OBS_ATUAL']
            # df_SAT_TAREFAS_full = df_SAT_TAREFAS_full[ordem]
            # df_SAT_TAREFAS_full = df_SAT_TAREFAS_full.rename(columns={
            #     'NUMDOC': 'Número Doc.',
            #     'dt_inicio_trated': 'Data de abertura',
            #     'dt_fim_trated': 'Data de conclusão',
            #     'DESCRICAO_TAREFA': 'Descrição da tarefa',
            #     'DESCRICAO_ECP': 'Escopo',
            #     'OBS_ATUAL': 'Obs.'
            # })
            # st.dataframe(df_SAT_TAREFAS_full, hide_index=True)

        # ------------------------
            if not df_SAT_TAREFAS_full.empty:
                df_SAT_TAREFAS_full = df_SAT_TAREFAS_full[[
                    'NUMDOC', 'DH_CRIACAO', 'DHFIM', 'DESCRICAO_TAREFA', 'Status', 'DESCRICAO_ECP', 'Sistema', 'OBS_ATUAL']]

            def plotar_TELA_SAT(df_SAT_TAREFAS_full):

                import streamlit as st
                import streamlit.components.v1 as components
                import pandas as pd
                import json

                # st.write("---")
                st.markdown(f"### Tarefas Realizadas em Manutenção")

                # Converter DataFrame para lista de dicionários
                dados = df_SAT_TAREFAS_full.to_dict(orient="records")

                # Converter Timestamp para string
                for row in dados:
                    for k, v in row.items():

                        # Tratamento para Timestamps
                        if isinstance(v, pd.Timestamp):
                            row[k] = "" if pd.isna(v) else v.strftime(
                                "%Y-%m-%d %H:%M:%S")

                        # NaT explícito
                        elif v is pd.NaT:
                            row[k] = ""

                        # NaN numérico (float("nan"))
                        elif isinstance(v, float) and np.isnan(v):
                            row[k] = ""

                        # None
                        elif v is None:
                            row[k] = ""

                html_code = f"""
                <html>
                <head>
                <meta charset="UTF-8">

                <style>

                    #root, .block-container, .main {{
                        padding: 0 !important;
                        margin: 0 !important;
                    }}
                    .block-container {{
                        max-width: 100% !important;
                    }}

                    /* Remover padding lateral do Streamlit */
                    .main .block-container {{
                        padding-left: 0 !important;
                        padding-right: 0 !important;
                    }}

                    /* Container em largura total */
                    .container {{
                        width: 100% !important;
                        max-width: 100% !important;
                        margin: 0 !important;
                        padding: 0 20px !important;
                    }}

                    body {{
                        font-family: 'Segoe UI', Arial, sans-serif;
                        background-color: #ffffff;
                    }}

                    /* SEARCH BOX FIXA */
                    .search-box {{
                        margin: 0 0 15px 0;
                        display: flex;
                        border: 1px solid #ddd;
                        padding: 12px 18px;
                        border-radius: 25px;
                        background: #ffffff !important;
                        box-shadow: 0px 2px 6px rgba(0,0,0,0.05);

                        position: sticky;
                        top: 0;
                        z-index: 20;
                    }}

                    .search-input {{
                        border: none;
                        background: none;
                        width: 100%;
                        outline: none;
                        font-size: 16px;
                    }}

                    /* TABELA ESTILO NOTION + GOOGLE */
                    table {{
                        width: 100%;
                        border-collapse: separate;
                        border-spacing: 0 4px;
                        font-size: 14px;
                    }}

                    thead tr {{
                        background: #f3f3f3;
                        border-radius: 6px;

                        position: sticky;
                        top: 60px; /* Alinhar com search-box */
                        z-index: 10;
                    }}

                    th {{
                        text-align: left;
                        padding: 10px 12px;
                        font-weight: 600;
                        color: #333;
                        border-bottom: 1px solid #e5e5e5;
                    }}

                    tbody tr {{
                        background: #fff;
                        transition: 0.15s ease-in-out;
                    }}

                    tbody tr:hover {{
                        background: #f7faff;
                        box-shadow: 0px 2px 6px rgba(0,0,0,0.05);
                    }}

                    td {{
                        padding: 10px 12px;
                        color: #333;
                        border-bottom: 1px solid #f1f1f1;
                        text-align: left;
                    }}

                    tbody tr:nth-child(even) {{
                        background: #fafafa;
                    }}

                    .info-linhas {{
                        font-size: 12px;
                        color: #666;
                        margin-top: 5px;
                    }}

                </style>

                </head>

                <body>

                <div class="container">

                    <div class="search-box">
                        <input class="search-input" id="searchInput" placeholder="Pesquisar por DESCRICAO_TAREFA..." />
                    </div>

                    <div class="info-linhas" id="infoLinhas"></div>

                    <table>
                        <thead>
                            <tr id="headerRow"></tr>
                        </thead>
                        <tbody id="tableBody"></tbody>
                    </table>

                </div>

                <script>

                    const dados = {json.dumps(dados, ensure_ascii=False)};
                    const colunas = dados.length > 0 ? Object.keys(dados[0]) : [];

                    // Montar cabeçalho
                    function renderHeader() {{
                        const headerRow = document.getElementById("headerRow");
                        headerRow.innerHTML = "";
                        colunas.forEach(col => {{
                            const th = document.createElement("th");
                            th.textContent = col;
                            headerRow.appendChild(th);
                        }});
                    }}

                    // Montar tabela
                    function renderTabela(linhas) {{
                        const tbody = document.getElementById("tableBody");
                        const info = document.getElementById("infoLinhas");
                        tbody.innerHTML = "";

                        linhas.forEach(row => {{
                            const tr = document.createElement("tr");
                            colunas.forEach(col => {{
                                const td = document.createElement("td");
                                td.textContent = row[col] ?? "";
                                tr.appendChild(td);
                            }});
                            tbody.appendChild(tr);
                        }});

                        info.textContent = linhas.length + " linha(s) exibida(s)";
                    }}

                    // Render inicial
                    renderHeader();
                    renderTabela(dados);

                    // Filtro em tempo real
                    document.getElementById("searchInput").addEventListener("input", function() {{
                        const q = this.value.toLowerCase();

                        const filtrado = dados.filter(row => {{
                            const texto = String(row["DESCRICAO_TAREFA"] || "").toLowerCase();
                            return texto.includes(q);
                        }});

                        renderTabela(filtrado);
                    }});

                </script>

                </body>
                </html>
                """

                components.html(html_code, height=900, scrolling=True)
            try:
                plotar_TELA_SAT(df_SAT_TAREFAS_full)
            except Exception as e:
                print(f"Erro ao exibir TELA SAT: {e}")
            st.write("---")
        # ------------------------

            try:  # 164
                st.markdown("## Dados SAP censo")
                st.markdown("### Informações técnicas última Manutenção")
                st.dataframe(df_censo)
            except Exception as e:
                print(f"Erro ao exibir dados senso: {e}")
            st.write("---")
            try:  # 164
                st.markdown("## Dados Tela 164 Translogic")
                st.markdown("### Posicionamento mais recente e Carga - Translogic")
                st.dataframe(df_164)
            except Exception as e:
                print(f"Erro ao exibir dados df_164: {e}")

            st.write("---")
            try:  # z369
                st.markdown("## Dados Tela z369 SAP")
                st.markdown("### Dados de Notas de Manutenção - SAP")
                colunas_z369 = [
                    "NOTA",
                    "ATIVO",
                    "MODELO",
                    "dt_abertura_trated",
                    "dt_fechamento_trated",
                    "STATUS",
                    "TP NOTA",
                    "TEXTO",
                    "TEXTO AVARIA",
                    "TEXTO CAUSA",
                    "Flag"
                ]
                df_z369['dt_abertura_trated'] = (
                    pd.to_datetime(df_z369['dt_abertura_trated'])
                    .dt.strftime("%d/%m/%Y")
                )

                df_z369['dt_fechamento_trated'] = (
                    pd.to_datetime(df_z369['dt_fechamento_trated'])
                    .dt.strftime("%d/%m/%Y")
                )
                st.dataframe(df_z369[colunas_z369].sort_values(
                    by="dt_abertura_trated", ascending=False).reset_index(drop=True))
            except Exception as e:
                print(f"Erro ao exibir dados df_z369: {e}")
            st.write("---")

            try:  # WCM
                st.markdown("## Dados WCM")
                st.markdown(
                    "### Dados de medição de Impacto de Roda - WAYSIDE Wheel Impact")

                colunas_zWCM = [
                    "json_header",
                    "json_Identificação do veículo",
                    "json_Força de pico de impacto da roda (kN)",
                    "Data",
                    "json_trem_TrainTime",
                    "json_Lateral da linha",
                    "json_trem_L_Dir",
                    "json_Tipo do veículo"
                ]
                st.dataframe(df_WCM[colunas_zWCM].sort_values(
                    by="Data", ascending=False).reset_index(drop=True))
            except Exception as e:
                print(f"Erro ao exibir dados df_WCM: {e}")
            st.write("---")

            try:  # trkv
                st.markdown("## Dados TRKV")
                st.markdown("### Dados de medição de Cunha - WAYSIDE TruckView")
                colunas_impacto = ["A#L_1", "A#L_2", "A#R_1", "A#R_2",
                           "B#L_1", "B#L_2", "B#R_1", "B#R_2",'max_valor']

                #df_trkv["A#L_1"] = df_trkv["A#L_1"].map('{:.2f}'.format)
                df_trkv[colunas_impacto] = df_trkv[colunas_impacto].map('{:.2f}'.format)
                #convertendo ponto para virgula
                #df_trkv[colunas_impacto] = df_trkv[colunas_impacto].applymap(lambda x: str(x).replace('.', ','))
                colunas_TRKV = [
                    "Header_TrainSequenceNumber",
                    "CarOrientation",
                    "CarIDInitial",
                    "CarIDNumber",
                    "max_valor",
                    "A#L_1",
                    "A#L_2",
                    "A#R_1",
                    "A#R_2",
                    "B#L_1",
                    "B#L_2",
                    "B#R_1",
                    "B#R_2",
                    "STATUS_out"
                ]

                st.dataframe(
                    df_trkv[colunas_TRKV]
                    .sort_values(by="max_valor", ascending=False)
                    .reset_index(drop=True)
                )
            except Exception as e:
                print(f"Erro ao exibir dados df_trkv: {e}")
            st.write("---")

            try:
                st.markdown("## Dados SAP sz851")
                st.markdown("### Cadastro do vagão")
                st.dataframe(df_z851)
            except Exception as e:
                print(f"Erro ao exibir dados df_z851: {e}")

            st.write("---")

            try:
                st.markdown("## Dados SAP z1568")
                st.markdown("### Liberações e Retenções")
                st.dataframe(df_z1568)
            except Exception as e:
                print(f"Erro ao exibir dados df_z1568: {e}")
            st.write("---")

            try:
                # Selecionar apenas as colunas desejadas
                def tratar_versos(df):

                    df_clean = df_versonota[[
                        "QMDAT", "QMNUM", "ATIVO_TL", "VERSO"]].copy()

                    # ---- Tratamento da data QMDAT ----
                    # QMDAT vem no formato YYYYMMDD como inteiro
                    df_clean["QMDAT"] = (
                        df_clean["QMDAT"]
                        .astype(str)
                        .str.zfill(8)                # garante 8 dígitos
                        # formata para YYYY-MM-DD
                        .apply(lambda x: f"{x[0:4]}-{x[4:6]}-{x[6:8]}")
                    )

                    return df_clean
                st.markdown("## Dados df_versonota")
                st.markdown("### Anotações de Verso de Notas")
                st.dataframe(tratar_versos(df_versonota))
            except Exception as e:
                print(f"Erro ao exibir dados df_versonota: {e}")
            st.write("---")

            # ----------------------------------------------------
            # FORMATADOR DE TEXTO
            # ----------------------------------------------------

            def formatar_texto_avaria(texto):
                if not isinstance(texto, str):
                    return ""

                partes = [p.strip() for p in texto.split(";") if p.strip()]
                linhas = []

                for parte in partes:

                    if re.match(r'^\d+\.', parte):  # Título principal
                        linhas.append(
                            f"<h4 style='margin-top:12px;color:#1F4E79'><b>{parte}</b></h4>")
                        continue

                    if re.match(r'^\d+\.\d+', parte):  # Subtítulo
                        linhas.append(f"<b style='color:#3A3A3A'>{parte}</b><br>")
                        continue

                    if ":" in parte:
                        chave, valor = parte.split(":", 1)
                        linhas.append(
                            f"<div style='margin-left:10px;'>• <b>{chave.strip()}</b>: {valor.strip()}</div>")
                        continue

                    linhas.append(parte + "<br>")

                return "\n".join(linhas)

            # ----------------------------------------------------
            # STREAMLIT
            # ----------------------------------------------------

            st.title("📄 Visualizador do Verso da Nota")

            coluna_texto = "VERSO"

            if "QMNUM" not in df_versonota.columns:
                st.error("A coluna QMNUM não existe.")
                st.stop()

            if coluna_texto not in df_versonota.columns:
                st.error("A coluna VERSO não existe.")
                st.stop()

            df_versonota["texto_formatado"] = df_versonota[coluna_texto].apply(
                formatar_texto_avaria)

            registros = df_versonota[["QMNUM", "QMDAT",
                                    "texto_formatado"]].to_dict(orient="records")
            df_versonota["QMDAT"] = (
                df_versonota["QMDAT"]
                .astype(str)
                .str.zfill(8)                # garante 8 dígitos
                # formata para YYYY-MM-DD
                .apply(lambda x: f"{x[0:4]}-{x[4:6]}-{x[6:8]}")
            )

            # ----------------------------------------------------
            # HTML + CSS + JS (CARD À ESQUERDA)
            # ----------------------------------------------------
            st.components.v1.html(f"""

            <style>
                .card {{
                    background: #ffffff;
                    border-radius: 12px;
                    padding: 20px;
                    margin-left: 0px;
                    max-width: 650px;
                    box-shadow: 0px 4px 15px rgba(0,0,0,0.08);
                }}
                .nav-buttons {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 15px;
                }}
                .btn-nav {{
                    flex: 1;
                    padding: 12px;
                    margin: 4px;
                    background: #1F4E79;
                    color: white;
                    font-size: 16px;
                    border-radius: 8px;
                    border: none;
                    cursor: pointer;
                }}
                .btn-nav:disabled {{
                    background: #A0A0A0;
                    cursor: not-allowed;
                }}
            </style>

            <div class="card">

                <div class="nav-buttons">
                    <button id="prevBtn" class="btn-nav">⬅️ Anterior</button>
                    <button id="nextBtn" class="btn-nav">Próximo ➡️</button>
                </div>

                <h3 id="qmnum" style="margin-bottom:4px;"></h3>
                <p id="qmdat" style="margin-top:-8px; color:#777;"></p>
                <p id="pos" style="color:#555; margin-top:4px;"></p>

                <div id="texto" style="margin-top: 15px; font-size: 16px; line-height: 1.45;"></div>

            </div>

            <script>
                const registros = {json.dumps(registros)};
                let pos = 0;

                function render() {{
                    const r = registros[pos];

                    document.getElementById("qmnum").innerHTML =
                        "📌 QMNUM: <b>" + r.QMNUM + "</b>";

                    document.getElementById("qmdat").innerHTML =
                        "📅 Data: <b>" + (r.QMDAT ?? "").slice(0, 10) + "</b>";

                    document.getElementById("pos").innerHTML =
                        "Registro " + (pos+1) + " de " + registros.length;

                    document.getElementById("texto").innerHTML = r.texto_formatado;

                    document.getElementById("prevBtn").disabled = (pos === 0);
                    document.getElementById("nextBtn").disabled = (pos === registros.length - 1);
                }}

                document.getElementById("prevBtn").onclick = () => {{
                    if (pos > 0) {{ pos--; render(); }}
                }}

                document.getElementById("nextBtn").onclick = () => {{
                    if (pos < registros.length-1) {{ pos++; render(); }}
                }}

                render();
            </script>

            """, height=750, scrolling=True)
