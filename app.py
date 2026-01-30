import streamlit as st
import json
import os
import unicodedata
import streamlit.components.v1 as components
import base64
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="DataChango 🛒",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- VARIABLES DE ICONOS (COMPACTADOS) ---
ICONO_TELEGRAM = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#229ED9" width="24" height="24"><path d="M20.665 3.717l-17.73 6.837c-1.21.486-1.203 1.161-.222 1.462l4.552 1.42 10.532-6.645c.498-.303.953-.14.579.192l-8.533 7.701h-.002l-.302 4.318c.443 0 .634-.203.882-.448l2.109-2.052 4.37 3.224c.805.442 1.396.216 1.612-.742l2.914-13.725c.297-1.188-.429-1.727-1.188-1.542z"/></svg>'
ICONO_TWITTER = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#1DA1F2" width="22" height="22"><path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/></svg>'

# --- CONEXIÓN A SHEETS ---
@st.cache_resource(ttl=60, show_spinner=False)
def conectar_google_sheets():
    try:
        # 1. Recuperamos las credenciales manejando la estructura anidada o aplanada
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            creds_dict = dict(st.secrets["connections"]["gsheets"])
        elif "connections.gsheets" in st.secrets:
            creds_dict = dict(st.secrets["connections.gsheets"])
        else:
            # Fallback: intentar buscar claves sueltas si no está en connections
            # Esto es útil si pegaste el json directo en secrets.toml sin cabecera [connections.gsheets]
            try:
                creds_dict = dict(st.secrets)
            except:
                return None

        # 2. Fix para saltos de línea en la clave privada
        if creds_dict and "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        # 3. Conectar con gspread
        gc = gspread.service_account_from_dict(creds_dict)
        sh = gc.open("DataChango_Live_DB") # Nombre exacto de tu hoja
        return sh.sheet1

    except Exception as e:
        # print(f"⚠️ Error conectando a Sheets: {e}") # Debug local
        return None

def obtener_alertas_vivas():
    hoja = conectar_google_sheets()
    if not hoja: return []
    try:
        datos = hoja.get_all_records()
        # Filtramos filas vacías o incompletas
        return [d for d in datos if d.get("producto") and str(d.get("producto")).strip() != ""] 
    except:
        return []

