# Repositorio OKF D&D 5e (Open Knowledge Format)

Base de conocimiento departamentalizada, atómica y estructurada para **D&D 5ª Edición (PHB 2024, Xanathar, Tasha)**.

Diseñada para:
1. Búsqueda semántica e indexación ultrarrápida por Inteligencias Artificiales y motores locales (<5ms).
2. Autocompletado modular de conjuros, rasgos, dotes y clases en la aplicación web y en la versión de escritorio en Python/Flet.
3. Desacoplamiento total de los pesados archivos PDF de 120 MB en entidades Markdown atómicas con metadatos estructurados (`YAML Frontmatter`).

## Taxonomía y Directorios
- `conjuros/`: Ficheros individuales por nivel (trucos a nivel 9) con datos de tiempo, alcance, componentes, escuela y daño.
- `clases/`: Progresión nivel 1 a 20 y carpeta `subclases/`.
- `especies_y_linajes/`: Razas, subrazas y magia innata.
- `dotes/`: Dotes de origen y generales con reglas oficiales.
- `trasfondos/`: Historias de personaje.
- `equipo_y_armamento/`: Tablas de armas, armaduras y equipo.
- `reglas_y_mecanicas/`: Reglas oficiales de combate, salvaciones y descansos.
- `index_metadata.json`: Catálogo maestro de entidades para búsqueda indexada instantánea.
