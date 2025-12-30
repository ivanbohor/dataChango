import json
import time
import requests
import easyocr
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# --- CONFIGURACIÓN ---
NOMBRE_SUPER = "MasOnline"
URL_SUPER = "https://www.masonline.com.ar"
ARCHIVO_SALIDA = "ofertas_masonline.json"

print(f">>> 🌈 Iniciando Scraper {NOMBRE_SUPER} (V16.3: Fix Bazar Específico)...")

if os.path.exists(ARCHIVO_SALIDA): os.remove(ARCHIVO_SALIDA)

reader = easyocr.Reader(['es'], gpu=False) 

# --- 1. BASE DE CONOCIMIENTO (V16 + Bazar) ---
DB_CONOCIMIENTO = {
    "bazar": ("Bazar", "🏠 Hogar"), # <--- Único agregado
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
    "peceto": ("Peceto", "🥩 Carnicería"),
    "colita": ("Colita de Cuadril", "🥩 Carnicería"),
    "cuadril": ("Cuadril", "🥩 Carnicería"),
    "vino": ("Vinos", "🍷 Bebidas"),
    "espumante": ("Espumantes", "🍷 Bebidas"),
    "champagne": ("Champagne", "🍷 Bebidas"),
    "sidra": ("Sidras", "🍷 Bebidas"),
    "anana fizz": ("Sidras", "🍷 Bebidas"),
    "cerveza": ("Cervezas", "🍷 Bebidas"),
    "fernet": ("Fernet", "🍷 Bebidas"),
    "aperitivo": ("Aperitivos", "🍷 Bebidas"),
    "gaseosa": ("Gaseosas", "🍷 Bebidas"),
    "electro": ("Electro", "📺 Electro"),
    "aire": ("Aires Acondicionados", "📺 Electro"),
    "tv": ("Smart TV", "📺 Electro"),
    "televisor": ("Smart TV", "📺 Electro"),
    "celular": ("Celulares", "📺 Electro"),
    "smartphone": ("Celulares", "📺 Electro"),
    "heladera": ("Heladeras", "📺 Electro"),
    "lavarropas": ("Lavarropas", "📺 Electro"),
    "notebook": ("Notebooks", "📺 Electro"),
    "tecnologia": ("Tecnología", "📺 Electro"),
    "leche": ("Leche", "🥛 Lácteos"),
    "yogur": ("Yogures", "🥛 Lácteos"),
    "queso": ("Quesos", "🥛 Lácteos"),
    "manteca": ("Manteca", "🥛 Lácteos"),
    "pan dulce": ("Pan Dulce", "🍝 Almacén"),
    "budin": ("Budines", "🍝 Almacén"),
    "turron": ("Turrones", "🍝 Almacén"),
    "almacen": ("Almacén", "🍝 Almacén"),
    "aceite": ("Aceite", "🍝 Almacén"),
    "fideo": ("Pastas", "🍝 Almacén"),
    "juguete": ("Juguetería", "🧸 Juguetería"),
    "pileta": ("Piletas", "🧸 Juguetería"),
    "limpieza": ("Limpieza", "🧹 Limpieza"),
    "jabon": ("Jabón", "🧹 Limpieza"),
    "farmacia": ("Farmacia", "💊 Farmacia"),
    "perfumeria": ("Perfumería", "💊 Farmacia"),
    "bebe": ("Mundo Bebé", "💊 Farmacia"),
    "pañal": ("Pañales", "💊 Farmacia"),
}

# --- 2. FILTRO DE VALIDEZ ---
def es_oferta_valida(texto):
    t = texto.lower()
    keywords_producto = list(DB_CONOCIMIENTO.keys())
    if any(p in t for p in keywords_producto): return True
    if any(x in t for x in ["horarios", "sucursales", "copyright", "posible info", "ver más"]): return False
    # Agregamos "bazar"
    senales = ["%", "off", "2x1", "3x2", "4x2", "2da", "cuotas", "ahorro", "descuento", "precio", "$", "oferta", "llevando", "hasta", "80%", "bazar"]
    return any(s in t for s in senales)

