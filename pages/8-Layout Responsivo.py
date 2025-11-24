 # app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from numpy.random import default_rng as rng
from streamlit_plotly_events import plotly_events


st.set_page_config(layout="wide")
st.title("Dashboard com Crossfilter (Plotly)")

@st.cache_data
def load_data():
    # Exemplo: dataset sintético
    df = pd.DataFrame({
        "categoria": ["A","A","B","B","C","C"] * 5,
        "data": pd.date_range("2024-01-01", periods=30, freq="D"),
        "valor": (pd.Series(range(30))*3.5 + 10).sample(30, random_state=42).values
    })
    return df

df = load_data()

# Estado de filtro: categorias selecionadas
if "cats" not in st.session_state:
    st.session_state.cats = []

col1, col2 = st.columns([1, 2])

with col1:
    df_agg = df.groupby("categoria", as_index=False)["valor"].sum().sort_values("valor", ascending=False)
    fig_bar = px.bar(df_agg, x="categoria", y="valor", title="Clique na barra para filtrar")
    #fig_bar.update_layout(margin=dict(l=10,r=10,t=40,b=10))

    # Captura eventos de clique/seleção
    points = plotly_events(
        fig_bar,
        click_event=True,
        select_event=True,
        hover_event=False,          # desnecessário
        override_height=400,
        override_width="100%"
    )

    # Extrai categorias clicadas/selecionadas
    selected_cats = [p.get("x") for p in points] if points else []

    # Atualiza o filtro (toggle simples)
    if selected_cats:
        st.session_state.cats = selected_cats

    # Botão para limpar filtro
    if st.button("Limpar filtro", type="secondary"):
        st.session_state.cats = []

    # Mostra o estado atual
    st.caption(f"Filtro categorias: {st.session_state.cats or '— (sem filtro)'}")

with col2:
    # Aplica o filtro nas demais views
    df_f = df[df["categoria"].isin(st.session_state.cats)] if st.session_state.cats else df.copy()

    # Tabela filtrada
    st.subheader("Tabela filtrada")
    st.dataframe(df_f.sort_values(["categoria","data"]), use_container_width=True, hide_index=True)

    # Outro gráfico filtrado (ex.: série temporal)
    st.subheader("Série temporal filtrada")
    fig_line = px.line(df_f, x="data", y="valor", color="categoria")
    if (st.session_state.cats != [] and  st.session_state.cats[0] == 'C' ):
        st.session_state.cats = []
        st.switch_page("pages/1-📊Consulta Master.py")
        
        #pg.run()
    if (st.session_state.cats != [] and st.session_state.cats[0] == 'B'):
        st.session_state.cats = []
        st.switch_page("pages/2 - 🤖Chat Bot.py")

df2 = pd.DataFrame(
    rng(0).standard_normal((12, 5)), columns=["a", "b", "c", "d", "e"]
)
event = st.dataframe(
    df2,
    key="data",
    on_select="rerun",
    selection_mode=["multi-row", "multi-column","multi-cell"]
)

event.selection

print(event.selection.cells[0])
st.write(df2.loc[event.selection.cells[0][0],event.selection.cells[0][1]])