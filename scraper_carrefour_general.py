import json
import time
import requests
import easyocr
import re
import os
import unicodedata

# --- IMPORTS DE SELENIUM ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURACIÓN ---
NOMBRE_SUPER = "Carrefour"
URL_SUPER = "https://www.carrefour.com.ar"
ARCHIVO_SALIDA = "ofertas_carrefour.json"

# Filtro general para el resto de la página
MIN_ANCHO_BANNER = 150 

print(f">>> 🇫🇷 Iniciando Scraper {NOMBRE_SUPER} (V49: Slider Sniper)...")

if os.path.exists(ARCHIVO_SALIDA): os.remove(ARCHIVO_SALIDA)

reader = easyocr.Reader(['es'], gpu=False) 

# --- 1. DICCIONARIO MAESTRO (CON PLURALES Y LÁCTEOS) ---
DB_MAESTRA = {
    # 🧀 LÁCTEOS Y FRESCOS
    "lacteo": ("Lácteos", "🧀 Lácteos y Frescos"),
    "lacteos": ("Lácteos", "🧀 Lácteos y Frescos"),
    "leche": ("Leche", "🧀 Lácteos y Frescos"),
    "leches": ("Leche", "🧀 Lácteos y Frescos"), 
    "yogur": ("Yogur", "🧀 Lácteos y Frescos"),
    "yogures": ("Yogur", "🧀 Lácteos y Frescos"), 
    "queso": ("Quesos", "🧀 Lácteos y Frescos"),
    "quesos": ("Quesos", "🧀 Lácteos y Frescos"),
    "manteca": ("Manteca", "🧀 Lácteos y Frescos"),
    "crema": ("Crema", "🧀 Lácteos y Frescos"),

    # 🍷 BEBIDAS
    "vino": ("Vinos", "🍷 Bebidas"),
    "vinos": ("Vinos", "🍷 Bebidas"), 
    "vlnos": ("Vinos", "🍷 Bebidas"),
    "bodega": ("Vinos", "🍷 Bebidas"),
    "bodegas": ("Vinos", "🍷 Bebidas"),
    "cerveza": ("Cervezas", "🍷 Bebidas"),
    "cervezas": ("Cervezas", "🍷 Bebidas"),
    "gaseosa": ("Gaseosas", "🍷 Bebidas"),
    "bebida": ("Bebidas", "🍷 Bebidas"),
    "bebidas": ("Bebidas", "🍷 Bebidas"),
    
    # 🥩 CARNICERÍA
    "carne": ("Carne Vacuna", "🥩 Carnicería"),
    "asado": ("Asado", "🥩 Carnicería"),
    "pollo": ("Pollo", "🥩 Carnicería"),
    "pollos": ("Pollo", "🥩 Carnicería"),
    "cerdo": ("Cerdo", "🥩 Carnicería"),

    # 🍝 ALMACÉN
    "fideo": ("Fideos", "🍝 Almacén"),
    "fideos": ("Fideos", "🍝 Almacén"),
    "arroz": ("Arroz", "🍝 Almacén"),
    "galletita": ("Galletitas", "🍝 Almacén"),
    "galletitas": ("Galletitas", "🍝 Almacén"),
    "aceite": ("Aceite", "🍝 Almacén"),
    "cafe": ("Café", "🍝 Almacén"),
    "yerba": ("Yerba", "🍝 Almacén"),
    "atun": ("Atún", "🍝 Almacén"),
    "mayonesa": ("Mayonesa", "🍝 Almacén"),
    "desayuno": ("Desayuno", "🍝 Almacén"),
    "almacen": ("Almacén", "🍝 Almacén"),
    
    # 🧴 PERFUMERÍA
    "jabon": ("Jabón", "🧹 Limpieza"),
    "huggies": ("Pañales", "🧴 Perfumería y Bebé"),
    "pampers": ("Pañales", "🧴 Perfumería y Bebé"),
    "shampoo": ("Shampoo", "🧴 Perfumería y Bebé"),

    # 📺 ELECTRO
    "tv": ("Smart TV", "📺 Electro y Tecno"),
    "smart": ("Smart TV", "📺 Electro y Tecno"),
    "aire": ("Aires Acondicionados", "📺 Electro y Tecno"),
    "celular": ("Celulares", "📺 Electro y Tecno"),
    "heladera": ("Heladeras", "📺 Electro y Tecno"),
    "lavarropas": ("Lavarropas", "📺 Electro y Tecno"),
    "notebook": ("Notebooks", "📺 Electro y Tecno"),
}

# --- FUNCIONES DE LIMPIEZA ---
def normalizar_texto(texto):
    if not texto: return ""
    t = texto.lower()
    return ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')

def sanitizar_texto_exclusiones(texto):
    if not texto: return ""
    t_norm = normalizar_texto(texto)
    palabras_corte = ["excluye", "no incluye", "legales", "bases y cond", "consultar en", "no acumulable", "ver legal", "valido en", "stock", "disponible"]
    indice_corte = len(t_norm)
    for palabra in palabras_corte:
        idx = t_norm.find(palabra)
        if idx != -1 and idx < indice_corte:
            indice_corte = idx
    return texto[:indice_corte]

