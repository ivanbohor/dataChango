import json
import time
import requests
import easyocr
import re
import os
import urllib.parse
import unicodedata
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# --- CONFIGURACIÓN ---
NOMBRE_SUPER = "MasOnline"
URL_SUPER = "https://www.masonline.com.ar"
ARCHIVO_SALIDA = "ofertas_masonline.json"

print(f">>> 🌈 Iniciando Scraper {NOMBRE_SUPER} (V25: Detección Técnica de Aires)...")

if os.path.exists(ARCHIVO_SALIDA): os.remove(ARCHIVO_SALIDA)

reader = easyocr.Reader(['es'], gpu=False) 

# --- 1. DICCIONARIO MAESTRO (VERSION V51 - PALABRAS TÉCNICAS) ---
DB_MAESTRA = {
    # 🥩 CARNICERÍA
    "carne": ("Carne Vacuna", "🥩 Carnicería"),
    "asado": ("Asado", "🥩 Carnicería"),
    "bife": ("Bifes", "🥩 Carnicería"),
    "pollo": ("Pollo", "🥩 Carnicería"),
    "cerdo": ("Cerdo", "🥩 Carnicería"),
    "bondiola": ("Bondiola", "🥩 Carnicería"),
    "matambre": ("Matambre", "🥩 Carnicería"),
    "peceto": ("Peceto", "🥩 Carnicería"),
    "nalga": ("Corte Nalga", "🥩 Carnicería"),
    "hamburguesa": ("Hamburguesas", "🥩 Carnicería"),
    "hamburguesas": ("Hamburguesas", "🥩 Carnicería"),
    "milanesa": ("Milanesas", "🥩 Carnicería"),
    "milanesas": ("Milanesas", "🥩 Carnicería"),
    "salchicha": ("Salchichas", "🥩 Carnicería"),
    "salchichas": ("Salchichas", "🥩 Carnicería"),
    "pescado": ("Pescadería", "🥩 Carnicería"),
    "pescaderia": ("Pescadería", "🥩 Carnicería"),
    "pechito": ("Pechito de Cerdo", "🥩 Carnicería"),
    "solomillo": ("Solomillo", "🥩 Carnicería"),
    "cuadril": ("Cuadril", "🥩 Carnicería"),
    "colita": ("Colita de Cuadril", "🥩 Carnicería"),

    # 🧀 LÁCTEOS Y FRESCOS
    "leche": ("Leche", "🧀 Lácteos y Frescos"),
    "yogur": ("Yogur", "🧀 Lácteos y Frescos"),
    "yogures": ("Yogur", "🧀 Lácteos y Frescos"),
    "queso": ("Quesos", "🧀 Lácteos y Frescos"),
    "quesos": ("Quesos", "🧀 Lácteos y Frescos"),
    "manteca": ("Manteca", "🧀 Lácteos y Frescos"),
    "crema": ("Crema", "🧀 Lácteos y Frescos"),
    "dulce de leche": ("Dulce de Leche", "🧀 Lácteos y Frescos"),
    "postre": ("Postres Lácteos", "🧀 Lácteos y Frescos"),
    "postres": ("Postres Lácteos", "🧀 Lácteos y Frescos"),
    "fiambre": ("Fiambres", "🧀 Lácteos y Frescos"),
    "fiambres": ("Fiambres", "🧀 Lácteos y Frescos"),
    "jamon": ("Jamón", "🧀 Lácteos y Frescos"),
    "salam": ("Salame", "🧀 Lácteos y Frescos"),
    "pasta": ("Pastas Frescas", "🧀 Lácteos y Frescos"),
    "pastas": ("Pastas Frescas", "🧀 Lácteos y Frescos"),
    "tapas": ("Tapas", "🧀 Lácteos y Frescos"),
    "fruta": ("Frutas", "🧀 Lácteos y Frescos"),
    "frutas": ("Frutas", "🧀 Lácteos y Frescos"),
    "verdura": ("Verduras", "🧀 Lácteos y Frescos"),
    "verduras": ("Verduras", "🧀 Lácteos y Frescos"),

    # 🍷 BEBIDAS
    "bebida": ("Bebidas", "🍷 Bebidas"),
    "bebidas": ("Bebidas", "🍷 Bebidas"),
    "gaseosa": ("Gaseosas", "🍷 Bebidas"),
    "gaseosas": ("Gaseosas", "🍷 Bebidas"),
    "cola": ("Gaseosa Cola", "🍷 Bebidas"),
    "agua": ("Aguas", "🍷 Bebidas"),
    "aguas": ("Aguas", "🍷 Bebidas"),
    "jugo": ("Jugos", "🍷 Bebidas"),
    "jugos": ("Jugos", "🍷 Bebidas"),
    "cerveza": ("Cervezas", "🍷 Bebidas"),
    "cervezas": ("Cervezas", "🍷 Bebidas"),
    "vino": ("Vinos", "🍷 Bebidas"),
    "vinos": ("Vinos", "🍷 Bebidas"),
    "champagne": ("Champagne", "🍷 Bebidas"),
    "espumante": ("Espumantes", "🍷 Bebidas"),
    "espumantes": ("Espumantes", "🍷 Bebidas"),
    "sidra": ("Sidras", "🍷 Bebidas"),
    "sidras": ("Sidras", "🍷 Bebidas"),
    "fernet": ("Fernet", "🍷 Bebidas"),
    "aperitivo": ("Aperitivos", "🍷 Bebidas"),
    "aperitivos": ("Aperitivos", "🍷 Bebidas"),
    "gin": ("Gin", "🍷 Bebidas"),
    "vodka": ("Vodka", "🍷 Bebidas"),
    "whisky": ("Whisky", "🍷 Bebidas"),
    "anana fizz": ("Sidras", "🍷 Bebidas"),

    # 🍝 ALMACÉN
    "almacen": ("Almacén", "🍝 Almacén"),
    "aceite": ("Aceite", "🍝 Almacén"),
    "aceites": ("Aceite", "🍝 Almacén"),
    "arroz": ("Arroz", "🍝 Almacén"),
    "fideo": ("Fideos Secos", "🍝 Almacén"),
    "fideos": ("Fideos Secos", "🍝 Almacén"),
    "harina": ("Harina", "🍝 Almacén"),
    "yerba": ("Yerba", "🍝 Almacén"),
    "cafe": ("Café", "🍝 Almacén"),
    "mate cocido": ("Mate Cocido", "🍝 Almacén"),
    "galletita": ("Galletitas", "🍝 Almacén"),
    "galletitas": ("Galletitas", "🍝 Almacén"),
    "bizcocho": ("Bizcochos", "🍝 Almacén"),
    "bizcochos": ("Bizcochos", "🍝 Almacén"),
    "tostada": ("Tostadas", "🍝 Almacén"),
    "tostadas": ("Tostadas", "🍝 Almacén"),
    "mermelada": ("Mermeladas", "🍝 Almacén"),
    "conserva": ("Conservas", "🍝 Almacén"),
    "conservas": ("Conservas", "🍝 Almacén"),
    "atun": ("Atún", "🍝 Almacén"),
    "aderezo": ("Aderezos", "🍝 Almacén"),
    "mayonesa": ("Mayonesa", "🍝 Almacén"),
    "ketchup": ("Ketchup", "🍝 Almacén"),
    "snack": ("Snacks", "🍝 Almacén"),
    "snacks": ("Snacks", "🍝 Almacén"),
    "papas fritas": ("Snacks", "🍝 Almacén"),
    "golosina": ("Golosinas", "🍝 Almacén"),
    "golosinas": ("Golosinas", "🍝 Almacén"),
    "chocolate": ("Chocolates", "🍝 Almacén"),
    "chocolates": ("Chocolates", "🍝 Almacén"),
    "alfajor": ("Alfajores", "🍝 Almacén"),
    "alfajores": ("Alfajores", "🍝 Almacén"),
    "pan dulce": ("Pan Dulce", "🍝 Almacén"),
    "budin": ("Budines", "🍝 Almacén"),
    "budines": ("Budines", "🍝 Almacén"),
    "turron": ("Turrones", "🍝 Almacén"),
    "turrones": ("Turrones", "🍝 Almacén"),
    "confite": ("Confites", "🍝 Almacén"),
    "confites": ("Confites", "🍝 Almacén"),
    "gallet": ("Galletitas", "🍝 Almacén"),

    # 🧹 LIMPIEZA
    "limpieza": ("Art. Limpieza", "🧹 Limpieza"),
    "detergente": ("Detergente", "🧹 Limpieza"),
    "lavandina": ("Lavandina", "🧹 Limpieza"),
    "jabon liquido": ("Jabón Ropa", "🧹 Limpieza"),
    "suavizante": ("Suavizante", "🧹 Limpieza"),
    "desodorante ambiente": ("Desodorante Amb.", "🧹 Limpieza"),
    "papel higienico": ("Papel Higiénico", "🧹 Limpieza"),
    "rollo cocina": ("Rollo de Cocina", "🧹 Limpieza"),
    "trapo": ("Trapos", "🧹 Limpieza"),
    "insecticida": ("Insecticidas", "🧹 Limpieza"),

    # 🧴 PERFUMERÍA Y BEBÉ
    "perfumeria": ("Perfumería", "🧴 Perfumería y Bebé"),
    "shampoo": ("Shampoo", "🧴 Perfumería y Bebé"),
    "acondicionador": ("Acondicionador", "🧴 Perfumería y Bebé"),
    "jabon tocador": ("Jabón Tocador", "🧴 Perfumería y Bebé"),
    "desodorante corporal": ("Desodorante Corp.", "🧴 Perfumería y Bebé"),
    "crema": ("Cremas", "🧴 Perfumería y Bebé"),
    "dentifrico": ("Pasta Dental", "🧴 Perfumería y Bebé"),
    "colgate": ("Pasta Dental", "🧴 Perfumería y Bebé"),
    "pañal": ("Pañales", "🧴 Perfumería y Bebé"),
    "pañales": ("Pañales", "🧴 Perfumería y Bebé"),
    "toallita humeda": ("Toallitas Bebé", "🧴 Perfumería y Bebé"),
    "huggies": ("Pañales", "🧴 Perfumería y Bebé"),
    "pampers": ("Pañales", "🧴 Perfumería y Bebé"),
    "baby": ("Mundo Bebé", "🧴 Perfumería y Bebé"),
    "bebe": ("Mundo Bebé", "🧴 Perfumería y Bebé"),
    "farmacia": ("Farmacia", "🧴 Perfumería y Bebé"),

    # 📺 ELECTRO Y TECNO (PALABRAS TÉCNICAS AGREGADAS)
    "electro": ("Electro", "📺 Electro y Tecno"),
    "televisor": ("Smart TV", "📺 Electro y Tecno"),
    "tv": ("Smart TV", "📺 Electro y Tecno"),
    "smart tv": ("Smart TV", "📺 Electro y Tecno"),
    "aire": ("Aires Acondicionados", "📺 Electro y Tecno"), 
    "aires": ("Aires Acondicionados", "📺 Electro y Tecno"),
    "split": ("Aires Acondicionados", "📺 Electro y Tecno"), # TÉCNICA
    "inverter": ("Aires Acondicionados", "📺 Electro y Tecno"), # TÉCNICA
    "frigorias": ("Aires Acondicionados", "📺 Electro y Tecno"), # TÉCNICA
    "watts": ("Electro", "📺 Electro y Tecno"), # TÉCNICA
    "climatizacion": ("Aires Acondicionados", "📺 Electro y Tecno"), 
    "ventilador": ("Ventiladores", "📺 Electro y Tecno"),
    "heladera": ("Heladeras", "📺 Electro y Tecno"),
    "lavarropas": ("Lavarropas", "📺 Electro y Tecno"),
    "cocina": ("Cocinas", "📺 Electro y Tecno"),
    "microondas": ("Microondas", "📺 Electro y Tecno"),
    "pequeño electro": ("Pequeños Electro", "📺 Electro y Tecno"),
    "licuadora": ("Licuadoras", "📺 Electro y Tecno"),
    "pava": ("Pavas Eléctricas", "📺 Electro y Tecno"),
    "celular": ("Celulares", "📺 Electro y Tecno"),
    "celulares": ("Celulares", "📺 Electro y Tecno"),
    "smartphone": ("Celulares", "📺 Electro y Tecno"),
    "notebook": ("Notebooks", "📺 Electro y Tecno"),
    "auricular": ("Auriculares", "📺 Electro y Tecno"),
    "tecnologia": ("Tecnología", "📺 Electro y Tecno"),
    "philco": ("Electro Philco", "📺 Electro y Tecno"),
    "samsung": ("Electro Samsung", "📺 Electro y Tecno"),
    "noblex": ("Electro Noblex", "📺 Electro y Tecno"),
    "bgh": ("Electro BGH", "📺 Electro y Tecno"),
    "tcl": ("Electro TCL", "📺 Electro y Tecno"),
    "motorola": ("Celulares", "📺 Electro y Tecno"),

    # 🏠 HOGAR Y BAZAR
    "hogar": ("Hogar", "🏠 Hogar y Bazar"),
    "bazar": ("Bazar", "🏠 Hogar y Bazar"),
    "textil": ("Textil Hogar", "🏠 Hogar y Bazar"),
    "sabana": ("Sábanas", "🏠 Hogar y Bazar"),
    "toalla": ("Toallas", "🏠 Hogar y Bazar"),
    "deco": ("Decoración", "🏠 Hogar y Bazar"),
    "mueble": ("Muebles", "🏠 Hogar y Bazar"),
    "olla": ("Ollas y Sartenes", "🏠 Hogar y Bazar"),
    "vaso": ("Vasos y Copas", "🏠 Hogar y Bazar"),
    "colchon": ("Colchones", "🏠 Hogar y Bazar"),
    "valija": ("Valijas", "🏠 Hogar y Bazar"),

    # 🚗 AUTO Y AIRE LIBRE
    "automotor": ("Accesorios Auto", "🚗 Auto y Aire Libre"),
    "neumatico": ("Neumáticos", "🚗 Auto y Aire Libre"),
    "neumaticos": ("Neumáticos", "🚗 Auto y Aire Libre"),
    "cubierta": ("Neumáticos", "🚗 Auto y Aire Libre"),
    "bateria": ("Baterías Auto", "🚗 Auto y Aire Libre"),
    "camping": ("Camping", "🚗 Auto y Aire Libre"),
    "carpa": ("Carpas", "🚗 Auto y Aire Libre"),
    "reposera": ("Reposeras", "🚗 Auto y Aire Libre"),
    "pileta lona": ("Piletas", "🚗 Auto y Aire Libre"),
    "bicicleta": ("Bicicletas", "🚗 Auto y Aire Libre"),
    "deporte": ("Deportes", "🚗 Auto y Aire Libre"),
    "jardin": ("Jardín", "🚗 Auto y Aire Libre"),
    "aire libre": ("Aire Libre", "🚗 Auto y Aire Libre"),
    "climatizacion": ("Climatización", "🚗 Auto y Aire Libre"),

    # 🧸 JUGUETES
    "juguete": ("Juguetería", "🧸 Juguetería"),
    "juguetes": ("Juguetería", "🧸 Juguetería"),
    "jugueteria": ("Juguetería", "🧸 Juguetería"),
    "muñeca": ("Muñecas", "🧸 Juguetería"),
    "juego de mesa": ("Juegos de Mesa", "🧸 Juguetería"),
    "pelota": ("Pelotas", "🧸 Juguetería"),
    "pistola agua": ("Juguetes Agua", "🧸 Juguetería"),
    "inflable": ("Inflables", "🧸 Juguetería"),
    "pileta": ("Piletas", "🧸 Juguetería"),

    # 🐶 MASCOTAS
    "mascota": ("Mascotas", "🐶 Mascotas"),
    "perro": ("Alimento Perro", "🐶 Mascotas"),
    "gato": ("Alimento Gato", "🐶 Mascotas"),
    "balanceado": ("Alimento Balanceado", "🐶 Mascotas"),
}

