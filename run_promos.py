import subprocess
import sys
import time
import os

# Configuración: Lista de scripts a ejecutar dentro de la carpeta
SCRIPTS = [
    "bancarias_coto.py",
    "bancarias_jumbo.py",
    "bancarias_masonline.py",
    "bancarias_carrefour.py"
]

CARPETA = "scrapers_bancarios"

def ejecutar_scrapers():
    print(f"🚀 INICIANDO ACTUALIZACIÓN DE PROMOS BANCARIAS")
    print("=" * 60)
    
    inicio_total = time.time()
    exitos = 0
    errores = 0

    for script in SCRIPTS:
        ruta_script = os.path.join(CARPETA, script)
        
        # Verificamos que el archivo exista antes de intentar correrlo
        if not os.path.exists(ruta_script):
            print(f"⚠️  ADVERTENCIA: No se encontró {ruta_script}. Saltando...")
            errores += 1
            continue

        print(f"\n▶️  Ejecutando: {script}...")
        try:
            # subprocess.run ejecuta el script como si lo escribieras en la terminal
            # sys.executable asegura que use el mismo Python (venv) que estás usando ahora
            resultado = subprocess.run(
                [sys.executable, ruta_script], 
                check=True,                 # Lanza error si el script falla
                text=True,                  # Maneja la salida como texto
                capture_output=False        # False para que veas los prints del script en vivo
            )
            print(f"✅ {script} finalizado correctamente.")
            exitos += 1
            
        except subprocess.CalledProcessError as e:
            print(f"❌ ERROR en {script}: El proceso terminó con código {e.returncode}.")
            errores += 1
        except Exception as e:
            print(f"❌ ERROR CRÍTICO ejecutando {script}: {e}")
            errores += 1

    duracion = round(time.time() - inicio_total, 2)
    
    print("\n" + "=" * 60)
    print(f"🏁 RESUMEN FINAL")
    print(f"⏱️  Tiempo total: {duracion} segundos")
    print(f"✅ Exitosos: {exitos}")
    print(f"❌ Fallidos: {errores}")
    print("=" * 60)

if __name__ == "__main__":
    ejecutar_scrapers()