# --- LÓGICA DE CATEGORIZACIÓN ---
def detectar_categorias_inteligente(texto_sanitizado, es_cluster=False):
    t_limpio = normalizar_texto(texto_sanitizado.replace("carrefour", ""))
    etiquetas = []
    
    # 1. Busqueda estricta en diccionario
    for keyword, (producto, categoria_final) in DB_MAESTRA.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', t_limpio):
            if categoria_final not in etiquetas:
                etiquetas.append(categoria_final)
    
    if any(k in t_limpio for k in ["banco", "tarjeta", "modo"]): etiquetas.append("💳 Bancarias")

    # 2. Inferencias
    if not etiquetas:
        if re.search(r'\b(12|18|24)\s*(cuotas|pagos)', t_limpio):
            etiquetas.append("📺 Electro y Tecno")
        elif "tecno" in t_limpio: etiquetas.append("📺 Electro y Tecno")
        elif "limpie" in t_limpio: etiquetas.append("🧹 Limpieza")

    cats_prod = [c for c in etiquetas if c != "💳 Bancarias"]
    if cats_prod: return list(set(cats_prod))
    
    if es_cluster: return ["🍝 Almacén"]
    return ["🍝 Almacén"] 

# --- VALIDACIÓN ---
def es_oferta_valida(texto_sanitizado, href_real):
    t_norm = normalizar_texto(texto_sanitizado)
    href_lower = (href_real or "").lower()

    if "productclusterids" in href_lower or "collection" in href_lower: return True
    if any(x in t_norm for x in ["horarios", "sucursales", "copyright", "seguinos", "whatsapp", "app"]): return False

    senales = ["%", "off", "2x1", "3x2", "4x2", "2da", "cuotas", "ahorro", "descuento", "precio", "$", "oferta", "llevando"]
    tiene_senal = any(s in t_norm for s in senales)

    es_producto = href_lower.endswith("/p") or "/p?" in href_lower
    if es_producto: return True if tiene_senal else False
    
    super_vips = ["vino", "bodega", "tv", "aire", "celular", "leche", "carne", "asado", "pollo", "atun"]
    if any(v in t_norm for v in super_vips): return True
    
    if tiene_senal: return True
    return False

def limpiar_texto_ocr(texto_sanitizado, texto_alt, categorias_detectadas, href_real):
    t = (texto_sanitizado + " " + texto_alt).replace("\n", " ").strip()
    t_clean = t.replace("12CUOTAS", "12 Cuotas").replace("18CUOTAS", "18 Cuotas")
    t_norm = normalizar_texto(t_clean)
    
    prefijo = "Oferta"
    match_cuotas = re.search(r'\b(3|6|9|12|18|24)\s*(?:CUO|CTA|PAGOS)', t_clean, re.IGNORECASE)
    match_pct = re.search(r'(\d+)%', t_clean)
    match_nxn = re.search(r'(\d+\s*[xX]\s*\d+)', t_clean) 
    
    if match_nxn: prefijo = match_nxn.group(1).lower().replace(" ", "")
    elif match_cuotas: prefijo = f"{match_cuotas.group(1)} Cuotas S/Int"
    elif match_pct: 
        if "2do" in t_norm: prefijo = f"2do al {match_pct.group(1)}%"
        else: prefijo = f"{match_pct.group(1)}% Off"
    
    prods = []
    for k, v in DB_MAESTRA.items():
        if re.search(r'\b' + re.escape(k) + r'\b', t_norm):
            if v[0] != "Promoción Bancaria": prods.append(v[0])
            
    if prods:
        prod = list(set(prods))[0]
        if len(set(prods)) > 2: return f"{prefijo} en Varios Productos"
        return f"{prefijo} en {prod}"
    
    if categorias_detectadas:
        cat = categorias_detectadas[0].replace("🧸 ", "").replace("📺 ", "").replace("🏠 ", "").replace("🥩 ", "").replace("💳 ", "").replace("🔥 ", "").strip()
        if "Electro" in cat: cat = "Electro"
        return f"{prefijo} en Seleccionados ({cat})"

    return f"{prefijo} en Supermercado"

