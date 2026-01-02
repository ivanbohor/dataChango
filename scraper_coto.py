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
NOMBRE_SUPER = "Coto"
URL_SUPER = "https://www.cotodigital.com.ar/sitios/cdigi/"
ARCHIVO_SALIDA = "ofertas_coto.json"

print(f">>> 🥩 Iniciando Scraper {NOMBRE_SUPER} (V24: Fix Electrodomésticos + Lógica Semántica)...")

if os.path.exists(ARCHIVO_SALIDA): os.remove(ARCHIVO_SALIDA)

reader = easyocr.Reader(['es'], gpu=False) 

# --- 1. DICCIONARIO MAESTRO (VERSION V46 - RESCATE ELECTRO) ---
DB_MAESTRA = {
    # 🥩 CARNICERÍA
    "carne": ("Carne Vacuna", "🥩 Carnicería"),
    "asado": ("Asado", "🥩 Carnicería"),
    "bife": ("Bifes", "🥩 Carnicería"),
    "bifes": ("Bifes", "🥩 Carnicería"),
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

    # 🧀 LÁCTEOS Y FRESCOS
    "leche": ("Leche", "🧀 Lácteos y Frescos"),
    "yogur": ("Yogur", "🧀 Lácteos y Frescos"),
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
    "feria": ("Feria de Frescos", "🧀 Lácteos y Frescos"), 

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

    # 📺 ELECTRO Y TECNO
    "electro": ("Electro", "📺 Electro y Tecno"),
    "electrodomesticos": ("Electro", "📺 Electro y Tecno"),
    "electrodomésticos": ("Electro", "📺 Electro y Tecno"),
    "televisor": ("Smart TV", "📺 Electro y Tecno"),
    "smart tv": ("Smart TV", "📺 Electro y Tecno"),
    "aire acondicionado": ("Aires Acondicionados", "📺 Electro y Tecno"),
    "ventilador": ("Ventiladores", "📺 Electro y Tecno"),
    "heladera": ("Heladeras", "📺 Electro y Tecno"),
    "lavarropas": ("Lavarropas", "📺 Electro y Tecno"),
    "cocina": ("Cocinas", "📺 Electro y Tecno"),
    "cocinas": ("Cocinas", "📺 Electro y Tecno"),
    "microondas": ("Microondas", "📺 Electro y Tecno"),
    "pequeño electro": ("Pequeños Electro", "📺 Electro y Tecno"),
    "licuadora": ("Licuadoras", "📺 Electro y Tecno"),
    "pava": ("Pavas Eléctricas", "📺 Electro y Tecno"),
    "celular": ("Celulares", "📺 Electro y Tecno"),
    "celulares": ("Celulares", "📺 Electro y Tecno"),
    "notebook": ("Notebooks", "📺 Electro y Tecno"),
    "auricular": ("Auriculares", "📺 Electro y Tecno"),
    "tecnologia": ("Tecnología", "📺 Electro y Tecno"),

    # 🏠 HOGAR Y BAZAR
    "hogar": ("Hogar", "🏠 Hogar y Bazar"),
    "bazar": ("Bazar", "🏠 Hogar y Bazar"),
    "textil": ("Textil Hogar", "🏠 Hogar y Bazar"),
    "sabana": ("Sábanas", "🏠 Hogar y Bazar"),
    "sabanas": ("Sábanas", "🏠 Hogar y Bazar"),
    "toalla": ("Toallas", "🏠 Hogar y Bazar"),
    "toallas": ("Toallas", "🏠 Hogar y Bazar"),
    "toallon": ("Toallones", "🏠 Hogar y Bazar"),
    "toallones": ("Toallones", "🏠 Hogar y Bazar"),
    "deco": ("Decoración", "🏠 Hogar y Bazar"),
    "mueble": ("Muebles", "🏠 Hogar y Bazar"),
    "muebles": ("Muebles", "🏠 Hogar y Bazar"),
    "olla": ("Ollas y Sartenes", "🏠 Hogar y Bazar"),
    "ollas": ("Ollas y Sartenes", "🏠 Hogar y Bazar"),
    "vaso": ("Vasos y Copas", "🏠 Hogar y Bazar"),
    "vasos": ("Vasos y Copas", "🏠 Hogar y Bazar"),
    "copa": ("Vasos y Copas", "🏠 Hogar y Bazar"),
    "copas": ("Vasos y Copas", "🏠 Hogar y Bazar"),
    "vidrio": ("Bazar Vidrio", "🏠 Hogar y Bazar"),
    "plato": ("Vajilla", "🏠 Hogar y Bazar"),
    "platos": ("Vajilla", "🏠 Hogar y Bazar"),
    "fuente": ("Fuentes", "🏠 Hogar y Bazar"),
    "fuentes": ("Fuentes", "🏠 Hogar y Bazar"),
    "tender": ("Tenders", "🏠 Hogar y Bazar"),
    "tenders": ("Tenders", "🏠 Hogar y Bazar"), 
    "playero": ("Art. Playa", "🏠 Hogar y Bazar"),
    "playeros": ("Art. Playa", "🏠 Hogar y Bazar"), 
    "playa": ("Art. Playa", "🏠 Hogar y Bazar"), 
    "mantel": ("Mantelería", "🏠 Hogar y Bazar"),
    "manteles": ("Mantelería", "🏠 Hogar y Bazar"),
    "lona": ("Lonas", "🏠 Hogar y Bazar"),
    "lonas": ("Lonas", "🏠 Hogar y Bazar"),
    "reposera": ("Reposeras", "🏠 Hogar y Bazar"), 
    "reposeras": ("Reposeras", "🏠 Hogar y Bazar"), 
    "home": ("Hogar", "🏠 Hogar y Bazar"),
    "colchon": ("Colchones", "🏠 Hogar y Bazar"),
    "valija": ("Valijas", "🏠 Hogar y Bazar"),

    # 🚗 AUTO Y AIRE LIBRE
    "automotor": ("Accesorios Auto", "🚗 Auto y Aire Libre"),
    "neumatico": ("Neumáticos", "🚗 Auto y Aire Libre"),
    "neumaticos": ("Neumáticos", "🚗 Auto y Aire Libre"),
    "cubierta": ("Neumáticos", "🚗 Auto y Aire Libre"),
    "bateria": ("Baterías Auto", "🚗 Auto y Aire Libre"),
    "baterias": ("Baterías Auto", "🚗 Auto y Aire Libre"),
    "camping": ("Camping", "🚗 Auto y Aire Libre"),
    "carpa": ("Carpas", "🚗 Auto y Aire Libre"),
    "carpas": ("Carpas", "🚗 Auto y Aire Libre"),
    "pileta lona": ("Piletas", "🚗 Auto y Aire Libre"),
    "bicicleta": ("Bicicletas", "🚗 Auto y Aire Libre"),
    "bicicletas": ("Bicicletas", "🚗 Auto y Aire Libre"),
    "deporte": ("Deportes", "🚗 Auto y Aire Libre"),
    "jardin": ("Jardín", "🚗 Auto y Aire Libre"),
    "aire libre": ("Aire Libre", "🚗 Auto y Aire Libre"),
    "rodados": ("Rodados", "🚗 Auto y Aire Libre"),

    # 🧸 JUGUETES
    "juguete": ("Juguetería", "🧸 Juguetería"),
    "juguetes": ("Juguetería", "🧸 Juguetería"),
    "muñeca": ("Muñecas", "🧸 Juguetería"),
    "juego de mesa": ("Juegos de Mesa", "🧸 Juguetería"),
    "pelota": ("Pelotas", "🧸 Juguetería"),
    "pistola agua": ("Juguetes Agua", "🧸 Juguetería"),
    "inflable": ("Inflables", "🧸 Juguetería"),

    # 🐶 MASCOTAS
    "mascota": ("Mascotas", "🐶 Mascotas"),
    "mascotas": ("Mascotas", "🐶 Mascotas"),
    "perro": ("Alimento Perro", "🐶 Mascotas"),
    "gato": ("Alimento Gato", "🐶 Mascotas"),
    "balanceado": ("Alimento Balanceado", "🐶 Mascotas"),
    "pedigree": ("Alimento Perro", "🐶 Mascotas"),
    "whiskas": ("Alimento Gato", "🐶 Mascotas"),
}

