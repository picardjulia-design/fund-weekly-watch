"""
Veille hebdomadaire — CPR AM
Un seul fichier : app.py, fonds.json, requirements.txt suffisent.
Lancement : streamlit run app.py
"""

import datetime as dt
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st
import yfinance as yf

RACINE = Path(__file__).parent
CONFIG = RACINE / "fonds.json"
MODELE = "mistral-small-latest"

st.set_page_config(page_title="Veille hebdomadaire — CPR AM",
                   page_icon=None, layout="wide")


# ==========================================================================
# STYLE — direction editoriale, pas de composants Streamlit par defaut
# ==========================================================================

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>

:root {
  --nuit: #0E2745;
  --nuit-clair: #1C3E64;
  --accent: #A67C3D;
  --hausse: #0F6B4F;
  --baisse: #A3312A;
  --papier: #FBFAF7;
  --trait: #DDDAD1;
  --texte: #23262B;
  --gris: #7A7A72;
}

html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }

.stApp { background: var(--papier); }
.block-container { max-width: 1180px; padding-top: 0 !important; padding-bottom: 5rem; }

#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }

/* ---- Bandeau ---- */
.bandeau {
  background: var(--nuit);
  margin: 0 -100vw 2.6rem;
  padding: 1.9rem calc(100vw - 100% + 1rem) 1.7rem;
  display: flex;
  align-items: baseline;
  gap: 1rem;
  border-bottom: 3px solid var(--accent);
}
.bandeau .marque {
  font-family: 'Source Serif 4', serif;
  font-size: 1.5rem;
  color: #fff;
  letter-spacing: 0.02em;
}
.bandeau .sous {
  font-size: 0.78rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255,255,255,.6);
  border-left: 1px solid rgba(255,255,255,.25);
  padding-left: 1rem;
}

/* ---- Titres de section ---- */
h1, h2, h3 { font-family: 'Source Serif 4', serif !important; color: var(--nuit) !important; }
h1 { font-size: 2.1rem !important; font-weight: 400 !important; margin-bottom: 0.1rem !important; }
h2 {
  font-size: 1.02rem !important; font-weight: 600 !important;
  text-transform: uppercase; letter-spacing: 0.08em;
  font-family: 'Inter', sans-serif !important; color: var(--nuit) !important;
  border-bottom: 1px solid var(--trait); padding-bottom: 0.6rem;
  margin-top: 2.6rem !important; margin-bottom: 1.1rem !important;
}
.intro-desc { color: var(--gris); font-size: 0.95rem; max-width: 62ch; }

/* ---- Widgets generiques : angles droits, sobre ---- */
.stTextArea textarea, .stTextInput input, .stSelectbox [data-baseweb="select"] > div,
.stDateInput input, .stMultiSelect [data-baseweb="select"] > div {
  border-radius: 2px !important;
  border-color: var(--trait) !important;
  font-family: 'Inter', sans-serif !important;
  box-shadow: none !important;
}
.stTextArea textarea { font-family: 'IBM Plex Mono', 'SFMono-Regular', monospace !important; font-size: 0.86rem !important; }

.stButton > button {
  background: var(--nuit); color: #fff; border: none; border-radius: 2px;
  padding: 0.55rem 1.4rem; font-weight: 500; font-size: 0.88rem; letter-spacing: 0.02em;
}
.stButton > button:hover { background: var(--nuit-clair); color: #fff; }
.stButton > button:disabled { background: #C7CBD1; color: #fff; }

[data-testid="stMetricValue"] {
  font-family: 'Source Serif 4', serif !important; color: var(--nuit) !important; font-size: 1.7rem !important;
}
[data-testid="stMetricLabel"] {
  font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 0.07em; color: var(--gris) !important;
}

/* ---- Fiche valeur ---- */
.fiche {
  background: #fff; border: 1px solid var(--trait); margin-bottom: 1rem;
}
.fiche-tete {
  display: flex; align-items: baseline; gap: 0.9rem; flex-wrap: wrap;
  padding: 1rem 1.3rem; border-bottom: 1px solid var(--trait);
}
.fiche-nom { font-weight: 600; font-size: 0.98rem; color: var(--nuit); letter-spacing: 0.01em; }
.fiche-ticker {
  font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: var(--gris);
  background: var(--papier); padding: 2px 7px; border: 1px solid var(--trait);
}
.fiche-poids { font-size: 0.78rem; color: var(--gris); margin-left: auto; }
.fiche-perf { font-family: 'Source Serif 4', serif; font-size: 1.05rem; }

.hausse { color: var(--hausse); } .baisse { color: var(--baisse); } .neutre { color: var(--gris); }

.sources-titre {
  font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--gris); margin: 0.9rem 0 0.35rem; border-top: 1px dotted var(--trait); padding-top: 0.7rem;
}
.source-lien { font-size: 0.82rem; display: block; padding: 1px 0; color: var(--nuit-clair) !important; }

.avertissement { font-size: 0.82rem; color: var(--baisse); margin: 0.25rem 0; }

hr { border: none; border-top: 1px solid var(--trait); margin: 2rem 0; }

.pied { color: var(--gris); font-size: 0.78rem; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--trait); }

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="bandeau">
  <span class="marque">CPR AM</span>
  <span class="sous">Veille hebdomadaire</span>
