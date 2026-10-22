"""
Air Cargo Hub — Logistique internationale
Interface complète : Devis, Fournisseur, Suivi 3D & Carburant, 
Douane, AWB dynamique et Correction du chevauchement de la carte.

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
# CONFIG PAGE + DESIGN DIRECTION ARTISTIQUE (DA)
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

    .doc-card {
        background: #ffffff; border-left: 5px solid #FF7A00; border-radius: 10px;
        padding: 1.2rem 1.5rem; margin-bottom: 1rem; color: #1e293b;
        box-shadow: 0 4px 16px rgba(0,0,0,0.04); border: 1px solid #f1f5f9;
    }
    .doc-title { font-weight: 700; color: #0B1B2E; font-size: 1.1rem; margin-bottom: .5rem; }
    
    .badge-warning { background: #FEF2F2; color: #DC2626; padding: 12px 16px; border-radius: 10px;
        border: 1px solid #FEE2E2; font-weight: 500; margin-top: 10px; font-size: 0.9rem; }
    .badge-success { background: #F0FDF4; color: #16A34A; padding: 12px 16px; border-radius: 10px;
        border: 1px solid #DCFCE7; font-weight: 600; font-size: 0.9rem; }
        
    .step { display: inline-block; padding: 6px 14px; border-radius: 999px; font-size: .85rem;
        margin: 4px 6px 4px 0; border: 1px solid #E2E8F0; color: #64748B; background: #F8FAFC; font-weight: 500; }
    .step.done { background: #F0FDF4; color: #16A34A; border-color: #BBF7D0; font-weight: 600; }
    .step.now  { background: #FF7A00; color: #fff; border-color: #FF7A00; font-weight: 700; box-shadow: 0 4px 12px rgba(255,122,0,0.3); }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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

FLEET = [
    ("AF-801", [139.69, 35.68], [103.81, 1.35], 0.8, 0.10),
    ("BA-249", [-0.12, 51.50], [55.27, 25.20], 0.9, 0.30),
    ("LH-400", [-73.77, 40.64], [8.57, 50.03], 0.7, 0.50),
    ("EK-308", [55.27, 25.20], [121.80, 31.14], 1.1, 0.20),
    ("AF-454", [2.54, 49.00], [-46.63, -23.55], 0.65, 0.60),
    ("SQ-322", [103.81, 1.35], [-0.12, 51.50], 0.75, 0.00),
    ("CX-251", [114.16, 22.31], [2.54, 49.00], 0.85, 0.40),
    ("JL-045", [139.69, 35.68], [2.54, 49.00], 0.70, 0.70),
    ("QR-001", [51.53, 25.27], [2.54, 49.00], 0.8, 0.15),
    ("DL-101", [-84.42, 33.64], [2.54, 49.00], 0.75, 0.25),
    ("AF-777", [-118.40, 33.94], [2.54, 49.00], 0.85, 0.45),
    ("UA-909", [-87.90, 41.97], [-0.12, 51.50], 0.8, 0.55),
    ("QF-009", [151.17, -33.94], [103.81, 1.35], 0.9, 0.80),
    ("KE-901", [126.45, 37.46], [2.54, 49.00], 0.7, 0.35),
    ("TG-930", [100.75, 13.68], [2.54, 49.00], 0.8, 0.65),
]

INCOTERM_INFO = {
    "EXW": "Ex Works : l'acheteur gère tout depuis l'usine (risques et frais maximaux pour l'acheteur).",
    "FCA": "Free Carrier : le vendeur remet la marchandise au transporteur désigné à l'aéroport de départ.",
    "CPT": "Carriage Paid To : le vendeur paie le transport principal jusqu'à CDG, transferts de risques anticipés.",
    "CIP": "Carriage and Insurance Paid : transport + assurance payés par le vendeur jusqu'à CDG.",
    "DAP": "Delivered at Place : livré à destination (CDG), non dédouané. Risques et frais pour le vendeur.",
    "DPU": "Delivered at Place Unloaded : livré et déchargé sur le terminal à destination.",
    "DDP": "Delivered Duty Paid : le vendeur gère tout, y compris le dédouanement à l'import et les taxes.",
}

STATUSES = [
    "Commande reçue",
    "Documents générés",
    "Au dépôt de départ",
    "Remis au transporteur",
    "En vol vers CDG",
    "Atterri à CDG",
    "Livré / dédouané",
]
FLIGHT_STEP = 4

# -----------------------------------------------------------------------------
# OUTILS GÉO & TRAJECTOIRE CORRIGÉE (ATLANTIQUE / ASIE)
# -----------------------------------------------------------------------------
def haversine_km(a, b):
    lon1, lat1, lon2, lat2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))

def great_circle(p1, p2, n=150):
    lon1, lat1, lon2, lat2 = map(math.radians, [p1[0], p1[1], p2[0], p2[1]])
    d = 2 * math.asin(math.sqrt(
        math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2))
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
    if start["lon"] > 50:
        via = [[85, 50], [58, 61], [30, 61], [12, 53]]
    else:
        via = [[-55, 52], [-35, 60], [-20, 64], [-10, 56]]
        
    wps = [[start["lon"], start["lat"]]] + via + [[end["lon"], end["lat"]]]
    route = []
    for a, b in zip(wps[:-1], wps[1:]):
        seg = great_circle(a, b, 150)
        route.extend(seg if not route else seg[1:])
    km = sum(haversine_km(route[i], route[i + 1]) for i in range(len(route) - 1))
    return route, km

# -----------------------------------------------------------------------------
# CARTE MAPLIBRE (HTML + JS autonome avec correction de positionnement UI)
# -----------------------------------------------------------------------------
MAP_HTML = r"""
<!doctype html><html><head><meta charset="utf-8">
<link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet">
<script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
<script src="https://unpkg.com/deck.gl@8.9.33/dist.min.js"></script>
<style>
 html,body{margin:0;height:100%;font-family:Inter,Segoe UI,Arial,sans-serif;background:#0b1b2e}
 #map{position:absolute;inset:0}
 .hud{position:absolute;left:14px;right:14px;bottom:14px;background:rgba(10,25,45,.92);color:#fff;
   border-radius:16px;padding:12px 16px;backdrop-filter:blur(10px);box-shadow:0 6px 24px rgba(0,0,0,.35)}
 .row{display:flex;gap:18px;flex-wrap:wrap;align-items:center;justify-content:space-between}
 .kpi{min-width:92px}.kpi b{display:block;font-size:1.2rem}.kpi span{font-size:.7rem;opacity:.65;text-transform:uppercase;letter-spacing:.05em}
 .bar{height:8px;background:rgba(255,255,255,.18);border-radius:99px;margin:10px 0 8px;overflow:hidden}
 .bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,#FF7A00,#FFC04D);border-radius:99px}
 button,select{background:#FF7A00;color:#fff;border:0;border-radius:10px;padding:8px 13px;font-weight:600;cursor:pointer;font-size:.85rem}
 button.alt,select{background:rgba(255,255,255,.14)}
 select option{color:#000}
 
 /* Correction du positionnement de l'encart vol en haut à gauche pour laisser la place au zoom en haut à droite */
 .flight-card {
    position: absolute; top: 14px; left: 14px; background: rgba(10, 25, 45, 0.92);
    color: #fff; border-radius: 10px; overflow: hidden; width: 220px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.5); z-index: 2; border: 1px solid rgba(255,255,255,0.1);
    backdrop-filter: blur(10px);
 }
 .flight-card img { width: 100%; height: 95px; object-fit: cover; display: block; border-bottom: 2px solid #FF7A00; }
 .flight-card-body { padding: 10px 12px; }
 .flight-card-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.15); padding-bottom: 6px;}
 .flight-card-header h2 { margin: 0; font-size: 1.1rem; color: #FF7A00; letter-spacing: 0.5px; }
 .flight-card-header span { font-size: 0.7rem; font-weight: 500; opacity: 0.9; }
 .flight-route { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }
 .route-point { text-align: center; }
 .route-point b { display: block; font-size: 1.1rem; font-weight: 800; }
 .route-point span { font-size: 0.65rem; opacity: 0.7; }
 .route-arrow { color: #FF7A00; font-size: 1.1rem; padding: 0 6px; opacity: 0.8; }

 .lbl{background:#fff;color:#0E2A47;font-weight:700;font-size:11px;padding:3px 8px;border-radius:99px;box-shadow:0 2px 6px rgba(0,0,0,.3);white-space:nowrap}
 .lbl.red{background:#C62828;color:#fff}.lbl.green{background:#2E7D32;color:#fff}
 .fl{font-size:10px;font-weight:600;color:#37474f;text-align:center;white-space:nowrap;text-shadow:0 0 3px #fff}
</style></head><body>
<div id="map"></div>

<div class="flight-card" id="flight-card"></div>

<div id="err" style="display:none;position:absolute;top:70px;left:14px;max-width:70%;background:#C62828;color:#fff;border-radius:10px;padding:8px 12px;font:12px monospace;white-space:pre-wrap;z-index:9"></div>
<div class="hud">
  <div class="row">
    <div class="kpi"><b id="k_alt">0 m</b><span>Altitude</span></div>
    <div class="kpi"><b id="k_spd">0 km/h</b><span>Vitesse</span></div>
    <div class="kpi"><b id="k_dist">0 km</b><span>Restant</span></div>
    <div class="kpi"><b id="k_eta">--</b><span>Arrivée dans</span></div>
    <div class="kpi"><b id="k_pct">0 %</b><span>Progression</span></div>
    <div class="row" style="gap:8px">
      <button id="b_play">▶ Lancer</button>
      <button class="alt" id="b_cam">🎥 Caméra : suivi</button>
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
const D = __DATA__;

const imgHtml = D.photo ? `<img src="${D.photo}" alt="Avion FedEx">` : '';
document.getElementById('flight-card').innerHTML = `
    ${imgHtml}
    <div class="flight-card-body">
        <div class="flight-card-header">
            <h2>${D.flight_num}</h2>
            <span>${D.plane_model}</span>
        </div>
        <div class="flight-route">
            <div class="route-point"><b>${D.origin.code}</b><span>${D.origin.ville}</span></div>
            <div class="route-arrow">✈</div>
            <div class="route-point"><b>${D.dest.code}</b><span>${D.dest.ville}</span></div>
        </div>
    </div>
`;

const rad = x => x*Math.PI/180, deg = x => x*180/Math.PI;
function hav(a,b){const dl=rad(b[1]-a[1]),dn=rad(b[0]-a[0]);
  const h=Math.sin(dl/2)**2+Math.cos(rad(a[1]))*Math.cos(rad(b[1]))*Math.sin(dn/2)**2;
  return 12742*Math.asin(Math.sqrt(h));}
function brg(a,b){const y=Math.sin(rad(b[0]-a[0]))*Math.cos(rad(b[1]));
  const x=Math.cos(rad(a[1]))*Math.sin(rad(b[1]))-Math.sin(rad(a[1]))*Math.cos(rad(b[1]))*Math.cos(rad(b[0]-a[0]));
  return (deg(Math.atan2(y,x))+360)%360;}
function mk(pts){const c=[0];for(let i=1;i<pts.length;i++)c.push(c[i-1]+hav(pts[i-1],pts[i]));return{pts,c,total:c[c.length-1]};}
function at(p,f){f=Math.min(Math.max(f,0),1);const d=f*p.total;let i=1;
  while(i<p.c.length-1&&p.c[i]<d)i++;const s=(p.c[i]-p.c[i-1])||1,k=(d-p.c[i-1])/s;
  const a=p.pts[i-1],b=p.pts[i];
  return{lon:a[0]+(b[0]-a[0])*k,lat:a[1]+(b[1]-a[1])*k,b:brg(a,b),i:i-1};}

const PLANE=(fill,sz)=>`<svg width="${sz}" height="${sz}" viewBox="0 0 64 64" style="filter:drop-shadow(0 4px 4px rgba(0,0,0,.45))">
<path d="M32 2 L37 22 L60 36 L60 42 L37 36 L36 52 L44 58 L44 62 L32 59 L20 62 L20 58 L28 52 L27 36 L4 42 L4 36 L27 22 Z"
 fill="${fill}" stroke="#fff" stroke-width="2.2" stroke-linejoin="round"/></svg>`;

const main = mk(D.route);
const map = new maplibregl.Map({container:'map',style:D.style,center:D.center,zoom:2.4,pitch:45,bearing:-8,attributionControl:{compact:true}});
map.addControl(new maplibregl.NavigationControl({visualizePitch:true}),'top-right');

function lab(txt,cls,lngLat){const e=document.createElement('div');e.className='lbl '+cls;e.textContent=txt;
  return new maplibregl.Marker({element:e,anchor:'bottom',offset:[0,-4]}).setLngLat(lngLat).addTo(map);}

let overlay=null;
let planeM, fleetM=[], playing=false, t=D.start, follow=true, mult=1, lastTs=null, curBearing=0, clock=0;
const BASE_DURATION = 70;

let inited=false;
function showErr(e){const d=document.getElementById('err');d.style.display='block';d.textContent+='⚠ '+(e&&e.message?e.message:e)+'\n';}
window.onerror=(m)=>{showErr(m);};
map.on('error',ev=>{if(ev&&ev.error)showErr('Carte : '+ev.error.message);});

function init(){
  if(inited||!map.isStyleLoaded())return;
  inited=true;
  try{
  map.addSource('nf',{type:'geojson',data:{type:'FeatureCollection',features:D.zones.map(z=>({type:'Feature',properties:{n:z.name},geometry:{type:'Polygon',coordinates:[z.ring]}}))}});
  map.addLayer({id:'nf3d',type:'fill-extrusion',source:'nf',paint:{'fill-extrusion-color':'#E53935','fill-extrusion-opacity':.38,'fill-extrusion-height':350000,'fill-extrusion-base':0}});
  map.addLayer({id:'nfl',type:'line',source:'nf',paint:{'line-color':'#C62828','line-width':2,'line-dasharray':[2,2]}});
  D.zones.forEach(z=>{lab('⛔ '+z.name,'red',[(z.ring[0][0]+z.ring[2][0])/2,(z.ring[0][1]+z.ring[2][1])/2]);});

  map.addSource('plan',{type:'geojson',data:{type:'Feature',geometry:{type:'LineString',coordinates:D.route}}});
  map.addLayer({id:'plan',type:'line',source:'plan',layout:{'line-cap':'round','line-join':'round'},paint:{'line-color':'#90A4AE','line-width':3,'line-dasharray':[1.5,2.5]}});
  
  map.addSource('trail',{type:'geojson',data:{type:'Feature',geometry:{type:'LineString',coordinates:[D.route[0],D.route[0]]}}});
  map.addLayer({id:'glow',type:'line',source:'trail',layout:{'line-cap':'round','line-join':'round'},paint:{'line-color':'#FF7A00','line-width':14,'line-opacity':.25,'line-blur':6}});
  map.addLayer({id:'trail',type:'line',source:'trail',layout:{'line-cap':'round','line-join':'round'},paint:{'line-color':'#FF5A00','line-width':5}});

  lab(D.origin.code+' · '+D.origin.ville,'red',[D.origin.lon,D.origin.lat]);
  lab(D.dest.code+' · '+D.dest.ville,'green',[D.dest.lon,D.dest.lat]);

  D.fleet.forEach(f=>{
    const w=document.createElement('div');
    w.innerHTML = `<div class="svg-container">${PLANE('#78909C',20)}</div><div class="fl">${f.code}</div>`;
    const m=new maplibregl.Marker({element:w,rotationAlignment:'map',pitchAlignment:'map'}).setLngLat(f.pts[0]).addTo(map);
    fleetM.push({m,path:mk(f.pts),speed:f.speed,phase:f.phase,el:w});
  });

  const pe=document.createElement('div');pe.innerHTML=PLANE('#FF7A00',46);
  planeM=new maplibregl.Marker({element:pe,rotationAlignment:'map',pitchAlignment:'map'}).setLngLat(D.route[0]).addTo(map);
  
  if(D.model && window.deck){
    try{
      overlay=new deck.MapboxOverlay({interleaved:false,layers:[]});
      map.addControl(overlay);
      pe.style.display='none'; 
    }catch(e){
      overlay=null;
      console.error(e);
    }
  }

  update(t);
  map.fitBounds([[Math.min(D.origin.lon,D.dest.lon)-8,Math.min(D.origin.lat,D.dest.lat)-6],[Math.max(D.origin.lon,D.dest.lon)+8,Math.max(D.origin.lat,D.dest.lat)+10]],{padding:60,duration:0});
  requestAnimationFrame(loop);
  }catch(e){showErr(e);}
}
map.on('style.load',init);map.on('load',init);
const _iv=setInterval(()=>{if(inited)clearInterval(_iv);else init();},700);

function fmtH(h){const H=Math.floor(h),M=Math.round((h-H)*60);return H+' h '+String(M).padStart(2,'0');}

function update(f){
  const p=at(main,f);
  curBearing += ((((p.b - curBearing) + 540) % 360) - 180) * 0.10;
  planeM.setLngLat([p.lon,p.lat]).setRotation(p.b);
  
  const tr=D.route.slice(0,p.i+1).concat([[p.lon,p.lat]]);
  if(tr.length<2) tr.push([p.lon,p.lat]);
  map.getSource('trail').setData({type:'Feature',geometry:{type:'LineString',coordinates:tr}});
  
  const prof=Math.max(0.12,Math.min(1,f/0.08,(1-f)/0.08));
  const alt=f<=0||f>=1?0:Math.round(11000*prof/100)*100;
  const spd=f<=0||f>=1?0:Math.round(870*prof);
  const rem=main.total*(1-f), hrs=rem/870+(f<1?0.2:0);
  
  k_alt.textContent=alt.toLocaleString('fr-FR')+' m';
  k_spd.textContent=spd+' km/h';
  k_dist.textContent=Math.round(rem).toLocaleString('fr-FR')+' km';
  k_eta.textContent=f>=1?'Atterri ✔':fmtH(hrs);
  k_pct.textContent=Math.round(f*100)+' %';
  bar.style.width=(f*100)+'%';
  
  if(follow&&playing){map.jumpTo({center:[p.lon,p.lat],bearing:curBearing,pitch:55,zoom:4.2});}
}

function loop(ts){
  if(lastTs===null)lastTs=ts;const dt=(ts-lastTs)/1000;lastTs=ts;clock+=dt;
  
  if(playing){
    t+=dt*mult/BASE_DURATION;
    if(t>=1){t=1;playing=false;b_play.textContent='↺ Rejouer';}
    update(t);
  }

  const p = at(main, t);
  const prof0 = Math.max(0.12, Math.min(1, t/0.08, (1-t)/0.08));
  let sceneData = [];
  
  sceneData.push({
      pos: [p.lon, p.lat, (t<=0||t>=1)?0:11000*prof0],
      yaw: -p.b
  });

  fleetM.forEach(f => {
      const q = at(f.path, (f.phase + clock * f.speed / 260) % 1);
      f.m.setLngLat([q.lon, q.lat]).setRotation(q.b);
      
      if(overlay) {
          f.el.querySelector('.svg-container').style.display = 'none';
      }
      
      sceneData.push({
          pos: [q.lon, q.lat, 11000],
          yaw: -q.b
      });
  });

  if(overlay){
    try {
      overlay.setProps({layers:[new deck.ScenegraphLayer({
        id:'planes-3d',
        data: sceneData,
        scenegraph: D.model,
        getPosition: d => d.pos,
        getOrientation: d => [0, d.yaw, 90],
        sizeScale: 100000, 
        _lighting: 'pbr',
        pickable: false
      })]});
    } catch(e) {
      overlay=null;
      planeM.getElement().style.display=''; 
      fleetM.forEach(f => f.el.querySelector('.svg-container').style.display = 'block');
      console.error(e);
    }
  }
  
  requestAnimationFrame(loop);
}

b_play.onclick=()=>{
  if(t>=1){t=0;curBearing=at(main,0).b;}
  playing=!playing;
  b_play.textContent=playing?'⏸ Pause':'▶ Reprendre';
  if(playing&&follow){map.easeTo({pitch:55,zoom:4.2,duration:1200});}
};
b_cam.onclick=()=>{
  follow=!follow;b_cam.textContent='🎥 Caméra : '+(follow?'suivi':'libre');
  if(!follow)map.easeTo({pitch:35,bearing:-8,zoom:2.6,duration:1200});
};
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
        "Relief rues": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
    }[style_name]
    
    fleet = [
        {"code": c, "pts": great_circle(a, b, 150), "speed": s, "phase": ph}
        for c, a, b, s, ph in FLEET
    ]
    
    model_data, _ = load_plane_model()
    photo_b64 = load_fedex_image()
    
    data = {
        "model": model_data,
        "photo": photo_b64,
        "flight_num": flight_num,
        "plane_model": "Boeing 777F",
        "route": route,
        "origin": origin,
        "dest": dest,
        "zones": NO_FLY,
        "fleet": fleet,
        "style": style,
        "start": start_progress,
        "center": [(origin["lon"] + dest["lon"]) / 2, (origin["lat"] + dest["lat"]) / 2],
    }
    components.html(MAP_HTML.replace("__DATA__", json.dumps(data)), height=height, scrolling=False)

# -----------------------------------------------------------------------------
# ÉTAT DE SESSION & COMMANDES
# -----------------------------------------------------------------------------
if "orders" not in st.session_state:
    st.session_state.orders = [{
        "reference": "CMD-AIR-10001",
        "origine": "Chine (Pékin - PEK)",
        "incoterm": "CIP",
        "poids_reel": 265.0,
        "volume": 1.3,
        "poids_taxable": 265.0,
        "fret_aerien": 795.0,
        "cout_total_dap": 13870.0,
        "valeur": 12600.0,
        "statut": 0,
        "cree_le": datetime.now() - timedelta(hours=3),
        "docs_generated": False,
        "carrier_assigned": False,
        "entrepot": "Non assigné",
        "manutention": "Standard"
    }]

orders = st.session_state.orders

def order_label(o):
    return f"{o['reference']} · {AIRPORTS[o['origine']]['code']}→CDG · {STATUSES[o['statut']]}"

def stepper(idx):
    html = ""
    for i, s in enumerate(STATUSES):
        cls = "done" if i < idx else "now" if i == idx else ""
        html += f'<span class="step {cls}">{"✔ " if i < idx else ""}{s}</span>'
    st.markdown(html, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# EN-TÊTE + NAVIGATION PAR ONGLETS (4 ONGLETS)
# -----------------------------------------------------------------------------
st.markdown(
    """
<div class="hero-header">
    <h1>✈️ Air Cargo Hub — Logistique internationale</h1>
    <p>Plateforme unifiée de cotation, gestion fournisseur, suivi 3D, carburant en direct et dédouanement.</p>
</div>
""",
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs([
    "🛒 Espace Client (Devis & Incoterms)", 
    "🏭 Espace Fournisseur (Facturation)", 
    "🌍 Suivi du vol & Carburant",
    "🛃 Douane, AWB & Procédure d'Import"
])

# -----------------------------------------------------------------------------
# 1. ESPACE CLIENT
# -----------------------------------------------------------------------------
with tab1:
    st.subheader("Cotation Fret Aérien & Choix des Incoterms")
    
    with st.expander("📚 Guide complet des Incoterms (Transfert de risques et de frais)"):
        for inc, desc in INCOTERM_INFO.items():
            st.markdown(f"- **{inc}** : {desc}")

    col_form, col_sum = st.columns([1.5, 1])

    with col_form:
        st.markdown("#### 📍 Origine & Marchandise")
        origine = st.selectbox("Aéroport de départ (Fournisseur)", list(AIRPORTS.keys()), index=1)
        valeur_marchandise = st.number_input("Valeur de la marchandise (EXW) en €", value=12600)
        
        c1, c2 = st.columns(2)
        poids_reel = c1.number_input("Poids réel total (kg)", value=265)
        volume_m3 = c2.number_input("Volume total (m³)", value=1.3, step=0.1)

        st.markdown("#### ⚖️ Règle Poids/Volume & Tarification")
        poids_volumetrique = volume_m3 * 166.67
        poids_taxable = max(poids_reel, poids_volumetrique)
        
        st.info(f"**Équivalence IATA (1T = 6m³)** : Volume de {volume_m3} m³ = {poids_volumetrique:.1f} kg volumétrique.\n\n"
                f"Poids taxable retenu (le plus élevé) : **{poids_taxable:.1f} kg**")

        tarif_normal = AIRPORTS[origine]["tarif"]
        tarif_sup = tarif_normal - 0.25
        seuil_sup = 300

        cout_base = poids_taxable * tarif_normal
        cout_payant_pour = seuil_sup * tarif_sup

        if cout_payant_pour < cout_base and poids_taxable < seuil_sup:
            cout_fret = cout_payant_pour
            st.success(f"✅ Règle du 'Payant Pour' appliquée : Taxation à {seuil_sup}kg au tarif de {tarif_sup}€/kg ({cout_payant_pour}€) est plus avantageuse que {poids_taxable:.0f}kg à {tarif_normal}€/kg ({cout_base}€).")
        else:
            cout_fret = cout_base
            st.write(f"Coût du fret appliqué : {poids_taxable:.0f} kg x {tarif_normal} €/kg = **{cout_fret:.2f} €**")

        st.markdown("#### 🛡️ Surcharges & Incoterms")
        incoterm = st.selectbox("Incoterm cible", list(INCOTERM_INFO.keys()), index=3)
        
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
            ref = f"CMD-AIR-{random.randint(10000, 99999)}"
            orders.append({
                "reference": ref, "origine": origine, "incoterm": incoterm,
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
        cout_logistique_pct = ((val_cip - valeur_marchandise) / valeur_marchandise) * 100
        bilan_carbone = 0.45 * (poids_taxable / 1000)
        st.write(f"- **Coût logistique (CIP/EXW)** : {cout_logistique_pct:.2f}%")
        st.write("- **Délai estimé** : 4 à 6 jours")
        st.write("- **Taux d'avarie standard** : 3%")
        st.write(f"- **Bilan carbone estimé** : {bilan_carbone:.2f} kg CO2")

# -----------------------------------------------------------------------------
# 2. ESPACE FOURNISSEUR
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
                 if st.button("📄 Valider & Générer Facture", key=f"btn_gen_{idx}", use_container_width=True):
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
            st.markdown(f"### 📑 Facture / Devis Logistique — {o['reference']}")
            
            facture_txt = f"""======================================================
FACTURE PROFORMA / COTATION LOGISTIQUE
======================================================
Référence Commande : {o['reference']}
Incoterm Convenu   : {o['incoterm']}
Départ             : {a['ville']} ({a['code']})
Destination        : Paris (CDG)
Entrepôt Affecté   : {o.get('entrepot', 'N/A')}
Manutention        : {o.get('manutention', 'N/A')}

--- DONNÉES D'EXPÉDITION ---
Poids Réel Brut    : {o['poids_reel']} kg
Volume Total       : {o['volume']} m3
Équivalence        : 1 Tonne = 6 m3
Poids Volumétrique : {(o['volume'] * 166.67):.1f} kg
Poids Taxable      : {o['poids_taxable']:.1f} kg (Règle à l'avantage du transporteur)

--- DÉTAIL TARIFAIRE ---
Valeur Marchandise (EXW) : {o['valeur']:.2f} EUR
Frais de Fret Aérien     : {o['fret_aerien']:.2f} EUR (Inclut Fret de base + Surcharges MYC, IRC, SPX)
Coût Total Estimé (DAP)  : {o['cout_total_dap']:.2f} EUR

--- KPIs ---
Délai estimé       : 4 à 6 Jours
Taux d'avarie      : 3%
Bilan Carbone      : {0.45 * (o['poids_taxable'] / 1000):.2f} kg CO2/T
======================================================"""
            
            st.text_area("Aperçu du document", facture_txt, height=400, key=f"txt_area_{idx}")
            st.download_button(f"⬇️ Télécharger la Facture ({o['reference']})", facture_txt, file_name=f"Facture_{o['reference']}.txt", key=f"dl_btn_{idx}", type="primary")

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
        style_name = c2.selectbox("Fond de carte", ["Clair", "Sombre", "Relief rues"], key=f"style_sel_{idx}", label_visibility="collapsed")
        c3.caption("Clique sur ▶ Lancer dans la carte")

        if o["statut"] < FLIGHT_STEP:
            st.warning("L'avion n'a pas encore décollé : prévisualisation du trajet.")
            
        start = 1.0 if o["statut"] > FLIGHT_STEP else 0.0
        render_flight_map(route, a, CDG, start, style_name, flight_num)

# -----------------------------------------------------------------------------
# 4. DOUANE, AWB (AIR WAYBILL) & PROCÉDURE D'IMPORT
# -----------------------------------------------------------------------------
with tab4:
    st.subheader("🛃 Douane, Air Waybill (AWB) & Procédure d'Import (CDG)")

    if not orders:
        st.warning("Aucune commande enregistrée pour analyser la douane.")
    else:
        idx_d = st.selectbox("Sélectionner la commande pour l'analyse et la LTA", range(len(orders)), format_func=lambda i: order_label(orders[i]), key="douane_order_sel")
        o_d = orders[idx_d]
        a_d = AIRPORTS[o_d["origine"]]

        valeur_fob = o_d["valeur"]
        fret_estime = o_d["fret_aerien"]
        
        droits_de_douane = (valeur_fob + fret_estime) * 0.04
        tva_import = (valeur_fob + fret_estime + droits_de_douane) * 0.20

        col_d1, col_d2 = st.columns(2)

        with col_d1:
            st.markdown(f"#### 📋 Paramètres Douaniers de la Commande")
            st.write(f"- **Origine / Provenance** : {a_d['ville']} ({a_d['code']}), Hors Union Européenne")
            st.write(f"- **Incoterm sélectionné** : `{o_d['incoterm']}`")
            
            if o_d['incoterm'] in ["EXW"]:
                st.markdown('<div class="badge-warning">⚠️ <b>Incoterm EXW :</b> C\'est l\'acheteur (toi) qui organise tout et émet/gère la LTA (Air Waybill) depuis l\'usine.</div>', unsafe_allow_html=True)
            elif o_d['incoterm'] in ["FCA", "CPT", "CIP"]:
                st.markdown('<div class="badge-success">🛡️ <b>Incoterm Vendeur/Transitaire :</b> Le vendeur ou le transitaire désigné émet la LTA principale jusqu\'à Paris CDG.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="badge-success">🛡️ <b>Incoterm Livré (DAP/DDP) :</b> Le fournisseur gère intégralement le transport et l\'émission de la LTA.</div>', unsafe_allow_html=True)

            st.markdown("#### 📑 Documents requis pour le Dédouanement à CDG")
            st.markdown("""
            * **DAU (Document Administratif Unique)** : Déclaration en douane (DELTA).
            * **Facture Commerciale** : Mentions obligatoires (origine, code SH, valeur).
            * **LTA / Air Waybill (AWB)** : Document de transport aérien officiel (généré ci-contre).
            * **Certificat d'origine** : Accord préférentiel.
            """)

        with col_d2:
            st.markdown("#### 💰 Simulation des Taxes et Droits à l'Import")
            st.metric("Valeur Marchandise (FOB)", f"{valeur_fob:,.2f} €".replace(",", " "))
            st.metric("Fret & Assurance pris en compte", f"{fret_estime:,.2f} €".replace(",", " "))
            st.metric("Droits de douane estimés (~4%)", f"{droits_de_douane:,.2f} €".replace(",", " "))
            st.metric("TVA à l'importation (20%)", f"{tva_import:,.2f} €".replace(",", " "))
            
            total_taxes = droits_de_douane + tva_import
            st.markdown(f"### Total des taxes exigibles : **{total_taxes:,.2f} €**")

        st.markdown("---")
        st.markdown("### ✈️ Générateur Officiel de Lettre de Transport Aérien (Air Waybill / AWB)")
        st.info(f"Génération dynamique pour la commande **{o_d['reference']}** au départ de **{a_d['ville']} ({a_d['code']})**.")

        awb_number = f"057-{abs(hash(o_d['reference'])) % 9000000 + 1000000}"
        date_exp = o_d["cree_le"].strftime("%d-%b-%Y").upper()

        awb_text = f"""========================================================================================
AIR WAYBILL (AWB) — DOCUMENT DE TRANSPORT AÉRIEN INTERNATIONAL
----------------------------------------------------------------------------------------
AWB Number : {awb_number}                                        Non-Negotiable
----------------------------------------------------------------------------------------
Shipper's Name and Address:                      Shipper's Account Number:
FOURNISSEUR INDUSTRIEL S.A.                      ACC-{a_d['code']}-992
{a_d['ville']}, {a_d['code']} (ORIGINE)
--------------------------------------------------------------------------------        
Consignee's Name and Address:                    Consignee's Account Number:
SAINT-EURISTIDE LOGISTICS HUB                    ACC-PARIS-750
Aéroport de Paris - Roissy CDG (CDG)
75000 Paris, FRANCE
--------------------------------------------------------------------------------
Issuing Carrier's Agent Name and City:           Accounting Information:
AIR CARGO GLOBAL FORWARDING                      ++ INCOTERM : {o_d['incoterm']} ++
{a_d['code']} / PARIS (CDG)                      VALEUR DÉCLARÉE : {o_d['valeur']} EUR
--------------------------------------------------------------------------------
Airport of Departure (Addr. of First Carrier)    Requested Routing:
{a_d['ville'].upper()} ({a_d['code']})                         {a_d['code']} / CDG
--------------------------------------------------------------------------------
To  | By First Carrier | To | By | To | By | Currency | CHGS Code | WT/VAL | Other
{a_d['code']} | EY               | CDG|    |    |    | EUR      | PP        | X      | NVD
--------------------------------------------------------------------------------
Airport of Destination:                          Flight / Date:
PARIS - CHARLES DE GAULLE (CDG)                  FDX-{abs(hash(o_d['reference'])) % 900 + 100} / {date_exp}
--------------------------------------------------------------------------------
Handling Information:
CONSOLIDATION AS PER ATTACHED LIST. 
MANUTENTION DÉPÔT : {o_d.get('manutention', 'Standard')}
ENTREPÔT : {o_d.get('entrepot', 'Standard')}
--------------------------------------------------------------------------------
NO. OF | GROSS   | RATE CLASS | CHARGEABLE | RATE/    | TOTAL    | NATURE AND QUANTITY
PIECES | WEIGHT  |            | WEIGHT     | CHARGE   |          | OF GOODS (DIMS)
--------------------------------------------------------------------------------
  1    | {o_d['poids_reel']:>6.1f} K  |     Q      |  {o_d['poids_taxable']:>6.1f} K  |   3.75   | {o_d['fret_aerien']:>8.2f} | Marchandise Générale Industrielle
       |         |            |            |          |          | Volume : {o_d['volume']} m3
       |         |            |            |          |          | Poids Taxable : {o_d['poids_taxable']} kg
--------------------------------------------------------------------------------
TOTAL PIECES: 1                TOTAL GROSS WEIGHT: {o_d['poids_reel']} KG
--------------------------------------------------------------------------------
WEIGHT CHARGE: {o_d['fret_aerien']:>8.2f} EUR    VALUATION CHARGE: 0.00    TAX: 0.00
TOTAL OTHER CHARGES DUE AGENT / CARRIER: 130.00 EUR (Assurance & Surcharges)
--------------------------------------------------------------------------------
TOTAL PREPAID: {(o_d['fret_aerien'] + 130.00):>8.2f} EUR       TOTAL COLLECT: 0.00
--------------------------------------------------------------------------------
Executed on (date): {date_exp}           Signature of Shipper or his Agent:
At (place): {a_d['ville']} ({a_d['code']})            AS AGENT OF THE SHIPPER / SELLER
--------------------------------------------------------------------------------
Signature of Issuing Carrier or its Agent:
AIR CARGO GLOBAL EXPRESS - SIGNED ELECTRONICALLY
================================================================================="""

        st.text_area("Aperçu de la LTA / Air Waybill", awb_text, height=450, key=f"awb_txt_{idx_d}")
        st.download_button(
            label=f"⬇️ Télécharger l'Air Waybill officiel ({o_d['reference']})",
            data=awb_text,
            file_name=f"AWB_{o_d['reference']}_{a_d['code']}_CDG.txt",
            key=f"dl_awb_{idx_d}",
            type="primary"
        )