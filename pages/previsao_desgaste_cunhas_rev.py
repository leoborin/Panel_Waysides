# # ======================
# #%% Importando bibliotecas e configurações
# =======================================
from pymongo import MongoClient
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import pyarrow
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import create_engine, text
import unicodedata
from sklearn.linear_model import LinearRegression
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import r2_score

# Configurações para exibição de dataframes
pd.set_option('display.max_columns', None)     # mostra todas as colunas
pd.set_option('display.max_colwidth', None)    # não corta conteúdo
pd.set_option('display.width', 0)              # ajusta largura automaticamente

# Paleta de Cores e CSS 
PRIMARY = "#0D3B66"
WARNING = "#F39C12"
DANGER = "#E74C3C"

# =======================================
#%% Importação de dados
# =======================================
# Caminho da base de truques
truques_dim = pd.read_excel(r"C:\Users\cs377198\inteligencia_dados\data\base_truques.xlsx")

# Ler parquets 
df_trkv = pd.read_parquet(
    r"C:\Users\cs377198\inteligencia_dados\data\df_trkv.parquet",
    engine="pyarrow"
)

df_z851 = pd.read_parquet(
    r"C:\Users\cs377198\inteligencia_dados\data\df_z851.parquet",
    engine="pyarrow"
)

# =======================================
#%% Funções
# =======================================
# Salvar gráficos e arquivos
# 📁 Diretórios (definidos uma vez só)
try:
    BASE_DIR = Path(__file__).resolve().parent.parent
except NameError:
    BASE_DIR = Path.cwd().parent  # 🔥 sobe um nível

REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
 
def salvar_parquet(dfs, incluir_timestamp=False):
    """
    Salva DataFrames em parquet.

    Parâmetros
    ----------
    dfs : dict ou DataFrame

    Exemplos:
    ----------
    salvar_parquet({
        "df_prognostico": df_prognostico,
        "df_min": df_min
    })

    salvar_parquet(
        df_prognostico,
        nome_arquivo="df_prognostico"
    )
    """

    timestamp = ""
    if incluir_timestamp:
        timestamp = "_" + datetime.now().strftime("%Y%m%d_%H%M")

    # ---------------------------------------------------
    # Caso 1 → vários dataframes
    # ---------------------------------------------------
    if isinstance(dfs, dict):

        for nome_arquivo, df in dfs.items():

            caminho = REPORTS_DIR / f"{nome_arquivo}{timestamp}.parquet"

            df.to_parquet(
                caminho,
                engine="pyarrow",
                index=False
            )

            print(f"Parquet salvo em: {caminho}")

    # ---------------------------------------------------
    # Caso 2 → dataframe único
    # ---------------------------------------------------
    else:
        raise ValueError(
            "Para salvar um único DataFrame, envie um dicionário: "
            '{"nome_arquivo": dataframe}'
        )

# Padroniza o nome das colunas
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

def tratar_outliers_trkv(df):

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

    # 📍 referência temporal = hoje
    x_base = df["timestamp"].min()

    data_hoje = pd.Timestamp.today()

    x_hoje = (
        (data_hoje - x_base)
        .total_seconds() / 86400
    )

    # valor atual = última medição válida
    y_atual = y_valid[-1]

    # 🔮 horizonte de 12 meses a partir de hoje
    horizonte_dias = 365

    x_futuro = np.linspace(
        x_hoje,
        x_hoje + horizonte_dias,
        100
    )

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


        data_cross = x_base + pd.to_timedelta(x_cross, unit="D")
    else:
        data_cross = None

    return {
        "valor_atual": y_atual,
        "valor_1ano": y_1ano,
        "limite": limite,
        "data_cruzamento": data_cross
    }
# =============================
#%% Filtros e tratamento de dados
# =============================
# Padronização das colunas
df_z851 = padronizar_colunas(df_z851)
df_trkv = padronizar_colunas(df_trkv)
truques_dim = padronizar_colunas(truques_dim)

