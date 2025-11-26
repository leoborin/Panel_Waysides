import streamlit as st
from PIL import Image
# Configurações MongoDB
MONGO_URI = "mongodb+srv://int_dados:e7bUe2bXbKDu3Xzr@rumo-dev2.hbdcrld.mongodb.net/?authSource=admin"
DB_NAME = "supervisorio"
with open("css/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.set_page_config(layout="wide")
logo = Image.open("assets/logo.png")
st.logo(logo, size='large')
# Mensagem de boas-vindas
st.markdown("<h1 style='text-align: center;'>👋 Bem vindo ao Portal de Inteligência de Dados</h1>", unsafe_allow_html=True)
st.markdown("""
    <style>
        header {
            background-color: #32A6E6 !important; /* Cor azul */
            height: 60px !important; /* Ajusta altura */
            color: white !important; /* Cor do texto */
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            font-size: 20px;
            font-weight: bold;
        }
        header .st-emotion-cache-1dp5vir { /* Remove logo padrão se quiser */
            display: none;
        }
        header:before {
            
            content: 'RailCenter - Inteligência de Dados';
            color: white;
            font-size: 18px;
            font-weight: bold;
            display: block;
            width: 100%; /* Ocupa toda a largura disponível */
            text-align: left; /* Alinha à esquerda */
            padding-left: 20px; /* Espaço interno */
            white-space: nowrap; /* Evita quebra de linha */
        }
        .card-button {
    background-color: #F0E8E6;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    text-align: center;
    border-color: transparent;  
    flex-direction: column
    box-sizing: border-box;  /* Padding não “estoura” o tamanho */
    min-height: 140px;       /* Opcional: altura mínima */
    height: 100%;
    width: 100%; 

}
.card-button:hover {
    transform: scale(1.02);
    box-shadow: 0px 8px 16px rgba(0,0,0,0.3);
}
</style>""", unsafe_allow_html=True)


col1, col2 = st.columns([1, 2])
st.markdown("<br>", unsafe_allow_html=True) 
with col1:
    st.image("assets/vg666.png", width=100)

with col2:
    st.title("RailCenter - Inteligência de Dados")
# Layout dos cards
cols = st.columns(3)
with cols[0]:
    st.markdown("""
<a href="https://panelwaysides-xfblbinrrpidr7nkwhmykk.streamlit.app/Consulta_Master" target="_self">
<button id="consulta-btn" class="card-button">
<h3>Consulta Master</h3>
<p>Realize uma pesquisa detalhada de cada Ativo</p>
</button>
</a>
""", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True) 
    st.markdown("""
<a href="https://panelwaysides-xfblbinrrpidr7nkwhmykk.streamlit.app/Gest%C3%A3o_de_Ativos" target="_self">
<button id="consulta-btn" class="card-button">
<h3>Gestão de Ativos</h3>
<p>Detalhes da Gestão de Ativos</p>
</button>
</a>
""", unsafe_allow_html=True)
with cols[1]:
    st.markdown("""
<a href="https://panelwaysides-xfblbinrrpidr7nkwhmykk.streamlit.app/Chat_Bot" target="_self">
<button id="consulta-btn" class="card-button">
<h3>🤖 Chat Bot</h3>
<p>Consulte nossa base de dados conversando com chatbot</p>
</button>
</a>
""", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True) 
    st.markdown("""
<a href="https://panelwaysides-xfblbinrrpidr7nkwhmykk.streamlit.app/Consulta_Master" target="_self">
<button id="consulta-btn" class="card-button">
<h3>Consulta Master</h3>
<p>Realize uma pesquisa detalhada de cada Ativo</p>
</button>
</a>
""", unsafe_allow_html=True)
with cols[2]:
    st.markdown("""
<a href="https://panelwaysides-xfblbinrrpidr7nkwhmykk.streamlit.app/Saude_de_Frota" target="_self">
<button id="consulta-btn" class="card-button">
<h3>🎯Saude_de_Frota</h3>
<p>Consulte a Saúde da frota da Malha Norte</p>
</button>
</a>
""", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True) 
    st.markdown("""
<a href="https://panelwaysides-xfblbinrrpidr7nkwhmykk.streamlit.app/Consulta_Master" target="_self">
<button id="consulta-btn" class="card-button">
<h3>Consulta Master</h3>
<p>Realize uma pesquisa detalhada de cada Ativo</p>
</button>
</a>
""", unsafe_allow_html=True)



