#primaryColor="#0052CC"        # cor principal (botões, sliders)
# ALTEREI PARA primaryColor="#6C7C8C"        # cor principal (botões, sliders)
#--------------------------------------------------------------------------------
## Importando bibliotecas
#--------------------------------------------------------------------------------

import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import glob
import os


import matplotlib.pyplot as plt
from PIL import Image
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
import json
warnings.filterwarnings("ignore")
eqnr = st.query_params.get("eqnr")

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
SUCCESS = "#3CB371"
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
#--------------------------------------------------------------------------------
## Carregamento de Dados 
#--------------------------------------------------------------------------------

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
#df_WCM = dfs["df_WCM"]
df_z369 = dfs["df_z369"]
df_z851 = dfs["df_z851"]
df_z1568 = dfs["df_z1568"]
df_tbogi = dfs["df_tbogi"]



# # SHAREPOINT | Enriquecimento – Sistema da Falha
# df_avarias = pd.read_excel(
#     r'Panel_Waysides\Base_avarias.xlsx',
#     engine='openpyxl'
# )

# MONGO DB | Dados do censo
# def function_to_get_data(MONGO_URI_PRD, DB_NAME_PRD, COLLECTION_NAME):
#     client = MongoClient(MONGO_URI_PRD)
#     db = client[DB_NAME_PRD]
#     collection = db[COLLECTION_NAME]
#     # Buscar documentos ordenados por timestamp decrescente
#     docs = list(collection.find().sort("timestamp", -1))
#     if docs:
#         # Converter lista de documentos para DataFrame, removendo coluna _id
#         df = pd.DataFrame(docs).drop(columns=['_id'], errors='ignore')
#         if 'json_documents' in df.columns:
#             df['json_documents'] = df['json_documents'].fillna('').astype(str)
#         return df
#     else:
#         return pd.DataFrame()  # DataFrame vazio

def function_to_get_data(
    MONGO_URI_PRD,
    DB_NAME_PRD,
    COLLECTION_NAME,
    query=None,          # filtro MongoDB (ex: {"equipamento": "ABC"})
    projection=None,     # campos a retornar (ex: {"campo": 1})
    limit=None,          # limitar quantidade de registros
    sort_field="timestamp",
    sort_order=-1
):
    client = MongoClient(MONGO_URI_PRD)
    db = client[DB_NAME_PRD]
    collection = db[COLLECTION_NAME]

    # Query padrão (sem filtro)
    if query is None:
        query = {}

    cursor = collection.find(query, projection)

    # Ordenação
    if sort_field:
        cursor = cursor.sort(sort_field, sort_order)

    # Limite de registros
    if limit:
        cursor = cursor.limit(limit)

    docs = list(cursor)

    if docs:
        df = pd.DataFrame(docs).drop(columns=["_id"], errors="ignore")

        if "json_documents" in df.columns:
            df["json_documents"] = df["json_documents"].fillna("").astype(str)

        return df

    return pd.DataFrame()


# MONGO_URI_PRD = 'mongodb+srv://inteligencia_dados:AR5VxIUwpWIt3VlK@rumo-dev.eqds1.mongodb.net/?authSource=admin'
# DB_NAME_PRD = 'inteligencia_MR'
# MONGO_URI_DEV = 'mongodb+srv://int_dados:e7bUe2bXbKDu3Xzr@rumo-dev2.hbdcrld.mongodb.net/?authSource=admin'
# DB_NAME_DEV = 'supervisorio'

MONGO_URI_DEV = st.secrets.database_dev.MONGO_URI
DB_NAME_DEV = st.secrets.database_dev.DB_NAME
MONGO_URI_PRD = st.secrets.database_prod.MONGO_URI_PRD
DB_NAME_PRD = st.secrets.database_prod.DB_NAME_PRD
df_censo = function_to_get_data(MONGO_URI_PRD, DB_NAME_PRD, "SAP_censo_trated")
df_WCM = function_to_get_data(
            MONGO_URI_PRD, DB_NAME_PRD, 'WCM_treated'#,
            #query={
            #    'tipo_do_veículo': {
            #        '$not': {
            #            '$regex': 'L'
            #        }
            #    }}
        )
#df_tbogi = function_to_get_data(MONGO_URI_PRD, DB_NAME_PRD, "tbogi_treated")
# -----------------------------
# Funções
# -----------------------------
# --- Função para tratar nome das colunas ---
def tratar_nome(col):
    col = col.lower()
    # transforma e_3 ou d_2 em e3/d2
    col = re.sub(r'([a-z])_(\d)', r'\1\2', col)
    # troca _ por espaço
    col = col.replace('_', ' ')
    # primeira letra maiúscula em cada palavra
    col = col.title()

    return col

