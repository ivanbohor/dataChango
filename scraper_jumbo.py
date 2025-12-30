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

print(f">>> 🐘 Iniciando Scraper {NOMBRE_SUPER} (V13: Fix Categorización Inteligente)...")

if os.path.exists(ARCHIVO_SALIDA): os.remove(ARCHIVO_SALIDA)

# Inicializamos OCR
reader = easyocr.Reader(['es'], gpu=False) 

# ==============================================================================
#  🧠 NUEVO CEREBRO DE CATEGORIZACIÓN
# ==============================================================================
# ==============================================================================
#  🧠 NUEVO CEREBRO DE CATEGORIZACIÓN (V13.1 - Fix Plurales)
# ==============================================================================
class CategorizadorInteligente:
    def __init__(self):
        self.reglas = {
            "🍷 Bebidas": [
                "vino", "cerveza", "gaseosa", "bebida", "fernet", "aperitivo", 
                "jugo", "agua", "soda", "champagne", "sidra", "malbec", "cabernet", 
                "cola", "sprite", "licor", "tintos", "blancos"
            ],
            "🥛 Lácteos": [
                "lacteo", "leche", "queso", "yogur", "manteca", "crema", "postre", 
                "serenisima", "sancor", "finlandia", "danette", "actimel", "casancrem"
            ],
            "🧹 Limpieza": [
                "limpieza", "papel higienico", "rollo", "cocina", "jabon", "detergente", 
                "lavandina", "suavizante", "elite", "cif", "magistral", "ayudin", 
                "trapo", "escoba", "ariel", "skip", "vela"
            ],
            "💊 Farmacia": [
                "farmacia", "shampoo", "acondicionador", "desodorante", "corporal", 
                "dove", "colgate", "pasta dental", "jabon tocador", "pantene", "nivea", 
                "rexona", "ax3", "cuidado personal", "huggies", "babysec", "pampers", 
                "pañal", "toallitas"
            ],
            "🍝 Almacén": [
                "almacen", "fideo", "arroz", "aceite", "cafe", "yerba", "galletita", 
                "chocolate", "nestle", "dulce", "pan", "budin", "harina", "pure", 
                "salsa", "mayonesa", "ketchup", "aderezo", "atun", "nescafe", "dolca", 
                "mermelada", "azucar"
            ],
            "🥩 Carnicería": [
                "carne", "carniceria", "pollo", "milanesa", "hamburguesa", "asado", 
                "bife", "pavita", "cerdo", "vacuno", "nalga", "picada", "paty", 
                "granjas", "patita"
            ],
            "📺 Electro": [
                "tv", "celular", "aire", "heladera", "notebook", "smart", 
                "tecnologia", "electro", "lavarropas", "cocina", "horno", 
                "pequeños", "audio", "auricular"
            ],
            "🧸 Juguetería": ["juguete", "pileta", "inflable", "juego", "muñeca"],
            "🥦 Frescos": ["fruta", "verdura", "papa", "cebolla", "tomate", "lechuga", "banana", "manzana"],
            "🏠 Hogar": ["hogar", "deco", "bazar", "cama", "sabana", "toalla"]
        }

    def _normalizar(self, texto):
        if not texto: return ""
        # Normaliza tildes (Lácteos -> lacteos) y pasa a minusculas
        return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')

    def inferir(self, texto_completo):
        """Analiza título + OCR + tags y decide la categoría final."""
        texto_norm = self._normalizar(texto_completo)
        
        # 1. Búsqueda inteligente (Soporta plurales automáticos)
        for categoria, keywords in self.reglas.items():
            for kw in keywords:
                # El regex mágico:
                # \b = inicio de palabra
                # re.escape(kw) = la palabra clave (ej: "vino")
                # (?:s|es)? = acepta opcionalmente "s" o "es" al final (vinos, licores)
                # \b = fin de palabra
                patron = r'\b' + re.escape(kw) + r'(?:s|es)?\b'
                
                if re.search(patron, texto_norm):
                    return categoria
        
        # 2. Casos de Marcas Específicas (Fallback fuerte)
        if "nestle" in texto_norm: return "🍝 Almacén"
        if "elite" in texto_norm: return "🧹 Limpieza"
        if "cencosud" in texto_norm or "tarjeta" in texto_norm: return "💳 Bancarias"

        # 3. Default
        return "⚡ Varios"

