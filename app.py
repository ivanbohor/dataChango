import streamlit as st
import json
import os
import unicodedata
import streamlit.components.v1 as components
import math
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="DataChango 🛒",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- INYECCIÓN DE GTM + ESTILOS ---
def inyectar_gtm_y_estilos():
    GTM_ID = "GTM-PFPW7P44"
    
    js_code = f"""
    <script>
        (function() {{
            var parentHead = window.parent.document.head;
            var parentBody = window.parent.document.body;

            // 1. ESTILOS DE ESTRUCTURA
            if (!window.parent.document.getElementById('custom-styles')) {{
                var style = window.parent.document.createElement('style');
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

            // 2. GOOGLE TAG MANAGER
            if (!window.parent.document.getElementById('gtm-injected')) {{
                var script = window.parent.document.createElement('script');
                script.id = 'gtm-injected';
                script.text = "(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);}})(window,document,'script','dataLayer','{GTM_ID}');";
                parentHead.insertBefore(script, parentHead.firstChild);
                
                var noscript = window.parent.document.createElement('noscript');
                noscript.innerHTML = '<iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}" height="0" width="0" style="display:none;visibility:hidden"></iframe>';
                parentBody.insertBefore(noscript, parentBody.firstChild);
            }}
        }})();
    </script>
    """
    components.html(js_code, height=0, width=0)

inyectar_gtm_y_estilos()

# --- 1. GESTIÓN DE ESTADO ---
if 'categoria_activa' not in st.session_state: st.session_state.categoria_activa = None
if 'filtro_ver_todo' not in st.session_state: st.session_state.filtro_ver_todo = True

hipers_init = ["Carrefour", "Jumbo", "Coto", "MasOnline"]
for h in hipers_init:
    if f"chk_{h}" not in st.session_state: st.session_state[f"chk_{h}"] = False

# --- 2. UTILIDADES Y SANITIZACIÓN ---
def normalizar_texto(texto):
    if not isinstance(texto, str): return ""
    texto = texto.lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

def sanitizar_oferta(oferta):
    cats_sucias = oferta.get("categoria", [])
    cats_limpias = []
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
        elif "hogar" in c_lower and "bazar" not in c_lower: cats_limpias.append("🏠 Hogar y Bazar")
        elif "automotor" in c_lower and "aire" not in c_lower: cats_limpias.append("🚗 Auto y Aire Libre")
        elif "electro" in c_lower and "tecno" not in c_lower: cats_limpias.append("📺 Electro y Tecno")
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
                    for d in datos: 
                        d["origen_filtro"] = nombre
                        d = sanitizar_oferta(d)
                    todas_ofertas.extend(datos)
                    conteo_ofertas[nombre] = len(datos)
            except: pass
    return todas_ofertas, conteo_ofertas

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: data = f.read()
        return base64.b64encode(data).decode()
    except: return ""

