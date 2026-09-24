# Visualizador & Editor D&D 5e (Flet Desktop Edition)

Una aplicación nativa de escritorio moderna, reactiva, elegante y **100% offline** construida en **Python y Flet (Flutter engine)** para **visualizar, editar interactivamente y gestionar** hojas de personaje de D&D 5e basadas en PDFs editables (AcroForm), acompañada de una base de conocimiento atómica **OKF (Open Knowledge Format)** extraída íntegramente del **Manual del Jugador 2024**, **Guía de Xanathar para Todo** y **El Caldero de Tasha para Todo**.

---

## 🚀 Inicio Rápido Multiplataforma

### En Linux 🐧
```bash
./iniciar.sh
# O directamente:
.venv/bin/python run_app.py
```

### En Windows 🪟
1. **Doble clic en `iniciar_desktop.bat`** (o `iniciar.bat`)
2. O desde PowerShell / CMD:
   ```powershell
   .\iniciar_desktop.bat
   ```

---

## 📁 Jerarquía de Datos y PDFs
- `data/manuals/`: Libros de reglas oficiales en PDF (`Manual del Jugador 2024.pdf`, `Guía de Xanathar`, `Caldero de Tasha`).
- `data/characters/`: Fichas de personaje en PDF (`Artanis LVL 4.pdf`), exportaciones de hojas y avatares.
- `okf_dnd5e/`: Compendio atómico de 495 entidades (conjuros, dotes, especies, clases, reglas).

---

## ✨ Módulos y Características de la Suite de Escritorio

### 1. ⚔️ Combate & Estado
- **Salud y Puntos de Golpe (PG)**: Barra de salud en tiempo real con selector de daño, curación y PG temporal.
- **Salvaciones Contra la Muerte**: Casillas de éxitos y fallos con botón interactivo de tirada d20 (reconoce 20 natural y 1 crítico).
- **Armas y Ataques**: Lista interactiva de armas con botones para tirar ataque y daño, además de diálogo para añadir nuevas armas y botón para eliminarlas.

### 2. 📄 Hoja Clásica de Personaje
- Cálculo automático de modificadores de característica (-5 a +10).
- Bonificador por competencia automático según el nivel.
- Tiradas de salvación con botón directo `Tirar Salvación`.
- Las 18 habilidades oficiales con soporte para pericia (`expertise`) y competencia (`proficient`).
- Sentidos pasivos (Percepción pasiva), idiomas y competencias de equipo.

### 3. ✨ Conjuros & Magia
- **Tarjetas de Conjuros Oficiales**: Visualización rica de cada conjuro con tiempo de lanzamiento, alcance, duración, concentración, ritual, componentes (`Comp: V, S, M`) y **badges dorados de las clases permitidas**.
- **Botón `🎲 Lanzar`**: Si es un truco (nivel 0), se lanza sin coste. Si es de nivel 1 a 9, descuenta automáticamente 1 espacio de conjuro en el rastreador interactivo (`SlotTracker`).
- **Selector Rápido OKF**: Modal de búsqueda rápida entre los 378 conjuros clasificados por clase y nivel.

### 4. 🌟 Rasgos & Poderes
- Seguimiento interactivo de usos de habilidades por descanso (Dados de inspiración, puntos de suerte, etc.).
- **`+ Añadir Dote (OKF)`**: Modal interactivo para explorar y agregar cualquiera de las 74 dotes oficiales del Manual 2024 a la ficha.

### 5. 🌳 Árbol OKF (Compendio Completo 495 Entidades)
- Navegador visual del árbol de conocimiento atómico en Markdown con YAML frontmatter:
  - 📁 **Conjuros (378)**: Filtrado por nivel (0 a 9) y clase (Bardo, Mago, Clérigo, etc.).
  - 📁 **Dotes (74)**: Origen, Generales, Estilo de combate y Dones épicos.
  - 📁 **Especies y Linajes (11)**.
  - 📁 **Trasfondos (17)**.
  - 📁 **Clases y Subclases (13)**.
  - 📁 **Reglas y Mecánicas**.
- Cada entidad se despliega como una tarjeta visual completa con descripción íntegra y botón `+ Añadir a mi Ficha`.

### 6. 📘 Visor de Manuales PDF (PyMuPDF)
- Renderizado de PDFs en alta resolución con control estricto de memoria (caché LRU de 4 páginas y liberación inmediata de pixmaps nativos).
- **Selector de Documentos**: `Manual del Jugador 2024.pdf`, `Guía de Xanathar para Todo.pdf`, `Caldero de Tasha para Todo.pdf` y `Artanis LVL 4.pdf`.
- **Índice Interactivo (TOC / Bookmarks)**: Despliega el índice del manual para saltar a cualquier capítulo en 1 clic.
- **Navegación y Zoom**: Paginación directa, zoom del 100% al 200% y ajuste de página.

### 7. 📖 Diario de Campaña & 🌐 Red de Personajes
- Registro cronológico de sesiones, botín y experiencia.
- Directorio de aliados, PNJs, facciones y rivales de la campaña.

### 8. 💾 Gestión de Fichas (PDF & JSON)
- **`Abrir PDF`**: Carga e interpreta hojas oficiales editables AcroForm (bilingüe español/inglés).
- **`💾 Guardar JSON`**: Exporta y respalda todo el estado de la partida a un archivo `.json`.
- **`📂 Cargar JSON`**: Restaura cualquier ficha previamente guardada.
- **`📖 Reglas`**: Modal de referencia rápida para combate, descansos y condiciones.

---

## 📦 Compilación a Ejecutables Nativos

### En Linux (Binario Nativo ELF) 🐧
```bash
./compilar.sh
```
El ejecutable se compilará en `dist/linux/Visualizador_Dnd_5e/Visualizador_Dnd_5e`.

### En Windows (Ejecutable `.EXE`) 🪟
Doble clic en `compilar_exe.bat` o desde la terminal:
```powershell
.\compilar_exe.bat
```
El ejecutable se compilará en `dist\windows\Visualizador_Dnd_5e\Visualizador_Dnd_5e.exe`.

---

## 🛡️ Convenciones de Desarrollo (Linux & Windows)
1. **Multiplataforma por diseño**: Toda nueva característica o librería debe funcionar de forma idéntica en Linux y Windows.
2. **Dependencias limpias**: Los paquetes deben ser agnósticos o usar marcadores de plataforma PEP 508.
3. **Paridad de UI y lógica**: La experiencia visual en Flet y la lógica de juego son 100% compartidas.

Para consultar la especificación técnica completa y la hoja de ruta del proyecto, revisa [docs/PROJECT_CONVENTIONS_SDD.md](docs/PROJECT_CONVENTIONS_SDD.md).

