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

print(f">>> 🥩 Iniciando Scraper {NOMBRE_SUPER} (V16: Limpieza de Títulos + Anti-Bancos)...")

if os.path.exists(ARCHIVO_SALIDA): os.remove(ARCHIVO_SALIDA)

reader = easyocr.Reader(['es'], gpu=False) 

# ==============================================================================
#  🧠 CEREBRO INTELIGENTE (Actualizado con Pescadería)
# ==============================================================================
class CategorizadorInteligente:
    def __init__(self):
        self.reglas = {
            "🥩 Carnicería": ["carne", "asado", "vacio", "pollo", "milanesa", "hamburguesa", "bife", "nalga", "picada", "peceto", "cuadril", "cerdo", "matambre", "paty", "novillo", "vacuno", "parrillada", "achuras", "pescaderia", "pescado", "marisco", "fillet", "merluza", "calamar"],
            "🍷 Bebidas": ["vino", "cerveza", "gaseosa", "bebida", "fernet", "aperitivo", "jugo", "agua", "soda", "sidra", "malbec", "alcohol", "licor", "champagne", "espumante"],
            "🥛 Lácteos": ["lacteo", "leche", "queso", "yogur", "manteca", "crema", "postre", "serenisima", "sancor", "finlandia", "danette", "actimel"],
            "🧹 Limpieza": ["limpieza", "papel higienico", "rollo", "cocina", "jabon", "detergente", "lavandina", "suavizante", "elite", "cif", "magistral", "ayudin"],
            "💊 Farmacia": ["farmacia", "shampoo", "acondicionador", "desodorante", "corporal", "dove", "colgate", "pasta dental", "jabon tocador", "pantene", "nivea", "huggies", "babysec", "pampers", "pañal"],
            "🍝 Almacén": ["almacen", "fideo", "arroz", "aceite", "cafe", "yerba", "galletita", "chocolate", "nestle", "dulce", "pan", "budin", "harina", "pure", "mayonesa", "aderezo", "azucar", "galletitas", "mate", "te", "cafe"],
            "📺 Electro": ["tv", "celular", "aire", "heladera", "notebook", "smart", "tecnologia", "electro", "lavarropas", "cocina", "horno", "pequeños", "audio", "samsung", "motorola", "rodado", "bici"],
            "🧸 Juguetería": ["juguete", "pileta", "inflable", "juego"],
            "🏠 Hogar": ["bazar", "hogar", "deco", "cama", "toalla", "sabana", "colchon", "mueble", "vaso", "plato", "termo", "olla", "sarten"], 
            # Bancos están aquí para ser detectados y luego filtrados
            "💳 Bancarias": ["banco", "tarjeta", "cencosud", "modo", "galicia", "santander", "ahorro", "promocion bancaria", "bna", "nacion", "comunidad", "hsbc", "icbc", "macro", "supervielle", "ciudad", "visa", "mastercard"]
        }

    def _normalizar(self, texto):
        if not texto: return ""
        return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')

    def inferir(self, texto_completo):
        texto_norm = self._normalizar(texto_completo)
        for categoria, keywords in self.reglas.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'(?:s|es)?\b', texto_norm):
                    return categoria
        if "mascotas" in texto_norm: return "🐶 Mascotas"
        return "⚡ Varios"

brain = CategorizadorInteligente()

# --- DICCIONARIO DE TRADUCCIÓN DE NOMBRES DE ARCHIVO COTO ---
# Esto arregla los títulos rotos
MAPEO_FILENAMES = {
    "clases": "Pan Dulce y Budines", # Tu corrección específica
    "pescaderia": "Pescadería",
    "jugueteria": "Juguetería",
    "vinos": "Vinos Seleccionados",
    "rodados": "Rodados y Bicicletas",
    "electro": "Electrodomésticos",
    "bazar": "Bazar y Hogar",
    "feria": "Feria de Frescos",
    "textil": "Textil y Ropa",
    "salon": "Almacén y Bebidas", # Genérico para "salon"
    "mix": "Ofertas Varias"
}