# --- 3. CATEGORÍA ---
def detectar_categoria(texto_completo):
    t_limpio = texto_completo.lower().replace("masonline", "").replace("chango", "")
    etiquetas = []
    
    for k, v in DB_CONOCIMIENTO.items():
        if len(k) < 5:
            if re.search(r'\b' + re.escape(k) + r'\b', t_limpio):
                if v[1] not in etiquetas: etiquetas.append(v[1])
        else:
            if k in t_limpio:
                if v[1] not in etiquetas: etiquetas.append(v[1])

    if "banco" in t_limpio or "tarjeta" in t_limpio or "modo" in t_limpio: 
        etiquetas.append("💳 Bancarias")
            
    if not etiquetas:
        if "electro" in t_limpio or "tv" in t_limpio or "tecnologia" in t_limpio: etiquetas.append("📺 Electro")
        elif "bebe" in t_limpio or "pañal" in t_limpio: etiquetas.append("💊 Farmacia")
        elif "limpieza" in t_limpio: etiquetas.append("🧹 Limpieza")
        elif "mercado" in t_limpio or "almacen" in t_limpio: etiquetas.append("🍝 Almacén")
        elif "bazar" in t_limpio: etiquetas.append("🏠 Hogar")
        else: etiquetas.append("⚡ Varios")
    
    if len(etiquetas) > 1 and "💳 Bancarias" in etiquetas:
        etiquetas.remove("💳 Bancarias")
        
    return etiquetas

# --- 4. EXTRAER LINK ---
def obtener_link_especifico(elemento_img):
    try:
        padre = elemento_img.find_element(By.XPATH, "./ancestor::a")
        link = padre.get_attribute("href")
        if link and "http" in link: return link
    except: pass
    return URL_SUPER

# --- 5. LIMPIEZA ---
def limpiar_texto_ocr(texto_sucio, texto_alt=""):
    t = (texto_sucio + " " + texto_alt).replace("\n", " ").strip()
    t = t.replace("18CUOTAS", "18 Cuotas").replace("12CUOTAS", "12 Cuotas")
    
    prefijo = "Oferta"
    match_pct = re.search(r'(\d+)%', t)
    match_nxn = re.search(r'(\d+[xX]\d+)', t)
    match_cuotas = re.search(r'(\d+)\s*(CUO|CTA)', t, re.IGNORECASE)
    
    if match_nxn: prefijo = match_nxn.group(1).lower()
    elif match_cuotas: prefijo = f"{match_cuotas.group(1)} Cuotas S/Int"
    elif match_pct:
        if "2do" in t.lower() or "segunda" in t.lower() or "2da" in t.lower(): prefijo = f"2do al {match_pct.group(1)}%"
        else: prefijo = f"{match_pct.group(1)}% Off"
    elif "$" in t:
        prefijo = "Precio Especial"
    
    if "sidra" in t.lower() and "2x1" in t.lower(): prefijo = "2x1"
    if "tv" in t.lower() and "40" in t.lower(): prefijo = "Hasta 40% Off"

    prods = []
    t_limpio = t.lower().replace("masonline", "") 
    for k, v in DB_CONOCIMIENTO.items():
        if len(k) < 5:
            if re.search(r'\b' + re.escape(k) + r'\b', t_limpio): prods.append(v[0])
        else:
            if k in t_limpio: prods.append(v[0])
    
    if prods:
        prod_str = ", ".join(list(set(prods))[:2])
        return f"{prefijo} en {prod_str}"
    
    if "en:" in t.lower():
        try:
            raw = t.lower().split("en:")[1].strip()
            return f"{prefijo} en {raw.split()[0].title()}..."
        except: pass

    return f"{prefijo} en Varios"

