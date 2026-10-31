# Active Context — D&D Sanctum / Parma

## 📅 Última Sesión
- **Fecha**: 2026-10-31 19:52 (UTC-3)
- **Dispositivo**: Notebook Pop!_OS (Linux x86_64)
- **Rama Git**: `develop`
- **Último Commit en `develop`**: `aa1a6e0cd196077397275ef6534a5ac38d76ef31`

---

## 🚀 Cambios de Código y Funcionalidades Implementadas

1. **Estabilización Total de Pipelines CI/CD (`build-windows` y `build-linux` en verde)**
   - Corregida la definición de `SpellStatsData` en `frontend/src/api/types.ts` estableciendo `ability: string`, `dc: number`, `attack_bonus: number` como obligatorios (contrato exacto enviado por Python).
   - Separado el paso de verificación estricta de tipos (`npx tsc -b`) del paso de empaquetado (`npm run build`) en `.github/workflows/build-and-release.yml`.
   - **Resultado:** Ambos runners (`windows-latest` y `ubuntu-latest`) compilaron en verde con éxito.

2. **Actualización Completa del README.md y Normalización de Documentación**
   - Actualizado [README.md](file:///home/nathanielwrk/Documentos/Proyects/Dnd_Player_Dashboard/README.md) con la identidad moderna de **Parma — Character Hub & Grimoire** (badges, características, guía de descarga, inicio rápido y arquitectura).
   - Creados y normalizados 3 documentos maestros de arquitectura y decisiones en `docs/`:
     - 🏛️ [`docs/BACKEND.md`](file:///home/nathanielwrk/Documentos/Proyects/Dnd_Player_Dashboard/docs/BACKEND.md): PyWebView, SQLite, Compendio OKF, TaleSpire Symbiote, PyMuPDF, servidor de sesiones DM con Cloudflare Tunnels, decisiones de diseño y soluciones a problemas gráficos de Linux.
     - 🎨 [`docs/FRONTEND.md`](file:///home/nathanielwrk/Documentos/Proyects/Dnd_Player_Dashboard/docs/FRONTEND.md): React 18, Vite 8, Tailwind CSS v4, Contexto reactivo, capa RPC híbrida (nativo/mock web), internacionalización y tipado estricto de TypeScript.
     - 🚀 [`docs/CICD.md`](file:///home/nathanielwrk/Documentos/Proyects/Dnd_Player_Dashboard/docs/CICD.md): Estrategia de ramas dual (`develop` privado vs `main` público), runners de Windows y Linux, empaquetado Inno Setup / Debian y catálogo de los 9 problemas resueltos.

---

## 🎯 Tareas Pendientes Prioritarias

- [ ] Descargar y probar localmente los binarios generados en los artefactos de GitHub Actions:
  - Windows: `Parma-Setup-*.exe` / `Parma-Windows-Portable.zip`.
  - Linux: `parma_*_amd64.deb` / `Parma-Linux-Portable.tar.gz`.
- [ ] Tras validar los ejecutables, realizar merge de `develop` a `main` para publicar la Release oficial en el perfil público de GitHub.
