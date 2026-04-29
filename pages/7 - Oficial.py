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
import matplotlib.pyplot as plt
# import seaborn as sns
import glob
import os
import unicodedata
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from sklearn.linear_model import LinearRegression
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import r2_score

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

# st.markdown("""
#     <style>
#     .stApp {
#         background-color: #F2F5F6;
#     }
#     </style>
# """, unsafe_allow_html=True)

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
  border-radius: 0px;       /* Cantos retos arredondados */
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

# # =======================================
# Funções de gráfico
# # =======================================
def grafico_rosca_truques(
    df_z851,
    truques_dim,
    status_validos=("1", "2"),
    limite_percentual=0.05
):
    """
    Gera gráfico de rosca da distribuição de tipos de truque.
    
    Parâmetros:
    - df_z851: DataFrame principal da frota
    - truques_dim: DataFrame com equnr e Truque
    - status_validos: tupla com status considerados na frota ativa
    - limite_percentual: percentual mínimo para exibir valor dentro da fatia
    """

    # -------------------------
    # Merge com dimensão
    # -------------------------

    truques_dim = truques_dim.rename(columns={
        "concatenatedcarid": "equnr"
    })[["equnr", "truque"]]

    df = df_z851.merge(truques_dim, on="equnr", how="left")

    # -------------------------
    # Filtro de status
    # -------------------------

    df = df[df["status"].isin(status_validos)]

    # -------------------------
    # Contagem
    # -------------------------

    df_count = (
        df["truque"]
        .value_counts()
        .reset_index()
    )

    df_count.columns = ["truque", "quantidade"]
    df_count = df_count.sort_values("quantidade", ascending=False)

    total = df_count["quantidade"].sum()

    df_count["percentual"] = df_count["quantidade"] / total

    # -------------------------
    # Cores fixas
    # -------------------------

    mapa_cores = {
        "Ride Master": "#0D3B66",
        "Ride Control": "#5EA9DD",
        "Motion Control": "#1E9F7F",
        "Barber": "#7FE06C"
    }

    cores = [
        mapa_cores.get(tipo, "#B0B0B0")
        for tipo in df_count["truque"]
    ]

    # -------------------------
    # Texto interno
    # -------------------------

    texto_interno = [
        f"{p:.1%}" if p >= limite_percentual else ""
        for p in df_count["percentual"]
    ]

    # -------------------------
    # Criar gráfico
    # -------------------------

    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=df_count["truque"],
        values=df_count["quantidade"],
        hole=0.65,
        marker=dict(colors=cores, line=dict(color="white", width=2)),
        text=texto_interno,
        textinfo="text",
        textposition="inside",
        hovertemplate=
            "<b>%{label}</b><br>" +
            "Quantidade: %{value}<br>" +
            "Percentual: %{percent}<br>" +
            "<extra></extra>",
        sort=False
    ))

    fig.add_annotation(
        text=f"<b style='font-size:28px'>{total}</b><br>"
             "<span style='font-size:14px;color:gray'>Vagões</span>",
        x=0.5,
        y=0.5,
        showarrow=False
    )

    fig.update_layout(
        #template="plotly_white",
        margin=dict(t=40, b=20, l=20, r=20),
        title = "Distribuição de truques na frota",
        legend_title="Tipo de Truque",
        height=380
    )
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5
        ),
        paper_bgcolor="rgba(0,0,0,0)",  # fundo total transparente
        plot_bgcolor="rgba(0,0,0,0)"    # área interna transparente
    )

    return fig

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

# Valores limites por truque - configuração dos gráficos
def get_ylim_por_truque(df):
    if "truque" not in df.columns:
        return None

    truque_series = df["truque"].dropna()
    if truque_series.empty:
        return None

    truque = truque_series.iloc[0]

    if truque == "Ride Control":
        return (15, 52)
    elif truque == "Ride Master":
        return (30, 70)

    return None
# =======================================
## Funções de tratamento
# =======================================
def padronizar_colunas(df):
    df = df.copy()
    
    df.columns = (
        df.columns
        .str.strip()  # remove espaços no começo/fim
        .str.lower()  # tudo minúsculo
        .str.replace(' ', '_', regex=False)  # espaço -> _
        .map(lambda x: unicodedata.normalize('NFKD', x)
             .encode('ascii', 'ignore')
             .decode('utf-8'))  # remove acentos
    )
    
    return df

# Padronizar identificação do ativo para 7 números + 3 letras
def padronizar_identificacao(valor):
    if pd.isna(valor):
        return None
    
    valor = str(valor).strip().upper()
    
    # Extrai letras e números
    letras = re.findall(r'[A-Z]+', valor)
    numeros = re.findall(r'\d+', valor)
    
    if letras and numeros:
        return numeros[0].zfill(7) + letras[0]
    
    return None

def tratar_outliers_trkv(df, cof_Outlier=0.2):

    """
    Remove medições anômalas com base nas 3 últimas medições por key.

    - Valor é outlier se:
        valor > max_3 * (1 + cof_Outlier)
        valor < min_3 * (1 - cof_Outlier)
    """

    df = df.copy()

    df["key"] = df["caridnumber"].astype(int)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.sort_values(["key", "timestamp"])

    # Cálculo da força máxima entre os 8 sensores (ignora NaN automaticamente)
    sensores = [
        "a#l_1","a#l_2","a#r_1","a#r_2",
        "b#l_1","b#l_2","b#r_1","b#r_2"
    ]

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

    # Regra de outlier
    df["descartar"] = (
        (df["max_valor"] > df["max_3"] * (1 + cof_Outlier)) |
        (df["max_valor"] < df["min_3"] * (1 - cof_Outlier)) |
        (df["max_valor"] == 0)
    )

    df["status_out"] = df["descartar"].map(
        {True: "descartar", False: "OK"}
    )

    return df

