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
NOMBRE_SUPER = "Carrefour"
URL_SUPER = "https://www.carrefour.com.ar"
ARCHIVO_SALIDA = "ofertas_carrefour.json"

print(f">>> 🇫🇷 Iniciando Scraper {NOMBRE_SUPER} (V35: Filtro Anti-Productos + Fix Links)...")

if os.path.exists(ARCHIVO_SALIDA): os.remove(ARCHIVO_SALIDA)

reader = easyocr.Reader(['es'], gpu=False) 

# --- 1. DICCIONARIO MAESTRO (VERSION V58) ---
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

    # 📺 ELECTRO Y TECNO
    "electro": ("Electro", "📺 Electro y Tecno"),
    "televisor": ("Smart TV", "📺 Electro y Tecno"),
    "tv": ("Smart TV", "📺 Electro y Tecno"),
    "smart tv": ("Smart TV", "📺 Electro y Tecno"),
    "aire": ("Aires Acondicionados", "📺 Electro y Tecno"), 
    "aires": ("Aires Acondicionados", "📺 Electro y Tecno"),
    "split": ("Aires Acondicionados", "📺 Electro y Tecno"), 
    "inverter": ("Aires Acondicionados", "📺 Electro y Tecno"), 
    "frigorias": ("Aires Acondicionados", "📺 Electro y Tecno"), 
    "watts": ("Electro", "📺 Electro y Tecno"), 
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
    "intel": ("Informática", "📺 Electro y Tecno"), 
    "core": ("Informática", "📺 Electro y Tecno"), 
    "ryzen": ("Informática", "📺 Electro y Tecno"), 
    "ram": ("Informática", "📺 Electro y Tecno"), 
    "ssd": ("Informática", "📺 Electro y Tecno"), 
    "gb": ("Informática", "📺 Electro y Tecno"), 
    "pulgadas": ("TV/Monitor", "📺 Electro y Tecno"), 
    "4k": ("Smart TV", "📺 Electro y Tecno"), 
    "uhd": ("Smart TV", "📺 Electro y Tecno"), 
    "android": ("Celulares/TV", "📺 Electro y Tecno"),

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
    "navidad": ("Navidad", "🏠 Hogar y Bazar"), 
    "arbol": ("Navidad", "🏠 Hogar y Bazar"), 
    "adorno": ("Navidad", "🏠 Hogar y Bazar"), 
    "luces": ("Navidad", "🏠 Hogar y Bazar"),

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
    "juguet": ("Juguetería", "🧸 Juguetería"), 
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
    "alimento seco": ("Alimento Mascotas", "🐶 Mascotas"),
    "alimento humedo": ("Alimento Mascotas", "🐶 Mascotas"),
    "cachorro": ("Alimento Mascotas", "🐶 Mascotas"), 
    "adulto": ("Alimento Mascotas", "🐶 Mascotas"), 
    "raza": ("Alimento Mascotas", "🐶 Mascotas"), 
    "kilos": ("Alimento Mascotas", "🐶 Mascotas"), 
    "kg": ("Alimento Mascotas", "🐶 Mascotas"), 
    "pedigr": ("Alimento Mascotas", "🐶 Mascotas"),
    "whisk": ("Alimento Mascotas", "🐶 Mascotas"),
    "dog chow": ("Alimento Mascotas", "🐶 Mascotas"),
    "cat chow": ("Alimento Mascotas", "🐶 Mascotas"),
    "pro plan": ("Alimento Mascotas", "🐶 Mascotas"),
    "eukanuba": ("Alimento Mascotas", "🐶 Mascotas"),
    "royal canin": ("Alimento Mascotas", "🐶 Mascotas"),
    "sabrositos": ("Alimento Mascotas", "🐶 Mascotas"),
    "tiernit": ("Alimento Mascotas", "🐶 Mascotas"),
    "gati": ("Alimento Mascotas", "🐶 Mascotas"), 
    "excellence": ("Alimento Mascotas", "🐶 Mascotas"),
    "sieger": ("Alimento Mascotas", "🐶 Mascotas"),
    "nutrique": ("Alimento Mascotas", "🐶 Mascotas"),
}

# --- FUNCIONES DE LIMPIEZA ---
def normalizar_texto(texto):
    if not texto: return ""
    t = texto.lower()
    return ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')

def sanitizar_texto_exclusiones(texto):
    if not texto: return ""
    t_norm = normalizar_texto(texto)
    palabras_corte = ["excluye", "no incluye", "legales", "bases y cond", "consultar en", "no acumulable", "ver legal", "valido en"]
    indice_corte = len(t_norm)
    for palabra in palabras_corte:
        idx = t_norm.find(palabra)
        if idx != -1 and idx < indice_corte:
            indice_corte = idx
    return texto[:indice_corte]

