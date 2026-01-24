# 🛒 DataChango | Agregador Inteligente de Ofertas

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)
![Selenium](https://img.shields.io/badge/Scraping-Selenium-green)
![Status](https://img.shields.io/badge/Status-Stable%20v1.0-success)

**DataChango** es una plataforma de inteligencia de datos que centraliza, normaliza y visualiza ofertas de los principales hipermercados de Argentina (**Coto, Jumbo, Carrefour y MasOnline**). 

El objetivo es simplificar la toma de decisiones del consumidor mediante un dashboard unificado que combina descuentos por categoria  y promociones bancarias, utilizando técnicas de extracción de datos con Selenium y Python.

🔗 **Demo en vivo:** [datachangoweb.onrender.com](https://datachangoweb.onrender.com)

---

##  Características Técnicas

###  1. Scraping Híbrido (DOM + Visión Artificial)
- **Extracción Híbrida:** Combina selectores CSS/XPath tradicionales con **EasyOCR** (Optical Character Recognition) para leer ofertas "incrustadas" en imágenes.
- **Normalización de Texto:** Algoritmos propios para estandarizar nombres de productos y categorías heterogéneas.

###  2. Validación y Filtrado Inteligente
- **Detección de "Falsas Ofertas":** Lógica condicional para distinguir entre descuentos reales y financiación pura.
- **Anti-Alucinación:** Filtros de precisión para evitar errores comunes de OCR y garantizar la integridad de los datos.

###  3. Arquitectura y Performance
- **Orquestación Modular:** Scripts de extracción (`scrapers_bancarios/`, `run_all.py`) separados de la capa de visualización (`app.py`).
- **Dependencias Optimizadas:** Separación de entornos (`requirements.txt` ligero para Web vs `ori-requirements.txt` completo para Scraping) para despliegues ágiles en la nube.
- **UX Avanzada:** Modal de "Lupa" con inyección JS personalizada y delegación de eventos para compatibilidad móvil/desktop.

---

## 📂 Estructura del Proyecto

```text
datachango_root/
├── app.py                      # Dashboard principal (Frontend Streamlit)
├── run_promos.py               # Orquestador: Promos Bancarias
├── run_all.py                  # Orquestador: Ofertas de Productos
├── deploy_diario.py            # Script de automatización (Scrape + Git Push)
│
├── scrapers_bancarios/         # Paquete: Scrapers de Bancos
│   ├── __init__.py
│   ├── bancarias_coto.py
│   ├── bancarias_jumbo.py
│   └── ...
│
├── scraper_carrefour_general.py 
├── scraper_coto.py             
├── scraper_jumbo.py            
│
├── ofertas_*.json              # Base de datos (Archivos planos)
├── promos_*.json               # Datos bancarios procesados
├── requirements.txt            # Dependencias ligeras (Solo para Render/App)
└── ori-requirements.txt        # Dependencias completas (Para correr Scrapers localmente)


## 📦 Instalación y Uso Local
Pasos para levantar el proyecto completo en tu computadora:

1. Clonar el repositorio
2. Crear entorno virtual:
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

3. Instalar dependencias:
pip install -r ori-requirements.txt

4. Ejecutar Scrapers
python run_promos.py  # Bancos
python run_all.py     # Productos

5. Iniciar el Dashboard:
streamlit run app.py