@st.cache_data
def preparar_dados_trkv(
    df_trkv_f,
    df_z851,
    truques_dim,
    cof_outlier=0.2,
    sensores=None
):
    """
    Aplica filtros, tratamento de outliers e preparação final dos dados TRKV.

    Parâmetros:
    ----------
    df_trkv_f : DataFrame
    df_z851 : DataFrame
    truques_dim : DataFrame
    cof_outlier : float (default=0.2)
    sensores : list (opcional)

    Retorno:
    -------
    DataFrame tratado
    """

    df_trkv_f = df_trkv_f.copy()
    df_z851 = df_z851.copy()

    # -------------------------
    # Sensores padrão
    # -------------------------
    if sensores is None:
        sensores = [
            "a#l_1","a#l_2","a#r_1","a#r_2",
            "b#l_1","b#l_2","b#r_1","b#r_2"
        ]

    # -------------------------
    # 1. Filtro direção
    # -------------------------
    df_trkv_f = df_trkv_f[
        df_trkv_f['header_traindirection'] == "S"
    ]

    # -------------------------
    # 2. Merge com truque
    # -------------------------
    truques_dim = (
        truques_dim
        .rename(columns={'vg_+_serie': 'concatenatedcarid'})
        [['concatenatedcarid', 'truque']]
    )

    df_trkv_f = df_trkv_f.merge(
        truques_dim,
        on="concatenatedcarid",
        how="left"
    )

    df_trkv_f = df_trkv_f[
        df_trkv_f["truque"].isin(["Ride Control", "Ride Master"])
    ]

    # -------------------------
    # 3. Remoção física inválida
    # -------------------------
    mask_rc = df_trkv_f["truque"] == "Ride Control"
    mask_rm = df_trkv_f["truque"] == "Ride Master"

    df_trkv_f.loc[mask_rc, sensores] = df_trkv_f.loc[mask_rc, sensores].mask(
        (df_trkv_f.loc[mask_rc, sensores] < 15) |
        (df_trkv_f.loc[mask_rc, sensores] > 52)
    )

    df_trkv_f.loc[mask_rm, sensores] = df_trkv_f.loc[mask_rm, sensores].mask(
        (df_trkv_f.loc[mask_rm, sensores] < 30) |
        (df_trkv_f.loc[mask_rm, sensores] > 70)
    )

    # -------------------------
    # 4. Outliers
    # -------------------------
    # global cof_Outlier
    # cof_Outlier = cof_outlier  # usado na sua função

    # df_trkv_f = tratar_outliers_trkv(df_trkv_f)
    df_trkv_f = tratar_outliers_trkv(df_trkv_f, cof_outlier)

    df_trkv_f = df_trkv_f[
        df_trkv_f['status_out'] == "OK"
    ]

    # -------------------------
    # 5. Remover linhas vazias
    # -------------------------
    df_trkv_f = df_trkv_f.dropna(
        subset=sensores,
        how='all'
    )

    # -------------------------
    # 6. Drop colunas inúteis
    # -------------------------
    cols_drop = [
        'carsequencenumber','carorientation','cartype',
        'truckfields','truckids','truckvalues','timestr',
        'header_trainsequencenumber','data_sincronizacao'
    ]

    df_trkv_f = df_trkv_f.drop(
        columns=cols_drop,
        errors='ignore'
    )

    # -------------------------
    # 7. Mapeamento de alarme
    # -------------------------
    MAP_WEDGE = {
        "Ride Control": 45,
        "Barber": 57,
        "Ride Master": 64,
        "Motion Control": 57,
    }

    df_trkv_f['alarme'] = (
        df_trkv_f['truque']
        .map(MAP_WEDGE)
        .fillna("inválido")
    )

    # -------------------------
    # 8. Ajustes finais
    # -------------------------
    df_trkv_f["concatenatedcarid"] = df_trkv_f["concatenatedcarid"].astype(str)
    df_trkv_f["timestamp"] = pd.to_datetime(df_trkv_f["timestamp"], errors="coerce")

    df_trkv_f["alarme"] = pd.to_numeric(
        df_trkv_f["alarme"],
        errors="coerce"
    ).astype("float64")

    # -------------------------
    # 9. Filtro pós-RR
    # -------------------------
    df_z851["concatenatedcarid"] = df_z851["equnr"]
    df_z851["ultima_rr"] = pd.to_datetime(df_z851["ultima_rr"], errors="coerce")

    df_dim = df_z851[
        ["concatenatedcarid", "ultima_rr"]
    ].drop_duplicates()

    df_trkv_f = df_trkv_f.merge(
        df_dim,
        on="concatenatedcarid",
        how="left"
    )

    df_trkv_f = df_trkv_f[
        df_trkv_f["timestamp"] >= df_trkv_f["ultima_rr"]
    ]

    return df_trkv_f, truques_dim

# ===========================================================
# Funções de modelagem
# ===========================================================
# Converte timestamp para número
# Usa só caso for fazer com data, e nao km
def converter_timestamp_para_numero(df, col="timestamp"):
    df = df.copy()
    
    # converte para datetime (garantia)
    df[col] = pd.to_datetime(df[col])
    x_base = df["timestamp"].min()
    # converte para segundos (float)
    # df["x_num"] = df[col].astype("int64") / 1e9

    # converter para dias (mais seguro)
    df["x_num"] = (df["timestamp"] - x_base).dt.total_seconds() / 86400
    
    return df

# Modelo: regressão isotônica + regressão linear
def treinar_pipeline(df, col, min_pontos = 10):
    
    #x = df["km_acumulado"].values # Km acumulado
    df = converter_timestamp_para_numero(df) # Timestamp

    # x = df["x"].values # Km acumulado
    x = df["x_num"].values # Timestamp
    y = df[col].values

    mask = (~np.isnan(x)) & (~np.isnan(y)) & (y > 0)

    #if mask.sum() < 3:
    #    return None, None
    # 🔴 NOVA REGRA
    if mask.sum() < min_pontos:
        #print(f"[IGNORADO] Poucos dados ({mask.sum()}) - Cunha {col}")
        return None, None
    
    x_valid = x[mask]
    y_valid = y[mask]

    # 🔵 Isotônica (suaviza + monotônico)
    iso = IsotonicRegression(increasing=True)
    y_iso = iso.fit_transform(x_valid, y_valid)

    # 🔵 Regressão linear
    model = LinearRegression(positive=True)
    model.fit(x_valid.reshape(-1, 1), y_iso)

    return iso, model

