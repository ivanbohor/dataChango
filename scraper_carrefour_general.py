import json
import time
import requests
import easyocr
import re
import os
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURACIÓN ---
NOMBRE_SUPER = "Carrefour"
URL_SUPER = "https://www.carrefour.com.ar"
ARCHIVO_SALIDA = "ofertas_carrefour.json"

print(f">>> 🛒 Iniciando Scraper {NOMBRE_SUPER} (V30: Base Estable + Inyección Mascota)...")

if os.path.exists(ARCHIVO_SALIDA): os.remove(ARCHIVO_SALIDA)

reader = easyocr.Reader(['es'], gpu=False) 

# --- 1. BASE DE CONOCIMIENTO ---
DB_CONOCIMIENTO = {
    # MASCOTAS (PRIORIDAD ALTA)
    "23614": ("Mascotas", "🐶 Mascotas"), # ID del cluster que pasaste
    "mascota": ("Mascotas", "🐶 Mascotas"),
    "perro": ("Alimento Perro", "🐶 Mascotas"),
    "gato": ("Alimento Gato", "🐶 Mascotas"),
    "dog ui": ("Alimento Perro", "🐶 Mascotas"),
    "gati": ("Alimento Gato", "🐶 Mascotas"),

    # CARNES
    "bondiola": ("Bondiola", "🥩 Carnicería"),
    "cerdo": ("Carne de Cerdo", "🥩 Carnicería"),
    "solomillo": ("Solomillo", "🥩 Carnicería"),
    "carre": ("Carré de Cerdo", "🥩 Carnicería"),
    "pechito": ("Pechito de Cerdo", "🥩 Carnicería"),
    "matambre": ("Matambre", "🥩 Carnicería"),
    "carne": ("Carne Vacuna", "🥩 Carnicería"),
    "asado": ("Asado", "🥩 Carnicería"),
    "vacio": ("Vacío", "🥩 Carnicería"),
    "pollo": ("Pollo", "🥩 Carnicería"),
    "milanesa": ("Milanesas", "🥩 Carnicería"),
    "hamburguesa": ("Hamburguesas", "🥩 Carnicería"),
    "bife": ("Bifes", "🥩 Carnicería"),
    "nalga": ("Corte Nalga", "🥩 Carnicería"),
    "picada": ("Carne Picada", "🥩 Carnicería"),
    
    # ALMACÉN & BEBIDAS
    "pan dulce": ("Pan Dulce", "🍝 Almacén"),
    "budin": ("Budines", "🍝 Almacén"),
    "turron": ("Turrones", "🍝 Almacén"),
    "confitura": ("Mesa Dulce", "🍝 Almacén"),
    "aceite": ("Aceite", "🍝 Almacén"),
    "vino": ("Vinos", "🍷 Bebidas"),
    "espumante": ("Espumantes", "🍷 Bebidas"),
    "champagne": ("Champagne", "🍷 Bebidas"),
    "cerveza": ("Cervezas", "🍷 Bebidas"),
    "fernet": ("Fernet", "🍷 Bebidas"),
    "gaseosa": ("Gaseosas", "🍷 Bebidas"),

    # RESTO
    "juguete": ("Juguetería", "🧸 Juguetería"),
    "playstation": ("PlayStation 5", "📺 Electro"),
    "tv": ("Smart TV", "📺 Electro"),
    "heladera": ("Heladeras", "📺 Electro"),
    "aire": ("Aires Acondicionados", "📺 Electro"),
    "leche": ("Leche", "🥛 Lácteos"),
    "pampers": ("Pañales Pampers", "💊 Farmacia"),
    "huggies": ("Pañales Huggies", "💊 Farmacia"),
}

# --- 2. FILTRO DE VALIDEZ ---
def es_oferta_valida(texto, link=""):
    t = texto.lower()
    l = link.lower()

    # REGLA DE ORO: Si el link es de mascotas, ES VÁLIDA (Bypass OCR)
    if "mascotas" in l or "23614" in l:
        return True

    # Filtros normales
    if "precio oferta" in t or "hasta el" in t: return True
    
    # Palabras clave en texto
    keywords_producto = [k for k in DB_CONOCIMIENTO.keys() if not k.isdigit()]
    if any(p in t for p in keywords_producto): return True

    if any(x in t for x in ["horarios", "sucursales", "copyright", "posible info"]): return False
    
    senales = ["%", "off", "2x1", "3x2", "4x2", "2da", "cuotas", "ahorro", "descuento", "precio", "$", "oferta", "llevando", "hasta", "80%"]
    return any(s in t for s in senales)

