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

# Configurações MongoDB
MONGO_URI = "mongodb+srv://int_dados:e7bUe2bXbKDu3Xzr@rumo-dev2.hbdcrld.mongodb.net/?authSource=admin"
DB_NAME = "supervisorio"

st.set_page_config(layout="wide")
logo = Image.open("assets/logo.png")
st.logo(logo, size='large')
st.image("assets/vg666.png", width=100)
st.title("RailCenter - Inteligência de Dados")
st.header("Consulta Completa Vagões v0 - Visão Micro")
# st.write("POC Testes")

# functions Begin --------------------------------------------------
# main def
def busca_dados(vagao):
    def busca_z1568(vagao):
        # Conexão com o MongoDB
        vagao = int(vagao)
        client = MongoClient(
            MONGO_URI)

        # Definição do filtro
        filter = {'ATIVO': re.compile(f"{vagao}")}

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
        filter = {'EQUNR': re.compile(f"{vagao}")}

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
                    'json_documents.json_Identificação do veículo': {
                        '$regex': vagao_str,
                        '$options': 'i'
                    }
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
                    'json_documents.json_Identificação do veículo': {
                        '$regex': vagao_str,
                        '$options': 'i'
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

        return df

    def busca_z369(vagao):
        # Conexão com o MongoDB
        client = MongoClient(
            MONGO_URI)

        vagao_str = str(vagao)

        # Definição do filtro
        filter = {"ATIVO_tratado": vagao_str}

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
        filter = {'CarIDNumber': vagao}

        # Consulta
        cursor = client[DB_NAME]['TRKV_treated'].find(filter)

        # Converter o cursor em lista e depois em DataFrame
        df = pd.DataFrame(list(cursor))

        # (Opcional) Remover a coluna _id, se não for necessária
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
            busca_z1568
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

    print(len(df_WCM))
    print(len(df_z369))
    print(len(df_trkv))
    print(len(df_z851))
    print(len(df_z1568))
    st.success("Função executada com sucesso!")

    return df_WCM, df_z369, df_trkv, df_z851, df_z1568

def tratar_dfs(df_WCM, df_z369, df_trkv):

    def tratar_trkv(df_trkv):
        # Converter datas (aceita ISO e dd/mm/yyyy)
        df_trkv['timestr'] = pd.to_datetime(
            df_trkv['timestr'], format='mixed', dayfirst=True, errors='coerce'
        )
        df_trkv['Data'] = df_trkv['timestr'].dt.date

        # Colunas de impacto
        colunas_impacto = ['A#L_1', 'A#L_2', 'A#R_1',
                            'A#R_2', 'B#L_1', 'B#L_2', 'B#R_1']

        # Substituir valores 0 por NaN
        df_trkv[colunas_impacto] = df_trkv[colunas_impacto].replace(
            0, np.nan)

        # Calcular o maior valor por linha
        df_trkv['Maior_Impacto_Linha'] = df_trkv[colunas_impacto].max(
            axis=1, skipna=True)

        # Agrupar por data
        df_trkv_max = (
            df_trkv.groupby('Data', as_index=False)['Maior_Impacto_Linha']
            .max()
            .rename(columns={'Maior_Impacto_Linha': 'Maior_Impacto_Diario'})
            .sort_values(by='Data', ascending=True)
        )

        # Formatar
        df_trkv_max['TRKV_MAX_Cunha'] = df_trkv_max['Maior_Impacto_Diario'].round(
            2)

        return df_trkv_max[['Data', 'TRKV_MAX_Cunha']]

    df_trkv_trated = tratar_trkv(df_trkv)

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
    df_wcm_trated = tratar_WCM(df_WCM)

    def tratar_z369(df_z369):

        # df_z369['timestr'] = pd.to_datetime(df_z369['timestr'])
        # df_z369['Data'] = df_z369['timestr'].dt.date

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

    df_timeline_z369, df_z369_trated = tratar_z369(df_z369)

    return df_trkv_trated, df_wcm_trated, df_timeline_z369, df_z369_trated

def inserir_wcm_hist(df_wcm_trated):
    df_wcm_trated_histgeral = df_wcm_trated.copy()
    print(df_wcm_trated)
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

# functions End ----------------------------------------------------
# Tela -----------------------
# Campo de entrada de texto
vg_entrada = st.text_input("Digite algo:")

# Botão que executa a função
if st.button("Executar função"):
    with st.spinner("🔄 Processando... Aguarde alguns segundos..."):

        vg_entrada = tratar_entrada(vg_entrada)
        minha_funcao(vg_entrada)

        df_WCM, df_z369, df_trkv, df_z851, df_z1568 = busca_dados(
            vg_entrada)

        df_trkv_trated, df_wcm_trated, df_timeline_z369, df_z369_trated = tratar_dfs(
            df_WCM, df_z369, df_trkv)

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

            # ===== Dados =====
            row = df_z851.iloc[0]

            campos = [
                'EQUNR',
                'BITOLA',
                'MALHA',
                'DATA_DE_FABRICACAO_trated',
                'DATA_FIM_trated',
                'DATA_GARANTIA_trated',
                'KM_RODADO_DESDE_ULTIMA_RG',
                'MODELO',
                'STATUS',
                'ULTIMA_RG',
                'ULTIMA_RI',
                'ULTIMA_RR'
            ]

            st.subheader("📌 Informações do Vagão")

            cards_por_linha = 3

            # ===== Renderização =====
            for i in range(0, len(campos), cards_por_linha):
                cols = st.columns(cards_por_linha)

                for idx, campo in enumerate(campos[i:i + cards_por_linha]):
                    valor = row[campo]

                    with cols[idx]:
                        st.markdown(
                            f"""
                            <div class="card">
                                <div class="card-title">{campo}</div>
                                <div class="card-value">{valor}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

            st.subheader("Linha do Tempo")

        resumo_z1568()
# -------------------------------------------------------------------RESUMO

        def plotar_gaph_resumo():
            import plotly.express as px
            import pandas as pd
            import streamlit as st

            df_wcm_timeline = inserir_wcm_hist(df_wcm_trated)

            df_trkv_timeline = inserir_trkv_hist(df_trkv_trated)

            df_z1568_timeline = inserir_z1568(
                df_z1568).reset_index(drop=True)

            print(df_z1568_timeline)

            df_final = pd.concat([df_z1568_timeline, df_timeline_z369, df_wcm_timeline,  df_trkv_timeline]
                                    )

            df_final["Texto_Label"] = df_final["Tipo_Evento"].apply(
                lambda x: "" if x in ["WCM", "trkv"] else x
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

            st.plotly_chart(fig, use_container_width=True)

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

    import numpy as np
    import pandas as pd
    from math import sqrt

    def projetar_regressao(df, slope, intercept, dias_a_frente=30):
        # Converte datas para inteiro ordinal
        x = pd.to_datetime(df["Data"], errors="coerce").map(
            pd.Timestamp.toordinal).values
        x = x[~np.isnan(x)]  # remove valores inválidos

        ultimo_x = x[-1]

        # Cria novos pontos no futuro
        novos_x = np.array(
            [ultimo_x + i for i in range(1, dias_a_frente + 1)])

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
        x_all = pd.to_datetime(df[col_x], errors="coerce").map(
            pd.Timestamp.toordinal).values
        y_all = df[col_y].values

        # Máscara para limpar NaN
        mask = ~np.isnan(x_all) & ~np.isnan(y_all)
        x = x_all[mask]
        y = y_all[mask]

        n = len(x)

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


# -------------------------------------------------------------------Regressão
    # df_trkv_trated, r2, mae, rmse = regrecao()


    def plot_Waysides():

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
            line=dict(width=2)
        ))

        # -------------------------
        # 2. Linha de regressão real
        # -------------------------
        fig_trkv.add_trace(go.Scatter(
            x=df_trkv_trated["Data"],
            y=y_pred,
            mode="lines",
            line=dict(width=2, dash="dash", color="#A52BE3"),
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

        # Layout
        fig_trkv.update_layout(
            title="TRKV - Regressão + Projeção Futura",
            xaxis_title="Data",
            yaxis_title="Valor",
            template="plotly_white",
            height=380,
        )

        # Range eixo Y
        fig_trkv.update_yaxes(range=[10, 70])

        # =========================
        # WCM
        # =========================

        df_wcm_trated["Alarme"] = 200

        fig_wcm = go.Figure()

        # Curva principal
        fig_wcm.add_trace(go.Scatter(
            x=df_wcm_trated["Data"],
            y=df_wcm_trated["Maior_Impacto_kN"],
            mode="lines+markers+text",
            text=df_wcm_trated["Maior_Impacto_kN"].round(1).astype(str),
            textposition="top center",
            name="Maior_Impacto_kN",
            marker=dict(size=7),
            line=dict(width=2)
        ))

        # Linha de limite
        fig_wcm.add_trace(go.Scatter(
            x=df_wcm_trated["Data"],
            y=df_wcm_trated["Alarme"],
            mode="lines",
            name="Alarme 200 kN",
            line=dict(color="red", width=2, dash="dash")
        ))

        fig_wcm.update_layout(
            title="wcm",
            xaxis_title="Data",
            yaxis_title="Valor",
            template="plotly_white",
            height=380
        )

        fig_wcm.update_yaxes(range=[0, 300])
        # =========================
        # STREAMLIT LAYOUT
        # =========================

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("TRKV Cunha Máximo Passagem (mm)")
            st.plotly_chart(fig_trkv, use_container_width=True)
            st.markdown(f"""
            **R²:** `{r2:.4f}`  
            **MAE:** `{mae:.4f}`  
            **RMSE:** `{rmse:.4f}`  
            """)
            st.dataframe(df_trkv_trated)

        with col2:

            st.subheader("WCM Maior Impacto (kN)")
            st.plotly_chart(fig_wcm, use_container_width=True)
            st.markdown(f"""
            **Alarme Baixo:** `-`   
            **Alarme Médio:** `-`   
            **Alarme Alto:** `-`  
            """)
            st.dataframe(df_wcm_trated)

            # Plota gráfico de linha
# graficos WCM e TRKV
    plot_Waysides()
    st.write("Dados z369")
    st.dataframe(df_z369)
    st.write("Dados WCM")
    st.dataframe(df_WCM)
    st.write("Dados TRKV")
    st.dataframe(df_trkv)
    st.write("Dados z851")
    st.dataframe(df_z851)
    st.write("Dados z1568")
    st.dataframe(df_z1568)

# Tela -----------------------
