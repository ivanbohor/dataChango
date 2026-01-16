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
NOMBRE_ARCHIVO = "promos_bancarias_jumbo.json"
BASE_URL = "https://www.jumbo.com.ar/descuentos-del-dia?type=por-dia&day="

MAPA_DIAS = {
    1: "lunes", 2: "martes", 3: "miercoles", 4: "jueves", 5: "viernes", 6: "sabado", 7: "domingo"
}

def normalizar_texto(texto):
    if not texto: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')

def es_promo_online(texto_completo, banco_detectado):
    """
    Filtro estricto usando REGEX.
    """
    txt = normalizar_texto(texto_completo)
    
    # 1. KILL PHRASES (Descarte inmediato)
    if re.search(r'no\s+valido.*en\s+autopagos', txt): return False, "Dice 'no valido en autopagos'"
    if re.search(r'ni\s+pagos\s+online', txt): return False, "Dice 'ni pagos online'"
    if re.search(r'no\s+valido.*online', txt): return False, "Dice 'no valido ... online'"
    if re.search(r'solo\s+.*presencial', txt): return False, "Dice 'solo presencial'"
    if re.search(r'exclusivo\s+.*tienda', txt): return False, "Dice 'exclusivo tienda'"

    # 2. LOGICA MODO (Por defecto suele ser presencial en Jumbo)
    if banco_detectado == "Billetera MODO":
        if re.search(r'valido\s+.*online', txt):
            return True, "MODO (Explicitamente Online)"
        else:
            # Si no dice explícitamente online, MODO en Jumbo se descarta
            return False, "MODO (Por defecto Offline en Jumbo)"

    # 3. VALIDACIÓN POSITIVA
    if "online" in txt or "web" in txt or "digital" in txt or "jumbo.com.ar" in txt:
        return True, "OK (Dice Online/Web)"
    
    # 4. ANTE LA DUDA
    if "local" in txt or "sucursal" in txt:
        return False, "Dice Local/Sucursal sin Web"
        
    return True, "OK (Implícito)"

def detectar_banco_estricto(src_img, texto_completo):
    src = str(src_img).lower() if src_img else ""
    txt = str(texto_completo).lower()
    
    # --- NIVEL 1: IMAGEN (Prioridad Absoluta) ---
    
    # Correction: Jumbo a veces escribe mal "superville" en la imagen
    if "supervielle" in src or "superville" in src: return "Banco Supervielle"
    
    if "clarin" in src or "365" in src: return "Clarín 365"
    if "patagonia" in src: return "Banco Patagonia"
    if "tarjetasol" in src: return "Tarjeta Sol"
    if "amex" in src or "american" in src: return "American Express"
    if "naranja" in src: return "Tarjeta Naranja"
    if "cencosud" in src or "cencopay" in src: return "Tarjeta Cencosud"
    if "modo" in src: return "Billetera MODO"
    if "mercadopago" in src: return "Mercado Pago"
    if "personal" in src: return "Personal Pay"
    
    # Bancos tradicionales
    if "galicia" in src: return "Banco Galicia"
    if "santander" in src: return "Banco Santander"
    if "nacion" in src: return "Banco Nación"
    if "macro" in src: return "Banco Macro"
    if "bbva" in src or "frances" in src: return "Banco BBVA"
    if "icbc" in src: return "ICBC"
    if "ciudad" in src: return "Banco Ciudad"
    if "hipotecario" in src: return "Banco Hipotecario"
    if "comafi" in src: return "Banco Comafi"
    if "cordoba" in src: return "Banco Córdoba"
    if "columbia" in src: return "Banco Columbia"
    
    # --- NIVEL 2: TEXTO (Solo si la imagen falló) ---
    
    if "supervielle" in txt: return "Banco Supervielle"
    if ("clarin" in txt or "365" in txt): return "Clarín 365"
    if "tarjeta sol" in txt: return "Tarjeta Sol"
    if "american express" in txt: return "American Express"
    
    # Lógica Anti-Excepciones para MODO
    if "modo" in txt and "pagando con modo" in txt:
        if "excepto" not in txt and "excepcion" not in txt:
            return "Billetera MODO"

    if "galicia" in txt: return "Banco Galicia"
    if "santander" in txt: return "Banco Santander"
    if "nacion" in txt: return "Banco Nación"
    
    if "cencosud" in txt or "cencopay" in txt: return "Tarjeta Cencosud"
    
    return "Varios / Otros"

def scrape_bancarias_jumbo():
    options = Options()
    options.add_argument('--log-level=3')
    options.add_argument('--disable-gpu')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    datos_crudos = []

    try:
        print("--- INICIANDO SCRAPER JUMBO (V5 FINAL) ---")
        
        for num_dia, nombre_dia in MAPA_DIAS.items():
            url_dia = f"{BASE_URL}{num_dia}"
            # print(f"\n> {nombre_dia.upper()} -------------------")
            
            driver.get(url_dia)
            time.sleep(1.5)
            
            for _ in range(4):
                driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(0.5)
            
            try:
                tarjetas = driver.find_elements(By.CSS_SELECTOR, "ul[class*='jumboargentinaio-store-theme'] > li")
            except:
                continue

            for i, card in enumerate(tarjetas):
                try:
                    texto_full = card.get_attribute("textContent").strip()
                    texto_debug = texto_full[:30] + "..."

                    # 1. FILTRO %
                    if "%" not in texto_full:
                        continue
                    
                    # --- PRE-EXTRACCIÓN ---
                    src_img = ""
                    try:
                        img_elem = card.find_element(By.TAG_NAME, "img")
                        src_img = img_elem.get_attribute("src")
                    except: pass
                    
                    # Detectamos Banco (Con corrección Superville)
                    banco = detectar_banco_estricto(src_img, texto_full)

                    # 2. FILTRO ONLINE (Pasamos el banco detectado)
                    es_valida, razon = es_promo_online(texto_full, banco)
                    
                    if not es_valida:
                        continue

                    # Descuento
                    match_pct = re.search(r'(\d+)\s*%', texto_full)
                    val_num = int(match_pct.group(1)) if match_pct else 0
                    
                    # Tope
                    tope = "Sin tope"
                    match_tope = re.search(r'tope.*?(\$[\d\.]+)', texto_full.lower())
                    if match_tope:
                        tope = match_tope.group(1)
                    
                    print(f"  [OK] {banco} | {val_num}%")
                    
                    datos_crudos.append({
                        "dia": nombre_dia,
                        "banco": banco,
                        "val_num": val_num,
                        "tope": tope,
                        "link": url_dia
                    })

                except Exception:
                    continue
        
        print(f"\n📊 Extracción válida: {len(datos_crudos)} registros.")

        # --- FASE 2: AGRUPAMIENTO ---
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
                "supermercado": "Jumbo",
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
            promos_finales.sort(key=lambda x: (x['dia'], x['banco']))
            ruta_absoluta = os.path.abspath(NOMBRE_ARCHIVO)
            with open(ruta_absoluta, "w", encoding="utf-8") as f:
                json.dump(promos_finales, f, ensure_ascii=False, indent=4)
            print("="*60)
            print(f"🎉 FINALIZADO: {len(promos_finales)} promociones en {NOMBRE_ARCHIVO}")
            print("="*60)

if __name__ == "__main__":
    scrape_bancarias_jumbo()