# Filtrar modelos válidos
modelos_validos = [
    'GRANELEIROS',
    'TANQUES',
    'FECHADOS',
    'PLATAFORMAS',
    'GÔNDOLAS BAUXITA'
]

modelos = modelos_validos

vagoes_validos = (
    df_z851
    .loc[df_z851['modelo'].isin(modelos), 'equnr']
    .unique()
)

# Filtrar vagões válidos da base do Truck View
df_trkv_f = df_trkv[df_trkv['concatenatedcarid'].isin(vagoes_validos)].copy()
del df_trkv
# Filtrar vagões válidos da z851
df_z851 = df_z851[df_z851['equnr'].isin(vagoes_validos)].copy()

# Tratamento z851
colunas_data = ['data_de_fabricacao', 'data_fim', 'data_garantia', 'ultima_rg',
       'ultima_rr', 'ultima_ri', 'atualizacao', 'data_de_fabricacao_trated', 'data_fim_trated', 'data_garantia_trated',
       'dt_last_udate_trated', 'dt_sincronizacao']
df_z851[colunas_data] = df_z851[colunas_data].apply(
    lambda x: pd.to_datetime(x, errors='coerce')
)
del colunas_data
df_z851['equnr'] = df_z851['equnr'].astype(str)

# Tratamento Truck View
# 1. Filtro de direção do trem 
df_trkv_f = df_trkv_f[
    df_trkv_f['header_traindirection'] == "S"
]

# 2. Merge com tipo de truque e filtro
truques_dim = (
    truques_dim
    .rename(columns={
        'vg_+_serie': 'concatenatedcarid',
        'truque': 'truque'
    })[['concatenatedcarid', 'truque']]
)
df_trkv_f = df_trkv_f.merge(truques_dim, on="concatenatedcarid", how="left")
df_trkv_f = df_trkv_f[
    df_trkv_f["truque"].isin(["Ride Control", "Ride Master"])
]

# 3. Remover valores fisicamente inválidos por sensor
sensores = [
    "a#l_1","a#l_2","a#r_1","a#r_2",
    "b#l_1","b#l_2","b#r_1","b#r_2"
]

# Ride Control
mask_rc = df_trkv_f["truque"] == "Ride Control"
df_trkv_f.loc[mask_rc, sensores] = df_trkv_f.loc[mask_rc, sensores].mask(
    (df_trkv_f.loc[mask_rc, sensores] < 15) |
    (df_trkv_f.loc[mask_rc, sensores] > 52)
)

# Ride Master
mask_rm = df_trkv_f["truque"] == "Ride Master"
df_trkv_f.loc[mask_rm, sensores] = df_trkv_f.loc[mask_rm, sensores].mask(
    (df_trkv_f.loc[mask_rm, sensores] < 30) |
    (df_trkv_f.loc[mask_rm, sensores] > 70)
)

# 5. Aplicar tratamento de outlier
cof_Outlier = 0.2
df_trkv_f = tratar_outliers_trkv(df_trkv_f)

# 6. Remover outliers
df_trkv_f = df_trkv_f[
    df_trkv_f['status_out'] == "OK"
]

# Remove as linhas onde TODAS as colunas da lista 'sensores' são NaN
df_trkv_f = df_trkv_f.dropna(subset=sensores, how='all')

# 7. Limpeza inicial de colunas desnecessárias
cols_drop = [
    'carsequencenumber','carorientation','cartype',
    'truckfields','truckids','truckvalues','timestr',
    'header_trainsequencenumber','data_sincronizacao'
]
df_trkv_f = df_trkv_f.drop(columns=cols_drop, errors='ignore')


# 8. Mapeamento de alarme de cunha
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

# 9. Ajustes finais
df_trkv_f["concatenatedcarid"] = df_trkv_f["concatenatedcarid"].astype(str)
df_trkv_f["timestamp"] = pd.to_datetime(df_trkv_f["timestamp"], errors="coerce")

df_trkv_f["alarme"] = pd.to_numeric(
    df_trkv_f["alarme"],
    errors="coerce"
).astype("float64")

