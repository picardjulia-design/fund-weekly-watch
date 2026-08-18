import streamlit as st
import pandas as pd
import yfinance as yf
import json
import re
import base64

from pathlib import Path
from datetime import date, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="CPR AM | Weekly Fund Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# COULEURS CPR
# ============================================================

NAVY = "#001C4B"
NAVY_2 = "#0A2A63"
CYAN = "#009EE0"
CYAN_D = "#0082B8"
BLUE_LIGHT = "#D6EAF7"

GRAY = "#F5F5F5"
LINE = "#E4EBF4"

POS = "#1F9D57"
NEG = "#D0432B"


# ============================================================
# LOGO
# ============================================================

def get_logo_data_uri():
    possible_files = [
        "cpram-logo.jpg",
        "cpram-logo.png",
        "logo.jpg",
        "logo.png"
    ]

    for filename in possible_files:
        path = Path(filename)

        if path.exists():
            mime = (
                "image/png"
                if path.suffix.lower() == ".png"
                else "image/jpeg"
            )

            encoded = base64.b64encode(
                path.read_bytes()
            ).decode()

            return f"data:{mime};base64,{encoded}"

    return None


LOGO_URI = get_logo_data_uri()


# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
<style>

:root {{
    --cyan: {CYAN};
    --cyan-dark: {CYAN_D};
    --navy: {NAVY};
    --navy2: {NAVY_2};
    --blue-light: {BLUE_LIGHT};
    --gray: {GRAY};
    --line: {LINE};
    --positive: {POS};
    --negative: {NEG};
}}


/* ---------------------------------------------------------
   STREAMLIT
--------------------------------------------------------- */

.stApp {{
    background: #FFFFFF;
    color: var(--navy);
}}

.block-container {{
    max-width: 1420px;
    padding-top: 1rem;
    padding-bottom: 5rem;
}}

[data-testid="stHeader"] {{
    background: transparent;
}}

#MainMenu {{
    visibility: hidden;
}}

footer {{
    visibility: hidden;
}}


/* ---------------------------------------------------------
   TYPO
--------------------------------------------------------- */

html,
body,
[class*="css"] {{
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Roboto,
        Helvetica,
        Arial,
        sans-serif;
}}

h1, h2, h3, h4 {{
    color: var(--navy) !important;
}}

h2 {{
    font-size: 1.7rem !important;
    letter-spacing: -0.02em;
}}

h3 {{
    font-size: 1.15rem !important;
}}

p {{
    line-height: 1.55;
}}


/* ---------------------------------------------------------
   HERO
--------------------------------------------------------- */

.cpr-top {{
    display: flex;
    align-items: center;
    gap: 18px;

    background: rgba(0, 28, 75, 0.98);

    margin-left: calc(-50vw + 50%);
    margin-right: calc(-50vw + 50%);
    margin-top: -1rem;

    padding:
        13px
        max(26px, calc((100vw - 1360px) / 2));

    border-bottom: 1px solid rgba(255,255,255,.08);
}}

.cpr-logo-box {{
    background: #FFFFFF;
    border-radius: 7px;
    padding: 7px 12px;
    display: flex;
    align-items: center;
}}

.cpr-logo-box img {{
    height: 30px;
    display: block;
}}

.cpr-brand-fallback {{
    font-weight: 800;
    color: var(--navy);
    letter-spacing: -.02em;
}}

.internal-badge {{
    margin-left: auto;

    font-size: 10px;
    letter-spacing: .09em;
    text-transform: uppercase;
    font-weight: 800;

    color: var(--navy);
    background: var(--cyan);

    padding: 6px 10px;
    border-radius: 6px;
}}


.cpr-hero {{
    position: relative;
    overflow: hidden;

    margin-left: calc(-50vw + 50%);
    margin-right: calc(-50vw + 50%);

    padding:
        50px
        max(26px, calc((100vw - 1360px) / 2))
        44px;

    color: #EAF1FB;

    background:
        radial-gradient(
            850px 420px at 82% -20%,
            rgba(0,158,224,.30),
            transparent 60%
        ),
        radial-gradient(
            650px 450px at 0% 120%,
            rgba(0,158,224,.12),
            transparent 55%
        ),
        linear-gradient(
            180deg,
            var(--navy),
            #02123A
        );

    border-bottom: 3px solid var(--cyan);
}}


