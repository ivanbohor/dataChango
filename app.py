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

# --- INYECCIÓN DE GTM + ESTILOS FORZADOS (JAVA SCRIPT NUCLEAR) ---
def inyectar_gtm_y_estilos():
    # Tu ID real de GTM
    GTM_ID = "GTM-PFPW7P44"
    
    # Este script hace 2 cosas:
    # 1. Inyecta Google Tag Manager en la ventana principal (Padre)
    # 2. Inyecta CSS en la ventana principal para ocultar la barra negra y el footer
    js_code = f"""
    <script>
        (function() {{
            var parentHead = window.parent.document.head;
            var parentBody = window.parent.document.body;

            // --- A. INYECCIÓN DE ESTILOS (OCULTAR BARRA) ---
            if (!window.parent.document.getElementById('custom-styles')) {{
                var style = window.parent.document.createElement('style');
                style.id = 'custom-styles';
                style.innerHTML = `
                    header[data-testid="stHeader"] {{ display: none !important; }}
                    footer {{ display: none !important; }}
                    #MainMenu {{ display: none !important; }}
                    .stApp {{ margin-top: 0px !important; }} 
                `;
                parentHead.appendChild(style);
                console.log("Estilos inyectados: Barra oculta.");
            }}

            // --- B. INYECCIÓN DE GOOGLE TAG MANAGER ---
            if (!window.parent.document.getElementById('gtm-injected')) {{
                // 1. Script en HEAD
                var script = window.parent.document.createElement('script');
                script.id = 'gtm-injected';
                script.innerHTML = "(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);}})(window,document,'script','dataLayer','{GTM_ID}');";
                parentHead.appendChild(script);
                
                // 2. Noscript en BODY
                var noscript = window.parent.document.createElement('noscript');
                noscript.innerHTML = '<iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}" height="0" width="0" style="display:none;visibility:hidden"></iframe>';
                parentBody.appendChild(noscript);
                
                console.log("GTM inyectado correctamente.");
            }}
        }})();
    </script>
    """
    components.html(js_code, height=0, width=0)

# Ejecutamos la inyección al inicio
inyectar_gtm_y_estilos()

# --- 1. GESTIÓN DE ESTADO ---
if 'categoria_activa' not in st.session_state:
    st.session_state.categoria_activa = None
if 'filtro_ver_todo' not in st.session_state: 
    st.session_state.filtro_ver_todo = True

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
    archivos = {
        "Carrefour": "ofertas_carrefour.json",
        "Jumbo": "ofertas_jumbo.json",
        "Coto": "ofertas_coto.json",
        "MasOnline": "ofertas_masonline.json"
    }
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