# Avaliação do modelo
def avaliar_modelo(df, model, col):
    
    # x = df["km_acumulado"].values # km acumulado
    df = converter_timestamp_para_numero(df) # timestamp

    # x = df["x"].values # km acumulado
    x = df["x_num"].values # timestamp
    y_real = df[col].values

    mask = (~np.isnan(x)) & (~np.isnan(y_real)) & (y_real > 0)

    if mask.sum() == 0:
        return None

    x_valid = x[mask]
    y_real_valid = y_real[mask]

    y_pred = model.predict(x_valid.reshape(-1, 1))
    y_pred = np.maximum.accumulate(y_pred)

    erro = y_real_valid - y_pred

    mae = np.mean(np.abs(erro))
    rmse = np.sqrt(np.mean(erro**2))
    r2 = r2_score(y_real_valid, y_pred)

    return mae, rmse, r2

def get_limite_alarme(df):
    if "truque" not in df.columns:
        return None

    truque_series = df["truque"].dropna()
    if truque_series.empty:
        return None

    truque = truque_series.iloc[0]

    if truque == "Ride Control":
        return 45
    elif truque == "Ride Master":
        return 64

    return None

def tem_dados_suficientes(grupo, colunas, min_pontos=10):

    for col in colunas:
        y = grupo[col]
        validos = y[(~y.isna()) & (y > 0)]

        if len(validos) >= min_pontos:
            return True  # pelo menos uma cunha confiável

    return False

def prever_1_ano_e_limite(df, model, col):

    df = df.sort_values("timestamp")
    df = converter_timestamp_para_numero(df)

    limite = get_limite_alarme(df) 
    if limite is None:
        return None

    x = df["x_num"].values
    y = df[col].values

    mask = (~np.isnan(x)) & (~np.isnan(y)) & (y > 0)

    if mask.sum() < 3:
        return None

    x_valid = x[mask]
    y_valid = y[mask]

    # 📍 estado atual
    x_max = x_valid.max()
    y_atual = y_valid[-1]

    # 🔮 horizonte 1 ano
    horizonte_dias = 365
    x_futuro = np.linspace(x_max, x_max + horizonte_dias, 100)

    y_futuro = model.predict(x_futuro.reshape(-1, 1))
    y_futuro = np.maximum.accumulate(
        np.concatenate([[y_valid[-1]], y_futuro])
    )[1:]

    y_1ano = y_futuro[-1]

    # 🚨 cruzamento do limite
    cruzou = y_futuro >= limite

    if cruzou.any():
        idx = np.argmax(cruzou)
        x_cross = x_futuro[idx]

        x_base = df["timestamp"].min()
        data_cross = x_base + pd.to_timedelta(x_cross, unit="D")
    else:
        data_cross = None

    return {
        "valor_atual": y_atual,
        "valor_1ano": y_1ano,
        "limite": limite,
        "data_cruzamento": data_cross
    }

# ===================================
# Funções de pipeline
# ===================================
# def rodar_prognostico(df_trkv_f, truques_dim, mae_max=1.5):

#     resultados_prognostico = []
#     ignorados = []

#     colunas_cunha = [
#         "a#l_1","a#l_2","a#r_1","a#r_2",
#         "b#l_1","b#l_2","b#r_1","b#r_2"
#     ]

#     for vagao, grupo in df_trkv_f.groupby("concatenatedcarid"):

#         if not tem_dados_suficientes(grupo, colunas_cunha):
#             ignorados.append({"vagao": vagao, "motivo": "sem_dados"})
#             continue

#         for col in colunas_cunha:

#             iso, model = treinar_pipeline(grupo, col, min_pontos=10)

#             if model is None:
#                 continue

#             avaliacao = avaliar_modelo(grupo, model, col)
#             if avaliacao is None:
#                 continue

#             mae, rmse, r2 = avaliacao

#             if mae > mae_max:
#                 continue

#             # taxa
#             taxa = None
#             if hasattr(model, "coef_"):
#                 taxa = model.coef_[0]
#             elif hasattr(model, "named_steps"):
#                 for step in model.named_steps.values():
#                     if hasattr(step, "coef_"):
#                         taxa = step.coef_[0]
#                         break

#             resultado = prever_1_ano_e_limite(grupo, model, col)
#             if resultado is None:
#                 continue

#             resultados_prognostico.append({
#                 "vagao": vagao,
#                 "cunha": col,
#                 "valor_atual": resultado["valor_atual"],
#                 "valor_1ano": resultado["valor_1ano"],
#                 "limite": resultado["limite"],
#                 "data_cruzamento": resultado["data_cruzamento"],
#                 "mae": mae,
#                 "rmse": rmse,
#                 "r2": r2,
#                 "taxa_desgaste": taxa
#             })

#     df_prognostico = pd.DataFrame(resultados_prognostico)
#     df_ignorados = pd.DataFrame(ignorados)

#     df_prognostico["vai_estourar"] = (
#         df_prognostico["valor_1ano"] >= df_prognostico["limite"]
#     )

#     df_prognostico = df_prognostico.merge(
#         truques_dim,
#         left_on="vagao",
#         right_on="concatenatedcarid",
#         how="left"
#     ).drop(columns=["concatenatedcarid"])

#     return df_prognostico, df_ignorados

