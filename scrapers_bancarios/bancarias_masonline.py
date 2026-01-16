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
NOMBRE_ARCHIVO = "promos_bancarias_masonline.json"
BASE_URL = "https://www.masonline.com.ar/promociones-bancarias?dia="

DIAS_SEMANA = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]

def normalizar_texto(texto):
    if not texto: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')

def es_valida_online(card_element):
    """Verifica si la tarjeta tiene los logos de 'Express' o 'Online'."""
    try:
        iconos = card_element.find_elements(By.CSS_SELECTOR, "div[class*='logoIcon']")
        for icono in iconos:
            style_attr = icono.get_attribute("style") or ""
            if "logo_express" in style_attr or "logo_com" in style_attr:
                return True
        return False
    except:
        return False

def detectar_banco_detallado(src_img, texto_completo, titulo_tarjeta):
    """
    Detector ajustado para Mercado Pago y falsos positivos.
    """
    src = str(src_img).lower()
    txt_legal = str(texto_completo).lower()
    titulo = str(titulo_tarjeta).lower()
    
    data_all = src + " " + txt_legal + " " + titulo
    
    # 1. BLOQUEOS
    if "anses" in data_all: return "IGNORAR"

    # 2. MERCADO PAGO (Mejorado)
    # Por imagen (nombres variados)
    if "mercado pago" in src or "mercadopago" in src: return "Mercado Pago"
    if "logo mercado pago" in src: return "Mercado Pago"
    # Por título
    if "mercado pago" in titulo: return "Mercado Pago"
    # Por legal (SOLO FRASES POSITIVAS)
    if "procesamiento de pagos de mercado pago" in txt_legal: return "Mercado Pago"
    if "qr con la app de mercado pago" in txt_legal: return "Mercado Pago"

    # 3. OTROS ESPECÍFICOS
    if "todas_lastarjetas" in src: return "Todas las Tarjetas (Débito)"
    if "cuenta dni" in data_all: return "Cuenta DNI"
    if "naranja" in data_all: return "Tarjeta Naranja"
    if "club" in titulo or "masclub" in src or "club masonline" in txt_legal: return "Club MasOnline"
    if "prex" in data_all: return "Tarjeta Prex"
    if "yoy" in data_all: return "YOY (ICBC)"

    # 4. MODO + BANCO
    es_modo = "modo" in src or "modo" in titulo
    if not es_modo and "modo" in txt_legal and "pagando con modo" in txt_legal:
        es_modo = True

    banco_detectado = None
    if "nacion" in data_all or "bna" in data_all: banco_detectado = "Banco Nación"
    elif "credicoop" in data_all: banco_detectado = "Banco Credicoop"
    # Anti-Cerveza Patagonia
    elif "patagonia" in src or "banco patagonia" in txt_legal: banco_detectado = "Banco Patagonia"
    elif "hipotecario" in data_all: banco_detectado = "Banco Hipotecario"
    elif "galicia" in data_all: banco_detectado = "Banco Galicia"
    elif "santander" in data_all: banco_detectado = "Banco Santander"
    elif "macro" in data_all: banco_detectado = "Banco Macro"
    elif "bbva" in data_all or "frances" in data_all: banco_detectado = "Banco BBVA"
    elif "icbc" in data_all: banco_detectado = "ICBC"
    elif "ciudad" in data_all: banco_detectado = "Banco Ciudad"
    elif "supervielle" in data_all or "superville" in data_all: banco_detectado = "Banco Supervielle"
    elif "columbia" in data_all: banco_detectado = "Banco Columbia"
    elif "comafi" in data_all: banco_detectado = "Banco Comafi"
    elif "cencosud" in data_all: banco_detectado = "Tarjeta Cencosud"

    if es_modo and banco_detectado: return f"{banco_detectado} + MODO"
    if banco_detectado: return banco_detectado
    if es_modo: return "Billetera MODO"
    
    # Fallback final
    if "club" in txt_legal and "masonline" in txt_legal: return "Club MasOnline"

    return "Varios / Otros"

