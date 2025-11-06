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


@st.cache_data(ttl=600)  # busca notas por vagão z369 TRKV WCM
@st.cache_data(ttl=600)
def function_to_get_data(MONGO_URI, DB_NAME, COLLECTION_NAME, lines=5):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    # Buscar últimos 5 documentos ordenados por timestamp decrescente
    docs = list(collection.find().sort("timestamp", -1).limit(lines))

    if docs:
        # Converter lista de documentos para DataFrame, removendo coluna _id
        df = pd.DataFrame(docs).drop(columns=['_id'], errors='ignore')
        if 'json_documents' in df.columns:
            df['json_documents'] = df['json_documents'].fillna('').astype(str)
        return df
    else:
        return pd.DataFrame()  # DataFrame vazio


@st.cache_data(ttl=600)
def function_to_get_data_from_z369(MONGO_URI, DB_NAME, COLLECTION_NAME, lines=10000):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    # Buscar últimos documentos ordenados por timestamp decrescente
    docs = collection.find().sort("dt_abertura_trated", -1).limit(lines)

    if docs:
        # Converter lista de documentos para DataFrame, removendo coluna _id
        df = pd.DataFrame(docs).drop(columns=['_id'], errors='ignore')
        if 'json_documents' in df.columns:
            df['json_documents'] = df['json_documents'].fillna('').astype(str)
        return df
    else:
        return pd.DataFrame()  # DataFrame vazio


@st.cache_data
def get_latest_documents():
    COLLECTION_NAME = "TRKV"
    df_trkv = function_to_get_data(
        MONGO_URI, DB_NAME, COLLECTION_NAME, lines=5)

    COLLECTION_NAME = "WCM"
    df_WCM = function_to_get_data(
        MONGO_URI, DB_NAME, COLLECTION_NAME, lines=5)

    COLLECTION_NAME = "z369_full"
    df_Z369 = function_to_get_data(
        MONGO_URI, DB_NAME, COLLECTION_NAME)

    return df_trkv, df_WCM, df_Z369


logo = Image.open("assets/logo.png")
st.logo(logo, size='large')

st.image("assets/vg666.png", width=100)
st.title("RailCenter - Inteligência de Dados")

# Cria abas na parte superior
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs(
    ["Verify", "Consulta Master", "Saúde de Frota", "Chat Bot", "Sobre", "Testes de componentes"])

with aba1:
    st.header("Consulta MongoDB")
    if st.button("Carregar últimos 5 documentos"):
        df_WCM, df_trkv = get_latest_documents()

        if df_WCM.empty:
            st.warning("Nenhum documento encontrado em WCM.")
        else:
            st.subheader("Tabela dos documentos carregados [WCM]")
            st.dataframe(df_WCM)

        if df_trkv.empty:
            st.warning("Nenhum documento encontrado em TRKV.")
        else:
            st.subheader("Tabela dos documentos carregados [TRKV]")
            st.dataframe(df_trkv)