def processar_vagao(args):
    vagao, grupo, colunas_cunha, mae_max = args

    resultados = []
    ignorados = []

    if not tem_dados_suficientes(grupo, colunas_cunha):
        ignorados.append({"vagao": vagao, "motivo": "sem_dados"})
        return resultados, ignorados

    for col in colunas_cunha:

        iso, model = treinar_pipeline(grupo, col, min_pontos=10)

        if model is None:
            continue

        avaliacao = avaliar_modelo(grupo, model, col)
        if avaliacao is None:
            continue

        mae, rmse, r2 = avaliacao

        if mae > mae_max:
            continue

        # taxa
        taxa = None
        if hasattr(model, "coef_"):
            taxa = model.coef_[0]

        resultado = prever_1_ano_e_limite(grupo, model, col)
        if resultado is None:
            continue

        resultados.append({
            "vagao": vagao,
            "cunha": col,
            "valor_atual": resultado["valor_atual"],
            "valor_1ano": resultado["valor_1ano"],
            "limite": resultado["limite"],
            "data_cruzamento": resultado["data_cruzamento"],
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
            "taxa_desgaste": taxa
        })

    return resultados, ignorados 

def rodar_prognostico_paralelo(df_trkv_f, truques_dim, mae_max=1.5):

    colunas_cunha = [
        "a#l_1","a#l_2","a#r_1","a#r_2",
        "b#l_1","b#l_2","b#r_1","b#r_2"
    ]

    tarefas = [
        (vagao, grupo, colunas_cunha, mae_max)
        for vagao, grupo in df_trkv_f.groupby("concatenatedcarid")
    ]

    resultados_prognostico = []
    ignorados = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        for res, ign in executor.map(processar_vagao, tarefas):
            resultados_prognostico.extend(res)
            ignorados.extend(ign)

    df_prognostico = pd.DataFrame(resultados_prognostico)
    df_ignorados = pd.DataFrame(ignorados)

    df_prognostico["vai_estourar"] = (
        df_prognostico["valor_1ano"] >= df_prognostico["limite"]
    )

    df_prognostico = df_prognostico.merge(
        truques_dim,
        left_on="vagao",
        right_on="concatenatedcarid",
        how="left"
    ).drop(columns=["concatenatedcarid"])

    return df_prognostico, df_ignorados

#--------------------------------------------------------------------------------
## Carregamento de Dados 
#--------------------------------------------------------------------------------

# =============================
# Carregar Parquet
# =============================
# Caminho da pasta onde estão os parquet
CAMINHO = r"./temp"   # ajuste se necessário

@st.cache_data
def carregar_parquets(caminho):

    arquivos_parquet = glob.glob(os.path.join(caminho, "*.parquet"))
    dfs = {}

    for arquivo in arquivos_parquet:
        nome = os.path.basename(arquivo).replace(".parquet", "")
        dfs[nome] = pd.read_parquet(arquivo)
    return dfs


# # Lista todos os arquivos .parquet da pasta
# arquivos_parquet = glob.glob(os.path.join(CAMINHO, "*.parquet"))

# dfs = {}  # dicionário para armazenar cada dataframe

# for arquivo in arquivos_parquet:
#     nome = os.path.basename(arquivo).replace(".parquet", "")
#     dfs[nome] = pd.read_parquet(arquivo)
#     print(f"Carregado: {nome}  →  {dfs[nome].shape}")

# # DataFrames individuais
# df_164 = dfs["df_164"]
# df_trkv = dfs["df_trkv"]
# df_WCM = dfs["df_WCM"]
# df_z369 = dfs["df_z369"]
# df_z851 = dfs["df_z851"]
# df_z1568 = dfs["df_z1568"]
# df_tbogi = dfs["df_tbogi"]

@st.cache_data
def carregar_bases_externas():

    df_avarias = pd.read_excel(
        "Base_avarias.xlsx",
        engine="openpyxl"
    )

    truques_dim = pd.read_excel(
        "base_truques.xlsx",
        engine="openpyxl"
    )
    return df_avarias, truques_dim
# # SHAREPOINT | Enriquecimento – Sistema da Falha
# df_avarias = pd.read_excel(
#     r'Base_avarias.xlsx',
#     engine='openpyxl'
# )

# # SHAREPOINT | Base de truques
# truques_dim = pd.read_excel(
#     r'base_truques.xlsx',
#     engine='openpyxl'
# )

# 🔽 CHAMADA DAS FUNÇÕES
dfs = carregar_parquets(CAMINHO)
df_avarias, truques_dim = carregar_bases_externas()


# 🔽 DataFrames individuais (fora do cache)
df_164 = dfs.get("df_164")
df_trkv = dfs.get("df_trkv")
df_WCM = dfs.get("df_WCM")
df_z369 = dfs.get("df_z369")
df_z851 = dfs.get("df_z851")
df_z1568 = dfs.get("df_z1568")
df_tbogi = dfs.get("df_tbogi")

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


# Tratamento dos dados
df_z851 = padronizar_colunas(df_z851)
df_164 = padronizar_colunas(df_164)
df_trkv = padronizar_colunas(df_trkv)
df_WCM = padronizar_colunas(df_WCM)
df_z369 = padronizar_colunas(df_z369)
df_z1568 = padronizar_colunas(df_z1568)
df_tbogi = padronizar_colunas(df_tbogi)
truques_dim = padronizar_colunas(truques_dim)
df_avarias = padronizar_colunas(df_avarias)

#--------------------------------------------------------------------------------
## Filtro Global – MODELO
#--------------------------------------------------------------------------------
modelos_validos = [
    'GRANELEIROS',
    'TANQUES',
    'FECHADOS',
    'PLATAFORMAS',
    'GÔNDOLAS BAUXITA'
]

df_z369['ativo'] = df_z369['ativo'].astype(str).str.zfill(10)

modelos = modelos_validos

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
    .loc[df_z851['modelo'].isin(modelo_sel), 'equnr']
    .unique()
)