# --- MAPEO DE FILENAMES ---
MAPEO_FILENAMES = {
    "clases": "Pan Dulce y Budines",
    "pescaderia": "Pescadería",
    "jugueteria": "Juguetería",
    "vinos": "Vinos Seleccionados",
    "rodados": "Rodados y Bicicletas",
    "electro": "Electrodomésticos",
    "bazar": "Bazar y Hogar",
    "feria": "Feria de Frescos",
    "textil": "Textil y Ropa",
    "salon": "Almacén y Bebidas",
    "mix": "Ofertas Varias"
}

CATEGORIAS_FRESH_VALIDAS = ["🥩 Carnicería", "🧀 Lácteos y Frescos"]

# --- 2. LÓGICA DE DETECCIÓN MULTI-ETIQUETA (ESTRICTA + RESCATE) ---
def detectar_categorias_inteligente(texto_completo, filename=""):
    t_limpio = (texto_completo + " " + filename).lower()
    etiquetas = []
    
    # A. Detección Bancaria
    if any(k in t_limpio for k in ["banco", "tarjeta", "naranja", "modo", "ahorro", "financiacion", "cuotas"]):
        etiquetas.append("💳 Bancarias")

    # B. Detección por Texto (Barrido ESTRICTO)
    for keyword, (producto, categoria_final) in DB_MAESTRA.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', t_limpio):
            if categoria_final not in etiquetas:
                etiquetas.append(categoria_final)

    # C. RESCATE DE ELECTRODOMÉSTICOS (Lógica Fuzzy manual)
    # Si contiene fragmentos clave de "electrodomesticos" aunque el OCR falle
    if "electro" in t_limpio or "domesticos" in t_limpio:
        if "📺 Electro y Tecno" not in etiquetas:
            etiquetas.append("📺 Electro y Tecno")

    # D. FALLBACK INTELIGENTE
    if not etiquetas:
        if "feria" in filename: etiquetas.append("🧀 Lácteos y Frescos")
        elif "bazar" in filename: etiquetas.append("🏠 Hogar y Bazar")
        elif "electro" in filename: etiquetas.append("📺 Electro y Tecno")
        elif "textil" in filename: etiquetas.append("🏠 Hogar y Bazar")
        elif "juguete" in filename: etiquetas.append("🧸 Juguetería")
        elif "rodados" in filename: etiquetas.append("🚗 Auto y Aire Libre")
        elif "pescaderia" in filename: etiquetas.append("🥩 Carnicería")
        else:
            etiquetas.append("🍝 Almacén")
            
    # CORRECCIONES POST-DETECCIÓN
    if "jugueteria" in t_limpio and "🧸 Juguetería" not in etiquetas:
        etiquetas.append("🧸 Juguetería")
        
    if "🥩 Carnicería" in etiquetas and "🍝 Almacén" in etiquetas:
        etiquetas.remove("🍝 Almacén")
    
    # Si detectó Electro y Almacén (error común), borra Almacén
    if "📺 Electro y Tecno" in etiquetas and "🍝 Almacén" in etiquetas:
        etiquetas.remove("🍝 Almacén")
        
    if "🏠 Hogar y Bazar" in etiquetas and "🍝 Almacén" in etiquetas:
        etiquetas.remove("🍝 Almacén")
        
    # Limpieza de Alucinaciones
    if len(etiquetas) > 3:
        cats_prioritarias = ["🧸 Juguetería", "📺 Electro y Tecno", "🏠 Hogar y Bazar", "🐶 Mascotas"]
        etiquetas_filtradas = [c for c in etiquetas if c in cats_prioritarias]
        if etiquetas_filtradas: etiquetas = etiquetas_filtradas
        else: etiquetas = etiquetas[:2]
            
    return etiquetas