# ======= Aba 2 - Consulta master =======
with aba2:
    import numpy as np
    import plotly.express as px
    import pandas as pd
    from datetime import datetime

    st.header("Consulta Completa Vagões v0")
    # st.write("POC Testes")

    # functions Begin --------------------------------------------------
    # main def
    def busca_dados(vagao):

        def busca_wcm(vagao):
            # Conexão com o MongoDB
            client = MongoClient(
                'mongodb+srv://int_dados:e7bUe2bXbKDu3Xzr@rumo-dev2.hbdcrld.mongodb.net/?authSource=admin')
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
            result = client['supervisorio']['WCM'].aggregate(pipeline)

            # Converte o resultado em DataFrame
            df = pd.DataFrame(list(result))

            # Se quiser expandir o dicionário 'json_documents' em colunas separadas:
            if not df.empty and 'json_documents' in df.columns:
                df = pd.json_normalize(df['json_documents'])

            return df

        def busca_z369(vagao):
            # Conexão com o MongoDB
            client = MongoClient(
                'mongodb+srv://int_dados:e7bUe2bXbKDu3Xzr@rumo-dev2.hbdcrld.mongodb.net/?authSource=admin')

            vagao_str = str(vagao)

            # Definição do filtro
            filter = {"ATIVO_tratado": vagao_str}

            # Consulta
            cursor = client['supervisorio']['z369_trated'].find(filter)

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
                'mongodb+srv://int_dados:e7bUe2bXbKDu3Xzr@rumo-dev2.hbdcrld.mongodb.net/?authSource=admin')

            # Definição do filtro
            filter = {'CarIDNumber': vagao}

            # Consulta
            cursor = client['supervisorio']['TRKV_treated'].find(filter)

            # Converter o cursor em lista e depois em DataFrame
            df = pd.DataFrame(list(cursor))

            # (Opcional) Remover a coluna _id, se não for necessária
            if '_id' in df.columns:
                df.drop('_id', axis=1, inplace=True)

            return df

        df_WCM = busca_wcm(vagao)
        df_z369 = busca_z369(vagao)
        df_trkv = busca_TRKV(vagao)

        print(len(df_WCM))
        print(len(df_z369))
        print(len(df_trkv))
        st.success("Função executada com sucesso!")

        return df_WCM, df_z369, df_trkv

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

            df_z369_Aberturas = df_z369_trated[[
                'dt_abertura_trated', 'TP NOTA', 'NOTA', 'Texto_Completo', 'STATUS']]
            df_z369_Aberturas["Evento"] = "Abertura"
            df_z369_Aberturas = df_z369_Aberturas.rename(columns={
                'dt_abertura_trated': 'Data',
            })

            df_z369_fechamentos = df_z369_trated[df_z369_trated['dt_fechamento_trated'].notnull(
            )]
            df_z369_fechamentos = df_z369_fechamentos[[
                'dt_fechamento_trated', 'TP NOTA', 'NOTA', 'Texto_Completo', 'STATUS']]
            df_z369_fechamentos = df_z369_fechamentos.rename(columns={
                'dt_fechamento_trated': 'Data',
            })
            df_z369_fechamentos["Evento"] = "Fechamento"

            # Concatenar os dois dataframes um embaixo do outro
            df_z369_total = pd.concat(
                [df_z369_Aberturas, df_z369_fechamentos], ignore_index=True)

            # Ordenar pela coluna "Data"
            df_z369_total = df_z369_total.sort_values(
                by='Data', ascending=True).reset_index(drop=True)
            df_z369_total["NOTA"] = "NOTA-" + df_z369_total["NOTA"].astype(str)

            return df_z369_total, df_z369_trated

        df_z369_total, df_z369_trated = tratar_z369(df_z369)

        return df_trkv_trated, df_wcm_trated, df_z369_total, df_z369_trated

    def inserir_wcm_hist(df_wcm_trated):
        df_wcm_trated_histgeral = df_wcm_trated.copy()
        # 1) Garantir datetime (com hora) na coluna Data
        df_wcm_trated_histgeral['Data'] = pd.to_datetime(
            df_wcm_trated_histgeral['Data'])
        df_wcm_trated_histgeral['TP NOTA'] = "Passagem wcm"
        df_wcm_trated_histgeral['NOTA'] = "wcm_" + \
            df_wcm_trated_histgeral['Data'].astype(str)
        df_wcm_trated_histgeral['Texto_Completo'] = "Maior_Impacto_kN = " + \
            df_wcm_trated_histgeral['Maior_Impacto_kN'].astype(str)

        df_wcm_trated_ab = df_wcm_trated_histgeral.copy()
        df_wcm_trated_ab['Evento'] = "Abertura"

        df_wcm_trated_fx = df_wcm_trated_histgeral.copy()
        df_wcm_trated_fx['Data'] = df_wcm_trated_fx['Data'] + \
            pd.to_timedelta(12, unit='h')
        df_wcm_trated_fx['Evento'] = "Fechamento"

        # Agora sim, cada um é independente
        df_wcm_total = pd.concat(
            [df_wcm_trated_ab, df_wcm_trated_fx], ignore_index=True)
        df_wcm_total = df_wcm_total[[
            'Data', 'TP NOTA', 'NOTA', 'Texto_Completo', 'Evento']]

        return df_wcm_total

    def inserir_trkv_hist(df_trkv_trated):
        df_trkv_trated_histgeral = df_trkv_trated.copy()
        df_trkv_trated_histgeral['Data'] = pd.to_datetime(
            df_trkv_trated_histgeral['Data'])
        df_trkv_trated_histgeral['TP NOTA'] = "Passagem trkv"
        df_trkv_trated_histgeral['NOTA'] = "trkv_" + \
            df_trkv_trated_histgeral['Data'].astype(str)
        df_trkv_trated_histgeral['Texto_Completo'] = "TRKV_MAX_Cunha = " + \
            df_trkv_trated_histgeral['TRKV_MAX_Cunha'].astype(str)

        df_trkv_trated_ab = df_trkv_trated_histgeral.copy()
        df_trkv_trated_ab['Evento'] = "Abertura"

        df_trkv_trated_fx = df_trkv_trated_histgeral.copy()
        df_trkv_trated_fx['Data'] = df_trkv_trated_fx['Data'] + \
            pd.to_timedelta(12, unit='h')
        df_trkv_trated_fx['Evento'] = "Fechamento"

        # Agora sim, cada um é independente
        df_trkv_total = pd.concat(
            [df_trkv_trated_ab, df_trkv_trated_fx], ignore_index=True)
        df_trkv_total = df_trkv_total[[
            'Data', 'TP NOTA', 'NOTA', 'Texto_Completo', 'Evento']]

        return df_trkv_total

    def minha_funcao(texto):
        st.write(f"Você digitou: {texto}")

    # functions End ----------------------------------------------------
    # Tela -----------------------
    # Campo de entrada de texto
    vg_entrada = st.text_input("Digite algo:")

    # Botão que executa a função
    if st.button("Executar função"):
        with st.spinner("🔄 Processando... Aguarde alguns segundos..."):
            minha_funcao(vg_entrada)
            df_WCM, df_z369, df_trkv = busca_dados(vg_entrada)

            df_trkv_trated, df_wcm_trated, df_z369_total, df_z369_trated = tratar_dfs(
                df_WCM, df_z369, df_trkv)

