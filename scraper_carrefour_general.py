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

print(f">>> 🇫🇷 Iniciando Scraper {NOMBRE_SUPER} (V57: Precision Filter)...")

if os.path.exists(ARCHIVO_SALIDA): os.remove(ARCHIVO_SALIDA)

reader = easyocr.Reader(['es'], gpu=False) 

# --- 1. DICCIONARIO MAESTRO (EXPANDIDO PARA ELECTRO) ---
DB_MAESTRA = {
    # 🧀 LÁCTEOS Y FRESCOS
    "lacteo": ("Lácteos", "🧀 Lácteos y Frescos"),
    "lacteos": ("Lácteos", "🧀 Lácteos y Frescos"),
    "leche": ("Leche", "🧀 Lácteos y Frescos"),
    "leches": ("Leche", "🧀 Lácteos y Frescos"), 
    "yogur": ("Yogur", "🧀 Lácteos y Frescos"),
    "queso": ("Quesos", "🧀 Lácteos y Frescos"),
    "manteca": ("Manteca", "🧀 Lácteos y Frescos"),
    "crema": ("Crema", "🧀 Lácteos y Frescos"),

    # 🍷 BEBIDAS
    "vino": ("Vinos", "🍷 Bebidas"),
    "bodega": ("Vinos", "🍷 Bebidas"),
    "cerveza": ("Cervezas", "🍷 Bebidas"),
    "gaseosa": ("Gaseosas", "🍷 Bebidas"),
    "bebida": ("Bebidas", "🍷 Bebidas"),
    
    # 🥩 CARNICERÍA
    "carne": ("Carne Vacuna", "🥩 Carnicería"),
    "asado": ("Asado", "🥩 Carnicería"),
    "pollo": ("Pollo", "🥩 Carnicería"),
    "suprema": ("Pollo", "🥩 Carnicería"), 
    "cerdo": ("Cerdo", "🥩 Carnicería"),

    # 🍝 ALMACÉN
    "fideo": ("Fideos", "🍝 Almacén"),
    "arroz": ("Arroz", "🍝 Almacén"),
    "galletita": ("Galletitas", "🍝 Almacén"),
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

    # 📺 ELECTRO (EXPANDIDO)
    "tv": ("Smart TV", "📺 Electro y Tecno"),
    "smart": ("Smart TV", "📺 Electro y Tecno"),
    "aire": ("Aires Acondicionados", "📺 Electro y Tecno"),
    "celular": ("Celulares", "📺 Electro y Tecno"),
    "heladera": ("Heladeras", "📺 Electro y Tecno"),
    "lavarropas": ("Lavarropas", "📺 Electro y Tecno"),
    "notebook": ("Notebooks", "📺 Electro y Tecno"),
    "electro": ("Electrodomésticos", "📺 Electro y Tecno"), # NUEVO
    "pequeno": ("Electrodomésticos", "📺 Electro y Tecno"), # NUEVO
    "cocina": ("Electrodomésticos", "📺 Electro y Tecno"), # NUEVO
    "batidora": ("Electrodomésticos", "📺 Electro y Tecno"), # NUEVO
    "pava": ("Electrodomésticos", "📺 Electro y Tecno"), # NUEVO
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
def detectar_categorias_inteligente(texto_sanitizado, href_real=""):
    t_limpio = normalizar_texto(texto_sanitizado.replace("carrefour", "") + " " + href_real)
    etiquetas = []
    
    for keyword, (producto, categoria_final) in DB_MAESTRA.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', t_limpio):
            if categoria_final not in etiquetas:
                etiquetas.append(categoria_final)
    
    if any(k in t_limpio for k in ["banco", "tarjeta", "modo", "galicia", "santander"]): 
        etiquetas.append("💳 Bancarias")

    if not etiquetas:
        if re.search(r'\b(12|18|24)\s*(cuotas|pagos)', t_limpio):
            etiquetas.append("📺 Electro y Tecno")
        elif "tecno" in t_limpio: etiquetas.append("📺 Electro y Tecno")
        elif "limpie" in t_limpio: etiquetas.append("🧹 Limpieza")

    cats_prod = [c for c in etiquetas if c != "💳 Bancarias"]
    if cats_prod: return list(set(cats_prod))
    
    # Si no detectó nada pero es un cluster, miramos keywords genéricas
    if "productclusterids" in href_real.lower(): 
        if "electro" in t_limpio: return ["📺 Electro y Tecno"]
        return ["🍝 Almacén"] # Default
    return ["🍝 Almacén"] 

# --- VALIDACIÓN ---
def es_oferta_valida(texto_sanitizado, href_real):
    t_norm = normalizar_texto(texto_sanitizado)
    href_lower = (href_real or "").lower()

    if "productclusterids" in href_lower or "collection" in href_lower: return True
    if any(x in t_norm for x in ["horarios", "sucursales", "copyright", "seguinos", "whatsapp", "app"]): return False

    senales = ["%", "off", "2x1", "3x2", "4x2", "2da", "cuotas", "ahorro", "descuento", "precio", "$", "oferta", "llevando", "cupo"]
    tiene_senal = any(s in t_norm for s in senales)

    es_producto = href_lower.endswith("/p") or "/p?" in href_lower
    
    if es_producto:
        # Lista VIP expandida
        super_vips = ["vino", "bodega", "tv", "aire", "celular", "leche", "carne", "asado", "pollo", "suprema", "atun", "milanesa", "jamon", "queso", "electro", "pequeno"]
        if any(v in href_lower for v in super_vips): return True
        if any(v in t_norm for v in super_vips): return True
        return True if tiene_senal else False
    
    if tiene_senal: return True
    return False

# --- LIMPIEZA Y TITULADO ---
def limpiar_texto_ocr(texto_sanitizado, texto_alt, categorias_detectadas, href_real):
    t = (texto_sanitizado + " " + texto_alt).replace("\n", " ").strip()
    t_clean = t.replace("12CUOTAS", "12 Cuotas").replace("18CUOTAS", "18 Cuotas")
    t_norm = normalizar_texto(t_clean)
    
    prefijo = "Oferta"
    
    match_cuotas = re.search(r'\b(3|6|9|12|18|24)\s*(?:CUO|CTA|PAGOS)', t_clean, re.IGNORECASE)
    match_pct = re.search(r'(\d+)\s*%', t_clean)
    match_nxn = re.search(r'(\d+\s*[xX]\s*\d+)', t_clean) 
    match_precio = re.search(r'\$\s?(\d{1,3}(?:[.,\s]\d{3})*)', t_clean)

    if "cupo" in t_norm: 
        if match_precio:
             val = match_precio.group(1).replace(".", "").replace(" ", "").replace(",", "")
             if val.isdigit() and int(val) > 100: prefijo = f"Cupón de ${val}"
             else: prefijo = "Cupón de Descuento"
        else: prefijo = "Cupón de Descuento"

    elif match_nxn: 
        prefijo = match_nxn.group(1).lower().replace(" ", "")
    
    elif match_cuotas: 
        prefijo = f"{match_cuotas.group(1)} Cuotas S/Int"
    
    elif match_pct: 
        if "2do" in t_norm: prefijo = f"2do al {match_pct.group(1)}%"
        else: prefijo = f"{match_pct.group(1)}% Off"
    
    elif match_precio:
        val = match_precio.group(1).replace(".", "").replace(" ", "").replace(",", "")
        if val.isdigit() and int(val) > 100: prefijo = f"A solo ${val}"
        else: prefijo = "Oferta"
    
    prods = []
    texto_busqueda = t_norm + " " + normalizar_texto(href_real)
    
    for k, v in DB_MAESTRA.items():
        if re.search(r'\b' + re.escape(k) + r'\b', texto_busqueda):
            if v[0] != "Promoción Bancaria": prods.append(v[0])
            
    if prods:
        prod = list(set(prods))[0]
        if len(set(prods)) > 2: return f"{prefijo} en Varios Productos"
        return f"{prefijo} en {prod}"
    
    if categorias_detectadas:
        cat = categorias_detectadas[0].replace("🧸 ", "").replace("📺 ", "").replace("🏠 ", "").replace("🥩 ", "").replace("💳 ", "").replace("🔥 ", "").strip()
        if "Electro" in cat: cat = "Electro"
        return f"{prefijo} en Seleccionados ({cat})"

    return f"{prefijo} en Varios Productos"

def procesar_oferta(src, href_real, texto_alt, titulos_procesados, ofertas_encontradas):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', 'Referer': 'https://www.carrefour.com.ar/'}
        try: resp = requests.get(src, headers=headers, timeout=5)
        except: return
        if resp.status_code != 200: return

        res_ocr = reader.readtext(resp.content, detail=0, paragraph=True)
        texto_ocr = " ".join(res_ocr)
        texto_limpio = sanitizar_texto_exclusiones(f"{texto_ocr} {texto_alt}")
        
        if es_oferta_valida(texto_limpio, href_real):
            cats = detectar_categorias_inteligente(texto_limpio, href_real)
            titulo_final = limpiar_texto_ocr(texto_limpio, "", cats, href_real)

            # --- FILTRO ANTI-RUIDO FINANCIERO (V57) ---
            # Si NO encontramos descuento explícito (empezamos con "Oferta en...")
            # Y detectamos palabras de logística o banca
            # Y la categoría es genérica (Almacén/Lácteos)... ELIMINAMOS.
            if titulo_final.startswith("Oferta en"):
                texto_low = texto_limpio.lower()
                es_ruido = any(x in texto_low for x in ["galicia", "santander", "banco", "tarjeta", "entrega", "envio", "inmediata", "retiro"])
                
                # Lista de categorías donde suelen aparecer estos banners basura
                cats_genericas = ["🧀 Lácteos y Frescos", "🍝 Almacén", "🧹 Limpieza", "Varios Productos"]
                es_cat_generica = any(c in cats for c in cats_genericas) or not cats

                if es_ruido and es_cat_generica:
                    return # DESCARTAR BANNER DE ENVIO/BANCO SIN DESCUENTO
            # ----------------------------------------

            if titulo_final not in titulos_procesados:
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
                print(f"      ✅ GUARDADO: {titulo_final}")
    except Exception as e: pass

# --- NAVEGACIÓN Y EXTRACCIÓN ---

def intentar_cerrar_popups(driver):
    print("   🛡️ Neutralizando pop-ups...")
    try: webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    except: pass
    try: driver.find_element(By.TAG_NAME, "body").click()
    except: pass

def ejecutar_script_extraccion(driver):
    script_js = """
    var items = [];
    function esBannerValido(src) {
        if (!src) return false;
        var s = src.toLowerCase();
        if (s.includes('logo') || s.includes('icon') || s.includes('facebook') || s.includes('instagram')) return false;
        if (s.length < 15) return false;
        return true;
    }
    var bannersVtex = document.querySelectorAll('.vtex-store-components-3-x-imageElement');
    bannersVtex.forEach(img => {
        var src = img.currentSrc || img.src || img.dataset.src;
        var parentLink = img.closest('a');
        var href = parentLink ? parentLink.href : '';
        if (esBannerValido(src)) items.push({src: src, href: href});
    });
    var anchors = document.querySelectorAll('a');
    anchors.forEach(a => {
        var img = a.querySelector('img');
        if (img) {
            var src = img.currentSrc || img.src || img.dataset.src;
            if (src && src.includes(' ')) src = src.split(' ')[0];
            if (esBannerValido(src)) {
                var width = img.naturalWidth || img.width || 0;
                if (width > 150) items.push({src: src, href: a.href});
            }
        }
    });
    return items;
    """
    return driver.execute_script(script_js)

def barrido_iterativo(driver, titulos_procesados, ofertas_encontradas):
    print(f"   ☢️ Iniciando Barrido Iterativo (Scroll + Scan)...")
    urls_procesadas_temp = set()
    altura_total = driver.execute_script("return document.body.scrollHeight")
    posicion_actual = 0
    paso_scroll = 600 
    
    while posicion_actual < altura_total:
        items_crudos = ejecutar_script_extraccion(driver)
        nuevos_items = 0
        for item in items_crudos:
            if item['src'] not in urls_procesadas_temp:
                urls_procesadas_temp.add(item['src'])
                procesar_oferta(item['src'], item['href'], "JS-Vtex", titulos_procesados, ofertas_encontradas)
                nuevos_items += 1
        
        if nuevos_items > 0: print(f"      -> Encontrados {nuevos_items} nuevos elementos.")
        posicion_actual += paso_scroll
        driver.execute_script(f"window.scrollTo(0, {posicion_actual});")
        time.sleep(2) 
        altura_total = driver.execute_script("return document.body.scrollHeight")

def obtener_ofertas_carrefour():
    opts = Options()
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=opts)
    ofertas = []
    titulos = set()
    try:
        driver.get(URL_SUPER)
        print("   ⏳ Esperando carga inicial...")
        time.sleep(5) 
        intentar_cerrar_popups(driver)
        barrido_iterativo(driver, titulos, ofertas)
    except Exception as e: print(f"❌ Error: {e}")
    finally: driver.quit()
    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f: json.dump(ofertas, f, ensure_ascii=False, indent=4)
    return ofertas

if __name__ == "__main__":
    datos = obtener_ofertas_carrefour()
    print(f"\n💾 Guardado Carrefour: {len(datos)} ofertas.")