.eyebrow {{
    display: flex;
    align-items: center;
    gap: 9px;

    font-size: 11px;
    letter-spacing: .16em;
    text-transform: uppercase;
    font-weight: 800;

    color: var(--cyan);
}}

.eyebrow::before {{
    content: "";
    width: 24px;
    height: 2px;

    background: var(--cyan);
    border-radius: 2px;
}}


.cpr-hero h1 {{
    color: #FFFFFF !important;

    font-size: clamp(30px, 4vw, 46px) !important;
    line-height: 1.05 !important;

    max-width: 850px;
    margin-top: 14px !important;
    margin-bottom: 0 !important;

    letter-spacing: -.035em;
}}


.cpr-hero .lead {{
    color: #BCD0EA;

    font-size: 16px;
    max-width: 850px;

    margin-top: 15px;
}}


.hero-meta {{
    margin-top: 18px;

    display: flex;
    flex-wrap: wrap;
    gap: 9px 22px;

    font-size: 12px;
    color: #8497B4;
}}

.hero-meta b {{
    color: #DCE8F7;
}}


/* ---------------------------------------------------------
   KPI HERO
--------------------------------------------------------- */

.hero-kpis {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);

    gap: 13px;
    margin-top: 28px;
}}

.hero-kpi {{
    background: rgba(255,255,255,.055);
    border: 1px solid rgba(255,255,255,.12);

    border-radius: 13px;

    padding: 15px 16px;
}}

.hero-kpi-label {{
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: .07em;

    color: #8497B4;
}}

.hero-kpi-value {{
    font-size: 24px;
    line-height: 1.15;

    font-weight: 800;
    letter-spacing: -.03em;

    color: #FFFFFF;

    margin-top: 6px;
}}

.hero-kpi-sub {{
    font-size: 11px;
    color: #9FB6D4;

    margin-top: 4px;
}}


@media(max-width: 800px) {{
    .hero-kpis {{
        grid-template-columns: repeat(2, 1fr);
    }}
}}


/* ---------------------------------------------------------
   SECTIONS
--------------------------------------------------------- */

.section-eyebrow {{
    display: flex;
    align-items: center;
    gap: 8px;

    margin-bottom: 7px;

    color: var(--cyan-dark);

    font-size: 11px;
    font-weight: 800;
    letter-spacing: .12em;
    text-transform: uppercase;
}}

.section-eyebrow::before {{
    content: "";
    width: 22px;
    height: 2px;
    background: var(--cyan);
}}


.section-description {{
    color: #5B6B85;

    max-width: 850px;
    font-size: 14px;

    margin-top: -5px;
    margin-bottom: 20px;
}}


/* ---------------------------------------------------------
   PANELS
--------------------------------------------------------- */

.cpr-panel {{
    background: #FFFFFF;

    border: 1px solid var(--line);
    border-radius: 15px;

    padding: 21px;

    box-shadow:
        0 10px 28px rgba(0,28,75,.07);
}}


/* ---------------------------------------------------------
   TABS
--------------------------------------------------------- */

.stTabs [data-baseweb="tab-list"] {{
    gap: 8px;

    border-bottom: 1px solid var(--line);

    margin-top: 18px;
}}

.stTabs [data-baseweb="tab"] {{
    color: #5B6B85;

    height: 48px;

    padding-left: 18px;
    padding-right: 18px;

    font-size: 13px;
    font-weight: 650;

    border-radius: 8px 8px 0 0;
}}

.stTabs [aria-selected="true"] {{
    color: var(--navy) !important;
    background: var(--blue-light) !important;
}}


/* ---------------------------------------------------------
   BUTTONS
--------------------------------------------------------- */

.stButton > button {{
    background: var(--navy) !important;

    border: 1px solid var(--navy) !important;
    border-radius: 8px !important;

    min-height: 42px;

    padding-left: 17px;
    padding-right: 17px;

    box-shadow: none !important;
}}