def procesar_oferta(src, href_real, texto_alt, titulos_procesados, ofertas_encontradas):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        try: resp = requests.get(src, headers=headers, timeout=5)
        except: return
        if resp.status_code != 200: return

        res_ocr = reader.readtext(resp.content, detail=0, paragraph=True)
        texto_ocr = " ".join(res_ocr)
        texto_limpio = sanitizar_texto_exclusiones(f"{texto_ocr} {texto_alt}")
        
        es_cluster = "productclusterids" in (href_real or "").lower() or "collection" in (href_real or "").lower()

        if es_oferta_valida(texto_limpio, href_real):
            cats = detectar_categorias_inteligente(texto_limpio, es_cluster)
            titulo_final = limpiar_texto_ocr(texto_limpio, "", cats, href_real)

            if titulo_final not in titulos_procesados:
                print(f"      👀 RAW: {texto_limpio[:40]}... -> CAT: {cats}")
                oferta = {
                    "supermercado": NOMBRE_SUPER,
                    "titulo": titulo_final,
                    "descripcion": texto_ocr if texto_ocr else "Oferta Detectada",
                    "categoria": cats,
                    "link": href_real,
                    "imagen": src,
                    "fecha": time.strftime("%Y-%m-%d")
                }
                ofertas_encontradas.append(oferta)
                titulos_procesados.add(titulo_final)
                print(f"      ✅ GUARDADO: {cats} {titulo_final}")
    except Exception as e: pass

# --- NAVEGACIÓN ---

def intentar_cerrar_popups(driver):
    print("   🛡️ Neutralizando pop-ups...")
    try: webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    except: pass
    try:
        wait = WebDriverWait(driver, 5)
        xpath_busqueda = "//button[contains(., 'Aceptar') or contains(., 'Cerrar') or contains(., 'Entendido') or contains(@class, 'close') or contains(@class, 'vtex-modal')]"
        boton = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_busqueda)))
        boton.click()
    except: pass

def scroll_progresivo(driver):
    print("   📜 Scroll Progresivo...")
    altura = driver.execute_script("return document.body.scrollHeight")
    for i in range(0, altura, 500):
        driver.execute_script(f"window.scrollTo(0, {i});")
        time.sleep(0.2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

def extraccion_masiva_js(driver, titulos_procesados, ofertas_encontradas):
    print(f"   ☢️ Extracción JS (V49: SLIDER SNIPER ACTIVO)...")
    
    script_js = f"""
    var minSize = {MIN_ANCHO_BANNER}; 
    var items = [];
    
    // 1. ESTRATEGIA SNIPER: Buscar Específicamente el Slider de VTEX (Tu HTML)
    // Buscamos imagenes que tengan la clase 'vtex-slider-layout...'
    var sliderImages = document.querySelectorAll('img[class*="vtex-slider-layout"]');
    sliderImages.forEach(img => {{
        var src = img.src || img.dataset.src;
        
        // NO USAMOS FILTRO DE TAMAÑO ESTRICTO AQUÍ
        // Porque los sliders a veces reportan width=0 hasta que se ven.
        // Solo verificamos que tenga src válido.
        if (src && src.length > 20) {{
             var parent = img.closest('a');
             console.log("Slider Image found: " + src);
             items.push({{src: src, href: parent ? parent.href : ""}});
        }}
    }});

    // 2. ESTRATEGIA GENERAL (Para el resto de la página)
    var anchors = document.querySelectorAll('a img');
    anchors.forEach(img => {{
        // Evitamos duplicar lo que ya agarró el sniper
        if (!img.className.includes('vtex-slider-layout')) {{
            var src = img.src || img.dataset.src;
            var esGrande = (img.naturalWidth > minSize) || (img.width > minSize);
            if (src && src.length > 20 && src.includes('carrefourar') && esGrande) {{
                items.push({{src: src, href: img.closest('a') ? img.closest('a').href : ""}});
            }}
        }}
    }});

    // 3. BACKGROUNDS CSS
    document.querySelectorAll('a div').forEach(div => {{
        var bg = window.getComputedStyle(div).backgroundImage;
        var esGrande = div.offsetWidth > minSize;
        if (bg && bg.includes('url') && bg.includes('carrefourar') && esGrande) {{
             var srcBg = bg.replace('url("', '').replace('")', '').replace('url(', '').replace(')', '').replace(/"/g, "");
             items.push({{src: srcBg, href: div.closest('a') ? div.closest('a').href : ""}});
        }}
    }});

    return items;
    """
    
    try:
        items_crudos = driver.execute_script(script_js)
        items_unicos = {i['src']: i for i in items_crudos}.values()
        print(f"      -> {len(items_unicos)} Banners (incluyendo Sliders ocultos).")
        for item in items_unicos:
            if item['src'] not in [o['imagen'] for o in ofertas_encontradas]:
                procesar_oferta(item['src'], item['href'], "JS-Massive", titulos_procesados, ofertas_encontradas)
    except Exception as e: print(f"Error JS: {e}")

def obtener_ofertas_carrefour():
    opts = Options()
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=opts)
    ofertas = []
    titulos = set()

    try:
        driver.get(URL_SUPER)
        intentar_cerrar_popups(driver)
        # Hacemos scroll para forzar la carga de imagenes lazy del slider
        scroll_progresivo(driver)
        extraccion_masiva_js(driver, titulos, ofertas)

    except Exception as e: print(f"❌ Error: {e}")
    finally: driver.quit()
    
    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
        json.dump(ofertas, f, ensure_ascii=False, indent=4)
    return ofertas

if __name__ == "__main__":
    datos = obtener_ofertas_carrefour()
    print(f"\n💾 Guardado Carrefour: {len(datos)} ofertas.")