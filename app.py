import streamlit as st
import pandas as pd
import yfinance as yf
import json

from datetime import date, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Weekly Fund Monitor",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>

.stApp {
    background-color: #FFFFFF;
}

.block-container {
    max-width: 1450px;
    padding-top: 2.5rem;
    padding-bottom: 5rem;
}

/* Titres */

h1 {
    color: #17324D;
    font-size: 2.4rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem !important;
}

h2 {
    color: #17324D;
    font-size: 1.45rem !important;
    font-weight: 600 !important;
    margin-top: 2.5rem !important;
}

h3 {
    color: #17324D;
    font-size: 1.15rem !important;
    font-weight: 600 !important;
}

p, label {
    color: #333333;
}

/* Boutons */

.stButton > button {
    background-color: #17324D;
    color: white;
    border: none;
    border-radius: 0px;
    padding: 0.55rem 1.2rem;
    font-weight: 500;
}

.stButton > button:hover {
    background-color: #294D6D;
    color: white;
    border: none;
}

/* Champs */

[data-baseweb="select"] > div,
textarea,
input {
    border-radius: 0px !important;
    box-shadow: none !important;
}

/* Tableaux */

[data-testid="stDataFrame"] {
    border-top: 2px solid #17324D;
    border-bottom: 1px solid #D6D6D6;
}

/* File uploader */

[data-testid="stFileUploader"] {
    border-radius: 0px;
}

/* Séparateurs */

hr {
    border: none;
    border-top: 1px solid #D9D9D9;
    margin: 2.5rem 0;
}

/* Alertes */

[data-testid="stAlert"] {
    border-radius: 0px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# CLÉ MISTRAL
# ============================================================

try:
    MISTRAL_API_KEY = st.secrets["MISTRAL_API_KEY"]
except Exception:
    MISTRAL_API_KEY = st.sidebar.text_input(
        "Clé API Mistral",
        type="password"
    )


# ============================================================
# FONCTIONS
# ============================================================

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

        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside"
        ]):
            tag.decompose()

        paragraphs = soup.find_all("p")

        text = "\n".join(
            p.get_text(" ", strip=True)
            for p in paragraphs
            if len(p.get_text(" ", strip=True)) > 40
        )

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
            result = json.loads(
                response.read().decode("utf-8")
            )

        return result["choices"][0]["message"]["content"]

    except HTTPError as e:
        return f"Erreur API Mistral : {e.code}"

    except URLError:
        return "Impossible de contacter Mistral."

    except Exception as e:
        return f"Erreur : {str(e)}"


def get_stock_data(yf_ticker, monday, friday):

    data = yf.download(
        yf_ticker,
        start=monday - timedelta(days=7),
        end=friday + timedelta(days=3),
        progress=False,
        auto_adjust=False
    )

    if data.empty:
        return None

    closes = data["Close"].dropna()

    if hasattr(closes, "columns"):
        closes = closes.iloc[:, 0]

    closes = closes[
        closes.index.date <= friday
    ]

    week_closes = closes[
        (closes.index.date >= monday) &
        (closes.index.date <= friday)
    ]

    if week_closes.empty:
        return None

    return closes, week_closes


# ============================================================
# DONNÉES
# ============================================================

config = pd.read_csv("config.csv")


# ============================================================
# EN-TÊTE
# ============================================================

st.title("Weekly Fund Monitor")

st.caption(
    "Suivi hebdomadaire des valeurs du fonds — "
    "cours, actualités et commentaires de gestion"
)

st.divider()


# ============================================================
# PARAMÈTRES DE LA SEMAINE
# ============================================================

st.subheader("Semaine analysée")

col1, col2 = st.columns([1, 2])

with col1:

    selected_date = st.date_input(
        "Sélectionner une date",
        value=date.today()
    )

monday = (
    selected_date -
    timedelta(days=selected_date.weekday())
)

friday = monday + timedelta(days=4)

with col2:

    st.write("")
    st.write("")

    st.markdown(
        f"**{monday.strftime('%d/%m/%Y')} "
        f"— {friday.strftime('%d/%m/%Y')}**"
    )


# ============================================================
# IMPORT DES SOURCES
# ============================================================

st.subheader("Sources de la semaine")

uploaded_file = st.file_uploader(
    "Importer le fichier CSV contenant ticker, title et url",
    type=["csv"]
)

weekly_news = None

if uploaded_file is not None:

    try:

        weekly_news = pd.read_csv(
            uploaded_file,
            sep=";"
        )

        weekly_news = weekly_news.dropna(
            subset=["ticker", "url"],
            how="any"
        )

        st.success(
            f"{len(weekly_news)} source(s) importée(s)"
        )

        with st.expander("Voir les sources importées"):

            st.dataframe(
                weekly_news,
                use_container_width=True,
                hide_index=True
            )

    except Exception as e:

        st.error(
            f"Impossible de lire le fichier : {e}"
        )


st.divider()


# ============================================================
# TABLEAU DES COURS
# ============================================================

st.subheader("Performance des valeurs")