# --- LÓGICA DETECCIÓN ---
def detectar_categorias_inteligente(texto_sanitizado, link=""):
    t_limpio = normalizar_texto(texto_sanitizado.replace("carrefour", ""))
    etiquetas = []
    
    if any(k in t_limpio for k in ["banco", "tarjeta", "modo", "ahorro", "financiacion", "cuotas"]):
        etiquetas.append("💳 Bancarias")

    if "12 cuotas" in t_limpio or "18 cuotas" in t_limpio or "24 cuotas" in t_limpio:
        etiquetas.append("📺 Electro y Tecno")
    
    for keyword, (producto, categoria_final) in DB_MAESTRA.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', t_limpio):
            if categoria_final not in etiquetas:
                etiquetas.append(categoria_final)

    categorias_producto = [c for c in etiquetas if c != "💳 Bancarias"]
    if len(set(categorias_producto)) > 3: return ["💳 Bancarias"]

    if not etiquetas:
        if "fresco" in t_limpio: etiquetas.append("🧀 Lácteos y Frescos")
        elif "limpie" in t_limpio: etiquetas.append("🧹 Limpieza")
        elif "tecno" in t_limpio: etiquetas.append("📺 Electro y Tecno")
        elif "casa" in t_limpio: etiquetas.append("🏠 Hogar y Bazar")
        else: etiquetas.append("🍝 Almacén") 
    return etiquetas

# --- VALIDACIÓN V35 (FILTRO DE PRODUCTOS SUELTOS) ---
def es_oferta_valida(texto_sanitizado, src_url):
    t_norm = normalizar_texto(texto_sanitizado)
    
    # 1. Filtro Negativo Estándar
    if any(x in t_norm for x in ["horarios", "sucursales", "copyright", "posible info", "seguinos", "whatsapp", "descarga", "app", "canal", "comunidad", "beneficio"]): 
        return False

    # 2. Señales de Promoción (Obligatorias)
    # Si no tiene "%", "off", "cuotas", etc., NO es una oferta, es solo un producto.
    senales = ["%", "off", "2x1", "3x2", "4x2", "2da", "cuotas", "ahorro", "descuento", "precio", "$", "oferta", "llevando", "hasta", "80%", "bazar", "especial"]
    tiene_senal = any(s in t_norm for s in senales)
    
    if not tiene_senal:
        # Excepción muy específica: Si detecta "Electro" por inferencia visual (futura) o palabras clave muy fuertes sin precio (ej: "HOT SALE")
        # Por ahora, somos estrictos: Sin señal de oferta -> Basura.
        return False

    # 3. Coincidencia con Diccionario (Solo si pasó el filtro de señal)
    for k in DB_MAESTRA.keys():
        if re.search(r'\b' + re.escape(k) + r'\b', t_norm): return True
    
    return True # Si tiene señal de oferta pero no producto conocido, pasa como "Varios"

# --- LIMPIEZA INTELIGENTE ---
def limpiar_texto_ocr(texto_sanitizado, texto_alt, src_url, categorias_detectadas=[]):
    t = (texto_sanitizado + " " + texto_alt).replace("\n", " ").strip()
    t_norm = normalizar_texto(t)
    t_clean = t.replace("12CUOTAS", "12 Cuotas").replace("18CUOTAS", "18 Cuotas").replace("6CUOTAS", "6 Cuotas")
    
    prefijo = "Oferta"
    match_cuotas = re.search(r'\b(\d{1,2})\s*(?:CUO|CTA|PAGOS)', t_clean, re.IGNORECASE)
    match_pct = re.search(r'(\d+)%', t_clean)
    match_nxn = re.search(r'(\d+[xX]\d+)', t_clean)
    
    if "501" in t_clean and "descuento" in t_norm: prefijo = "50% Off"
    elif match_nxn: prefijo = match_nxn.group(1).lower()
    elif match_cuotas: prefijo = f"{match_cuotas.group(1)} Cuotas S/Int"
    elif match_pct:
        if "2do" in t_norm: prefijo = f"2do al {match_pct.group(1)}%"
        else: prefijo = f"{match_pct.group(1)}% Off"
    elif "$" in t_clean: prefijo = "Precio Especial"
    
    prods = []
    for k, v in DB_MAESTRA.items():
        if re.search(r'\b' + re.escape(k) + r'\b', t_norm): prods.append(v[0])
    
    if prods:
        if len(set(prods)) > 3:
             if any(k in t_norm for k in ["banco", "tarjeta", "modo"]): return "Promoción Bancaria"
             return f"{prefijo} en Varios Productos"
        prod_str = list(set(prods))[0] 
        return f"{prefijo} en {prod_str}"
    
    if categorias_detectadas:
        cats_prioritarias = [c for c in categorias_detectadas if "Electro" in c or "Hogar" in c]
        cat_principal = cats_prioritarias[0] if cats_prioritarias else categorias_detectadas[0]
        nombre_cat = cat_principal.replace("🧸 ", "").replace("📺 ", "").replace("🏠 ", "").replace("🥩 ", "").replace("💳 ", "").strip()
        if "Bancaria" not in nombre_cat and "Almacén" not in nombre_cat and "Varios" not in nombre_cat:
            return f"{prefijo} en {nombre_cat}"
        if ("12 Cuotas" in prefijo or "18 Cuotas" in prefijo) and "Electro" not in nombre_cat:
             return f"{prefijo} en Electro"

    if any(k in t_norm for k in ["banco", "tarjeta", "modo"]): return "Promoción Bancaria"
    return f"{prefijo} en Varios Productos"