# linha do tempo begin
            import plotly.express as px
            from datetime import datetime
            import pandas as pd

            # ... (seu código anterior)
            wcm_hist = inserir_wcm_hist(df_wcm_trated)
            trkv_hist = inserir_trkv_hist(df_trkv_trated)

            # ====== Linha do tempo ======
            import plotly.express as px
            from datetime import datetime
            import pandas as pd
            import streamlit as st

            # ... (seu código anterior de preparação)

            # ====== Linha do tempo ======
            df = pd.concat([df_z369_total, trkv_hist,
                           wcm_hist], ignore_index=True)
            df["Data"] = pd.to_datetime(df["Data"])

            # === Agrupar aberturas e fechamentos ===
            aberturas = df[df["Evento"] == "Abertura"].groupby(
                "NOTA").first().reset_index()
            fechamentos = df[df["Evento"] == "Fechamento"].groupby(
                "NOTA").first().reset_index()

            timeline = pd.merge(
                aberturas[["NOTA", "TP NOTA",
                           "Texto_Completo", "Data", "STATUS"]],
                fechamentos[["NOTA", "Data"]],
                on="NOTA",
                how="left",
                suffixes=("_Abertura", "_Fechamento")
            )

            timeline["Data_Fechamento"] = timeline["Data_Fechamento"].fillna(
                pd.Timestamp(datetime.now()))

            # === Filtro de ano com opção "Todos" ===
            timeline["Ano_Abertura"] = timeline["Data_Abertura"].dt.year
            anos_disponiveis = sorted(
                timeline["Ano_Abertura"].unique(), reverse=True)
            anos_opcoes = ["Todos os anos"] + \
                [str(a) for a in anos_disponiveis]
            ano_selecionado = st.selectbox("📅 Selecione o ano:", anos_opcoes)

            if ano_selecionado != "Todos os anos":
                timeline = timeline[timeline["Ano_Abertura"]
                                    == int(ano_selecionado)]

            # === Dicionário de cores ===
            cores = {
                "M1": "#F1C40F",
                "M2": "#E74C3C",
                "M3": "#2E86C1",
                "M4": "#8E44AD",
                "M5": "#2BC064",
                "M6": "#6E2C00",
                "M7": "#27AE60",
                "M8": "#17A589",
                "M9": "#7F8C8D",
                "Passagem trkv": "#7F8C8D",
                "Passagem WCM": "#7F8C8D"
            }

            significados = {
                "M1": "Nota monitorada",
                "M2": "Nota crítica",
                "M3": "Nota de retenção",
                "M4": "Nota da Engenharia",
                "M5": "Encerramento manutenção corretiva",
                "M6": "Vagão acidentado/descarrilado",
                "M7": "Encerramento manutenção preventiva",
                "M8": "Plano do PCM",
                "M9": "Vandalismo",
                "Passagem trkv": "trkv",
                "Passagem WCM": "WCM"
            }

            timeline["Tipo_Nota_Desc"] = timeline["TP NOTA"].map(significados)

            # === Ordenar legenda alfabeticamente ===
            categorias_ordenadas = sorted(
                timeline["TP NOTA"].dropna().unique())
            timeline["TP NOTA"] = pd.Categorical(
                timeline["TP NOTA"], categories=categorias_ordenadas, ordered=True)

            # === Plotly Timeline ===
            fig = px.timeline(
                timeline,
                x_start="Data_Abertura",
                x_end="Data_Fechamento",
                y="NOTA",
                color="TP NOTA",
                text="NOTA",
                hover_data={
                    "STATUS": True,
                    "Texto_Completo": True,
                    "Tipo_Nota_Desc": True,
                    "TP NOTA": True,
                    "Data_Abertura": True,
                    "Data_Fechamento": True
                },
                color_discrete_map=cores,
                category_orders={"TP NOTA": categorias_ordenadas}
            )

            fig.update_yaxes(autorange="reversed")
            fig.update_layout(
                title=f"Linha do Tempo de Notas ({ano_selecionado})",
                xaxis_title="Data",
                yaxis_title="Número da Nota",
                height=600,
                hoverlabel_bgcolor="white",
                legend_title_text="Tipo de Nota",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                )
            )

            st.plotly_chart(fig, use_container_width=True)


