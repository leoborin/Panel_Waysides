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
st.title("Consulta MongoDB via Streamlit v55")

# Cria abas na parte superior
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs(
    ["Verify", "Graph", "Saúde de Frota", "Chat Bot", "Sobre", "Testes de componentes"])

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

# ======= Aba 2 - Sobre =======
with aba2:
    import numpy as np
    import plotly.express as px
    import pandas as pd

    st.header("Sobre o Aplicativo")
    st.write("Este é um app para consulta de dados no MongoDB com Streamlit v3.")
    st.markdown("---")

    # Gera dados de exemplo
    dados = np.random.randn(10)
    df = pd.DataFrame({
        "x": list(range(10)),
        "y": dados,
        "categoria": [f"L{i}" for i in range(10)]
    })

    # Cria layout 2x2a
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    with col1:
        st.subheader("Gráfico 1 - Linha 📈")
        fig1 = px.line(df, x="x", y="y", markers=True, title="Série temporal")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Gráfico 2 - Barras 📊")
        fig2 = px.bar(df, x="categoria", y="y",
                      title="Distribuição por categoria")
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        st.subheader("Gráfico 3 - Histograma 📦")
        fig3 = px.histogram(df, x="y", nbins=5,
                            title="Distribuição dos valores")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("Gráfico 4 - Pizza 🥧")
        fig4 = px.pie(df.head(5), values="y", names="categoria",
                      title="Top 5 categorias")
        st.plotly_chart(fig4, use_container_width=True)

with aba3:

    st.sidebar.markdown("### Portal de BI")

    # st.header("Ficha Vagão")
    st.title("Ficha Vagão - Prognósticos Integrado de Vagões")
    st.write("Testes de desenvolvimento de BI para Vagões")
    df_Z369 = function_to_get_data_from_z369(MONGO_URI, DB_NAME, "z369_full")
    df_Z369_1 = function_to_get_data_from_z369(MONGO_URI, DB_NAME, "z369_full")
    # teste = df_Z369['data_sincronizacao'].drop_duplicates()
    # st.write(teste)
    # contagem_mensal = df_Z369['data_sincronizacao'].dt.to_period('M').value_counts().sort_index()
    df_Z369_1['mes'] = df_Z369_1['data_sincronizacao'].dt.to_period('M')
    # st.write(df_Z369_1.groupby('DESC STATUS').size())
    # st.write(df_Z369_1.groupby('mes').size())

    contagens = (pd.crosstab(df_Z369_1['mes'], df_Z369_1['DESC STATUS'])   # linhas=mes, colunas=status
                 .reindex(columns=['Mensagem encerrada', 'Mensagem pendente', 'Mensagem em processamento'], fill_value=0)
                 .sort_index())
    # st.write(contagens)
    # 3st.dataframe(df_Z369_1)
    # qtd_por_mes =

    cont1 = df_Z369['DESC STATUS'].value_counts()
    col5, col6, col7 = st.columns(3)
    with col5:
        col5 = st.metric(label='Total de Notas fechadas',
                         value=cont1['Mensagem encerrada'], delta='10%')
    with col6:
        col6 = st.metric(label='Total de Notas pendentes',
                         value=cont1['Mensagem pendente'], delta='30%')
    with col7:
        col7 = st.metric(label='Total de Notas em processamento',
                         value=cont1['Mensagem em processamento'], delta='-25%')

    st.date_input(label='Data de Atualização', value='today', disabled=True)

    vagao_input = st.text_input('Escreva um vagão')
    filtro_vagao = df_Z369['ATIVO'] == vagao_input
    st.dataframe(df_Z369[filtro_vagao])

    col1, col2, col3 = st.columns(3)
    with col1:
        col1 = st.selectbox('Selecione um Local', sorted(
            df_Z369['Local'].drop_duplicates()))
        filtro1 = df_Z369["Local"] == col1
        df_Z369 = df_Z369[filtro1]
    with col2:
        col2 = st.selectbox('Selecione um Estado',
                            df_Z369['DESC STATUS'].drop_duplicates())
        filtro2 = df_Z369["DESC STATUS"] == col2
        df_Z369 = df_Z369[filtro2]
    with col3:
        col3 = st.selectbox('Selecione uma Nota', sorted(
            df_Z369['TP NOTA'].drop_duplicates()))
        filtro3 = df_Z369["TP NOTA"] == col3
        df_Z369 = df_Z369[filtro3]

    df1 = df_Z369[filtro3]

    st.dataframe(df1)