# --- FUNCIÓN DE NORMALIZACIÓN ---
def normalizar_texto(texto):
    if not texto: return ""
    t = texto.lower()
    return ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')

# --- 2. LÓGICA DE DETECCIÓN MULTI-ETIQUETA ---
def detectar_categorias_inteligente(texto_completo, link=""):
    t_limpio = normalizar_texto(texto_completo.replace("masonline", "").replace("chango", ""))
    etiquetas = []
    
    if any(k in t_limpio for k in ["banco", "tarjeta", "modo", "ahorro", "financiacion", "cuotas"]):
        etiquetas.append("💳 Bancarias")

    for keyword, (producto, categoria_final) in DB_MAESTRA.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', t_limpio):
            if categoria_final not in etiquetas:
                etiquetas.append(categoria_final)

    if not etiquetas:
        if "fresco" in t_limpio: etiquetas.append("🧀 Lácteos y Frescos")
        elif "limpie" in t_limpio: etiquetas.append("🧹 Limpieza")
        elif "tecno" in t_limpio: etiquetas.append("📺 Electro y Tecno")
        elif "casa" in t_limpio: etiquetas.append("🏠 Hogar y Bazar")
        else:
            etiquetas.append("🍝 Almacén") 
            
    return etiquetas

# --- VALIDACIÓN OFERTA REAL ---
def es_oferta_valida(texto, src_url):
    t_norm = normalizar_texto(texto)
    url_clean = src_url.lower()

    if any(x in t_norm for x in ["horarios", "sucursales", "copyright", "posible info", "seguinos", "whatsapp", "descarga", "app", "canal", "comunidad"]): 
        return False

    if "html_directo" in src_url: return True

    for k in DB_MAESTRA.keys():
        if re.search(r'\b' + re.escape(k) + r'\b', t_norm): return True
    
    senales = ["%", "off", "2x1", "3x2", "4x2", "2da", "cuotas", "ahorro", "descuento", "precio", "$", "oferta", "llevando", "hasta", "80%", "bazar"]
    return any(s in t_norm for s in senales)

