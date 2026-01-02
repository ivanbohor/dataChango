import json
import time
import requests
import easyocr
import re
import os
import unicodedata
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# --- CONFIGURACIÓN ---
NOMBRE_SUPER = "Jumbo"
URL_SUPER = "https://www.jumbo.com.ar"
ARCHIVO_SALIDA = "ofertas_jumbo.json"

print(f">>> 🐘 Iniciando Scraper {NOMBRE_SUPER} (V16.1: Fix 100% Quesos)...")

if os.path.exists(ARCHIVO_SALIDA): os.remove(ARCHIVO_SALIDA)

reader = easyocr.Reader(['es'], gpu=False) 

# --- 1. DICCIONARIO MAESTRO (V41) ---
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
    "milanesa": ("Milanesas", "🥩 Carnicería"),
    "salchicha": ("Salchichas", "🥩 Carnicería"),
    "pescado": ("Pescadería", "🥩 Carnicería"),
    "pescaderia": ("Pescadería", "🥩 Carnicería"),
    "pavita": ("Pavita", "🥩 Carnicería"),
    "granjas": ("Pollo", "🥩 Carnicería"),
    "paty": ("Hamburguesas", "🥩 Carnicería"),

    # 🧀 LÁCTEOS Y FRESCOS
    "leche": ("Leche", "🧀 Lácteos y Frescos"),
    "yogur": ("Yogur", "🧀 Lácteos y Frescos"),
    "queso": ("Quesos", "🧀 Lácteos y Frescos"),
    "manteca": ("Manteca", "🧀 Lácteos y Frescos"),
    "crema": ("Crema", "🧀 Lácteos y Frescos"),
    "dulce de leche": ("Dulce de Leche", "🧀 Lácteos y Frescos"),
    "postre": ("Postres Lácteos", "🧀 Lácteos y Frescos"),
    "fiambre": ("Fiambres", "🧀 Lácteos y Frescos"),
    "jamon": ("Jamón", "🧀 Lácteos y Frescos"),
    "salam": ("Salame", "🧀 Lácteos y Frescos"),
    "pasta": ("Pastas Frescas", "🧀 Lácteos y Frescos"),
    "tapas": ("Tapas", "🧀 Lácteos y Frescos"),
    "fruta": ("Frutas", "🧀 Lácteos y Frescos"),
    "verdura": ("Verduras", "🧀 Lácteos y Frescos"),
    "casancrem": ("Queso Crema", "🧀 Lácteos y Frescos"),
    "serenisima": ("Lácteos", "🧀 Lácteos y Frescos"),
    "sancor": ("Lácteos", "🧀 Lácteos y Frescos"),
    "finlandia": ("Quesos", "🧀 Lácteos y Frescos"),
    "actimel": ("Yogur", "🧀 Lácteos y Frescos"),
    "danette": ("Postres", "🧀 Lácteos y Frescos"),

    # 🍷 BEBIDAS
    "bebida": ("Bebidas", "🍷 Bebidas"),
    "gaseosa": ("Gaseosas", "🍷 Bebidas"),
    "cola": ("Gaseosa Cola", "🍷 Bebidas"),
    "agua": ("Aguas", "🍷 Bebidas"),
    "jugo": ("Jugos", "🍷 Bebidas"),
    "cerveza": ("Cervezas", "🍷 Bebidas"),
    "vino": ("Vinos", "🍷 Bebidas"),
    "champagne": ("Champagne", "🍷 Bebidas"),
    "espumante": ("Espumantes", "🍷 Bebidas"),
    "sidra": ("Sidras", "🍷 Bebidas"),
    "fernet": ("Fernet", "🍷 Bebidas"),
    "aperitivo": ("Aperitivos", "🍷 Bebidas"),
    "gin": ("Gin", "🍷 Bebidas"),
    "vodka": ("Vodka", "🍷 Bebidas"),
    "whisky": ("Whisky", "🍷 Bebidas"),
    "malbec": ("Vino Malbec", "🍷 Bebidas"),
    "cabernet": ("Vino Cabernet", "🍷 Bebidas"),
    "sprite": ("Gaseosa Lima", "🍷 Bebidas"),

    # 🍝 ALMACÉN
    "almacen": ("Almacén", "🍝 Almacén"),
    "aceite": ("Aceite", "🍝 Almacén"),
    "arroz": ("Arroz", "🍝 Almacén"),
    "fideo": ("Fideos Secos", "🍝 Almacén"),
    "harina": ("Harina", "🍝 Almacén"),
    "yerba": ("Yerba", "🍝 Almacén"),
    "cafe": ("Café", "🍝 Almacén"),
    "mate cocido": ("Mate Cocido", "🍝 Almacén"),
    "galletita": ("Galletitas", "🍝 Almacén"),
    "bizcocho": ("Bizcochos", "🍝 Almacén"),
    "tostada": ("Tostadas", "🍝 Almacén"),
    "mermelada": ("Mermeladas", "🍝 Almacén"),
    "conserva": ("Conservas", "🍝 Almacén"),
    "atun": ("Atún", "🍝 Almacén"),
    "aderezo": ("Aderezos", "🍝 Almacén"),
    "mayonesa": ("Mayonesa", "🍝 Almacén"),
    "ketchup": ("Ketchup", "🍝 Almacén"),
    "snack": ("Snacks", "🍝 Almacén"),
    "papas fritas": ("Snacks", "🍝 Almacén"),
    "golosina": ("Golosinas", "🍝 Almacén"),
    "chocolate": ("Chocolates", "🍝 Almacén"),
    "alfajor": ("Alfajores", "🍝 Almacén"),
    "pan dulce": ("Pan Dulce", "🍝 Almacén"),
    "budin": ("Budines", "🍝 Almacén"),
    "turron": ("Turrones", "🍝 Almacén"),
    "confite": ("Confites", "🍝 Almacén"),
    "nestle": ("Productos Nestlé", "🍝 Almacén"),
    "dolca": ("Café", "🍝 Almacén"),
    "azucar": ("Azúcar", "🍝 Almacén"),

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
    "ariel": ("Jabón Ropa", "🧹 Limpieza"),
    "skip": ("Jabón Ropa", "🧹 Limpieza"),
    "cif": ("Limpiadores", "🧹 Limpieza"),
    "magistral": ("Detergente", "🧹 Limpieza"),
    "ayudin": ("Lavandina", "🧹 Limpieza"),
    "elite": ("Papel Higiénico", "🧹 Limpieza"),

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
    "toallita humeda": ("Toallitas Bebé", "🧴 Perfumería y Bebé"),
    "huggies": ("Pañales", "🧴 Perfumería y Bebé"),
    "pampers": ("Pañales", "🧴 Perfumería y Bebé"),
    "baby": ("Mundo Bebé", "🧴 Perfumería y Bebé"),
    "dove": ("Cuidado Personal", "🧴 Perfumería y Bebé"),
    "rexona": ("Desodorante", "🧴 Perfumería y Bebé"),
    "pantene": ("Cuidado Capilar", "🧴 Perfumería y Bebé"),
    "nivea": ("Cremas", "🧴 Perfumería y Bebé"),

    # 📺 ELECTRO Y TECNO
    "electro": ("Electro", "📺 Electro y Tecno"),
    "televisor": ("Smart TV", "📺 Electro y Tecno"),
    "smart tv": ("Smart TV", "📺 Electro y Tecno"),
    "aire acondicionado": ("Aires Acondicionados", "📺 Electro y Tecno"),
    "ventilador": ("Ventiladores", "📺 Electro y Tecno"),
    "heladera": ("Heladeras", "📺 Electro y Tecno"),
    "lavarropas": ("Lavarropas", "📺 Electro y Tecno"),
    "cocina": ("Cocinas", "📺 Electro y Tecno"),
    "microondas": ("Microondas", "📺 Electro y Tecno"),
    "pequeño electro": ("Pequeños Electro", "📺 Electro y Tecno"),
    "licuadora": ("Licuadoras", "📺 Electro y Tecno"),
    "pava": ("Pavas Eléctricas", "📺 Electro y Tecno"),
    "celular": ("Celulares", "📺 Electro y Tecno"),
    "notebook": ("Notebooks", "📺 Electro y Tecno"),
    "auricular": ("Auriculares", "📺 Electro y Tecno"),
    "tecnologia": ("Tecnología", "📺 Electro y Tecno"),
    "horno": ("Hornos", "📺 Electro y Tecno"),

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
    "cama": ("Ropa de Cama", "🏠 Hogar y Bazar"),

    # 🚗 AUTO Y AIRE LIBRE
    "automotor": ("Accesorios Auto", "🚗 Auto y Aire Libre"),
    "neumatico": ("Neumáticos", "🚗 Auto y Aire Libre"),
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

    # 🧸 JUGUETES
    "juguete": ("Juguetería", "🧸 Juguetería"),
    "muñeca": ("Muñecas", "🧸 Juguetería"),
    "juego de mesa": ("Juegos de Mesa", "🧸 Juguetería"),
    "pelota": ("Pelotas", "🧸 Juguetería"),
    "pistola agua": ("Juguetes Agua", "🧸 Juguetería"),
    "inflable": ("Inflables", "🧸 Juguetería"),

    # 🐶 MASCOTAS
    "mascota": ("Mascotas", "🐶 Mascotas"),
    "perro": ("Alimento Perro", "🐶 Mascotas"),
    "gato": ("Alimento Gato", "🐶 Mascotas"),
    "balanceado": ("Alimento Balanceado", "🐶 Mascotas"),
    "pedigree": ("Alimento Perro", "🐶 Mascotas"),
    "whiskas": ("Alimento Gato", "🐶 Mascotas"),
    "dog": ("Alimento Perro", "🐶 Mascotas"),
    "cat": ("Alimento Gato", "🐶 Mascotas"),
    "piedras": ("Piedras Sanitarias", "🐶 Mascotas"),
}

