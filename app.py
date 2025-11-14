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

# Função para conectar e buscar dados


# @st.cache_data(ttl=600)
# def function_to_get_data(MONGO_URI, DB_NAME, COLLECTION_NAME, lines=5):
#     client = MongoClient(MONGO_URI)
#     db = client[DB_NAME]
#     collection = db[COLLECTION_NAME]
#     # Buscar últimos 5 documentos ordenados por timestamp decrescente
#     docs = list(collection.find().sort("timestamp", -1).limit(lines))

#     if docs:
#         # Converter lista de documentos para DataFrame, removendo coluna _id
#         df = pd.DataFrame(docs).drop(columns=['_id'], errors='ignore')
#         if 'json_documents' in df.columns:
#             df['json_documents'] = df['json_documents'].fillna('').astype(str)
#         return df
#     else:
#         return pd.DataFrame()  # DataFrame vazio


logo = Image.open("assets/logo.png")
st.logo(logo, size='large')

st.image("assets/vg666.png", width=100)
st.title("RailCenter - Inteligência de Dados")

# Cria abas na parte superior
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs(
    ["Verify", "Consulta Master", "Saúde de Frota", "Chat Bot", "Sobre", "Testes de componentes"])

with aba1:
    st.header("Consulta de verificação")
    if st.button("Verificar Bases"):
        import pandas as pd
        from pymongo import MongoClient

        client = MongoClient(MONGO_URI)

        collection = client[DB_NAME]['base_last_update']

        # Buscar todos os documentos
        cursor = collection.find({})

        # Transformar em lista e depois em DataFrame
        df = pd.DataFrame(list(cursor))

        # Remover o _id se não quiser no DataFrame
        df = df.drop(columns=["_id"], errors="ignore")

        st.dataframe(df)


# ======= Aba 2 - Consulta master =======
with aba2:
    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd
    from datetime import datetime
    import re
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time

    st.header("Consulta Completa Vagões v0")
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
                    text="Tipo_Evento",
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
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import mean_squared_error, mean_absolute_error
        from sklearn.metrics import root_mean_squared_error
        import pandas as pd
        import plotly.graph_objects as go

        # =========================
        # 1. Garantir que Data é datetime
        # =========================
        df_trkv_trated["Data"] = pd.to_datetime(
            df_trkv_trated["Data"], errors="coerce")

        # Remover linhas sem Data ou sem valores
        df_trkv_trated = df_trkv_trated.dropna(
            subset=["Data", "TRKV_MAX_Cunha"])

        # Ordenar por data (importante!)
        df_trkv_trated = df_trkv_trated.sort_values("Data")

        # =========================
        # 2. Regressão Linear
        # =========================
        X = df_trkv_trated["Data"].map(
            pd.Timestamp.toordinal).values.reshape(-1, 1)
        y = df_trkv_trated["TRKV_MAX_Cunha"].values

        model = LinearRegression()
        model.fit(X, y)

        slope = model.coef_[0]
        intercept = model.intercept_
        # Predição
        y_pred = model.predict(X)
        # ====== MÉTRICAS ======
        r2 = model.score(X, y)
        rmse = root_mean_squared_error(y, y_pred)
        mae = mean_absolute_error(y, y_pred)

        print(f"R²:   {r2:.4f}")
        print(f"MAE:  {mae:.4f}")
        print(f"RMSE: {rmse:.4f}")

        print(f"Coeficiente angular (slope): {slope:.4f}")
# -------------------------------------------------------------------Regressão
        # df_trkv_trated, r2, mae, rmse = regrecao()

        def plot_Waysides():
            # =========================
            # 3. Gráfico TRKV + Regressão
            # =========================
            fig_trkv = go.Figure()

            # --- SÉRIE REAL ---
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

            # --- LINHA DE REGRESSÃO ---
            fig_trkv.add_trace(go.Scatter(
                x=df_trkv_trated["Data"],
                y=y_pred,
                mode="lines",
                line=dict(width=2, dash="dash", color="#A52BE3"),
                name=f"Regressão Linear (slope={slope:.4f})"
            ))

            fig_trkv.update_layout(
                title="TRKV - com Regressão Linear",
                xaxis_title="Data",
                yaxis_title="Valor",
                template="plotly_white",
                height=380
            )

            # Ajuste do range do eixo Y
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


