# Guía Metódica de Pruebas y Verificación (QA Checklist)
## Visualizador & Editor de Personajes D&D 5e (PyWebView + React Desktop)

Este documento contiene la lista ordenada y estructurada de pruebas para validar de forma progresiva todas las funcionalidades de la aplicación de escritorio.

---

## 📋 Resumen Rápido de Novedades y Correcciones Recientes

1. **Compendio OKF - Trasfondos Restaurados**: El catálogo oficial ahora indexa y muestra los **17 trasfondos oficiales** (Acólito, Soldado, Vagabundo, Sabio, etc.) con sus dotes de origen y bonos de atributos (antes mostraba 0).
2. **Corrección de Pantalla en Blanco en "+ Compendio OKF"**: Erradicado el fallo en tiempo de ejecución de React provocado por componentes de conjuro que venían como diccionarios YAML (`{verbal, somatico, material}`). Ahora se sanitizan y formatean siempre a strings seguros (`V, S, M`).
3. **Alcance en Casillas (Tiles)**: Todos los alcances de conjuros y armas en metros ahora muestran su equivalente exacto en casillas tácticas: `1.5 m (1 casilla)`, `9 m (6 casillas)`, `18 m (12 casillas)`, `36 m (24 casillas)`.
4. **Duración en Turnos de Combate**: Las duraciones temporales especifican los turnos de combate D&D 5e: `1 minuto (10 turnos)`, `10 minutos (100 turnos)`, `1 hora (600 turnos)`.
5. **Retrato Heroico Ampliado**: Imagen del personaje notablemente más grande, con subida de archivo desde disco con refresco visual instantáneo (sin necesidad de reiniciar o recargar).
6. **Generador de Retratos con IA y Apariencia**: Nueva sección en la ficha para describir la apariencia física y nuevo modal para generar prompts en estilos como **Pixel Art (16-bit RPG)**, **Fantasía Épica**, **Óleo Renacentista**, con soporte para conectar endpoints de APIs de imagen (OpenAI DALL-E, SD WebUI, etc.) o copiar prompts para Midjourney.

---

## 🧪 Fase 1: Compendio de Reglas Oficiales (Compendium View)

Navega a la pestaña **Compendio** en la barra superior.

- [ ] **1.1 Conteo de Categorías**:
  - Verifica que las pestañas superiores muestren conteos reales mayores a 0:
    - *Clases y Subclases (70)*
    - *Especies y Linajes (10)*
    - *Grimorio de Conjuros (380)*
    - *Trasfondos (17)* *(¡Previamente marcaba 0!)*
    - *Dotes (75)*
    - *Equipo y Armamento (4)*
    - *Reglas y Mecánicas (5)*
- [ ] **1.2 Pestaña "Trasfondos"**:
  - Haz clic en la pestaña **Trasfondos**.
  - Comprueba que en la columna izquierda aparecen listados los 17 trasfondos oficiales (Acólito, Animador, Artesano, Campesino, Charlatán, Comerciante, Criminal, Ermitaño, Escribano, Granjero, Guardia, Guía, Marinero, Noble, Sabio, Soldado, Vagabundo).
  - Comprueba que los subtítulos (snippets) muestran la Dote de Origen y los atributos clave (ej: `PHB 2024 • Dote: Iniciado en la magia (Clérigo) • Sabiduría, Inteligencia, Carisma`).
- [ ] **1.3 Visualización de Markdown de Trasfondo**:
  - Haz clic sobre un trasfondo cualquiera (ej: **Soldado** o **Acólito**).
  - En la columna derecha debe renderizarse fluidamente el Markdown completo con las características clave, dote concedida y competencias.
- [ ] **1.4 Buscador Central del Compendio**:
  - En el campo de búsqueda escribe `"Fuego"` o `"Sigilo"`.
  - Verifica que la lista filtre en tiempo real con debounce fluido y sin parpadeos.

---

## 🧪 Fase 2: Grimorio de Conjuros y Gestor de Compendio (Spells View)

Navega a la pestaña **Grimorio**.