# --- 2. LÓGICA DE DETECCIÓN MULTI-ETIQUETA ---
def detectar_categorias_inteligente(texto_completo, link=""):
    t_limpio = texto_completo.lower().replace("jumbo", "")
    etiquetas = []
    
    if any(k in t_limpio for k in ["banco", "tarjeta", "cencosud", "cencopay", "modo", "ahorro", "financiacion", "cuotas"]):
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

def es_oferta_valida(texto):
    t = texto.lower()
    if any(x in t for x in ["horarios", "sucursales", "copyright", "ver más", "retira", "beneficio", "descubri", "conoce"]): return False

    # Filtros obligatorios para evitar publicidad pura
    tiene_precio = bool(re.search(r'\$\s?\d+', t))
    tiene_porcentaje = bool(re.search(r'\d+\s?%', t))
    tiene_cuotas = bool(re.search(r'\d+\s*(?:cuotas|csi|pagos)', t))
    tiene_promo_txt = any(s in t for s in ["2x1", "3x2", "4x2", "2da al", "3ra al", "ahorro", "descuento", "off", "oferta"])
    
    return tiene_precio or tiene_porcentaje or tiene_cuotas or tiene_promo_txt

def obtener_link_especifico(elemento_img):
    try:
        padre = elemento_img.find_element(By.XPATH, "./ancestor::a")
        link = padre.get_attribute("href")
        if link: return link
    except: pass
    return URL_SUPER