with aba3:

    st.sidebar.markdown("### Portal de BI")

    # # st.header("Ficha Vagão")
    # st.title("Ficha Vagão - Prognósticos Integrado de Vagões")
    # st.write("Testes de desenvolvimento de BI para Vagões")
    # df_Z369 = function_to_get_data_from_z369(MONGO_URI, DB_NAME, "z369_full")
    # df_Z369_1 = function_to_get_data_from_z369(MONGO_URI, DB_NAME, "z369_full")
    # # teste = df_Z369['data_sincronizacao'].drop_duplicates()
    # # st.write(teste)
    # # contagem_mensal = df_Z369['data_sincronizacao'].dt.to_period('M').value_counts().sort_index()
    # df_Z369_1['mes'] = df_Z369_1['data_sincronizacao'].dt.to_period('M')
    # # st.write(df_Z369_1.groupby('DESC STATUS').size())
    # # st.write(df_Z369_1.groupby('mes').size())

    # contagens = (pd.crosstab(df_Z369_1['mes'], df_Z369_1['DESC STATUS'])   # linhas=mes, colunas=status
    #              .reindex(columns=['Mensagem encerrada', 'Mensagem pendente', 'Mensagem em processamento'], fill_value=0)
    #              .sort_index())
    # # st.write(contagens)
    # # 3st.dataframe(df_Z369_1)
    # # qtd_por_mes =

    # cont1 = df_Z369['DESC STATUS'].value_counts()
    # col5, col6, col7 = st.columns(3)
    # with col5:
    #     col5 = st.metric(label='Total de Notas fechadas',
    #                      value=cont1['Mensagem encerrada'], delta='10%')
    # with col6:
    #     col6 = st.metric(label='Total de Notas pendentes',
    #                      value=cont1['Mensagem pendente'], delta='30%')
    # with col7:
    #     col7 = st.metric(label='Total de Notas em processamento',
    #                      value=cont1['Mensagem em processamento'], delta='-25%')

    # st.date_input(label='Data de Atualização', value='today', disabled=True)

    # vagao_input = st.text_input('Escreva um vagão')
    # filtro_vagao = df_Z369['ATIVO'] == vagao_input
    # st.dataframe(df_Z369[filtro_vagao])

    # col1, col2, col3 = st.columns(3)
    # with col1:
    #     col1 = st.selectbox('Selecione um Local', sorted(
    #         df_Z369['Local'].drop_duplicates()))
    #     filtro1 = df_Z369["Local"] == col1
    #     df_Z369 = df_Z369[filtro1]
    # with col2:
    #     col2 = st.selectbox('Selecione um Estado',
    #                         df_Z369['DESC STATUS'].drop_duplicates())
    #     filtro2 = df_Z369["DESC STATUS"] == col2
    #     df_Z369 = df_Z369[filtro2]
    # with col3:
    #     col3 = st.selectbox('Selecione uma Nota', sorted(
    #         df_Z369['TP NOTA'].drop_duplicates()))
    #     filtro3 = df_Z369["TP NOTA"] == col3
    #     df_Z369 = df_Z369[filtro3]

    # df1 = df_Z369[filtro3]

    # st.dataframe(df1)