def procesar_oferta(src, href_real, texto_alt, titulos_procesados, ofertas_encontradas):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        try: resp = requests.get(src, headers=headers, timeout=5)
        except: return
        if resp.status_code != 200: return

        res_ocr = reader.readtext(resp.content, detail=0, paragraph=True)
        texto_ocr = " ".join(res_ocr)
        
        # --- DEBUG MODE ---
        # print(f"   🔍 RAW OCR: {texto_ocr[:100]}...") 
        # ------------------

        texto_limpio = sanitizar_texto_exclusiones(f"{texto_ocr} {texto_alt}")
        
        filename = os.path.basename(urllib.parse.urlparse(src).path)
        if not es_oferta_valida(texto_limpio, filename): return
        
        cats = detectar_categorias_inteligente(texto_limpio, filename)
        titulo_final = limpiar_texto_ocr(texto_limpio, "", filename, cats)

        if titulo_final not in titulos_procesados:
            oferta = {
                "supermercado": NOMBRE_SUPER,
                "titulo": titulo_final,
                "descripcion": texto_ocr,
                "categoria": cats,
                "link": href_real, # URL REAL DEL PRODUCTO/CATEGORÍA
                "imagen": src,
                "fecha": time.strftime("%Y-%m-%d")
            }
            ofertas_encontradas.append(oferta)
            titulos_procesados.add(titulo_final)
            print(f"      🇫🇷 {cats} {titulo_final}")
    except Exception: pass

# --- EXTRACCIÓN MASIVA POR JS (CON LINKS) ---
def extraccion_masiva_js(driver, titulos_procesados, ofertas_encontradas):
    print("   ☢️ Ejecutando Extracción Masiva JS (Imágenes + Links)...")
    try:
        # Script Mejorado: Busca la imagen Y su link padre
        script_js = """
        var items = [];
        var imgs = document.getElementsByTagName('img');
        for (var i = 0; i < imgs.length; i++) {
            var src = imgs[i].src || imgs[i].dataset.src;
            if (src) {
                var parentAnchor = imgs[i].closest('a');
                var href = parentAnchor ? parentAnchor.href : "";
                items.push({src: src, href: href});
            }
        }
        return items;
        """
        items_crudos = driver.execute_script(script_js)
        
        # Filtrar solo carrefour assets
        items_filtrados = [item for item in items_crudos if "carrefourar.vtexassets.com" in item['src']]
        
        # Eliminar duplicados por SRC
        items_unicos = {item['src']: item for item in items_filtrados}.values()
        
        print(f"      -> {len(items_unicos)} elementos únicos encontrados.")
        
        for item in items_unicos:
            if item['src'] not in [o['imagen'] for o in ofertas_encontradas]:
                # Si no tiene href, usamos la URL base, pero intentamos que tenga href
                href_final = item['href'] if item['href'] else URL_SUPER
                procesar_oferta(item['src'], href_final, "JS Masivo", titulos_procesados, ofertas_encontradas)
                
    except Exception as e: print(f"Error en JS Masivo: {e}")

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
        time.sleep(6)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        extraccion_masiva_js(driver, titulos_procesados, ofertas_encontradas)

        # EL BARRIDO VISUAL YA NO ES NECESARIO SI EL JS FUNCIONA BIEN Y TRAE LINKS
        # Lo quitamos para evitar duplicados y lógica confusa de links

    except Exception as e: print(f"❌ Error: {e}")
    finally: driver.quit()
    
    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
        json.dump(ofertas_encontradas, f, ensure_ascii=False, indent=4)
    return ofertas_encontradas

if __name__ == "__main__":
    datos = obtener_ofertas_carrefour()
    print(f"\n💾 Guardado Carrefour: {len(datos)} ofertas.")