import streamlit as st
import json
import os
import unicodedata
import streamlit.components.v1 as components
import math
import base64
import datetime 

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="DataChango 🛒",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 🧪 MODO PRUEBA ---
MODO_PRUEBA = True 

# --- DATOS DE PROMOS BANCARIAS (CARGA Y TRANSFORMACIÓN) ---
def cargar_y_transformar_promos():
    # Lista de archivos a leer
    archivos_json = ["promos_bancarias.json", "promos_bancarias_coto.json", "promos_bancarias_jumbo.json", "promos_bancarias_masonline.json"]
    
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
                    banco = p.get("banco")
                    desc = p.get("descuento")
                    tope = p.get("tope", "Sin tope")
                    ver_legales = "SI" if p.get("ver_legales") else "NO"
                    link = p.get("link", "#")

                    if super_nm in estructura and dia in estructura[super_nm]:
                        valor_formateado = f"{banco}|{desc}|{tope}|{ver_legales}|{link}"
                        estructura[super_nm][dia].append(valor_formateado)
                        
            except Exception as e:
                print(f"Error cargando {archivo}: {e}")
            
    return estructura

PROMOS_DATA = cargar_y_transformar_promos()

# --- INYECCIÓN DE SCRIPTS GLOBALES ---
def inyectar_recursos_globales():
    GTM_ID = "GTM-PFPW7P44"
    js_global = f"""
    <script>
        (function() {{
            var parentHead = window.parent.document.head;
            var parentBody = window.parent.document.body;
            var parentDoc = window.parent.document;
            if (!parentDoc.getElementById('custom-styles')) {{
                var style = parentDoc.createElement('style');
                style.id = 'custom-styles';
                style.innerHTML = `
                    header[data-testid="stHeader"] {{ display: none !important; }}
                    footer {{ display: none !important; }}
                    #MainMenu {{ display: none !important; }}
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
            if (!window.parent.copyListenerAttached) {{
                parentDoc.addEventListener('click', function(e) {{
                    var target = e.target.closest('.js-copy-btn');
                    if (target) {{
                        var textToCopy = target.getAttribute('data-clipboard-text');
                        if (textToCopy) {{
                            var textArea = parentDoc.createElement("textarea");
                            textArea.value = textToCopy;
                            textArea.style.position = "fixed";
                            textArea.style.left = "-9999px";
                            parentBody.appendChild(textArea);
                            textArea.focus();
                            textArea.select();
                            try {{
                                var successful = parentDoc.execCommand('copy');
                                if(successful) {{
                                    var originalHtml = target.innerHTML;
                                    target.innerHTML = "👍";
                                    target.classList.add('copied');
                                    setTimeout(function() {{
                                        target.innerHTML = originalHtml;
                                        target.classList.remove('copied');
                                    }}, 2000);
                                }}
                            }} catch (err) {{ console.error('Error copy', err); }}
                            parentBody.removeChild(textArea);
                        }}
                    }}
                }});
                window.parent.copyListenerAttached = true;
            }}
        }})();
    </script>
    """
    components.html(js_global, height=0, width=0)

inyectar_recursos_globales()

# --- CONSTANTES Y ESTADO ---
HIPERS = ["Carrefour", "Jumbo", "Coto", "MasOnline"]

if 'categoria_activa' not in st.session_state: st.session_state.categoria_activa = None
if 'filtro_ver_todo' not in st.session_state: st.session_state.filtro_ver_todo = True
for h in HIPERS:
    if f"chk_{h}" not in st.session_state: st.session_state[f"chk_{h}"] = False

# --- UTILIDADES ---
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