# linha do tempo End
            col1, col2 = st.columns(2)
            with col1:
                st.header("📈 Truck View - TRKV_MAX_Cunha")
                # df_trkv_trated["Alarme"]
                st.line_chart(df_trkv_trated, x="Data", y="TRKV_MAX_Cunha")
                st.dataframe(df_trkv_trated)

            with col2:
                st.header("📈 WCM - Maior_Impacto_kN")
                df_wcm_trated["Alarme"] = 200
                st.line_chart(df_wcm_trated, x="Data", y=[
                              "Maior_Impacto_kN", "Alarme"])

                st.dataframe(df_wcm_trated)

            # Plota gráfico de linha

            st.write("Dados z369")
            st.dataframe(df_z369)
            st.write("Dados WCM")
            st.dataframe(df_WCM)
            st.write("Dados TRKV")
            st.dataframe(df_trkv)

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
            response = requests.post(WEBHOOK_URL, json=payload, timeout=60)
            if response.status_code == 200:
                return response.text
            else:
                return f"Erro: resposta do servidor {response.status_code}"
        except requests.exceptions.Timeout:
            return "⏱️ Tempo limite excedido: o servidor demorou mais de 60 segundos para responder."
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
    import streamlit as st
    import pandas as pd
    import plotly.express as px

    # ====== Exemplo do seu DataFrame ======
    data = {
        "Data": [
            "2024-01-05", "2024-02-12", "2024-03-28", "2024-04-15", "2024-04-25",
            "2024-05-10", "2024-06-06", "2024-06-06", "2024-06-07", "2024-06-07"
        ],
        "TP NOTA": ["M8", "M8", "M1", "M1", "M8", "M1", "M3", "M5", "M5", "M3"],
        "NOTA": ["NOTA-23651936", "NOTA-23681796", "NOTA-23518544", "NOTA-23733050", "NOTA-23681796", "NOTA-23733050", "NOTA-23771970", "NOTA-23771971", "NOTA-23771971", "NOTA-23771970"],
        "Texto_Completo": [
            "Análise Acionamento - Inspeção", "INSP LONGARINA PRATO", "REVI MONITORADO | Amort",
            "REVI MONITORADO | Freio", "INSP LONGARINA PRATO", "REVI MONITORADO | Freio",
            "VGH DETECTOR ACÚSTICO", "MC RUMO PMV OFVRCI", "MC RUMO PMV OFVRCI", "VGH DETECTOR ACÚSTICO"
        ],
        "Evento": ["Abertura", "Abertura", "Abertura", "Abertura", "Fechamento", "Fechamento", "Abertura", "Abertura", "Fechamento", "Fechamento"]
    }

    df = pd.DataFrame(data)
    df["Data"] = pd.to_datetime(df["Data"])

    # ====== Encontrar início e fim de cada NOTA ======
    aberturas = df[df["Evento"] == "Abertura"].groupby(
        "NOTA").first().reset_index()
    fechamentos = df[df["Evento"] == "Fechamento"].groupby(
        "NOTA").first().reset_index()

    # Unir Abertura e Fechamento
    timeline = pd.merge(
        aberturas[["NOTA", "TP NOTA", "Texto_Completo", "Data"]],
        fechamentos[["NOTA", "Data"]],
        on="NOTA",
        how="left",
        suffixes=("_Abertura", "_Fechamento")
    )

    # Se não tiver fechamento, usa a data da abertura como fim
    timeline["Data_Fechamento"] = timeline["Data_Fechamento"].fillna(
        timeline["Data_Abertura"])

    # ====== Plotly Timeline ======
    fig = px.timeline(
        timeline,
        x_start="Data_Abertura",
        x_end="Data_Fechamento",
        y="NOTA",
        color="TP NOTA",
        text="NOTA",
        hover_data=["Texto_Completo"]
    )

    fig.update_yaxes(autorange="reversed")  # para ordenar de cima p/ baixo
    fig.update_layout(
        title="Linha do Tempo de Notas (Abertura → Fechamento)",
        xaxis_title="Data",
        yaxis_title="Tipo de Nota",
        height=500,
        hoverlabel_bgcolor="white"
    )

    st.plotly_chart(fig, use_container_width=True)


with aba6:  # Teste de Componentes do STREAMLIT
    import datetime
    st.header("Teste de Componentes do STREAMLIT")
    st.title("Teste Title")
    st.write("Teste Write")
    st.write("""#Teste Write""")

    date = st.date_input("When's your birthday", value="today")
    st.write("Your birthday is:", date)
