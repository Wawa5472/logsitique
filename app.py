"""
Air Cargo Hub — simulateur de chaîne logistique fret aérien
Cotation client, expédition fournisseur, suivi de vol 3D, douane et documents légaux.

Lancer :  pip install "streamlit>=1.40" pandas
          streamlit run app.py

Pour modifier le rendu :
  - couleurs et polices : bloc :root au début de la constante APP_CSS ci-dessous
  - thème Streamlit (widgets) : fichier .streamlit/config.toml
"""

import hashlib
import json
import math
import random
import base64
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# CONFIG PAGE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Air Cargo Hub",
    page_icon=":material/flight:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# DESIGN : thème sombre, navigation en segments, panneaux, frise de statut
# Toutes les couleurs et polices se règlent dans le bloc :root.
# -----------------------------------------------------------------------------
APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root{
  --bg:#232E44;
  --surface:#2D3A54;
  --surface-2:#364563;
  --line:#4A5B7E;
  --line-soft:#3D4D6E;
  --text:#F2F5FB;
  --muted:#BAC5DA;
  --faint:#9AA8C4;
  --accent:#FF7A00;
  --accent-soft:rgba(255,122,0,.16);
  --ok:#34C48B;
  --warn:#F2B03D;
  --bad:#EF5B5B;
  --info:#5B9BFF;
  color-scheme:dark;
  --sans:'IBM Plex Sans',system-ui,-apple-system,'Segoe UI',sans-serif;
  --mono:'IBM Plex Mono',ui-monospace,'SF Mono',Menlo,monospace;
}