# --- 3. LIMPIEZA Y FORMATEO (FIX ANTI-100%) ---
def limpiar_texto_ocr(texto_sucio, texto_alt=""):
    texto_combinado = texto_sucio
    if texto_alt and texto_alt.lower() not in texto_sucio.lower():
        texto_combinado += " " + texto_alt

    t = texto_combinado.replace("\n", " ").strip()
    t = t.replace("Ax2", "4x2").replace("ax2", "4x2").replace("Ax1", "2x1")
    t = t.replace("18CUOTAS", "18 Cuotas").replace("12CUOTAS", "12 Cuotas")
    t_lower = t.lower()
    
    if any(k in t_lower for k in ["banco", "tarjeta", "cencosud", "cencopay", "modo"]):
        return "Promoción Bancaria"

    prefijo = "Oferta"
    match_nxn = re.search(r'(\d+[xX]\d+)', t)            
    match_cuotas = re.search(r'(\d+)\s*(CUO|CTA|CSI)', t, re.IGNORECASE) 
    match_desc = re.search(r'(\d+)%', t)
    
    if match_nxn: prefijo = match_nxn.group(1).lower().replace("x", "x")
    elif match_cuotas: prefijo = f"{match_cuotas.group(1)} Cuotas S/Int"
    elif match_desc: 
        num = int(match_desc.group(1))
        # CORRECCIÓN V16.1: Si es 100%, solo es válido si dice "2do" (2x1)
        if num == 100:
            if "2do" in t_lower or "segunda" in t_lower: prefijo = "2x1"
            else: prefijo = "Oferta" # 100% suelto suele ser "100% Calidad", lo ignoramos como descuento.
        elif num > 100:
            if str(num).startswith("2"): prefijo = f"2do al {str(num)[1:]}%"
            else: prefijo = f"{num % 100}% Off"
        else:
            if "2do" in t_lower or "segunda" in t_lower: prefijo = f"2do al {num}%"
            else: prefijo = f"{num}% Off"
    
    if "hasta" in t_lower and "50" in t: prefijo = "Hasta 50% Off"
    
    prods_encontrados = []
    for keyword, (producto, _) in DB_MAESTRA.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', t_lower):
            prods_encontrados.append(producto)
    
    if prods_encontrados: 
        prod_str = ", ".join(list(set(prods_encontrados))[:2])
        return f"{prefijo} en {prod_str}"
    
    # Fallback mejorado: Si el título es muy largo, lo cortamos
    if not prods_encontrados and texto_alt and len(texto_alt) > 3 and "oferta" not in texto_alt.lower():
        titulo_alt = texto_alt.title()
        # Evitar redundancia fea "Hasta 50% en Hasta 50%..."
        if "hasta" in titulo_alt.lower() or "%" in titulo_alt:
            return f"{prefijo} en Varios Productos"
        return f"{prefijo} en {titulo_alt[:40]}..." # Cortamos a 40 chars

    return f"{prefijo} en Varios Productos"