# --- 3. ESTILOS GLOBALES (CSS FINAL) ---
st.markdown("""
    <style>
        .stApp { background-color: #0e3450; }
        h1, h2, h3, h4, h5, h6, p, div, label, span { color: #ffffff !important; }
        
        /* --- CHECKBOX POR DEFECTO (Con icono blanco reforzado) --- */
        div[data-testid="stCheckbox"] label span[data-checked="true"] svg {
            fill: white !important;
            stroke: white !important;
            stroke-width: 3px !important;
        }

        /* --- BOTONES DE CATEGORÍA --- */
        div[data-testid="stButton"] button[kind="primary"] { 
            background-color: #c7501e !important; 
            color: white !important; 
            border: 1px solid #c7501e !important; 
            box-shadow: 0 0 5px rgba(199, 80, 30, 0.5);
        }
        div[data-testid="stButton"] button[kind="secondary"] { 
            background-color: transparent; 
            color: white; 
            border: 1px solid #cfa539; 
        }
        div[data-testid="stButton"] button[kind="secondary"]:hover { 
            background-color: #c7501e; 
            border-color: #c7501e; 
            color: white; 
        }

        /* --- HEADER RESPONSIVO --- */
        .header-container { 
            display: flex; 
            align-items: center; 
            gap: 15px; 
            padding-bottom: 5px; 
            margin-bottom: 10px; 
            border-bottom: 1px solid rgba(207, 165, 57, 0.3); 
        }
        .logo-img { 
            width: 100px; 
            height: 100px; 
            object-fit: contain; 
            border-radius: 10px; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.3); 
            flex-shrink: 0; 
        }
        .header-text-col {
            display: flex;
            flex-direction: column;
            justify-content: center;
            flex: 1; 
        }
        .app-subtitle { 
            font-size: 0.85rem; 
            color: #e0e0e0 !important; 
            font-weight: 300; 
            line-height: 1.3;
            margin-bottom: 5px;
        } 
        
        /* --- LINK DE CONTACTO --- */
        .contact-container {
            width: 100%;
            display: flex;
            justify-content: flex-end; /* SIEMPRE A LA DERECHA (Móvil y PC) */
            padding-right: 15px;
            margin-bottom: 5px; 
        }
        .contact-link-text { 
            font-size: 0.85rem; 
            color: #cfa539 !important; 
            text-decoration: underline; 
            cursor: pointer; 
            font-weight: bold;
        }
        .contact-link-text:hover { color: white !important; }

        /* Escritorio (Pantallas > 768px) */
        @media (min-width: 768px) {
            .header-container { 
                flex-direction: column; 
                align-items: center; 
                text-align: center; 
                gap: 10px; 
                border-bottom: none;
                margin-bottom: 20px;
            }
            .logo-img { width: 180px; height: auto; border-radius: 20px; }
            .header-text-col { align-items: center; }
            .app-subtitle { font-size: 1.1rem; margin-top: 5px; text-align: center; }
            
            /* En escritorio también lo mantenemos a la derecha */
            .contact-container { 
                justify-content: flex-end; 
                padding-right: 20px; 
                padding-bottom: 15px; 
            }
            .contact-link-text { font-size: 0.9rem; }
        }

        /* FILTROS */
        .stCheckbox label { font-size: 0.9rem; }
        div[data-testid="stExpander"] { border: 1px solid #cfa539; border-radius: 8px; background-color: rgba(11, 42, 64, 0.5); }
        .streamlit-expanderHeader { font-size: 1rem !important; color: #cfa539 !important; background-color: transparent !important; }
        div[data-testid="stButton"] button { padding: 0.25rem 0.5rem !important; min-height: 0px !important; height: auto !important; }
        
        /* GRID */
        .grid-container { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; padding-bottom: 20px; }
        .oferta-card { background-color: #16425b; border-radius: 10px; padding: 10px; box-shadow: 0 3px 5px rgba(0,0,0,0.2); border: 1px solid rgba(207, 165, 57, 0.5); display: flex; flex-direction: column; justify-content: space-between; height: 340px; transition: transform 0.2s; }
        .oferta-card:hover { transform: translateY(-3px); border-color: #c7501e; }
        .img-container { height: 140px; background-color: white; border-radius: 6px; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; }
        .img-container img { max-height: 95%; max-width: 95%; object-fit: contain; }
        .card-title { color: white; font-size: 1rem; font-weight: 600; line-height: 1.2; margin-bottom: 5px; height: 40px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; word-wrap: break-word; }
        .super-badge { font-size: 0.7rem; padding: 2px 8px; border-radius: 10px; color: white; font-weight: bold; }
        .btn-ver { background-color: #c7501e; color: white; text-align: center; padding: 8px; border-radius: 5px; text-decoration: none; font-size: 0.9rem; font-weight: bold; display: block; margin-top: auto; }
        .btn-ver:hover { background-color: #a84015; color: white; }
        
        /* Botón Copy con estado Copied */
        .btn-copy { width: 35px; background: transparent; border: 1px solid #cfa539; border-radius: 5px; color: #cfa539; cursor: pointer; transition: all 0.3s ease; white-space: nowrap; overflow: hidden; display: flex; align-items: center; justify-content: center; }
        .btn-copy.copied { background-color: #28a745 !important; border-color: #28a745 !important; color: white !important; width: auto; padding: 0 10px; font-weight: bold; }
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

# --- 5. LOGICA DE DATOS Y FILTROS ---
ofertas_raw, conteos = cargar_datos()
hipers = ["Carrefour", "Jumbo", "Coto", "MasOnline"]
emojis = {"Carrefour": "🛒", "Jumbo": "🛒", "Coto": "🛒", "MasOnline": "🛒"}

def on_change_ver_todo():
    if st.session_state.filtro_ver_todo:
        for k in hipers: st.session_state[f"chk_{k}"] = False

def on_change_hiper(nombre):
    if st.session_state[f"chk_{nombre}"]: st.session_state.filtro_ver_todo = False
    if not any(st.session_state[f"chk_{h}"] for h in hipers): st.session_state.filtro_ver_todo = True

# --- MENU FILTROS (CERRADO) ---
with st.expander("🔎 Filtrar Ofertas", expanded=False):
    c_todo, c_h1, c_h2, c_h3, c_h4 = st.columns(5)
    with c_todo: st.checkbox("Todo", key='filtro_ver_todo', on_change=on_change_ver_todo)
    col_hipers = [c_h1, c_h2, c_h3, c_h4]
    for i, h in enumerate(hipers):
        with col_hipers[i]: st.checkbox(f"{h} ({conteos[h]})", key=f"chk_{h}", on_change=on_change_hiper, args=(h,))

    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    
    categorias = [
        ("🥩 Carnes", "carne"), ("🧀 Lácteos", "lacteos"), ("🍷 Bebidas", "bebida"),
        ("🍝 Almacén", "almacen"), ("🧹 Limpieza", "limpieza"), ("🧴 Perfumería", "perfumeria"),
        ("📺 Electro", "electro"), ("🏠 Hogar", "hogar"), ("🚗 Auto", "automotor"),
        ("🧸 Juguetes", "juguete"), ("🐶 Mascotas", "mascota")
    ]
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

hipers_activos = hipers if st.session_state.filtro_ver_todo else [h for h in hipers if st.session_state[f"chk_{h}"]]
filtro_cat = st.session_state.categoria_activa

# --- BÚSQUEDA Y FILTRADO FINAL ---
mapa_categorias = {
    "carne": "Carnicería", "lacteos": "Lácteos y Frescos", "bebida": "Bebidas", "almacen": "Almacén",
    "limpieza": "Limpieza", "perfumeria": "Perfumería y Bebé", "electro": "Electro y Tecno",
    "hogar": "Hogar y Bazar", "automotor": "Auto y Aire Libre", "juguete": "Juguetería", "mascota": "Mascotas"
}

ofertas_filtradas = []
for oferta in ofertas_raw:
    if oferta.get("origen_filtro") not in hipers_activos: continue 
    if filtro_cat:
        tag_buscado = mapa_categorias.get(filtro_cat, "")
        cats_oferta = oferta.get("categoria", [])
        if not any(tag_buscado.lower() in c.lower() or c.lower() in tag_buscado.lower() for c in cats_oferta): continue
    ofertas_filtradas.append(oferta)

# --- 6. GRID HTML ---
if not ofertas_filtradas:
    st.warning(f"🤷‍♂️ No encontré ofertas para este filtro. Prueba 'Ver Todo'.")
else:
    nombres_mostrar = "Todos" if st.session_state.filtro_ver_todo else ", ".join(hipers_activos)
    
    url_cafecito = "https://cafecito.app/datachango" 
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; flex-wrap: wrap; gap: 10px;">
        <div style="color: #ccc; font-size: 0.9rem;">
            Resultados: <span style="color: white; font-weight: bold;">{len(ofertas_filtradas)}</span> ({nombres_mostrar})
        </div>
        <div style="font-size: 0.85rem; color: #eee;">
            ¿Te sirvió? <a href="{url_cafecito}" target="_blank" style="color: #cfa539; text-decoration: none; font-weight: bold; border-bottom: 1px dotted #cfa539;">Invitame un Cafecito ☕</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    cant_ofertas = len(ofertas_filtradas)
    filas = math.ceil(cant_ofertas / 3) 
    altura_dinamica = (filas * 360) + 100 

    css_cards = """
    <style>
        /* Estilos inyectados arriba */
    </style>
    """

    cards_html = ""
    for i, oferta in enumerate(ofertas_filtradas):
        super_name = oferta.get('supermercado', 'Super')
        link_oferta = oferta.get('link', '#')
        bg_badge = "#d32f2f" if "Coto" in super_name else "#2e7d32" if "Jumbo" in super_name else "#1565c0" if "Carrefour" in super_name else "#ef6c00"
        
        cats_visuales = [c for c in oferta.get('categoria', []) if "Bancarias" not in c][:1] 
        tag_text = cats_visuales[0] if cats_visuales else "Oferta"
        
        texto_copiar = f"Mira esta oferta que encontro DataChango: {link_oferta}".replace("'", "")
        btn_id = f"btn-copy-{i}"

        cards_html += f"""
        <div class="oferta-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span class="super-badge" style="background-color: {bg_badge};">{super_name}</span>
                <span style="color:#aaa; font-size:0.7rem;">{oferta.get('fecha', '')}</span>
            </div>
            <div class="img-container"><img src="{oferta.get('imagen', '')}" alt="Oferta" onerror="this.style.display='none'"></div>
            <div class="card-title">{oferta.get('titulo', 'Oferta')}</div>
            <div style="margin-bottom: auto;"><span style="color: #cfa539; font-size: 0.75rem; border: 1px solid #cfa539; padding: 2px 6px; border-radius: 4px;">{tag_text}</span></div>
            <div style="display: flex; gap: 8px; margin-top: 10px;">
                <a href="{link_oferta}" target="_blank" class="btn-ver" style="flex:1;">Ver Oferta 🛒</a>
                <button id="{btn_id}" class="btn-copy" onclick="copiarLink('{texto_copiar}', '{btn_id}')">🔗</button>
            </div>
        </div>
        """

    components.html(f"""<html><head>{css_cards}<style>
        body {{ margin: 0; padding: 0; font-family: sans-serif; }}
        .grid-container {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; }}
        @media (min-width: 600px) {{ .grid-container {{ grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 20px; }} }}
        .oferta-card {{ background-color: #16425b; border-radius: 8px; padding: 10px; border: 1px solid #cfa539; display: flex; flex-direction: column; height: 320px; box-sizing: border-box; }}
        .img-container {{ height: 130px; background: white; border-radius: 4px; display: flex; align-items: center; justify-content: center; margin-bottom: 5px; }}
        .img-container img {{ max-height: 100%; max-width: 100%; object-fit: contain; }}
        .card-title {{ color: white; font-size: 0.95rem; font-weight: 600; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 5px; height: 36px; word-wrap: break-word; }}
        .super-badge {{ color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; }}
        .btn-ver {{ background: #c7501e; color: white; text-align: center; padding: 8px; border-radius: 4px; text-decoration: none; font-size: 0.9rem; font-weight: bold; display: block; }}
        /* Estilos botón copiar inyectados para el estado 'copied' */
        .btn-copy {{ width: 35px; background: transparent; border: 1px solid #cfa539; border-radius: 5px; color: #cfa539; cursor: pointer; transition: all 0.3s ease; white-space: nowrap; overflow: hidden; display: flex; align-items: center; justify-content: center; }}
        .btn-copy.copied {{ background-color: #28a745 !important; border-color: #28a745 !important; color: white !important; width: auto; padding: 0 10px; font-weight: bold; }}
    </style></head><body><div class="grid-container">{cards_html}</div><script>function copiarLink(t,i){{navigator.clipboard.writeText(t);let b=document.getElementById(i);let org=b.innerHTML; b.innerHTML="Copy"; b.classList.add("copied"); setTimeout(()=>{{b.innerHTML=org; b.classList.remove("copied")}},1500)}}</script></body></html>""", height=altura_dinamica, scrolling=True)

# --- 7. FOOTER ---
st.markdown("<br><hr style='border-color: #cfa539; opacity: 0.3;'>", unsafe_allow_html=True)

with st.expander("⚖️ Aviso Legal y Exención de Responsabilidad", expanded=False):
    st.markdown("""
    <div style='color:#ccc;font-size:0.8rem;line-height:1.6;text-align:justify;background-color:rgba(0,0,0,0.2);padding:15px;border-radius:8px;'>
        <p><strong>Carácter de la Información:</strong> "DataChango" funciona exclusivamente como un agregador y buscador de ofertas. No somos un supermercado ni una tienda online. Nuestra función se limita a recopilar y organizar información pública disponible en los sitios web de terceros.</p>
        <p><strong>Precios Referenciales y No Vinculantes:</strong> Los precios, promociones, descuentos y stock mostrados en este sitio tienen un carácter meramente informativo y referencial. Debido a la naturaleza dinámica de las ofertas, la información puede no estar actualizada en tiempo real. El precio y las condiciones válidas y finales para la compra son SIEMPRE los que figuran en el sitio web oficial del supermercado o vendedor al momento de finalizar la transacción.</p>
        <p><strong>Deslinde de Responsabilidad:</strong> "DataChango" no garantiza la exactitud, vigencia o integridad de la información. No nos responsabilizamos por discrepancias de precios, falta de stock, cambios en las condiciones de las promociones o cualquier perjuicio derivado del uso de esta información. El usuario tiene la obligación de verificar todos los datos directamente en la web del vendedor antes de realizar cualquier compra.</p>
        <p><strong>Propiedad Intelectual:</strong> Todas las marcas comerciales, logotipos, nombres de productos y fotografías mostradas en este sitio son propiedad de sus respectivos titulares y se utilizan aquí únicamente con fines identificatorios y de referencia informativa para el usuario (uso nominativo), sin implicar asociación, patrocinio o endoso alguno por parte de dichas marcas hacia este sitio.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='text-align: center; color: #666; font-size: 0.75rem; margin-top: 10px;'>© 2026 DataChango | <a href='mailto:datachangoweb@gmail.com' style='color:#888;'>Contacto</a></div>", unsafe_allow_html=True)