st.markdown(f"Quantidade de vagões válidos: {len(vagoes_validos)}")

df_trkv_f = df_trkv[df_trkv['concatenatedcarid'].isin(vagoes_validos)].copy()
# Tratamento z369
df_z369['ativo'] = df_z369['ativo'].astype(str).str.zfill(10)
df_z369_f = df_z369[df_z369['ativo'].isin(vagoes_validos)].copy()
df_z369_f['dt_abertura_trated'] = pd.to_datetime(df_z369_f['dt_abertura_trated'])
df_z369_f = df_z369_f[df_z369_f['dt_abertura_trated'].dt.year <= 2100]
# Tratamento z851
df_z851 = df_z851[df_z851['equnr'].isin(vagoes_validos)].copy()
colunas_data = ['data_de_fabricacao', 'data_fim', 'data_garantia', 'ultima_rg',
       'ultima_rr', 'ultima_ri', 'atualizacao', 'data_de_fabricacao_trated', 'data_fim_trated', 'data_garantia_trated',
       'dt_last_udate_trated', 'dt_sincronizacao']
df_z851[colunas_data] = df_z851[colunas_data].apply(
    lambda x: pd.to_datetime(x, errors='coerce')
)
df_z851['equnr'] = df_z851['equnr'].astype(str)
# Tratamento WCM
df_WCM['equnr'] = df_WCM['json_identificacao_do_veiculo'].apply(padronizar_identificacao)
df_WCM_f = df_WCM[df_WCM['equnr'].isin(vagoes_validos)].copy()

df_avarias['sistema'] = (
    df_avarias['combinado2']
    .fillna('')
    .str.split('|', n=1)
    .str[0]
    .replace('', np.nan)
)

df_z369_f = (
    df_z369_f
    .merge(
        df_avarias[['codfalha', 'sistema']].drop_duplicates(),
        how='left',
        left_on='cod_falha',
        right_on='codfalha'
    )
    .drop(columns='codfalha')
)

df_z369_f['sistema'] = df_z369_f['sistema'].map({
    'FR': 'FREIO',
    'SE': 'SUPERESTRUTURA',
    'CCT': 'CCT',
    'RD': 'RODEIRO',
    'TR': 'TRUQUE'
})

# KPIs + Top 5 Defeitos 
qtd_vgs = df_z851['equnr'].nunique()

def contar(texto):
    return df_z369_f[
        (df_z369_f['status'] == 'MSPN') &
        (df_z369_f['texto'].str.contains(texto, case=False, na=False))
    ]['ativo'].nunique()

kpis = [
    ("Truck view", contar("TRKV"), "Ocorrências", SUCCESS),
    ("T-BOGI", contar("T-BOGI"), "Ocorrências", WARNING),
    ("TADS", contar("ACÚSTICO"), "Ocorrências", DANGER),
    ("WCM", contar("WCM"), "Ocorrências", SUCCESS),
]

top5 = (
    df_z369_f[
        (df_z369_f["status"] == "MSPN") &
        (df_z369_f["tp_nota"].isin(["M1", "M2"]))
    ]["texto"]
    .value_counts()
    .head(5)
    .reset_index(name="quantidade")
)

st.divider()
# =============================================================================================
# TOP 5 DEFEITOS
# =============================================================================================
st.markdown("<div class='section-title'>Top 5 defeitos mais recorrentes</div>", unsafe_allow_html=True)
# st.subheader("Top 5 defeitos mais recorrentes")

col_l, col_r = st.columns([7, 3])