# --- Função para tratar dataframes ----
def tratar_dfs(df_WCM, df_z369, df_trkv, df_tbogi):
    # def tratar_tbogi(df_tbogi):
    #     if "tp" in df_tbogi.columns:
    #             df_tbogi["valor_mod_pd"] = df_tbogi["tp"].abs()
    #     else:
    #         print(
    #             "TBOGI: coluna 'tp' não encontrada — adicionando valor_mod_pd = NaN")
    #         df_tbogi["valor_mod_pd"] = np.nan
    #     df_tbogi_treated = (
    #         df_tbogi.groupby("timestamp_received", as_index=False)[
    #             "valor_mod_pd"]
    #         .max()
    #         .rename(columns={"valor_mod_pd": "max_valor_mod_pd"})
    #         .sort_values(by="timestamp_received")
    #     )
    #     return df_tbogi_treated
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
        df_TBOGI_trated = tratar_tbogi(df_tbogi)
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

    def tratar_WCM(df_WCM, num_vg):
        # Garantir que o campo de tempo esteja em formato datetime
        df_WCM['trem_traintime'] = pd.to_datetime(
            df_WCM['trem_traintime'])

        # Criar uma coluna apenas com a data (sem hora)
        df_WCM['Data'] = df_WCM['trem_traintime'].dt.date

        # # Extrair os 7 primeiros caracteres da variável
        # prefixo = vg_entrada[:7]

        # Filtrar dataframe
        df_WCM_f = df_WCM[
            df_WCM['identificação_do_veículo']
            .astype(str)
            .str.contains(num_vg, na=False)
        ]

        # Agrupar por dia e pegar o maior valor da força de impacto
        df_WCM_max = (
            df_WCM_f.groupby('Data', as_index=False)[
                'força_de_pico_de_impacto_da_roda_kn']
            .max()
            .rename(columns={'força_de_pico_de_impacto_da_roda_kn': 'Maior_Impacto_kN'})
            # ✅ organiza do mais antigo para o mais recente
            .sort_values(by='Data', ascending=True)
        )
        return df_WCM_max
        #return df_WCM_f
    try:
        df_wcm_trated = tratar_WCM(df_WCM, num_vg)
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
# -----------------------------
#  Seleção do vagão
# -----------------------------

# Campo de entrada de texto
st.container(height=50, border=False)
vg_entrada = st.text_input("Digite o vagão:", value=eqnr, key='text_input_CM')


