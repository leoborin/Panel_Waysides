import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import os
import glob

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
df_trkv = dfs["df_trkv"]
df_WCM = dfs["df_WCM"]
df_z369 = dfs["df_z369"]
df_z851 = dfs["df_z851"]
df_z1568 = dfs["df_z1568"]
df_tbogi = dfs["df_tbogi"]


# -----------------------------
# Configuração da página
# -----------------------------
st.set_page_config(page_title="Saúde da Frota de Vagões", page_icon="🚆", layout="wide")

# Paleta de cores
PRIMARY = "#0D3B66"
ACCENT = "#5EA9DD"
CARD_BG = "#F5F8FC"
BORDER = "#DEE6F1"
SUCCESS = "#3CB371"
WARNING = "#F39C12"
DANGER = "#E74C3C"
TEXT = "#1F2D3D"
MUTED = "#6C7C8C"

# -----------------------------
# CSS customizado
# -----------------------------
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

# -----------------------------
# Topbar
# -----------------------------
st.markdown("""
<div class="topbar">
  <div class="title">SAÚDE DA FROTA DE VAGÕES</div>
  <div class="menu">
    <div class="pill">🧭 Visão executiva</div>
    <div class="pill">⚠️ Previsões & Riscos</div>
    <div class="pill">🧩 Saúde dos componentes</div>
    <div class="pill">📓 Detalhamento por vagão</div>
  </div>
  <div class="brand">rumo</div>
</div>
""", unsafe_allow_html=True)

st.write("")  # Espaço

# ------------------------------------------------
# CALCULOS
# ---------------------------------------------

df_sem_duplicatas = df_z851.drop_duplicates(subset=['EQUNR'], keep='first')
df_z851 = df_z851[df_z851['ELIMINADO'] != 'X']
df_z851 = df_z851[df_z851['MALHA'] == 'N']
df_z851 = df_z851[df_z851['BITOLA'] == 'L']
df_z851_copia = df_z851

df_z851_copia["count"] = df_z851_copia["STATUS"].value_counts()
vagoes_disp = df_z851_copia["STATUS"].value_counts()
#st.dataframe(vagoes_disp)
disp_metric = (f'{(vagoes_disp[0]*100)/(vagoes_disp[0]+vagoes_disp[1]):.2f}')
retidos_metric = (f'{(vagoes_disp[1]*100)/(vagoes_disp[0]+vagoes_disp[1]):.2f}')
retidos_value = vagoes_disp[1]










# -----------------------------
# KPIs (8 colunas lado a lado)
# -----------------------------
kpis = [
    ("Disponibilidade", str(disp_metric)+'%', "Objetivo", SUCCESS),
    ("Frota em manutenção", str(retidos_metric)+'%', "Backlog", WARNING),
    ("Vagões críticos", "27", "Estado", DANGER),
    ("Incidentes (Mês)", "1.218", "Ocorrências", DANGER),
    ("Vagões retidos", str(retidos_value), "Pátio", WARNING),
    ("Vagões novos", "0", "Entrada", SUCCESS),
    ("KM MTBF médio", "150.321", "km", ACCENT),
    ("Componente crítico", "Engate-TESTE", "Atual", PRIMARY),
]

