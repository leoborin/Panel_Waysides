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

# -----------------------------
# Funções de gráfico
# -----------------------------
# def semicircle_gauge(title:str, value:int, color:str=ACCENT) -> go.Figure:
#     v = max(0, min(100, int(value)))
#     values = [v, 100 - v, 100]
#     fig = go.Figure(go.Pie(values=values, hole=0.7, rotation=180, sort=False, showlegend = False,
#                             marker=dict(colors=[color, "#E1ECF4", "rgba(0,0,0,0)"]),
#                             textinfo="none"))
#     fig.add_annotation(text=f"<b>{v}%</b><br><span style='color:{MUTED};font-size:12px;'>SCORE</span>",
#                        showarrow=False, font=dict(size=20), x=0.5, y=0.5)
#     fig.add_annotation(text=f"<b>{title}</b>", showarrow=False, x=0.5, y=1.2,
#                        font=dict(size=14, color=TEXT))
#     fig.update_layout(height=220, margin=dict(l=10, r=10, t=40, b=0), paper_bgcolor="white")
#     return fig

def semicircle_gauge(title: str, value: int, color: str = ACCENT) -> go.Figure:
    v = max(0, min(100, int(value)))

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=v,
        number={"suffix": "%", "font": {"size": 20}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color, "line": {"width": 0}},
            "bgcolor": "#E1ECF4",
            "shape": "angular"
        },
        title={"text": f"<b>{title}</b>", "font": {"size": 18}}
    ))

    fig.update_layout(
        height=150,
        margin=dict(l=10, r=10, t=50, b=0),
        paper_bgcolor="white"
    )

    return fig
# Line plot com média móvel
def line_plot_mm(df, x, y, title, y_title, color=PRIMARY):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[x], y=df[y], mode="lines+markers",
                             line=dict(color=color, width=2),
                             marker=dict(size=5, color=ACCENT), name=y_title))
    fig.add_trace(go.Scatter(x=df[x], y=df[y].rolling(3).mean(), mode="lines",
                             line=dict(color="#9EB6C3", width=2, dash="dash"), name="Média móvel (3)"))
    fig.update_layout(title=title, height=250, margin=dict(l=10,r=10,t=40,b=10),
                      paper_bgcolor="white", plot_bgcolor="white",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text=y_title)
    return fig

def line_plot_real(df, x, y, z, title, y_title, color=PRIMARY):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[x], y=df[y], mode="lines+markers",
                             line=dict(color=color, width=2),
                             marker=dict(size=5, color=ACCENT), name=y_title))
    fig.add_trace(go.Scatter(x=df[x], y=df[z], mode="lines",
                             line=dict(color="#9EB6C3", width=2, dash="dash"), name="Contratada"))
    fig.update_layout(title=title, height=250, margin=dict(l=10,r=10,t=40,b=10),
                      paper_bgcolor="white", plot_bgcolor="white",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text=y_title)
    return fig

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
#df_trkv = dfs["df_trkv"]
df_WCM = dfs["df_WCM"]
df_z369 = dfs["df_z369"]
df_z851 = dfs["df_z851"]
df_z1568 = dfs["df_z1568"]
df_tbogi = dfs["df_tbogi"]

# SHAREPOINT | Enriquecimento – Sistema da Falha
df_avarias = pd.read_excel(
    r'Base_avarias.xlsx',
    engine='openpyxl'
)

# Dados simulados
np.random.seed(42)
dates = pd.date_range(datetime.today() - timedelta(days=180), periods=26, freq="7D")
df_dispon = pd.DataFrame({"data": dates, "real": np.clip(240 + np.cumsum(np.random.randn(len(dates))), 230, 250), "contratada": np.full(len(dates), 243)})