- [ ] **2.1 Apertura del Gestor de Conjuros (+ Compendio OKF)**:
  - Haz clic en el botón dorado **+ Compendio OKF** en la esquina superior derecha.
  - **Prueba crítica**: Espera más de 200 milisegundos tras la apertura.
  - Verifica que **la pantalla NO se pone en blanco** y que el listado de conjuros se carga con normalidad.
- [ ] **2.2 Filtros de Clase y Nivel en el Gestor**:
  - Cambia entre las clases (Bardo, Mago, Clérigo, etc.).
  - Filtra por nivel (Trucos, Niv 1, Niv 2, etc.).
  - Escribe en el buscador `"Risa"` o `"Bola"`.
  - Haz clic en **Risa Espantosa de Tasha**:
    - Verifica que el campo *Componentes* muestra: `V, S, M (pequeñas tartas y una pluma)`.
    - Verifica que el *Alcance* muestra: `9 m (6 casillas) / 30 pies`.
    - Verifica que la *Duración* muestra: `Concentración, hasta 1 minuto (10 turnos)`.
- [ ] **2.3 Añadir y Quitar Conjuros**:
  - Haz clic en el botón verde/dorado **Añadir** en un conjuro.
  - El botón debe cambiar inmediatamente a estado **En Grimorio** con opción de eliminar (ícono de papelera).
  - Cierra el modal con `Esc` o el botón de cerrar.
  - Comprueba que el conjuro añadido aparece en tu lista principal de conjuros preparados.
- [ ] **2.4 Tarjetas del Grimorio y Detalle Canónico**:
  - En las tarjetas del grimorio, verifica que el alcance indique casillas (ej: `18 m (12 casillas)`).
  - Haz clic en una tarjeta de conjuro para abrir el visor interactivo (Pop-forward).
  - Comprueba que puedes lanzar el conjuro gastando una ranura de conjuro.
  - Haz clic en **Copiar Comando TaleSpire** y comprueba que se copia al portapapeles (ej: `!Bola de Fuego:8d6`).

---

## 🧪 Fase 3: Ficha de Personaje, Retrato Ampliado e IA (Sheet View)

Navega a la pestaña **Ficha**.

- [ ] **3.1 Retrato Heroico Ampliado**:
  - Comprueba que el contenedor del retrato del personaje es notablemente más grande (128x128px o 144x144px) con borde metálico y sombra elegante.
- [ ] **3.2 Subida de Retrato desde Disco**:
  - Pasa el cursor sobre el retrato y haz clic en **Subir** (o en el botón inferior "Subir").
  - Selecciona cualquier archivo de imagen (.png, .jpg o .webp).
  - **Verificación**: La imagen seleccionada debe aparecer **al instante** en el retrato sin necesidad de recargar la página ni reiniciar la aplicación.
- [ ] **3.3 Sección de Apariencia Física**:
  - Baja a la sección **Apariencia Física y Rasgos del Personaje**.
  - Escribe o edita una descripción en el cuadro de texto (ej: *"Guerrero de 1.85 m, ojos verdes, armadura de placas bruñida con emblema de dragón plateado"*).
  - Haz clic en **Guardar Cambios** arriba a la derecha y verifica que se conserva al navegar entre pestañas.
- [ ] **3.4 Generador de Retratos con IA (Modal)**:
  - Haz clic en el botón **Retrato IA** (sobre el retrato) o **Generar Retrato con IA** (en la sección de apariencia).
  - Comprueba que se abre el modal *"Generador de Retrato IA de Personaje"*.
  - Cambia entre los estilos artísticos:
    - 🎨 **Pixel Art (16-bit RPG)** *(Estilo solicitado por defecto)*
    - ⚔️ **Fantasía Épica Digital**
    - 🖌️ **Pintura al Óleo Clásica**
    - ✏️ **Boceto a Tinta / Pergamino**
    - 🎬 **Cinemático Realista**
  - Observa cómo el texto del prompt se actualiza automáticamente incorporando el nombre, clase, raza, descripción de apariencia y el estilo elegido.