if st.button("Actualiser les cours"):

    price_rows = []

    for _, row in config.iterrows():

        result = get_stock_data(
            row["yfinance_ticker"],
            monday,
            friday
        )

        if result is None:
            continue

        closes, week_closes = result

        row_data = {
            "Valeur": row["name"],
            "Ticker": row["ticker"]
        }

        day_names = {
            0: "Lun.",
            1: "Mar.",
            2: "Mer.",
            3: "Jeu.",
            4: "Ven."
        }

        for dt, close in week_closes.items():

            position = closes.index.get_loc(dt)

            variation = None

            if position > 0:

                previous_close = closes.iloc[
                    position - 1
                ]

                variation = (
                    close / previous_close - 1
                ) * 100

            day = day_names.get(
                dt.weekday(),
                dt.strftime("%d/%m")
            )

            row_data[day] = round(
                float(close),
                2
            )

            if variation is not None:

                row_data[f"{day} %"] = (
                    f"{variation:+.2f}%"
                )

        first_position = closes.index.get_loc(
            week_closes.index[0]
        )

        if first_position > 0:

            previous_close = closes.iloc[
                first_position - 1
            ]

            weekly_perf = (
                week_closes.iloc[-1] /
                previous_close - 1
            ) * 100

            row_data["Semaine"] = (
                f"{weekly_perf:+.2f}%"
            )

        price_rows.append(row_data)

    if price_rows:

        prices_df = pd.DataFrame(price_rows)

        st.dataframe(
            prices_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.warning(
            "Aucun cours disponible pour cette semaine."
        )


st.divider()


# ============================================================
# ANALYSE PAR VALEUR
# ============================================================

st.subheader("Commentaire par valeur")

if weekly_news is None:

    st.info(
        "Importe d'abord le fichier des sources de la semaine."
    )

else:

    available_tickers = (
        weekly_news["ticker"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_ticker = st.selectbox(
        "Valeur",
        available_tickers
    )

    company_config = config[
        config["ticker"] == selected_ticker
    ]

    if not company_config.empty:

        company_name = company_config.iloc[0]["name"]
        weight = company_config.iloc[0]["weight"]

        st.markdown(
            f"### {company_name}"
        )

        info1, info2, info3 = st.columns(3)

        with info1:
            st.caption("Ticker")
            st.write(selected_ticker)

        with info2:
            st.caption("Poids dans le fonds")
            st.write(f"{weight} %")

        company_news = weekly_news[
            weekly_news["ticker"] ==
            selected_ticker
        ]

        with info3:
            st.caption("Sources")
            st.write(
                len(company_news)
            )

        with st.expander(
            "Sources utilisées"
        ):

            for _, article in company_news.iterrows():

                st.markdown(
                    f"**{article['title']}**"
                )

                st.write(article["url"])

        if st.button(
            "Générer le commentaire",
            type="primary"
        ):

            article_contents = []

            unreadable = []

            for _, article in company_news.iterrows():

                text = extract_article_text(
                    article["url"]
                )

                if text:

                    article_contents.append(
                        f"""
TITRE : {article['title']}

CONTENU :
{text}
"""
                    )

                else:

                    unreadable.append(
                        article["title"]
                    )

            if not article_contents:

                st.error(
                    "Aucune source exploitable pour cette valeur."
                )

            else:

                result = get_stock_data(
                    company_config.iloc[0][
                        "yfinance_ticker"
                    ],
                    monday,
                    friday
                )

                if result is None:

                    st.error(
                        "Impossible de récupérer les cours."
                    )

                else:

                    closes, week_closes = result

                    price_text = []

                    for dt, close in week_closes.items():

                        position = closes.index.get_loc(dt)

                        variation = None

                        if position > 0:

                            previous_close = closes.iloc[
                                position - 1
                            ]

                            variation = (
                                close /
                                previous_close - 1
                            ) * 100

                        if variation is not None:

                            price_text.append(
                                f"{dt.strftime('%d/%m/%Y')} : "
                                f"{float(close):.2f} "
                                f"({variation:+.2f} %)"
                            )

                    first_position = closes.index.get_loc(
                        week_closes.index[0]
                    )

                    if first_position > 0:

                        previous_close = closes.iloc[
                            first_position - 1
                        ]

                        weekly_perf = (
                            week_closes.iloc[-1] /
                            previous_close - 1
                        ) * 100

                    else:

                        weekly_perf = 0

                    prompt = f"""
Tu es analyste au sein d'une société de gestion d'actifs.

Rédige le commentaire hebdomadaire de la valeur suivante.

VALEUR
{company_name}

TICKER
{selected_ticker}

POIDS DANS LE FONDS
{weight} %

COURS ET VARIATIONS
{chr(10).join(price_text)}

PERFORMANCE HEBDOMADAIRE
{weekly_perf:+.2f} %

INFORMATIONS DISPONIBLES
{chr(10).join(article_contents)}

Rédige un seul paragraphe en français de 4 à 6 phrases.

Contraintes impératives :

- Commence directement par le fait marquant de la semaine.
- Cite les chiffres précis utiles présents dans les informations.
- Relie explicitement les événements au mouvement du titre.
- Si le comportement boursier paraît contradictoire avec
  l'actualité, indique-le.
- Termine par l'implication pour la position dans le fonds :
  risque, catalyseur ou point de vigilance.
- Ton factuel, concis et professionnel.
- Ne parle jamais des articles, des sources ou de la presse.
- N'invente aucune information ou aucun chiffre.
"""

                    with st.spinner(
                        f"Analyse de {company_name}..."
                    ):

                        comment = call_mistral(
                            prompt,
                            MISTRAL_API_KEY
                        )

                    st.session_state[
                        f"comment_{selected_ticker}"
                    ] = comment

                    if unreadable:

                        st.warning(
                            f"{len(unreadable)} source(s) "
                            "n'ont pas pu être lues."
                        )


        comment_key = (
            f"comment_{selected_ticker}"
        )

        if comment_key in st.session_state:

            st.markdown("#### Commentaire")

            edited_comment = st.text_area(
                "Le commentaire peut être modifié directement",
                value=st.session_state[
                    comment_key
                ],
                height=200,
                key=f"editor_{selected_ticker}"
            )

            if st.button(
                "Sauvegarder la modification"
            ):

                st.session_state[
                    comment_key
                ] = edited_comment

                st.success(
                    "Commentaire sauvegardé."
                )


st.divider()

st.caption(
    "Weekly Fund Monitor"
)
