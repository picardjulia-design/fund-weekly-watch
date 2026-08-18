import streamlit as st
import pandas as pd
import yfinance as yf
import json

from datetime import date, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup


# ------------------------------------------------------------
# PAGE
# ------------------------------------------------------------

st.set_page_config(
    page_title="Weekly Fund Monitor",
    page_icon="📊",
    layout="wide"
)
st.markdown("""
<style>

/* =========================================================
   PAGE
   ========================================================= */

.stApp {
    background: #FFFFFF;
}

.block-container {
    max-width: 1380px;
    padding-top: 3rem;
    padding-bottom: 5rem;
    padding-left: 3.5rem;
    padding-right: 3.5rem;
}


/* =========================================================
   TYPOGRAPHIE
   ========================================================= */

html, body, [class*="css"] {
    font-family: Arial, Helvetica, sans-serif;
}

h1 {
    color: #0F2D4A;
    font-size: 3rem !important;
    line-height: 1.08 !important;
    font-weight: 500 !important;
    letter-spacing: -0.035em !important;
    margin-bottom: 0.6rem !important;
}

h2 {
    color: #0F2D4A;
    font-size: 1.65rem !important;
    line-height: 1.2 !important;
    font-weight: 500 !important;
    letter-spacing: -0.015em;
    margin-top: 2.8rem !important;
    margin-bottom: 1.2rem !important;
}

h3 {
    color: #0F2D4A;
    font-size: 1.15rem !important;
    font-weight: 600 !important;
}

p {
    color: #34393D;
    line-height: 1.55;
}

[data-testid="stCaptionContainer"] {
    color: #6F757B;
    font-size: 0.95rem;
}


/* =========================================================
   SEPARATEURS
   ========================================================= */

hr {
    border: 0;
    border-top: 1px solid #DADDE0;
    margin-top: 2.8rem;
    margin-bottom: 2.8rem;
}


/* =========================================================
   BOUTONS
   ========================================================= */

.stButton > button {
    background-color: #0F2D4A;
    color: #FFFFFF;
    border: 1px solid #0F2D4A;
    border-radius: 0px;
    min-height: 42px;
    padding: 0.55rem 1.3rem;
    font-size: 0.95rem;
    font-weight: 500;
    transition: all 0.15s ease;
}

.stButton > button:hover {
    background-color: #FFFFFF;
    color: #0F2D4A;
    border: 1px solid #0F2D4A;
}


/* =========================================================
   INPUTS
   ========================================================= */

[data-baseweb="select"] > div,
[data-testid="stDateInput"] input,
textarea,
input {
    background: #FFFFFF !important;
    border: 1px solid #C9CDD1 !important;
    border-radius: 0px !important;
    box-shadow: none !important;
}

[data-baseweb="select"] > div:focus-within,
[data-testid="stDateInput"] input:focus,
textarea:focus,
input:focus {
    border-color: #0F2D4A !important;
}


/* =========================================================
   UPLOAD
   ========================================================= */

[data-testid="stFileUploaderDropzone"] {
    background: #F7F8F9;
    border: 1px solid #D8DADD;
    border-radius: 0px;
    padding: 1.2rem;
}

[data-testid="stFileUploaderDropzone"] button {
    border-radius: 0px;
}


/* =========================================================
   TABLEAUX
   ========================================================= */

[data-testid="stDataFrame"] {
    border-top: 2px solid #0F2D4A;
    border-bottom: 1px solid #D8DADD;
    background: #FFFFFF;
}

[data-testid="stDataFrame"] * {
    font-size: 0.92rem;
}


/* =========================================================
   METRICS
   ========================================================= */

[data-testid="stMetric"] {
    background: #FFFFFF;
    padding: 0;
    border: none;
}

[data-testid="stMetricLabel"] {
    color: #72777C;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

[data-testid="stMetricValue"] {
    color: #0F2D4A;
    font-size: 1.5rem;
    font-weight: 500;
}


/* =========================================================
   EXPANDERS
   ========================================================= */

[data-testid="stExpander"] {
    background: #FFFFFF;
    border: none;
    border-top: 1px solid #D8DADD;
    border-bottom: 1px solid #D8DADD;
    border-radius: 0px;
}


/* =========================================================
   ALERTES
   ========================================================= */

[data-testid="stAlert"] {
    border-radius: 0px;
    border-left-width: 3px;
}


/* =========================================================
   TEXT AREA
   ========================================================= */

textarea {
    min-height: 180px !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
}


/* =========================================================
   HEADER STREAMLIT
   ========================================================= */

[data-testid="stHeader"] {
    background: rgba(255, 255, 255, 0.96);
    border-bottom: 1px solid #ECEDEF;
}

</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# MISTRAL KEY
# ------------------------------------------------------------

try:
    MISTRAL_API_KEY = st.secrets["MISTRAL_API_KEY"]
except Exception:
    MISTRAL_API_KEY = st.sidebar.text_input(
        "Clé API Mistral",
        type="password"
    )


# ------------------------------------------------------------
# FUNCTIONS
# ------------------------------------------------------------

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


def build_price_table(config, monday, friday):
    rows = []

    day_names = {
        0: "Lun.",
        1: "Mar.",
        2: "Mer.",
        3: "Jeu.",
        4: "Ven."
    }

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

        for dt, close in week_closes.items():
            position = closes.index.get_loc(dt)

            variation = None

            if position > 0:
                previous_close = closes.iloc[position - 1]
                variation = (
                    close / previous_close - 1
                ) * 100

            day = day_names.get(
                dt.weekday(),
                dt.strftime("%d/%m")
            )

            row_data[day] = round(float(close), 2)

            if variation is not None:
                row_data[f"{day} %"] = f"{variation:+.2f}%"

        first_position = closes.index.get_loc(
            week_closes.index[0]
        )

        if first_position > 0:
            previous_close = closes.iloc[first_position - 1]

            weekly_perf = (
                week_closes.iloc[-1] /
                previous_close - 1
            ) * 100

            row_data["Semaine"] = f"{weekly_perf:+.2f}%"

        rows.append(row_data)

    return pd.DataFrame(rows)


# ------------------------------------------------------------
# DATA
# ------------------------------------------------------------

config = pd.read_csv("config.csv")


# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------

st.title("Weekly Fund Monitor")
st.caption(
    "Suivi hebdomadaire des valeurs du fonds"
)

st.divider()


# ------------------------------------------------------------
# WEEK
# ------------------------------------------------------------

st.subheader("1. Semaine")

selected_date = st.date_input(
    "Choisir une date comprise dans la semaine",
    value=date.today()
)

monday = selected_date - timedelta(
    days=selected_date.weekday()
)

friday = monday + timedelta(days=4)

st.write(
    f"**Du {monday.strftime('%d/%m/%Y')} "
    f"au {friday.strftime('%d/%m/%Y')}**"
)

st.divider()


# ------------------------------------------------------------
# SOURCES
# ------------------------------------------------------------

st.subheader("2. Sources")

uploaded_file = st.file_uploader(
    "Importer le fichier CSV de la semaine",
    type=["csv"]
)

weekly_news = None

if uploaded_file is not None:
    try:
        weekly_news = pd.read_csv(
            uploaded_file,
            sep=";"
        )

        required_columns = {
            "ticker",
            "title",
            "url"
        }

        if not required_columns.issubset(
            set(weekly_news.columns)
        ):
            st.error(
                "Le CSV doit contenir les colonnes : "
                "ticker, title, url"
            )
            st.stop()

        weekly_news = weekly_news.dropna(
            subset=["ticker", "url"]
        )

        st.success(
            f"{len(weekly_news)} source(s) importée(s)"
        )

        with st.expander(
            "Voir les sources importées"
        ):
            st.dataframe(
                weekly_news,
                use_container_width=True,
                hide_index=True
            )

    except Exception as e:
        st.error(
            f"Erreur lors de la lecture du CSV : {e}"
        )

st.divider()


# ------------------------------------------------------------
# PRICES
# ------------------------------------------------------------

st.subheader("3. Cours et performances")

if st.button("Récupérer les cours"):
    prices_df = build_price_table(
        config,
        monday,
        friday
    )

    if prices_df.empty:
        st.warning(
            "Aucun cours disponible pour cette semaine."
        )
    else:
        st.session_state["prices_df"] = prices_df

if "prices_df" in st.session_state:
    st.dataframe(
        st.session_state["prices_df"],
        use_container_width=True,
        hide_index=True
    )

st.divider()


# ------------------------------------------------------------
# COMMENT
# ------------------------------------------------------------

st.subheader("4. Commentaire par valeur")

if weekly_news is None:
    st.info(
        "Importe d'abord le fichier CSV de la semaine."
    )

else:
    available_tickers = (
        weekly_news["ticker"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_ticker = st.selectbox(
        "Valeur à analyser",
        available_tickers
    )

    company_config = config[
        config["ticker"] == selected_ticker
    ]

    if company_config.empty:
        st.error(
            "Cette valeur n'existe pas dans config.csv."
        )

    else:
        company_name = company_config.iloc[0]["name"]
        weight = company_config.iloc[0]["weight"]
        yf_ticker = company_config.iloc[0][
            "yfinance_ticker"
        ]

        company_news = weekly_news[
            weekly_news["ticker"] == selected_ticker
        ]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Valeur",
                company_name
            )

        with col2:
            st.metric(
                "Poids",
                f"{weight}%"
            )

        with col3:
            st.metric(
                "Sources",
                len(company_news)
            )

        with st.expander(
            "Voir les sources de cette valeur"
        ):
            for _, article in company_news.iterrows():
                st.markdown(
                    f"**{article['title']}**"
                )
                st.write(article["url"])

        if st.button(
            "Générer / régénérer le commentaire"
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
TITRE :
{article['title']}

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
                    "Aucune source n'a pu être lue."
                )

            else:
                result = get_stock_data(
                    yf_ticker,
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
                                f"({variation:+.2f}%)"
                            )

                    first_position = closes.index.get_loc(
                        week_closes.index[0]
                    )

                    weekly_perf = 0

                    if first_position > 0:
                        previous_close = closes.iloc[
                            first_position - 1
                        ]

                        weekly_perf = (
                            week_closes.iloc[-1] /
                            previous_close - 1
                        ) * 100

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

Contraintes :
- commence directement par le fait marquant de la semaine ;
- cite les chiffres précis utiles ;
- relie les événements au mouvement du cours ;
- si le mouvement du titre semble contradictoire avec l'actualité,
  indique-le explicitement ;
- termine par l'implication pour la position dans le fonds :
  risque, catalyseur ou point de vigilance ;
- ton factuel, concis et professionnel ;
- ne mentionne jamais les articles, la presse ou les sources ;
- n'invente aucune information.
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

        comment_key = f"comment_{selected_ticker}"

        if comment_key in st.session_state:
            edited_comment = st.text_area(
                "Commentaire",
                value=st.session_state[
                    comment_key
                ],
                height=220,
                key=f"editor_{selected_ticker}"
            )

            if st.button(
                "Sauvegarder le commentaire"
            ):
                st.session_state[
                    comment_key
                ] = edited_comment

                st.success(
                    "Commentaire sauvegardé."
                )