# 10. Filtro de dados anteriores à ultima RG
df_z851["concatenatedcarid"] = df_z851["equnr"]
df_z851["ultima_rr"] = pd.to_datetime(df_z851["ultima_rr"], errors="coerce")
df_dim = df_z851[["concatenatedcarid", "ultima_rr"]].drop_duplicates()
df_trkv_f = df_trkv_f.merge(df_dim, on="concatenatedcarid", how="left")
df_trkv_f = df_trkv_f[df_trkv_f["timestamp"] >= df_trkv_f["ultima_rr"]]

# ============================
#%% Modelagem
# ============================

resultados_prognostico = []
ignorados = []
mae_max = 1.5

colunas_cunha = [
    "a#l_1","a#l_2","a#r_1","a#r_2",
    "b#l_1","b#l_2","b#r_1","b#r_2"
]

for vagao, grupo in df_trkv_f.groupby("concatenatedcarid"):

    # 🔴 BLOQUEIO
    if not tem_dados_suficientes(grupo, colunas_cunha):
        #print(f"[VAGAO IGNORADO] {vagao} sem dados suficientes")
        ignorados.append({
            "vagao": vagao,
            "cunha": None,
            "motivo": "sem_dados_suficientes",
            "mae": None,
            "rmse": None, 
            "r2": None
        })
        continue

    for col in colunas_cunha:

        iso, model = treinar_pipeline(grupo, col, min_pontos=10)

        if model is None:
            ignorados.append({
                "vagao": vagao,
                "cunha": col,
                "motivo": "falha_treino",
                "mae": None,
                "rmse": None,
                "r2": None
            })
            continue

        # 🔹 AVALIAÇÃO DO MODELO
        avaliacao = avaliar_modelo(grupo, model, col)

        if avaliacao is None:
            ignorados.append({
                "vagao": vagao,
                "cunha": col,
                "motivo": "falha_avaliacao",
                "mae": None,
                "rmse": None,
                "r2": None
            })
            continue

        mae, rmse, r2 = avaliacao

        # 🔴 FILTRO DE QUALIDADE
        if mae > mae_max:
            #print(f"[IGNORADO] MAE alto ({mae:.2f}) - Vagão {vagao} - Cunha {col}")
            ignorados.append({
                "vagao": vagao,
                "cunha": col,
                "motivo": "mae_alto",
                "mae": mae,
                "rmse": rmse,
                "r2": r2
            })
            continue

        # 🔥 NOVO: EXTRAIR TAXA DE DESGASTE (coeficiente)
        taxa = None
        try:
            # caso simples (LinearRegression direto)
            if hasattr(model, "coef_"):
                taxa = model.coef_[0]

            # caso pipeline sklearn
            elif hasattr(model, "named_steps"):
                for step in model.named_steps.values():
                    if hasattr(step, "coef_"):
                        taxa = step.coef_[0]
                        break
        except:
            pass

        resultado = prever_1_ano_e_limite(grupo, model, col)

        if resultado is None:
            ignorados.append({
                "vagao": vagao,
                "cunha": col,
                "motivo": "falha_previsao",
                "mae": mae,
                "rmse": rmse,
                "r2": r2
            })
            continue

        resultados_prognostico.append({
            "vagao": vagao,
            "cunha": col,
            "valor_atual": resultado["valor_atual"],
            "valor_1ano": resultado["valor_1ano"],
            "limite": resultado["limite"],
            "data_cruzamento": resultado["data_cruzamento"],
            "rmse": rmse,   # 🔥 opcional (recomendo guardar)
            "mae": mae,
            "r2": r2,
            "taxa_desgaste": taxa
        })

df_prognostico = pd.DataFrame(resultados_prognostico)
df_ignorados = pd.DataFrame(ignorados)