def obtener_link_especifico(elemento_img):
    try:
        padre = elemento_img.find_element(By.XPATH, "./ancestor::a")
        link = padre.get_attribute("href")
        if link and "http" in link: return link
    except: pass
    return URL_SUPER

# --- LIMPIEZA INTELIGENTE ---
def limpiar_texto_ocr(texto_sucio, texto_alt, src_url, categorias_detectadas=[]):
    t = (texto_sucio + " " + texto_alt).replace("\n", " ").strip()
    t_norm = normalizar_texto(t)
    
    if "html_directo" in src_url:
        return f"Oferta en {texto_sucio}"

    t_clean = t.replace("18CUOTAS", "18 Cuotas").replace("12CUOTAS", "12 Cuotas")
    
    prefijo = "Oferta"
    match_pct = re.search(r'(\d+)%', t_clean)
    match_nxn = re.search(r'(\d+[xX]\d+)', t_clean)
    match_cuotas = re.search(r'(\d+)\s*(CUO|CTA)', t_clean, re.IGNORECASE)
    
    if match_nxn: prefijo = match_nxn.group(1).lower()
    elif match_cuotas: prefijo = f"{match_cuotas.group(1)} Cuotas S/Int"
    elif match_pct:
        if "2do" in t_norm: prefijo = f"2do al {match_pct.group(1)}%"
        else: prefijo = f"{match_pct.group(1)}% Off"
    elif "$" in t_clean: prefijo = "Precio Especial"
    
    prods = []
    for k, v in DB_MAESTRA.items():
        if re.search(r'\b' + re.escape(k) + r'\b', t_norm):
            prods.append(v[0])
    
    if prods:
        prod_str = list(set(prods))[0] 
        return f"{prefijo} en {prod_str}"
    
    # SALVAVIDAS: Usar categoría si no hay producto
    if categorias_detectadas:
        cat_principal = categorias_detectadas[0]
        nombre_cat = cat_principal.replace("🧸 ", "").replace("📺 ", "").replace("🏠 ", "").replace("🥩 ", "").replace("💳 ", "").strip()
        
        if "Bancaria" not in nombre_cat and "Almacén" not in nombre_cat and "Varios" not in nombre_cat:
            return f"{prefijo} en {nombre_cat}"

    if any(k in t_norm for k in ["banco", "tarjeta", "modo"]):
        return "Promoción Bancaria"
    
    return f"{prefijo} en Varios Productos"

