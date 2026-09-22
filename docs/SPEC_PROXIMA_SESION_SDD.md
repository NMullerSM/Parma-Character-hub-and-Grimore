# Especificación Formal SDD: Persistencia SQLite, Árbol OKF, Visor PDF y Retrato del Personaje

Este documento deja formalmente estipulada la especificación de **Desarrollo Guiado por Requisitos (Spec-Driven Development - SDD)** solicitada para la siguiente sesión de trabajo.

---

## 1. Persistencia Local con SQLite (`dnd_database.db`)
- **Objetivo**: Reemplazar el almacenamiento plano de archivo JSON único por una base de datos relacional local en SQLite (`sqlite3` nativo de Python).
- **Esquema propuesto**:
  - `characters`: Almacenamiento tipado de atributos, identidad, dados de vida, CA, espacios de conjuro, inventario y rasgos, con soporte para perfiles multi-personaje.
  - `network_nodes` y `network_edges`: Persistencia relacional de los aliados, rivales y vínculos de campaña vinculados a cada personaje.
  - `campaign_journals`: Diario de campaña relacional con registro de sesiones, fechas, botín y PX.
  - `app_settings`: Preferencias de aplicación (personaje activo, manual PDF reciente, última página leída, nivel de zoom).
- **Características**: Conexión en modo WAL (`PRAGMA journal_mode=WAL`), transacciones atómicas transparentes y migración automática del archivo `autosave_character.json` existente.

---

## 2. Árbol Atómico OKF: Renderizado Markdown Real y Buscador en Índice
- **Renderizado Markdown**: Sustituir el actual contenedor `ft.Text` en la vista de detalle por `ft.Markdown(extension_set=ft.MarkdownExtensionSet.GITHUB_WEB)`.
- **Limpieza de comillas y caracteres de escape**: Higienizar las descripciones para eliminar las comillas dobles envolventes (`""`), barras invertidas de escape y marcas de Markdown crudas que actualmente se ven como texto plano.
- **Buscador directo en el Índice de Entidades**: Integrar un campo de búsqueda interactivo en la cabecera del panel izquierdo (`master_panel`) que filtre en tiempo real los 378 conjuros, 74 dotes, especies, clases y reglas.

---

## 3. Visor de Manuales: Modo Lectura Inmersivo y Controles Superiores Ergonómicos
- **Reorganización de Controles en Barra Superior**:
  - **Izquierda**: Selector de manual (`Manual del Jugador 2024.pdf`, `Artanis LVL 4.pdf`, etc.) y botón de Índice de Contenidos (TOC).
  - **Centro**: Paginación directa (`[◄] [Página actual] / [Total] [►]`).
  - **Derecha**: Controles de zoom (`[-]`, `[%]`, `[+]`), `Ajustar al Ancho` y botón de `Modo Lectura Inmersivo`.
- **Modo Inmersivo (Zen Reader)**: Oculta temporalmente las pestañas generales y la barra de herramientas principal de la aplicación, destinando el 100% del área vertical a la visualización inmersiva del documento PDF sin elementos que lo empujen hacia abajo.

---

## 4. Visualización del Propio Personaje (Retrato, Avatar y Ficha Gráfica)
- **Componente de Retrato (`CharacterPortraitCard`)**:
  - Marco artístico dorado con avatar del héroe en la cabecera de la **Hoja Clásica** y en la vista de **Combate**.
  - Soporte para subir o elegir imagen local (PNG, JPG, WebP) que se persiste en SQLite.
  - Fallback visual estilizado con icono de clase e iniciales si no hay foto seleccionada.
  - Integración armónica con la barra de puntos de golpe, inspiración heroica y rasgos físicos.

---

*Documento preparado y aprobado para ejecución en la próxima sesión.*