def scrape_bancarias_masonline():
    options = Options()
    options.add_argument('--log-level=3')
    options.add_argument('--disable-gpu')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    datos_crudos = []

    try:
        print("--- INICIANDO SCRAPER MASONLINE (V7 - MP FIX) ---")
        
        for dia in DIAS_SEMANA:
            url_dia = f"{BASE_URL}{dia}"
            # print(f"\n> Analizando día: {dia.upper()}")
            
            driver.get(url_dia)
            time.sleep(2)
            for _ in range(3):
                driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(0.5)
            
            try:
                tarjetas = driver.find_elements(By.CSS_SELECTOR, "div[class*='cardBox']")
            except: continue

            for card in tarjetas:
                try:
                    if not es_valida_online(card): continue

                    try:
                        pct_elem = card.find_element(By.CSS_SELECTOR, "span[class*='ColLeftPercentage']")
                        val_num = int(pct_elem.text.strip())
                    except: continue
                    
                    if val_num < 5: continue 

                    texto_completo = card.get_attribute("textContent").strip()
                    src_img = ""
                    titulo_promo = ""
                    
                    try:
                        img_elem = card.find_element(By.CSS_SELECTOR, "img[class*='ImageCard']")
                        src_img = img_elem.get_attribute("src")
                    except: pass
                    
                    try:
                        titulo_promo = card.find_element(By.CSS_SELECTOR, "span[class*='ColRightTittle']").text
                    except: pass
                    
                    banco = detectar_banco_detallado(src_img, texto_completo, titulo_promo)
                    
                    if banco == "IGNORAR": continue

                    # Tope
                    tope = "Sin tope"
                    tope_encontrado = False
                    try:
                        right_text = card.find_element(By.CSS_SELECTOR, "span[class*='ColRightText']").text
                        if "tope" in right_text.lower():
                            tope = right_text
                            tope_encontrado = True
                    except: pass
                    
                    if not tope_encontrado:
                        if "sin tope" in titulo_promo.lower():
                            tope = "Sin tope"

                    print(f"  [OK] {banco} | {val_num}%")
                    
                    datos_crudos.append({
                        "dia": dia,
                        "banco": banco,
                        "val_num": val_num,
                        "tope": tope,
                        "link": url_dia
                    })

                except Exception: continue
        
        print(f"\n📊 Extracción válida: {len(datos_crudos)} registros.")

        grupos = defaultdict(list)
        for d in datos_crudos:
            clave = (d['dia'], d['banco'])
            grupos[clave].append(d)

        promos_finales = []

        for (dia, banco), lista in grupos.items():
            porcentajes = sorted(list(set(item['val_num'] for item in lista)))
            if not porcentajes: continue

            if len(porcentajes) > 1:
                txt_descuento = f"{porcentajes[0]}% al {porcentajes[-1]}%"
            else:
                txt_descuento = f"{porcentajes[0]}%"

            if len(lista) > 1:
                ver_legales = True
                tope_final = None
            else:
                ver_legales = False
                tope_final = lista[0]['tope']

            promo = {
                "supermercado": "MasOnline",
                "dia": dia,
                "banco": banco,
                "descuento": txt_descuento,
                "tope": tope_final,
                "ver_legales": ver_legales,
                "link": lista[0]['link'],
                "categoria": "General"
            }
            promos_finales.append(promo)

    except Exception as e_main:
        print(f"❌ Error crítico: {e_main}")

    finally:
        driver.quit()
        
        if promos_finales:
            dia_orden = {d: i for i, d in enumerate(DIAS_SEMANA)}
            promos_finales.sort(key=lambda x: (dia_orden.get(x['dia'], 99), x['banco']))
            
            ruta_absoluta = os.path.abspath(NOMBRE_ARCHIVO)
            with open(ruta_absoluta, "w", encoding="utf-8") as f:
                json.dump(promos_finales, f, ensure_ascii=False, indent=4)
            print("="*60)
            print(f"🎉 FINALIZADO: {len(promos_finales)} promociones en {NOMBRE_ARCHIVO}")
            print("="*60)

if __name__ == "__main__":
    scrape_bancarias_masonline()