def cargar_datos():
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
        elif MODO_PRUEBA:
            fake = []
            if nombre == "Coto": fake = [{"titulo": "Asado", "categoria": ["🥩 Carnes"], "supermercado": "Coto", "imagen": "https://via.placeholder.com/300", "link": "#", "origen_filtro": "Coto", "fecha": "2026-01-01"}] * 3
            if nombre == "Jumbo": fake = [{"titulo": "Detergente", "categoria": ["🧹 Limpieza"], "supermercado": "Jumbo", "imagen": "https://via.placeholder.com/300", "link": "#", "origen_filtro": "Jumbo", "fecha": "2026-01-01"}] * 2
            if fake:
                todas_ofertas.extend(fake)
                conteo_ofertas[nombre] = len(fake)
    return todas_ofertas, conteo_ofertas

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return ""

# --- 3. ESTILOS GLOBALES ---
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
        .contact-container { width: 100%; display: flex; justify-content: flex-end; padding-right: 15px; margin-bottom: 5px; }
        .contact-link-text { font-size: 0.85rem; color: #cfa539 !important; text-decoration: underline; cursor: pointer; font-weight: bold; }

        @media (min-width: 768px) {
            .header-container { flex-direction: column; align-items: center; text-align: center; border-bottom: none; margin-bottom: 20px; }
            .logo-img { width: 180px; height: auto; border-radius: 20px; }
            .app-subtitle { font-size: 1.1rem; text-align: center; }
        }

        div[data-testid="stExpander"] { border: 1px solid #cfa539 !important; border-radius: 8px; background-color: rgba(11, 42, 64, 0.5); }
        .streamlit-expanderHeader { font-size: 1rem !important; color: #cfa539 !important; background-color: transparent !important; }

        .grid-container { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; padding-bottom: 5px; width: 100%; }
        @media (min-width: 600px) { .grid-container { grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 20px; } }
        
        .oferta-card { background-color: #16425b; border-radius: 10px; padding: 8px; border: 1px solid #cfa539; display: flex; flex-direction: column; height: 310px; box-sizing: border-box; transition: transform 0.2s, border-color 0.2s; overflow: hidden; position: relative; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        @media (min-width: 600px) { .oferta-card { padding: 10px; height: 340px; } }
        .oferta-card:hover { transform: translateY(-4px); border-color: #c7501e; box-shadow: 0 8px 12px rgba(199, 80, 30, 0.2); }
        
        .img-container { height: 120px; background: white; border-radius: 6px; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; width: 100%; }
        @media (min-width: 600px) { .img-container { height: 140px; margin-bottom: 10px; } }
        .img-container img { max-height: 95%; max-width: 95%; object-fit: contain; }
        
        .card-title { color: white; font-size: 0.85rem; font-weight: 600; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 6px; height: 34px; word-wrap: break-word; line-height: 1.2; }
        @media (min-width: 600px) { .card-title { font-size: 0.95rem; margin-bottom: 8px; height: 38px; } }
        
        .tag-pill { font-size: 0.65rem; padding: 3px 8px; border-radius: 10px; font-weight: bold; color: white !important; border: none; display: inline-block; box-shadow: 0 1px 3px rgba(0,0,0,0.3); }
        
        .btn-ver-link { background: #c7501e; color: white !important; text-align: center; padding: 6px; border-radius: 5px; text-decoration: none; font-size: 0.8rem; font-weight: bold; display: block; width: 100%; }
        @media (min-width: 600px) { .btn-ver-link { padding: 8px; font-size: 0.9rem; } }
        .btn-ver-link:hover { background-color: #a84015; text-decoration: none; opacity: 0.9; }

        .js-copy-btn { background: transparent; border: 1px solid; border-radius: 5px; cursor: pointer; display: flex; align-items: center; justify-content: center; width: 35px; min-width: 35px; transition: all 0.2s; color: inherit; }
        .js-copy-btn:hover { background-color: rgba(255,255,255,0.1); }
        .js-copy-btn.copied { background-color: #2e7d32 !important; border-color: #2e7d32 !important; color: white !important; }

        /* --- ESTILOS TABLA PROMOS BANCARIAS --- */
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
        
        /* Estilos nuevos para Tope y Legales */
        .tope-txt { font-size: 0.7rem; color: #a4d4ae; margin-top: 2px; display: block; font-style: italic;}
        .link-legales { font-size: 0.7rem; color: #4fc3f7 !important; text-decoration: none; border-bottom: 1px dotted #4fc3f7; margin-top: 2px; display: inline-block; }
        .link-legales:hover { color: white !important; border-bottom-style: solid; }

    </style>
""", unsafe_allow_html=True)

# --- 4. HEADER ---
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
    <div>¿Ideas? <a href="mailto:datachangoweb@gmail.com" target="_blank" rel="noopener noreferrer" class="contact-link-text">Hablemos</a></div>
</div>
""", unsafe_allow_html=True)

# --- 5. LOGICA ---
ofertas_raw, conteos = cargar_datos()

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

# --- CAJA DE FILTROS ---
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

# --- MODULO DE PROMOS BANCARIAS ---
with st.expander("💳 Ver Calendario de Promociones Bancarias", expanded=False):
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
                    # Formato recibido: BANCO|DESCUENTO|TOPE|VER_LEGALES|LINK
                    partes = p.split("|")
                    if len(partes) >= 5:
                        banco = partes[0]
                        desc = partes[1]
                        tope = partes[2]
                        ver_legales = partes[3] # "SI" o "NO"
                        link = partes[4]

                        # Bloque Base
                        html_promo = f'<div class="promo-badge">'
                        html_promo += f'<strong>{desc}</strong>'
                        html_promo += f'<span class="banco-nm">{banco}</span>'
                        
                        # Lógica Condicional: Link o Tope
                        if ver_legales == "SI":
                            html_promo += f'<a href="{link}" target="_blank" class="link-legales">Ver legales 🔗</a>'
                        else:
                            # Solo mostramos el tope si no es "Sin tope" y no es nulo
                            if tope and "sin tope" not in tope.lower() and tope != "None":
                                html_promo += f'<span class="tope-txt">Tope: {tope}</span>'
                        
                        html_promo += '</div>'
                        content += html_promo
            else:
                content = "-"
            
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
            txt_copy = f"Mira esta oferta de {hiper}: {link}".replace("'", "")
            
            card = f"""
            <div class="oferta-card">
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                    <span style="color:#aaa; font-size:0.7rem;">📅 {fecha}</span>
                </div>
                <div class="img-container"><img src="{img}" alt="Producto" onerror="this.style.display='none'"></div>
                <div class="card-title">{titulo}</div>
                <div style="margin-bottom: auto;">
                    <span class="tag-pill" style="background-color: {color_tema};">{tag}</span>
                </div>
                <div style="display: flex; gap: 8px; margin-top: 10px;">
                    <a href="{link}" target="_blank" class="btn-ver-link" style="background-color: {color_tema}; flex: 1;">Ver Oferta</a>
                    <button class="js-copy-btn" data-clipboard-text="{txt_copy}" style="color: {color_tema}; border-color: {color_tema};">🔗</button>
                </div>
            </div>
            """
            cards_html_list.append(card)

        full_grid_html = "".join(cards_html_list).replace("\n", "")
        st.markdown(f'<div class="grid-container">{full_grid_html}</div>', unsafe_allow_html=True)

# --- 7. FOOTER ---
st.markdown("<br><hr style='border-color: #cfa539; opacity: 0.3;'>", unsafe_allow_html=True)
with st.expander("⚖️ Aviso Legal y Exención de Responsabilidad", expanded=False):
    st.markdown("""
    <div style='color:#ccc;font-size:0.8rem;line-height:1.6;text-align:justify;background-color:rgba(0,0,0,0.2);padding:15px;border-radius:8px;'>
        <p><strong>Carácter de la Información:</strong> "DataChango" funciona exclusivamente como un agregador...</p>
        <p><strong>Precios Referenciales:</strong> Los precios son informativos...</p>
        <p><strong>Deslinde:</strong> No garantizamos la exactitud...</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='text-align: center; color: #666; font-size: 0.75rem; margin-top: 10px;'>© 2026 DataChango | <a href='mailto:datachangoweb@gmail.com' style='color:#888;'>Contacto</a></div>", unsafe_allow_html=True)