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
st.divider()

st.subheader("Importer les actualités de la semaine")

uploaded_file = st.file_uploader(
    "Dépose le fichier CSV de la semaine",
    type=["csv"]
)

if uploaded_file is not None:
    weekly_news = pd.read_csv(uploaded_file, sep=";")

    weekly_news = weekly_news.dropna(
        subset=["ticker", "url"],
        how="any"
    )

    st.success("Fichier importé avec succès")

    st.dataframe(
        weekly_news,
        use_container_width=True,
        hide_index=True
    )