with aba4:  # Chat Bot
    import streamlit as st
    import requests
    import pandas as pd
    import io
    import json
    import re
    from datetime import datetime

    WEBHOOK_URL = "http://35.212.133.206/webhook/chatbot"

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
        Tenta json.loads no texto completo, depois em bloco ```json```, depois no primeiro trecho {...} ou [...].
        Retorna (obj, fonte) ou (None, None).
        """
        try:
            return json.loads(text), 'full'
        except Exception:
            pass
        block = _extract_json_block(text)
        if block:
            try:
                return json.loads(block), 'block'
            except Exception:
                pass
        m = re.search(r"(\{.*\}|\[.*\])", text, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1)), 'snippet'
            except Exception:
                pass
        return None, None

    def _possible_markdown_table(text: str) -> bool:
        """
        Heurística para detectar tabela Markdown com linha separadora ---.
        """
        has_pipes = '|' in text
        has_sep_row = re.search(
            r'^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$',
            text, flags=re.MULTILINE
        ) is not None
        return has_pipes and has_sep_row

    def try_parse_table(text: str):
        """
        Tenta converter a resposta em DataFrame.
        Suporta: JSON (lista/dict), bloco ```json```, Markdown table, TSV, pipe, CSV.
        """
        # JSON
        obj, source = _safe_json_loads(text)
        if obj is not None:
            if isinstance(obj, list) and (len(obj) == 0 or isinstance(obj[0], dict)):
                return pd.DataFrame(obj)
            if isinstance(obj, dict):
                for key in ['data', 'items', 'result', 'rows']:
                    if key in obj and isinstance(obj[key], list) and (len(obj[key]) == 0 or isinstance(obj[key][0], dict)):
                        return pd.DataFrame(obj[key])
                return pd.DataFrame([obj])

        # Markdown
        if _possible_markdown_table(text):
            lines = [ln.strip()
                     for ln in text.strip().splitlines() if ln.strip()]
            table_lines = [ln for ln in lines if '|' in ln]
            if table_lines:
                cleaned = "\n".join(
                    [re.sub(r'^\||\|$', '', ln).strip() for ln in table_lines])
                try:
                    df = pd.read_csv(io.StringIO(cleaned), sep='|')
                    # remove linha separadora (---)
                    df = df[[not re.fullmatch(
                        r'\s*:?-{3,}:?\s*', str(x)) for x in df.iloc[:, 0]]]
                    return df.reset_index(drop=True)
                except Exception:
                    pass

        # TSV / Pipe / CSV (nessa ordem)
        for sep in ['\t', '|', ',']:
            if sep in text:
                try:
                    df = pd.read_csv(io.StringIO(text), sep=sep)
                    if df.shape[1] > 1:
                        return df
                except Exception:
                    pass

        return None

    def _format_date_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Converte colunas com 'dt' ou 'data' no nome para dd/mm/yyyy.
        """
        out = df.copy()
        for col in out.columns:
            low = str(col).lower()
            if 'dt' in low or 'data' in low:
                try:
                    series = pd.to_datetime(
                        out[col], errors='coerce', utc=True)
                    series = series.dt.tz_localize(
                        None).dt.strftime('%d/%m/%Y')
                    out[col] = series.fillna(out[col])
                except Exception:
                    pass
        return out

    def _reorder_cols(df: pd.DataFrame) -> pd.DataFrame:
        """
        Reordena colunas para um padrão conhecido, se existirem.
        """
        preferred = [
            'NOTA', 'ATIVO', 'TP NOTA', 'STATUS', 'STATUS_traduzido', 'classificacao_nota',
            'TEXTO', 'TEXTO AVARIA', 'TEXTO CAUSA',
            'dt_abertura_trated', 'dt_fechamento_trated'
        ]
        cols = [c for c in preferred if c in df.columns] + \
            [c for c in df.columns if c not in preferred]
        return df[cols]

    def _remove_json_from_text(text: str) -> str:
        """
        Remove blocos ```...``` e objetos/arrays JSON inline da parte textual exibida.
        (Não afeta o parsing da tabela, que usa o texto original.)
        """
        # Remove blocos de código
        no_code = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        # Remove objetos/arrays JSON inline (heurística ampla)
        no_json = re.sub(r"\[[\s\S]*\]|\{[\s\S]*\}", "", no_code).strip()
        # Colapsa quebras de linha longas
        no_json = re.sub(r"\n{3,}", "\n\n", no_json)
        return no_json

    # -----------------------------
    # 3) UI do chat + renderização
    # -----------------------------
    st.subheader("🤖 VAGO - ChatBot Vagões")

    user_msg = st.chat_input("Digite sua mensagem e pressione Enter")

    if user_msg:
        with st.chat_message("user"):
            st.write(user_msg)

        # Spinner de carregamento + mensagem final "dados carregados"
        with st.chat_message("assistant"):
            placeholder = st.empty()  # cria área para trocar mensagem
            with st.spinner("⏳ Aguardando resposta do servidor..."):
                response_text = send_message_to_webhook(user_msg)

            # após o término do spinner
            placeholder.success("✅ Dados carregados com sucesso!")

        # Processa resposta
        df = try_parse_table(response_text)
        texto_sem_json = _remove_json_from_text(response_text)

        with st.chat_message("assistant"):
            if isinstance(df, pd.DataFrame) and not df.empty:
                # Texto explicativo (sem JSON) acima da tabela
                if texto_sem_json:
                    st.markdown(texto_sem_json)

                # Formata e exibe tabela
                df = _format_date_columns(df)
                df = _reorder_cols(df)
                st.dataframe(df, use_container_width=True)

            else:
                # Quando não há tabela, mostra apenas texto (sem JSON)
                st.markdown(
                    texto_sem_json if texto_sem_json else response_text)


with aba6:  # Teste de Componentes do STREAMLIT
    import datetime
    st.header("Teste de Componentes do STREAMLIT")
    st.title("Teste Title")
    st.write("Teste Write")
    st.write("""#Teste Write""")

    date = st.date_input("When's your birthday", value="today")
    st.write("Your birthday is:", date)