# --- VALIDACIÓN ---
def es_oferta_valida(texto, src=""):
    # Si la URL dice explícitamente ofertas, confiamos ciegamente
    if "/ofertas/" in src: return True

    t = texto.lower()
    if any(x in t for x in ["horarios", "sucursales", "copyright", "ver más", "retira", "beneficio", "envios", "ayuda", "pedidos"]): return False

    tiene_precio = bool(re.search(r'\d{1,3}[.,]\d{3}', t))
    tiene_senal = any(s in t for s in ["%", "off", "2x1", "3x2", "4x2", "2da", "cuotas", "bazar", "banco", "tarjeta", "precio especial", "oferta", "descuento", "llevando"]) 
    
    return tiene_precio or tiene_senal

# --- LIMPIEZA INTELIGENTE ---
def generar_titulo_bonito(texto_ocr, src):
    t = texto_ocr.replace("\n", " ").strip()
    nombre_archivo = src.split("/")[-1].lower()
    
    # 1. TRADUCCIÓN POR NOMBRE DE ARCHIVO (Prioridad para corregir errores de Coto)
    producto_detectado = "Varios"
    for clave, valor in MAPEO_FILENAMES.items():
        if clave in nombre_archivo:
            producto_detectado = valor
            break
    
    # Si no matcheó nada en el archivo, intentamos buscar en el OCR
    if producto_detectado == "Varios":
        if "pescaderia" in t.lower(): producto_detectado = "Pescadería"
        elif "juguete" in t.lower(): producto_detectado = "Juguetería"
    
    # 2. DETECTAR TIPO DE OFERTA (Prefijo)
    prefijo = "Oferta"
    match_nxn = re.search(r'(\d+[xX]\d+)', t)
    match_desc = re.search(r'(\d+)%', t)
    match_cuotas = re.search(r'\b(\d{1,2})\s*(?:CUO|CTA|PAGOS)', t, re.IGNORECASE)
    
    # Prioridad en el prefijo
    if "3x2" in nombre_archivo: prefijo = "3x2" # A veces el nombre lo dice
    elif "2x1" in nombre_archivo: prefijo = "2x1"
    elif "50" in nombre_archivo: prefijo = "50% Off" # Caso 50salon
    elif match_nxn: prefijo = match_nxn.group(1).lower()
    elif match_desc: prefijo = f"{match_desc.group(1)}% Off"
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
        
        # Análisis combinado: Texto OCR + Nombre de archivo (útil para Coto)
        texto_analisis = f"{texto_ocr} {src}".strip()
        
        if not es_oferta_valida(texto_analisis, src): return
        
        categoria = brain.inferir(texto_analisis)
        
        # --- FILTRO ANTI-BANCOS ---
        # Si detectamos que es oferta bancaria, LA SALTAMOS (no se guarda)
        if categoria == "💳 Bancarias":
            # print(f"      [INFO] Oferta bancaria ignorada: {src.split('/')[-1]}")
            return 
        # --------------------------

        titulo = generar_titulo_bonito(texto_ocr, src)

        # Corrección de categoría si el título es explícito
        if "Pescadería" in titulo: categoria = "🥩 Carnicería" # O crear categoría Pescadería
        if "Juguetería" in titulo: categoria = "🧸 Juguetería"
        if "Rodados" in titulo: categoria = "📺 Electro" # O Deportes/Aire libre

        if titulo not in titulos_procesados:
            oferta = {
                "supermercado": NOMBRE_SUPER,
                "titulo": titulo,
                "categoria": [categoria],
                "link": URL_SUPER,
                "imagen": src,
                "fecha": time.strftime("%Y-%m-%d")
            }
            ofertas_encontradas.append(oferta)
            titulos_procesados.add(titulo)
            print(f"      🥩 [{categoria}] {titulo}")

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
        
        # Scroll hasta el fondo para cargar lazy loading (Pescadería suele estar abajo)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);") # Volver arriba por si acaso
        time.sleep(1)

        todas_imgs = driver.find_elements(By.TAG_NAME, "img")
        print(f"      -> Total imágenes en DOM: {len(todas_imgs)}")
        
        for img in todas_imgs:
            try:
                src = img.get_attribute("src")
                if not src: 
                    srcset = img.get_attribute("srcset")
                    if srcset: src = srcset.split(" ")[0]

                # Filtro: Solo imágenes que contengan "/ofertas/" en su ruta
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