def procesar_oferta(elemento_img, src, texto_alt, titulos_procesados, ofertas_encontradas, forzar_texto=None):
    try:
        if forzar_texto:
            cats = detectar_categorias_inteligente(forzar_texto, "html_directo")
            titulo_final = limpiar_texto_ocr(forzar_texto, "", "html_directo", cats)
            
            link_real = URL_SUPER
            try: link_real = obtener_link_especifico(elemento_img)
            except: pass

            if titulo_final not in titulos_procesados:
                oferta = {
                    "supermercado": NOMBRE_SUPER,
                    "titulo": titulo_final,
                    "descripcion": forzar_texto,
                    "categoria": cats,
                    "link": link_real,
                    "imagen": src,
                    "fecha": time.strftime("%Y-%m-%d")
                }
                ofertas_encontradas.append(oferta)
                titulos_procesados.add(titulo_final)
                print(f"      🌈 [HTML] {cats} {titulo_final}")
            return

        if src.startswith("/"): src = URL_SUPER + src
        filename = os.path.basename(urllib.parse.urlparse(src).path)
        link_real = obtener_link_especifico(elemento_img)
        
        try:
            w = int(elemento_img.get_attribute("width") or 0)
            if w > 0 and w < 100: return
        except: pass

        headers = {'User-Agent': 'Mozilla/5.0'}
        try: resp = requests.get(src, headers=headers, timeout=5)
        except: return
        if resp.status_code != 200: return

        res_ocr = reader.readtext(resp.content, detail=0, paragraph=True)
        texto_ocr = " ".join(res_ocr)
        
        texto_completo = f"{texto_ocr} {texto_alt}"
        
        if not es_oferta_valida(texto_completo, filename): return
        
        cats = detectar_categorias_inteligente(texto_completo, filename)
        titulo_final = limpiar_texto_ocr(texto_ocr, texto_alt, filename, cats)

        if titulo_final not in titulos_procesados:
            oferta = {
                "supermercado": NOMBRE_SUPER,
                "titulo": titulo_final,
                "descripcion": texto_completo,
                "categoria": cats,
                "link": link_real,
                "imagen": src,
                "fecha": time.strftime("%Y-%m-%d")
            }
            ofertas_encontradas.append(oferta)
            titulos_procesados.add(titulo_final)
            print(f"      🌈 {cats} {titulo_final}")

    except Exception: pass