# Instanciamos el cerebro
brain = CategorizadorInteligente()

# ==============================================================================
#  CONFIGURACIÓN VIEJA (Solo para embellecer títulos, ya no define categoría)
# ==============================================================================
DB_NOMBRES_BONITOS = {
    "pavita": "Pavita", "pavo": "Pavo", "bondiola": "Bondiola", "cerdo": "Carne de Cerdo",
    "carne": "Carne Vacuna", "asado": "Asado", "vacio": "Vacío", "pollo": "Pollo",
    "bife": "Bifes", "nalga": "Corte Nalga", "matambre": "Matambre", "casancrem": "Queso Crema",
    "queso": "Quesos", "leche": "Leche", "yogur": "Yogures", "manteca": "Manteca",
    "pan dulce": "Pan Dulce", "budin": "Budines", "almacen": "Almacén", "fideo": "Pastas",
    "arroz": "Arroz", "aceite": "Aceite", "colgate": "Cuidado Oral", "dove": "Cuidado Personal",
    "carefree": "Protección Femenina", "jabon": "Jabón", "shampoo": "Shampoo",
    "aire": "Aires Acondicionados", "tv": "Smart TV", "heladera": "Heladeras",
    "celular": "Celulares", "vino": "Vinos", "cerveza": "Cervezas", "juguete": "Juguetería",
    "pileta": "Piletas", "limpieza": "Limpieza"
}

# --- 2. FILTROS Y VALIDACIÓN ---
def es_oferta_valida(texto):
    t = texto.lower()
    if any(x in t for x in ["horarios", "sucursales", "copyright", "ver más", "retira", "beneficio"]): return False

    # Validaciones de precio y señales de oferta
    tiene_formato_precio = bool(re.search(r'\d{1,3}[.,]\d{3}', t))
    tiene_pesos = "$" in t
    tiene_senal = any(s in t for s in ["%", "off", "2x1", "3x2", "4x2", "2da", "cuotas"])
    
    return tiene_formato_precio or tiene_pesos or tiene_senal

def obtener_link_especifico(elemento_img):
    try:
        padre = elemento_img.find_element(By.XPATH, "./ancestor::a")
        link = padre.get_attribute("href")
        if link: return link
    except: pass
    return URL_SUPER

