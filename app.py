import streamlit as st
import json
import os
import unicodedata
import streamlit.components.v1 as components
import math
import base64


# --- OCULTAR LA BARRA DE STREAMLIT ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="DataChango 🛒",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 1. GESTIÓN DE ESTADO (SESSION STATE) ---
# Inicializamos el estado para saber qué categoría está "encendida"
if 'categoria_activa' not in st.session_state:
    st.session_state.categoria_activa = None

if 'filtro_ver_todo' not in st.session_state: st.session_state.filtro_ver_todo = True
if 'filtros_hipers' not in st.session_state: 
    hipers_init = ["Carrefour", "Jumbo", "Coto", "MasOnline"]
    st.session_state.filtros_hipers = {k: False for k in hipers_init}

# --- 2. UTILIDADES ---
def normalizar_texto(texto):
    if not isinstance(texto, str): return ""
    texto = texto.lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

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
                    for d in datos: d["origen_filtro"] = nombre
                    todas_ofertas.extend(datos)
                    conteo_ofertas[nombre] = len(datos)
            except: pass
            
    return todas_ofertas, conteo_ofertas

def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- 3. ESTILOS GLOBALES (CSS) ---
st.markdown("""
    <style>
        .stApp { background-color: #0e3450; }
        
        /* Textos Generales */
        h1, h2, h3, h4, h5, h6, p, div, label, span { color: #ffffff !important; }
        
        /* Checkboxes */
        .stCheckbox label { color: #ffffff !important; font-size: 1rem; font-weight: 500; }
        
        /* Alineación Centrada de Checkboxes (Escritorio y Móvil) */
        div[data-testid="stVerticalBlock"] > div > div[data-testid="stCheckbox"] { 
            display: flex; 
            justify-content: center; 
        }
        
        /* REGLA RESPONSIVE PARA MÓVILES */
        @media (max-width: 768px) {
            /* Centrar columnas en móvil */
            div[data-testid="column"] {
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
            }
            /* Asegurar que los botones de categoría ocupen ancho completo pero centrados */
            .stButton { width: 100%; display: flex; justify-content: center; }
        }

        hr { border-color: #cfa539; opacity: 0.5; }
        
        /* Botones Streamlit (Estilo Normal) */
        div[data-testid="stButton"] button[kind="secondary"] {
            background-color: transparent; 
            color: #ffffff;
            border: 1px solid #cfa539; 
            border-radius: 20px; 
            transition: all 0.3s; 
            width: 100%; 
        }
        div[data-testid="stButton"] button[kind="secondary"]:hover {
            background-color: #c7501e; 
            border-color: #c7501e; 
            color: white; 
            transform: scale(1.05);
        }

        /* Botones Streamlit (Estilo ACTIVO/PRIMARY) */
        div[data-testid="stButton"] button[kind="primary"] {
            background-color: #c7501e !important; 
            color: white !important;
            border: 1px solid #c7501e !important; 
            border-radius: 20px; 
            width: 100%;
            box-shadow: 0 0 10px rgba(199, 80, 30, 0.6);
        }

        /* Títulos */
        .filter-title {
            text-align: center; font-size: 1.5rem !important; font-weight: 600;
            margin-bottom: 20px; margin-top: 10px; color: #cfa539 !important; 
            text-transform: uppercase; letter-spacing: 1.5px;
        }
        
        /* Disclaimer */
        .streamlit-expanderHeader {
            background-color: #0b2a40; border: 1px solid #cfa539; border-radius: 8px;
            color: #cfa539 !important; font-weight: bold;
        }
        .streamlit-expanderContent {
            background-color: #0b2a40; border: 1px solid #cfa539; border-top: none;
            border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; color: #ccc !important;
        }

        /* Enlace contacto */
        .contact-link-text {
            color: white !important; text-decoration: underline; cursor: pointer;
        }
        .contact-link-text:hover { color: #cfa539 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. CABECERA ---
logo_file = "logo.jpg" 

if os.path.exists(logo_file):
    img_b64 = get_img_as_base64(logo_file)
    logo_html = f"""<div style="display: flex; flex-direction: column; justify-content: center; align-items: center; padding-top: 10px;"><img src="data:image/jpeg;base64,{img_b64}" style="width: 250px; height: auto; border-radius: 20px; object-fit: contain; box-shadow: 0 4px 15px rgba(0,0,0,0.3); display: block;"><h4 style='text-align: center; color: #cfa539 !important; font-weight: 300; letter-spacing: 2px; text-transform: uppercase; margin-top: 20px; font-size: 1.1rem; line-height: 1.6;'>Recopilo las principales ofertas de los Hipermercados <span style="font-weight: bold; color: white;">AR</span><br><span style="font-size: 0.95rem; text-transform: none; color: #e0e0e0; letter-spacing: 0.5px;">DataChango hace las búsquedas de ofertas por vos ahorrandote tiempo y dinero!</span></h4></div>"""
    st.markdown(logo_html, unsafe_allow_html=True)
else:
    st.warning(f"⚠️ Falta el archivo '{logo_file}' en la carpeta.")

st.markdown("<hr style='margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

# --- 5. LOGICA DE DATOS Y FILTROS ---
ofertas_raw, conteos = cargar_datos()

hipers = ["Carrefour", "Jumbo", "Coto", "MasOnline"]
emojis = {"Carrefour": "🛒", "Jumbo": "🛒", "Coto": "🛒", "MasOnline": "🛒"}

def on_change_ver_todo():
    if st.session_state.filtro_ver_todo:
        for k in hipers: st.session_state.filtros_hipers[k] = False

def on_change_hiper(nombre):
    if st.session_state.filtros_hipers[nombre]: 
        st.session_state.filtro_ver_todo = False
    if not any(st.session_state.filtros_hipers.get(h, False) for h in hipers): 
        st.session_state.filtro_ver_todo = True

# --- CONTACTO ---
contact_html = """
<div style="text-align: center; margin-bottom: 25px; font-weight: bold; color: white; font-size: 1rem;">
    Ideas, sugerencias, comentarios? 
    <a href="mailto:datachangoweb@gmail.com" class="contact-link-text">Hablemos</a> 
    <svg style="width: 20px; height: 20px; fill: white; vertical-align: middle; margin-left: 5px;" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2ZM20 16H6L4 18V4H20V16Z"/>
    </svg>
</div>
"""
st.markdown(contact_html, unsafe_allow_html=True)

st.markdown('<p class="filter-title"> Filtros por Supermercado</p>', unsafe_allow_html=True)

# Checkboxes de Supermercados
c_todo, c_h1, c_h2, c_h3, c_h4 = st.columns(5)
with c_todo:
    st.checkbox("✅ Ver Todo", key='filtro_ver_todo', on_change=on_change_ver_todo)

columnas_hipers = [c_h1, c_h2, c_h3, c_h4]
for i, h in enumerate(hipers):
    with columnas_hipers[i]:
        label = f"{emojis[h]} {h} ({conteos[h]})"
        st.checkbox(label, key=f"chk_{h}", value=st.session_state.filtros_hipers[h], on_change=on_change_hiper, args=(h,))
        # Actualizamos el estado interno desde el key del checkbox
        st.session_state.filtros_hipers[h] = st.session_state[f"chk_{h}"]

if st.session_state.filtro_ver_todo:
    hipers_activos = hipers
else:
    hipers_activos = [h for h in hipers if st.session_state.filtros_hipers[h]]

st.markdown("<br>", unsafe_allow_html=True)

# --- BOTONES DE CATEGORÍA (TOGGLE) ---
st.markdown('<p class="filter-title">⚡ Filtrar por Rubro</p>', unsafe_allow_html=True)

# Definimos las categorías y sus claves
categorias = [
    ("🥩 Carnes", "carne"),
    ("🍷 Bebidas", "bebida"),
    ("🍝 Almacén", "almacen"),
    ("🧹 Limpieza", "limpieza"),
    ("📺 Electro", "electro"),
    ("🧸 Juguetes", "juguete")
]

cols_cat = st.columns(6)

# Función para manejar el clic en categoría (Toggle)
def toggle_categoria(cat_key):
    if st.session_state.categoria_activa == cat_key:
        st.session_state.categoria_activa = None # Apagar si ya estaba activa
    else:
        st.session_state.categoria_activa = cat_key # Encender nueva

for i, (label, key) in enumerate(categorias):
    # Determinamos el tipo de botón (primary = encendido, secondary = apagado)
    btn_type = "primary" if st.session_state.categoria_activa == key else "secondary"
    
    # Creamos el botón ocupando el ancho del contenedor
    if cols_cat[i].button(label, key=f"btn_{key}", type=btn_type, use_container_width=True):
        toggle_categoria(key)
        st.rerun()

# Definimos el término de búsqueda según el estado
filtro_cat = st.session_state.categoria_activa

# --- BÚSQUEDA Y FILTRADO ---
termino_busqueda = filtro_cat if filtro_cat else "" 
query_clean = normalizar_texto(termino_busqueda)

sinonimos = {
    "carne": ["carniceria", "asado", "bondiola", "pollo", "cerdo", "bife", "hamburguesa", "milanesa", "nalga", "vacío", "chorizo", "picada", "peceto", "colita", "ternera"],
    "bebida": ["vino", "cerveza", "gaseosa", "agua", "fernet", "coca", "pepsi", "sprite", "alcohol", "aperitivo"],
    "almacen": ["fideos", "arroz", "aceite", "yerba", "galletitas", "cafe"],
    "limpieza": ["jabon", "detergente", "lavandina", "papel", "rollo", "cif", "ala", "ariel", "suavizante"],
    "electro": ["tv", "smart", "celular", "aire", "heladera", "notebook", "tecnologia", "lavarropas", "tablet", "playstation", "consola"],
    "juguete": ["jugueteria", "juego", "muñeca", "lego", "niño", "infantil", "regalo", "pileta"]
}
palabras_clave = [query_clean]
if query_clean in sinonimos: palabras_clave.extend(sinonimos[query_clean])
palabras_clave = list(set(p for p in palabras_clave if p)) 

ofertas_filtradas = []
for oferta in ofertas_raw:
    if oferta.get("origen_filtro") not in hipers_activos: continue 
    if not termino_busqueda:
        ofertas_filtradas.append(oferta)
    else:
        titulo_norm = normalizar_texto(oferta.get("titulo", ""))
        desc_norm = normalizar_texto(oferta.get("descripcion", ""))
        cats_norm = " ".join([normalizar_texto(c) for c in oferta.get("categoria", [])])
        texto_total = f"{titulo_norm} {desc_norm} {cats_norm}"
        if any(palabra in texto_total for palabra in palabras_clave): ofertas_filtradas.append(oferta)

# --- 6. GRID HTML ---
if not ofertas_filtradas:
    st.warning(f"🤷‍♂️ No encontré ofertas. Prueba 'Ver Todo'.")
else:
    nombres_mostrar = "Todos los Supermercados" if st.session_state.filtro_ver_todo else ", ".join(hipers_activos)
    
    stats_html = f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <div style="color: #ccc; font-size: 1rem; margin-bottom: 5px;">
            Mostrando <span style="color: white; font-weight: bold;">{len(ofertas_filtradas)}</span> ofertas de: {nombres_mostrar}
        </div>
        <div style="color: #aaa; font-size: 0.9rem;">
            ¿Te sirvió DataChango? 
            <a href="https://cafecito.app/datachango" target="_blank" style="color: #ffffff; text-decoration: underline; font-weight: bold; margin-left: 4px;">
                Invitame un Cafecito ☕
            </a>
        </div>
    </div>
    """
    st.markdown(stats_html, unsafe_allow_html=True)
    
    cant_ofertas = len(ofertas_filtradas)
    filas = math.ceil(cant_ofertas / 3) 
    
    # Ajuste de altura dinámica (Considerando móviles 1 columna vs desktop 3 columnas)
    # Scrolling=True en components.html soluciona el corte, pero damos una altura base generosa
    altura_dinamica = (filas * 400) + 100 

    css_styles = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
        body { margin: 0; padding: 10px; font-family: 'Roboto', sans-serif; background-color: transparent; }
        
        /* Grid responsive: se adapta automáticamente al ancho */
        .grid-container { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
            gap: 20px; 
            padding-bottom: 20px;
        }
        
        .oferta-card {
            background-color: #16425b; border-radius: 12px; padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3); border: 1px solid #cfa539; 
            display: flex; flex-direction: column; justify-content: space-between;
            transition: transform 0.2s, box-shadow 0.2s; height: 380px;
        }
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
        bg_badge = "#555"
        if "Coto" in super_name: bg_badge = "#d32f2f"
        elif "Jumbo" in super_name: bg_badge = "#2e7d32"
        elif "Carrefour" in super_name: bg_badge = "#1565c0"
        elif "MasOnline" in super_name: bg_badge = "#ef6c00"

        cats_html = "".join([f'<span class="tag">{c}</span>' for c in oferta.get('categoria', [])[:2]])
        texto_copiar = f"👵 Mira esta oferta en DataChango: {link_oferta}".replace("'", "")
        btn_id = f"btn-copy-{i}"

        card = f"""
        <div class="oferta-card">
            <div class="card-header">
                <span class="super-badge" style="background-color: {bg_badge};">{super_name}</span>
                <span class="date-text">{oferta.get('fecha', '')}</span>
            </div>
            <div class="img-container">
                <img src="{oferta.get('imagen', '')}" alt="Oferta" onerror="this.style.display='none'">
            </div>
            <div class="card-title">{oferta.get('titulo', 'Oferta')}</div>
            <div class="tags">{cats_html}</div>
            <div class="btn-row">
                <a href="{link_oferta}" target="_blank" class="btn-ver">Ver Oferta 🛒</a>
                <button id="{btn_id}" class="btn-copy" onclick="copiarLink('{texto_copiar}', '{btn_id}')" title="Copiar Link">🔗</button>
            </div>
        </div>
        """
        cards_html += card

    js_script = """
    <script>
        function copiarLink(texto, btnId) {
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(texto);
            } else {
                let textArea = document.createElement("textarea");
                textArea.value = texto;
                textArea.style.position = "fixed";
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try { document.execCommand('copy'); } catch (e) {}
                document.body.removeChild(textArea);
            }
            let btn = document.getElementById(btnId);
            let originalContent = btn.innerHTML;
            btn.classList.add("copied");
            btn.innerHTML = "¡Copiado!";
            setTimeout(() => {
                btn.classList.remove("copied");
                btn.innerHTML = originalContent;
            }, 2000);
        }
    </script>
    """

    full_html = f"""
    <html><head>{css_styles}</head><body>
        <div class="grid-container">{cards_html}</div>
        {js_script}
    </body></html>
    """
    
    # IMPORTANTE: scrolling=True habilita el scroll interno si la altura calculada falla en móviles
    components.html(full_html, height=altura_dinamica, scrolling=True)

# --- 7. FOOTER ---
st.markdown("<br><br>", unsafe_allow_html=True) 
st.markdown("---")

with st.expander("⚖️ Aviso Legal y Exención de Responsabilidad (Leer más)", expanded=False):
    st.markdown("""
<div style='color: #ddd; font-size: 0.9rem; line-height: 1.6;'>
    <p style="margin-bottom: 10px;"><strong style="color: #cfa539;">AVISO LEGAL IMPORTANTE SOBRE PRECIOS Y OFERTAS</strong></p>
    <p><strong style="color: #fff;">1. Carácter de la Información:</strong> "DataChango" funciona exclusivamente como un agregador y facilitador de información. No somos un supermercado ni vendemos productos. Todas las imágenes, marcas, descripciones y precios que se muestran pertenecen a sus respectivos dueños (Carrefour, Coto, Jumbo, MasOnline, etc.).</p>
    <p><strong style="color: #fff;">2. Precios Referenciales:</strong> Los precios y ofertas mostrados son capturados automáticamente y pueden diferir del precio real en góndola o en la web oficial del supermercado al momento de la compra debido a actualizaciones de último momento o errores de lectura. <strong>El precio válido siempre será el que figure en la página oficial del supermercado o en su línea de cajas.</strong></p>
    <p><strong style="color: #fff;">3. Deslinde de Responsabilidad:</strong> "DataChango" no garantiza la exactitud, integridad o actualidad de los datos. No nos hacemos responsables por diferencias de precios, falta de stock, errores en las promociones bancarias o cualquier perjuicio derivado del uso de esta información. Siempre verifique la oferta en la fuente original antes de comprar.</p>
    <p><strong style="color: #fff;">4. Propiedad Intelectual:</strong> Todos los logotipos y nombres comerciales de los supermercados son propiedad exclusiva de sus titulares y se utilizan aquí únicamente con fines informativos y de referencia para el usuario (Uso Justo / Fair Use).</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""<div style='text-align: center; color: #888; font-size: 0.8rem; margin-top: 15px; margin-bottom: 20px;'>© 2025 DataChango - Comparador Inteligente - Hecho con 🧉 en Argentina</div>""", unsafe_allow_html=True)