def procesar_oferta(elemento_img, src, texto_alt, titulos_procesados, ofertas_encontradas):
    try:
        # --- FIX URL RELATIVA ---
        # Solo corregimos si empieza con /api/, que es el caso de Bazar y productos reales.
        # Esto evita capturar loaders tipo /assets/img/loader.svg
        if src.startswith("/"):
            src = URL_SUPER + src
        # ------------------------

        link_real = obtener_link_especifico(elemento_img)
        headers = {'User-Agent': 'Mozilla/5.0'}
        try: resp = requests.get(src, headers=headers, timeout=5)
        except: return
        if resp.status_code != 200: return

        res_ocr = reader.readtext(resp.content, detail=0, paragraph=True)
        texto_ocr = " ".join(res_ocr)
        texto_analisis = f"{texto_ocr} {texto_alt}".strip()

        if not es_oferta_valida(texto_analisis): return
        cats = detectar_categoria(texto_analisis)
        
        es_logistica = any(k in texto_analisis.lower() for k in ["entrega", "envio", "financiacion", "pedila", "online", "app"])
        tiene_producto = any(k in texto_analisis.lower() for k in DB_CONOCIMIENTO.keys())
        
        if es_logistica and not tiene_producto: return
        if len(cats) == 1 and cats[0] == "💳 Bancarias": return
            
        titulo_final = limpiar_texto_ocr(texto_ocr, texto_alt)

        if titulo_final not in titulos_procesados:
            oferta = {
                "supermercado": NOMBRE_SUPER,
                "titulo": titulo_final,
                "descripcion": texto_ocr + " " + texto_alt,
                "categoria": cats,
                "link": link_real,
                "imagen": src,
                "fecha": time.strftime("%Y-%m-%d")
            }
            ofertas_encontradas.append(oferta)
            titulos_procesados.add(titulo_final)
            print(f"      🌈 [{cats[0]}] {titulo_final}")

    except Exception: pass

# --- 6. SCRAPER PRINCIPAL ---
def obtener_ofertas_masonline():
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

        print("   🎡 Escaneando Carrusel Principal...")
        for i in range(12): 
            imgs = driver.find_elements(By.CSS_SELECTOR, "img[class*='main-banner-slider']")
            nuevos = 0
            for img in imgs:
                try:
                    src = img.get_attribute("src")
                    if src and src not in src_procesados:
                        src_procesados.add(src)
                        nuevos += 1
                        procesar_oferta(img, src, "", titulos_procesados, ofertas_encontradas)
                except: continue
            try:
                flechas = driver.find_elements(By.CSS_SELECTOR, "button[class*='sliderRightArrow']")
                if flechas:
                    driver.execute_script("arguments[0].click();", flechas[0])
                    time.sleep(1.5)
                else:
                    if i > 5: break 
            except: break

        print("   📜 Barrido Profundo (Buscando Sidras y Tech)...")
        altura_total = driver.execute_script("return document.body.scrollHeight")
        paso_scroll = 500
        
        for y in range(0, altura_total, paso_scroll):
            driver.execute_script(f"window.scrollTo(0, {y});")
            time.sleep(1) 
            
            imagenes_visibles = driver.find_elements(By.TAG_NAME, "img")
            
            for img in imagenes_visibles:
                try:
                    w = int(img.get_attribute("width") or img.size['width'] or 0)
                    h = int(img.get_attribute("height") or img.size['height'] or 0)
                    
                    if w > 180 and h > 100:
                        src = img.get_attribute("src")
                        texto_alt = (img.get_attribute("alt") or "") + " " + (img.get_attribute("title") or "")
                        
                        # --- MODIFICACIÓN: FILTRO LÁSER ---
                        # Solo aceptamos HTTP normal O rutas relativas que sean claramente de API de productos
                        # Esto evita que se llenen los procesados con "/assets/loading.gif"
                        es_http = src and "http" in src
                        es_api = src and src.startswith("/api/") 
                        
                        if es_http or es_api:
                            if src not in src_procesados:
                                if "icon" in src or "logo" in src: continue
                                src_procesados.add(src)
                                procesar_oferta(img, src, texto_alt, titulos_procesados, ofertas_encontradas)
                        # ----------------------------------
                except: continue

    except Exception as e: print(f"❌ Error: {e}")
    finally: driver.quit()
    return ofertas_encontradas

if __name__ == "__main__":
    datos = obtener_ofertas_masonline()
    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
    print(f"\n💾 Guardado MasOnline: {len(datos)} ofertas.")