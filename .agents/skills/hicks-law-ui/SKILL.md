---
name: hicks-law-ui
description: >-
  Principios de diseño UI y UX basados en la Ley de Hick para el Visualizador & Editor D&D 5e.
  Minimiza la sobrecarga cognitiva, erradica la saturación innecesaria de iconos,
  evita superposiciones visuales y garantiza divulgación progresiva con salidas claras.
---

# Principios de Diseño UI / UX: Ley de Hick y Ergonomía Visual

Este skill codifica las preferencias fundamentales de experiencia de usuario y arquitectura visual para el proyecto **Visualizador & Editor D&D 5e**.

---

## 1. La Ley de Hick ($T = b \cdot \log_2(n + 1)$)

> *"El tiempo que tarda una persona en tomar una decisión aumenta logarítmicamente con el número y la complejidad de las opciones presentes."*

### Reglas de Aplicación en la Interfaz:
1. **Reducción de Alternativas Inmediatas**:
   - No expongas todas las micro-opciones a la vez.
   - En lugar de saturar al usuario con 40 configuraciones simultáneas, estructura los flujos en etapas lógicas y secuenciales (divulgación progresiva).
2. **Jerarquía Visual Clara**:
   - Una acción primaria indiscutible por pantalla (ej. "Siguiente Fase" o "Forjar Personaje").
   - Acciones secundarias atenuadas y acciones destructivas claramente diferenciadas.

---

## 2. Restricción Estricta de Iconos (Anti-Icon Proliferation)

⚠️ **DIRECTRIZ CRÍTICA DEL USUARIO**: No poner iconos en cada elemento, texto o botón.

### Lineamientos de Iconografía:
- **Prohibido**: Añadir iconos decorativos redundantes a cada etiqueta de texto (ej. no poner `❤️ Vida:`, `🛡️ Defensa:`, `⚡ Iniciativa:`, `📜 Nombre:` juntos de forma invasiva si generan ruido visual).
- **Permitido con Moderación**:
  - Iconos de navegación universal: `Cerrar (✕)`, `Volver (◄)`, `Ajustes (⚙)`.
  - Iconos de acción primaria distintiva: Tirar dados (`CASINO`), Subir foto (`UPLOAD_FILE`).
- **Prioridad Tipográfica**:
  - La tipografía limpia con contrastes de peso (`Bold` vs `Normal`) y colores atenuados (`TEXT_MAIN` vs `TEXT_MUTED`) es mucho más legible, elegante y profesional que un muro de pictogramas.

---

## 3. Divulgación Progresiva (Progressive Disclosure)

- Despliega detalles únicamente cuando el contexto lo requiere:
  - Las **Subrazas / Linajes** solo se muestran tras seleccionar la especie base.
  - Los **Arquetipos / Subclases** solo se habilitan cuando el nivel del personaje alcanza el umbral de desbloqueo oficial (Nivel 1 para Clérigo/Brujo; Nivel 2 para Mago/Druida; Nivel 3 para Guerrero/Pícaro/etc.).
  - Las secciones de **Conjuros y Magia** se omiten o sintetizan si la clase es 100% marcial.

---

## 4. Prevención de Superposiciones y Desbordamientos (Responsive Spacing)

- **Contenedores Adaptables**: Ningún widget puede solaparse con otro.
- Utiliza siempre contenedores con `expand=True`, `scroll=ft.ScrollMode.ADAPTIVE` o listas con espaciado controlado (`spacing=8` a `12`).
- Las ventanas modulares y diálogos deben calcular su anchura y altura con margen de seguridad para evitar recortes en pantallas de resolución estándar (ej. 1366×768 hasta 4K).

---

## 5. Salidas Claras y Mecanismos de Escape (Clear Escape Hatches)

- Todo diálogo modal, asistente o vista superpuesta debe contar obligatoriamente con:
  1. Botón de cierre visible en la esquina superior derecha (`ft.IconButton(ft.Icons.CLOSE)`).
  2. Botón explícito de `Cancelar / Salir` en la barra de acciones inferior.
  3. Soporte para cierre mediante la tecla `Escape` o clic en el fondo (`modal=False`).