# --- 3. CATEGORÍA ---
def detectar_categoria(texto_completo, link=""):
    t_limpio = texto_completo.lower().replace("carrefour", "").replace("mi carrefour", "")
    l_limpio = link.lower()
    etiquetas = []
    
    # 1. DETECCIÓN BANCARIA (Prioridad Alta)
    # Si detectamos esto, abortamos búsqueda de comida para evitar falsos positivos
    keywords_banco = ["banco", "tarjeta", "naranja", "naranjax", "modo", "reintegro", "tope", "ahorro", "financiacion"]
    if any(k in t_limpio for k in keywords_banco):
        return ["💳 Bancarias"]

    # 2. Prioridad: LINK (Mascotas por ID 23614)
    if "23614" in l_limpio or "mascota" in l_limpio:
        if "🐶 Mascotas" not in etiquetas: etiquetas.append("🐶 Mascotas")

    # 3. Búsqueda Texto (Productos)
    for k, v in DB_CONOCIMIENTO.items():
        if k in t_limpio:
            if v[1] not in etiquetas: etiquetas.append(v[1])
            
    if not etiquetas:
        if "electro" in t_limpio or "tv" in t_limpio or "tecnologia" in t_limpio: etiquetas.append("📺 Electro")
        elif "bebe" in t_limpio or "pañal" in t_limpio: etiquetas.append("💊 Farmacia")
        elif "limpieza" in t_limpio: etiquetas.append("🧹 Limpieza")
        elif "mercado" in t_limpio or "almacen" in t_limpio: etiquetas.append("🍝 Almacén")
        else: etiquetas.append("⚡ Varios")
        
    return etiquetas

# --- 4. EXTRAER LINK ---
def obtener_link(elemento_img, driver):
    try:
        # Método JS robusto para encontrar el <a> padre
        link = driver.execute_script("""
            let el = arguments[0];
            let parent = el.closest('a');
            return parent ? parent.href : null;
        """, elemento_img)
        if link: return urljoin(URL_SUPER, link)
    except: pass
    return URL_SUPER

# --- 5. LIMPIEZA ---
# --- 5. LIMPIEZA INTELIGENTE (SANITIZACIÓN) ---
def limpiar_texto_ocr(texto_sucio, link=""):
    if not texto_sucio: texto_sucio = ""
    # Limpieza básica
    t = texto_sucio.replace("\n", " ").strip()
    t = re.sub(r'(\d+)([a-zA-Z])', r'\1 \2', t) 
    t_lower = t.lower()
    l = link.lower()
    
    # --- A. DETECCIÓN DE BANCOS/TARJETAS (Cortocircuito) ---
    # Si es una promo bancaria, no intentamos inventar un título de producto
    keywords_banco = ["banco", "tarjeta", "naranja", "naranjax", "modo", "reintegro", "tope"]
    if any(kb in t_lower for kb in keywords_banco) and not "leche" in t_lower: 
        # Nota: El "not leche" es por si acaso hay una promo de "Leche con Banco", 
        # pero generalmente las promos bancarias son genéricas.
        # Mejoramos el título extrayendo el nombre del banco si es posible
        banco = "Promoción Bancaria"
        if "naranja" in t_lower: banco = "Promo NaranjaX"
        elif "carrefour" in t_lower and "tarjeta" in t_lower: banco = "Promo Tarjeta Carrefour"
        elif "modo" in t_lower: banco = "Promo MODO"
        return banco

    prefijo = "Oferta"

    # --- B. DETECCIÓN DE CUOTAS (CON SANITIZACIÓN) ---
    match_cuotas = re.search(r'(\d+)\s*(?:CUO|CTA|PAGOS)', t, re.IGNORECASE)
    if match_cuotas:
        raw_num = match_cuotas.group(1)
        num_int = int(raw_num)
        if num_int <= 24:
            prefijo = f"{num_int} Cuotas S/Int"
        else:
            if raw_num.startswith("12"): prefijo = "12 Cuotas S/Int"
            elif raw_num.startswith("18"): prefijo = "18 Cuotas S/Int"
            elif raw_num.startswith("6"): prefijo = "6 Cuotas S/Int"
            elif raw_num.startswith("3"): prefijo = "3 Cuotas S/Int"
            else: prefijo = "Financiación Disponible"

    # --- C. DETECCIÓN DE PORCENTAJE ---
    elif "%" in t or "off" in t_lower:
        match_pct = re.search(r'(\d+)\s*%', t)
        if match_pct:
            pct_val = int(match_pct.group(1))
            if 5 <= pct_val <= 95:
                if any(x in t_lower for x in ["2do", "2da", "segunda"]):
                    prefijo = f"2do al {pct_val}%"
                else:
                    prefijo = f"{pct_val}% Off"
            else: prefijo = "Descuento Especial"

    elif re.search(r'\b(\d+)[xX](\d+)\b', t):
        match_nxn = re.search(r'\b(\d+)[xX](\d+)\b', t)
        prefijo = f"{match_nxn.group(1)}x{match_nxn.group(2)}"

    elif "$" in t: prefijo = "Precio Especial"
    
    # --- D. LOGICA DE RESCATE MASCOTAS ---
    if ("23614" in l or "mascota" in l) and prefijo == "Oferta":
        return "Oferta en Mascotas (Ver Imagen)"

    # --- E. DETECCIÓN DE PRODUCTO (CON WORD BOUNDARIES \b) ---
    prods = []
    # Eliminamos palabras comunes que ensucian
    t_limpio = t_lower.replace("carrefour", "").replace("mi carrefour", "").replace("oferta", "")
    
    for k, v in DB_CONOCIMIENTO.items():
        if k.isdigit(): continue 
        # USO DE REGEX \b: Solo matchea si es una palabra completa
        # Evita que "seleccione" active "leche" o "carniceria" active "carne" incorrectamente
        if re.search(r'\b' + re.escape(k) + r'\b', t_limpio):
            prods.append(v[0])
    
    if prods:
        prod_str = ", ".join(list(set(prods))[:2])
        return f"{prefijo} en {prod_str}"
    
    return f"{prefijo} en Varios"