</div>
""", unsafe_allow_html=True)


# ==========================================================================
# LECTURE / NORMALISATION
# ==========================================================================

SUFFIXES = {
    "XNAS": "", "XNYS": "", "XASE": "", "ARCX": "", "BATS": "",
    "NASDAQ": "", "NSDQ": "", "NYSE": "", "AMEX": "",
    "XKRX": ".KS", "XKOS": ".KQ", "KRX": ".KS", "KOSPI": ".KS", "KOSDAQ": ".KQ",
    "XPAR": ".PA", "EPA": ".PA", "XAMS": ".AS", "XBRU": ".BR", "XLIS": ".LS",
    "XLON": ".L", "LSE": ".L", "XETR": ".DE", "ETR": ".DE", "XSWX": ".SW",
    "XMIL": ".MI", "XMAD": ".MC", "XSTO": ".ST", "XCSE": ".CO",
    "XTAI": ".TW", "TPE": ".TW", "XTKS": ".T", "TSE": ".T",
    "XHKG": ".HK", "XSES": ".SI", "XTSE": ".TO", "XASX": ".AX",
}
MOTIF_URL = re.compile(r"https?://[^\s;\"'<>]+")


def normaliser_ticker(brut):
    t = brut.strip().strip('"').upper()
    if ":" not in t:
        return t
    place, code = t.split(":", 1)
    place, code = place.strip(), code.strip()
    return code + SUFFIXES.get(place, "")


def lire_liens_texte(texte):
    """{ticker: [url, ...]} depuis du texte colle. Tolere colonnes en trop."""
    liens, ignorees = {}, []
    for numero, brut in enumerate(texte.splitlines(), 1):
        ligne = brut.strip()
        if not ligne or ligne.startswith("#"):
            continue
        premier = re.split(r"[;,\t]", ligne, maxsplit=1)[0]
        ticker = normaliser_ticker(premier)
        if ticker in ("TICKER", ""):
            continue
        trouvees = MOTIF_URL.findall(ligne)
        if not trouvees:
            ignorees.append((numero, ticker))
            continue
        for url in trouvees:
            liens.setdefault(ticker, []).append(url.rstrip(".,"))
    return liens, ignorees


def lire_texte(chemin):
    donnees = Path(chemin).read_bytes()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return donnees.decode(enc)
        except UnicodeDecodeError:
            continue
    return donnees.decode("utf-8", errors="replace")


@st.cache_data(show_spinner=False)
def charger_config():
    return json.loads(lire_texte(CONFIG))


def devise_du_ticker(ticker):
    if ticker.endswith(".KS"): return "KRW"
    if ticker.endswith(".TW"): return "TWD"
    if ticker.endswith((".PA", ".AS", ".MI", ".MC", ".BR", ".LS")): return "EUR"
    return "USD"


def libelle_semaine(code):
    m = re.match(r"(\d{4})-S(\d{1,2})$", code)
    if not m:
        return code
    annee, num = int(m.group(1)), int(m.group(2))
    lundi = dt.date.fromisocalendar(annee, num, 1)
    return f"semaine du {lundi.strftime('%d/%m')}"


def semaine_courante():
    a, s, _ = dt.date.today().isocalendar()
    return f"{a}-S{s}"


# ==========================================================================
# COURS
# ==========================================================================

@st.cache_data(show_spinner=False, ttl=3600)
def charger_cours(ticker, code_semaine):
    if not ticker:
        return []
    annee, num = int(code_semaine[:4]), int(code_semaine.split("S")[1])
    fin = min(dt.date.fromisocalendar(annee, num, 5), dt.date.today())
    debut = fin - dt.timedelta(days=16)

    hist = yf.Ticker(ticker).history(
        start=debut.isoformat(), end=(fin + dt.timedelta(days=1)).isoformat(),
        auto_adjust=False)
    if hist.empty:
        return []

    hist = hist.tail(6)
    seances, precedent = [], None
    for date, ligne in hist.iterrows():
        cloture = float(ligne["Close"])
        variation = None if precedent is None else (cloture / precedent - 1) * 100
        seances.append({"date": date.strftime("%Y-%m-%d"), "dernier": round(cloture, 2),
                        "variation": None if variation is None else round(variation, 2)})
        precedent = cloture
    return seances[-5:]


def perf_semaine(seances):
    if len(seances) < 2:
        return None
    return round((seances[-1]["dernier"] / seances[0]["dernier"] - 1) * 100, 2)


# ==========================================================================
# EXTRACTION ARTICLE
# ==========================================================================

def extraire_article(url):
    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 Chrome/120 Safari/537.36"})
        with urlopen(req, timeout=15) as reponse:
            html = reponse.read()
    except (HTTPError, URLError, TimeoutError, Exception):
        return None

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        paragraphes = soup.find_all("p")
        texte = "\n".join(p.get_text(" ", strip=True) for p in paragraphes
                          if len(p.get_text(" ", strip=True)) > 40)
        if len(texte) < 300:
            texte = soup.get_text(" ", strip=True)
        titre_tag = soup.find("title")
        titre = titre_tag.get_text(strip=True) if titre_tag else url
    except Exception:
        return None

    if len(texte) < 250:
        return None
    return {"url": url, "titre": titre, "texte": texte[:12000]}


# ==========================================================================
# RESUME — Mistral en HTTP direct, pas de SDK
# ==========================================================================

SYSTEME = """Tu es analyste actions dans une societe de gestion francaise. Tu \
rediges la note hebdomadaire de suivi d'un fonds thematique."""

