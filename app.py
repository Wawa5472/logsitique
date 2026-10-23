"""
Air Cargo Hub — Logistique internationale
Interface intégrale : Devis détaillé, Fournisseur complet, Suivi 3D (vitesse restaurée), 
Douane, et Gestion Documentaire Légale Totale (Obligatoire + Facultatif en HTML).

Lancer :  pip install streamlit pandas
          streamlit run app.py
"""

import base64
import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# CONFIG PAGE + DESIGN DIRECTION ARTISTIQUE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Air Cargo Hub",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .hero-header {
        background: linear-gradient(135deg, #0B1B2E 0%, #1A4D7C 100%);
        color: white; padding: 2rem 2.5rem; border-radius: 16px;
        margin-bottom: 1.5rem; box-shadow: 0 10px 30px rgba(11,27,46,0.15);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .hero-header h1 { color:#fff !important; margin:0; font-size:2.2rem; font-weight:800; letter-spacing: -0.5px; }
    .hero-header p  { color:#B0C4DE; margin:.5rem 0 0; font-size:1.05rem; font-weight: 400; }

    .doc-card { background: #ffffff; border-left: 5px solid #FF7A00; border-radius: 10px; padding: 1.2rem 1.5rem; margin-bottom: 1rem; color: #1e293b; box-shadow: 0 4px 16px rgba(0,0,0,0.04); border: 1px solid #f1f5f9; }
    .badge-warning { background: #FEF2F2; color: #DC2626; padding: 12px 16px; border-radius: 10px; border: 1px solid #FEE2E2; font-weight: 500; margin-top: 10px; font-size: 0.9rem; }
    .badge-success { background: #F0FDF4; color: #16A34A; padding: 12px 16px; border-radius: 10px; border: 1px solid #DCFCE7; font-weight: 600; font-size: 0.9rem; }
        
    .step { display: inline-block; padding: 6px 14px; border-radius: 999px; font-size: .85rem; margin: 4px 6px 4px 0; border: 1px solid #E2E8F0; color: #64748B; background: #F8FAFC; font-weight: 500; }
    .step.done { background: #F0FDF4; color: #16A34A; border-color: #BBF7D0; font-weight: 600; }
    .step.now  { background: #FF7A00; color: #fff; border-color: #FF7A00; font-weight: 700; box-shadow: 0 4px 12px rgba(255,122,0,0.3); }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

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

STATUSES = ["Commande reçue", "Documents générés", "Au dépôt de départ", "Remis au transporteur", "En vol vers CDG", "Atterri à CDG", "Livré / dédouané"]
FLIGHT_STEP = 4

PRODUCTS = {
    "Rétroviseur Voiture": {"prix": 45, "poids": 1.2, "vol": 0.01},
    "Rétroviseur BUS": {"prix": 120, "poids": 3.5, "vol": 0.03},
    "Rétroviseur Camion": {"prix": 95, "poids": 2.8, "vol": 0.02},
    "Rétroviseur Engins de chantier": {"prix": 150, "poids": 4.5, "vol": 0.04},
    "Rétroviseur Caméra (High-Tech)": {"prix": 250, "poids": 1.5, "vol": 0.008},
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
    if d == 0: return [list(p1)]
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
# CARTE MAPLIBRE + DECK.GL (AVEC SÉLECTEUR DE VITESSE RESTAURÉ)
# -----------------------------------------------------------------------------
MAP_HTML = r"""
<!doctype html><html><head><meta charset="utf-8">
<link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet">
<script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
<script src="https://unpkg.com/deck.gl@8.9.33/dist.min.js"></script>
<style>
 html,body{margin:0;height:100%;font-family:Inter,sans-serif;background:#0b1b2e}
 #map{position:absolute;inset:0}
 .hud{position:absolute;left:14px;right:14px;bottom:14px;background:rgba(10,25,45,.92);color:#fff;
   border-radius:16px;padding:12px 16px;backdrop-filter:blur(10px);box-shadow:0 6px 24px rgba(0,0,0,.35)}
 .row{display:flex;gap:18px;flex-wrap:wrap;align-items:center;justify-content:space-between}
 .kpi{min-width:92px}.kpi b{display:block;font-size:1.2rem}.kpi span{font-size:.7rem;opacity:.65;text-transform:uppercase}
 .bar{height:8px;background:rgba(255,255,255,.18);border-radius:99px;margin:10px 0 8px;overflow:hidden}
 .bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,#FF7A00,#FFC04D);border-radius:99px}
 button,select{background:#FF7A00;color:#fff;border:0;border-radius:10px;padding:8px 13px;font-weight:600;cursor:pointer;font-size:.85rem}
 button.alt,select{background:rgba(255,255,255,.14)}
 select option{color:#000}
 .flight-card { position:absolute;top:14px;left:14px;background:rgba(10,25,45,.92);color:#fff;border-radius:10px;overflow:hidden;width:220px;z-index:2;border:1px solid rgba(255,255,255,.1);backdrop-filter:blur(10px)}
 .flight-card img { width:100%;height:95px;object-fit:cover;display:block;border-bottom:2px solid #FF7A00 }
 .flight-card-body { padding:10px 12px }
 .flight-card-header { display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;border-bottom:1px solid rgba(255,255,255,.15);padding-bottom:6px}
 .flight-card-header h2 { margin:0;font-size:1.1rem;color:#FF7A00 }
 .flight-card-header span { font-size:0.7rem;opacity:0.9 }
 .flight-route { display:flex;justify-content:space-between;align-items:center;margin-top:4px }
 .route-point { text-align:center }
 .route-point b { display:block;font-size:1.1rem }
 .route-point span { font-size:0.65rem;opacity:0.7 }
 .route-arrow { color:#FF7A00;font-size:1.1rem;opacity:0.8 }
 .lbl{background:#fff;color:#0E2A47;font-weight:700;font-size:11px;padding:3px 8px;border-radius:99px;white-space:nowrap}
 .lbl.red{background:#C62828;color:#fff}.lbl.green{background:#2E7D32;color:#fff}
 .fl{font-size:10px;font-weight:600;color:#37474f;text-align:center;white-space:nowrap;text-shadow:0 0 3px #fff}
</style></head><body>
<div id="map"></div><div class="flight-card" id="flight-card"></div>
<div class="hud">
  <div class="row">
    <div class="kpi"><b id="k_alt">0 m</b><span>Altitude</span></div>
    <div class="kpi"><b id="k_spd">0 km/h</b><span>Vitesse</span></div>
    <div class="kpi"><b id="k_dist">0 km</b><span>Restant</span></div>
    <div class="kpi"><b id="k_pct">0 %</b><span>Progression</span></div>
    <div class="row">
      <button id="b_play">▶ Lancer</button>
      <button class="alt" id="b_cam">🎥 Caméra</button>
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
document.getElementById('flight-card').innerHTML=`${D.photo?`<img src="${D.photo}">`:''}<div class="flight-card-body"><div class="flight-card-header"><h2>${D.flight_num}</h2><span>${D.plane_model}</span></div><div class="flight-route"><div class="route-point"><b>${D.origin.code}</b><span>${D.origin.ville}</span></div><div class="route-arrow">✈</div><div class="route-point"><b>${D.dest.code}</b><span>${D.dest.ville}</span></div></div></div>`;
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
  map.addSource('plan',{type:'geojson',data:{type:'Feature',geometry:{type:'LineString',coordinates:D.route}}});
  map.addLayer({id:'plan',type:'line',source:'plan',paint:{'line-color':'#90A4AE','line-width':3,'line-dasharray':[1.5,2.5]}});
  map.addSource('trail',{type:'geojson',data:{type:'Feature',geometry:{type:'LineString',coordinates:[D.route[0],D.route[0]]}}});
  map.addLayer({id:'trail',type:'line',source:'trail',paint:{'line-color':'#FF5A00','line-width':5}});
  lab(D.origin.code,'red',[D.origin.lon,D.origin.lat]); lab(D.dest.code,'green',[D.dest.lon,D.dest.lat]);
  
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
  if(playing){ t+=dt*mult/70; if(t>=1){t=1;playing=false;b_play.textContent='↺ Rejouer';} update(t); }
  
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

b_play.onclick=()=>{if(t>=1){t=0;curB=at(main,0).b;}playing=!playing;b_play.textContent=playing?'⏸ Pause':'▶ Reprendre';if(playing&&follow)map.easeTo({pitch:55,zoom:4.2,duration:1200});};
b_cam.onclick=()=>{follow=!follow;b_cam.textContent='🎥 Caméra : '+(follow?'suivi':'libre');if(!follow)map.easeTo({pitch:35,bearing:-8,zoom:2.6,duration:1200});};
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
    style = {"Clair": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json", "Sombre": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"}[style_name]
    model_data, _ = load_plane_model()
    photo_b64 = load_fedex_image()
    fleet = [{"code": c, "pts": great_circle(a, b, 150), "speed": s, "phase": ph} for c, a, b, s, ph in FLEET]
    
    data = {
        "model": model_data, "photo": photo_b64, "flight_num": flight_num, "plane_model": "Boeing 777F", 
        "route": route, "origin": origin, "dest": dest, "fleet": fleet, "style": style, 
        "start": start_progress, "center": [(origin["lon"] + dest["lon"]) / 2, (origin["lat"] + dest["lat"]) / 2]
    }
    components.html(MAP_HTML.replace("__DATA__", json.dumps(data)), height=height, scrolling=False)


# -----------------------------------------------------------------------------
# GÉNÉRATEURS DE DOCUMENTS HTML (OBLIGATOIRES)
# -----------------------------------------------------------------------------
def generate_packing_list_html(order, airport, shipper_name):
    rows = ""
    for idx, item in enumerate(order["items"], 1):
        rows += f"""<tr><td style="border: 1px solid #000; padding: 5px;">{idx}</td><td style="border: 1px solid #000; padding: 5px;">{item['nom']}</td><td style="border: 1px solid #000; padding: 5px;">Unité</td><td style="border: 1px solid #000; padding: 5px;">{item['qte']}</td><td style="border: 1px solid #000; padding: 5px;">-</td></tr>"""
    return f"""<div style="font-family: Arial, sans-serif; padding: 30px; background: #fff; color: #000; max-width: 800px; margin: auto;"><div style="display: flex; justify-content: space-between; margin-bottom: 30px;"><div><h2 style="margin: 0 0 10px 0;">{shipper_name}</h2><div>Aéroport de {airport['ville']}</div><div>Code IATA: {airport['code']}</div></div><div style="text-align: right;"><h1 style="margin: 0; font-size: 24px;">Fiche de colisage</h1><div style="font-size: 12px; color: #555;">(Ceci n'est pas une facture)</div></div></div><table style="width: 100%; margin-bottom: 30px; font-size: 14px;"><tr><td style="width: 50%;"><b>Date :</b> {order['cree_le'].strftime("%d/%m/%Y")}</td><td style="width: 50%;"><b>Numéro commande :</b> {order['reference']}</td></tr></table><table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;"><thead><tr style="background-color: #f2f2f2;"><th style="border: 2px solid #000; padding: 8px;">Partie #</th><th style="border: 2px solid #000; padding: 8px;">Désignation</th><th style="border: 2px solid #000; padding: 8px;">Type d'unité</th><th style="border: 2px solid #000; padding: 8px;">Quantité</th><th style="border: 2px solid #000; padding: 8px;">Reste</th></tr></thead><tbody>{rows}</tbody></table></div>"""

def generate_awb_html(order, airport, shipper_name, flight_code):
    awb_num = f"057-{abs(hash(order['reference'])) % 9000000 + 1000000}"
    return f"""<div style="font-family: Arial, sans-serif; padding: 20px; background: #fff; color: #000; max-width: 800px; margin: auto; font-size: 10px;"><div style="border: 2px solid #000;"><div style="display: flex; border-bottom: 2px solid #000;"><div style="width: 50%; border-right: 2px solid #000; padding: 5px;"><b>Shipper's Name</b><br><br>{shipper_name}<br>{airport['ville']}</div><div style="width: 50%; padding: 5px;"><b>AWB Number</b><br><br><span style="font-size: 16px; font-weight: bold;">{awb_num}</span></div></div><table style="width: 100%; border-collapse: collapse; text-align: center; font-size: 9px; margin-top: 10px;"><tr style="border-bottom: 1px solid #000; border-top: 2px solid #000;"><th style="border-right: 1px solid #000; padding: 4px;">Pieces</th><th style="border-right: 1px solid #000; padding: 4px;">Gross Weight</th><th style="border-right: 1px solid #000; padding: 4px;">Chargeable Weight</th><th style="padding: 4px;">Nature of Goods</th></tr><tr style="height: 100px; vertical-align: top;"><td style="border-right: 1px solid #000;">{sum(i['qte'] for i in order['items'])}</td><td style="border-right: 1px solid #000;">{order['poids_reel']}</td><td style="border-right: 1px solid #000;">{order['poids_taxable']}</td><td style="text-align: left; padding: 5px;">Auto Parts<br>Incoterm: {order['incoterm']}</td></tr></table></div></div>"""

def generate_dau_html(order, airport, shipper_name):
    return f"""<div style="font-family: Arial, sans-serif; padding: 10px; background: #fff; color: #000; max-width: 800px; margin: auto; font-size: 9px; border: 1px solid #ccc;"><div style="display: flex; border-bottom: 2px solid #000; padding-bottom: 5px;"><div style="width: 50%; font-size: 14px; font-weight: bold;">COMMUNAUTE EUROPEENNE</div><div style="width: 25%; border: 1px solid #000; padding: 2px;">1 DECLARATION<br><b>IM / A</b></div></div><div style="display: flex; border: 2px solid #000; margin-top: 5px;"><div style="width: 50%; border-right: 2px solid #000;"><div style="border-bottom: 1px solid #000; padding: 5px; height: 50px;">2 Expéditeur<br><b>{shipper_name}<br>{airport['ville']}</b></div><div style="border-bottom: 1px solid #000; padding: 5px; height: 50px;">8 Destinataire<br><b>SAINT-EURISTIDE LOGISTICS</b></div></div><div style="width: 50%;"><div style="border-bottom: 1px solid #000; padding: 5px;">31 Colis<br><b>{sum(i['qte'] for i in order['items'])} Colis</b><br>Poids brut: {order['poids_reel']} kg</div><div style="padding: 5px;">46 Valeur Statistique<br><b>{order['valeur'] + order['fret_aerien']:.2f} EUR</b></div></div></div></div>"""


# -----------------------------------------------------------------------------
# GÉNÉRATEURS DE DOCUMENTS HTML (FACULTATIFS - NOUVEAUX)
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
    policy_num = f"029.880.{abs(hash(order['reference'])) % 900 + 100}"
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
            Marseille, le {order['cree_le'].strftime("%d %B %Y")}.<br><br>
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
        "entrepot": "Non assigné", "manutention": "Standard"
    }]

orders = st.session_state.orders

def order_label(o): return f"{o['reference']} · {AIRPORTS[o['origine']]['code']}→CDG · {STATUSES[o['statut']]}"
def stepper(idx):
    html = "".join([f'<span class="step {"done" if i < idx else "now" if i == idx else ""}">{s}</span>' for i, s in enumerate(STATUSES)])
    st.markdown(html, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# EN-TÊTE + NAVIGATION PAR ONGLETS (5 ONGLETS)
# -----------------------------------------------------------------------------
st.markdown("""<div class="hero-header"><h1>✈️ Air Cargo Hub — Logistique internationale</h1><p>Cotation, Fournisseur, Suivi 3D & Légal (AWB, DAU, CGA, Conformité).</p></div>""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🛒 1. Client (Devis & Catalogue)", 
    "🏭 2. Fournisseur (Expédition)", 
    "🌍 3. Suivi Vol & Carburant",
    "🛃 4. Douane & Import",
    "⚖️ 5. Légal & Conformité (Docs)"
])

# -----------------------------------------------------------------------------
# 1. ESPACE CLIENT (Intégral)
# -----------------------------------------------------------------------------
with tab1:
    st.subheader("Cotation Fret Aérien & Catalogue d'articles")
    
    with st.expander("📚 Guide complet des Incoterms (Transfert de risques et de frais)"):
        for inc, desc in INCOTERM_INFO.items():
            st.markdown(f"- **{inc}** : {desc}")

    col_form, col_sum = st.columns([1.5, 1])

    with col_form:
        st.markdown("#### 📦 Sélection des Rétroviseurs (Production)")
        selected_items = []
        for name, spec in PRODUCTS.items():
            c1, c2 = st.columns([3, 1])
            qty = c2.number_input(f"Quantité", min_value=0, value=0, key=f"qty_{name}", label_visibility="collapsed")
            c1.markdown(f"**{name}** — {spec['prix']}€ / unité ({spec['poids']} kg, {spec['vol']} m³)")
            if qty > 0:
                selected_items.append({"nom": name, "qte": qty, "prix_u": spec['prix'], "poids_u": spec['poids'], "vol_u": spec['vol']})
        
        valeur_marchandise = sum(item["qte"] * item["prix_u"] for item in selected_items)
        poids_reel = sum(item["qte"] * item["poids_u"] for item in selected_items)
        volume_m3 = sum(item["qte"] * item["vol_u"] for item in selected_items)

        st.markdown("#### 📍 Origine & Incoterm")
        origine = st.selectbox("Aéroport de départ (Fournisseur)", list(AIRPORTS.keys()), index=1)
        incoterm = st.selectbox("Incoterm cible", list(INCOTERM_INFO.keys()), index=3)

        st.markdown("#### ⚖️ Règle Poids/Volume & Tarification")
        poids_volumetrique = volume_m3 * 166.67
        poids_taxable = max(poids_reel, poids_volumetrique)
        
        st.info(f"**Équivalence IATA (1T = 6m³)** : Volume de {volume_m3:.2f} m³ = {poids_volumetrique:.1f} kg volumétrique.\n\n"
                f"Poids taxable retenu (le plus élevé) : **{poids_taxable:.1f} kg**")

        tarif_normal = AIRPORTS[origine]["tarif"]
        tarif_sup = tarif_normal - 0.25
        seuil_sup = 300

        cout_base = poids_taxable * tarif_normal
        cout_payant_pour = seuil_sup * tarif_sup

        if cout_payant_pour < cout_base and poids_taxable < seuil_sup and poids_taxable > 0:
            cout_fret = cout_payant_pour
            st.success(f"✅ Règle du 'Payant Pour' appliquée : Taxation à {seuil_sup}kg au tarif de {tarif_sup}€/kg ({cout_payant_pour}€) est plus avantageuse que {poids_taxable:.0f}kg à {tarif_normal}€/kg ({cout_base}€).")
        else:
            cout_fret = cout_base
            st.write(f"Coût du fret appliqué : {poids_taxable:.0f} kg x {tarif_normal} €/kg = **{cout_fret:.2f} €**")

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

        if st.button("🚀 Valider la cotation et commander", use_container_width=True, type="primary"):
            if not selected_items:
                st.error("Veuillez ajouter au moins un article pour valider la commande.")
            else:
                ref = f"CMD-AIR-{random.randint(10000, 99999)}"
                orders.append({
                    "reference": ref, "origine": origine, "incoterm": incoterm, "items": selected_items,
                    "poids_reel": poids_reel, "volume": volume_m3, "poids_taxable": poids_taxable,
                    "fret_aerien": cout_fret + surcharges_compagnie, "cout_total_dap": val_dap,
                    "valeur": valeur_marchandise, "statut": 0, "cree_le": datetime.now(),
                    "docs_generated": False, "carrier_assigned": False,
                    "entrepot": "Non assigné", "manutention": "Standard"
                })
                st.success(f"Commande {ref} enregistrée avec succès !")

    with col_sum:
        st.markdown("#### 📈 Détail de la Cotation (Cascade)")
        st.metric("1. EXW (Valeur Marchandise)", f"{valeur_marchandise:.2f} €")
        if incoterm in ["FCA", "CPT", "CIP", "DAP", "DPU", "DDP"]:
            st.metric("2. FCA (Aéroport de départ)", f"{val_fca:.2f} €", delta=f"+ {val_fca - valeur_marchandise:.2f} € Frais annexes")
        if incoterm in ["CPT", "CIP", "DAP", "DPU", "DDP"]:
            st.metric("3. CIP/CPT (Paris CDG)", f"{val_cip:.2f} €", delta=f"+ {cout_fret + surcharges_compagnie + assurance:.2f} € Fret, Surcharges & Ass.")
        if incoterm in ["DAP", "DPU", "DDP"]:
            st.metric("4. DAP (Livré final)", f"{val_dap:.2f} €", delta=f"+ {val_dap - val_cip:.2f} € THC & Post-acheminement")

        st.markdown("#### 📊 KPIs Logistiques")
        if valeur_marchandise > 0:
            cout_logistique_pct = ((val_cip - valeur_marchandise) / valeur_marchandise) * 100
            st.write(f"- **Coût logistique (CIP/EXW)** : {cout_logistique_pct:.2f}%")
        bilan_carbone = 0.45 * (poids_taxable / 1000)
        st.write("- **Délai estimé** : 4 à 6 jours")
        st.write("- **Taux d'avarie standard** : 3%")
        st.write(f"- **Bilan carbone estimé** : {bilan_carbone:.2f} kg CO2")

# -----------------------------------------------------------------------------
# 2. ESPACE FOURNISSEUR (Intégral)
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("Traitement Fournisseur & Facturation")

    if not orders:
        st.warning("Aucune commande à traiter.")
    else:
        col_sel_ord, col_del_ord = st.columns([3, 1])
        with col_sel_ord:
            idx = st.selectbox("Sélectionner la commande à traiter", range(len(orders)), format_func=lambda i: order_label(orders[i]), key="provider_order_sel")
        
        with col_del_ord:
            st.write("")
            if st.button("🗑️ Supprimer", key=f"del_btn_{idx}", help="Supprimer cette commande de la liste"):
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

        stepper(o["statut"])
        st.progress((o["statut"]) / (len(STATUSES) - 1))

        col_action1, col_action2, col_action3 = st.columns(3)
        with col_action1:
             st.markdown("#### 1. Préparation")
             if o["statut"] == 0:
                 if st.button("📄 Valider & Générer Documents", key=f"btn_gen_{idx}", use_container_width=True):
                     o["docs_generated"] = True
                     o["statut"] = 1
                     st.rerun()
             elif o["statut"] > 0:
                 st.success("Documents générés")
                 
        with col_action2:
             st.markdown("#### 2. Logistique & Dépôt")
             if o["statut"] == 1:
                 choix_entrepot = st.selectbox("Sélectionner l'entrepôt de départ", [
                     "Entrepôt Central Nord (Zone A)", 
                     "Hub Logistique International Cargo (Zone B)", 
                     "Terminal Express Cargo Fret"
                 ], key=f"ent_{idx}")
                 
                 choix_manutention = st.radio("Type de manutention au dépôt", [
                     "Palette Standard ULD (Filmée + Cerclée)", 
                     "Conteneur Sécurisé Haute Valeur", 
                     "Colisage Express Renforcé"
                 ], key=f"man_{idx}")

                 if st.button("🚚 Valider l'affectation au dépôt", key=f"btn_dep_{idx}", use_container_width=True):
                     o["entrepot"] = choix_entrepot
                     o["manutention"] = choix_manutention
                     o["statut"] = 2
                     st.rerun()
             elif o["statut"] == 2:
                  st.info(f"📍 **Entrepôt** : {o.get('entrepot', 'Standard')}\n\n📦 **Manutention** : {o.get('manutention', 'Standard')}")
                  if st.button("✈️ Remettre au transporteur aérien", key=f"btn_trans_{idx}", use_container_width=True):
                      o["carrier_assigned"] = True
                      o["transporteur"] = "Air Cargo Express"
                      o["statut"] = 3
                      st.rerun()
             elif o["statut"] > 2:
                  st.success(f"Affecté à l'entrepôt et remis au transporteur")

        with col_action3:
             st.markdown("#### 3. Suivi & Clôture")
             if o["statut"] == 3:
                  if st.button("🛫 Autoriser le décollage", key=f"btn_dec_{idx}", use_container_width=True):
                      o["statut"] = 4
                      st.rerun()
             elif o["statut"] == 4:
                   if st.button("🛬 Confirmer l'atterrissage", key=f"btn_att_{idx}", use_container_width=True):
                        o["statut"] = 5
                        st.rerun()
             elif o["statut"] == 5:
                  if st.button("📦 Confirmer Livraison", key=f"btn_liv_{idx}", use_container_width=True):
                       o["statut"] = 6
                       st.rerun()
             elif o["statut"] == 6:
                  st.success("Processus logistique terminé")

        if o.get("docs_generated"):
            st.markdown("---")
            st.markdown(f"### 📑 Récapitulatif Interne — {o['reference']}")
            
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

# -----------------------------------------------------------------------------
# 3. SUIVI DU VOL & CARBURANT EN TEMPS RÉEL
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("Suivi du vol en direct & Gestion du Carburant en temps réel")
    if not orders:
        st.warning("Aucune commande à suivre pour le moment.")
    else:
        idx = st.selectbox("Commande à suivre sur la carte", range(len(orders)), format_func=lambda i: order_label(orders[i]), key="tracking_order_sel")
        o = orders[idx]
        a = AIRPORTS[o["origine"]]
        route, km = build_route(a, CDG)

        flight_num = f"FDX-{abs(hash(o['reference'])) % 900 + 100}"

        total_conso_estimee = km * 11.5 + (o["poids_taxable"] * 0.15)
        carburant_depart = total_conso_estimee * 1.35  

        progress_val = st.slider("Simulation de progression du vol", 0.0, 1.0, 0.0, 0.01, key=f"prog_{idx}")
        
        carburant_consomme_actuel = total_conso_estimee * progress_val
        carburant_restant_actuel = carburant_depart - carburant_consomme_actuel

        c_f1, c_f2, c_f3, c_f4 = st.columns(4)
        c_f1.metric("Distance Totale", f"{km:,.0f} km".replace(",", " "))
        c_f2.metric("Carburant Embarqué", f"{carburant_depart:,.0f} kg".replace(",", " "))
        c_f3.metric("Carburant Consommé (Actuel)", f"{carburant_consomme_actuel:,.0f} kg".replace(",", " "), delta=f"{progress_val*100:.0f}% du vol")
        c_f4.metric("Réserve Kérosène Restante", f"{carburant_restant_actuel:,.0f} kg", delta_color="inverse")

        st.markdown("---")

        c1, c2, c3 = st.columns([2, 1, 1])
        c1.info(f"📍 **{a['ville']} ({a['code']}) → Paris (CDG)** · Vol : **{flight_num}**")
        style_name = c2.selectbox("Fond de carte", ["Clair", "Sombre"], key=f"style_sel_{idx}", label_visibility="collapsed")
        c3.caption("Clique sur ▶ Lancer dans la carte (Sélecteur de vitesse actif)")

        if o["statut"] < FLIGHT_STEP:
            st.warning("L'avion n'a pas encore décollé : prévisualisation du trajet.")
            
        start = 1.0 if o["statut"] > FLIGHT_STEP else 0.0
        render_flight_map(route, a, CDG, start, style_name, flight_num)

# -----------------------------------------------------------------------------
# 4. DOUANE & IMPORT
# -----------------------------------------------------------------------------
with tab4:
    st.subheader("🛃 Douane & Analyse Fiscale (CDG)")
    if not orders:
        st.warning("Aucune commande enregistrée.")
    else:
        idx_d = st.selectbox("Commande pour l'analyse douanière", range(len(orders)), format_func=lambda i: order_label(orders[i]), key="dou_sel")
        o_d = orders[idx_d]
        a_d = AIRPORTS[o_d["origine"]]
        dd = (o_d["valeur"] + o_d["fret_aerien"]) * 0.04
        tva = (o_d["valeur"] + o_d["fret_aerien"] + dd) * 0.20
        c1, c2, c3 = st.columns(3)
        c1.write(f"**Incoterm de référence** : `{o_d['incoterm']}`")
        c1.write(f"**Origine** : {a_d['ville']} ({a_d['code']})")
        c2.metric("Droits de douane estimés (~4%)", f"{dd:,.2f} €")
        c3.metric("TVA à l'importation (20%)", f"{tva:,.2f} €")
        st.info("💡 Tous les documents légaux sont générés et téléchargeables dans le dernier onglet (Légal & Conformité).")

# -----------------------------------------------------------------------------
# 5. LÉGAL & CONFORMITÉ (DOCUMENTS DYNAMIQUES HAUTE FIDÉLITÉ)
# -----------------------------------------------------------------------------
with tab5:
    st.subheader("⚖️ Hub Documentaire Légal & Conformité (Génération Officielle)")
    st.markdown("Visualisation et génération des documents HTML réels, adaptés aux spécifications de votre commande.")

    if not orders:
        st.warning("Aucune commande enregistrée pour générer les documents.")
    else:
        idx_l = st.selectbox("Sélectionner la commande pour l'édition des documents", range(len(orders)), format_func=lambda i: order_label(orders[i]), key="leg_sel")
        o_l = orders[idx_l]
        a_l = AIRPORTS[o_l["origine"]]
        
        company_map = {
            "Chine (Shanghai - PVG)": "SHANGHAI AUTO PARTS LTD",
            "Chine (Pékin - PEK)": "BEIJING MIRRORS MFG",
            "Chine (Guangzhou - CAN)": "GUANGZHOU INDUSTRIAL CO.",
            "États-Unis (New York - JFK)": "NY AUTO COMPONENTS INC."
        }
        shipper_name = company_map.get(o_l["origine"], "AUTOMOTIVE MIRRORS MFG")
        flight_code = f"FDX-{abs(hash(o_l['reference'])) % 900 + 100}"

        col_ob, col_fac = st.columns(2)

        # ==========================================
        # 🔴 DOCUMENTS OBLIGATOIRES (HTML)
        # ==========================================
        with col_ob:
            st.markdown("### 🔴 Documents Obligatoires")
            
            with st.expander("📦 Fiche de Colisage (Packing List)"):
                html_pack = generate_packing_list_html(o_l, a_l, shipper_name)
                components.html(html_pack, height=400, scrolling=True)
                b64_pack = base64.b64encode(html_pack.encode()).decode()
                st.markdown(f'<a href="data:text/html;base64,{b64_pack}" download="Fiche_Colisage_{o_l["reference"]}.html" target="_blank"><button style="background-color:#FF7A00;color:white;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;">⬇️ Télécharger (.html)</button></a>', unsafe_allow_html=True)

            with st.expander("✈️ LTA / Air Waybill (AWB)"):
                html_awb = generate_awb_html(o_l, a_l, shipper_name, flight_code)
                components.html(html_awb, height=350, scrolling=True)
                b64_awb = base64.b64encode(html_awb.encode()).decode()
                st.markdown(f'<a href="data:text/html;base64,{b64_awb}" download="AWB_{o_l["reference"]}.html" target="_blank"><button style="background-color:#FF7A00;color:white;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;">⬇️ Télécharger (.html)</button></a>', unsafe_allow_html=True)
                
            with st.expander("🛃 Déclaration de Douane (DAU)"):
                html_dau = generate_dau_html(o_l, a_l, shipper_name)
                components.html(html_dau, height=350, scrolling=True)
                b64_dau = base64.b64encode(html_dau.encode()).decode()
                st.markdown(f'<a href="data:text/html;base64,{b64_dau}" download="DAU_{o_l["reference"]}.html" target="_blank"><button style="background-color:#FF7A00;color:white;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;">⬇️ Télécharger (.html)</button></a>', unsafe_allow_html=True)

        # ==========================================
        # 🔵 DOCUMENTS FACULTATIFS (NOUVEAU - HTML)
        # ==========================================
        with col_fac:
            st.markdown("### 🔵 Documents Facultatifs")
            
            with st.expander("✅ Déclaration de Conformité (CE)"):
                html_ce = generate_ce_html(o_l, shipper_name, a_l)
                components.html(html_ce, height=400, scrolling=True)
                b64_ce = base64.b64encode(html_ce.encode()).decode()
                st.markdown(f'<a href="data:text/html;base64,{b64_ce}" download="Conformite_{o_l["reference"]}.html" target="_blank"><button style="background-color:#FF7A00;color:white;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;">⬇️ Télécharger (.html)</button></a>', unsafe_allow_html=True)
                
            with st.expander("🛡️ Attestation d'Assurance"):
                html_ass = generate_assurance_html(o_l, shipper_name)
                components.html(html_ass, height=400, scrolling=True)
                b64_ass = base64.b64encode(html_ass.encode()).decode()
                st.markdown(f'<a href="data:text/html;base64,{b64_ass}" download="Assurance_{o_l["reference"]}.html" target="_blank"><button style="background-color:#FF7A00;color:white;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;">⬇️ Télécharger (.html)</button></a>', unsafe_allow_html=True)

            with st.expander("✍️ Preuve de Livraison (POD)"):
                html_pod = generate_pod_html(o_l, shipper_name)
                components.html(html_pod, height=400, scrolling=True)
                b64_pod = base64.b64encode(html_pod.encode()).decode()
                st.markdown(f'<a href="data:text/html;base64,{b64_pod}" download="POD_{o_l["reference"]}.html" target="_blank"><button style="background-color:#FF7A00;color:white;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;">⬇️ Télécharger (.html)</button></a>', unsafe_allow_html=True)

            with st.expander("⚖️ Conditions Générales (CGA)"):
                html_cga = generate_cga_html(o_l, shipper_name)
                components.html(html_cga, height=400, scrolling=True)
                b64_cga = base64.b64encode(html_cga.encode()).decode()
                st.markdown(f'<a href="data:text/html;base64,{b64_cga}" download="CGA_{o_l["reference"]}.html" target="_blank"><button style="background-color:#FF7A00;color:white;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;">⬇️ Télécharger (.html)</button></a>', unsafe_allow_html=True)