with col_l:
    fig_top5 = px.bar(
        top5,
        x="quantidade",
        y="texto",
        orientation="h",
        text="quantidade",
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

    st.plotly_chart(fig_top5, width='stretch')
    
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

# =============================================================================================
# HISTOGRAMA DE CUNHAS
# =============================================================================================

df_trkv_f, truques_dim = preparar_dados_trkv(
    df_trkv_f,
    df_z851,
    truques_dim,
    cof_outlier=0.2
)

# # 1. Filtro de direção do trem 
# df_trkv_f = df_trkv_f[
#     df_trkv_f['header_traindirection'] == "S"
# ]

# # 2. Merge com tipo de truque e filtro
# truques_dim = (
#     truques_dim
#     .rename(columns={
#         'vg_+_serie': 'concatenatedcarid',
#         'truque': 'truque'
#     })[['concatenatedcarid', 'truque']]
# )
# df_trkv_f = df_trkv_f.merge(truques_dim, on="concatenatedcarid", how="left")
# df_trkv_f = df_trkv_f[
#     df_trkv_f["truque"].isin(["Ride Control", "Ride Master"])
# ]

# # 3. Remover valores fisicamente inválidos por sensor
# sensores = [
#     "a#l_1","a#l_2","a#r_1","a#r_2",
#     "b#l_1","b#l_2","b#r_1","b#r_2"
# ]

# # Ride Control
# mask_rc = df_trkv_f["truque"] == "Ride Control"
# df_trkv_f.loc[mask_rc, sensores] = df_trkv_f.loc[mask_rc, sensores].mask(
#     (df_trkv_f.loc[mask_rc, sensores] < 15) |
#     (df_trkv_f.loc[mask_rc, sensores] > 52)
# )

# # Ride Master
# mask_rm = df_trkv_f["truque"] == "Ride Master"
# df_trkv_f.loc[mask_rm, sensores] = df_trkv_f.loc[mask_rm, sensores].mask(
#     (df_trkv_f.loc[mask_rm, sensores] < 30) |
#     (df_trkv_f.loc[mask_rm, sensores] > 70)
# )

# # 5. Aplicar tratamento de outlier
# cof_Outlier = 0.2
# df_trkv_f = tratar_outliers_trkv(df_trkv_f)

# # 6. Remover outliers
# df_trkv_f = df_trkv_f[
#     df_trkv_f['status_out'] == "OK"
# ]

# # Remove as linhas onde TODAS as colunas da lista 'sensores' são NaN
# df_trkv_f = df_trkv_f.dropna(subset=sensores, how='all')

# # 7. Limpeza inicial de colunas desnecessárias
# cols_drop = [
#     'carsequencenumber','carorientation','cartype',
#     'truckfields','truckids','truckvalues','timestr',
#     'header_trainsequencenumber','data_sincronizacao'
# ]
# df_trkv_f = df_trkv_f.drop(columns=cols_drop, errors='ignore')


# # 8. Mapeamento de alarme de cunha
# MAP_WEDGE = {
#     "Ride Control": 45,
#     "Barber": 57,
#     "Ride Master": 64,
#     "Motion Control": 57,
# }

# df_trkv_f['alarme'] = (
#     df_trkv_f['truque']
#     .map(MAP_WEDGE)
#     .fillna("inválido")
# )

# # 9. Ajustes finais
# df_trkv_f["concatenatedcarid"] = df_trkv_f["concatenatedcarid"].astype(str)
# df_trkv_f["timestamp"] = pd.to_datetime(df_trkv_f["timestamp"], errors="coerce")

# df_trkv_f["alarme"] = pd.to_numeric(
#     df_trkv_f["alarme"],
#     errors="coerce"
# ).astype("float64")


# # 10. Filtro de dados anteriores à ultima RG
# df_z851["concatenatedcarid"] = df_z851["equnr"]
# df_z851["ultima_rr"] = pd.to_datetime(df_z851["ultima_rr"], errors="coerce")
# df_dim = df_z851[["concatenatedcarid", "ultima_rr"]].drop_duplicates()
# df_trkv_f = df_trkv_f.merge(df_dim, on="concatenatedcarid", how="left")
# df_trkv_f = df_trkv_f[df_trkv_f["timestamp"] >= df_trkv_f["ultima_rr"]]

colunas_cunha = [
    "a#l_1","a#l_2","a#r_1","a#r_2",
    "b#l_1","b#l_2","b#r_1","b#r_2"
]

df = df_trkv_f.copy()
df["timestamp"] = pd.to_datetime(df["timestamp"])


# 1️⃣ Ordena e pega só 5 registros mais recentes por vagão
df = (
    df.sort_values(["concatenatedcarid", "timestamp"], ascending=[True, False])
      .groupby("concatenatedcarid")
      .head(5)
)

# 2️⃣ Converter cunhas para formato longo (muito mais rápido pra agrupar)
df_long = df.melt(
    id_vars=["concatenatedcarid", "truque", "timestamp"],
    value_vars=colunas_cunha,
    var_name="cunha",
    value_name="altura"
)

limites = {
    "Ride Master": 70,
    "Ride Control": 52
}

df_long = df_long[
    ~df_long.apply(
        lambda x: x["truque"] in limites and x["altura"] > limites[x["truque"]],
        axis=1
    )
]

# 3️⃣ Ignorar zeros
df_long["altura"] = df_long["altura"].replace(0, np.nan)
df_long = df_long.dropna(subset=["altura"])



# 4️⃣ Função vetorizada por vagão + cunha
def regra_altura(x):
    n = len(x)

    if n >= 5:
        vals = np.sort(x)[1:-1]
        return vals.mean()

    elif n == 4:
        vals = np.sort(x)[1:-1]
        return vals.mean()

    elif n == 3:
        return np.sort(x)[1]

    elif n == 2:
        return x.mean()

    elif n == 1:
        return x.iloc[0]

    return np.nan

alturas = (
    df_long.groupby(["concatenatedcarid", "cunha"])["altura"]
    .apply(regra_altura)
    .reset_index()
)


# 5️⃣ Pegar maior altura entre as cunhas de cada vagão
resultado = (
    alturas.groupby("concatenatedcarid")["altura"]
    .max()
    .reset_index(name="altura_cunha_max_media")
)


# 6️⃣ Recuperar tipo de truque
truque = (
    df.drop_duplicates("concatenatedcarid")
      [["concatenatedcarid", "truque"]]
)

resultado = resultado.merge(truque, on="concatenatedcarid", how="left")

dfs_por_truque = {
    truque: grupo.reset_index(drop=True)
    for truque, grupo in resultado.groupby('truque')
}

# Gerando um dataframe para cada tipo de truque
df_RC = dfs_por_truque['Ride Control']
df_RM = dfs_por_truque['Ride Master']

# Fazendo os bins de cada tipo de truque
bins_RM = [20, 30, 35, 40, 45, 50, 55, 57, 58, 59, 60, 61, 62, 63, 64, 100]
labels_RM = [f"{bins_RM[i]}-{bins_RM[i+1]}" for i in range(len(bins_RM)-1)]
df_RM["bin"] = pd.cut(
    df_RM["altura_cunha_max_media"],
    bins=bins_RM,
    labels=labels_RM,
    include_lowest=True
)
bins_RC = [15, 20, 25, 30, 35, 40, 41, 42, 43, 44, 45, 105]
labels_RC = [f"{bins_RC[i]}-{bins_RC[i+1]}" for i in range(len(bins_RC)-1)]
df_RC["bin"] = pd.cut(
    df_RC["altura_cunha_max_media"],
    bins=bins_RC,
    labels=labels_RC,
    include_lowest=True
)

def histograma_cunha_por_truque(
    df,
    bins,
    labels,
    bins_azul,
    bins_amarelo,
    bins_vermelho,
    coluna_valor="altura_cunha_max_media",
    titulo="Histograma de Cunha"
):

    # Criar coluna de bins
    df = df.copy()
    df["bin"] = pd.cut(
        df[coluna_valor],
        bins=bins,
        labels=labels,
        include_lowest=True
    )

    # Classificação de cores
    def classificar_cor(x):
        if x in bins_azul:
            return "Normal"
        elif x in bins_amarelo:
            return "Alerta"
        elif x in bins_vermelho:
            return "Crítico"
        return "Outros"

    df["faixa_cor"] = df["bin"].astype(str).apply(classificar_cor)

    # Gráfico
    fig = px.histogram(
        df,
        x="bin",
        text_auto=True,  # mostra a contagem em cada barra
        color="faixa_cor",
        category_orders={"bin": labels},
        color_discrete_map={
            "Normal": PRIMARY,
            "Alerta": WARNING,
            "Crítico": DANGER
        },
        labels={
            "bin": "Altura de cunha",
            "count": "Quantidade de vagões"
        },
        title=titulo
    )

    return fig

fig_RM = histograma_cunha_por_truque(
    df_RM,
    bins=bins_RM,
    labels=labels_RM,
    bins_azul=labels_RM[:7],
    bins_amarelo=labels_RM[7:14],
    bins_vermelho=[labels_RM[-1]],
    titulo="Histograma - Ride Master"
)

fig_RC = histograma_cunha_por_truque(
    df_RC,
    bins=bins_RC,
    labels=labels_RC,
    bins_azul=labels_RC[:5],
    bins_amarelo=labels_RC[5:10],
    bins_vermelho=[labels_RC[-1]],
    titulo="Histograma - Ride Control"
)

# Caixa de seleção
opcao = st.selectbox(
    "Tipo de truque:",
    [
        "Ride Master",
        "Ride Control"
    ]
)

if opcao == "Ride Master":
    col1, col2 = st.columns(2)
    with col1:
        fig_RM.update_layout(showlegend=False)
        st.plotly_chart(fig_RM, width='stretch')
    with col2:
        colunas = ["concatenatedcarid", "altura_cunha_max_media"]
        limite_RM = 64
        df_RM_f = df_RM[df_RM["altura_cunha_max_media"] > limite_RM][colunas]
        df_RM_f = df_RM_f.sort_values(by="altura_cunha_max_media", ascending=False)
        st.dataframe(
            df_RM_f,
            column_config={
                "concatenatedcarid": "Vagão",
                "altura_cunha_max_media": "Altura de cunha",
                },
            hide_index=True,
            )
elif opcao == "Ride Control":
    col1, col2 = st.columns(2)
    with col1:
        fig_RC.update_layout(showlegend=False)
        st.plotly_chart(fig_RC, width='stretch')
    with col2:
        colunas = ["concatenatedcarid", "altura_cunha_max_media"]
        limite_RC = 45
        df_RC_f = df_RC[df_RC["altura_cunha_max_media"] > limite_RC][colunas]
        df_RC_f = df_RC_f.sort_values(by="altura_cunha_max_media", ascending=False)
        st.dataframe(
            df_RC_f,
            column_config={
                "concatenatedcarid": "Vagão",
                "altura_cunha_max_media": "Altura de cunha",
                },
            hide_index=True,
            )
        
# ============================================================================================================================
# PREVISÃO DE DESGASTE
# ============================================================================================================================
        
# df_prognostico, df_ignorados = rodar_prognostico(
#     df_trkv_f,
#     truques_dim,
#     mae_max=1.5
# )

mae_max = 1.5

df_prognostico, df_ignorados = rodar_prognostico_paralelo(
    df_trkv_f,
    truques_dim,
    mae_max
)   
# Plot distribuiçao de taxas

df_plot = df_prognostico.dropna(subset=["taxa_desgaste"])

media = df_plot["taxa_desgaste"].mean()
mediana = df_plot["taxa_desgaste"].median()

fig_tx = px.histogram(
    df_plot,
    x="taxa_desgaste",
    nbins=30,
    title="Distribuição das taxas de desgaste (por dia)",
    color_discrete_sequence=["#0D3B66"]
)

fig_tx.update_traces(
    marker_line_color="white",
    marker_line_width=1
)
fig_tx.add_vline(x=media, line_dash="dash")
fig_tx.add_vline(x=mediana, line_dash="dot")




# Plot previsao de vencimento
fig_previsao, ax = plt.subplots(figsize=(10,6))

# (opcional) cores fixas por truque
cores = {
    "Ride Control": "#0D3B66",
    "Ride Master": "#7FE06C"
}

df_min = df_prognostico[df_prognostico["vai_estourar"] == True].copy()
df_min["data_cruzamento"] = pd.to_datetime(df_min["data_cruzamento"])
df_min = (
    df_min.sort_values("data_cruzamento")
          .drop_duplicates(subset="vagao", keep="first")
)
df_min["mes"] = df_min["data_cruzamento"].dt.strftime("%Y-%m")

resumo_prognostico = (
    df_min
    .groupby(["mes", "truque"])["vagao"]
    .nunique()
    .unstack(fill_value=0)
).sort_index()

df_plot = resumo_prognostico.reset_index().melt(
    id_vars="mes",
    var_name="truque",
    value_name="quantidade"
)

fig_previsao = px.bar(
    df_plot,
    x="mes",
    y="quantidade",
    color="truque",
    title=f"Vagões que atingirão o limite de cunha mês a mês - Erro máx.: {mae_max}",
    text="quantidade",  # já coloca os valores nas barras
    color_discrete_map={
        "Ride Control": "#0D3B66",
        "Ride Master": "#7FE06C"
    }
)

fig_previsao.update_layout(
    xaxis_title="Mês",
    yaxis_title="Quantidade de vagões",
    xaxis_tickangle=-45,
    barmode="stack",  # empilhado igual seu matplotlib
    template="plotly_white",
    legend_title="Truque"
)

fig_previsao.add_annotation(
    text=f"<b>Total de vagões avaliados:</b> {df_prognostico["vagao"].nunique()}<br><b> Total de vagões com vencimento nos próximos 12 meses:</b> {df_prognostico[df_prognostico["vai_estourar"]]["vagao"].nunique()}<br> <b>Total de vagões ignorados:</b> {df_ignorados["vagao"].nunique()}",    xref="paper",
    yref="paper",
    x=0.99,
    y=0.95,
    showarrow=False,
    align="right",
    bgcolor="white",
    bordercolor="black"
)

fig_previsao.update_traces(
    textposition="inside"
)
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig_tx, use_container_width=True) # Gráfico da distribuição de taxas na frota
with col2:
    st.plotly_chart(fig_previsao, use_container_width=True) # Gráfico de quantidade de truques vencidos mês a mês