# --- VALIDACIÓN PROFESIONAL ---
def es_oferta_valida(texto, src="", categorias_detectadas=[]):
    t = texto.lower()
    if any(x in t for x in ["horarios", "sucursales", "copyright", "ver más", "retira"]): return False

    tiene_precio = bool(re.search(r'\$\s?\d+', t))
    tiene_porcentaje = bool(re.search(r'\d+\s?%', t))
    tiene_cuotas = bool(re.search(r'\d+\s*(?:cuotas|csi|pagos)', t))
    tiene_promo_txt = any(s in t for s in ["2x1", "3x2", "4x2", "2da", "3ra", "ahorro", "descuento", "off", "llevando"])
    
    if tiene_precio or tiene_porcentaje or tiene_cuotas or tiene_promo_txt:
        return True

    # Excepción Frescos
    es_fresh = any(c in CATEGORIAS_FRESH_VALIDAS for c in categorias_detectadas)
    if es_fresh: return True

    # Excepción Electro (A veces son banners de cuotas sin precio explícito)
    if "📺 Electro y Tecno" in categorias_detectadas and ("12" in t or "18" in t or "cuotas" in t):
        return True

    return False

# --- LIMPIEZA INTELIGENTE ---
def generar_titulo_bonito(texto_ocr, src):
    t = texto_ocr.replace("\n", " ").strip()
    t_lower = t.lower()
    nombre_archivo = src.split("/")[-1].lower()
    
    producto_detectado = "Varios"
    for clave, valor in MAPEO_FILENAMES.items():
        if clave in nombre_archivo:
            producto_detectado = valor
            break
    
    # Intento de rescate de producto por DB
    if producto_detectado == "Varios":
        prods = []
        for keyword, (prod, _) in DB_MAESTRA.items():
            if re.search(r'\b' + re.escape(keyword) + r'\b', t_lower):
                prods.append(prod)
        if prods:
            producto_detectado = ", ".join(list(set(prods))[:2])
    
    # Rescate final por categoría fuerte detectada
    if producto_detectado == "Varios":
        if "electro" in t_lower or "electro" in nombre_archivo:
            producto_detectado = "Electrodomésticos"
        elif "juguete" in t_lower or "juguete" in nombre_archivo:
            producto_detectado = "Juguetería"

    prefijo = "Oferta"
    match_nxn = re.search(r'(\d+[xX]\d+)', t)
    match_desc = re.search(r'(\d+)%', t)
    match_cuotas = re.search(r'\b(\d{1,2})\s*(?:CUO|CTA|PAGOS)', t, re.IGNORECASE)
    
    if "3x2" in nombre_archivo: prefijo = "3x2"
    elif "2x1" in nombre_archivo: prefijo = "2x1"
    elif "50" in nombre_archivo: prefijo = "50% Off"
    elif match_nxn: prefijo = match_nxn.group(1).lower()
    elif match_desc: 
        num = int(match_desc.group(1))
        if num < 5: prefijo = "Oferta"
        else: prefijo = f"{num}% Off"
    elif match_cuotas: prefijo = f"{match_cuotas.group(1)} Cuotas S/Int"
    
    return f"{prefijo} en {producto_detectado}"

