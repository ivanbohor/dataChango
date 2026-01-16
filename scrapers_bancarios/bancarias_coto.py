import time
import json
import os
import re
import unicodedata
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ---
NOMBRE_ARCHIVO = "promos_bancarias_coto.json"
URL_COTO = "https://www.cotodigital.com.ar/sitios/cdigi/descuentos"

def normalizar_texto(texto):
    if not texto: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')

def interpretar_dias(texto_dia):
    """Convierte texto libre a lista de días normalizados."""
    txt = normalizar_texto(texto_dia)
    todos = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    
    if "lunes a domingo" in txt or "todos los dias" in txt or "diario" in txt:
        return todos
    if "fin de semana" in txt:
        return ["sabado", "domingo"]

    encontrados = []
    for d in todos:
        if d in txt:
            encontrados.append(d)
    return encontrados

def detectar_banco(src_img, texto_completo):
    """
    Detecta el banco analizando tanto el nombre del archivo de imagen (src)
    como el texto descriptivo de la tarjeta.
    """
    data = (str(src_img) + " " + str(texto_completo)).lower()
    
    # --- BANCOS PROVINCIALES (Grupo Petersen) ---
    if "sanjuan" in data or "san juan" in data: return "Banco San Juan"
    if "entrerios" in data or "entre rios" in data: return "Banco Entre Ríos"
    if "santafe" in data or "santa fe" in data: return "Banco Santa Fe"
    if "santacruz" in data or "santa cruz" in data: return "Banco Santa Cruz"

    # --- TARJETA COTO ---
    if "tci" in data or "nuestra tarjeta" in data: return "Tarjeta Coto"

    # --- BANCOS TRADICIONALES ---
    if "nacion" in data: return "Banco Nación"
    if "macro" in data: return "Banco Macro"
    if "galicia" in data: return "Banco Galicia"
    if "santander" in data: return "Banco Santander"
    if "bbva" in data or "frances" in data: return "Banco BBVA"
    if "icbc" in data: return "ICBC"
    if "ciudad" in data: return "Banco Ciudad"
    if "naranja" in data: return "Tarjeta Naranja"
    if "supervielle" in data: return "Banco Supervielle"
    if "patagonia" in data: return "Banco Patagonia"
    if "columbia" in data: return "Banco Columbia"
    if "comafi" in data: return "Banco Comafi"
    if "hipotecario" in data: return "Banco Hipotecario"
    if "hsbc" in data: return "HSBC"
    if "credicoop" in data: return "Banco Credicoop"
    if "cencosud" in data: return "Tarjeta Cencosud"
    if "mercadopago" in data: return "Mercado Pago"
    if "personal" in data and "pay" in data: return "Personal Pay"
    if "modo" in data: return "Billetera MODO"
    if "comunidad" in data: return "Comunidad Coto"
    
    return "Varios / Otros"

def scrape_bancarias_coto():
    options = Options()
    options.add_argument('--log-level=3')
    options.add_argument('--disable-gpu')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    datos_crudos = []

    try:
        print("--- INICIANDO SCRAPER COTO (FILTRO % Y BANCOS PROVINCIALES) ---")
        driver.get(URL_COTO)
        
        print("📜 Scrolleando para asegurar carga del DOM...")
        for _ in range(5):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(1)
        
        tarjetas = driver.find_elements(By.CSS_SELECTOR, "div.grid-item")
        print(f"🔎 Analizando {len(tarjetas)} tarjetas detectadas...")

        count_raw = 0
        
        for card in tarjetas:
            try:
                # Usamos textContent para leer aunque esté oculto
                texto_full = card.get_attribute("textContent").strip()
                
                # --- FILTRO 1: SOLO DESCUENTOS PORCENTUALES (%) ---
                if "%" not in texto_full:
                    continue

                # --- EXTRACCIÓN ---
                src_img = ""
                try:
                    img_elem = card.find_element(By.TAG_NAME, "img")
                    src_img = img_elem.get_attribute("src")
                except: pass

                # Días
                texto_dias = ""
                try:
                    p_dia = card.find_element(By.CSS_SELECTOR, "p.card-text")
                    texto_dias = p_dia.get_attribute("textContent").strip()
                except: texto_dias = texto_full

                dias_detectados = interpretar_dias(texto_dias)
                if not dias_detectados: dias_detectados = interpretar_dias(texto_full)
                if not dias_detectados: continue

                # Valor numérico del descuento
                match_pct = re.search(r'(\d+)\s*%', texto_full)
                val_num = int(match_pct.group(1)) if match_pct else 0
                
                # Banco (Ahora incluye provinciales y TCI)
                banco = detectar_banco(src_img, texto_full)
                
                # Tope
                tope = "Sin tope"
                match_tope = re.search(r'tope.*?(\$[\d\.]+)', texto_full.lower())
                if match_tope:
                    tope = match_tope.group(1)
                elif "sin tope" in texto_full.lower():
                    tope = "Sin tope"

                # Guardamos la data cruda
                for dia in dias_detectados:
                    datos_crudos.append({
                        "dia": dia,
                        "banco": banco,
                        "val_num": val_num,
                        "tope": tope,
                        "link": URL_COTO
                    })
                    count_raw += 1

            except Exception:
                continue

        print(f"📊 Extracción cruda: {count_raw} registros (filtrados %).")

        # --- FASE 2: AGRUPAMIENTO ---
        print("🔄 Agrupando promociones...")
        
        grupos = defaultdict(list)
        for d in datos_crudos:
            clave = (d['dia'], d['banco'])
            grupos[clave].append(d)

        promos_finales = []

        for (dia, banco), lista in grupos.items():
            porcentajes = sorted(list(set(item['val_num'] for item in lista)))
            
            if not porcentajes: continue

            # Rango de Descuento
            if len(porcentajes) > 1:
                txt_descuento = f"{porcentajes[0]}% al {porcentajes[-1]}%"
            else:
                txt_descuento = f"{porcentajes[0]}%"

            # Tope y Legales
            if len(lista) > 1:
                ver_legales = True
                tope_final = None 
            else:
                ver_legales = False
                tope_final = lista[0]['tope']

            promo = {
                "supermercado": "Coto",
                "dia": dia,
                "banco": banco,
                "descuento": txt_descuento,
                "tope": tope_final,
                "ver_legales": ver_legales,
                "link": URL_COTO,
                "categoria": "General"
            }
            promos_finales.append(promo)

    except Exception as e_main:
        print(f"❌ Error crítico: {e_main}")

    finally:
        driver.quit()
        
        if promos_finales:
            promos_finales.sort(key=lambda x: (x['dia'], x['banco']))
            
            ruta_absoluta = os.path.abspath(NOMBRE_ARCHIVO)
            with open(ruta_absoluta, "w", encoding="utf-8") as f:
                json.dump(promos_finales, f, ensure_ascii=False, indent=4)
            
            print("\n" + "="*60)
            print(f"🎉 FINALIZADO: {len(promos_finales)} promociones consolidadas en {NOMBRE_ARCHIVO}")
            print("="*60)
        else:
            print("⚠️ No se encontraron promociones.")

if __name__ == "__main__":
    scrape_bancarias_coto()