# IMPORTANDO DADOS DO TRKV PROVISORIAMENTE
def function_to_get_data(MONGO_URI_PRD, DB_NAME_PRD, COLLECTION_NAME):
    client = MongoClient(MONGO_URI_PRD)
    db = client[DB_NAME_PRD]
    collection = db[COLLECTION_NAME]
    # Buscar últimos 5 documentos ordenados por timestamp decrescente
    docs = list(collection.find().sort("timestamp", -1))
    if docs:
        # Converter lista de documentos para DataFrame, removendo coluna _id
        df = pd.DataFrame(docs).drop(columns=['_id'], errors='ignore')
        if 'json_documents' in df.columns:
            df['json_documents'] = df['json_documents'].fillna('').astype(str)
        return df
    else:
        return pd.DataFrame()  # DataFrame vazio
    
# Dados do Mongo
# MONGO_URI_PRD = 'mongodb+srv://inteligencia_dados:AR5VxIUwpWIt3VlK@rumo-dev.eqds1.mongodb.net/?authSource=admin'
# DB_NAME_PRD = 'inteligencia_MR'
MONGO_URI_PRD = st.secrets.database_prod.MONGO_URI_PRD
DB_NAME_PRD = st.secrets.database_prod.DB_NAME_PRD

# Importação dos dados do Truck View
df_trkv = function_to_get_data(
            MONGO_URI_PRD, DB_NAME_PRD, 'TRKV_treated'#,
            #query={
            #    'tipo_do_veículo': {
            #        '$not': {
            #            '$regex': 'L'
            #        }
            #    }}
)
#--------------------------------------------------------------------------------
## Filtro Global – MODELO
#--------------------------------------------------------------------------------
df_z369['ATIVO'] = df_z369['ATIVO'].astype(str).str.zfill(10)

modelos = sorted(df_z851['MODELO'].dropna().unique())

# modelo_sel = st.multiselect(
#     "Modelo do vagão",
#     modelos,
#     default=modelos
# )

st.markdown(
    "<span style='font-size:14px;font-weight:600;'>Modelo do vagão:</span>",
    unsafe_allow_html=True
)

modelo_sel = st.multiselect(
    label="Modelo do vagão",
    options=modelos,
    default=modelos,
    label_visibility="collapsed"
)

vagoes_validos = (
    df_z851
    .loc[df_z851['MODELO'].isin(modelo_sel), 'EQUNR']
    .unique()
)

df_z369_f = df_z369[df_z369['ATIVO'].isin(vagoes_validos)].copy()
df_z369_f['dt_abertura_trated'] = pd.to_datetime(df_z369_f['dt_abertura_trated'])
df_z369_f = df_z369_f[df_z369_f['dt_abertura_trated'].dt.year <= 2100]

df_avarias['Sistema'] = (
    df_avarias['Combinado2']
    .fillna('')
    .str.split('|', n=1)
    .str[0]
    .replace('', np.nan)
)

df_z369_f = (
    df_z369_f
    .merge(
        df_avarias[['CODFalha', 'Sistema']].drop_duplicates(),
        how='left',
        left_on='Cod Falha',
        right_on='CODFalha'
    )
    .drop(columns='CODFalha')
)

df_z369_f['Sistema'] = df_z369_f['Sistema'].map({
    'FR': 'FREIO',
    'SE': 'SUPERESTRUTURA',
    'CCT': 'CCT',
    'RD': 'RODEIRO',
    'TR': 'TRUQUE'
})

# KPIs + Top 5 Defeitos 
qtd_vgs = df_z851['EQUNR'].nunique()

def contar(texto):
    return df_z369_f[
        (df_z369_f['STATUS'] == 'MSPN') &
        (df_z369_f['TEXTO'].str.contains(texto, case=False, na=False))
    ]['ATIVO'].nunique()

kpis = [
    ("Truck view", contar("TRKV"), "Ocorrências", SUCCESS),
    ("T-BOGI", contar("T-BOGI"), "Ocorrências", WARNING),
    ("TADS", contar("ACÚSTICO"), "Ocorrências", DANGER),
    ("WCM", contar("WCM"), "Ocorrências", SUCCESS),
]

top5 = (
    df_z369_f[
        (df_z369_f["STATUS"] == "MSPN") &
        (df_z369_f["TP NOTA"].isin(["M1", "M2"]))
    ]["TEXTO"]
    .value_counts()
    .head(5)
    .reset_index(name="QUANTIDADE")
)

