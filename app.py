from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
import yfinance as yf

def extract_article_text(url):
    try:
        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/120 Safari/537.36"
                )
            }
        )

        with urlopen(request, timeout=15) as response:
            html = response.read()

        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        paragraphs = soup.find_all("p")

        text = "\n".join(
            p.get_text(" ", strip=True)
            for p in paragraphs
            if len(p.get_text(" ", strip=True)) > 40
        )

        if len(text) < 300:
            return None

        return text[:12000]

    except Exception:
        return None
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
from datetime import date, timedelta

st.divider()
st.subheader("Cours de la semaine")

selected_date = st.date_input(
    "Choisis une date comprise dans la semaine à analyser",
    value=date.today()
)

monday = selected_date - timedelta(days=selected_date.weekday())
friday = monday + timedelta(days=4)

st.write(
    f"Semaine analysée : du {monday.strftime('%d/%m/%Y')} "
    f"au {friday.strftime('%d/%m/%Y')}"
)

if st.button("Récupérer les cours"):
    price_rows = []

    for _, row in config.iterrows():
        yf_ticker = row["yfinance_ticker"]

        # On récupère quelques jours avant pour avoir
        # la clôture précédente du lundi
        data = yf.download(
            yf_ticker,
            start=monday - timedelta(days=7),
            end=friday + timedelta(days=3),
            progress=False,
            auto_adjust=False
        )

        if data.empty:
            continue

        closes = data["Close"].dropna()

        if hasattr(closes, "columns"):
            closes = closes.iloc[:, 0]

        # On garde toutes les clôtures jusqu'au vendredi
        closes = closes[closes.index.date <= friday]

        # Séances de la semaine analysée
        week_closes = closes[
            (closes.index.date >= monday) &
            (closes.index.date <= friday)
        ]

        if week_closes.empty:
            continue

        for dt, close in week_closes.items():
            position = closes.index.get_loc(dt)

            daily_change = None

            if position > 0:
                previous_close = closes.iloc[position - 1]
                daily_change = (close / previous_close - 1) * 100

            price_rows.append({
                "name": row["name"],
                "ticker": row["ticker"],
                "date": dt.strftime("%d/%m/%Y"),
                "close": round(float(close), 2),
                "daily_change_%": (
                    round(float(daily_change), 2)
                    if daily_change is not None
                    else None
                )
            })

        # Performance totale de la semaine :
        # dernière clôture / clôture précédente au lundi
        first_date = week_closes.index[0]
        first_position = closes.index.get_loc(first_date)

        weekly_perf = None

        if first_position > 0:
            previous_week_close = closes.iloc[first_position - 1]
            last_close = week_closes.iloc[-1]
            weekly_perf = (last_close / previous_week_close - 1) * 100

        if weekly_perf is not None:
            price_rows.append({
                "name": row["name"],
                "ticker": row["ticker"],
                "date": "Performance semaine",
                "close": None,
                "daily_change_%": round(float(weekly_perf), 2)
            })

    prices_df = pd.DataFrame(price_rows)

    if prices_df.empty:
        st.warning("Aucun cours trouvé pour cette semaine.")
    else:
        st.success("Cours récupérés avec succès")
        st.dataframe(
            prices_df,
            use_container_width=True,
            hide_index=True
        )
st.divider()
st.subheader("Test de lecture des articles")

if uploaded_file is not None:
    test_url = st.selectbox(
        "Choisis un article à tester",
        weekly_news["url"].tolist()
    )

    if st.button("Lire cet article"):
        article_text = extract_article_text(test_url)

        if article_text:
            st.success("Article lu avec succès")
            st.text_area(
                "Texte récupéré",
                article_text,
                height=300
            )
        else:
            st.warning(
                "Impossible de lire cette source automatiquement."
            )