# ============================================================================================================================
# DISTRIBUIÇÃO DE TRUQUES
# ============================================================================================================================
col1, col2 = st.columns([1, 3])

with col1:
    fig = grafico_rosca_truques(df_z851, truques_dim)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================================================================
# GRAFICO WCM 
# ============================================================================================================================
# Jogar fora dados de locomotivas
df_WCM_f = df_WCM_f[
    ~df_WCM_f['json_tipo_do_veiculo']
    .astype(str)
    .str.upper()
    .str.startswith('L')
]

df_WCM_f = df_WCM_f[
    ~df_WCM_f['json_trem_l_dir']
    .astype(str)
    .str.upper()
    .str.startswith('IMPORT')
]

# Jogar fora dados anteriores à ultima RG
df_WCM_f = df_WCM_f.merge(df_z851[['equnr','ultima_rr']], on="equnr", how="left")
df_WCM_f = df_WCM_f[df_WCM_f["json_trem_traintime_dt"] >= df_WCM_f["ultima_rr"]]

def calcular_media_maximas_passagens(
    df,
    col_vagao='equnr',
    col_data='json_trem_traintime_dt',
    col_impacto='json_forca_de_pico_de_impacto_da_roda_(kn)',
    n_passagens=2
):
    """
    Calcula, para cada vagão:
    - O maior impacto por passagem
    - Seleciona as N últimas passagens
    - Retorna a média dos maiores impactos dessas passagens
    """

    df = df.copy()

    # Garantir datetime
    df[col_data] = pd.to_datetime(df[col_data], errors='coerce')

    # Remover linhas inválidas
    df = df.dropna(subset=[col_vagao, col_data, col_impacto])

    # 1️⃣ Maior impacto por vagão por passagem
    df_max_por_passagem = (
        df
        .groupby([col_vagao, col_data])[col_impacto]
        .max()
        .reset_index()
    )

    # 2️⃣ Ordenar por data (mais recente primeiro)
    df_max_por_passagem = df_max_por_passagem.sort_values(
        [col_vagao, col_data],
        ascending=[True, False]
    )

    # 3️⃣ Selecionar últimas N passagens
    df_ultimas = (
        df_max_por_passagem
        .groupby(col_vagao)
        .head(n_passagens)
    )

    # 4️⃣ Média dos máximos
    df_resultado = (
        df_ultimas
        .groupby(col_vagao)[col_impacto]
        .mean()
        .reset_index(name='media_max_ultimas_passagens')
    )

    return df_resultado

