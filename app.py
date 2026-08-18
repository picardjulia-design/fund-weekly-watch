from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
import yfinance as yf
import json
from urllib.error import HTTPError, URLError
try:
    MISTRAL_API_KEY = st.secrets["MISTRAL_API_KEY"]
except Exception:
    MISTRAL_API_KEY = st.sidebar.text_input(
        "Clé API Mistral",
        type="password"
    )
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

# Fallback : si les paragraphes sont trop pauvres,
# on récupère le texte général de la page
if len(text) < 300:
    text = soup.get_text(" ", strip=True)

if len(text) < 300:
    return None

        return text[:12000]

    except Exception:
        return None

def call_mistral(prompt, api_key):
    url = "https://api.mistral.ai/v1/chat/completions"

    payload = {
        "model": "mistral-small-latest",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2
    }

    data = json.dumps(payload).encode("utf-8")

    request = Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

        return result["choices"][0]["message"]["content"]

    except HTTPError as e:
        return f"Erreur API Mistral : {e.code}"

    except URLError:
        return "Impossible de contacter Mistral."

    except Exception as e:
        return f"Erreur : {str(e)}"
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
if MISTRAL_API_KEY:
    st.success("Clé Mistral détectée")
else:
    st.warning("Aucune clé Mistral détectée")
st.divider()
st.subheader("Génération du commentaire")

if uploaded_file is not None:

    available_tickers = weekly_news["ticker"].dropna().unique().tolist()

    selected_ticker = st.selectbox(
        "Valeur à analyser",
        available_tickers
    )

    if st.button("Générer le commentaire"):

        # Informations de la valeur
        company_config = config[
            config["ticker"] == selected_ticker
        ]

        if company_config.empty:
            st.error("Cette valeur n'existe pas dans config.csv.")
            st.stop()

        company_name = company_config.iloc[0]["name"]
        weight = company_config.iloc[0]["weight"]

        # Articles associés à cette valeur
        company_news = weekly_news[
            weekly_news["ticker"] == selected_ticker
        ]

        article_contents = []

        for _, article in company_news.iterrows():

            text = extract_article_text(article["url"])

            if text:
                article_contents.append(
                    f"""
TITRE : {article['title']}

CONTENU :
{text}
"""
                )

        if not article_contents:
            st.error(
                "Aucun des articles de cette valeur n'a pu être lu."
            )
            st.stop()

        # Récupération des cours spécifiquement pour cette valeur
        yf_ticker = company_config.iloc[0]["yfinance_ticker"]

        data = yf.download(
            yf_ticker,
            start=monday - timedelta(days=7),
            end=friday + timedelta(days=3),
            progress=False,
            auto_adjust=False
        )

        closes = data["Close"].dropna()

        if hasattr(closes, "columns"):
            closes = closes.iloc[:, 0]

        closes = closes[closes.index.date <= friday]

        week_closes = closes[
            (closes.index.date >= monday) &
            (closes.index.date <= friday)
        ]

        if week_closes.empty:
            st.error("Impossible de récupérer les cours.")
            st.stop()

        price_text = []

        for dt, close in week_closes.items():

            position = closes.index.get_loc(dt)

            if position > 0:
                previous_close = closes.iloc[position - 1]
                variation = (close / previous_close - 1) * 100
            else:
                variation = None

            price_text.append(
                f"{dt.strftime('%A %d/%m/%Y')} : "
                f"{float(close):.2f} "
                f"({variation:+.2f} %)"
                if variation is not None
                else f"{dt.strftime('%A %d/%m/%Y')} : {float(close):.2f}"
            )

        first_position = closes.index.get_loc(week_closes.index[0])

        if first_position > 0:
            previous_close = closes.iloc[first_position - 1]
            weekly_perf = (
                week_closes.iloc[-1] / previous_close - 1
            ) * 100
        else:
            weekly_perf = 0

        prompt = f"""
Tu es analyste au sein d'une société de gestion d'actifs.

Tu dois rédiger le commentaire hebdomadaire d'une valeur détenue
dans un fonds thématique.

VALEUR
{company_name} ({selected_ticker})

POIDS DANS LE FONDS
{weight} %

COURS DE LA SEMAINE
{chr(10).join(price_text)}

PERFORMANCE HEBDOMADAIRE
{weekly_perf:+.2f} %

INFORMATIONS DISPONIBLES
{chr(10).join(article_contents)}

Rédige UN SEUL paragraphe en français de 4 à 6 phrases.

Contraintes impératives :

- Commence directement par le fait marquant de la semaine.
- Utilise les chiffres précis présents dans les informations fournies
  lorsqu'ils sont pertinents.
- Explique explicitement comment ces événements peuvent avoir contribué
  au mouvement du cours observé pendant la semaine.
- Si le comportement du titre paraît contradictoire avec les nouvelles,
  signale-le explicitement.
- Termine par une phrase indiquant l'implication pour la position dans
  le fonds : risque, catalyseur à venir ou point de vigilance.
- Adopte un ton factuel, concis et professionnel de note de gestion.
- Ne mentionne jamais "l'article", "les articles", "la presse",
  "la source" ou "selon".
- N'invente aucun chiffre ni aucune information.
- Si une information n'est pas disponible, ne la suppose pas.
"""

        with st.spinner("Génération du commentaire..."):
            comment = call_mistral(
                prompt,
                MISTRAL_API_KEY
            )

        st.text_area(
            "Commentaire généré",
            value=comment,
            height=220
        )
