import subprocess
import time
import sys
import os
import shutil
import schedule
from datetime import datetime

# --- CONFIGURACIÓN ---
CARPETA_HISTORIAL = "historial_ofertas"
# Lista de tuplas: (Nombre Visual, Nombre del Script)
SCRAPERS = [
    ("🛒 Carrefour", "scraper_carrefour_general.py"),
    ("🐘 Jumbo", "scraper_jumbo.py"),
    ("🥩 Coto", "scraper_coto.py"),
    ("🌈 MasOnline", "scraper_masonline.py")
]

# --- FUNCIONES DE UTILIDAD ---
def hacer_backups():
    """Guarda una copia de los JSONs actuales antes de sobreescribirlos"""
    if not os.path.exists(CARPETA_HISTORIAL):
        os.makedirs(CARPETA_HISTORIAL)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    
    # Buscamos todos los archivos .json de ofertas
    archivos_ofertas = [f for f in os.listdir() if f.startswith("ofertas_") and f.endswith(".json")]
    
    if not archivos_ofertas:
        print("ℹ️ No hay archivos previos para backupear.")
        return

    print(f"📦 Generando backups ({len(archivos_ofertas)} archivos)...")
    for archivo in archivos_ofertas:
        try:
            nombre_backup = f"{archivo.replace('.json', '')}_{timestamp}.json"
            ruta_origen = archivo
            ruta_destino = os.path.join(CARPETA_HISTORIAL, nombre_backup)
            shutil.copy(ruta_origen, ruta_destino)
        except Exception as e:
            print(f"⚠️ Error backup {archivo}: {e}")

def ejecutar_ciclo_completo():
    """Ejecuta todos los scrapers en orden"""
    print(f"\n" + "═"*60)
    print(f"⏰ INICIANDO CICLO PROGRAMADO: {datetime.now().strftime('%d/%m %H:%M:%S')}")
    print("═"*60 + "\n")

    # 1. Hacemos backup de lo que había antes
    hacer_backups()

    exitos = 0
    start_time = time.time()

    # 2. Corremos los scrapers uno por uno
    for nombre_visual, script_archivo in SCRAPERS:
        print(f"🚀 Ejecutando {nombre_visual}...")
        try:
            # sys.executable asegura que usamos el mismo python del entorno virtual
            subprocess.run([sys.executable, script_archivo], check=True)
            print(f"✅ {nombre_visual} OK.")
            exitos += 1
        except subprocess.CalledProcessError:
            print(f"❌ {nombre_visual} FALLÓ. Continuando con el siguiente...")
        except FileNotFoundError:
            print(f"❌ Archivo no encontrado: {script_archivo}")
        except Exception as e:
            print(f"❌ Error inesperado en {nombre_visual}: {e}")
        
        time.sleep(2) # Pequeña pausa entre scrapers

    tiempo_total = (time.time() - start_time) / 60
    print(f"\n🏁 CICLO TERMINADO en {tiempo_total:.1f} minutos.")
    print(f"📊 Resultado: {exitos}/{len(SCRAPERS)} scrapers exitosos.")

def main():
    print("🤖 SISTEMA DE INTELIGENCIA DE MERCADO - MODO CRONOGRAMA")
    print("🕒 Horarios de Ejecución:")
    print("   - 09:00 HS (Apertura)")
    print("   - 14:30 HS (Tarde)")
    print("   - 20:30 HS (Noche)")
    print("   - 00:30 HS (Cierre)")
    print("---------------------------------------------------------------")

    # 1. Ejecución inmediata al abrir (para verificar que todo ande)
    print("⚡ Ejecutando vuelta inicial de comprobación...")
    ejecutar_ciclo_completo()

    # 2. Programación de Horarios Exactos
    schedule.every().day.at("09:00").do(ejecutar_ciclo_completo)
    schedule.every().day.at("14:30").do(ejecutar_ciclo_completo)
    schedule.every().day.at("20:30").do(ejecutar_ciclo_completo)
    schedule.every().day.at("00:30").do(ejecutar_ciclo_completo)

    print("\n⏳ El sistema está en espera activa. No cierres esta ventana.")
    
    # Bucle infinito de revisión
    while True:
        schedule.run_pending()
        time.sleep(30) # Revisa el reloj cada 30 segundos

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Sistema detenido manualmente.")