.stButton > button,
.stButton > button p,
.stButton > button span,
.stButton > button div {{
    color: #FFFFFF !important;
    font-weight: 650 !important;
}}

.stButton > button:hover {{
    background: var(--cyan) !important;
    border-color: var(--cyan) !important;
}}

.stButton > button:hover p,
.stButton > button:hover span,
.stButton > button:hover div {{
    color: #FFFFFF !important;
}}


/* ---------------------------------------------------------
   INPUTS
--------------------------------------------------------- */

[data-baseweb="select"] > div,
[data-testid="stDateInput"] input,
textarea,
input {{
    background: #FFFFFF !important;

    color: var(--navy) !important;

    border: 1px solid #D8E1EC !important;
    border-radius: 8px !important;

    box-shadow: none !important;
}}

textarea {{
    font-size: 14px !important;
    line-height: 1.6 !important;
}}


/* ---------------------------------------------------------
   UPLOAD
--------------------------------------------------------- */

[data-testid="stFileUploaderDropzone"] {{
    background: #F8FAFC !important;

    border: 1px dashed #B9C7D8 !important;
    border-radius: 11px !important;
}}

[data-testid="stFileUploaderDropzone"]:hover {{
    border-color: var(--cyan) !important;
}}


/* ---------------------------------------------------------
   METRICS
--------------------------------------------------------- */

[data-testid="stMetric"] {{
    background: #FFFFFF;

    border: 1px solid var(--line);
    border-radius: 12px;

    padding: 14px 16px;

    box-shadow:
        0 6px 18px rgba(0,28,75,.05);
}}

[data-testid="stMetricLabel"] {{
    color: #8497B4 !important;

    text-transform: uppercase;
    letter-spacing: .06em;

    font-size: 10px !important;
    font-weight: 800;
}}

[data-testid="stMetricValue"] {{
    color: var(--navy) !important;

    font-size: 22px !important;
    font-weight: 800 !important;
}}


/* ---------------------------------------------------------
   EXPANDERS
--------------------------------------------------------- */

[data-testid="stExpander"] {{
    background: #FFFFFF;

    border: 1px solid var(--line) !important;
    border-radius: 11px !important;

    box-shadow: none;
}}


/* ---------------------------------------------------------
   ALERTS
--------------------------------------------------------- */

[data-testid="stAlert"] {{
    border-radius: 10px !important;
}}


/* ---------------------------------------------------------
   DIVIDERS
--------------------------------------------------------- */

hr {{
    border: 0;
    border-top: 1px solid var(--line);

    margin: 30px 0;
}}


/* ---------------------------------------------------------
   COMMENT BOX
--------------------------------------------------------- */

.comment-head {{
    background:
        linear-gradient(
            90deg,
            var(--navy),
            var(--navy2)
        );

    color: #FFFFFF;

    border-radius: 12px 12px 0 0;

    padding: 14px 17px;
}}

.comment-head .small {{
    color: #8ECDE9;

    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: .09em;
    font-weight: 800;
}}

.comment-head .name {{
    color: #FFFFFF;

    font-size: 18px;
    font-weight: 750;

    margin-top: 3px;
}}


/* ---------------------------------------------------------
   SMALL BADGES
--------------------------------------------------------- */

.source-badge {{
    display: inline-flex;

    background: #E2F4FC;
    color: var(--cyan-dark);

    border-radius: 6px;

    padding: 4px 8px;

    font-size: 10px;
    font-weight: 800;

    text-transform: uppercase;
    letter-spacing: .04em;
}}


/* ---------------------------------------------------------
   SOURCES
--------------------------------------------------------- */

.source-item {{
    padding: 13px 0;

    border-bottom: 1px solid var(--line);
}}

.source-item:last-child {{
    border-bottom: none;
}}

.source-title {{
    color: var(--navy);

    font-size: 13px;
    font-weight: 700;
}}

.source-url {{
    margin-top: 3px;

    color: var(--cyan-dark);

    font-size: 11px;

    overflow-wrap: anywhere;
}}


