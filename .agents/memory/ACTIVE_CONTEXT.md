# Active Context — D&D Sanctum / Parma

## 📅 Última Sesión
- **Fecha**: 2026-10-30 16:25 (UTC-3)
- **Dispositivo**: Notebook Pop!_OS (Linux x86_64)
- **Rama Git**: `develop`
- **Último Commit en `develop`**: `63bde4e676568aff609564773e748936dda763ac`

---

## 🚀 Cambios de Código y Funcionalidades Implementadas

1. **Reparación de Tipos TypeScript y Frontend para CI/CD**
   - `frontend/src/components/AnimatedHealthBar.tsx`: Corregido tipo del timer a `ReturnType<typeof setTimeout>` para evitar el fallo `Cannot find namespace 'NodeJS'` en Vite.
   - `frontend/src/api/types.ts`: Incorporadas propiedades `symbiote_connected`, `symbiote_folder_installed` y `symbiote_install_path` en `TaleSpireStatus`.
   - `frontend/src/api/client.ts`: Añadidos métodos `reinstallTaleSpireSymbiote` y `openTaleSpireSymbiotesFolder`.
   - `desktop_api/bridge.py`: Implementados métodos de backend `reinstall_talespire_symbiote` y `open_talespire_symbiotes_folder`.
   - `frontend/tsconfig.app.json`: Añadido `"node"` a `"types"` para compatibilidad total de compilación `tsc -b`.

2. **Pipeline Multiplataforma CI/CD (`.github/workflows/build-and-release.yml`)**
   - **En `develop` (Test Compilation):**
     - Compila en paralelo para Windows (`windows-latest`) y Linux (`ubuntu-latest`).
     - Genera instalador Inno Setup (`.exe`), paquete portable (`.zip`), paquete Debian (`.deb`) y tarball portable (`.tar.gz`).
     - **Resguardo interno / Oculto:** Las compilaciones se guardan como artefactos de GitHub Actions (retención 14 días), sin crear releases públicos en la portada del repositorio.
   - **En `main` (Public Release):**
     - Al hacer merge a `main`, ejecuta el mismo pipeline y publica automáticamente una **Release oficial en el perfil público de GitHub** con los 4 ejecutables adjuntos y changelog de versión.

---

## 🎯 Tareas Pendientes Prioritarias

- [ ] Monitorear la ejecución del workflow en GitHub Actions sobre la rama `develop`.
- [ ] Validar la generación de artefactos en Windows y Linux.
- [ ] Merge a `main` cuando esté validado.