def procesar_oferta(elemento_img, src, titulos_procesados, ofertas_encontradas, driver, forzar_validez=False):
    try:
        link_real = obtener_link(elemento_img, driver)
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        try: resp = requests.get(src, headers=headers, timeout=5)
        except: return
        if resp.status_code != 200: return

        res_ocr = reader.readtext(resp.content, detail=0, paragraph=True)
        texto_raw = " ".join(res_ocr)
        texto_lower = texto_raw.lower()

        # VALIDACIÓN: Si forzamos (porque vino del slider de mascotas) pasa directo
        es_valida = es_oferta_valida(texto_lower, link_real)
        if not es_valida and not forzar_validez:
            return
        
        cats = detectar_categoria(texto_lower, link_real)
        titulo_final = limpiar_texto_ocr(texto_raw, link_real)

        if titulo_final not in titulos_procesados:
            oferta = {
                "supermercado": NOMBRE_SUPER,
                "titulo": titulo_final,
                "descripcion": texto_raw if texto_raw else "Ver imagen",
                "categoria": cats,
                "link": link_real,
                "imagen": src,
                "fecha": time.strftime("%Y-%m-%d")
            }
            ofertas_encontradas.append(oferta)
            titulos_procesados.add(titulo_final)
            print(f"      🛒 [{cats[0]}] {titulo_final}")

    except Exception: pass

# --- SCRAPER PRINCIPAL ---
def obtener_ofertas_carrefour():
    opts = Options()
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=opts)
    ofertas_encontradas = []
    titulos_procesados = set() 
    src_procesados = set()

    try:
        driver.get(URL_SUPER)
        print(f"   🌐 Entrando a {NOMBRE_SUPER}...")
        time.sleep(5)

        # FASE 0: INYECCIÓN QUIRÚRGICA (Banner Mascotas)
        # Buscamos la clase específica que pasaste en el HTML
        print("   💉 Ejecutando extracción quirúrgica (Sliders)...")
        sliders_especificos = driver.find_elements(By.CSS_SELECTOR, "div[class*='vtex-slider-layout-0-x-slide'] a img")
        
        for img in sliders_especificos:
            try:
                src = img.get_attribute("src")
                if src and src not in src_procesados:
                    # Chequeo si es el de mascotas por link (antes de procesar) o lo mando a procesar forzado
                    src_procesados.add(src)
                    procesar_oferta(img, src, titulos_procesados, ofertas_encontradas, driver, forzar_validez=True)
            except: continue

        # FASE 1: SMART SCROLL (EL CLÁSICO QUE FUNCIONABA BIEN)
        print("   📜 Smart Scroll (Recuperando volumen de ofertas)...")
        altura_total = driver.execute_script("return document.body.scrollHeight")
        paso_scroll = 500
        
        for y in range(0, altura_total, paso_scroll):
            driver.execute_script(f"window.scrollTo(0, {y});")
            time.sleep(1.5)
            
            # Buscamos TODAS las imágenes visibles
            imagenes = driver.find_elements(By.TAG_NAME, "img")
            
            for img in imagenes:
                try:
                    src = img.get_attribute("src")
                    if not src or src in src_procesados: continue
                    
                    # Filtro geométrico (El que funcionaba antes)
                    w = driver.execute_script("return arguments[0].naturalWidth;", img) or 0
                    h = driver.execute_script("return arguments[0].naturalHeight;", img) or 0
                    
                    if w > 300 and h > 100:
                        src_procesados.add(src)
                        procesar_oferta(img, src, titulos_procesados, ofertas_encontradas, driver, forzar_validez=False)
                except: continue

    except Exception as e: print(f"❌ Error: {e}")
    finally: 
        driver.quit()
        # Guardado final
        with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
            json.dump(ofertas_encontradas, f, ensure_ascii=False, indent=4)
    
    return ofertas_encontradas

if __name__ == "__main__":
    datos = obtener_ofertas_carrefour()
    print(f"\n💾 Guardado Final Carrefour: {len(datos)} ofertas.")