/* ---------------------------------------------------------
   FOOTER
--------------------------------------------------------- */

.cpr-footer {{
    margin-left: calc(-50vw + 50%);
    margin-right: calc(-50vw + 50%);

    margin-top: 70px;

    background: var(--navy);
    border-top: 3px solid var(--cyan);

    color: #9FB3CF;

    padding:
        34px
        max(26px, calc((100vw - 1360px) / 2));

    font-size: 11px;
    line-height: 1.6;
}}

.cpr-footer b {{
    color: #FFFFFF;
}}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# MISTRAL
# ============================================================

try:
    MISTRAL_API_KEY = st.secrets["MISTRAL_API_KEY"]

except Exception:
    MISTRAL_API_KEY = st.sidebar.text_input(
        "Clé API Mistral",
        type="password"
    )


# ============================================================
# HELPERS
# ============================================================

def clean_comment(text):
    if not text:
        return ""

    text = text.replace("**", "")
    text = text.replace("__", "")

    text = re.sub(
        r"^#{1,6}\s*",
        "",
        text,
        flags=re.MULTILINE
    )

    text = re.sub(
        r"^\s*[-•]\s+",
        "",
        text,
        flags=re.MULTILINE
    )

    return text.strip()


def extract_article_text(url):
    try:
        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "Chrome/120 Safari/537.36"
                )
            }
        )

        with urlopen(
            request,
            timeout=15
        ) as response:
            html = response.read()

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

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
            p.get_text(
                " ",
                strip=True
            )
            for p in paragraphs
            if len(
                p.get_text(
                    " ",
                    strip=True
                )
            ) > 40
        )

        if len(text) < 300:
            text = soup.get_text(
                " ",
                strip=True
            )

        if len(text) < 300:
            return None

        return text[:12000]

    except Exception:
        return None


def call_mistral(prompt, api_key):
    url = (
        "https://api.mistral.ai/"
        "v1/chat/completions"
    )

    payload = {
        "model": "mistral-small-latest",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.15
    }

    request = Request(
        url,
        data=json.dumps(
            payload
        ).encode("utf-8"),
        headers={
            "Authorization":
                f"Bearer {api_key}",
            "Content-Type":
                "application/json"
        },
        method="POST"
    )

    try:
        with urlopen(
            request,
            timeout=60
        ) as response:

            result = json.loads(
                response
                .read()
                .decode("utf-8")
            )

        text = (
            result["choices"][0]
            ["message"]["content"]
        )

        return clean_comment(text)

    except HTTPError as e:
        return (
            f"Erreur API Mistral : "
            f"{e.code}"
        )

    except URLError:
        return (
            "Impossible de contacter "
            "Mistral."
        )

    except Exception as e:
        return f"Erreur : {e}"


def get_stock_data(
    yf_ticker,
    monday,
    friday
):
    data = yf.download(
        yf_ticker,
        start=monday - timedelta(days=7),
        end=friday + timedelta(days=3),
        progress=False,
        auto_adjust=False
    )

    if data.empty:
        return None

    closes = (
        data["Close"]
        .dropna()
    )

    if hasattr(
        closes,
        "columns"
    ):
        closes = closes.iloc[:, 0]

    closes = closes[
        closes.index.date
        <= friday
    ]

    week_closes = closes[
        (
            closes.index.date
            >= monday
        )
        &
        (
            closes.index.date
            <= friday
        )
    ]

    if week_closes.empty:
        return None

    return closes, week_closes