df_WCM_result = calcular_media_maximas_passagens(df_WCM_f)

def plot_distribuicao_impacto(df_WCM_result, passo_faixa=10):
    # =========================
    # PREPARAÇÃO
    # =========================
    df_plot = df_WCM_result.dropna(subset=['media_max_ultimas_passagens']).copy()

    valor_max = df_plot['media_max_ultimas_passagens'].max()
    bins = np.arange(40, valor_max + passo_faixa, passo_faixa)

    df_plot['faixa_impacto'] = pd.cut(
        df_plot['media_max_ultimas_passagens'],
        bins=bins
    )

    # =========================
    # AGREGAÇÃO
    # =========================
    contagem = (
        df_plot.groupby('faixa_impacto')['equnr']
        .nunique()
        .reset_index()
    )

    contagem.columns = ['faixa_impacto', 'quantidade']

    # =========================
    # CLASSIFICAÇÃO
    # =========================
    def classificar_faixa(faixa):
        valor = faixa.left
        
        if valor <= 210:
            return 'Normal'
        elif 210 < valor <= 224:
            return 'Impacto baixo'
        elif 225 <= valor <= 299:
            return 'Impacto médio'
        elif 300 <= valor <= 399:
            return 'Impacto alto'
        else:
            return 'Impacto severo'

    contagem['status'] = contagem['faixa_impacto'].apply(classificar_faixa)

    contagem['faixa_str'] = contagem['faixa_impacto'].astype(str)

    # =========================
    # GRÁFICO
    # =========================
    fig = px.bar(
        contagem,
        x='faixa_str',
        y='quantidade',
        color='status',
        text='quantidade',
        color_discrete_map={
            'Normal': PRIMARY,
            'Impacto baixo': SUCCESS,
            'Impacto médio': WARNING,
            'Impacto alto': DANGER,
            'Impacto severo': TEXT
        },
        labels={
            'faixa_str': 'Faixa de Impacto (kN)',
            'quantidade': 'Quantidade de Vagões'
        },
        title='Distribuição de Impacto – Faixas Técnicas'
    )

    fig.update_traces(textposition='outside')

    fig.update_layout(
        xaxis_tickangle=-45,
        template='plotly_white'
    )
    st.plotly_chart(fig, use_container_width=True)

    return contagem

with col2:
    contagem = plot_distribuicao_impacto(df_WCM_result)

qtd_wcm = (
    df_z369_f[df_z369_f["texto"].str.contains("WCM", na=False)]["ativo"]
    .nunique()
)


col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    st.markdown(f"""
            <div style="
                background-color:{CARD_BG};
                border:1px solid {BORDER};
                border-radius:10px;
                padding:14px;
                text-align:center;
            ">
                <div style="color:{MUTED}; font-size:14px;"><b>Notas abertas WCM</b></div>
                <div style="color:{TEXT}; font-size:28px; font-weight:700;">{qtd_wcm}</div>
            </div>
            """, unsafe_allow_html=True)