import time
import json
import os
import re
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN GLOBAL ---
NOMBRE_ARCHIVO = "promos_bancarias.json"

def detectar_banco_estricto(titulo_oferta):
    """
    Analiza el TÍTULO para determinar el banco.
    """
    texto = titulo_oferta.lower()
    
    # --- 1. Lógica Específica (Prioridad Alta) ---
    if "club la nacion" in texto or "club la nación" in texto:
        return "Club La Nación"
    
    if "carrefour" in texto:
        if "crédito" in texto or "credito" in texto:
            return "Tarjeta Carrefour Crédito"
        elif "prepaga" in texto:
            return "Tarjeta Carrefour Prepaga"
        else:
            return "Mi Carrefour (Beneficio/App)"

    # --- 2. Bancos Tradicionales ---
    if "frances" in texto or "bbva" in texto: return "Banco BBVA"
    if "galicia" in texto: return "Banco Galicia"
    if "macro" in texto: return "Banco Macro"
    if "santander" in texto: return "Banco Santander"
    if "nacion" in texto or "nación" in texto: return "Banco Nación"
    if "patagonia" in texto: return "Banco Patagonia"
    if "icbc" in texto: return "ICBC"
    if "supervielle" in texto: return "Banco Supervielle"
    if "hipotecario" in texto: return "Banco Hipotecario"
    if "comafi" in texto: return "Banco Comafi"
    if "naranja" in texto: return "Tarjeta Naranja"
    if "columbia" in texto: return "Banco Columbia"
    if "ciudad" in texto: return "Banco Ciudad"
    if "modo" in texto: return "Billetera MODO"
    if "mercado pago" in texto: return "Mercado Pago"
    if "personal pay" in texto: return "Personal Pay"
    
    return "Otros / Varios"

def scrape_promos_bancarias():
    dias_semana = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    nuevas_promos = []

    options = Options()
    options.add_argument('--start-maximized')
    options.add_argument('--log-level=3') 
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        print("--- INICIANDO SCRAPER DE PROMOS BANCARIAS (CARREFOUR) ---")
        
        for dia in dias_semana:
            url_dia = f"https://www.carrefour.com.ar/descuentos-bancarios?filtro=por-dia&dia={dia}&formato=ecommerce"
            print(f"\n> Analizando día: {dia.upper()}")
            
            driver.get(url_dia)

            try:
                wait = WebDriverWait(driver, 10)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='promotionsContainer']")))
                
                driver.execute_script("window.scrollBy(0, 600);")
                time.sleep(2)

                tarjetas = driver.find_elements(By.CSS_SELECTOR, "div[class*='promotionsContainer'] > div")
                
                # --- MEMORIA TEMPORAL ---
                # Estructura: 'Banco': [ {num: 20, tope: '$10.000'}, {num: 15, tope: 'Sin tope'} ]
                bancos_del_dia = defaultdict(list)
                
                # Guardamos un título de referencia
                titulos_referencia = {}

                for tarjeta in tarjetas:
                    try:
                        # 1. Extracción de Título y Porcentaje
                        try:
                            titulo = tarjeta.find_element(By.CSS_SELECTOR, "span[class*='ColRightTittle']").text.strip()
                            raw_num = tarjeta.find_element(By.CSS_SELECTOR, "span[class*='ColLeftPercentage']").text.strip()
                        except: continue
                        
                        # 2. Extracción del TOPE (Nueva lógica)
                        try:
                            # Buscamos el elemento del texto derecho (donde suele estar el tope)
                            tope_element = tarjeta.find_element(By.CSS_SELECTOR, "span[class*='ColRightText']")
                            texto_tope = tope_element.text.strip()
                            
                            if "tope" in texto_tope.lower():
                                # Limpieza: quitar "Tope de devolución:" y dejar solo el monto
                                tope_clean = texto_tope.replace("Tope de devolución:", "").replace("Tope de reintegro:", "").strip()
                            else:
                                tope_clean = "Sin tope"
                        except:
                            tope_clean = "Sin tope"

                        # --- FILTRO ANTI-CUOTAS ---
                        match_num = re.search(r'\d+', raw_num)
                        val_num = int(match_num.group()) if match_num else 0
                        
                        es_cuota = "cuota" in titulo.lower() and "descuento" not in titulo.lower()
                        es_numero_chico = val_num <= 10 and "%" not in raw_num

                        if es_cuota or es_numero_chico:
                            continue

                        # Detección
                        banco = detectar_banco_estricto(titulo)
                        
                        # Guardamos objeto completo en vez de solo numero
                        bancos_del_dia[banco].append({
                            "val_num": val_num,
                            "tope": tope_clean
                        })
                        
                        if banco not in titulos_referencia:
                            titulos_referencia[banco] = titulo

                    except Exception:
                        continue

                # --- PROCESAMIENTO Y AGRUPACIÓN FINAL DEL DÍA ---
                count_dia = 0
                for banco, lista_datos in bancos_del_dia.items():
                    # Extraemos solo los porcentajes para el rango
                    pcts_unicos = sorted(list(set(d["val_num"] for d in lista_datos)))
                    
                    if not pcts_unicos: continue

                    # Lógica de rango de descuento:
                    if len(pcts_unicos) > 1:
                        minimo = pcts_unicos[0]
                        maximo = pcts_unicos[-1]
                        txt_descuento = f"{minimo}% al {maximo}%"
                    else:
                        txt_descuento = f"{pcts_unicos[0]}%"

                    # --- LÓGICA DE VISUALIZACIÓN (TOPE VS LEGALES) ---
                    # Si hay más de una promo para este banco este día -> Ver legales
                    if len(lista_datos) > 1:
                        tope_final = None # No mostramos tope individual
                        ver_legales = True
                    else:
                        # Si es una sola, mostramos su tope específico
                        tope_final = lista_datos[0]["tope"]
                        ver_legales = False

                    promo_consolidada = {
                        "supermercado": "Carrefour",
                        "dia": dia,
                        "banco": banco,
                        "descuento": txt_descuento,
                        "tope": tope_final,          # Nuevo campo
                        "ver_legales": ver_legales,  # Nuevo campo (bool)
                        "detalle": titulos_referencia.get(banco, "Ver legales"),
                        "categoria": "General",
                        "link": url_dia 
                    }
                    
                    nuevas_promos.append(promo_consolidada)
                    count_dia += 1

                print(f"  ✅ {count_dia} bancos procesados (agrupados).")

            except Exception as e:
                print(f"  ⚠️ Error en {dia}: {e}")

    except Exception as e_main:
        print(f"Error crítico: {e_main}")

    finally:
        driver.quit()
        
        if nuevas_promos:
            ruta_absoluta = os.path.abspath(NOMBRE_ARCHIVO)
            with open(ruta_absoluta, "w", encoding="utf-8") as f:
                json.dump(nuevas_promos, f, ensure_ascii=False, indent=4)
            
            print("\n" + "="*60)
            print(f"🎉 BASE DE DATOS ACTUALIZADA: {NOMBRE_ARCHIVO}")
            print(f"📊 Total registros consolidados: {len(nuevas_promos)}")
            print("="*60)
        else:
            print("❌ No se obtuvieron datos.")

if __name__ == "__main__":
    scrape_promos_bancarias()