/* ---- Base ---- */
html, body, .stApp, [data-testid="stAppViewContainer"]{ background:var(--bg); color:var(--text); }
html, body, .stApp, .stMarkdown, .stMarkdown p, label, input, textarea, button, [data-baseweb]{ font-family:var(--sans) !important; }
[data-testid="stIconMaterial"], [class*="material-symbols"]{ font-family:'Material Symbols Rounded' !important; }
.stApp, [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *, [data-testid="stRadio"] label, [data-testid="stRadio"] label *,
[data-testid="stSlider"] *, [data-testid="stText"]{ color:var(--text) !important; }
header[data-testid="stHeader"] *, [data-testid="stToolbar"] *{ color:var(--muted) !important; }
.block-container{ max-width:1320px; padding-top:1.4rem; padding-bottom:4rem; }
header[data-testid="stHeader"]{ background:transparent; }
#MainMenu, footer{ visibility:hidden; }
h1,h2,h3,h4,h5,h6{ letter-spacing:-.01em; font-weight:600; color:var(--text) !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] *{ color:var(--muted) !important; }
hr{ border-color:var(--line-soft); }
.mono{ font-family:var(--mono) !important; }
.acc{ color:var(--accent); }

/* ---- Barre de marque ---- */
.topbar{ display:flex; justify-content:space-between; align-items:center; gap:1.5rem; flex-wrap:wrap;
  padding:1.1rem 1.4rem; border:1px solid var(--line-soft); border-radius:14px;
  background:var(--surface); margin-bottom:1.3rem; }
.brand{ display:flex; align-items:center; gap:.9rem; }
.brand-mark{ width:42px; height:42px; border-radius:10px; background:var(--accent-soft);
  border:1px solid rgba(255,122,0,.35); display:grid; place-items:center; }
.brand-name{ font-weight:700; font-size:1.25rem; letter-spacing:-.01em; }
.brand-sub{ color:var(--muted); font-size:.82rem; margin-top:2px; }
.tb-stats{ display:flex; gap:1.8rem; }
.tb-stat b{ display:block; font-family:var(--mono); font-size:1.3rem; font-weight:600; }
.tb-stat span{ font-size:.68rem; letter-spacing:.09em; text-transform:uppercase; color:var(--muted); }

/* ---- Navigation (onglets en segments) ---- */
[data-baseweb="tab-list"], [role="tablist"]{ gap:4px !important; background:var(--surface) !important; border:1px solid var(--line-soft) !important;
  padding:4px !important; border-radius:12px !important; width:fit-content !important; max-width:100%; overflow-x:auto; }
button[role="tab"]{ height:38px; padding:0 18px !important; border-radius:8px !important; background:transparent !important;
  color:var(--muted) !important; font-weight:500; border:0 !important; }
button[role="tab"] p{ color:inherit !important; font-size:.88rem; }
button[role="tab"]:hover{ color:var(--text) !important; background:rgba(255,255,255,.07) !important; }
button[role="tab"][aria-selected="true"]{ background:var(--accent-soft) !important; color:var(--accent) !important; box-shadow:inset 0 0 0 1px rgba(255,122,0,.5) !important; }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"]{ display:none !important; height:0 !important; background:transparent !important; }
[data-baseweb="tab-panel"]{ padding-top:1.6rem; }

/* ---- Titres de section ---- */
.sec{ margin:.2rem 0 1.1rem; }
.sec h3{ margin:0; font-size:1.35rem; font-weight:600; }
.sec p{ margin:.25rem 0 0; color:var(--muted) !important; font-size:.9rem; }
.eyebrow{ font-size:.7rem; letter-spacing:.12em; text-transform:uppercase; color:var(--faint); font-weight:600; margin-bottom:.15rem; }

/* ---- Panneaux ---- */
[class*="st-key-panel_"]{ background:var(--surface); border:1px solid var(--line-soft); border-radius:14px; padding:1.2rem 1.4rem; }

/* ---- Boutons ---- */
.stButton > button, .stDownloadButton > button{ width:100%; border-radius:10px; border:1px solid var(--line);
  background:var(--surface-2); color:var(--text); font-weight:500; padding:.55rem 1rem; transition:border-color .15s, background .15s; }
.stButton > button:hover, .stDownloadButton > button:hover{ border-color:var(--accent); color:#fff; background:#41537A; }
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible{ outline:2px solid var(--accent); outline-offset:2px; }
[data-testid="stBaseButton-primary"]{ background:var(--accent) !important; border-color:var(--accent) !important; color:#0A101C !important; font-weight:600 !important; }
[data-testid="stBaseButton-primary"]:hover{ background:#FF8F2B !important; }

/* ---- Champs : tous les calques du widget partagent fond et texte ---- */
[data-testid="stNumberInput"] [data-baseweb], [data-testid="stSelectbox"] [data-baseweb], [data-testid="stTextInput"] [data-baseweb],
[data-testid="stTextArea"] [data-baseweb], [data-testid="stNumberInputContainer"]{
  background:var(--surface-2) !important; border-color:var(--line) !important; border-radius:10px !important; color:var(--text) !important; }
input, textarea{ background:transparent !important; color:var(--text) !important; -webkit-text-fill-color:var(--text) !important; caret-color:var(--accent); }
[data-testid="stSelectbox"] [data-baseweb="select"] *{ color:var(--text) !important; }
[data-testid="stNumberInputStepDown"], [data-testid="stNumberInputStepUp"]{ background:transparent !important; color:var(--muted) !important; }
[data-testid="stSelectbox"] svg, [data-testid="stNumberInput"] svg{ fill:var(--muted) !important; color:var(--muted) !important; }
[data-baseweb="popover"] *{ color:var(--text) !important; }
[data-baseweb="popover"] [data-baseweb="menu"], [data-baseweb="popover"] ul, [data-baseweb="popover"] li{ background:var(--surface-2) !important; }
[data-baseweb="popover"] li:hover{ background:var(--surface) !important; }
textarea{ font-family:var(--mono) !important; font-size:.8rem !important; }

/* ---- Alertes, expanders, métriques ---- */
[data-testid="stAlert"]{ border-radius:10px; border:1px solid var(--line) !important; background:var(--surface-2) !important; }
[data-testid="stAlert"] *{ color:var(--text) !important; }
[data-testid="stExpander"]{ border:1px solid var(--line-soft); border-radius:12px; background:var(--surface); }
[data-testid="stExpander"] details{ background:var(--surface) !important; border:0 !important; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary *{ color:var(--text) !important; }
[data-testid="stExpander"] summary:hover, [data-testid="stExpander"] summary:hover *{ color:var(--accent) !important; }
[data-testid="stMetric"]{ background:var(--surface-2); border:1px solid var(--line-soft); border-radius:10px; padding:.8rem 1rem; }
[data-testid="stMetricLabel"]{ color:var(--muted); font-size:.72rem; letter-spacing:.06em; text-transform:uppercase; }
[data-testid="stMetricValue"]{ font-family:var(--mono) !important; font-size:1.4rem; }
.stApp iframe{ border-radius:12px; border:1px solid var(--line-soft); }

/* ---- Frise du processus ---- */
.pipeline{ display:flex; gap:0; padding:1rem 1.2rem 1.1rem; border:1px solid var(--line-soft); border-radius:14px;
  background:var(--surface); margin:.4rem 0 1.2rem; overflow-x:auto; }
.pl-step{ flex:1 0 108px; position:relative; text-align:center; padding:0 .3rem; }
.pl-step::before{ content:""; position:absolute; top:13px; left:-50%; width:100%; height:2px; background:var(--line); }
.pl-step:first-child::before{ display:none; }
.pl-step.done::before, .pl-step.now::before{ background:var(--accent); }
.pl-dot{ position:relative; z-index:1; width:28px; height:28px; border-radius:50%; margin:0 auto .5rem; display:grid; place-items:center;
  font-family:var(--mono); font-size:.72rem; font-weight:600; background:var(--surface-2); border:2px solid var(--line); color:var(--faint); }
.pl-step.done .pl-dot{ background:var(--accent); border-color:var(--accent); color:#0A101C; }
.pl-step.now .pl-dot{ background:var(--bg); border-color:var(--accent); color:var(--accent); box-shadow:0 0 0 5px var(--accent-soft); }
.pl-label{ font-size:.74rem; color:var(--faint); line-height:1.25; }
.pl-step.done .pl-label{ color:var(--muted); }
.pl-step.now .pl-label{ color:var(--text); font-weight:600; }

/* ---- Cascade des coûts ---- */
.ladder{ display:flex; flex-direction:column; gap:.5rem; }
.rung{ display:grid; grid-template-columns:78px 1fr auto; align-items:center; gap:.9rem; padding:.8rem 1rem;
  border:1px solid var(--line-soft); border-radius:10px; background:var(--surface-2); }
.rung.off{ opacity:.6; }
.rung.sel{ border-color:var(--accent); background:var(--accent-soft); }
.rung-code{ font-family:var(--mono); font-weight:600; font-size:.82rem; color:var(--accent); }
.rung-label{ font-size:.84rem; color:var(--muted); }
.rung-label em{ display:block; font-style:normal; font-family:var(--mono); font-size:.72rem; color:var(--faint); margin-top:2px; }
.rung-amt{ font-family:var(--mono); font-size:1.12rem; font-weight:600; text-align:right; white-space:nowrap; }
.note{ margin-top:.7rem; font-size:.8rem; color:var(--muted); }

/* ---- Tuiles de chiffres ---- */
.stats{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:.7rem; }
.stat{ padding:.8rem 1rem; border:1px solid var(--line-soft); border-radius:10px; background:var(--surface-2); }
.stat span{ display:block; font-size:.68rem; letter-spacing:.09em; text-transform:uppercase; color:var(--muted); }
.stat b{ display:block; font-family:var(--mono); font-size:1.2rem; font-weight:600; margin-top:.25rem; }
.stat em{ display:block; font-style:normal; font-size:.74rem; color:var(--faint); margin-top:2px; }

/* ---- Tableaux ---- */
.tbl{ width:100%; border-collapse:collapse; font-size:.88rem; }
.tbl th{ text-align:left; font-size:.68rem; letter-spacing:.1em; text-transform:uppercase; color:var(--faint); font-weight:600; padding:.5rem .7rem; border-bottom:1px solid var(--line); }
.tbl td{ padding:.6rem .7rem; border-bottom:1px solid var(--line-soft); color:var(--text); }
.tbl td.num, .tbl th.num{ text-align:right; font-family:var(--mono); }
.tbl td.mono{ color:var(--accent); font-weight:600; }
.tbl tr.total td{ font-weight:600; border-bottom:none; border-top:1px solid var(--line); }

/* ---- Produits, pastilles, bandeau de vol ---- */
.prod-name{ font-weight:600; }
.prod-spec{ font-family:var(--mono); font-size:.76rem; color:var(--muted); margin-top:2px; }
.chip{ display:inline-block; padding:.15rem .65rem; border-radius:99px; font-size:.72rem; font-weight:600; border:1px solid var(--line); color:var(--muted); }
.chip.accent{ color:var(--accent); border-color:rgba(255,122,0,.45); background:var(--accent-soft); }
.chip.ok{ color:var(--ok); border-color:rgba(52,196,139,.4); }
.banner{ display:flex; align-items:center; gap:.8rem; flex-wrap:wrap; padding:.8rem 1.1rem; border:1px solid var(--line-soft);
  border-radius:12px; background:var(--surface); }
.banner .path{ font-family:var(--mono); font-weight:600; font-size:1.05rem; }
.banner .city{ color:var(--muted); font-size:.88rem; }
</style>
"""
st.markdown(APP_CSS, unsafe_allow_html=True)


def md(html: str) -> None:
    st.markdown(html, unsafe_allow_html=True)


def section(title: str, caption: str = "") -> None:
    cap = f"<p>{caption}</p>" if caption else ""
    md(f'<div class="sec"><h3>{title}</h3>{cap}</div>')


def eyebrow(text: str) -> None:
    md(f'<div class="eyebrow">{text}</div>')


def eur(x: float) -> str:
    return f"{x:,.2f}".replace(",", " ").replace(".", ",") + " €"


def num(x: float, dec: int = 0) -> str:
    return f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")


def stats(items) -> str:
    cells = "".join(
        f'<div class="stat"><span>{l}</span><b>{v}</b>' + (f"<em>{s}</em>" if s else "") + "</div>"
        for l, v, s in items
    )
    return f'<div class="stats">{cells}</div>'


def stable_int(text: str, mod: int, offset: int = 0) -> int:
    """Nombre stable (identique à chaque redémarrage), contrairement à hash()."""
    return int(hashlib.md5(text.encode()).hexdigest(), 16) % mod + offset


MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def date_fr(d: datetime) -> str:
    return f"{d.day} {MOIS[d.month - 1]} {d.year}"


# -----------------------------------------------------------------------------
# DONNÉES DE BASE
# -----------------------------------------------------------------------------
AIRPORTS = {
    "Chine (Shanghai - PVG)": {"lat": 31.1443, "lon": 121.8083, "code": "PVG", "ville": "Shanghai", "tarif": 3.9},
    "Chine (Pékin - PEK)": {"lat": 40.0799, "lon": 116.6031, "code": "PEK", "ville": "Pékin", "tarif": 3.0},
    "Chine (Guangzhou - CAN)": {"lat": 23.3924, "lon": 113.2988, "code": "CAN", "ville": "Guangzhou", "tarif": 4.0},
    "États-Unis (New York - JFK)": {"lat": 40.6413, "lon": -73.7781, "code": "JFK", "ville": "New York", "tarif": 2.9},
}
CDG = {"lat": 49.0097, "lon": 2.5479, "code": "CDG", "ville": "Paris"}

NO_FLY = [
    {"name": "Zone interdite A", "ring": [[34, 24], [62, 24], [62, 38], [34, 38], [34, 24]]},
    {"name": "Zone interdite B", "ring": [[24, 44], [45, 44], [45, 58], [24, 58], [24, 44]]},
]

# Flotte annexe
FLEET = [
    ("AF-801", [139.69, 35.68], [103.81, 1.35], 0.8, 0.10),
    ("BA-249", [-0.12, 51.50], [55.27, 25.20], 0.9, 0.30),
    ("LH-400", [-73.77, 40.64], [8.57, 50.03], 0.7, 0.50),
    ("EK-308", [55.27, 25.20], [121.80, 31.14], 1.1, 0.20),
    ("AF-454", [2.54, 49.00], [-46.63, -23.55], 0.65, 0.60),
    ("SQ-322", [103.81, 1.35], [-0.12, 51.50], 0.75, 0.00),
    ("CX-251", [114.16, 22.31], [2.54, 49.00], 0.85, 0.40),
    ("JL-045", [139.69, 35.68], [2.54, 49.00], 0.70, 0.70),
    ("DL-101", [-84.42, 33.64], [2.54, 49.00], 0.75, 0.25),
    ("UA-909", [-87.90, 41.97], [-0.12, 51.50], 0.8, 0.55),
]

INCOTERM_INFO = {
    "EXW": "Ex Works : l'acheteur gère tout depuis l'usine.",
    "FCA": "Free Carrier : remis au transporteur désigné à l'aéroport de départ.",
    "CPT": "Carriage Paid To : transport payé jusqu'à CDG, transferts de risques anticipés.",
    "CIP": "Carriage and Insurance Paid : transport + assurance payés jusqu'à CDG.",
    "DAP": "Delivered at Place : livré à destination (CDG), non dédouané.",
    "DPU": "Delivered at Place Unloaded : livré et déchargé sur le terminal à destination.",
    "DDP": "Delivered Duty Paid : vendeur gère tout, y compris dédouanement à l'import.",
}
INCOTERM_RANK = {"EXW": 1, "FCA": 2, "CPT": 3, "CIP": 3, "DAP": 4, "DPU": 4, "DDP": 4}

STATUSES = ["Commande reçue", "Documents générés", "Au dépôt de départ", "Remis au transporteur", "En vol vers CDG", "Atterri à CDG", "Livré / dédouané"]
FLIGHT_STEP = 4

PRODUCTS = {
    "Rétroviseur Voiture": {"prix": 45, "poids": 1.2, "vol": 0.01},
    "Rétroviseur BUS": {"prix": 120, "poids": 3.5, "vol": 0.03},
    "Rétroviseur Camion": {"prix": 95, "poids": 2.8, "vol": 0.02},
    "Rétroviseur Engins de chantier": {"prix": 150, "poids": 4.5, "vol": 0.04},
    "Rétroviseur Caméra (High-Tech)": {"prix": 250, "poids": 1.5, "vol": 0.008},
}

COMPANY_MAP = {
    "Chine (Shanghai - PVG)": "SHANGHAI AUTO PARTS LTD",
    "Chine (Pékin - PEK)": "BEIJING MIRRORS MFG",
    "Chine (Guangzhou - CAN)": "GUANGZHOU INDUSTRIAL CO.",
    "États-Unis (New York - JFK)": "NY AUTO COMPONENTS INC.",
}

# -----------------------------------------------------------------------------
# OUTILS GÉO
# -----------------------------------------------------------------------------
def haversine_km(a, b):
    lon1, lat1, lon2, lat2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def great_circle(p1, p2, n=150):
    lon1, lat1, lon2, lat2 = map(math.radians, [p1[0], p1[1], p2[0], p2[1]])
    d = 2 * math.asin(math.sqrt(math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2))
    if d == 0:
        return [list(p1)]
    pts = []
    for i in range(n + 1):
        f = i / n
        a = math.sin((1 - f) * d) / math.sin(d)
        b = math.sin(f * d) / math.sin(d)
        x = a * math.cos(lat1) * math.cos(lon1) + b * math.cos(lat2) * math.cos(lon2)
        y = a * math.cos(lat1) * math.sin(lon1) + b * math.cos(lat2) * math.sin(lon2)
        z = a * math.sin(lat1) + b * math.sin(lat2)
        pts.append([math.degrees(math.atan2(y, x)), math.degrees(math.atan2(z, math.hypot(x, y)))])
    return pts


def build_route(start, end):
    via = [[85, 50], [58, 61], [30, 61], [12, 53]] if start["lon"] > 50 else [[-55, 52], [-35, 60], [-20, 64], [-10, 56]]
    wps = [[start["lon"], start["lat"]]] + via + [[end["lon"], end["lat"]]]
    route = []
    for a, b in zip(wps[:-1], wps[1:]):
        seg = great_circle(a, b, 150)
        route.extend(seg if not route else seg[1:])
    km = sum(haversine_km(route[i], route[i + 1]) for i in range(len(route) - 1))
    return route, km


# -----------------------------------------------------------------------------
# CARTE MAPLIBRE + DECK.GL (logique inchangée, habillage sombre)
# -----------------------------------------------------------------------------
MAP_HTML = r"""
<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet">
<script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
<script src="https://unpkg.com/deck.gl@8.9.33/dist.min.js"></script>
<style>
 html,body{margin:0;height:100%;font-family:'IBM Plex Sans',system-ui,sans-serif;background:#232E44;color:#F2F5FB}
 #map{position:absolute;inset:0}
 .hud{position:absolute;left:14px;right:14px;bottom:14px;background:rgba(35,46,68,.93);color:#F2F5FB;
   border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:12px 16px;backdrop-filter:blur(10px);box-shadow:0 8px 28px rgba(0,0,0,.4)}
 .row{display:flex;gap:18px;flex-wrap:wrap;align-items:center;justify-content:space-between}
 .kpi{min-width:92px}
 .kpi b{display:block;font-family:'IBM Plex Mono',monospace;font-size:1.1rem;font-weight:600}
 .kpi span{font-size:.64rem;letter-spacing:.09em;opacity:.6;text-transform:uppercase}
 .bar{height:6px;background:rgba(255,255,255,.14);border-radius:99px;margin:10px 0 4px;overflow:hidden}
 .bar i{display:block;height:100%;width:0;background:#FF7A00;border-radius:99px}
 button,select{background:#FF7A00;color:#0A101C;border:0;border-radius:8px;padding:8px 14px;font-weight:600;cursor:pointer;font-size:.82rem;font-family:inherit}
 button.alt,select{background:rgba(255,255,255,.1);color:#E7ECF6}
 select option{color:#000}
 .flight-card{position:absolute;top:14px;left:14px;background:rgba(35,46,68,.95);color:#F2F5FB;border-radius:12px;overflow:hidden;width:220px;z-index:2;border:1px solid rgba(255,255,255,.1);backdrop-filter:blur(10px)}
 .flight-card img{width:100%;height:95px;object-fit:cover;display:block;border-bottom:2px solid #FF7A00}
 .flight-card-body{padding:10px 12px}
 .flight-card-header{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;border-bottom:1px solid rgba(255,255,255,.12);padding-bottom:6px}
 .flight-card-header h2{margin:0;font-family:'IBM Plex Mono',monospace;font-size:1.05rem;color:#FF7A00}
 .flight-card-header span{font-size:.7rem;opacity:.8}
 .flight-route{display:flex;justify-content:space-between;align-items:center;margin-top:4px}
 .route-point{text-align:center}
 .route-point b{display:block;font-family:'IBM Plex Mono',monospace;font-size:1.05rem}
 .route-point span{font-size:.65rem;opacity:.65}
 .route-arrow{color:#FF7A00;font-size:1.1rem;opacity:.9}
 .lbl{background:#fff;color:#0E2A47;font-weight:700;font-size:11px;padding:3px 8px;border-radius:99px;white-space:nowrap}
 .lbl.red{background:#C62828;color:#fff}.lbl.green{background:#2E7D32;color:#fff}
 .fl{font-size:10px;font-weight:600;color:#37474f;text-align:center;white-space:nowrap;text-shadow:0 0 3px #fff}
 body.dark .fl{color:#C9D3E8;text-shadow:0 0 3px #0A101C}
</style></head><body>
<div id="map"></div><div class="flight-card" id="flight-card"></div>
<div class="hud">
  <div class="row">
    <div class="kpi"><b id="k_alt">0 m</b><span>Altitude</span></div>
    <div class="kpi"><b id="k_spd">0 km/h</b><span>Vitesse</span></div>
    <div class="kpi"><b id="k_dist">0 km</b><span>Restant</span></div>
    <div class="kpi"><b id="k_pct">0 %</b><span>Progression</span></div>
    <div class="row">
      <button id="b_play">Lancer</button>
      <button class="alt" id="b_cam">Caméra : suivi</button>
      <select id="s_speed">
        <option value="0.5">×0.5</option>
        <option value="1" selected>×1</option>
        <option value="2">×2</option>
        <option value="4">×4</option>
        <option value="8">×8</option>
      </select>
    </div>
  </div>
  <div class="bar"><i id="bar"></i></div>
</div>
<script>
const D=__DATA__, rad=x=>x*Math.PI/180, deg=x=>x*180/Math.PI;
document.body.className = D.dark ? 'dark' : 'light';
document.getElementById('flight-card').innerHTML=`${D.photo?`<img src="${D.photo}">`:''}<div class="flight-card-body"><div class="flight-card-header"><h2>${D.flight_num}</h2><span>${D.plane_model}</span></div><div class="flight-route"><div class="route-point"><b>${D.origin.code}</b><span>${D.origin.ville}</span></div><div class="route-arrow">→</div><div class="route-point"><b>${D.dest.code}</b><span>${D.dest.ville}</span></div></div></div>`;
function hav(a,b){const dl=rad(b[1]-a[1]),dn=rad(b[0]-a[0]);return 12742*Math.asin(Math.sqrt(Math.sin(dl/2)**2+Math.cos(rad(a[1]))*Math.cos(rad(b[1]))*Math.sin(dn/2)**2));}
function brg(a,b){return(deg(Math.atan2(Math.sin(rad(b[0]-a[0]))*Math.cos(rad(b[1])),Math.cos(rad(a[1]))*Math.sin(rad(b[1]))-Math.sin(rad(a[1]))*Math.cos(rad(b[1]))*Math.cos(rad(b[0]-a[0]))))+360)%360;}
function mk(pts){const c=[0];for(let i=1;i<pts.length;i++)c.push(c[i-1]+hav(pts[i-1],pts[i]));return{pts,c,total:c[c.length-1]};}
function at(p,f){f=Math.min(Math.max(f,0),1);const d=f*p.total;let i=1;while(i<p.c.length-1&&p.c[i]<d)i++;const k=(d-p.c[i-1])/((p.c[i]-p.c[i-1])||1),a=p.pts[i-1],b=p.pts[i];return{lon:a[0]+(b[0]-a[0])*k,lat:a[1]+(b[1]-a[1])*k,b:brg(a,b),i:i-1};}

const PLANE=(f,s)=>`<svg width="${s}" height="${s}" viewBox="0 0 64 64"><path d="M32 2 L37 22 L60 36 L60 42 L37 36 L36 52 L44 58 L44 62 L32 59 L20 62 L20 58 L28 52 L27 36 L4 42 L4 36 L27 22 Z" fill="${f}" stroke="#fff" stroke-width="2.2"/></svg>`;
const main=mk(D.route), map=new maplibregl.Map({container:'map',style:D.style,center:D.center,zoom:2.4,pitch:45,bearing:-8});
map.addControl(new maplibregl.NavigationControl({visualizePitch:true}),'top-right');
function lab(txt,cls,lngLat){const e=document.createElement('div');e.className='lbl '+cls;e.textContent=txt;return new maplibregl.Marker({element:e,anchor:'bottom',offset:[0,-4]}).setLngLat(lngLat).addTo(map);}

let overlay=null, planeM, fleetM=[], playing=false, t=D.start, follow=true, lastTs=null, curB=0, clock=0, mult=1;

map.on('load',()=>{
  // 1. Zones d'exclusion aérienne (NO_FLY) sans texte
  if(D.no_fly) {
    D.no_fly.forEach((zone, i) => {
      map.addSource('nofly-'+i, {
        'type': 'geojson',
        'data': { 'type': 'Feature', 'geometry': { 'type': 'Polygon', 'coordinates': [zone.ring] } }
      });
      map.addLayer({
        'id': 'nofly-fill-'+i, 'type': 'fill', 'source': 'nofly-'+i,
        'paint': { 'fill-color': '#EF4444', 'fill-opacity': 0.15 }
      });
      map.addLayer({
        'id': 'nofly-line-'+i, 'type': 'line', 'source': 'nofly-'+i,
        'paint': { 'line-color': '#B91C1C', 'line-width': 1.5, 'line-dasharray': [4, 4] }
      });
    });
  }

  // 2. Trajet principal
  map.addSource('plan',{type:'geojson',data:{type:'Feature',geometry:{type:'LineString',coordinates:D.route}}});
  map.addLayer({id:'plan',type:'line',source:'plan',paint:{'line-color':'#90A4AE','line-width':3,'line-dasharray':[1.5,2.5]}});
  map.addSource('trail',{type:'geojson',data:{type:'Feature',geometry:{type:'LineString',coordinates:[D.route[0],D.route[0]]}}});
  map.addLayer({id:'trail',type:'line',source:'trail',paint:{'line-color':'#FF5A00','line-width':5}});
  lab(D.origin.code,'red',[D.origin.lon,D.origin.lat]); lab(D.dest.code,'green',[D.dest.lon,D.dest.lat]);

  // 3. Flotte annexe
  D.fleet.forEach(f=>{
    const w=document.createElement('div');
    w.innerHTML = `<div class="svg-container">${PLANE('#78909C',20)}</div><div class="fl">${f.code}</div>`;
    const m=new maplibregl.Marker({element:w,rotationAlignment:'map',pitchAlignment:'map'}).setLngLat(f.pts[0]).addTo(map);
    fleetM.push({m,path:mk(f.pts),speed:f.speed,phase:f.phase,el:w});
  });

  const pe=document.createElement('div');pe.innerHTML=PLANE('#FF7A00',46);
  planeM=new maplibregl.Marker({element:pe}).setLngLat(D.route[0]).addTo(map);

  if(D.model && window.deck){
    try{
      overlay=new deck.MapboxOverlay({interleaved:false,layers:[]});
      map.addControl(overlay);
      pe.style.display='none';
    }catch(e){console.error(e);}
  }

  update(t); requestAnimationFrame(loop);
});

function update(f){
  const p=at(main,f); curB+=((((p.b-curB)+540)%360)-180)*0.1; planeM.setLngLat([p.lon,p.lat]).setRotation(p.b);
  const tr=D.route.slice(0,p.i+1).concat([[p.lon,p.lat]]); if(tr.length<2)tr.push([p.lon,p.lat]);
  map.getSource('trail').setData({type:'Feature',geometry:{type:'LineString',coordinates:tr}});

  const prof=Math.max(0.12,Math.min(1,f/0.08,(1-f)/0.08)), rem=main.total*(1-f);
  k_alt.textContent=f<=0||f>=1?'0 m':Math.round(11000*prof/100)*100+' m';
  k_spd.textContent=f<=0||f>=1?'0 km/h':Math.round(870*prof)+' km/h';
  k_dist.textContent=Math.round(rem).toLocaleString('fr-FR')+' km';
  k_pct.textContent=Math.round(f*100)+' %'; bar.style.width=(f*100)+'%';

  if(follow&&playing)map.jumpTo({center:[p.lon,p.lat],bearing:curB,pitch:55,zoom:4.2});
}

function loop(ts){
  if(!lastTs)lastTs=ts; const dt=(ts-lastTs)/1000; lastTs=ts; clock+=dt;
  if(playing){ t+=dt*mult/70; if(t>=1){t=1;playing=false;b_play.textContent='Rejouer';} update(t); }

  let sceneData = [];
  const p = at(main, t);
  const prof0 = Math.max(0.12, Math.min(1, t/0.08, (1-t)/0.08));
  sceneData.push({pos: [p.lon, p.lat, (t<=0||t>=1)?0:11000*prof0], yaw: -p.b});

  fleetM.forEach(f => {
      const q = at(f.path, (f.phase + clock * f.speed / 260) % 1);
      f.m.setLngLat([q.lon, q.lat]).setRotation(q.b);
      if(overlay) f.el.querySelector('.svg-container').style.display = 'none';
      sceneData.push({pos: [q.lon, q.lat, 11000], yaw: -q.b});
  });

  if(overlay){
    overlay.setProps({layers:[new deck.ScenegraphLayer({
      id:'planes-3d', data: sceneData, scenegraph: D.model,
      getPosition: d => d.pos, getOrientation: d => [0, d.yaw, 90],
      sizeScale: 100000, _lighting: 'pbr', pickable: false
    })]});
  }
  requestAnimationFrame(loop);
}

b_play.onclick=()=>{if(t>=1){t=0;curB=at(main,0).b;}playing=!playing;b_play.textContent=playing?'Pause':'Reprendre';if(playing&&follow)map.easeTo({pitch:55,zoom:4.2,duration:1200});};
b_cam.onclick=()=>{follow=!follow;b_cam.textContent='Caméra : '+(follow?'suivi':'libre');if(!follow)map.easeTo({pitch:35,bearing:-8,zoom:2.6,duration:1200});};
s_speed.onchange=e=>mult=parseFloat(e.target.value);
</script></body></html>
"""


@st.cache_data(show_spinner=False)
def load_plane_model():
    folder = Path(__file__).parent
    for f in sorted(folder.glob("*.glb")):
        return "data:model/gltf-binary;base64," + base64.b64encode(f.read_bytes()).decode(), f.name
    return None, None


@st.cache_data(show_spinner=False)
def load_fedex_image():
    img_path = Path(__file__).parent / "fedex.jpeg"
    if img_path.exists():
        return "data:image/jpeg;base64," + base64.b64encode(img_path.read_bytes()).decode()
    return ""


def render_flight_map(route, origin, dest, start_progress, style_name, flight_num, height=720):
    style = {
        "Clair": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        "Sombre": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    }[style_name]
    model_data, _ = load_plane_model()
    photo_b64 = load_fedex_image()
    fleet = [{"code": c, "pts": great_circle(a, b, 150), "speed": s, "phase": ph} for c, a, b, s, ph in FLEET]

    data = {
        "model": model_data, "photo": photo_b64, "flight_num": flight_num, "plane_model": "Boeing 777F",
        "route": route, "origin": origin, "dest": dest, "fleet": fleet, "style": style,
        "start": start_progress, "center": [(origin["lon"] + dest["lon"]) / 2, (origin["lat"] + dest["lat"]) / 2],
        "no_fly": NO_FLY, "dark": style_name == "Sombre",
    }
    components.html(MAP_HTML.replace("__DATA__", json.dumps(data)), height=height, scrolling=False)


# -----------------------------------------------------------------------------
# DOCUMENTS HTML OBLIGATOIRES (Packing list, AWB, DAU)
# Les documents restent sur fond blanc : ce sont des imitations de documents papier.
# -----------------------------------------------------------------------------
def generate_packing_list_html(order, airport, shipper_name):
    rows = ""
    for idx, item in enumerate(order["items"], 1):
        rows += f"""<tr><td style="border: 1px solid #000; padding: 5px;">{idx}</td><td style="border: 1px solid #000; padding: 5px;">{item['nom']}</td><td style="border: 1px solid #000; padding: 5px;">Unité</td><td style="border: 1px solid #000; padding: 5px;">{item['qte']}</td><td style="border: 1px solid #000; padding: 5px;">-</td></tr>"""
    return f"""<div style="font-family: Arial, sans-serif; padding: 30px; background: #fff; color: #000; max-width: 800px; margin: auto;"><div style="display: flex; justify-content: space-between; margin-bottom: 30px;"><div><h2 style="margin: 0 0 10px 0;">{shipper_name}</h2><div>Aéroport de {airport['ville']}</div><div>Code IATA: {airport['code']}</div></div><div style="text-align: right;"><h1 style="margin: 0; font-size: 24px;">Fiche de colisage</h1><div style="font-size: 12px; color: #555;">(Ceci n'est pas une facture)</div></div></div><table style="width: 100%; margin-bottom: 30px; font-size: 14px;"><tr><td style="width: 50%;"><b>Date :</b> {order['cree_le'].strftime("%d/%m/%Y")}</td><td style="width: 50%;"><b>Numéro commande :</b> {order['reference']}</td></tr></table><table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;"><thead><tr style="background-color: #f2f2f2;"><th style="border: 2px solid #000; padding: 8px;">Partie #</th><th style="border: 2px solid #000; padding: 8px;">Désignation</th><th style="border: 2px solid #000; padding: 8px;">Type d'unité</th><th style="border: 2px solid #000; padding: 8px;">Quantité</th><th style="border: 2px solid #000; padding: 8px;">Reste</th></tr></thead><tbody>{rows}</tbody></table></div>"""


def generate_awb_html(order, airport, shipper_name, flight_code):
    awb_num = f"057-{stable_int(order['reference'], 9000000, 1000000)}"
    return f"""<div style="font-family: Arial, sans-serif; padding: 20px; background: #fff; color: #000; max-width: 800px; margin: auto; font-size: 10px;"><div style="border: 2px solid #000;"><div style="display: flex; border-bottom: 2px solid #000;"><div style="width: 50%; border-right: 2px solid #000; padding: 5px;"><b>Shipper's Name</b><br><br>{shipper_name}<br>{airport['ville']}</div><div style="width: 50%; padding: 5px;"><b>AWB Number</b><br><br><span style="font-size: 16px; font-weight: bold;">{awb_num}</span></div></div><table style="width: 100%; border-collapse: collapse; text-align: center; font-size: 9px; margin-top: 10px;"><tr style="border-bottom: 1px solid #000; border-top: 2px solid #000;"><th style="border-right: 1px solid #000; padding: 4px;">Pieces</th><th style="border-right: 1px solid #000; padding: 4px;">Gross Weight</th><th style="border-right: 1px solid #000; padding: 4px;">Chargeable Weight</th><th style="padding: 4px;">Nature of Goods</th></tr><tr style="height: 100px; vertical-align: top;"><td style="border-right: 1px solid #000;">{sum(i['qte'] for i in order['items'])}</td><td style="border-right: 1px solid #000;">{order['poids_reel']}</td><td style="border-right: 1px solid #000;">{order['poids_taxable']}</td><td style="text-align: left; padding: 5px;">Auto Parts<br>Incoterm: {order['incoterm']}</td></tr></table></div></div>"""


def generate_dau_html(order, airport, shipper_name):
    return f"""<div style="font-family: Arial, sans-serif; padding: 10px; background: #fff; color: #000; max-width: 800px; margin: auto; font-size: 9px; border: 1px solid #ccc;"><div style="display: flex; border-bottom: 2px solid #000; padding-bottom: 5px;"><div style="width: 50%; font-size: 14px; font-weight: bold;">COMMUNAUTE EUROPEENNE</div><div style="width: 25%; border: 1px solid #000; padding: 2px;">1 DECLARATION<br><b>IM / A</b></div></div><div style="display: flex; border: 2px solid #000; margin-top: 5px;"><div style="width: 50%; border-right: 2px solid #000;"><div style="border-bottom: 1px solid #000; padding: 5px; height: 50px;">2 Expéditeur<br><b>{shipper_name}<br>{airport['ville']}</b></div><div style="border-bottom: 1px solid #000; padding: 5px; height: 50px;">8 Destinataire<br><b>SAINT-EURISTIDE LOGISTICS</b></div></div><div style="width: 50%;"><div style="border-bottom: 1px solid #000; padding: 5px;">31 Colis<br><b>{sum(i['qte'] for i in order['items'])} Colis</b><br>Poids brut: {order['poids_reel']} kg</div><div style="padding: 5px;">46 Valeur Statistique<br><b>{order['valeur'] + order['fret_aerien']:.2f} EUR</b></div></div></div></div>"""


# -----------------------------------------------------------------------------
# DOCUMENTS HTML FACULTATIFS (CE, assurance, POD, CGA)
# -----------------------------------------------------------------------------
def generate_ce_html(order, shipper_name, airport):
    items_list = ", ".join([item['nom'] for item in order['items']])
    return f"""
    <div style="font-family: 'Times New Roman', serif; padding: 40px; background: #fff; color: #000; max-width: 800px; margin: auto; border: 1px solid #ccc;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #000; padding-bottom: 20px; margin-bottom: 30px;">
            <div style="font-size: 24px; font-weight: bold; font-family: sans-serif; letter-spacing: 2px;">{shipper_name}</div>
            <div style="font-size: 70px; font-weight: bold; font-family: Arial, sans-serif; line-height: 1;">CE</div>
            <div style="border: 1px solid #000; padding: 10px; font-size: 12px; text-align: center;">
                <b>{shipper_name}</b><br>
                Aéroport de {airport['ville']}<br>
                {airport['code']}<br>
                Tel: +123 45 67 89 00
            </div>
        </div>
        <h2 style="text-align: center; text-decoration: underline; margin-bottom: 40px;">DECLARATION « CE » DE CONFORMITE</h2>
        <p>Nous soussignés, <b>{shipper_name}</b>, déclarons que les équipements désignés ci-après :</p>
        <p style="font-weight: bold; margin: 20px 0; line-height: 1.6;">
            COMMANDE REF: {order['reference']}<br>
            ARTICLES: {items_list}
        </p>
        <p>Sont conformes à la norme harmonisée : <b>NF EN 60730-2-15</b> (Classement C47-745)</p>
        <p>Conformément aux dispositions de la directive Basse Tension : <b>73/23/CEE</b> modifiée par <b>93/68/CEE</b> abrogée par <b>2006/95/CE</b></p>
        <p>Et aux législations nationales les transposant.</p>
        <div style="margin-top: 50px; display: flex; justify-content: space-between;">
            <div>
                Nom et fonction du signataire :<br><br>
                Fait à : {airport['ville']}<br>
                Le : {order['cree_le'].strftime("%d/%m/%Y")}
            </div>
            <div style="text-align: right; width: 250px;">
                Directeur Qualité<br>
                <div style="height: 60px; border-bottom: 1px dashed #000; margin-top: 10px; position: relative;">
                    <span style="position: absolute; top: 10px; right: 10px; font-family: cursive; font-size: 24px; color: #000080;">Signé num.</span>
                </div>
            </div>
        </div>
    </div>
    """


def generate_assurance_html(order, shipper_name):
    policy_num = f"029.880.{stable_int(order['reference'], 900, 100)}"
    return f"""
    <div style="font-family: Arial, sans-serif; padding: 40px; background: #fff; color: #000; max-width: 800px; margin: auto;">
        <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #ccc; padding-bottom: 20px; margin-bottom: 40px;">
            <div>
                <h1 style="margin: 0; font-size: 28px; color: #333;">BROKER Assurances</h1>
                <div style="font-size: 12px; color: #777;">Groupe International</div>
            </div>
            <div style="font-size: 11px; text-align: right; color: #555;">
                <b>AGENCE CENTRALE</b><br>
                141 avenue du Prado<br>
                13008 Marseille<br>
                Tél. : +33 (0)4 96 17 66 80
            </div>
        </div>
        <div style="border: 2px solid #000; text-align: center; padding: 10px; margin-bottom: 50px;">
            <h2 style="margin: 0; font-size: 22px; letter-spacing: 1px;">ATTESTATION D'ASSURANCE</h2>
        </div>
        <p style="text-align: justify; line-height: 1.6;">
            Nous soussignés <b>BROKER Assurances</b>, Courtier d'Assurances, sis 141 Avenue du Prado - Bat A - 13008 MARSEILLE, certifions par la présente que la société :
        </p>
        <div style="text-align: center; font-size: 18px; font-weight: bold; margin: 40px 0;">
            {shipper_name}<br>
            Expédition liée à la commande {order['reference']}<br>
            Incoterm : {order['incoterm']}
        </div>
        <p style="text-align: justify; line-height: 1.6;">
            Est assuré pour la période du <b>01.01.{datetime.now().year}</b> au <b>31.12.{datetime.now().year}</b> au titre du contrat d'assurance <b>Facultés Marchandises Transportées</b> portant le n°<b>{policy_num}</b> souscrit par notre intermédiaire auprès de la Compagnie ALLIANZ 1, A Avenue de la Marne - 59290 WASQUEHAL.
            <br><br>Valeur garantie : <b>{order['valeur'] * 1.1:,.2f} EUR</b> (110% de la valeur déclarée).
        </p>
        <div style="margin-top: 60px; text-align: right;">
            Marseille, le {date_fr(order['cree_le'])}.<br><br>
            Pour servir et valoir ce que de droit.<br>
            <div style="width: 200px; height: 100px; border: 2px solid #1A4D7C; border-radius: 50%; display: inline-block; margin-top: 20px; line-height: 100px; text-align: center; color: #1A4D7C; font-weight: bold; transform: rotate(-15deg); opacity: 0.6;">
                VALIDÉ PAR BROKER
            </div>
        </div>
    </div>
    """


def generate_pod_html(order, shipper_name):
    rows = ""
    for item in order["items"]:
        rows += f"""<tr>
            <td style="border: 1px solid #000; padding: 8px;">{item['nom']}</td>
            <td style="border: 1px solid #000; padding: 8px; text-align: center;">{item['qte']}</td>
            <td style="border: 1px solid #000; padding: 8px; text-align: center;">{item['qte']}</td>
            <td style="border: 1px solid #000; padding: 8px; text-align: right;">{item['prix_u']} €</td>
        </tr>"""

    return f"""
    <div style="font-family: Arial, sans-serif; padding: 30px; background: #fff; color: #000; max-width: 800px; margin: auto;">
        <h2 style="text-align: center; margin-bottom: 40px; font-size: 24px;">Proof of Delivery</h2>

        <div style="display: flex; justify-content: space-between; margin-bottom: 30px; font-size: 14px;">
            <div style="width: 45%;">
                <b>Company name:</b> {shipper_name}<br>
                <b>Address:</b> Usine d'expédition principale<br><br>
                <b>Email address:</b> logistics@provider.com<br>
                <b>Phone number:</b> +1 234 567 890
            </div>
            <div style="width: 45%;">
                <b>Date:</b> {order['cree_le'].strftime("%d/%m/%Y")}<br>
                <b>Order number:</b> {order['reference']}
            </div>
        </div>

        <div style="display: flex; justify-content: space-between; margin-bottom: 40px; font-size: 14px;">
            <div style="width: 45%;">
                <b>Delivered to</b><br>
                <b>Name:</b> SAINT-EURISTIDE LOGISTICS HUB<br>
                <b>Address:</b> Aéroport de Paris - Roissy CDG (France)
            </div>
            <div style="width: 45%;">
                <b>Billing details</b><br>
                <b>Name:</b> SAINT-EURISTIDE IMPORT DEPT<br>
                <b>Address:</b> 75000 Paris (France)
            </div>
        </div>

        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
            <thead>
                <tr>
                    <th colspan="4" style="border: 1px solid #000; padding: 10px; background-color: #f8f9fa; text-align: center; font-size: 16px;">Order Details</th>
                </tr>
                <tr style="background-color: #f2f2f2;">
                    <th style="border: 1px solid #000; padding: 8px; text-align: left;">Item description</th>
                    <th style="border: 1px solid #000; padding: 8px;">Quantity ordered</th>
                    <th style="border: 1px solid #000; padding: 8px;">Quantity delivered</th>
                    <th style="border: 1px solid #000; padding: 8px; text-align: right;">Price</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>

        <div style="margin-top: 60px; border-top: 1px solid #000; width: 300px; padding-top: 10px; font-size: 14px;">
            Signature de réception (Consignee)
        </div>
    </div>
    """


def generate_cga_html(order, shipper_name):
    return f"""
    <div style="font-family: Arial, sans-serif; padding: 30px; background: #fff; color: #000; max-width: 800px; margin: auto;">
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 28px; font-family: 'Times New Roman', serif;">SAINT-EURISTIDE LOGISTICS</h1>
        </div>
        <h2 style="text-align: center; text-decoration: underline; font-size: 16px; margin-bottom: 20px;">CONDITIONS GENERALES D'ACHAT ET DE TRANSPORT</h2>
        <p style="font-size: 10px; text-align: justify; margin-bottom: 30px;">
            Les conditions générales d'achat de Saint-Euristide sont des clauses qui s'appliquent aux expéditions internationales ponctuelles, réalisées par des bons de commande (à l'exclusion des bons de commande passés sur la base d'un accord cadre). L'acceptation de la commande implique de plein droit celle des conditions générales d'achat et le renoncement par le fournisseur à se prévaloir de ses conditions générales de vente. Ces conditions couvrent la commande <b>{order['reference']}</b> liant l'acheteur à <b>{shipper_name}</b>.
        </p>

        <div style="column-count: 2; column-gap: 30px; font-size: 10px; text-align: justify; line-height: 1.4;">
            <p><b>1. CHAMP D'APPLICATION DES PRESENTES CONDITIONS</b><br>
            Les présentes conditions générales d'achat ont pour objet de définir le cadre des relations contractuelles. Le marché prend la forme d'un simple bon de commande établi, ce bon de commande est alors soumis aux présentes conditions générales d'achat.</p>

            <p><b>2. NOTIFICATION</b><br>
            La notification consiste à adresser au fournisseur une copie du bon de commande et de ses éventuelles annexes par voie électronique ou manuscrite.</p>

            <p><b>3. VALIDITE</b><br>
            Toute fourniture de marchandise ou de prestation à Saint-Euristide est subordonnée à une commande régulière et préalable matérialisée par un écrit.</p>

            <p><b>4. NUMERO DE COMMANDE</b><br>
            Le numéro de commande <b>{order['reference']}</b> devra être obligatoirement mentionné sur toutes les correspondances ou documents de livraison, d'expédition et de facturation du fournisseur.</p>

            <p><b>5. DELAIS</b><br>
            Sauf stipulation contraire, les délais s'entendent « marchandise rendue à l'adresse portée sur la commande » (soit Paris CDG). Le transfert des risques est conditionné par l'Incoterm <b>{order['incoterm']}</b> retenu pour cette commande.</p>

            <p><b>6. QUALITE</b><br>
            Sauf indication contraire portée sur les commandes, les normes officielles sont applicables aux prestations qui doivent être effectuées conformément aux règles de l'art. Le fournisseur s'engage à garder les traces écrites et les enregistrements des contrôles, essais et vérifications effectués.</p>

            <p><b>7. PENALITES DE RETARD</b><br>
            Une pénalité de retard est appliquée au fournisseur si celui-ci dépasse le délai d'exécution de la commande, après mise en demeure préalable : 0,4% du montant total HT de la commande par jour ouvré de retard.</p>

            <p><b>8. RESPONSABILITE ENVIRONNEMENTALE</b><br>
            Saint-Euristide attache une grande importance au respect des dispositions en faveur du respect des droits de l'homme et du développement durable lors des opérations de fret.</p>

            <p><b>9. LIVRAISONS ET VOLUMETRIE</b><br>
            Toute livraison de marchandise doit être faite aux heures d'ouverture du service réceptionnaire. Les marchandises voyagent aux périls définis par l'Incoterm <b>{order['incoterm']}</b>. Le volume contractuel engagé pour la présente expédition est de <b>{order['volume']} m3</b>, pour un poids brut de <b>{order['poids_reel']} kg</b>.</p>

            <p><b>10. PRIX</b><br>
            Sauf stipulation contraire, les prix indiqués sur la commande sont fermes et non révisables. Pour les livraisons, les prix s'entendent selon la nomenclature douanière internationale. L'emballage des marchandises livrées devra répondre aux spécifications définies pour le fret aérien international.</p>

            <p><b>11. FACTURES ET PAIEMENT</b><br>
            Les factures doivent être envoyées par courriel en version PDF postérieurement à la livraison de la marchandise. Les paiements au fournisseur sont effectués à 60 jours nets à compter de la date d'émission, conformément à la LME.</p>
        </div>
    </div>
    """


def paper_preview(html: str) -> str:
    """Affiche un document blanc comme une feuille posée sur un fond sombre."""
    return (
        '<!doctype html><html><head><meta charset="utf-8"><style>'
        "html,body{margin:0;background:#232E44}"
        "body{padding:22px 16px}"
        ".sheet{max-width:840px;margin:0 auto;background:#fff;border-radius:4px;box-shadow:0 18px 50px rgba(0,0,0,.5);overflow:hidden}"
        '</style></head><body><div class="sheet">' + html + "</div></body></html>"
    )


def standalone(html: str, title: str) -> str:
    return (
        '<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>' + title + "</title>"
        "<style>body{margin:0;background:#fff}</style></head><body>" + html + "</body></html>"
    )


def document_block(key: str, label: str, html: str, filename: str, height: int = 420) -> None:
    with st.expander(label):
        components.html(paper_preview(html), height=height, scrolling=True)
        st.download_button(
            "Télécharger en HTML",
            data=standalone(html, label),
            file_name=filename,
            mime="text/html",
            key=f"dl_{key}",
        )


# -----------------------------------------------------------------------------
# COMPOSANTS D'AFFICHAGE
# -----------------------------------------------------------------------------
CHECK_SVG = '<svg width="13" height="13" viewBox="0 0 16 16" fill="none"><path d="M3 8.5l3.2 3.2L13 4.8" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def pipeline_html(idx: int) -> str:
    steps = []
    for i, label in enumerate(STATUSES):
        cls = "done" if i < idx else "now" if i == idx else ""
        dot = CHECK_SVG if i < idx else str(i + 1)
        steps.append(f'<div class="pl-step {cls}"><div class="pl-dot">{dot}</div><div class="pl-label">{label}</div></div>')
    return f'<div class="pipeline">{"".join(steps)}</div>'


def ladder_html(rungs, selected_rank: int) -> str:
    out = []
    for rank, code, label, total, delta in rungs:
        cls = "sel" if rank == selected_rank else "off" if rank > selected_rank else ""
        sub = f"<em>+ {eur(delta)}</em>" if delta is not None else ""
        out.append(
            f'<div class="rung {cls}"><div class="rung-code">{code}</div>'
            f'<div class="rung-label">{label}{sub}</div><div class="rung-amt">{eur(total)}</div></div>'
        )
    return f'<div class="ladder">{"".join(out)}</div>'


# -----------------------------------------------------------------------------
# ÉTAT DE SESSION & COMMANDES
# -----------------------------------------------------------------------------
if "orders" not in st.session_state:
    st.session_state.orders = [{
        "reference": "CMD-AIR-10001",
        "origine": "Chine (Pékin - PEK)",
        "incoterm": "CIP",
        "items": [{"nom": "Rétroviseur BUS", "qte": 105, "prix_u": 120, "poids_u": 3.5, "vol_u": 0.03}],
        "poids_reel": 367.5,
        "volume": 3.15,
        "poids_taxable": 525.0,
        "fret_aerien": 1575.0,
        "cout_total_dap": 15000.0,
        "valeur": 12600.0,
        "statut": 0,
        "cree_le": datetime.now() - timedelta(hours=3),
        "docs_generated": False, "carrier_assigned": False,
        "entrepot": "Non assigné", "manutention": "Standard",
    }]

orders = st.session_state.orders


def order_label(o):
    return f"{o['reference']} · {AIRPORTS[o['origine']]['code']} → CDG · {STATUSES[o['statut']]}"


# -----------------------------------------------------------------------------
# EN-TÊTE (rempli en fin de script pour refléter les commandes à jour)
# -----------------------------------------------------------------------------
header_slot = st.empty()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Cotation client",
    "Fournisseur",
    "Suivi de vol",
    "Douane & import",
    "Documents légaux",
])

# -----------------------------------------------------------------------------
# 1. COTATION CLIENT
# -----------------------------------------------------------------------------
with tab1:
    section("Cotation fret aérien", "Catalogue, poids taxable IATA et cascade de coûts par Incoterm.")

    with st.expander("Guide des Incoterms"):
        rows = "".join(f'<tr><td class="mono">{k}</td><td>{v}</td></tr>' for k, v in INCOTERM_INFO.items())
        md(f'<table class="tbl"><thead><tr><th>Incoterm</th><th>Transfert de risques et de frais</th></tr></thead><tbody>{rows}</tbody></table>')

    col_form, col_sum = st.columns([1.45, 1], gap="large")

    with col_form:
        with st.container(key="panel_catalogue"):
            eyebrow("Catalogue de production")
            selected_items = []
            for name, spec in PRODUCTS.items():
                c1, c2 = st.columns([3, 1.2], vertical_alignment="center")
                c1.markdown(
                    f'<div class="prod-name">{name}</div>'
                    f'<div class="prod-spec">{spec["prix"]} € / unité · {spec["poids"]} kg · {spec["vol"]} m³</div>',
                    unsafe_allow_html=True,
                )
                qty = c2.number_input("Quantité", min_value=0, value=0, key=f"qty_{name}", label_visibility="collapsed")
                if qty > 0:
                    selected_items.append({"nom": name, "qte": qty, "prix_u": spec["prix"], "poids_u": spec["poids"], "vol_u": spec["vol"]})

        valeur_marchandise = sum(item["qte"] * item["prix_u"] for item in selected_items)
        poids_reel = sum(item["qte"] * item["poids_u"] for item in selected_items)
        volume_m3 = sum(item["qte"] * item["vol_u"] for item in selected_items)

        with st.container(key="panel_params"):
            eyebrow("Origine et Incoterm")
            p1, p2 = st.columns(2)
            origine = p1.selectbox("Aéroport de départ (fournisseur)", list(AIRPORTS.keys()), index=1)
            incoterm = p2.selectbox("Incoterm cible", list(INCOTERM_INFO.keys()), index=3)

            eyebrow("Poids taxable et tarification")
            poids_volumetrique = volume_m3 * 166.67
            poids_taxable = max(poids_reel, poids_volumetrique)

            st.info(
                f"**Équivalence IATA (1 t = 6 m³)** : {volume_m3:.2f} m³ = {poids_volumetrique:.1f} kg volumétrique.\n\n"
                f"Poids taxable retenu (le plus élevé) : **{poids_taxable:.1f} kg**"
            )

            tarif_normal = AIRPORTS[origine]["tarif"]
            tarif_sup = tarif_normal - 0.25
            seuil_sup = 300

            cout_base = poids_taxable * tarif_normal
            cout_payant_pour = seuil_sup * tarif_sup

            if cout_payant_pour < cout_base and poids_taxable < seuil_sup and poids_taxable > 0:
                cout_fret = cout_payant_pour
                st.success(
                    f"Règle du « payant pour » appliquée : {seuil_sup} kg à {tarif_sup} €/kg ({cout_payant_pour:.2f} €) "
                    f"coûte moins que {poids_taxable:.0f} kg à {tarif_normal} €/kg ({cout_base:.2f} €)."
                )
            else:
                cout_fret = cout_base
                st.write(f"Coût du fret appliqué : {poids_taxable:.0f} kg × {tarif_normal} €/kg = **{cout_fret:.2f} €**")

        frais_pre_t = 100
        frais_douane_exp = 65
        thc_dep = 70
        surcharges_compagnie = poids_taxable * (0.85 + 0.15 + 0.05)
        assurance = 130
        taxes_supp = 65
        thc_arr = 55
        post_acheminement = 120

        val_fca = valeur_marchandise + frais_pre_t + frais_douane_exp + thc_dep
        val_cip = val_fca + cout_fret + surcharges_compagnie + assurance
        val_dap = val_cip + taxes_supp + thc_arr + post_acheminement

        if st.button("Valider la cotation et commander", type="primary"):
            if not selected_items:
                st.error("Ajoutez au moins un article pour valider la commande.")
            else:
                ref = f"CMD-AIR-{random.randint(10000, 99999)}"
                orders.append({
                    "reference": ref, "origine": origine, "incoterm": incoterm, "items": selected_items,
                    "poids_reel": poids_reel, "volume": volume_m3, "poids_taxable": poids_taxable,
                    "fret_aerien": cout_fret + surcharges_compagnie, "cout_total_dap": val_dap,
                    "valeur": valeur_marchandise, "statut": 0, "cree_le": datetime.now(),
                    "docs_generated": False, "carrier_assigned": False,
                    "entrepot": "Non assigné", "manutention": "Standard",
                })
                st.success(f"Commande {ref} enregistrée.")

    with col_sum:
        with st.container(key="panel_cascade"):
            eyebrow("Cascade des coûts")
            rungs = [
                (1, "EXW", "Valeur de la marchandise", valeur_marchandise, None),
                (2, "FCA", "Pré-acheminement, douane export, THC départ", val_fca, val_fca - valeur_marchandise),
                (3, "CPT / CIP", "Fret aérien, surcharges, assurance", val_cip, val_cip - val_fca),
                (4, "DAP", "Taxes, THC arrivée, post-acheminement", val_dap, val_dap - val_cip),
            ]
            md(ladder_html(rungs, INCOTERM_RANK[incoterm]))
            if incoterm == "DDP":
                md('<div class="note">DDP : les droits et la TVA à l\'import ne sont pas inclus dans cette cotation. Voir l\'onglet Douane & import.</div>')

        with st.container(key="panel_kpi"):
            eyebrow("Indicateurs logistiques")
            kpis = []
            if valeur_marchandise > 0:
                kpis.append(("Coût logistique", f"{((val_cip - valeur_marchandise) / valeur_marchandise) * 100:.1f} %", "CIP rapporté à l'EXW"))
            kpis += [
                ("Délai estimé", "4 à 6 jours", "porte à porte"),
                ("Taux d'avarie", "3 %", "standard"),
                ("Bilan carbone", f"{0.45 * (poids_taxable / 1000):.2f} kg", "CO2 estimé"),
            ]
            md(stats(kpis))

# -----------------------------------------------------------------------------
# 2. FOURNISSEUR
# -----------------------------------------------------------------------------
with tab2:
    section("Traitement fournisseur", "Préparation, dépôt, remise au transporteur et clôture, étape par étape.")

    if not orders:
        st.warning("Aucune commande à traiter.")
    else:
        col_sel_ord, col_del_ord = st.columns([4, 1], vertical_alignment="bottom")
        with col_sel_ord:
            idx = st.selectbox("Commande à traiter", range(len(orders)), format_func=lambda i: order_label(orders[i]), key="provider_order_sel")
        with col_del_ord:
            if st.button("Supprimer", key=f"del_btn_{idx}", help="Supprimer cette commande de la liste"):
                if len(orders) > 1:
                    removed = orders.pop(idx)
                    st.success(f"Commande {removed['reference']} supprimée.")
                    st.rerun()
                else:
                    st.error("Impossible de supprimer la dernière commande active.")

        if idx >= len(orders):
            idx = len(orders) - 1

        o = orders[idx]
        a = AIRPORTS[o["origine"]]

        md(pipeline_html(o["statut"]))

        col_action1, col_action2, col_action3 = st.columns(3, gap="medium")
        with col_action1:
            with st.container(key="panel_prep"):
                eyebrow("1. Préparation")
                if o["statut"] == 0:
                    st.write("Les documents d'expédition n'ont pas encore été générés.")
                    if st.button("Valider et générer les documents", key=f"btn_gen_{idx}"):
                        o["docs_generated"] = True
                        o["statut"] = 1
                        st.rerun()
                else:
                    st.success("Documents générés")

        with col_action2:
            with st.container(key="panel_depot"):
                eyebrow("2. Logistique et dépôt")
                if o["statut"] == 0:
                    st.write("En attente de la génération des documents.")
                elif o["statut"] == 1:
                    choix_entrepot = st.selectbox("Entrepôt de départ", [
                        "Entrepôt Central Nord (Zone A)",
                        "Hub Logistique International Cargo (Zone B)",
                        "Terminal Express Cargo Fret",
                    ], key=f"ent_{idx}")
                    choix_manutention = st.radio("Manutention au dépôt", [
                        "Palette Standard ULD (Filmée + Cerclée)",
                        "Conteneur Sécurisé Haute Valeur",
                        "Colisage Express Renforcé",
                    ], key=f"man_{idx}")
                    if st.button("Valider l'affectation au dépôt", key=f"btn_dep_{idx}"):
                        o["entrepot"] = choix_entrepot
                        o["manutention"] = choix_manutention
                        o["statut"] = 2
                        st.rerun()
                elif o["statut"] == 2:
                    st.info(f"**Entrepôt** : {o.get('entrepot', 'Standard')}\n\n**Manutention** : {o.get('manutention', 'Standard')}")
                    if st.button("Remettre au transporteur aérien", key=f"btn_trans_{idx}"):
                        o["carrier_assigned"] = True
                        o["transporteur"] = "Air Cargo Express"
                        o["statut"] = 3
                        st.rerun()
                else:
                    st.success("Affecté à l'entrepôt et remis au transporteur")

        with col_action3:
            with st.container(key="panel_close"):
                eyebrow("3. Suivi et clôture")
                if o["statut"] < 3:
                    st.write("En attente de la remise au transporteur.")
                elif o["statut"] == 3:
                    if st.button("Autoriser le décollage", key=f"btn_dec_{idx}"):
                        o["statut"] = 4
                        st.rerun()
                elif o["statut"] == 4:
                    if st.button("Confirmer l'atterrissage", key=f"btn_att_{idx}"):
                        o["statut"] = 5
                        st.rerun()
                elif o["statut"] == 5:
                    if st.button("Confirmer la livraison", key=f"btn_liv_{idx}"):
                        o["statut"] = 6
                        st.rerun()
                else:
                    st.success("Processus logistique terminé")

        if o.get("docs_generated"):
            st.write("")
            section(f"Récapitulatif interne · {o['reference']}")

            lignes_articles_txt = "\n".join([f"- {item['nom']} (x{item['qte']})" for item in o['items']])
            facture_txt = f"""======================================================
FACTURE PROFORMA / COTATION LOGISTIQUE
======================================================
Référence Commande : {o['reference']}
Incoterm Convenu   : {o['incoterm']}
Départ             : {a['ville']} ({a['code']})
Destination        : Paris (CDG)
Entrepôt Affecté   : {o.get('entrepot', 'N/A')}
Manutention        : {o.get('manutention', 'N/A')}

--- CONTENU ---
{lignes_articles_txt}

--- DONNÉES D'EXPÉDITION ---
Poids Réel Brut    : {o['poids_reel']} kg
Volume Total       : {o['volume']:.2f} m3
Poids Taxable      : {o['poids_taxable']:.1f} kg

--- DÉTAIL TARIFAIRE ---
Valeur Marchandise (EXW) : {o['valeur']:.2f} EUR
Frais de Fret Aérien     : {o['fret_aerien']:.2f} EUR
Coût Total Estimé (DAP)  : {o['cout_total_dap']:.2f} EUR
======================================================"""

            st.text_area("Aperçu du document de travail", facture_txt, height=250, key=f"txt_area_{idx}")
            st.download_button("Télécharger le récapitulatif (.txt)", data=facture_txt, file_name=f"Recap_{o['reference']}.txt", mime="text/plain", key=f"dl_recap_{idx}")

        st.write("")
        section("Registre des commandes")
        df = pd.DataFrame([
            {
                "Référence": x["reference"],
                "Origine": AIRPORTS[x["origine"]]["code"],
                "Incoterm": x["incoterm"],
                "Pièces": sum(i["qte"] for i in x["items"]),
                "Poids taxable (kg)": round(x["poids_taxable"], 1),
                "Valeur (EUR)": round(x["valeur"], 2),
                "Statut": STATUSES[x["statut"]],
            }
            for x in orders
        ])
        st.dataframe(df, hide_index=True)

# -----------------------------------------------------------------------------
# 3. SUIVI DE VOL ET CARBURANT
# -----------------------------------------------------------------------------
with tab3:
    section("Suivi de vol et carburant", "Trajet orthodromique avec contournement des zones interdites, flotte annexe et indicateurs de bord.")
    if not orders:
        st.warning("Aucune commande à suivre pour le moment.")
    else:
        idx = st.selectbox("Commande à suivre", range(len(orders)), format_func=lambda i: order_label(orders[i]), key="tracking_order_sel")
        o = orders[idx]
        a = AIRPORTS[o["origine"]]
        route, km = build_route(a, CDG)

        flight_num = f"FDX-{stable_int(o['reference'], 900, 100)}"

        total_conso_estimee = km * 11.5 + (o["poids_taxable"] * 0.15)
        carburant_depart = total_conso_estimee * 1.35

        progress_val = st.slider("Progression simulée du vol (indicateurs carburant)", 0.0, 1.0, 0.0, 0.01, key=f"prog_{idx}")

        carburant_consomme_actuel = total_conso_estimee * progress_val
        carburant_restant_actuel = carburant_depart - carburant_consomme_actuel

        md(stats([
            ("Distance totale", f"{num(km)} km", f"{a['code']} → CDG"),
            ("Carburant embarqué", f"{num(carburant_depart)} kg", "réserve de 35 % incluse"),
            ("Carburant consommé", f"{num(carburant_consomme_actuel)} kg", f"{progress_val * 100:.0f} % du vol"),
            ("Kérosène restant", f"{num(carburant_restant_actuel)} kg", "à l'instant simulé"),
        ]))
        st.write("")

        c1, c2 = st.columns([4, 1], vertical_alignment="center")
        with c1:
            md(
                f'<div class="banner"><span class="path">{a["code"]} → CDG</span>'
                f'<span class="city">{a["ville"]} vers Paris</span>'
                f'<span class="chip accent mono">{flight_num}</span></div>'
            )
        style_name = c2.selectbox("Fond de carte", ["Clair", "Sombre"], key=f"style_sel_{idx}", label_visibility="collapsed")
        st.caption("Le curseur pilote les indicateurs carburant. La carte a sa propre lecture : bouton Lancer, vitesse ×0,5 à ×8.")

        if o["statut"] < FLIGHT_STEP:
            st.warning("L'avion n'a pas encore décollé : prévisualisation du trajet.")

        start = 1.0 if o["statut"] > FLIGHT_STEP else 0.0
        render_flight_map(route, a, CDG, start, style_name, flight_num)

# -----------------------------------------------------------------------------
# 4. DOUANE ET IMPORT
# -----------------------------------------------------------------------------
with tab4:
    section("Douane et analyse fiscale", "Estimation des droits et de la TVA à l'importation à Paris CDG.")
    if not orders:
        st.warning("Aucune commande enregistrée.")
    else:
        idx_d = st.selectbox("Commande à analyser", range(len(orders)), format_func=lambda i: order_label(orders[i]), key="dou_sel")
        o_d = orders[idx_d]
        a_d = AIRPORTS[o_d["origine"]]

        base_douane = o_d["valeur"] + o_d["fret_aerien"]
        dd = base_douane * 0.04
        base_tva = base_douane + dd
        tva = base_tva * 0.20

        md(stats([
            ("Incoterm", o_d["incoterm"], f"{a_d['ville']} ({a_d['code']})"),
            ("Droits de douane", eur(dd), "taux indicatif 4 %"),
            ("TVA à l'importation", eur(tva), "taux 20 %"),
            ("Total à régler", eur(dd + tva), "droits + TVA"),
        ]))
        st.write("")
        with st.container(key="panel_douane"):
            eyebrow("Détail du calcul")
            md(
                '<table class="tbl"><thead><tr><th>Ligne</th><th class="num">Montant</th></tr></thead><tbody>'
                f'<tr><td>Valeur de la marchandise</td><td class="num">{eur(o_d["valeur"])}</td></tr>'
                f'<tr><td>Fret aérien et surcharges</td><td class="num">{eur(o_d["fret_aerien"])}</td></tr>'
                f'<tr><td>Base douanière</td><td class="num">{eur(base_douane)}</td></tr>'
                f'<tr><td>Droits de douane (4 %)</td><td class="num">{eur(dd)}</td></tr>'
                f'<tr><td>Base TVA (base douanière + droits)</td><td class="num">{eur(base_tva)}</td></tr>'
                f'<tr><td>TVA à l\'importation (20 %)</td><td class="num">{eur(tva)}</td></tr>'
                f'<tr class="total"><td>Total droits et taxes</td><td class="num">{eur(dd + tva)}</td></tr>'
                "</tbody></table>"
            )
        st.caption("Les documents légaux (AWB, DAU, CGA, conformité) sont dans l'onglet Documents légaux.")

# -----------------------------------------------------------------------------
# 5. DOCUMENTS LÉGAUX
# -----------------------------------------------------------------------------
with tab5:
    section("Documents légaux et conformité", "Aperçu et téléchargement des documents générés à partir de la commande.")

    if not orders:
        st.warning("Aucune commande enregistrée pour générer les documents.")
    else:
        idx_l = st.selectbox("Commande à documenter", range(len(orders)), format_func=lambda i: order_label(orders[i]), key="leg_sel")
        o_l = orders[idx_l]
        a_l = AIRPORTS[o_l["origine"]]
        shipper_name = COMPANY_MAP.get(o_l["origine"], "AUTOMOTIVE MIRRORS MFG")
        flight_code = f"FDX-{stable_int(o_l['reference'], 900, 100)}"
        ref = o_l["reference"]

        col_ob, col_fac = st.columns(2, gap="large")

        with col_ob:
            eyebrow("Documents obligatoires")
            document_block("pack", "Fiche de colisage (Packing List)", generate_packing_list_html(o_l, a_l, shipper_name), f"Fiche_Colisage_{ref}.html", 400)
            document_block("awb", "Lettre de transport aérien (AWB)", generate_awb_html(o_l, a_l, shipper_name, flight_code), f"AWB_{ref}.html", 350)
            document_block("dau", "Déclaration en douane (DAU)", generate_dau_html(o_l, a_l, shipper_name), f"DAU_{ref}.html", 350)

        with col_fac:
            eyebrow("Documents facultatifs")
            document_block("ce", "Déclaration de conformité (CE)", generate_ce_html(o_l, shipper_name, a_l), f"Conformite_{ref}.html", 420)
            document_block("ass", "Attestation d'assurance", generate_assurance_html(o_l, shipper_name), f"Assurance_{ref}.html", 420)
            document_block("pod", "Preuve de livraison (POD)", generate_pod_html(o_l, shipper_name), f"POD_{ref}.html", 420)
            document_block("cga", "Conditions générales (CGA)", generate_cga_html(o_l, shipper_name), f"CGA_{ref}.html", 420)

# -----------------------------------------------------------------------------
# EN-TÊTE : rempli ici pour compter les commandes après toutes les actions
# -----------------------------------------------------------------------------
n_total = len(orders)
n_flight = sum(1 for x in orders if x["statut"] == FLIGHT_STEP)
n_done = sum(1 for x in orders if x["statut"] == len(STATUSES) - 1)

PLANE_MARK = (
    '<svg width="22" height="22" viewBox="0 0 64 64"><path d="M32 2 L37 22 L60 36 L60 42 L37 36 L36 52 L44 58 L44 62 L32 59 '
    'L20 62 L20 58 L28 52 L27 36 L4 42 L4 36 L27 22 Z" fill="#FF7A00"/></svg>'
)
header_slot.markdown(
    '<div class="topbar"><div class="brand"><div class="brand-mark">' + PLANE_MARK + "</div>"
    '<div><div class="brand-name">Air Cargo Hub</div>'
    '<div class="brand-sub">Chaîne fret aérien · Chine et États-Unis vers Paris CDG</div></div></div>'
    '<div class="tb-stats">'
    f'<div class="tb-stat"><b>{n_total}</b><span>Commandes</span></div>'
    f'<div class="tb-stat"><b>{n_flight}</b><span>En vol</span></div>'
    f'<div class="tb-stat"><b>{n_done}</b><span>Livrées</span></div>'
    "</div></div>",
    unsafe_allow_html=True,
)