- [ ] **3.5 Acciones del Generador IA**:
  - Haz clic en **Copiar Prompt** y comprueba la confirmación *"¡Copiado!"*.
  - Haz clic en **Configuración API**: verifica que puedes ingresar la URL de un endpoint (ej: DALL-E de OpenAI o Stable Diffusion) y tu API Key.
  - Prueba pegar una URL de imagen o código Base64 en el campo *"O pega una URL o Base64 directamente"*.
  - Haz clic en **Aplicar a la Ficha**: comprueba que la imagen se aplica instantáneamente al retrato del personaje y se guarda en la base de datos.
- [ ] **3.6 Tiradas de Dados Interactivas**:
  - Haz clic sobre cualquier atributo (FUE, DES, etc.) para lanzar prueba de característica.
  - Haz clic en cualquier botón de salvación para tirar salvación con bono competente.
  - Haz clic en una habilidad de la lista lateral (ej: *Percepción*).
  - Haz clic en un arma (ej: *Estoque*) para tirar impacto (1d20 + bono) y en el botón de daño para tirar los dados de daño.
- [ ] **3.7 Exportación**:
  - Haz clic en **Exportar JSON**: verifica la generación del archivo `.json`.
  - Haz clic en **Exportar PDF**: verifica la exportación canónica.

---

## 🧪 Fase 4: Modo Combate Táctico (Combat View)

Navega a la pestaña **Combate**.

- [ ] **4.1 Gestor de Grimorio en Combate**:
  - En la sección mágica de combate, haz clic en **Gestionar Grimorio**.
  - Comprueba que el modal de conjuros OKF abre sin cierres inesperados ni pantallas blancas.
- [ ] **4.2 Alcances en Casillas (Tiles)**:
  - En las tarjetas de conjuro de combate, verifica que el alcance incluye las casillas (ej: `18 m (12 casillas)` o `1.5 m (1 casilla)`).
- [ ] **4.3 Ranuras de Conjuro en Combate**:
  - Haz clic en una esfera de ranura de conjuro para marcarla como gastada.
  - Vuelve a hacer clic para recuperarla.
- [ ] **4.4 Filtro por Tipo de Acción**:
  - Alterna entre los filtros: *Cualquiera*, *Acción*, *Bonus*, *Reacción*.
  - Comprueba que la lista de conjuros se filtra adecuadamente.
- [ ] **4.5 Descansos**:
  - Prueba el botón **Descanso Corto** y **Descanso Largo** verificando la recuperación de puntos de golpe y ranuras.

---

## 🧪 Fase 5: Configuración e Idioma (Settings View)

Navega a la pestaña **Ajustes / Configuración**.

- [ ] **5.1 Selector de Idioma (ES / EN)**:
  - Cambia el idioma entre **Español (ES)** e **English (SRD 5.2 EN)**.
  - Comprueba que los conjuros y dotes muestran los nombres en inglés en los encabezados secundarios o principales según la preferencia.
- [ ] **5.2 Estado de Conexión TaleSpire**:
  - Verifica el indicador de estado de TaleSpire. Si TaleSpire está ejecutándose en el equipo con el puerto activo, el bridge debe indicar estado conectado o listo.

---

## 🛠️ Guía Rápida para Solución de Problemas

| Síntoma | Causa Posible | Solución |
| :--- | :--- | :--- |
| **La imagen de retrato no cambia tras subirla** | Caché del navegador local o formato no soportado. | Los formatos recomendados son `.png`, `.jpg` y `.webp`. La versión actual actualiza el estado directamente en memoria y guarda en SQLite. |
| **La API de imagen devuelve error 401** | API Key no válida o expirada. | Abre el panel de *Configuración API* en el modal de retrato e introduce una API Key válida del proveedor seleccionado. |
| **Deseo usar Midjourney o ChatGPT externamente** | Flujo externo sin API directa. | Haz clic en **Copiar Prompt** dentro del modal, genérala en Midjourney/Discord o ChatGPT, copia el enlace de la imagen resultante y pégalo en el recuadro *"O pega una URL o Base64 directamente"*, luego haz clic en *"Aplicar a la Ficha"*. |
