import datetime
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import streamlit.components.v1 as components

#Criando um serviço multi-paginas
#Utilizado para padronização de componentes para todas as paginas
#Podemos utilizar para cabeçalho/rodapes e config de paginas, sidebars
# st.title("Página Home do BI - Centralização dos dados")
# st.set_page_config(layout="wide")
# pg = st.navigation([st.Page("pages/1-📊Graph.py"),st.Page("pages/2-🎯Saúde de Frota.py"),
#                     st.Page("pages/3-🤖Chat Bot.py"), st.Page("pages/4-🚆Sobre.py"), st.Page("pages/5-Testes de componentes.py")])
# pg.run()



st.header("HEADER Teste de Componentes do STREAMLIT")
st.header("HEADER Teste de 22222222222 do STREAMLIT", width=3800, divider="blue")
st.title("TITLE Teste Title")
st.write("WRITE Teste Write")
st.write("""#Teste Write""")
st.badge("New")
st.badge("Success", icon=":material/check:", color="green")
st.markdown(
    ":violet-badge[:material/star: Favorite] :orange-badge[⚠️ Needs review] :gray-badge[Deprecated]"
)

# Defina o estilo CSS para o contêiner
st.markdown("""
<style>
    .st-emotion-cache-119tkyc {
        background-color: #f0f8ff; /* Cor de fundo (azul claro) */
        padding: 20px; /* Preenchimento interno */
        border-radius: 10px; /* Borda arredondada */
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2); /* Sombra */
    }
</style>
""", unsafe_allow_html=True)

st.title("Retângulo Colorido com `st.container`")

# Crie o contêiner e adicione o conteúdo dentro dele
with st.container():
    st.write("Este é o seu retângulo colorido!")
    st.write("Você pode adicionar qualquer conteúdo aqui.")

st.write("Este texto está fora do contêiner e não é afetado pelo CSS.")

# st.markdown("""
#     <style>
#         .meu-botao {
#             background-color: #4CAF50;
#             color: white;
#             padding: 10px 20px;
#             border: none;
#             border-radius: 5px;
#             cursor: pointer;
#             font-size: 16px;
#         }
#     </style>
#     <button class="meu-botao">Botão Personalizado</button>
# """, unsafe_allow_html=True)


# components.html("""
#     <style>
#         .botao-unico {
#             background-color: #2196F3;
#             color: white;
#             padding: 12px 24px;
#             border: none;
#             border-radius: 8px;
#             font-size: 18px;
#         }
#     </style>
#     <button class="botao-unico">Clique Aqui</button>
# """, height=100)

with open("css/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


with st.container(key="container1", width="stretch"):
  col1, col2, col3 = st.columns(3)
  with col1: st.write("TESTE")
  with col2: st.image("assets/logo.png")

# Botões com classes específicas
#st.markdown('<div class="btn-amarelo">', unsafe_allow_html=True)
botao1 = st.button("Processar dados", key="btn1")
#st.markdown('</div>', unsafe_allow_html=True)
if botao1:
    st.balloons()

st.markdown('<div class="btn-outline">', unsafe_allow_html=True)
st.button("Exportar CSV", key="btn2")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
st.button("Excluir tudo", key="btn3")
st.markdown('</div>', unsafe_allow_html=True)


date= st.date_input("When's your birthday", value="today")
st.write("Your birthday is:", date)

import streamlit.components.v1 as components

# bootstrap 4 collapse example
components.html(
    """
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
    <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>
    <div id="accordion">
      <div class="card">
        <div class="card-header" id="headingOne">
          <h5 class="mb-0">
            <button class="btn btn-link" data-toggle="collapse" data-target="#collapseOne" aria-expanded="true" aria-controls="collapseOne">
            Collapsible Group Item #1
            </button>
          </h5>
        </div>
        <div id="collapseOne" class="collapse show" aria-labelledby="headingOne" data-parent="#accordion">
          <div class="card-body">
            Collapsible Group Item #1 content
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-header" id="headingTwo">
          <h5 class="mb-0">
            <button class="btn btn-link collapsed" data-toggle="collapse" data-target="#collapseTwo" aria-expanded="false" aria-controls="collapseTwo">
            Collapsible Group Item #2
            </button>
          </h5>
        </div>
        <div id="collapseTwo" class="collapse" aria-labelledby="headingTwo" data-parent="#accordion">
          <div class="card-body">
            Collapsible Group Item #2 content
          </div>
        </div>
      </div>
    </div>
    """,
    height=600,
)
#---------------------------------------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["Cat", "Dog", "Owl"])

with tab1:
    st.header("A cat")
    st.image("https://static.streamlit.io/examples/cat.jpg", width=200)
with tab2:
    st.header("A dog")
    st.image("https://static.streamlit.io/examples/dog.jpg", width=200)
with tab3:
    st.header("An owl")
    st.image("https://static.streamlit.io/examples/owl.jpg", width=200)
#---------------------------------------------------------------------------------------------------------
# Using object notation
add_selectbox = st.sidebar.selectbox(
    "How would you like to be contacted?",
    ("Email", "Home phone", "Mobile phone")
)

# Using "with" notation
with st.sidebar:
    add_radio = st.radio(
        "Choose a shipping method",
        ("Standard (5-15 days)", "Express (2-5 days)")
    )
#---------------------------------------------------------------------------------------------------------
with st.container():
    st.write("This is inside the container")

    # You can call any Streamlit command, including custom components:
    st.bar_chart(np.random.randn(50, 3))

st.write("This is outside the container")
#---------------------------------------------------------------------------------------------------------
@st.dialog("Cast your vote")
def vote(item):
    st.write(f"Why is {item} your favorite?")
    reason = st.text_input("Because...")
    if st.button("Submit"):
        st.session_state.vote = {"item": item, "reason": reason}
        st.rerun()

if "vote" not in st.session_state:
    st.write("Vote for your favorite")
    if st.button("A"):
        vote("A")
    if st.button("B"):
        vote("B")
else:
    f"You voted for {st.session_state.vote['item']} because {st.session_state.vote['reason']}"
#---------------------------------------------------------------------------------------------------------
if  st.button("Toast"):
    st.toast("Your edited image was saved!", icon="😍")
if st.button("baloes"):
    st.balloons()
if st.button("snow"):
    st.snow()