def escanear_banners_inferiores(driver, titulos_procesados, ofertas_encontradas):
    print("   🔎 Analizando Banners HTML Inferiores...")
    try:
        cards = driver.find_elements(By.CSS_SELECTOR, "div[class*='infocard-container']")
        if not cards:
             contenedores_texto = driver.find_elements(By.CSS_SELECTOR, "div[class*='infocards'] h3, div[class*='infocards'] h4")
        else:
             contenedores_texto = []

        if cards:
            for card in cards:
                try:
                    textos = card.find_elements(By.TAG_NAME, "h3") + card.find_elements(By.TAG_NAME, "h4")
                    if not textos: continue
                    texto_oferta = textos[0].text.strip()
                    imgs = card.find_elements(By.TAG_NAME, "img")
                    if not imgs: continue
                    src = imgs[0].get_attribute("src")
                    if src and texto_oferta:
                        procesar_oferta(imgs[0], src, "", titulos_procesados, ofertas_encontradas, forzar_texto=texto_oferta)
                except: continue
        
        elif contenedores_texto:
            for texto_element in contenedores_texto:
                try:
                    texto_oferta = texto_element.text.strip()
                    if not texto_oferta: continue
                    padre = texto_element.find_element(By.XPATH, "./..")
                    imgs = padre.find_elements(By.TAG_NAME, "img")
                    if not imgs:
                        abuelo = padre.find_element(By.XPATH, "./..")
                        imgs = abuelo.find_elements(By.TAG_NAME, "img")
                    if imgs:
                        src = imgs[0].get_attribute("src")
                        if src:
                            procesar_oferta(imgs[0], src, "", titulos_procesados, ofertas_encontradas, forzar_texto=texto_oferta)
                except: continue
    except Exception: pass

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
        time.sleep(6)

        print("   🎡 Escaneando Carrusel Principal...")
        for i in range(12): 
            imgs = driver.find_elements(By.CSS_SELECTOR, "img[class*='main-banner-slider']")
            for img in imgs:
                try:
                    src = img.get_attribute("src")
                    if src and src not in src_procesados:
                        src_procesados.add(src)
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
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(2)
        escanear_banners_inferiores(driver, titulos_procesados, ofertas_encontradas)

        print("   📜 Barrido Profundo...")
        altura_total = driver.execute_script("return document.body.scrollHeight")
        paso_scroll = 700
        
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
                        if not src: continue
                        if src in [o['imagen'] for o in ofertas_encontradas]: continue

                        texto_alt = (img.get_attribute("alt") or "") + " " + (img.get_attribute("title") or "")
                        es_http = "http" in src
                        es_api = src.startswith("/api/") 
                        
                        if es_http or es_api:
                            if src not in src_procesados:
                                if "icon" in src or "logo" in src: continue
                                src_procesados.add(src)
                                procesar_oferta(img, src, texto_alt, titulos_procesados, ofertas_encontradas)
                except: continue

    except Exception as e: print(f"❌ Error: {e}")
    finally: driver.quit()
    
    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
        json.dump(ofertas_encontradas, f, ensure_ascii=False, indent=4)
    return ofertas_encontradas

if __name__ == "__main__":
    datos = obtener_ofertas_masonline()
    print(f"\n💾 Guardado MasOnline: {len(datos)} ofertas.")