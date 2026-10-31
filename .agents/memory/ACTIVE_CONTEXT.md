# Active Context — D&D Sanctum / Parma

## 📅 Última Sesión
- **Fecha**: 2026-10-31 16:58 (UTC-3)
- **Dispositivo**: Notebook Pop!_OS (Linux x86_64)
- **Rama Git**: `develop`
- **Último Commit en `develop`**: `67299241aba644582d70e645d9f11b7c6c05c9a3`

---

## 🚀 Cambios de Código y Funcionalidades Implementadas

1. **Resolución Paralela con Subagentes y Worktrees (`fix/windows-compilation` y `fix/ci-linux-build`)**
   - **Frontend & Windows (PR #2 merged):**
     - `frontend/src/api/types.ts`: Sincronizada y enriquecida la interfaz `SpellStatsData` con compatibilidad completa para `ability`, `dc`, `save_dc`, `attack_bonus`, `is_caster`, `casting_ability`, `spell_save_dc`, `spell_attack_bonus`, `ability_mod`.
     - `frontend/src/api/client.ts`: Declarado e implementado el método `getClassSpells(className, maxLevel, lang)` conectado a `window.pywebview.api.get_class_spells`.
     - `frontend/src/views/JournalView.tsx`: Aplicada coalescencia nula segura en `selectSession` (`sess.id ?? null`, `sess.loot ?? ""`, `sess.xp_gained ?? 0`, `sess.session_id || ""`), protegiendo los hooks de estado.
     - `frontend/tsconfig.node.json`: Actualizado a `"module": "ESNext"` y `"moduleResolution": "Bundler"`, eliminando el error TS5110.
     - `ejecutables/windows/installer/parma_setup.iss`: Verificada y asegurada arquitectura x64 para Inno Setup.
   - **Linux & Packaging (PR #3 merged):**
     - `.github/workflows/build-and-release.yml`: Dependencias completas para Ubuntu 24.04 (`libgirepository-2.0-dev` con fallback `libgirepository1.0-dev`, `libcairo2-dev`, `gir1.2-webkit2-4.1`).
     - `ejecutables/linux/deb/build_deb.py`: Permisos recursivos estrictos `0o755` en el árbol de directorios y terminación estricta de `DEBIAN/control` con `\n`.
     - `ejecutables/linux/parma.sh`: Script lanzador portable con variable `WEBKIT_DISABLE_DMABUF_RENDERER=1` para evitar pantallas negras en NVIDIA/Wayland.
     - `build_desktop.py`: Integrada la copia automática y permisos `0o755` de `parma.sh` al generar el paquete tarball `.tar.gz`.

2. **Integración Consolidada en `develop`**
   - Ambas ramas convergieron limpiamente en `develop` con 0 conflictos.
   - Nuevo pipeline CI/CD en ejecución activa en GitHub Actions para compilar `build-windows` y `build-linux` en paralelo.

---

## 🎯 Tareas Pendientes Prioritarias

- [ ] Monitorear la ejecución del workflow de GitHub Actions en la rama `develop` (Commit `6729924`).
- [ ] Validar la generación de artefactos:
  - Windows: `Parma-Setup-*.exe` y portable `.zip`.
  - Linux: `parma_*_amd64.deb` y portable `.tar.gz`.
- [ ] Realizar merge a `main` para publicar la Release oficial en el perfil de GitHub.