# --- 3. ESTILOS GLOBALES (CSS INTERNO) ---
# Mantenemos esto para los elementos DENTRO de la app (botones, tarjetas)
st.markdown("""
    <style>
        .stApp { background-color: #0e3450; }
        h1, h2, h3, h4, h5, h6, p, div, label, span { color: #ffffff !important; }
        .stCheckbox label { color: #ffffff !important; font-size: 1rem; font-weight: 500; }
        div[data-testid="stVerticalBlock"] > div > div[data-testid="stCheckbox"] { display: flex; justify-content: center; }
        
        @media (max-width: 768px) {
            div[data-testid="column"] { display: flex; flex-direction: column; align-items: center; text-align: center; }
            .stButton { width: 100%; display: flex; justify-content: center; }
        }
        @media (min-width: 768px) {
            div[data-testid="stExpander"] details { border: none !important; box-shadow: none !important; background-color: transparent !important; }
            div[data-testid="stExpander"] details > summary { display: none !important; }
            div[data-testid="stExpander"] details > div { padding-left: 0 !important; padding-right: 0 !important; }
        }
        .streamlit-expanderHeader { background-color: #0b2a40; border: 1px solid #cfa539; border-radius: 8px; color: #cfa539 !important; font-weight: bold; }
        .streamlit-expanderContent { background-color: #0b2a40; border: 1px solid #cfa539; border-top: none; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; color: #ccc !important; }
        hr { border-color: #cfa539; opacity: 0.5; }
        
        div[data-testid="stButton"] button[kind="secondary"] { background-color: transparent; color: #ffffff; border: 1px solid #cfa539; border-radius: 20px; transition: all 0.3s; width: 100%; }
        div[data-testid="stButton"] button[kind="secondary"]:hover { background-color: #c7501e; border-color: #c7501e; color: white; transform: scale(1.05); }
        div[data-testid="stButton"] button[kind="primary"] { background-color: #c7501e !important; color: white !important; border: 1px solid #c7501e !important; border-radius: 20px; width: 100%; box-shadow: 0 0 10px rgba(199, 80, 30, 0.6); }
        
        .filter-title { text-align: center; font-size: 1.5rem !important; font-weight: 600; margin-bottom: 20px; margin-top: 10px; color: #cfa539 !important; text-transform: uppercase; letter-spacing: 1.5px; }
        .contact-link-text { color: white !important; text-decoration: underline; cursor: pointer; }
        .contact-link-text:hover { color: #cfa539 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. CABECERA (LIMPIA) ---
logo_file = "logo.jpg" 
if os.path.exists(logo_file):
    img_b64 = get_img_as_base64(logo_file)
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; padding-top: 10px;">
        <img src="data:image/jpeg;base64,{img_b64}" style="width: 250px; height: auto; border-radius: 20px; object-fit: contain; box-shadow: 0 4px 15px rgba(0,0,0,0.3); display: block;">
        <h4 style='text-align: center; color: #cfa539 !important; font-weight: 300; letter-spacing: 1px; text-transform: uppercase; margin-top: 20px; font-size: 1.1rem; line-height: 1.6;'>
            Las <span style="font-weight: bold; color: white;">mejores ofertas</span> de los principales Hipermercados en un solo lugar.<br>
            <span style="font-size: 0.95rem; text-transform: none; color: #e0e0e0; letter-spacing: 0.5px;">DataChango hace las búsquedas de ofertas por vos, ahorrandote tiempo y dinero!</span>
        </h4>
        <div style="text-align: center; margin-top: 10px; font-weight: bold; color: white; font-size: 0.9rem;">
            ¿Ideas, sugerencias? <a href="mailto:datachangoweb@gmail.com" class="contact-link-text">Hablemos</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
else: st.warning(f"⚠️ Falta el archivo '{logo_file}' en la carpeta.")

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

# --- MENU DESPLEGABLE ---
with st.expander("🎯 FILTROS Y CATEGORÍAS", expanded=False):
    st.markdown('<p class="filter-title">Filtros por Supermercado</p>', unsafe_allow_html=True)
    c_todo, c_h1, c_h2, c_h3, c_h4 = st.columns(5)
    with c_todo: st.checkbox("✅ Todo", key='filtro_ver_todo', on_change=on_change_ver_todo)
    col_hipers = [c_h1, c_h2, c_h3, c_h4]
    for i, h in enumerate(hipers):
        with col_hipers[i]: st.checkbox(f"{emojis[h]} {h} ({conteos[h]})", key=f"chk_{h}", on_change=on_change_hiper, args=(h,))

    st.markdown("---")
    st.markdown('<p class="filter-title">⚡ Filtrar por Rubro</p>', unsafe_allow_html=True)

    categorias = [
        ("🥩 Carnes", "carne"), ("🧀 Lácteos y Frescos", "lacteos"), ("🍷 Bebidas", "bebida"),
        ("🍝 Almacén", "almacen"), ("🧹 Limpieza", "limpieza"), ("🧴 Perfumería y Bebé", "perfumeria"),
        ("📺 Electro y Tecno", "electro"), ("🏠 Hogar y Bazar", "hogar"), ("🚗 Auto y Aire Libre", "automotor"),
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
    nombres_mostrar = "Todos los Supermercados" if st.session_state.filtro_ver_todo else ", ".join(hipers_activos)
    
    # === AQUI ESTÁ EL CAFECITO DISCRETO ===
    url_cafecito = "https://cafecito.app/datachango" 
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <div style="color: #ccc; font-size: 1rem; margin-bottom: 8px;">
            Mostrando <span style="color: white; font-weight: bold;">{len(ofertas_filtradas)}</span> ofertas de: {nombres_mostrar}
        </div>
        <div style="font-size: 0.9rem; color: #eee;">
            ¿Te sirvió DataChango? <a href="{url_cafecito}" target="_blank" style="color: #cfa539; text-decoration: underline; font-weight: bold; margin-left: 5px;">Invitame un Cafecito ☕</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    # ======================================
    
    cant_ofertas = len(ofertas_filtradas)
    filas = math.ceil(cant_ofertas / 3) 
    altura_dinamica = (filas * 400) + 100 

    css_styles = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
        body { margin: 0; padding: 10px; font-family: 'Roboto', sans-serif; background-color: transparent; }
        .grid-container { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; padding-bottom: 20px; }
        .oferta-card { background-color: #16425b; border-radius: 12px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border: 1px solid #cfa539; display: flex; flex-direction: column; justify-content: space-between; transition: transform 0.2s, box-shadow 0.2s; height: 380px; }
        .oferta-card:hover { transform: translateY(-5px); box-shadow: 0 8px 20px rgba(199, 80, 30, 0.4); border-color: #c7501e; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .super-badge { font-weight: 700; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; color: white; }
        .date-text { color: #ccc; font-size: 0.75rem; }
        .img-container { width: 100%; height: 160px; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; overflow: hidden; background-color: white; border-radius: 8px; }
        .img-container img { max-height: 100%; max-width: 100%; object-fit: contain; }
        .card-title { font-size: 1.1rem; font-weight: 600; color: #ffffff; margin-bottom: 8px; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .tags { margin-bottom: auto; }
        .tag { background-color: #0e3450; color: #cfa539; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; border: 1px solid #cfa539; margin-right: 5px; display: inline-block; }
        .btn-row { display: flex; gap: 10px; margin-top: 15px; }
        .btn-ver { flex: 1; padding: 10px; background-color: #c7501e; color: white; text-align: center; border-radius: 6px; text-decoration: none; font-weight: 500; font-size: 0.9rem; transition: background 0.2s; border: none; }
        .btn-ver:hover { background-color: #a84015; color: white; }
        .btn-copy { width: 45px; display: flex; align-items: center; justify-content: center; background-color: transparent; border: 1px solid #cfa539; border-radius: 6px; cursor: pointer; font-size: 1.2rem; transition: all 0.3s ease; color: #cfa539; }
        .btn-copy:hover { background-color: #cfa539; color: #0e3450; }
        .btn-copy.copied { background-color: #28a745; color: white; border-color: #28a745; width: auto; padding: 0 10px; font-size: 0.9rem; font-weight: bold; }
    </style>
    """

    cards_html = ""
    for i, oferta in enumerate(ofertas_filtradas):
        super_name = oferta.get('supermercado', 'Super')
        link_oferta = oferta.get('link', '#')
        bg_badge = "#d32f2f" if "Coto" in super_name else "#2e7d32" if "Jumbo" in super_name else "#1565c0" if "Carrefour" in super_name else "#ef6c00"
        
        cats_visuales = [c for c in oferta.get('categoria', []) if "Bancarias" not in c][:2]
        cats_html = "".join([f'<span class="tag">{c}</span>' for c in cats_visuales])
        
        texto_copiar = f"Mira esta oferta: {link_oferta}".replace("'", "")
        btn_id = f"btn-copy-{i}"

        cards_html += f"""
        <div class="oferta-card">
            <div class="card-header"><span class="super-badge" style="background-color: {bg_badge};">{super_name}</span><span class="date-text">{oferta.get('fecha', '')}</span></div>
            <div class="img-container"><img src="{oferta.get('imagen', '')}" alt="Oferta" onerror="this.style.display='none'"></div>
            <div class="card-title">{oferta.get('titulo', 'Oferta')}</div>
            <div class="tags">{cats_html}</div>
            <div class="btn-row">
                <a href="{link_oferta}" target="_blank" class="btn-ver">Ver Oferta 🛒</a>
                <button id="{btn_id}" class="btn-copy" onclick="copiarLink('{texto_copiar}', '{btn_id}')" title="Copiar Link">🔗</button>
            </div>
        </div>
        """

    components.html(f"""<html><head>{css_styles}</head><body><div class="grid-container">{cards_html}</div><script>function copiarLink(t,i){{navigator.clipboard.writeText(t);let b=document.getElementById(i);b.innerHTML="¡Copiado!";b.classList.add("copied");setTimeout(()=>{{b.innerHTML="🔗";b.classList.remove("copied")}},2000)}}</script></body></html>""", height=altura_dinamica, scrolling=True)

# --- 7. FOOTER Y SCRIPT ---
st.markdown("<br><br><hr>", unsafe_allow_html=True)
with st.expander("⚖️ Aviso Legal", expanded=False):
    st.markdown("<div style='color:#ddd;font-size:0.9rem;'>DataChango es un agregador de ofertas...</div>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; color: #888; font-size: 0.8rem; margin-top: 15px;'>© 2025 DataChango</div>", unsafe_allow_html=True)
components.html("<script>function abrirEnPC(){try{if(window.parent.innerWidth>768){var d=window.parent.document.querySelector('div[data-testid=\"stExpander\"] details');if(d&&!d.hasAttribute('open'))d.setAttribute('open','')}}catch(e){}}abrirEnPC();setTimeout(abrirEnPC,500);</script>", height=0, width=0)