cols = st.columns(8)
for i, (lbl, val, sub, color) in enumerate(kpis):
    with cols[i]:
        st.markdown(f"""
        <div style="
            background-color:{CARD_BG};
            border:1px solid {BORDER};
            border-radius:10px;
            padding:10px;
            text-align:center;
        ">
            <div style="color:{MUTED};font-size:12px;font-weight:600;">{lbl}</div>
            <div style="color:{color};font-size:22px;font-weight:800;">{val}</div>
            <div style="color:{MUTED};font-size:11px;">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")  # Espaço

# -----------------------------
# Dados simulados
# -----------------------------
np.random.seed(42)
dates = pd.date_range(datetime.today() - timedelta(days=180), periods=26, freq="7D")
df_dispon = pd.DataFrame({"data": dates, "disponibilidade": np.clip(85 + np.cumsum(np.random.randn(len(dates))), 70, 98)})
df_kmmtbf = pd.DataFrame({"data": dates, "km_mtbf": np.clip(120000 + np.cumsum(np.random.randn(len(dates))*3000), 80000, 160000)})

ranking_alertas = pd.DataFrame({
    "Vagão": [f"V{1000+i}" for i in range(12)],
    "Componente": np.random.choice(["Engate","Freio","Rolamento","Trincas","Estrutura"], 12),
    "Severidade": np.random.choice(["Alta","Média","Baixa"], 12, p=[0.45,0.4,0.15]),
    "Score": np.random.randint(60, 99, 12),
    "Último evento": pd.to_datetime("today").normalize() - pd.to_timedelta(np.random.randint(0, 30, 12), unit="D")
}).sort_values(["Severidade","Score"], ascending=[False,False]).reset_index(drop=True)

# -----------------------------
# Funções de gráfico
# -----------------------------
def semicircle_gauge(title:str, value:int, color:str=ACCENT) -> go.Figure:
    v = max(0, min(100, int(value)))
    values = [v, 100 - v, 100]
    fig = go.Figure(go.Pie(values=values, hole=0.7, rotation=180, sort=False,
                            marker=dict(colors=[color, "#E1ECF4", "rgba(0,0,0,0)"]),
                            textinfo="none"))
    fig.add_annotation(text=f"<b>{v}%</b><br><span style='color:{MUTED};font-size:12px;'>SCORE</span>",
                       showarrow=False, font=dict(size=20), x=0.5, y=0.5)
    fig.add_annotation(text=f"<b>{title}</b>", showarrow=False, x=0.5, y=1.2,
                       font=dict(size=14, color=TEXT))
    fig.update_layout(height=220, margin=dict(l=10, r=10, t=40, b=0), paper_bgcolor="white")
    return fig

def line_plot(df, x, y, title, y_title, color=PRIMARY):
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

# -----------------------------
# Layout principal
# -----------------------------
left, right = st.columns([8, 3], gap="small")

with left:
    st.markdown("<div class='section-box'><div class='section-title'>VISÃO MACRO DA FROTA</div>", unsafe_allow_html=True)
    g1, g2, g3, g4 = st.columns(4)
    g1.plotly_chart(semicircle_gauge("GRANELEIROS", 70, ACCENT), use_container_width=True)
    g2.plotly_chart(semicircle_gauge("PLATAFORMAS", 70, WARNING), use_container_width=True)
    g3.plotly_chart(semicircle_gauge("TANQUES", 70, ACCENT), use_container_width=True)
    g4.plotly_chart(semicircle_gauge("REFRIGERADOS", 70, SUCCESS), use_container_width=True)

    l1, l2 = st.columns(2)
    l1.plotly_chart(line_plot(df_dispon, "data", "disponibilidade", "Evolução da disponibilidade", "Disponibilidade (%)", color=SUCCESS), use_container_width=True)
    l2.plotly_chart(line_plot(df_kmmtbf, "data", "km_mtbf", "Evolução do KM MTBF", "KM", color=PRIMARY), use_container_width=True)

    st.markdown("<div class='caption'>GRÁFICO DE ADERÊNCIA À PREVISÃO DE PASSAGEM - ZTO e TOM</div></div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='section-box'><div class='section-title'>RANKING DE ALERTAS</div>", unsafe_allow_html=True)
    sev = st.multiselect("Severidade", ["Alta","Média","Baixa"], default=["Alta","Média","Baixa"])
    comp = st.multiselect("Componente", ["Engate","Freio","Rolamento","Trincas","Estrutura"], default=["Engate","Freio","Rolamento","Trincas","Estrutura"])
    rf = ranking_alertas[(ranking_alertas["Severidade"].isin(sev)) & (ranking_alertas["Componente"].isin(comp))]
    st.dataframe(rf, hide_index=True, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