# ===============================
# KPIs
# ===============================
st.markdown("<div class='section-title'>Indicadores principais</div>", unsafe_allow_html=True)

cols = st.columns(4)

for i, (lbl, val, sub, color) in enumerate(kpis):
    with cols[i]:
        st.markdown(f"""
        <div style="
            background-color:{CARD_BG};
            border:1px solid {BORDER};
            border-radius:10px;
            padding:14px;
            text-align:center;
        ">
            <div style="color:{MUTED}; font-size:14px;">{lbl}</div>
            <div style="color:{TEXT}; font-size:28px; font-weight:700;">{val}</div>
            <div style="color:{color}; font-size:12px;">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

#st.write("")
st.divider()

# ===============================
# SLA DE PÁTIOS
# ===============================
st.markdown("<div class='section-title'>SLA de pátios</div>", unsafe_allow_html=True)

g1, g2, g3, g4, g5, g6, g7, g8 = st.columns(8)
g1.plotly_chart(semicircle_gauge("ZRO", 41, SUCCESS), use_container_width=True)
g2.plotly_chart(semicircle_gauge("ZRX", 70, WARNING), use_container_width=True)
g3.plotly_chart(semicircle_gauge("ZTO", 85, DANGER), use_container_width=True)
g4.plotly_chart(semicircle_gauge("ZAR", 90, DANGER), use_container_width=True)
g5.plotly_chart(semicircle_gauge("ZZZ", 57, SUCCESS), use_container_width=True)
g6.plotly_chart(semicircle_gauge("TOM", 73, WARNING), use_container_width=True)
g7.plotly_chart(semicircle_gauge("TRO", 68, SUCCESS), use_container_width=True)
g8.plotly_chart(semicircle_gauge("PRV", 70, SUCCESS), use_container_width=True)

st.divider()
# ===============================
# TOP 5 DEFEITOS
# ===============================
st.markdown("<div class='section-title'>Top 5 defeitos mais recorrentes</div>", unsafe_allow_html=True)
# st.subheader("Top 5 defeitos mais recorrentes")

col_l, col_r = st.columns([7, 3])

with col_l:
    fig_top5 = px.bar(
        top5,
        x="QUANTIDADE",
        y="TEXTO",
        orientation="h",
        text="QUANTIDADE",
        #title="Top 5 defeitos mais frequentes",
        color_discrete_sequence=["#003865"]
    )

    fig_top5.update_layout(
        xaxis_title="Quantidade de Ocorrências",
        yaxis_title="Descrição do Defeito",
        yaxis=dict(autorange="reversed"),
        showlegend=False,
        height=300
    )

    st.plotly_chart(fig_top5, use_container_width=True)

# with col_r:
#     st.markdown(
#     """
#     <div style="
#         background-color:#F3F6FA;
#         border:1px solid #D0D7E2;
#         border-radius:10px;
#         padding:12px 16px;
#         font-size:14px;
#     ">
#         <b>Critério do ranking</b><br><br>
#         • Apenas notas com status <b>MSPN</b><br>
#         • Considera somente <b>M1 e M2</b><br>
#         • Respeita os filtros globais da página
#     </div>
#     """,
#     unsafe_allow_html=True
# )
    
with col_r:
    st.markdown(
        """
        <div class="center-vertical">
            <div style="
                height:300px;
                background-color:#F3F6FA;
                border:1px solid #D0D7E2;
                border-radius:10px;
                padding:12px 16px;
                font-size:14px;
            ">
                <b>Critério do ranking</b><br><br>
                • Apenas notas com status <b>MSPN</b><br>
                • Considera somente <b>M1 e M2</b><br>
                • Respeita os filtros globais da página
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
st.divider()
#8️⃣ EVOLUÇÃO + HEATMAP
st.markdown("<div class='section-title'>Evolução de abertura de notas por sistema</div>", unsafe_allow_html=True)
# st.subheader('Evolução de abertura de notas por sistema')

tipos_nota = sorted(df_z369_f['TP NOTA'].dropna().unique())
abas = st.tabs(tipos_nota)

for aba, tp in zip(abas, tipos_nota):
    with aba:
        df_tp = df_z369_f[df_z369_f['TP NOTA'] == tp].copy()

        if df_tp.empty:
            st.warning('Sem dados para este tipo de nota.')
            continue

        col1, col2 = st.columns(2)

        # ===== Evolução =====
        with col1:
            df_tp['MES'] = (
                df_tp['dt_abertura_trated']
                .dt.to_period('M')
                .dt.to_timestamp()
            )

            df_g = (
                df_tp
                .groupby(['MES', 'Sistema'])
                .size()
                .reset_index(name='QTD')
            )

            df_g['PERCENTUAL'] = (
                df_g['QTD'] /
                df_g.groupby('MES')['QTD'].transform('sum') * 100
            )

            fig_area = px.area(
                df_g,
                x='MES',
                y='PERCENTUAL',
                color='Sistema',
                groupnorm='percent',
                labels={'PERCENTUAL': '% de notas'}
            )

            fig_area.update_layout(
                yaxis=dict(ticksuffix='%'),
                hovermode='x unified'
            )

            # st.plotly_chart(fig_area, use_container_width=True)
            st.plotly_chart(
                fig_area,
                use_container_width=True,
                key=f"fig_area_{tp}"
            )

        # ===== Heatmap =====
        with col2:
            sistema = st.selectbox(
                'Sistema',
                sorted(df_tp['Sistema'].dropna().unique()),
                key=f'sis_{tp}'
            )

            df_h = (
                df_tp[df_tp['Sistema'] == sistema]
                .assign(
                    mes=lambda x: (
                        x['dt_abertura_trated']
                        .dt.to_period('M')
                        .dt.to_timestamp()
                    )
                )
                .groupby(['TEXTO', 'mes'])
                .size()
                .reset_index(name='qtd')
            )

            top_txt = (
                df_h.groupby('TEXTO')['qtd']
                .sum()
                .sort_values(ascending=False)
                .head(20)
                .index
            )

            heat = (
                df_h[df_h['TEXTO'].isin(top_txt)]
                .pivot(index='TEXTO', columns='mes', values='qtd')
                .fillna(0)
            )

            fig_heat = px.imshow(
                heat,
                aspect='auto',
                color_continuous_scale='Blues'
            )

            fig_heat.update_yaxes(autorange='reversed')
            # st.plotly_chart(fig_heat, use_container_width=True)
            st.plotly_chart(
                fig_heat,
                use_container_width=True,
                key=f"fig_heat_{tp}_{sistema}"
            )

st.divider()
st.markdown("<div class='section-title'>Disponibilidade real x contratada</div>", unsafe_allow_html=True)
# st.subheader("Disponibilidade real x contratada")

st.plotly_chart(line_plot_real(df_dispon, "data", "real", "contratada", "", "Real", color=SUCCESS), use_container_width=True)

# ----------------------------------------------------------------------------------------------------
# HISTOGRAMA DE CUNHAS
# ----------------------------------------------------------------------------------------------------
# Função para tratar outliers
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

cof_Outlier = 0.2
df_TRKV_2 = tratar_outliers_trkv(df_trkv) #df_TRKV_2 são todos os dados do truck view com indicação de outliers na coluna 

# Mapeamento de alarme de cunha
MAP_WEDGE = {
    2: 45,
    3: 57,
    4: 64,
    5: 57,
}
df_TRKV_2['Alarme'] = (
    df_TRKV_2['WedgeTypeCode']
    .map(MAP_WEDGE)
    .fillna("inválido")
)

# Mapeamento de tipo de truque
MAP_TRUQUE = {
    2: "Ride Control",
    3: "Barber",
    4: "Ride Master",
    5: "Motion Control",
}

df_TRKV_2['Truque'] = (
    df_TRKV_2['WedgeTypeCode']
    .map(MAP_TRUQUE)
    .fillna("inválido")
)

# Desconsiderar registros com STATUS_out = DESCARTAR (jogar outliers fora)
df_TRKV_3 = df_TRKV_2[df_TRKV_2['STATUS_out'] == "OK"]

# Desconsiderar registros com 'Header_TrainDirection' = N
df_TRKV_3 = df_TRKV_3[df_TRKV_3['Header_TrainDirection'] == "S"]

# Desconsiderar registros com concatenatedCarID = 000000None ou 0000000nan
df_TRKV_3 = df_TRKV_3[df_TRKV_3['concatenatedCarID'] != "000000None"]
df_TRKV_3 = df_TRKV_3[df_TRKV_3['concatenatedCarID'] != "0000000nan"]

# Jogar fora colunas desnecessárias
cols_drop = [
    'CarSequenceNumber','CarOrientation','CarType',
    'TruckFields','TruckIDs','TruckValues','timestr',
    'Header_TrainSequenceNumber','data_sincronizacao',
    'max_valor','min_3','max_3'
]
df_TRKV_3 = df_TRKV_3.drop(columns=cols_drop, errors='ignore')

# Últimos tratamentos do df_TRKV
# -----------------------------
df_TRKV_3["concatenatedCarID"] = df_TRKV_3["concatenatedCarID"].astype(str)
df_TRKV_3["timestamp"] = pd.to_datetime(df_TRKV_3["timestamp"], errors="coerce")
df_TRKV_3["Alarme"] = pd.to_numeric(
    df_TRKV_3["Alarme"],
    errors="coerce"
).astype("float64")

## Pegar a data da última RR no df_z851 e fazer um merge com o df_TRKV_3

# Preparar dataframe dimensão (df_z851)
df_z851["concatenatedCarID"] = df_z851["EQUNR"]
df_z851["ULTIMA_RR"] = pd.to_datetime(df_z851["ULTIMA_RR"], errors="coerce")

df_dim = df_z851[["concatenatedCarID", "ULTIMA_RR"]].drop_duplicates()

# Juntar dimensão com fatos
df_TRKV_4 = df_TRKV_3.merge(df_dim, on="concatenatedCarID", how="left")

# Filtrar somente registros após última RG
# -----------------------------
df_TRKV_4 = df_TRKV_4[df_TRKV_4["timestamp"] >= df_TRKV_4["ULTIMA_RR"]]

#Preparando histograma
colunas_cunha = [
    'A#L_1', 'A#L_2', 'A#R_1', 'A#R_2',
    'B#L_1', 'B#L_2', 'B#R_1', 'B#R_2'
]

# 1️⃣ Substituir zeros por NaN
df = df_TRKV_4.copy()
df[colunas_cunha] = df[colunas_cunha].replace(0, np.nan)

# 2️⃣ Média das cunhas por vagão + modelo do truque
df_media = (
    df.groupby('concatenatedCarID')
      .agg({**{c: 'mean' for c in colunas_cunha},
            'Truque': lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan})
      .reset_index()
)

# 3️⃣ Maior média entre as 8 cunhas
df_media['altura_cunha_max_media'] = df_media[colunas_cunha].max(axis=1)

# 4️⃣ Resultado final
histograma = df_media[['concatenatedCarID', 'Truque', 'altura_cunha_max_media']]

# Adicionando modelo do vagão
df_dim2 = df_z851[["concatenatedCarID", "MODELO"]].drop_duplicates()
histograma2 = histograma.merge(df_dim2, on="concatenatedCarID", how="left")

# Limites por truque
limites = {
    "Ride Control": 45,
    "Barber": 57,
    "Ride Master": 64,
    "Motion Control": 57
}

# ---- FILTRO ----
truques = sorted(histograma2["Truque"].dropna().unique())
truque_sel = st.selectbox("Filtrar tipo de truque:", ["Todos"] + list(truques))

if truque_sel != "Todos":
    df_plot = histograma2[histograma2["Truque"] == truque_sel]
else:
    df_plot = histograma2.copy()

# ---- HISTOGRAMA ----
fig = px.histogram(
    df_plot,
    x="altura_cunha_max_media",
    nbins=30,
    title="Histograma - Altura de Cunha"
)

# ---- LINHA DE LIMITE ----
if truque_sel in limites:
    fig.add_vline(
        x=limites[truque_sel],
        line_dash="dash",
        annotation_text=f"Limite {limites[truque_sel]}",
        annotation_position="top"
    )

st.plotly_chart(fig, use_container_width=True)