df_prognostico["vai_estourar"] = (
    df_prognostico["valor_1ano"] >= df_prognostico["limite"]
)
df_prognostico = df_prognostico.sort_values("data_cruzamento")
df_prognostico = df_prognostico.merge(truques_dim, left_on="vagao", right_on="concatenatedcarid", how="left")
df_prognostico = df_prognostico.drop(columns=["concatenatedcarid"])
# df_prognostico.head()


# Gráfico de previsão de vencimento de vagões por mÊs
# Preparação dos dados
df_min = df_prognostico[df_prognostico["vai_estourar"] == True].copy()
df_min["data_cruzamento"] = pd.to_datetime(df_min["data_cruzamento"])

# pega o primeiro cruzamento por vagão
df_min = (
    df_min.sort_values("data_cruzamento")
          .drop_duplicates(subset="vagao", keep="first")
)

# cria coluna de mês
df_min["mes"] = df_min["data_cruzamento"].dt.strftime("%Y-%m")

# Agrupamento mês + truque
resumo_prognostico = (
    df_min
    .groupby(["mes", "truque"])["vagao"]
    .nunique()
    .unstack(fill_value=0)
)

# ordenar meses
resumo_prognostico = resumo_prognostico.sort_index()

# # Prints de controle
# print(f"Vagões com previsão: {df_prognostico['vagao'].nunique()}")
# print(f"Vagões que irão atingir o limite em até 1 ano: {df_min['vagao'].nunique()}")
# print(f"Vagões ignorados: {df_ignorados['vagao'].nunique()}")

# df_plot = resumo_prognostico.reset_index().melt(
#     id_vars="mes",
#     var_name="truque",
#     value_name="quantidade"
# )

# totais = df_plot.groupby("mes")["quantidade"].sum().reset_index()
# totais = totais.rename(columns={"quantidade": "total"})

# Vagões mais críticos (20% das piores taxas)
df_max = (
    df_prognostico
    .sort_values("taxa_desgaste", ascending=False)
    .drop_duplicates(subset="vagao", keep="first")
)

# Definir quantidade (20%)
perc = 0.20
n_top = int(np.ceil(len(df_max) * perc))

# Selecionar top 20%
top_criticos = df_max.head(n_top)

# Resultado
# print(f"Total de vagões: {df_max['vagao'].nunique()}")
# print(f"Top 20%: {len(top_criticos)} vagões")
top_criticos.sort_values("taxa_desgaste",ascending=False)

# Avaliando a cobertura da previsão na frota
# lista de todos os vagões envolvidos
vagoes = pd.Series(
    pd.concat([df_prognostico["vagao"], df_ignorados["vagao"]]).unique()
)

# cria grade completa vagao x cunha
base = pd.MultiIndex.from_product(
    [vagoes, colunas_cunha],
    names=["vagao", "cunha"]
).to_frame(index=False)

# marcar se foi previsto
df_prev = df_prognostico.copy()
df_prev["tem_previsao"] = 1

base = base.merge(
    df_prev[["vagao", "cunha", "tem_previsao"]],
    on=["vagao", "cunha"],
    how="left"
)

base["tem_previsao"] = base["tem_previsao"].fillna(0)

# contar por vagão
resumo_vagao = base.groupby("vagao")["tem_previsao"].sum() # isso vai de 0 a 8

distribuicao = resumo_vagao.value_counts().sort_index()

percentual = distribuicao / distribuicao.sum() * 100

df_resultado = pd.DataFrame({
    "qtd_cunhas_previstas": distribuicao.index,
    "qtd_vagoes": distribuicao.values,
    "percentual": percentual.values
}).sort_values("qtd_cunhas_previstas")


# Quantos vagões sem previsão nenhuma
qtd_sem_previsao = df_resultado.loc[
    df_resultado["qtd_cunhas_previstas"] == 0,
    "qtd_vagoes"
].sum()

# print(qtd_sem_previsao)

salvar_parquet(
    {
        "df_prognostico": df_prognostico,
        "df_min": df_min,
        "df_ignorados": df_ignorados,
        "df_piores_taxas": top_criticos
    },
    incluir_timestamp=False
    )