# --- NUEVA LÓGICA: MODAL POPUP (DISEÑO MEJORADO) ---
if hasattr(st, "dialog"): # Verificación de versión compatible
    @st.dialog("🚨 Alertas en Vivo - Sentinel", width="large")
    def mostrar_modal_alertas(alertas):
        # ESTILOS CSS ESPECÍFICOS DEL MODAL
        st.markdown("""
        <style>
            /* ESTILO PARA TOP 3 (GRID) */
            .top-card {
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                border: 1px solid #ef4444;
                border-radius: 12px;
                padding: 10px;
                text-align: center;
                height: 100%;
                box-shadow: 0 4px 10px rgba(239, 68, 68, 0.2);
                transition: transform 0.2s;
                display: flex; flex-direction: column; justify-content: space-between;
            }
            .top-card:hover { transform: scale(1.02); }
            .top-img-box {
                background: white; border-radius: 8px; height: 120px; 
                display: flex; align-items: center; justify-content: center;
                margin-bottom: 8px; overflow: hidden;
            }
            .top-img-box img { max-height: 90%; max-width: 90%; object-fit: contain; }
            .top-title { font-size: 0.85rem; font-weight: bold; color: white; height: 40px; overflow: hidden; line-height: 1.2; margin-bottom: 5px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;}
            .top-price { font-size: 1.2rem; color: #ef4444; font-weight: 800; margin-bottom: 5px; }
            .top-tag { background-color: #ef4444; color: white; font-size: 0.7rem; padding: 2px 8px; border-radius: 4px; font-weight: bold; align-self: center; margin-bottom: 5px;}
            
            /* ESTILO PARA EL RESTO (LISTA COMPACTA) */
            .compact-list-container { margin-top: 20px; }
            .compact-row {
                display: flex; align-items: center; justify-content: space-between;
                background-color: rgba(255,255,255,0.05);
                border-bottom: 1px solid rgba(255,255,255,0.1);
                padding: 8px 10px;
                border-radius: 6px;
                margin-bottom: 6px;
                transition: background 0.2s;
            }
            .compact-row:hover { background-color: rgba(255,255,255,0.1); }
            .row-info { flex: 1; padding-right: 10px; overflow: hidden;}
            .row-title { font-size: 0.9rem; color: #e2e8f0; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block;}
            .row-meta { font-size: 0.75rem; color: #94a3b8; }
            .row-price { font-size: 1rem; color: #ef4444; font-weight: bold; min-width: 80px; text-align: right; margin-right: 10px;}
            .btn-go-small {
                background-color: transparent; border: 1px solid #ef4444; color: #ef4444 !important;
                text-decoration: none; font-size: 0.75rem; padding: 4px 10px; border-radius: 4px;
                font-weight: bold; transition: all 0.2s; white-space: nowrap;
            }
            .btn-go-small:hover { background-color: #ef4444; color: white !important; }
        </style>
        """, unsafe_allow_html=True)

        if not alertas:
            st.info("No hay alertas activas en este momento.")
            return

        # Ordenar: Más recientes primero (asumiendo que vienen en orden cronológico, invertimos)
        alertas_recientes = alertas[::-1]
        
        # Separar Top 3 y Resto
        top_3 = alertas_recientes[:3]
        resto = alertas_recientes[3:23] # Limitamos a 20 items extra para no saturar

        # --- SECCIÓN 1: GRID TOP 3 ---
        st.markdown("#### 🔥 Últimas Bombas Detectadas")
        
        # Usamos columns de Streamlit
        cols = st.columns(3)
        for i, item in enumerate(top_3):
            with cols[i]:
                prod = item.get("producto", "Producto")
                precio = item.get("precio", 0)
                desc = item.get("descuento", "")
                link = item.get("link", "#")
                # Intentamos obtener la imagen, si falla usamos placeholder
                img = item.get("link_imagen", "")
                if not img: img = "https://placehold.co/150x150/png?text=Oferta"
                
                st.markdown(f"""
                <div class="top-card">
                    <div class="top-img-box">
                        <img src="{img}">
                    </div>
                    <span class="top-tag">{desc}</span>
                    <div class="top-title">{prod}</div>
                    <div class="top-price">${precio}</div>
                    <a href="{link}" target="_blank" style="text-decoration:none; color:white; background:#ef4444; padding:5px 10px; border-radius:4px; font-size:0.8rem; display:block; font-weight:bold;">VER OFERTA</a>
                </div>
                """, unsafe_allow_html=True)

        # --- SECCIÓN 2: LISTA COMPACTA ---
        if resto:
            st.markdown("<br><h5>📋 Otras Oportunidades Recientes</h5>", unsafe_allow_html=True)
            st.markdown('<div class="compact-list-container">', unsafe_allow_html=True)
            
            for item in resto:
                prod = item.get("producto", "Producto")
                precio = item.get("precio", 0)
                desc = item.get("descuento", "")
                link = item.get("link", "#")
                motivo = item.get("tipo_alerta", "Alerta")
                fecha_raw = str(item.get("fecha", ""))
                hora = fecha_raw.split(" ")[-1] if " " in fecha_raw else fecha_raw

                st.markdown(f"""
                <div class="compact-row">
                    <div class="row-info">
                        <span class="row-title">{prod}</span>
                        <span class="row-meta">🕒 {hora} • {motivo} • {desc}</span>
                    </div>
                    <div class="row-price">${precio}</div>
                    <a href="{link}" target="_blank" class="btn-go-small">IR 🔗</a>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# --- FUNCIONES DE CARGA CON CACHÉ ---
@st.cache_data(ttl=3600, show_spinner=False)
def cargar_y_transformar_promos():
    archivos_json = ["promos_bancarias_carrefour.json", "promos_bancarias_coto.json", "promos_bancarias_jumbo.json", "promos_bancarias_masonline.json"]
    estructura = {
        "Carrefour": {d: [] for d in ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]},
        "Coto": {d: [] for d in ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]},
        "Jumbo": {d: [] for d in ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]},
        "MasOnline": {d: [] for d in ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]}
    }
    for archivo in archivos_json:
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    datos_planos = json.load(f)
                for p in datos_planos:
                    super_nm = p.get("supermercado")
                    dia = p.get("dia")
                    if super_nm in estructura and dia in estructura[super_nm]:
                        valor_formateado = f"{p.get('banco')}|{p.get('descuento')}|{p.get('tope', 'Sin tope')}|{'SI' if p.get('ver_legales') else 'NO'}|{p.get('link', '#')}"
                        estructura[super_nm][dia].append(valor_formateado)
            except: pass
    return estructura

@st.cache_data(ttl=3600, show_spinner=False)
def cargar_datos_ofertas():
    archivos = {"Carrefour": "ofertas_carrefour.json", "Jumbo": "ofertas_jumbo.json", "Coto": "ofertas_coto.json", "MasOnline": "ofertas_masonline.json"}
    todas_ofertas = []
    conteo_ofertas = {k: 0 for k in archivos.keys()} 
    for nombre, archivo in archivos.items():
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                    if isinstance(datos, list):
                        for d in datos: 
                            d["origen_filtro"] = nombre
                            d = sanitizar_oferta(d)
                        todas_ofertas.extend(datos)
                        conteo_ofertas[nombre] = len(datos)
            except: pass
    return todas_ofertas, conteo_ofertas

def normalizar_texto(texto):
    if not isinstance(texto, str): return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto.lower().strip()) if unicodedata.category(c) != 'Mn')

def sanitizar_oferta(oferta):
    cats_sucias = oferta.get("categoria", [])
    cats_limpias = []
    if isinstance(cats_sucias, str): cats_sucias = [cats_sucias]
    for c in cats_sucias:
        c_lower = c.lower()
        if "fresco" in c_lower: cats_limpias.append("🧀 Lácteos y Frescos")
        elif "vario" in c_lower:
            titulo = oferta.get("titulo", "").lower()
            if "toalla" in titulo or "sabana" in titulo: cats_limpias.append("🏠 Hogar y Bazar")
            elif "tv" in titulo or "celu" in titulo: cats_limpias.append("📺 Electro y Tecno")
            elif "juguete" in titulo: cats_limpias.append("🧸 Juguetes")
            else: cats_limpias.append("🍝 Almacén")
        elif "banco" in c_lower or "tarjeta" in c_lower: cats_limpias.append("💳 Bancarias")
        elif "hogar" in c_lower: cats_limpias.append("🏠 Hogar y Bazar")
        elif "automotor" in c_lower: cats_limpias.append("🚗 Auto y Aire Libre")
        elif "electro" in c_lower: cats_limpias.append("📺 Electro y Tecno")
        else: cats_limpias.append(c)
    oferta["categoria"] = list(set(cats_limpias))
    return oferta

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return ""

PROMOS_DATA = cargar_y_transformar_promos()
ofertas_raw, conteos = cargar_datos_ofertas()

# --- INYECCIÓN DE SCRIPTS GLOBALES ---
def inyectar_recursos_globales():
    GTM_ID = "GTM-PFPW7P44"
    js_global = f"""
    <script>
        (function() {{
            var parentDoc = window.parent.document;
            var parentHead = parentDoc.head;
            var parentBody = parentDoc.body;

            if (!parentDoc.getElementById('custom-styles')) {{
                var style = parentDoc.createElement('style');
                style.id = 'custom-styles';
                style.innerHTML = `
                    header[data-testid="stHeader"], footer, #MainMenu {{ display: none !important; }}
                    .block-container {{ padding-top: 1rem !important; padding-bottom: 3rem !important; }}
                    .stApp {{ margin-top: 0px !important; }}
                `;
                parentHead.appendChild(style);
            }}

            if (!parentDoc.getElementById('gtm-injected')) {{
                var script = parentDoc.createElement('script');
                script.id = 'gtm-injected';
                script.text = "(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);}})(window,document,'script','dataLayer','{GTM_ID}');";
                parentHead.insertBefore(script, parentHead.firstChild);
            }}

            if (!parentDoc.getElementById('imgModal')) {{
                var modal = parentDoc.createElement('div');
                modal.id = 'imgModal';
                modal.style.cssText = "display:none; position:fixed; z-index:999999; padding-top:50px; left:0; top:0; width:100%; height:100%; overflow:auto; background-color:rgba(0,0,0,0.9); backdrop-filter:blur(5px);";
                var close = parentDoc.createElement('span');
                close.innerHTML = "&times;";
                close.style.cssText = "position:absolute; top:15px; right:35px; color:#f1f1f1; font-size:40px; font-weight:bold; cursor:pointer; z-index:1000000;";
                close.onclick = function() {{ modal.style.display = "none"; }};
                var modalImg = parentDoc.createElement('img');
                modalImg.id = 'imgModalContent';
                modalImg.style.cssText = "margin:auto; display:block; max-width:90%; max-height:85vh; border-radius:8px; box-shadow:0 0 20px rgba(255,255,255,0.1); object-fit:contain;";
                modal.appendChild(close);
                modal.appendChild(modalImg);
                modal.onclick = function(e) {{
                    if (e.target === modal) modal.style.display = "none";
                }}
                parentBody.appendChild(modal);
            }}

            window.parent.openImageModal = function(src) {{
                var modal = parentDoc.getElementById('imgModal');
                var modalImg = parentDoc.getElementById('imgModalContent');
                modalImg.src = src;
                modal.style.display = "flex";
                modal.style.alignItems = "center";
                modal.style.justifyContent = "center";
            }};

            if (!window.parent.globalListenersAttached) {{
                parentDoc.addEventListener('click', function(e) {{
                    var zoomTarget = e.target.closest('.js-zoomable');
                    if (zoomTarget) {{
                        var imgSrc = zoomTarget.getAttribute('data-src');
                        if (imgSrc) {{
                            window.parent.openImageModal(imgSrc);
                            e.stopPropagation(); 
                        }}
                    }}
                    var copyTarget = e.target.closest('.js-copy-btn');
                    if (copyTarget) {{
                        var textToCopy = copyTarget.getAttribute('data-clipboard-text');
                        if (textToCopy) {{
                            var textArea = parentDoc.createElement("textarea");
                            textArea.value = textToCopy;
                            textArea.style.position = "fixed";
                            textArea.style.left = "-9999px";
                            parentBody.appendChild(textArea);
                            textArea.focus();
                            textArea.select();
                            try {{
                                parentDoc.execCommand('copy');
                                var originalHtml = copyTarget.innerHTML;
                                copyTarget.innerHTML = "👍";
                                copyTarget.classList.add('copied');
                                setTimeout(function() {{
                                    copyTarget.innerHTML = originalHtml;
                                    copyTarget.classList.remove('copied');
                                }}, 2000);
                            }} catch (err) {{ console.error('Error copy', err); }}
                            parentBody.removeChild(textArea);
                        }}
                    }}
                }});
                window.parent.globalListenersAttached = true;
            }}
        }})();
    </script>
    """
    components.html(js_global, height=0, width=0)

inyectar_recursos_globales()

# --- CONSTANTES ---
HIPERS = ["Carrefour", "Jumbo", "Coto", "MasOnline"]
if 'categoria_activa' not in st.session_state: st.session_state.categoria_activa = None
if 'filtro_ver_todo' not in st.session_state: st.session_state.filtro_ver_todo = True
for h in HIPERS:
    if f"chk_{h}" not in st.session_state: st.session_state[f"chk_{h}"] = False

# --- ESTILOS CSS ---
st.markdown("""
    <style>
        .stApp { background-color: #0e3450; }
        h1, h2, h3, h4, h5, h6, p, div, label, span { color: #ffffff !important; }
        div[data-testid="stCheckbox"] label span[data-checked="true"] svg { fill: white !important; stroke: white !important; stroke-width: 3px !important; }
        div[data-testid="stButton"] button[kind="primary"] { background-color: #c7501e !important; color: white !important; border: 1px solid #c7501e !important; box-shadow: 0 0 5px rgba(199, 80, 30, 0.5); }
        div[data-testid="stButton"] button[kind="secondary"] { background-color: transparent; color: white; border: 1px solid #cfa539; }
        div[data-testid="stButton"] button[kind="secondary"]:hover { background-color: #c7501e; border-color: #c7501e; }

        .header-container { display: flex; align-items: center; gap: 15px; padding-bottom: 5px; margin-bottom: 10px; border-bottom: 1px solid rgba(207, 165, 57, 0.3); }
        .logo-img { width: 100px; height: 100px; object-fit: contain; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.3); flex-shrink: 0; }
        .header-text-col { display: flex; flex-direction: column; justify-content: center; flex: 1; }
        .app-subtitle { font-size: 0.85rem; color: #e0e0e0 !important; font-weight: 300; line-height: 1.3; } 
        
        .contact-container { width: 100%; display: flex; justify-content: flex-end; align-items: center; padding-right: 15px; margin-bottom: 5px; gap: 12px; }
        .contact-label { font-size: 0.85rem; color: #ccc !important; font-weight: bold; }
        
        .social-link { text-decoration: none; display: inline-flex; align-items: center; justify-content: center; transition: transform 0.2s ease-in-out; }
        .social-link:hover { transform: scale(1.15); }
        .social-link:hover svg path { fill: #ffffff !important; }
        .social-link svg { filter: drop-shadow(0 2px 3px rgba(0,0,0,0.3)); transition: all 0.2s; }

        @media (min-width: 768px) {
            .header-container { flex-direction: column; align-items: center; text-align: center; border-bottom: none; margin-bottom: 20px; }
            .logo-img { width: 180px; height: auto; border-radius: 20px; }
            .app-subtitle { font-size: 1.1rem; text-align: center; }
            .contact-container { justify-content: center; margin-top: 10px; }
        }

        div[data-testid="stExpander"] { border: 1px solid #cfa539 !important; border-radius: 8px; background-color: rgba(11, 42, 64, 0.5); }
        .streamlit-expanderHeader { font-size: 1rem !important; color: #cfa539 !important; background-color: transparent !important; }

        .grid-container { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; padding-bottom: 5px; width: 100%; }
        @media (min-width: 600px) { .grid-container { grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 20px; } }
        
        .oferta-card { background-color: #16425b; border-radius: 10px; padding: 8px; border: 1px solid #cfa539; display: flex; flex-direction: column; height: 310px; box-sizing: border-box; transition: transform 0.2s, border-color 0.2s; overflow: hidden; position: relative; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        @media (min-width: 600px) { .oferta-card { padding: 10px; height: 340px; } }
        .oferta-card:hover { transform: translateY(-4px); border-color: #c7501e; box-shadow: 0 8px 12px rgba(199, 80, 30, 0.2); }
        
        .img-container { height: 120px; background: white; border-radius: 6px; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; width: 100%; position: relative; cursor: zoom-in; overflow: hidden; }
        @media (min-width: 600px) { .img-container { height: 140px; margin-bottom: 10px; } }
        .img-container img { max-height: 95%; max-width: 95%; object-fit: contain; transition: transform 0.3s ease; }
        .img-container::after { content: "🔎"; font-size: 24px; color: white; display: flex; align-items: center; justify-content: center; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.4); opacity: 0; transition: opacity 0.3s; pointer-events: none; }
        .img-container:hover::after { opacity: 1; }
        .img-container:hover img { transform: scale(1.05); }

        .card-title { color: white; font-size: 0.85rem; font-weight: 600; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 6px; height: 34px; word-wrap: break-word; line-height: 1.2; }
        @media (min-width: 600px) { .card-title { font-size: 0.95rem; margin-bottom: 8px; height: 38px; } }
        .tag-pill { font-size: 0.65rem; padding: 3px 8px; border-radius: 10px; font-weight: bold; color: white !important; border: none; display: inline-block; box-shadow: 0 1px 3px rgba(0,0,0,0.3); }
        .btn-ver-link { background: #c7501e; color: white !important; text-align: center; padding: 6px; border-radius: 5px; text-decoration: none; font-size: 0.8rem; font-weight: bold; display: block; width: 100%; }
        @media (min-width: 600px) { .btn-ver-link { padding: 8px; font-size: 0.9rem; } }
        .btn-ver-link:hover { background-color: #a84015; text-decoration: none; opacity: 0.9; }
        .js-copy-btn { background: transparent; border: 1px solid; border-radius: 5px; cursor: pointer; display: flex; align-items: center; justify-content: center; width: 35px; min-width: 35px; transition: all 0.2s; color: inherit; }
        .js-copy-btn:hover { background-color: rgba(255,255,255,0.1); }
        .js-copy-btn.copied { background-color: #2e7d32 !important; border-color: #2e7d32 !important; color: white !important; }

        .promo-table-container { overflow-x: auto; margin-bottom: 20px; border-radius: 8px; border: 1px solid #cfa539; box-shadow: 0 4px 8px rgba(0,0,0,0.3); }
        .promo-table { width: 100%; border-collapse: collapse; min-width: 600px; font-size: 0.85rem; }
        .promo-table th { background-color: #0b2a40; color: #cfa539; padding: 12px 8px; text-transform: uppercase; border-bottom: 2px solid #cfa539; text-align: center; font-weight: 800; letter-spacing: 0.5px; }
        .promo-table td { padding: 8px; text-align: center; border-bottom: 1px solid rgba(207, 165, 57, 0.2); color: #ddd; vertical-align: top; }
        .promo-table tr:last-child td { border-bottom: none; }
        .promo-table tr:nth-child(even) { background-color: rgba(255,255,255,0.03); }
        .today-col { background-color: rgba(207, 165, 57, 0.15) !important; border-left: 1px solid rgba(207, 165, 57, 0.3); border-right: 1px solid rgba(207, 165, 57, 0.3); }
        .today-header { background-color: #c7501e !important; color: white !important; border-bottom: 2px solid white !important; }
        .promo-badge { display: block; background-color: #1e3a5f; padding: 6px; border-radius: 4px; margin-bottom: 6px; border: 1px solid rgba(255,255,255,0.1); font-size: 0.75rem; text-align: left; position: relative; }
        .promo-badge strong { color: #fff; display: block; font-size: 0.9rem; margin-bottom: 2px; }
        .promo-badge .banco-nm { color: #aaa; font-weight: normal; font-size: 0.8rem; margin-bottom: 2px; display: block;}
        .tope-txt { font-size: 0.7rem; color: #a4d4ae; margin-top: 2px; display: block; font-style: italic;}
        .link-legales { font-size: 0.7rem; color: #4fc3f7 !important; text-decoration: none; border-bottom: 1px dotted #4fc3f7; margin-top: 2px; display: inline-block; }
        .link-legales:hover { color: white !important; border-bottom-style: solid; }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(220, 38, 38, 0); }
            100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
        }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
logo_file = "logo.jpg" 
img_src = f"data:image/jpeg;base64,{get_img_as_base64(logo_file)}" if os.path.exists(logo_file) else ""

st.markdown(f"""
<div class="header-container">
    <img src="{img_src}" class="logo-img">
    <div class="header-text-col">
        <div class="app-subtitle">
            Las <span style="font-weight: bold; color: white;">mejores ofertas</span> de los principales Hipermercados. <br> No scrollees de más, ahorrá tiempo y dinero!
        </div>
    </div>
</div>
<div class="contact-container">
    <span class="contact-label"> 🚨 Alertas de precios y actualizaciones en:</span>
    <a href="https://t.me/datachango_ofertas" target="_blank" class="social-link" title="Canal de Telegram">
        {ICONO_TELEGRAM}
    </a>
    <a href="https://x.com/DataChangoAr" target="_blank" class="social-link" title="Seguinos en X">
        {ICONO_TWITTER}
    </a>
</div>
""", unsafe_allow_html=True)

# --- BOTÓN ALERTAS EN VIVO (INYECTADO) ---
alertas_activas = obtener_alertas_vivas()
cantidad_alertas = len(alertas_activas)

if cantidad_alertas > 0:
    st.markdown(f"""
    <div style="display: flex; justify-content: center; margin-top: -10px; margin-bottom: 20px;">
        <div style="
            background: linear-gradient(90deg, #7f1d1d 0%, #b91c1c 100%);
            padding: 2px; border-radius: 12px; box-shadow: 0 0 15px rgba(220, 38, 38, 0.5);
            animation: pulse 2s infinite; width: 100%; max-width: 600px;
        ">
    """, unsafe_allow_html=True)
    
    if st.button(f"🚨 ALERTAS EN VIVO ({cantidad_alertas}) - CLICK PARA VER 🔥", type="primary", use_container_width=True):
        mostrar_modal_alertas(alertas_activas)
        
    st.markdown("</div></div>", unsafe_allow_html=True)

ESTILOS_SUPER = {
    "Carrefour": {"color": "#1e40af", "icono": "🔵"}, 
    "Coto":      {"color": "#d32f2f", "icono": "🔴"}, 
    "Jumbo":     {"color": "#2e7d32", "icono": "🟢"}, 
    "MasOnline": {"color": "#ef6c00", "icono": "🟠"}, 
    "default":   {"color": "#cfa539", "icono": "🛒"}
}

def on_change_ver_todo():
    if st.session_state.filtro_ver_todo:
        for k in HIPERS: st.session_state[f"chk_{k}"] = False
def on_change_hiper(nombre):
    if st.session_state[f"chk_{nombre}"]: st.session_state.filtro_ver_todo = False
    if not any(st.session_state[f"chk_{h}"] for h in HIPERS): st.session_state.filtro_ver_todo = True

# --- FILTROS ---
with st.expander("🔎 Filtrar Ofertas", expanded=False):
    c_todo, c_h1, c_h2, c_h3, c_h4 = st.columns(5)
    with c_todo: st.checkbox("Todo", key='filtro_ver_todo', on_change=on_change_ver_todo)
    col_hipers = [c_h1, c_h2, c_h3, c_h4]
    for i, h in enumerate(HIPERS):
        with col_hipers[i]: st.checkbox(f"{h} ({conteos[h]})", key=f"chk_{h}", on_change=on_change_hiper, args=(h,))
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    categorias = [("🥩 Carnes", "carne"), ("🧀 Lácteos", "lacteos"), ("🍷 Bebidas", "bebida"), ("🍝 Almacén", "almacen"), ("🧹 Limpieza", "limpieza"), ("🧴 Perfumería", "perfumeria"), ("📺 Electro", "electro"), ("🏠 Hogar", "hogar"), ("🚗 Auto", "automotor"), ("🧸 Juguetes", "juguete"), ("🐶 Mascotas", "mascota")]
    cols_cat, cols_cat_2 = st.columns(6), st.columns(5)
    all_cols = cols_cat + cols_cat_2
    
    def toggle_categoria(cat_key):
        st.session_state.categoria_activa = None if st.session_state.categoria_activa == cat_key else cat_key
        
    for i, (label, key) in enumerate(categorias):
        btn_type = "primary" if st.session_state.categoria_activa == key else "secondary"
        if i < len(all_cols):
            if all_cols[i].button(label, key=f"btn_{key}", type=btn_type, use_container_width=True):
                toggle_categoria(key)
                st.rerun()

# --- PROMOS BANCARIAS ---
with st.expander("💳 Calendario de Descuentos Bancarios (Online)", expanded=False):
    dia_semana_hoy = datetime.datetime.today().weekday()
    dias = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    headers = ["LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM"]
    html_table = '<div class="promo-table-container"><table class="promo-table"><thead><tr><th style="text-align:left; padding-left:15px;">Supermercado</th>'
    for i, h in enumerate(headers):
        clase_hoy = "today-header" if i == dia_semana_hoy else ""
        html_table += f'<th class="{clase_hoy}">{h}</th>'
    html_table += '</tr></thead><tbody>'
    for hiper, dias_data in PROMOS_DATA.items():
        estilo = ESTILOS_SUPER.get(hiper, ESTILOS_SUPER["default"])
        icono = estilo["icono"]
        html_table += f'<tr><td style="font-weight:bold; color:white; border-right:1px solid #cfa539; padding-left:10px;">{icono} {hiper}</td>'
        for i, dia_key in enumerate(dias):
            clase_celda = "today-col" if i == dia_semana_hoy else ""
            promos = dias_data.get(dia_key, [])
            content = ""
            if promos:
                for p in promos:
                    partes = p.split("|")
                    if len(partes) >= 5:
                        banco, desc, tope, ver_legales, link = partes[0], partes[1], partes[2], partes[3], partes[4]
                        html_promo = f'<div class="promo-badge"><strong>{desc}</strong><span class="banco-nm">{banco}</span>'
                        if ver_legales == "SI": html_promo += f'<a href="{link}" target="_blank" class="link-legales">Ver legales 🔗</a>'
                        else:
                            if tope and "sin tope" not in tope.lower() and tope != "None": html_promo += f'<span class="tope-txt">Tope: {tope}</span>'
                        html_promo += '</div>'
                        content += html_promo
            else: content = "-"
            html_table += f'<td class="{clase_celda}">{content}</td>'
        html_table += '</tr>'
    html_table += '</tbody></table></div>'
    st.markdown(html_table, unsafe_allow_html=True)

# --- RENDERIZADO GRID ---
hipers_activos = HIPERS if st.session_state.filtro_ver_todo else [h for h in HIPERS if st.session_state[f"chk_{h}"]]
filtro_cat = st.session_state.categoria_activa
mapa_categorias = {"carne": "Carnicería", "lacteos": "Lácteos", "bebida": "Bebidas", "almacen": "Almacén", "limpieza": "Limpieza", "perfumeria": "Perfumería", "electro": "Electro", "hogar": "Hogar", "automotor": "Auto", "juguete": "Juguetería", "mascota": "Mascotas"}

ofertas_globales = []
for oferta in ofertas_raw:
    if oferta.get("origen_filtro") not in hipers_activos: continue 
    if filtro_cat:
        tag_buscado = mapa_categorias.get(filtro_cat, "")
        if not any(tag_buscado.lower() in c.lower() or c.lower() in tag_buscado.lower() for c in oferta.get("categoria", [])): continue
    ofertas_globales.append(oferta)

if not ofertas_globales:
    st.warning(f"🤷‍♂️ No encontré ofertas para este filtro.")
else:
    url_cafecito = "https://cafecito.app/datachango" 
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; flex-wrap: wrap; gap: 10px;">
        <div style="color: #ccc; font-size: 0.9rem;">
            Resultados: <span style="color: white; font-weight: bold;">{len(ofertas_globales)}</span>
        </div>
        <div style="font-size: 0.85rem; color: #eee;">
            <a href="{url_cafecito}" target="_blank" style="color: #cfa539; text-decoration: none; font-weight: bold; border-bottom: 1px dotted #cfa539;">Invitame un Cafecito ☕</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    for hiper in hipers_activos:
        ofertas_seccion = [o for o in ofertas_globales if o.get('origen_filtro') == hiper]
        if not ofertas_seccion: continue

        estilo = ESTILOS_SUPER.get(hiper, ESTILOS_SUPER["default"])
        color_tema = estilo["color"]
        icono = estilo["icono"]
        
        st.markdown(f"""
        <div style="
            border-left: 6px solid {color_tema}; 
            padding-left: 15px; margin-top: 25px; margin-bottom: 15px; 
            background: linear-gradient(90deg, rgba(255,255,255,0.05) 0%, transparent 100%);
            border-radius: 0 8px 8px 0; display: flex; align-items: center; height: 50px;
        ">
            <h2 style="margin: 0; color: white !important; text-transform: uppercase; font-weight: 800; font-size: 1.5rem; display: flex; align-items: center; gap: 10px;">
                <span style="filter: drop-shadow(0 0 5px {color_tema});">{icono}</span> {hiper}
            </h2>
            <span style="margin-left: auto; margin-right: 15px; color: #aaa; font-size: 0.9rem;">({len(ofertas_seccion)})</span>
        </div>
        """, unsafe_allow_html=True)

        cards_html_list = []
        for i, oferta in enumerate(ofertas_seccion):
            link = oferta.get('link', '#')
            titulo = oferta.get('titulo', 'Oferta')
            img = oferta.get('imagen', '')
            fecha = oferta.get('fecha', '')
            cats_vis = [c for c in oferta.get('categoria', []) if "Bancarias" not in c][:1] 
            tag = cats_vis[0] if cats_vis else "Oferta"
            txt_copy = f"Mira esta oferta que encontre en DataChango: {link}".replace("'", "")
            
            # --- CARD BLINDADA ---
            btn_style = f"color: {color_tema}; border-color: {color_tema};"
            
            card = f"""
            <div class="oferta-card">
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                    <span style="color:#aaa; font-size:0.7rem;">📅 {fecha}</span>
                </div>
                <div class="img-container js-zoomable" data-src="{img}">
                    <img src="{img}" alt="Producto" onerror="this.style.display='none'">
                </div>
                <div class="card-title">{titulo}</div>
                <div style="margin-bottom: auto;">
                    <span class="tag-pill" style="background-color: {color_tema};">{tag}</span>
                </div>
                <div style="display: flex; gap: 8px; margin-top: 10px;">
                    <a href="{link}" target="_blank" class="btn-ver-link" style="background-color: {color_tema}; flex: 1;">Ver Oferta</a>
                    <button class="js-copy-btn" data-clipboard-text="{txt_copy}" style="{btn_style}">🔗</button>
                </div>
            </div>
            """
            cards_html_list.append(card)

        full_grid_html = "".join(cards_html_list).replace("\n", "")
        st.markdown(f'<div class="grid-container">{full_grid_html}</div>', unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("<br><hr style='border-color: #cfa539; opacity: 0.3;'>", unsafe_allow_html=True)
with st.expander("⚖️ Aviso Legal y Exención de Responsabilidad", expanded=False):
    st.markdown("""
    <div style='color:#ccc;font-size:0.8rem;line-height:1.6;text-align:justify;background-color:rgba(0,0,0,0.2);padding:15px;border-radius:8px;'>
        <p><strong>Carácter de la Información:</strong> "DataChango" funciona exclusivamente como un agregador y buscador de ofertas...</p>
    </div>
    """, unsafe_allow_html=True)
st.markdown("<div style='text-align: center; color: #666; font-size: 0.75rem; margin-top: 10px;'>© 2026 DataChango | <a href='mailto:datachangoweb@gmail.com' style='color:#888;'>Contacto</a></div>", unsafe_allow_html=True)