with aba4:  # Chat Bot
    import streamlit as st
    import requests
    import pandas as pd
    import io
    import json
    import re
    from datetime import datetime

    WEBHOOK_URL = "http://35.185.213.101/webhook/chatbot"

    # -----------------------------
    # 1) Envio ao Webhook
    # -----------------------------
    def send_message_to_webhook(message: str) -> str:
        payload = {"message": message}
        try:
            response = requests.post(WEBHOOK_URL, json=payload, timeout=200)
            if response.status_code == 200:
                return response.text
            else:
                return f"Erro: resposta do servidor {response.status_code}"
        except requests.exceptions.Timeout:
            return "⏱️ Tempo limite excedido: o servidor demorou mais de 90 segundos para responder."
        except Exception as e:
            return f"Erro ao conectar: {str(e)}"

    # -----------------------------
    # 2) Utilidades para parsing
    # -----------------------------
    def _extract_json_block(text: str):
        """
        Procura por blocos ```json ... ``` ou ``` ... ``` e retorna o conteúdo.
        """
        m = re.search(r"```json\s*(.*?)```", text,
                      flags=re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()
        m = re.search(r"```\s*(\{.*?\}|\[.*?\])\s*```", text, flags=re.DOTALL)
        if m:
            return m.group(1).strip()
        return None

    def _safe_json_loads(text: str):
        """
        Extrai e carrega JSON de forma segura.
        Suporta JSON puro, blocos ```json```, ou trechos {…}/[…].
        """
        # 1. Tenta carregar o texto diretamente
        try:
            return json.loads(text)
        except Exception:
            pass

        # 2. Extrai bloco ```json ... ```
        match = re.search(r"```json\s*(.*?)```", text,
                          flags=re.DOTALL | re.IGNORECASE)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except Exception:
                pass

        # 3. Extrai primeiro trecho {...} ou [...]
        match = re.search(r"(\{.*\}|\[.*\])", text, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

        return None

    def json_to_dataframe(obj):
        """
        Converte o objeto JSON (lista ou dicionário) em DataFrame.
        """
        if obj is None:
            return None

        if isinstance(obj, list):
            if len(obj) == 0 or isinstance(obj[0], dict):
                return pd.DataFrame(obj)

        if isinstance(obj, dict):
            # procura por chaves comuns
            for key in ['data', 'items', 'result', 'rows']:
                if key in obj and isinstance(obj[key], list):
                    if len(obj[key]) == 0 or isinstance(obj[key][0], dict):
                        return pd.DataFrame(obj[key])
            # se for um dict plano
            return pd.DataFrame([obj])

        return None

    def _format_date_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Converte colunas com 'dt' ou 'data' para formato dd/mm/yyyy."""
        out = df.copy()
        for col in out.columns:
            if any(k in col.lower() for k in ['dt', 'data']):
                try:
                    series = pd.to_datetime(
                        out[col], errors='coerce', utc=True)
                    out[col] = series.dt.tz_localize(
                        None).dt.strftime('%d/%m/%Y').fillna(out[col])
                except Exception:
                    pass
        return out

    def _remove_json_from_text(text: str) -> str:
        """Remove blocos JSON para exibir apenas o texto."""
        no_code = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        no_json = re.sub(r"\[[\s\S]*\]|\{[\s\S]*\}", "", no_code).strip()
        no_json = re.sub(r"\n{3,}", "\n\n", no_json)
        return no_json

    # --------------------------
    # INTERFACE STREAMLIT
    # --------------------------
    st.subheader("🤖 VAGO - ChatBot Vagões")

    user_msg = st.chat_input("Digite sua mensagem e pressione Enter")

    if user_msg:
        with st.chat_message("user"):
            st.write(user_msg)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            with st.spinner("⏳ Aguardando resposta do servidor..."):
                response_text = send_message_to_webhook(user_msg)

            placeholder.success("✅ Dados carregados com sucesso!")

        # Extrai JSON
        json_obj = _safe_json_loads(response_text)
        df = json_to_dataframe(json_obj)
        texto_sem_json = _remove_json_from_text(response_text)

        with st.chat_message("assistant"):
            if isinstance(df, pd.DataFrame) and not df.empty:
                if texto_sem_json:
                    st.markdown(texto_sem_json)

                df = _format_date_columns(df)
                st.dataframe(df, use_container_width=True)
            else:
                st.markdown(
                    texto_sem_json if texto_sem_json else response_text)


with aba5:

    import plotly.express as px
    import pandas as pd
    import streamlit as st

    df = pd.DataFrame({
        "NOTA": ["NOTA-123", "NOTA-124"],
        "Inicio": ["2024-01-01", "2024-01-01"],
        "Fim": ["2024-02-01", None],
        "Tipo": ["M1", "M2"]
    })

    # Converte datas
    df["Inicio"] = pd.to_datetime(df["Inicio"])
    df["Fim"] = pd.to_datetime(df["Fim"])

    # Cria Fim_Aux: se Fim for nulo -> usa data atual
    df["Fim_Aux"] = df["Fim"].fillna(pd.Timestamp.now())

    # Timeline usando Fim_Aux para x_end
    fig = px.timeline(
        df,
        x_start="Inicio",
        x_end="Fim_Aux",
        y="NOTA",
        color="Tipo",
        text="NOTA",
        hover_data={
            "Fim_Aux": False,   # não mostrar no hover
            "Fim": True,        # mostrar o Fim original
            "Inicio": True,
            "Tipo": True,
        }
    )

    fig.update_yaxes(autorange="reversed")

    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df)


with aba6:  # Teste de Componentes do STREAMLIT
    import datetime
    st.header("Teste de Componentes do STREAMLIT")
    st.title("Teste Title")
    st.write("Teste Write")
    st.write("""#Teste Write""")

    date = st.date_input("When's your birthday", value="today")
    st.write("Your birthday is:", date)