def procesar_oferta(elemento_img, src, texto_alt, titulos_procesados, ofertas_encontradas):
    try:
        link_real = obtener_link_especifico(elemento_img)
        headers = {'User-Agent': 'Mozilla/5.0'}
        try: resp = requests.get(src, headers=headers, timeout=3)
        except: return
        
        if resp.status_code != 200: return
        res_ocr = reader.readtext(resp.content, detail=0, paragraph=True)
        texto_ocr = " ".join(res_ocr)
        
        texto_analisis = f"{texto_ocr} {texto_alt}".strip()
        
        if not es_oferta_valida(texto_analisis): return
        
        cats = detectar_categorias_inteligente(texto_analisis, link_real)
        titulo_bonito = limpiar_texto_ocr(texto_ocr, texto_alt)
        
        if titulo_bonito not in titulos_procesados:
            oferta = {
                "supermercado": NOMBRE_SUPER,
                "titulo": titulo_bonito,
                "descripcion": texto_ocr + " " + texto_alt,
                "categoria": cats,
                "link": link_real,
                "imagen": src,
                "fecha": time.strftime("%Y-%m-%d")
            }
            ofertas_encontradas.append(oferta)
            titulos_procesados.add(titulo_bonito)
            
            print(f"      🐘 {cats} {titulo_bonito}")

    except Exception as e: pass

# --- 4. SCRAPER PRINCIPAL ---
def obtener_ofertas_jumbo():
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
        
        print("   🚜 Iniciando Barrido de Ofertas...")
        altura_total = driver.execute_script("return document.body.scrollHeight")
        paso_scroll = 600
        
        for y in range(0, altura_total, paso_scroll):
            driver.execute_script(f"window.scrollTo(0, {y});")
            time.sleep(1.0) 
            
            imagenes_visibles = driver.find_elements(By.TAG_NAME, "img")
            for img in imagenes_visibles:
                try:
                    w = int(img.get_attribute("width") or img.size['width'] or 0)
                    h = int(img.get_attribute("height") or img.size['height'] or 0)
                    
                    es_main = w > 600 and h > 200
                    es_mid = w > 300 and h > 150
                    es_card = w > 180 and h > 180
                    
                    if es_main or es_mid or es_card:
                        src = img.get_attribute("src")
                        if not src or "data:" in src:
                            srcset = img.get_attribute("srcset")
                            if srcset: src = srcset.split(" ")[0]
                        
                        alt_text = img.get_attribute("alt") or ""
                        title_text = img.get_attribute("title") or ""
                        
                        if src and "http" in src and src not in src_procesados:
                            if "icon" in src or "logo" in src: continue
                            src_procesados.add(src)
                            procesar_oferta(img, src, alt_text + " " + title_text, titulos_procesados, ofertas_encontradas)
                            
                except: continue

    except Exception as e: print(f"❌ Error: {e}")
    finally: driver.quit()
    return ofertas_encontradas

if __name__ == "__main__":
    datos = obtener_ofertas_jumbo()
    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
    print(f"\n💾 Guardado Jumbo: {len(datos)} ofertas.")