# --- 3. LIMPIEZA Y FORMATEO ---
def limpiar_texto_ocr(texto_sucio, texto_alt=""):
    texto_combinado = texto_sucio
    if texto_alt and texto_alt.lower() not in texto_sucio.lower():
        texto_combinado += " " + texto_alt

    t = texto_combinado.replace("\n", " ").strip()
    t = t.replace("Ax2", "4x2").replace("ax2", "4x2").replace("Ax1", "2x1")
    t = t.replace("18CUOTAS", "18 Cuotas").replace("12CUOTAS", "12 Cuotas")
    
    prefijo = "Oferta"
    match_nxn = re.search(r'(\d+[xX]\d+)', t)            
    match_cuotas = re.search(r'(\d+)\s*(CUO|CTA|CSI)', t, re.IGNORECASE) 
    match_desc = re.search(r'(\d+)%', t)
    match_precio = re.search(r'(\$\s?[\d\.,]+)', t)
    
    if not match_precio:
        match_precio_raw = re.search(r'\b(\d{1,3}[.,]\d{3})\b', t)
    else:
        match_precio_raw = None

    if match_nxn: prefijo = match_nxn.group(1).lower().replace("x", "x")
    elif match_cuotas: prefijo = f"{match_cuotas.group(1)} Cuotas S/Int"
    elif match_desc: 
        num = int(match_desc.group(1))
        if num > 100:
            if str(num).startswith("2"): prefijo = f"2do al {str(num)[1:]}%"
            else: prefijo = f"{num % 100}% Off"
        else:
            if "2do" in t.lower() or "segunda" in t.lower(): prefijo = f"2do al {num}%"
            else: prefijo = f"{num}% Off"
    elif match_precio: prefijo = f"A {match_precio.group(1)}"
    elif match_precio_raw: prefijo = f"A ${match_precio_raw.group(1)}"
    
    if "hasta" in t.lower() and "50" in t: prefijo = "Hasta 50% Off"
    
    productos = ""
    # Usamos ALT text limpio si es útil
    if texto_alt and len(texto_alt) > 3 and "oferta" not in texto_alt.lower(): 
        words = texto_alt.split()
        unique_words = []
        for w in words:
            if w not in unique_words: unique_words.append(w)
        productos = " ".join(unique_words).title()
    
    # Si no hay producto claro, buscamos en DB_NOMBRES_BONITOS para formatear lindo
    if not productos:
        for k, v in DB_NOMBRES_BONITOS.items():
            if k in t.lower(): 
                productos = v
                break
                
    if productos: return f"{prefijo} en {productos}"
    return f"{prefijo} en Varios"

def procesar_oferta(elemento_img, src, texto_alt, titulos_procesados, ofertas_encontradas):
    try:
        link_real = obtener_link_especifico(elemento_img)
        headers = {'User-Agent': 'Mozilla/5.0'}
        try: resp = requests.get(src, headers=headers, timeout=3)
        except: return
        
        if resp.status_code != 200: return
        res_ocr = reader.readtext(resp.content, detail=0, paragraph=True)
        texto_ocr = " ".join(res_ocr)
        
        # Texto completo para analizar (OCR + ALT)
        texto_analisis = f"{texto_ocr} {texto_alt}".strip()
        
        if not es_oferta_valida(texto_analisis): return
        
        # --- AQUÍ USAMOS EL NUEVO CEREBRO ---
        categoria_detectada = brain.inferir(texto_analisis)
        # ------------------------------------

        titulo_bonito = limpiar_texto_ocr(texto_ocr, texto_alt)
        
        if titulo_bonito not in titulos_procesados:
            oferta = {
                "supermercado": NOMBRE_SUPER,
                "titulo": titulo_bonito,
                "descripcion": texto_ocr + " " + texto_alt,
                "categoria": [categoria_detectada], # Formato lista para mantener compatibilidad
                "link": link_real,
                "imagen": src,
                "fecha": time.strftime("%Y-%m-%d")
            }
            ofertas_encontradas.append(oferta)
            titulos_procesados.add(titulo_bonito)
            
            # Imprimimos con la categoría nueva
            print(f"      🐘 [{categoria_detectada}] {titulo_bonito}")

    except Exception as e: pass

# --- 4. SCRAPER PRINCIPAL ---
def obtener_ofertas_jumbo():
    opts = Options()
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--log-level=3")
    # opts.add_argument("--headless") # Descomentar si quieres que no se abra la ventana
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
        paso_scroll = 600 # Un poco más rápido
        
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
                        contexto = f"{alt_text} {title_text}"
                        
                        if src and "http" in src and src not in src_procesados:
                            if "icon" in src or "logo" in src: continue
                            src_procesados.add(src)
                            procesar_oferta(img, src, contexto, titulos_procesados, ofertas_encontradas)
                            
                except: continue

    except Exception as e: print(f"❌ Error: {e}")
    finally: driver.quit()
    return ofertas_encontradas

if __name__ == "__main__":
    datos = obtener_ofertas_jumbo()
    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
    print(f"\n💾 Guardado Jumbo: {len(datos)} ofertas.")