CONSIGNES = """Redige un seul paragraphe en francais de 4 a 6 phrases.

Contraintes imperatives :
- Commence directement par le fait marquant de la semaine, pas par une generalite.
- Cite les chiffres precis presents dans les informations (resultats, guidance,
  montants, pourcentages).
- Relie explicitement les evenements au mouvement du cours observe ; si le
  comportement boursier semble contradictoire avec l'actualite, signale-le.
- Termine par l'implication pour la position dans le fonds : risque, catalyseur
  a venir ou point de vigilance.
- Ton factuel, concis, registre professionnel de gestion d'actifs.
- Ne parle jamais des articles, sources ou de la presse ; restitue l'information
  directement.
- N'invente aucune information ni aucun chiffre absent des sources fournies."""


def appeler_mistral(prompt, cle):
    corps = json.dumps({
        "model": MODELE,
        "messages": [{"role": "system", "content": SYSTEME},
                    {"role": "user", "content": prompt}],
        "temperature": 0.25, "max_tokens": 650,
    }).encode("utf-8")
    req = Request("https://api.mistral.ai/v1/chat/completions", data=corps,
                 headers={"Authorization": f"Bearer {cle}",
                          "Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=90) as reponse:
            donnees = json.loads(reponse.read().decode("utf-8"))
        return donnees["choices"][0]["message"]["content"].strip(), None
    except HTTPError as e:
        if e.code == 401:
            return None, "cle API refusee (401)"
        if e.code == 429:
            return None, "limite de debit atteinte (429), reessaie dans une minute"
        return None, f"erreur HTTP {e.code}"
    except Exception as e:
        return None, str(e)


def construire_prompt(nom, fonds_nom, poids, seances, articles):
    if seances:
        lignes = [f"  {s['date']} : {s['dernier']}"
                 + (f" ({s['variation']:+.2f} %)" if s["variation"] is not None else "")
                 for s in seances]
        bloc_cours = "\n".join(lignes)
        perf = perf_semaine(seances)
        if perf is not None:
            bloc_cours += f"\n  Performance sur la periode : {perf:+.2f} %"
    else:
        bloc_cours = "  Cours non disponibles."

    bloc_articles = "\n\n".join(
        f"--- Source {i} ---\n{a['titre']}\n\n{a['texte']}"
        for i, a in enumerate(articles, 1))

    return f"""Valeur : {nom}
Fonds : {fonds_nom}
Poids dans le fonds : {poids} %

Cours de cloture de la semaine :
{bloc_cours}

Informations disponibles :
{bloc_articles}

{CONSIGNES}"""


# ==========================================================================
# ETAT
# ==========================================================================

if "resultats" not in st.session_state:
    st.session_state.resultats = {}   # {code_semaine: {id_fonds: {ticker: {...}}}}

config = charger_config()


with st.sidebar:
    st.markdown("**Configuration**")

    try:
        cle_api = st.secrets["MISTRAL_API_KEY"]
        st.caption("Cle API — secrets Streamlit")
    except Exception:
        cle_api = st.text_input("Cle API Mistral", type="password",
                                help="console.mistral.ai")

    st.divider()
    defaut = semaine_courante()
    code_semaine = st.text_input("Semaine (AAAA-Sxx)", value=defaut)
    id_fonds = st.selectbox("Fonds", list(config), format_func=lambda k: config[k]["nom"])

    st.divider()
    st.download_button(
        "Telecharger la semaine (JSON)",
        json.dumps(st.session_state.resultats.get(code_semaine, {}).get(id_fonds, {}),
                   ensure_ascii=False, indent=1),
        file_name=f"{code_semaine}_{id_fonds}.json", mime="application/json",
        use_container_width=True,
        disabled=id_fonds not in st.session_state.resultats.get(code_semaine, {}))

fonds = config[id_fonds]

st.markdown(f"# {fonds['nom']}")
st.markdown(f'<p class="intro-desc">{fonds.get("description","")} — {libelle_semaine(code_semaine)}</p>',
           unsafe_allow_html=True)


# ==========================================================================
# SAISIE DES LIENS
# ==========================================================================

st.markdown("## Sources de la semaine")
st.caption("Un lien par ligne, precede du ticker. Colle directement depuis Excel : "
          "les colonnes intermediaires sont ignorees.")

texte_liens = st.text_area("liens", height=200, label_visibility="collapsed",
    placeholder="NVDA;https://www.reuters.com/...\nAAPL;https://finance.yahoo.com/...")

liens, ignorees = lire_liens_texte(texte_liens) if texte_liens.strip() else ({}, [])
tickers_connus = {t["ticker"] for t in fonds["titres"] if t["ticker"]}

c1, c2, c3 = st.columns(3)
c1.metric("Liens", sum(len(v) for v in liens.values()))
c2.metric("Valeurs couvertes", f"{len(set(liens) & tickers_connus)} / {len(tickers_connus)}")
c3.metric("Lignes ignorees", len(ignorees))

if ignorees:
    st.markdown(f'<p class="avertissement">Sans adresse valide : lignes '
               f'{", ".join(str(n) for n, _ in ignorees[:12])}</p>', unsafe_allow_html=True)

a_traiter = st.multiselect("Valeurs a traiter", [t["nom"] for t in fonds["titres"]],
    default=[t["nom"] for t in fonds["titres"] if t["ticker"] in liens])

lancer = st.button("Generer les commentaires", type="primary",
                   disabled=not a_traiter or not texte_liens.strip())

if lancer:
    if not cle_api:
        st.error("Renseigne ta cle API Mistral dans la barre laterale.")
        st.stop()

    st.session_state.resultats.setdefault(code_semaine, {}).setdefault(id_fonds, {})
    stockage = st.session_state.resultats[code_semaine][id_fonds]

    barre = st.progress(0.0)
    etat = st.empty()

    for i, titre in enumerate(fonds["titres"]):
        nom, ticker = titre["nom"], titre["ticker"]
        if nom not in a_traiter:
            barre.progress((i + 1) / len(fonds["titres"]))
            continue

        etat.caption(f"{nom} — cours")
        seances = charger_cours(ticker, code_semaine) if ticker else []

        articles, soucis = [], []
        for url in liens.get(ticker, []):
            etat.caption(f"{nom} — lecture de la source")
            a = extraire_article(url)
            if a:
                articles.append(a)
            else:
                soucis.append(url)

        resume, erreur = "", None
        if articles:
            etat.caption(f"{nom} — redaction")
            prompt = construire_prompt(nom, fonds["nom"], titre["poids"], seances, articles)
            resume, erreur = appeler_mistral(prompt, cle_api)
            resume = resume or ""

        stockage[ticker or nom] = {
            "nom": nom, "ticker": ticker, "devise": devise_du_ticker(ticker),
            "poids": titre["poids"], "cours": seances, "perf": perf_semaine(seances),
            "resume": resume, "erreur": erreur,
            "sources": [{"url": a["url"], "titre": a["titre"]} for a in articles],
            "sources_illisibles": soucis,
        }
        barre.progress((i + 1) / len(fonds["titres"]))

    etat.empty(); barre.empty()
    reussis = sum(1 for v in stockage.values() if v.get("resume"))
    st.success(f"{reussis} commentaire(s) genere(s) sur {len(a_traiter)} valeur(s) traitee(s).")


# ==========================================================================
# RESULTATS
# ==========================================================================

stockage = st.session_state.resultats.get(code_semaine, {}).get(id_fonds, {})

if stockage:
    st.markdown("## Synthese")

    valeurs = list(stockage.values())
    cotees = [v for v in valeurs if v.get("perf") is not None]
    poids_total = sum(v["poids"] for v in cotees)
    pondere = (sum(v["perf"] * v["poids"] for v in cotees) / poids_total
              if poids_total else None)

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Performance ponderee", "–" if pondere is None else f"{pondere:+.2f} %")
    if cotees:
        meilleur = max(cotees, key=lambda v: v["perf"])
        pire = min(cotees, key=lambda v: v["perf"])
        s2.metric(meilleur["nom"], f"{meilleur['perf']:+.2f} %")
        s3.metric(pire["nom"], f"{pire['perf']:+.2f} %")
    s4.metric("Valeurs commentees", f"{sum(1 for v in valeurs if v.get('resume'))} / {len(valeurs)}")

    st.markdown("## Valeurs")

    for titre in fonds["titres"]:
        v = stockage.get(titre["ticker"] or titre["nom"])
        if not v:
            continue

        perf = v.get("perf")
        classe = "neutre" if perf is None else ("hausse" if perf > 0 else "baisse" if perf < 0 else "neutre")
        perf_txt = "–" if perf is None else f"{perf:+.2f} %"

        st.markdown(f"""
        <div class="fiche">
          <div class="fiche-tete">
            <span class="fiche-nom">{v['nom']}</span>
            <span class="fiche-ticker">{v['ticker'] or '—'}</span>
            <span class="fiche-perf {classe}">{perf_txt}</span>
            <span class="fiche-poids">{v['poids']} % du fonds</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        gauche, droite = st.columns([1, 2.6])
        with gauche:
            if v.get("cours"):
                st.dataframe(
                    [{"Date": c["date"][5:].replace("-", "/"), "Cours": c["dernier"],
                      "Var.": "–" if c["variation"] is None else f"{c['variation']:+.2f} %"}
                     for c in v["cours"]],
                    hide_index=True, use_container_width=True)
            else:
                st.caption("Cours indisponibles.")

        with droite:
            if v.get("erreur"):
                st.markdown(f'<p class="avertissement">Echec de la redaction : {v["erreur"]}</p>',
                           unsafe_allow_html=True)

            nouveau = st.text_area("commentaire", value=v.get("resume", ""), height=170,
                key=f"txt_{code_semaine}_{id_fonds}_{titre['ticker']}",
                label_visibility="collapsed",
                placeholder="Aucun commentaire genere. Tu peux en ecrire un ici.")
            if nouveau != v.get("resume", ""):
                v["resume"] = nouveau

            if v.get("sources"):
                st.markdown('<p class="sources-titre">Sources</p>', unsafe_allow_html=True)
                for s in v["sources"]:
                    st.markdown(f'<a class="source-lien" href="{s["url"]}" target="_blank">{s["titre"][:90]}</a>',
                               unsafe_allow_html=True)
            if v.get("sources_illisibles"):
                st.markdown(f'<p class="avertissement">{len(v["sources_illisibles"])} '
                           f'source(s) illisible(s) — extraction bloquee par le site.</p>',
                           unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

else:
    st.info("Colle des liens ci-dessus puis lance la generation pour voir les resultats.")

st.markdown('<p class="pied">Document de travail interne. Les commentaires sont '
           'produits automatiquement a partir des sources listees et doivent etre '
           'relus avant toute diffusion.</p>', unsafe_allow_html=True)