def build_price_table(
    config,
    monday,
    friday
):
    rows = []

    days = {
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

        entry = {
            "Valeur": row["name"],
            "Ticker": row["ticker"]
        }

        for dt, close in week_closes.items():

            position = closes.index.get_loc(dt)

            variation = None

            if position > 0:
                previous = closes.iloc[
                    position - 1
                ]

                variation = (
                    close / previous - 1
                ) * 100

            day = days.get(
                dt.weekday()
            )

            if day:
                entry[day] = round(
                    float(close),
                    2
                )

                if variation is not None:
                    entry[
                        f"{day} %"
                    ] = round(
                        float(variation),
                        2
                    )

        first_pos = closes.index.get_loc(
            week_closes.index[0]
        )

        if first_pos > 0:
            previous = closes.iloc[
                first_pos - 1
            ]

            weekly_perf = (
                week_closes.iloc[-1]
                / previous
                - 1
            ) * 100

            entry["Semaine"] = round(
                float(weekly_perf),
                2
            )

        rows.append(entry)

    return pd.DataFrame(rows)


def style_price_table(df):

    pct_columns = [
        col
        for col in df.columns
        if "%" in col
        or col == "Semaine"
    ]

    def color_value(value):
        try:
            value = float(value)

            if value > 0:
                return (
                    f"color: {POS}; "
                    "font-weight:700"
                )

            if value < 0:
                return (
                    f"color: {NEG}; "
                    "font-weight:700"
                )

        except Exception:
            pass

        return ""

    styled = (
        df.style
        .map(
            color_value,
            subset=pct_columns
        )
        .format(
            {
                col: "{:+.2f}%"
                for col in pct_columns
            },
            na_rep="—"
        )
    )

    return styled


# ============================================================
# CONFIG
# ============================================================

config = pd.read_csv(
    "config.csv"
)


# ============================================================
# WEEK
# ============================================================

today = date.today()

default_monday = (
    today
    - timedelta(
        days=today.weekday()
    )
)


# ============================================================
# TOP BAR
# ============================================================

if LOGO_URI:

    logo_html = (
        f'<img src="{LOGO_URI}" '
        f'alt="CPR Asset Management">'
    )

else:

    logo_html = (
        '<div class="cpr-brand-fallback">'
        'CPR ASSET MANAGEMENT'
        '</div>'
    )


st.markdown(
    f"""
<div class="cpr-top">

    <div class="cpr-logo-box">
        {logo_html}
    </div>

    <div class="internal-badge">
        Document de travail interne
    </div>

</div>
""",
    unsafe_allow_html=True
)


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
<div class="cpr-hero">

    <div class="eyebrow">
        Veille hebdomadaire
    </div>

    <h1>
        Fund Weekly Monitor
    </h1>

    <div class="lead">
        Suivi des performances, actualités et
        commentaires de gestion des principales
        valeurs du portefeuille.
    </div>

    <div class="hero-meta">

        <span>
            Source marchés :
            <b>Yahoo Finance</b>
        </span>

        <span>
            Synthèse :
            <b>Mistral AI</b>
        </span>

        <span>
            Contrôle des sources :
            <b>manuel</b>
        </span>

    </div>

</div>
""",
    unsafe_allow_html=True
)


# ============================================================
# CONTROL BAR
# ============================================================

st.write("")

control1, control2 = st.columns(
    [1, 2]
)

with control1:

    selected_date = st.date_input(
        "Semaine analysée",
        value=default_monday
    )


monday = (
    selected_date
    - timedelta(
        days=selected_date.weekday()
    )
)

friday = (
    monday
    + timedelta(days=4)
)


with control2:

    uploaded_file = st.file_uploader(
        "Sources de la semaine",
        type=["csv"]
    )


weekly_news = None


if uploaded_file is not None:

    try:
        weekly_news = pd.read_csv(
            uploaded_file,
            sep=";"
        )

        required = {
            "ticker",
            "title",
            "url"
        }

        if not required.issubset(
            weekly_news.columns
        ):

            st.error(
                "Le fichier doit contenir "
                "ticker, title et url."
            )

            weekly_news = None

        else:

            weekly_news = (
                weekly_news
                .dropna(
                    subset=[
                        "ticker",
                        "url"
                    ]
                )
            )

    except Exception as e:

        st.error(
            f"Impossible de lire "
            f"le CSV : {e}"
        )


# ============================================================
# HERO KPI DATA
# ============================================================

source_count = (
    len(weekly_news)
    if weekly_news is not None
    else 0
)

ticker_count = (
    weekly_news[
        "ticker"
    ].nunique()
    if weekly_news is not None
    else len(config)
)


date_label = (
    f"{monday.strftime('%d/%m')}"
    f" → "
    f"{friday.strftime('%d/%m/%Y')}"
)


st.markdown(
    f"""
<div class="hero-kpis">

    <div class="hero-kpi">
        <div class="hero-kpi-label">
            Semaine
        </div>
        <div class="hero-kpi-value"
             style="font-size:19px">
            {date_label}
        </div>
        <div class="hero-kpi-sub">
            semaine de marché analysée
        </div>
    </div>

    <div class="hero-kpi">
        <div class="hero-kpi-label">
            Valeurs
        </div>
        <div class="hero-kpi-value">
            {ticker_count}
        </div>
        <div class="hero-kpi-sub">
            titres suivis
        </div>
    </div>

    <div class="hero-kpi">
        <div class="hero-kpi-label">
            Sources
        </div>
        <div class="hero-kpi-value">
            {source_count}
        </div>
        <div class="hero-kpi-sub">
            articles importés
        </div>
    </div>

    <div class="hero-kpi">
        <div class="hero-kpi-label">
            Statut
        </div>
        <div class="hero-kpi-value"
             style="font-size:19px">
            {"Prêt" if weekly_news is not None else "En attente"}
        </div>
        <div class="hero-kpi-sub">
            génération des commentaires
        </div>
    </div>

</div>
""",
    unsafe_allow_html=True
)


# ============================================================
# TABS
# ============================================================

tab_overview, tab_analysis, tab_sources = st.tabs(
    [
        "Vue d'ensemble",
        "Analyse par valeur",
        "Sources"
    ]
)


# ============================================================
# TAB 1 — OVERVIEW
# ============================================================

with tab_overview:

    st.write("")

    st.markdown(
        """
<div class="section-eyebrow">
    Marchés
</div>
""",
        unsafe_allow_html=True
    )

    st.subheader(
        "Performances de la semaine"
    )

    st.markdown(
        """
<div class="section-description">
Cours de clôture des séances de la semaine,
variations quotidiennes et performance cumulée.
</div>
""",
        unsafe_allow_html=True
    )


    if st.button(
        "Actualiser les cours",
        key="refresh_prices"
    ):

        with st.spinner(
            "Récupération des cours..."
        ):

            prices_df = build_price_table(
                config,
                monday,
                friday
            )

        st.session_state[
            "prices_df"
        ] = prices_df


    if "prices_df" in st.session_state:

        prices_df = st.session_state[
            "prices_df"
        ]

        if not prices_df.empty:

            perf_df = prices_df.dropna(
                subset=["Semaine"]
            )

            if not perf_df.empty:

                best = perf_df.loc[
                    perf_df[
                        "Semaine"
                    ].idxmax()
                ]

                worst = perf_df.loc[
                    perf_df[
                        "Semaine"
                    ].idxmin()
                ]

                average = (
                    perf_df[
                        "Semaine"
                    ].mean()
                )

                k1, k2, k3 = st.columns(3)

                with k1:
                    st.metric(
                        "Meilleure performance",
                        f"{best['Semaine']:+.2f}%",
                        best["Valeur"]
                    )

                with k2:
                    st.metric(
                        "Performance moyenne",
                        f"{average:+.2f}%"
                    )

                with k3:
                    st.metric(
                        "Plus faible performance",
                        f"{worst['Semaine']:+.2f}%",
                        worst["Valeur"]
                    )


            st.write("")

            st.dataframe(
                style_price_table(
                    prices_df
                ),
                use_container_width=True,
                hide_index=True,
                height=520
            )

        else:

            st.warning(
                "Aucune donnée de marché "
                "disponible."
            )

    else:

        st.info(
            "Clique sur « Actualiser les cours » "
            "pour charger les données de la semaine."
        )


# ============================================================
# TAB 2 — ANALYSIS
# ============================================================

with tab_analysis:

    st.write("")

    st.markdown(
        """
<div class="section-eyebrow">
    Commentaire de gestion
</div>
""",
        unsafe_allow_html=True
    )

    st.subheader(
        "Analyse par valeur"
    )


    if weekly_news is None:

        st.info(
            "Importe d'abord le CSV "
            "des sources de la semaine."
        )

    else:

        available_tickers = (
            weekly_news[
                "ticker"
            ]
            .dropna()
            .unique()
            .tolist()
        )


        selected_ticker = st.selectbox(
            "Valeur à analyser",
            available_tickers
        )


        company_config = config[
            config["ticker"]
            == selected_ticker
        ]


        if company_config.empty:

            st.error(
                "Cette valeur n'existe pas "
                "dans config.csv."
            )

        else:

            company_name = (
                company_config.iloc[0][
                    "name"
                ]
            )

            weight = (
                company_config.iloc[0][
                    "weight"
                ]
            )

            yf_ticker = (
                company_config.iloc[0][
                    "yfinance_ticker"
                ]
            )

            company_news = weekly_news[
                weekly_news["ticker"]
                == selected_ticker
            ]


            stock_result = get_stock_data(
                yf_ticker,
                monday,
                friday
            )


            weekly_perf = None

            if stock_result is not None:

                closes, week_closes = (
                    stock_result
                )

                first_pos = (
                    closes.index
                    .get_loc(
                        week_closes.index[0]
                    )
                )

                if first_pos > 0:

                    previous = closes.iloc[
                        first_pos - 1
                    ]

                    weekly_perf = (
                        week_closes.iloc[-1]
                        / previous
                        - 1
                    ) * 100


            perf_display = (
                f"{weekly_perf:+.2f}%"
                if weekly_perf
                is not None
                else "—"
            )


            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric(
                    "Valeur",
                    company_name
                )

            with c2:
                st.metric(
                    "Ticker",
                    selected_ticker
                )

            with c3:
                st.metric(
                    "Poids dans le fonds",
                    f"{weight}%"
                )

            with c4:
                st.metric(
                    "Performance semaine",
                    perf_display
                )


            st.write("")


            st.markdown(
                f"""
<div class="comment-head">

    <div class="small">
        Note hebdomadaire
    </div>

    <div class="name">
        {company_name}
    </div>

</div>
""",
                unsafe_allow_html=True
            )


            comment_key = (
                f"comment_"
                f"{selected_ticker}"
            )


            if comment_key not in (
                st.session_state
            ):

                st.session_state[
                    comment_key
                ] = ""


            edited_comment = st.text_area(
                "Commentaire",
                value=st.session_state[
                    comment_key
                ],
                height=230,
                key=(
                    f"editor_"
                    f"{selected_ticker}"
                ),
                label_visibility="collapsed"
            )


            button1, button2 = st.columns(
                [1, 1]
            )


            with button1:

                generate = st.button(
                    (
                        "Générer le commentaire"
                        if not st.session_state[
                            comment_key
                        ]
                        else
                        "Régénérer cette valeur"
                    ),
                    key=(
                        f"generate_"
                        f"{selected_ticker}"
                    )
                )


            with button2:

                if st.button(
                    "Sauvegarder les modifications",
                    key=(
                        f"save_"
                        f"{selected_ticker}"
                    )
                ):

                    st.session_state[
                        comment_key
                    ] = clean_comment(
                        edited_comment
                    )

                    st.success(
                        "Commentaire sauvegardé."
                    )


            if generate:

                article_contents = []
                unreadable = []


                for _, article in (
                    company_news.iterrows()
                ):

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
                        "Aucune des sources "
                        "de cette valeur n'a pu "
                        "être lue."
                    )

                else:

                    result = get_stock_data(
                        yf_ticker,
                        monday,
                        friday
                    )


                    if result is None:

                        st.error(
                            "Impossible de récupérer "
                            "les cours."
                        )

                    else:

                        closes, week_closes = (
                            result
                        )

                        price_text = []


                        for dt, close in (
                            week_closes.items()
                        ):

                            position = (
                                closes.index
                                .get_loc(dt)
                            )

                            variation = None


                            if position > 0:

                                previous = (
                                    closes.iloc[
                                        position - 1
                                    ]
                                )

                                variation = (
                                    close / previous
                                    - 1
                                ) * 100


                            if variation is not None:

                                price_text.append(
                                    (
                                        f"{dt.strftime('%d/%m/%Y')} : "
                                        f"{float(close):.2f} "
                                        f"({variation:+.2f} %)"
                                    )
                                )


                        first_pos = (
                            closes.index
                            .get_loc(
                                week_closes.index[0]
                            )
                        )


                        if first_pos > 0:

                            previous = (
                                closes.iloc[
                                    first_pos - 1
                                ]
                            )

                            weekly_perf_prompt = (
                                week_closes.iloc[-1]
                                / previous
                                - 1
                            ) * 100

                        else:

                            weekly_perf_prompt = 0


                        prompt = f"""
Tu es analyste au sein d'une société de gestion d'actifs.

Tu dois rédiger le commentaire hebdomadaire d'une valeur détenue dans un fonds thématique.

VALEUR
{company_name}

TICKER
{selected_ticker}

POIDS DANS LE FONDS
{weight} %

COURS DE LA SEMAINE
{chr(10).join(price_text)}

PERFORMANCE HEBDOMADAIRE
{weekly_perf_prompt:+.2f} %

INFORMATIONS DISPONIBLES
{chr(10).join(article_contents)}

Rédige un seul paragraphe en français de 4 à 6 phrases.

Contraintes impératives :

- Commence immédiatement par le fait marquant de la semaine.
- Utilise les chiffres précis réellement présents dans les informations fournies.
- Relie explicitement les nouvelles au mouvement du cours observé.
- Si le comportement du titre paraît contradictoire avec les nouvelles, indique-le clairement.
- Termine par le risque, le catalyseur ou le point de vigilance pertinent pour la position dans le fonds.
- Ton factuel, concis et professionnel de note de gestion.
- Ne mentionne jamais les articles, les sources ou la presse.
- N'invente aucune information ni aucun chiffre.
- N'utilise aucun Markdown.
- N'utilise aucun astérisque.
- N'utilise aucun titre.
- N'utilise aucune liste ou puce.
- Retourne uniquement le paragraphe final en texte brut.
"""


                        with st.spinner(
                            (
                                "Analyse de "
                                f"{company_name}..."
                            )
                        ):

                            comment = call_mistral(
                                prompt,
                                MISTRAL_API_KEY
                            )


                        st.session_state[
                            comment_key
                        ] = clean_comment(
                            comment
                        )


                        st.rerun()


                if unreadable:

                    st.warning(
                        (
                            f"{len(unreadable)} "
                            "source(s) n'ont pas "
                            "pu être lues."
                        )
                    )


            st.write("")


            with st.expander(
                "Sources utilisées"
            ):

                for _, article in (
                    company_news.iterrows()
                ):

                    st.markdown(
                        f"""
<div class="source-item">

    <div class="source-badge">
        Source
    </div>

    <div class="source-title">
        {article['title']}
    </div>

    <div class="source-url">
        {article['url']}
    </div>

</div>
""",
                        unsafe_allow_html=True
                    )


# ============================================================
# TAB 3 — SOURCES
# ============================================================

with tab_sources:

    st.write("")

    st.markdown(
        """
<div class="section-eyebrow">
    Contrôle des données
</div>
""",
        unsafe_allow_html=True
    )

    st.subheader(
        "Sources de la semaine"
    )


    if weekly_news is None:

        st.info(
            "Aucun fichier de sources "
            "n'a encore été importé."
        )

    else:

        st.markdown(
            f"""
<div class="section-description">
{len(weekly_news)} source(s) importée(s)
pour {weekly_news["ticker"].nunique()}
valeur(s). Les liens restent sous votre
contrôle et sont utilisés uniquement pour
la génération du commentaire.
</div>
""",
            unsafe_allow_html=True
        )

        st.dataframe(
            weekly_news,
            use_container_width=True,
            hide_index=True,
            height=520
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
<div class="cpr-footer">

    <b>CPR Asset Management · Document de travail interne</b>

    <br><br>

    Les données de marché sont utilisées à titre
    informatif dans le cadre de la préparation
    d'une veille interne. Les commentaires
    générés doivent faire l'objet d'une revue
    humaine avant toute utilisation.

</div>
""",
    unsafe_allow_html=True
)
