# Active Context — Parma (D&D Character Hub & Grimoire)

## 📅 Última Sesión
- **Fecha**: 2026-11-01
- **Dispositivo**: Notebook Pop!_OS Linux
- **Estado General**: Merge completo de `develop` a `main` exitoso (PR #4 cerrado con merge commit `a1e852c9cf1d0927eccb41b2ee6e80b113d62b10`). Pipeline CI/CD de GitHub Actions disparada en `main` para compilar instaladores de Windows (.exe / .zip) y Linux (.deb / .tar.gz).

---

## 🛠️ Decisiones Técnicas y Cambios Recientes

### 1. Merge Oficial a `main` (Release v1.0.0) y Homogeneización CI/CD
- Integración completa de todos los motores estabilizados:
  - `desktop_api/bridge.py`: RPC PyWebView completo (2370 líneas) con Forja, dados 3D con TaleSpire, visor de PDF, descargas y servidor DM.
  - `core/okf_engine.py`: Motor atómico OKF con normalización de rutas en Windows/Linux y soporte multilingüe (ES/EN).
  - `core/pdf_engine.py`: PyMuPDF con TOC, renderizado de páginas e importación/exportación AcroForm.
  - `core/paths.py`: Aislamiento UAC entre `bundle_dir` y `user_data_dir`.
  - Frontend React 18: Tipos TypeScript alineados, Forja accesible desde estado vacío, selector de género y prompt builder para Pollinations FLUX.
  - Scripts de empaquetado para Debian/Ubuntu e InnoSetup para Windows.
- **Homogeneización de GitHub Actions (`develop` y `main`)**:
  - Se homogeneizó `.github/workflows/build-and-release.yml` en ambas ramas incorporando la separación de `npx tsc -b` de `npm run build`.
  - Se robusteció el job `publish-release`: recolección automática y aplanado de artefactos (`.exe`, `.zip`, `.deb`, `.tar.gz`) en `release_assets/`, fijado de versión a `v1.0.0` oficial con `make_latest: true`, y soporte para ejecución manual vía `workflow_dispatch`.
  - Se incorporó en `README.md` (portada del repositorio) una tabla de descarga directa con insignias y enlaces directos a las releases oficiales.

### 2. Privacidad y Repositorio Limpio
- Se purgaron definitivamente las fichas personales de personajes (`Artanis LVL 4.pdf` y `Artanis_Sheet.pdf`) tanto en `main` como en `develop`.
- `.gitignore` configurado para ignorar `data/characters/*` preservando únicamente `.gitkeep` y plantillas oficiales.

### 3. Red y Conectividad (Alcance Congelado por Instrucción del Usuario)
- El reporte de conectividad (anfitrión en Linux recibiendo invitados de Windows vs anfitrión en Windows) se mantiene **congelado sin alteraciones de código** para pruebas futuras del usuario.

---

## 📋 Tareas Pendientes / Siguiente Equipo
1. Monitorear la finalización del workflow de GitHub Actions en `main` (`build-and-release.yml`).
2. Verificar la generación y publicación de los artefactos de la release en GitHub Releases (instalador Windows `.exe`, portable `.zip`, paquete Linux `.deb` y `.tar.gz`).
3. Realizar pruebas de conectividad de red entre Linux y Windows cuando el usuario decida retomar el análisis de túneles / sockets.
