import numpy as np
import plotly.express as px
import pandas as pd
import streamlit as st
from pymongo import MongoClient
import matplotlib.pyplot as plt
from PIL import Image

st.title("BI em desenvolvimento")
st.header("Centralização de dados")

if st.button("snow"):
    st.snow()

#st.button("snow",on_click= st.write("teste"))