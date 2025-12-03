import streamlit as st
import requests
import io
import json
import re
from datetime import datetime
from pymongo import MongoClient
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

with open("css/style.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


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
            st.dataframe(df, width='stretch')
        else:
            st.markdown(
                texto_sem_json if texto_sem_json else response_text)