################################################################################################################
#--------------------------------------------------------------------------------
## Filtro Global – MODELO
#--------------------------------------------------------------------------------
if st.button("Executar função"):
    with st.spinner("🔄 Processando... Aguarde alguns segundos..."):

        vg_entrada = vg_entrada.upper()
        num_vg = vg_entrada[:7].lstrip('0')

        # df_tbogi = function_to_get_data(
        #     MONGO_URI_DEV, DB_NAME_DEV, 'tbogi_treated',
        #     query={
        #         'car_num': num_vg
        #     }
        # )

        df_trkv_trated, df_wcm_trated, df_timeline_z369, df_z369_trated, df_TBOGI_trated = tratar_dfs(
            df_WCM, df_z369, df_trkv, df_tbogi)
        # Filtros e tratamentos z851
        df_z851_f = df_z851[
            df_z851["EQUNR"].astype(str) == vg_entrada
        ]

        m_status = {'1': 'Disponível', '2': 'Retido',
            '3': 'Indisponível ou Eliminado'}
        m_data_desativacao = {'None': '-'}

        df_z851_f.replace({
            'STATUS': m_status,
            'DATA_FIM_trated': m_data_desativacao
        }, inplace=True)

        datas = ['DATA_DE_FABRICACAO_trated', 'DATA_FIM_trated', 'DATA_GARANTIA_trated', 'ULTIMA_RG', 'ULTIMA_RI', 'ULTIMA_RR']
        datas_trat = ['Data de Fabricação', 'Data de Desativação', 'Data de Garantia do Ativo', 'Última RG', 'Última RI', 'Última RR']

        for col_origem, col_nova in zip(datas, datas_trat):
            df_z851_f[col_origem] = pd.to_datetime(df_z851_f[col_origem], errors='coerce')
            df_z851_f[col_nova] = df_z851_f[col_origem].dt.strftime('%d/%m/%Y')

        df_z851_f['KM_Exibicao'] = (
            df_z851_f['KM_RODADO_DESDE_ULTIMA_RG']
            .round()
            .astype('Int64')
        )

        df_z851_f.rename(columns={
            'EQUNR': 'Ativo',
            'KM_Exibicao': 'KM Rodado desde última RG',
            'MODELO': 'Modelo',
            'STATUS': 'Status'
        }, inplace=True)

        row = df_z851_f.iloc[0]
        campos = [
            'Ativo',
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

        cards_por_linha = 3

        # Filtros e tratamentos censo
        df_censo_f= df_censo[
            df_censo["Equipamento"].astype(str) == vg_entrada
        ]

        df_censo_f.columns = [tratar_nome(c) for c in df_censo_f.columns]

        for col in df_censo_f.columns:
            if 'data' in col.lower():
                df_censo_f[col] = pd.to_datetime(df_censo_f[col], errors='coerce').dt.date
        
        df_censo_f = df_censo_f.drop(['Id Reg', 'Id Reg Roda', 'Equipamento','Data Sincronizacao'], axis=1)

        # Filtros e tratamento SAT
        df_SAT_f = function_to_get_data(
            MONGO_URI_PRD, DB_NAME_PRD, 'SAT_TAREFAS_full',
            query={"EQUNR": vg_entrada}
        )

        df_SAT_f = df_SAT_f.drop(['IDTAREFA', 'DH_CRIACAO', 'UNAME_CRIACAO', 'ID', 
                                'DHFIM','EQUNR', 'MODELO', 'IDORDEMSERVICOSTATUS_ATUAL', 'TEMPO_PADRAO',
                                'HH_APLICADO', 'ID_TAREFA', 'NOME','data_sincronizacao'],axis=1)
        ordem = ['NUMDOC','dt_inicio_trated', 'dt_fim_trated','Sistema','DESCRICAO_TAREFA', 'DESCRICAO_ECP','Status','OBS_ATUAL']
        df_SAT_f = df_SAT_f[ordem]
        df_SAT_f = df_SAT_f.rename(columns={
            'NUMDOC': 'Número Doc.',
            'dt_inicio_trated': 'Data de abertura',
            'dt_fim_trated': 'Data de conclusão',
            'DESCRICAO_TAREFA': 'Descrição da tarefa',
            'DESCRICAO_ECP': 'Escopo',
            'OBS_ATUAL': 'Obs.'
        })

        # ===== Renderização =====
        st.markdown("<div class='section-title'>Dados gerais do ativo</div>", unsafe_allow_html=True)
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
                    # st.markdown(f"""
                    #         <div style="
                    #             background-color:{CARD_BG};
                    #             border:1px solid {BORDER};
                    #             border-radius:10px;
                    #             padding:14px;
                    #             text-align:center;
                    #         ">
                    #     <div class="card">
                    #         <div class="card-title">{campo}</div>
                    #         <div class="card-value">{valor}</div>
                    #     </div>
                    #     """,
                    #     unsafe_allow_html=True<
                    # )

        st.divider()

        col1, col2 = st.columns(2)

        # =========================
        # PLOT WCM
        # =========================
        with col1:
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
                    name="Impacto máximo (kN)",
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
                    title="Histórico WCM",
                    xaxis_title="Data",
                    yaxis_title="Valor",
                    template="plotly_white",
                    height=380,
                    legend=dict(
                        orientation="h",      # legenda horizontal
                        yanchor="bottom",
                        y=1.02,               # um pouco acima do gráfico
                        xanchor="center",
                        x=0.5                 # centralizado
                    )
                )

                fig_wcm.update_yaxes(range=[0, 300])
                st.plotly_chart(fig_wcm, use_container_width=True)
            except Exception as e:
                print(f"Erro ao plotar gráfico WCM: {e}")
                fig_wcm = go.Figure()
        
        # =========================
        # TBOGI
        # =========================
        with col2:
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
                    name="TP - Máximo valor absoluto",
                    marker=dict(size=7),
                    line=dict(color = PRIMARY,width=2)
                ))

                # Linha de limite
                fig_TBOGI.add_trace(go.Scatter(
                    x=df_TBOGI_trated["Data"],
                    y=df_TBOGI_trated["Alarme"],
                    mode="lines",
                    name="Alarme = 15",
                    line=dict(color=DANGER, width=2, dash="dash")
                ))

                fig_TBOGI.update_layout(
                    title="Histórico TBOGI",
                    xaxis_title="Data",
                    yaxis_title="Valor",
                    template="plotly_white",
                    height=380,
                    legend=dict(
                        orientation="h",      # legenda horizontal
                        yanchor="bottom",
                        y=1.02,               # um pouco acima do gráfico
                        xanchor="center",
                        x=0.5                 # centralizado
                    )
                )

                fig_TBOGI.update_yaxes(range=[0, 30])
                st.plotly_chart(fig_TBOGI, use_container_width=True)
            except Exception as e:
                print(f"Erro ao plotar gráfico TBOGI: {e}")
                fig_TBOGI = go.Figure()
        
        
        st.divider()

        st.markdown("<div class='section-title'>Dados do censo</div>", unsafe_allow_html=True)
        st.dataframe(df_censo_f, hide_index=True)

        st.divider()

        st.markdown("<div class='section-title'>Tarefas de manutenção</div>", unsafe_allow_html=True)
        st.dataframe(df_SAT_f, hide_index=True)

        


