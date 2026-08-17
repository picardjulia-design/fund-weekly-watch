import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(
    page_title="Fund Weekly Watch",
    page_icon="📊",
    layout="wide"
)

st.title("Fund Weekly Watch")
st.write("Veille hebdomadaire des valeurs du fonds")

# Chargement de la configuration
config = pd.read_csv("config.csv")

st.subheader("Valeurs suivies")
st.dataframe(
    config[["name", "ticker", "weight"]],
    use_container_width=True,
    hide_index=True
)