def procesar_oferta(elemento_img, src, titulos_procesados, ofertas_encontradas):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        try: resp = requests.get(src, headers=headers, timeout=5) 
        except: return
        
        if resp.status_code != 200: return
        
        res_ocr = reader.readtext(resp.content, detail=0, paragraph=True)
        texto_ocr = " ".join(res_ocr)
        
        texto_analisis = f"{texto_ocr} {src}".strip()
        
        # 1. Detectar primero (necesitamos las categorías para validar excepciones)
        cats = detectar_categorias_inteligente(texto_ocr, src.split('/')[-1])
        
        # 2. Validar
        if not es_oferta_valida(texto_analisis, src, cats): return
        
        # 3. Título
        titulo = generar_titulo_bonito(texto_ocr, src)

        if titulo not in titulos_procesados:
            oferta = {
                "supermercado": NOMBRE_SUPER,
                "titulo": titulo,
                "descripcion": texto_ocr,
                "categoria": cats,
                "link": URL_SUPER,
                "imagen": src,
                "fecha": time.strftime("%Y-%m-%d")
            }
            ofertas_encontradas.append(oferta)
            titulos_procesados.add(titulo)
            print(f"      🥩 {cats} {titulo}")

    except Exception as e: pass

# --- SCRAPER PRINCIPAL ---
def iniciar_scraper():
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
        time.sleep(7) 
        
        print("   🔍 Escaneando por Patrón de URL (cdn/ofertas/)...")
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);") 
        time.sleep(1)

        todas_imgs = driver.find_elements(By.TAG_NAME, "img")
        print(f"      -> Total imágenes en DOM: {len(todas_imgs)}")
        
        for img in todas_imgs:
            try:
                src = img.get_attribute("src")
                if not src: 
                    srcset = img.get_attribute("srcset")
                    if srcset: src = srcset.split(" ")[0]

                es_oferta_coto = src and ("cotodigital3.com.ar" in src) and ("/ofertas/" in src)
                
                if es_oferta_coto and src not in src_procesados:
                    src_procesados.add(src)
                    procesar_oferta(img, src, titulos_procesados, ofertas_encontradas)
            
            except: continue
            
    except Exception as e: print(f"❌ Error: {e}")
    finally: driver.quit()
    
    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
        json.dump(ofertas_encontradas, f, ensure_ascii=False, indent=4)
    print(f"\n💾 Guardado Coto: {len(ofertas_encontradas)} ofertas.")

if __name__ == "__main__":
    iniciar_scraper()