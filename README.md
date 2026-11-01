# ⚔️ Parma — Character Hub & Grimoire

<div align="center">

![CI/CD Main](https://img.shields.io/github/actions/workflow/status/NMullerSM/Parma-Character-hub-and-Grimore/build-and-release.yml?branch=main&label=CI%2FCD%20main&style=for-the-badge)
![CI/CD Develop](https://img.shields.io/github/actions/workflow/status/NMullerSM/Parma-Character-hub-and-Grimore/build-and-release.yml?branch=develop&label=CI%2FCD%20develop&style=for-the-badge)
![Platforms](https://img.shields.io/badge/Plataformas-Windows%20%7C%20Linux-blue?style=for-the-badge&logo=linux&logoColor=white)
[![GitHub release](https://img.shields.io/github/v/release/NMullerSM/Parma-Character-hub-and-Grimore?style=for-the-badge&color=gold&label=%C3%9Altima%20Versi%C3%B3n)](https://github.com/NMullerSM/Parma-Character-hub-and-Grimore/releases/latest)
![Frontend](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite%208-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Backend](https://img.shields.io/badge/Backend-Python%203.12%20%2B%20PyWebView-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Database](https://img.shields.io/badge/Base%20de%20Datos-SQLite%20ACID-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![TaleSpire](https://img.shields.io/badge/Integraci%C3%B3n-TaleSpire%203D%20Symbiote-8A2BE2?style=for-the-badge)

**La suite definitiva de escritorio para jugadores y Directores de Juego de Dungeons & Dragons (5ª Edición y Reglas 2024 / 5.5e).**  
*100% Offline-First, ultraligera, con motor web nativo del sistema, sincronización tridimensional con TaleSpire y compendio atómico OKF.*

---

### 📥 Descarga Directa de Ejecutables (Release Oficial)

| Plataforma | Tipo de Paquete | Enlace de Descarga |
| :--- | :--- | :--- |
| **🪟 Windows (10 / 11 de 64 bits)** | **Instalador Oficial Guiado (.exe)** | [💾 **Descargar Parma-Setup.exe**](https://github.com/NMullerSM/Parma-Character-hub-and-Grimore/releases/latest) |
| **🪟 Windows (10 / 11 de 64 bits)** | **Versión Portable (.zip)** | [📁 **Descargar Parma-Windows-Portable.zip**](https://github.com/NMullerSM/Parma-Character-hub-and-Grimore/releases/latest) |
| **🐧 Linux (Pop!_OS, Ubuntu, Debian, Mint)** | **Paquete Nativo (.deb)** | [🐧 **Descargar parma_amd64.deb**](https://github.com/NMullerSM/Parma-Character-hub-and-Grimore/releases/latest) |
| **🐧 Linux (Todas las Distribuciones)** | **Tarball Portable (.tar.gz)** | [📦 **Descargar Parma-Linux-Portable.tar.gz**](https://github.com/NMullerSM/Parma-Character-hub-and-Grimore/releases/latest) |

*Todos los paquetes se generan y publican automáticamente mediante GitHub Actions en la sección **[Releases](https://github.com/NMullerSM/Parma-Character-hub-and-Grimore/releases/latest)**.*

</div>

---

## ✨ Características Principales

### 1. ⚔️ Consola de Combate y Estado Dinámico
* **Salud Reactiva:** Barra de PG animada con gradientes reactivos, soporte de daño, curación y PG temporal.
* **Efectos Visuales Cinematográficos:** Destellos de viñeta en pantalla ante impactos de daño (carmesí) o curaciones (esmeralda).
* **Filtro Táctico de Acciones:** Clasificación en 1 clic de armas y conjuros por **Acción**, **Acción Adicional** y **Reacción**.
* **Gestor de Ranuras Mágicas:** Consumo automático de ranuras al lanzar conjuros y restauración en descansos.
* **Salvaciones contra la Muerte:** Registro interactivo de éxitos y fallos con detección de 20 natural y 1 de pifia.

### 2. 📜 Ficha Clásica Oficial y Asistente Legal
* Cálculo automático de modificadores de característica, competencia por nivel y tiradas de salvación.
* Las 18 habilidades oficiales con soporte para **Competencia** y **Pericia** (`expertise`).
* **Asistente de Creación:** Creador de personajes paso a paso 100% legal con soporte de **Point Buy (27 pts)** y **Standard Array**.

### 3. ✨ Grimorio Mágico y Compendio OKF (570+ Entidades)
* **Base de Conocimiento Atómica OKF (Open Knowledge Format):** Tarjetas en Markdown con YAML frontmatter extraídas del **PHB 2024**, **Guía de Xanathar** y **Caldero de Tasha**.
* Búsqueda difusa y filtros por nivel (Trucos a Nivel 9), clases permitidas, componentes (V, S, M), concentración y ritual.
* Modal de inspección detallada con fórmulas de tirada automáticas.

### 4. 🎲 Integración 3D con TaleSpire (Symbiote Oficial)
* Comunicación bidireccional mediante WebSockets locales.
* **Symbiote Auto-instalable:** Detecta automáticamente las rutas de Steam de TaleSpire en Windows y Linux e instala el symbiote oficial.
* Envío de tiradas de ataque, daño y conjuros con 1 clic directo a la mesa tridimensional de TaleSpire.

### 5. 🌐 Sesiones Online para DM y Cloudflare Tunnels
* Servidor local asíncrono **FastAPI + Uvicorn** integrado en la aplicación.
* Conexión para jugadores remotos desde cualquier navegador móvil o de escritorio mediante **Cloudflare Tunnels** temporales sin abrir puertos en el router.
* Generador de códigos QR para que los jugadores escaneen y se unan al instante.

### 6. 📘 Visor de Manuales PDF y Mapeo AcroForm
* Renderizado de manuales pesados en alta resolución mediante **PyMuPDF (`fitz`)** con control estricto de memoria y caché LRU de páginas.
* Importación y exportación de fichas oficiales editables en formato **AcroForm PDF** (bilingüe español/inglés).

### 7. 📖 Diario de Campaña y 🕸️ Red de Personajes
* Crónicas cronológicas de sesión, botín y experiencia (XP).
* Grafo visual interactivo de relaciones, aliados, PNJs y facciones de la campaña.

---

## 📦 Descarga e Instalación Detallada

Los ejecutables se compilan automáticamente para Windows y Linux mediante **GitHub Actions**:

### 🪟 Windows (10 / 11 de 64 bits)
* **Instalador Oficial (`Parma-Setup-*.exe`):** Asistente guiado de instalación con accesos directos y desinstalador limpio (Inno Setup 6).
* **Versión Portable (`Parma-Windows-Portable.zip`):** Descomprimir y ejecutar directamente `Parma.exe` sin necesidad de instalación.

### 🐧 Linux (Pop!_OS, Ubuntu, Debian, Linux Mint, Fedora, Arch)
* **Paquete Debian (`parma_*_amd64.deb`):** Paquete nativo Debian Policy compliant:
  ```bash
  sudo dpkg -i parma_*_amd64.deb
  # O abrir directamente con el instalador Eddy / GDebi
  ```
* **Tarball Portable (`Parma-Linux-Portable.tar.gz`):** Ejecutable en cualquier distro sin alterar el sistema:
  ```bash
  tar -xzf Parma-Linux-Portable.tar.gz
  cd Parma
  ./parma.sh
  ```

---

## 🛠️ Desarrollo Local

### Requisitos Previos
* **Python 3.11 o 3.12**
* **Node.js 22+** y **npm**
* *En Linux:* Cabeceras de WebKitGTK y Cairo:
  ```bash
  sudo apt-get install -y libgirepository-2.0-dev libcairo2-dev gir1.2-webkit2-4.1 python3-gi
  ```

### Puesta en Marcha en 3 Pasos
```bash
# 1. Clonar el repositorio
git clone https://github.com/NMullerSM/Parma-Character-hub-and-Grimore.git
cd Parma-Character-hub-and-Grimore

# 2. Instalar y compilar el frontend
cd frontend
npm install
npm run build
cd ..

# 3. Iniciar la aplicación de escritorio
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
python desktop_app.py
```

---

## 📚 Documentación Técnica Detallada

Para consultar las decisiones de diseño, contratos de datos y especificaciones técnicas completas:

* 🏛️ **[docs/BACKEND.md](docs/BACKEND.md)** — Arquitectura Python, SQLite, compendio OKF, puente TaleSpire y servidor de sesiones.
* 🎨 **[docs/FRONTEND.md](docs/FRONTEND.md)** — Arquitectura React 18, Vite 8, Tailwind v4, Contexto y contratos de tipado estricto.
* 🚀 **[docs/CICD.md](docs/CICD.md)** — Flujo GitHub Actions, empaquetado Inno Setup / Debian y catálogo de problemas resueltos.

---

## ⚖️ Licencia

Distribuido bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.  
*Dungeons & Dragons, D&D y sus contenidos asociados son marcas comerciales de Wizards of the Coast LLC.*
