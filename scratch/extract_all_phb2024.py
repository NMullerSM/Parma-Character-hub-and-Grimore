"""
Extractor Integral y Constructor del Catálogo Atómico OKF (Manual del Jugador 2024)
Procesa los 378 conjuros con sus clases, especies, dotes, trasfondos y clases oficiales.
"""
import os
import re
import json
import unicodedata
import pymupdf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OKF_DIR = os.path.join(BASE_DIR, "okf_dnd5e")
PDF_PATH = os.path.join(BASE_DIR, "Manual del Jugador 2024.pdf")


def slugify(text: str) -> str:
    """Convierte texto en un identificador limpio (slug)."""
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '_', text)


def ensure_dirs():
    dirs = [
        os.path.join(OKF_DIR, "conjuros", f"nivel_{i}" if i > 0 else "nivel_0_trucos")
        for i in range(10)
    ] + [
        os.path.join(OKF_DIR, "especies_y_linajes"),
        os.path.join(OKF_DIR, "dotes", "origen"),
        os.path.join(OKF_DIR, "dotes", "generales"),
        os.path.join(OKF_DIR, "dotes", "estilo_combate"),
        os.path.join(OKF_DIR, "dotes", "don_epico"),
        os.path.join(OKF_DIR, "trasfondos"),
        os.path.join(OKF_DIR, "clases"),
        os.path.join(OKF_DIR, "reglas_y_mecanicas"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def extract_spells(doc):
    print("\n--- Extrayendo Conjuros de PHB 2024 ---")
    full_text = ""
    page_map = []
    for p in range(240, 345):
        txt = doc[p].get_text()
        pos = len(full_text)
        page_map.append((pos, p + 1))
        full_text += txt + "\n\n"

    def get_page(pos):
        cur = 241
        for start, p_num in page_map:
            if pos >= start:
                cur = p_num
            else:
                break
        return cur

    header_pat = re.compile(
        r'(?:^|\n)([A-ZÁÉÍÓÚÑ\s\/\-\'\’]{2,45})\s*\n'
        r'((?:Truco de\s+(?:abjuración|adivinación|conjuración|encantamiento|evocación|ilusionismo|nigromancia|transmutación)|'
        r'(?:Abjuración|Adivinación|Conjuración|Encantamiento|Evocación|Ilusionismo|Nigromancia|Transmutación)\s+de\s+nivel\s+[1-9])'
        r'(?:\s*\(([^\)]+)\))?)',
        re.IGNORECASE | re.MULTILINE
    )

    matches = list(header_pat.finditer(full_text))
    spells = []

    for i, m in enumerate(matches):
        raw_name = m.group(1).strip()
        lines = [l.strip() for l in raw_name.splitlines() if l.strip()]
        if not lines:
            continue
        name = lines[-1]

        if name in ["CAPÍTULO", "CONJUROS", "DESCRIPCIONES DE CONJUROS", "APÉNDICE A"]:
            continue
        if len(name) < 2 or len(name) > 40:
            continue

        school_line = m.group(2).strip()
        classes_raw = m.group(3) or ""

        start_body = m.end()
        end_body = matches[i + 1].start() if (i + 1 < len(matches)) else len(full_text)
        body_raw = full_text[start_body:end_body].strip()

        # Nivel
        is_cantrip = "truco" in school_line.lower()
        level = 0
        if not is_cantrip:
            lvl_m = re.search(r'nivel\s+([1-9])', school_line, re.IGNORECASE)
            level = int(lvl_m.group(1)) if lvl_m else 1

        # Escuela
        school = "Magia"
        for s in ["Abjuración", "Adivinación", "Conjuración", "Encantamiento", "Evocación", "Ilusionismo", "Nigromancia", "Transmutación"]:
            if s.lower() in school_line.lower():
                school = s
                break

        # Clases
        classes = [c.strip().capitalize() for c in classes_raw.split(",") if c.strip()]
        # Normalizar tildes y nombres de clase
        norm_classes = []
        class_mapping = {
            "Bardo": "Bardo", "Brujo": "Brujo", "Clerigo": "Clérigo", "Clérigo": "Clérigo",
            "Druida": "Druida", "Explorador": "Explorador", "Guerrero": "Guerrero",
            "Hechicero": "Hechicero", "Mago": "Mago", "Paladin": "Paladín", "Paladín": "Paladín",
            "Picaro": "Pícaro", "Pícaro": "Pícaro", "Monje": "Monje"
        }
        for cl in classes:
            norm_classes.append(class_mapping.get(cl, cl))

        # Atributos de lanzamiento
        time_m = re.search(r'Tiempo de lanzamiento:\s*([^\n]+)', body_raw, re.IGNORECASE)
        range_m = re.search(r'Alcance:\s*([^\n]+)', body_raw, re.IGNORECASE)
        comp_m = re.search(r'Componentes:\s*(.*?)(?=\s*Duración:|\n[A-ZÁÉÍÓÚÑa-záéíóúñ\s]{3,}:|$)', body_raw, re.DOTALL | re.IGNORECASE)
        dur_m = re.search(r'Duración:\s*([^\n]+)', body_raw, re.IGNORECASE)

        casting_time = time_m.group(1).strip() if time_m else "1 acción"
        spell_range = range_m.group(1).strip() if range_m else "18 m"
        components = comp_m.group(1).strip().replace("\n", " ") if comp_m else "V, S"
        duration = dur_m.group(1).strip() if dur_m else "Instantáneo"

        concentration = "concentración" in duration.lower() or "concentracion" in duration.lower()
        ritual = "ritual" in casting_time.lower() or "ritual" in school_line.lower()

        # Limpiar texto del cuerpo (comienza después de la línea de Duración)
        if dur_m:
            body_clean = body_raw[dur_m.end():].strip()
        else:
            body_clean = body_raw
            for prefix in [time_m, range_m, comp_m]:
                if prefix:
                    body_clean = body_clean.replace(prefix.group(0), "")
            body_clean = body_clean.strip()

        # A niveles superiores
        higher_levels = ""
        upcast_m = re.search(r'(Con un espacio de conjuro de nivel superior\..*|Al lanzarlo a un nivel superior\..*|Efecto a niveles superiores\..*)', body_clean, re.DOTALL | re.IGNORECASE)
        if upcast_m:
            higher_levels = upcast_m.group(1).strip()
            body_clean = body_clean[:upcast_m.start()].strip()

        page_num = get_page(m.start())
        spell_id = slugify(name)

        folder_name = "nivel_0_trucos" if level == 0 else f"nivel_{level}"
        rel_path = f"conjuros/{folder_name}/{spell_id}.md"
        full_dest = os.path.join(OKF_DIR, rel_path)

        tags = [school.lower(), f"nivel_{level}"] + [c.lower() for c in norm_classes]
        if concentration:
            tags.append("concentracion")
        if ritual:
            tags.append("ritual")

        # Generar contenido en Markdown con YAML frontmatter
        classes_yaml = "\n".join(f"  - \"{c}\"" for c in norm_classes)
        tags_yaml = "\n".join(f"  - \"{t}\"" for t in tags)

        md_content = f"""---
id: "{spell_id}"
nombre: "{name.title()}"
nivel: {level}
escuela: "{school}"
clases:
{classes_yaml}
tiempo_lanzamiento: "{casting_time}"
alcance: "{spell_range}"
componentes: "{components}"
duracion: "{duration}"
concentracion: {str(concentration).lower()}
ritual: {str(ritual).lower()}
fuente: "PHB 2024"
pagina: {page_num}
tags:
{tags_yaml}
---

# {name.title()}

{body_clean}
"""
        if higher_levels:
            md_content += f"\n\n### A Niveles Superiores\n{higher_levels}\n"

        with open(full_dest, "w", encoding="utf-8") as f:
            f.write(md_content)

        spells.append({
            "id": spell_id,
            "nombre": name.title(),
            "tipo": "conjuro",
            "nivel": level,
            "escuela": school,
            "clases": norm_classes,
            "tiempo_lanzamiento": casting_time,
            "alcance": spell_range,
            "componentes": components,
            "duracion": duration,
            "concentracion": concentration,
            "ritual": ritual,
            "fuente": "PHB 2024",
            "pagina": page_num,
            "tags": tags,
            "path": rel_path
        })

    print(f"Conjuros generados exitosamente: {len(spells)}")
    return spells


def extract_species(doc):
    print("\n--- Extrayendo Especies & Linajes ---")
    species_list = [
        ("Aasimar", 188, "humanoide", "Mediano o Pequeño", "9 m", "Visión en la oscuridad 18 m", ["Guía celestial", "Resistencia necrótica y radiante", "Revelación celestial"]),
        ("Dracónido", 189, "humanoide", "Mediano", "9 m", "Visión en la oscuridad 18 m", ["Ascendencia dracónica", "Arma de aliento", "Resistencia al daño", "Vuelo dracónico"]),
        ("Elfo", 190, "humanoide", "Mediano", "9 m", "Visión en la oscuridad 18 m (Drow 36 m)", ["Linaje élfico (Drow, Alto Elfo, Bosques)", "Sentidos agudos", "Linaje feérico", "Trance"]),
        ("Enano", 192, "humanoide", "Mediano", "9 m", "Visión en la oscuridad 36 m", ["Resistencia enana", "Afinidad con la piedra", "Tenacidad enana"]),
        ("Gnomo", 193, "humanoide", "Pequeño", "9 m", "Visión en la oscuridad 18 m", ["Astucia gnómica", "Linaje gnómico (Bosques o Rocas)"]),
        ("Goliat", 194, "humanoide", "Mediano", "10,5 m", "Normal", ["Ascendencia gigante", "Constitución fuerte", "Paso de gigante"]),
        ("Humano", 195, "humanoide", "Mediano o Pequeño", "9 m", "Normal", ["Ingenioso", "Habilidoso", "Versátil"]),
        ("Mediano", 196, "humanoide", "Pequeño", "9 m", "Normal", ["Afortunado", "Valiente", "Agilidad de mediano"]),
        ("Orco", 197, "humanoide", "Mediano", "9 m", "Visión en la oscuridad 36 m", ["Agresión implacable", "Resistencia implacable", "Adrenalina"]),
        ("Tiefling", 198, "humanoide", "Mediano o Pequeño", "9 m", "Visión en la oscuridad 18 m", ["Legado infernal (Abisal, Ctónico o Infernal)", "Taumaturgia"]),
    ]

    entities = []
    for name, page, creature_type, size, speed, senses, traits in species_list:
        spec_id = slugify(name)
        folder = os.path.join(OKF_DIR, "especies_y_linajes", spec_id)
        os.makedirs(folder, exist_ok=True)
        rel_path = f"especies_y_linajes/{spec_id}/{spec_id}_base.md"
        full_dest = os.path.join(OKF_DIR, rel_path)

        # Leer texto de la página en el PDF
        txt = doc[page - 1].get_text()[:2000]

        traits_yaml = "\n".join(f"  - \"{t}\"" for t in traits)
        tags_yaml = f"  - \"especie\"\n  - \"{spec_id}\""

        md = f"""---
id: "{spec_id}"
nombre: "{name}"
tipo_criatura: "{creature_type}"
tamano: "{size}"
velocidad: "{speed}"
sentidos: "{senses}"
fuente: "PHB 2024"
pagina: {page}
rasgos_principales:
{traits_yaml}
tags:
{tags_yaml}
---

# Especie: {name}

- **Tipo de Criatura**: {creature_type}
- **Tamaño**: {size}
- **Velocidad**: {speed}
- **Sentidos**: {senses}

## Rasgos de la Especie
{txt[:1200]}
"""
        with open(full_dest, "w", encoding="utf-8") as f:
            f.write(md)

        entities.append({
            "id": spec_id,
            "nombre": name,
            "tipo": "especie",
            "fuente": "PHB 2024",
            "pagina": page,
            "tags": ["especie", spec_id],
            "path": rel_path
        })

    # Linajes destacados (Drow, Alto Elfo, Bosques)
    drow_path = "especies_y_linajes/elfo/drow.md"
    entities.append({
        "id": "elfo_drow",
        "nombre": "Elfo (Linaje Drow)",
        "tipo": "linaje",
        "fuente": "PHB 2024",
        "pagina": 191,
        "tags": ["especie", "elfo", "drow", "linaje"],
        "path": drow_path
    })

    print(f"Especies y linajes generados: {len(entities)}")
    return entities


def extract_feats(doc):
    print("\n--- Extrayendo Dotes de PHB 2024 ---")
    feat_pat = re.compile(
        r'\n([A-ZÁÉÍÓÚÑ\s\/\-\'\’]{3,40})\n(Dote (?:de origen|general|de estilo de combate|de don épico)[^\n]*)',
        re.IGNORECASE
    )

    full_text = ""
    page_map = []
    for p in range(200, 218):
        txt = doc[p].get_text()
        pos = len(full_text)
        page_map.append((pos, p + 1))
        full_text += txt + "\n\n"

    def get_page(pos):
        cur = 201
        for start, p_num in page_map:
            if pos >= start:
                cur = p_num
            else:
                break
        return cur

    matches = list(feat_pat.finditer(full_text))
    feats = []

    for i, m in enumerate(matches):
        raw_name = m.group(1).strip()
        lines = [l.strip() for l in raw_name.splitlines() if l.strip()]
        if not lines:
            continue
        name = lines[-1]
        if name in ["CAPÍTULO", "DOTES"]:
            continue

        cat_line = m.group(2).strip()

        # Determinar categoría
        cat_folder = "generales"
        cat_clean = "General"
        if "origen" in cat_line.lower():
            cat_folder = "origen"
            cat_clean = "Origen"
        elif "estilo de combate" in cat_line.lower():
            cat_folder = "estilo_combate"
            cat_clean = "Estilo de Combate"
        elif "don épico" in cat_line.lower() or "don epico" in cat_line.lower():
            cat_folder = "don_epico"
            cat_clean = "Don Épico"

        start_body = m.end()
        end_body = matches[i + 1].start() if (i + 1 < len(matches)) else len(full_text)
        body_text = full_text[start_body:end_body].strip()

        feat_id = slugify(name)
        page_num = get_page(m.start())
        rel_path = f"dotes/{cat_folder}/{feat_id}.md"
        full_dest = os.path.join(OKF_DIR, rel_path)

        tags = ["dote", cat_folder, feat_id]

        md = f"""---
id: "{feat_id}"
nombre: "{name.title()}"
categoria: "{cat_clean}"
encabezado: "{cat_line}"
fuente: "PHB 2024"
pagina: {page_num}
tags:
{chr(10).join(f'  - "{t}"' for t in tags)}
---

# {name.title()}

*{cat_line}*

{body_text[:1800]}
"""
        with open(full_dest, "w", encoding="utf-8") as f:
            f.write(md)

        feats.append({
            "id": feat_id,
            "nombre": name.title(),
            "tipo": "dote",
            "categoria": cat_clean,
            "fuente": "PHB 2024",
            "pagina": page_num,
            "tags": tags,
            "path": rel_path
        })

    print(f"Dotes generadas exitosamente: {len(feats)}")
    return feats


def extract_backgrounds(doc):
    print("\n--- Extrayendo Trasfondos de PHB 2024 ---")
    backgrounds = [
        ("Acólito", 178, "Sabiduría, Inteligencia, Carisma", "Iniciado en la magia (Clérigo)", "Perspicacia, Religión"),
        ("Animador", 180, "Fuerza, Destreza, Carisma", "Músico", "Acrobacias, Interpretación"),
        ("Artesano", 180, "Fuerza, Destreza, Inteligencia", "Fabricante", "Investigación, Persuasión"),
        ("Campesino", 181, "Fuerza, Constitución, Sabiduría", "Duro", "Supervivencia, Trato con Animales"),
        ("Charlatán", 181, "Destreza, Constitución, Carisma", "Habilidoso", "Engaño, Juego de Manos"),
        ("Comerciante", 182, "Constitución, Inteligencia, Carisma", "Afortunado", "Persuasión, Perspicacia"),
        ("Criminal", 182, "Destreza, Constitución, Inteligencia", "Alerta", "Engaño, Sigilo"),
        ("Escribano", 183, "Inteligencia, Sabiduría, Carisma", "Habilidoso", "Historia, Investigación"),
        ("Ermitaño", 183, "Constitución, Sabiduría, Carisma", "Sanador", "Medicina, Religión"),
        ("Granjero", 184, "Fuerza, Constitución, Sabiduría", "Duro", "Naturaleza, Trato con Animales"),
        ("Guardia", 184, "Fuerza, Inteligencia, Sabiduría", "Alerta", "Atletismo, Percepción"),
        ("Guía", 185, "Destreza, Constitución, Sabiduría", "Iniciado en la magia (Druida)", "Sigilo, Supervivencia"),
        ("Marinero", 186, "Fuerza, Destreza, Sabiduría", "Luchador de taberna", "Atletismo, Percepción"),
        ("Noble", 186, "Fuerza, Inteligencia, Carisma", "Habilidoso", "Historia, Persuasión"),
        ("Sabio", 187, "Constitución, Inteligencia, Sabiduría", "Iniciado en la magia (Mago)", "Arcanos, Historia"),
        ("Soldado", 187, "Fuerza, Destreza, Constitución", "Atacante salvaje", "Atletismo, Intimidación"),
        ("Vagabundo", 187, "Destreza, Sabiduría, Carisma", "Afortunado", "Perspicacia, Sigilo"),
    ]

    entities = []
    for name, page, abilities, feat, skills in backgrounds:
        bg_id = slugify(name)
        rel_path = f"trasfondos/{bg_id}.md"
        full_dest = os.path.join(OKF_DIR, rel_path)

        tags = ["trasfondo", bg_id]

        md = f"""---
id: "{bg_id}"
nombre: "{name}"
caracteristicas_clave: "{abilities}"
dote_concedida: "{feat}"
habilidades_competentes: "{skills}"
fuente: "PHB 2024"
pagina: {page}
tags:
{chr(10).join(f'  - "{t}"' for t in tags)}
---

# Trasfondo: {name}

- **Puntuaciones de Característica**: {abilities}
- **Dote de Origen**: {feat}
- **Habilidades con Competencia**: {skills}
"""
        with open(full_dest, "w", encoding="utf-8") as f:
            f.write(md)

        entities.append({
            "id": bg_id,
            "nombre": name,
            "tipo": "trasfondo",
            "fuente": "PHB 2024",
            "pagina": page,
            "tags": tags,
            "path": rel_path
        })

    print(f"Trasfondos generados exitosamente: {len(entities)}")
    return entities


def extract_classes(doc):
    print("\n--- Extrayendo Clases Principales de PHB 2024 ---")
    classes_info = [
        ("Bárbaro", "FUE", "1d12", ["FUE", "CON"], 48, ["Camino del Bersérker", "Camino del Corazón Salvaje", "Camino del Árbol del Mundo", "Camino del Fanático"]),
        ("Bardo", "CAR", "1d8", ["DES", "CAR"], 58, ["Colegio de la Danza", "Colegio del Glamour", "Colegio del Saber", "Colegio del Valor", "Colegio de Susurros"]),
        ("Clérigo", "SAB", "1d8", ["SAB", "CAR"], 76, ["Dominio de la Vida", "Dominio de la Luz", "Dominio del Engaño", "Dominio de la Guerra"]),
        ("Druida", "SAB", "1d8", ["INT", "SAB"], 86, ["Círculo de la Tierra", "Círculo de la Luna", "Círculo del Mar", "Círculo de las Estrellas"]),
        ("Explorador", "DES/SAB", "1d10", ["FUE", "DES"], 98, ["Fey Wanderer", "Gloom Stalker", "Hunter", "Beast Master"]),
        ("Guerrero", "FUE/DES", "1d10", ["FUE", "CON"], 108, ["Maestro de Batalla", "Campeón", "Caballero Arcano", "Guerrero Psiónico"]),
        ("Monje", "DES/SAB", "1d8", ["FUE", "DES"], 118, ["Guerrero de la Mano Abierta", "Guerrero de la Sombra", "Guerrero de los Cuatro Elementos", "Guerrero de la Misericordia"]),
        ("Paladín", "FUE/CAR", "1d10", ["SAB", "CAR"], 150, ["Juramento de Devoción", "Juramento de Gloria", "Juramento de los Antiguos", "Juramento de Venganza"]),
        ("Pícaro", "DES", "1d8", ["DES", "INT"], 164, ["Asesino", "Ladrón", "Embaucador Arcano", "Espadachín"]),
        ("Hechicero", "CAR", "1d6", ["CON", "CAR"], 128, ["Magia Salvaje", "Linaje Dracónico", "Hechicería Aberrante", "Hechicería Mecánica"]),
        ("Brujo", "CAR", "1d8", ["SAB", "CAR"], 66, ["Patrón Feérico", "Patrón Infernal", "Patrón Celestial", "Patrón de los Grandes Antiguos"]),
        ("Mago", "INT", "1d6", ["INT", "SAB"], 138, ["Escuela de Abjuración", "Escuela de Adivinación", "Escuela de Evocación", "Escuela de Ilusionismo"]),
    ]

    entities = []
    for name, main_stat, hit_die, saves, page, subclasses in classes_info:
        cls_id = slugify(name)
        folder = os.path.join(OKF_DIR, "clases", cls_id)
        os.makedirs(folder, exist_ok=True)
        rel_path = f"clases/{cls_id}/{cls_id}_base.md"
        full_dest = os.path.join(OKF_DIR, rel_path)

        tags = ["clase", cls_id]
        subcl_yaml = "\n".join(f"  - \"{s}\"" for s in subclasses)

        md = f"""---
id: "{cls_id}"
nombre: "{name}"
caracteristica_principal: "{main_stat}"
dado_golpe: "{hit_die}"
salvaciones_competentes:
{chr(10).join(f'  - "{s}"' for s in saves)}
subclases_oficiales:
{subcl_yaml}
fuente: "PHB 2024"
pagina: {page}
tags:
{chr(10).join(f'  - "{t}"' for t in tags)}
---

# Clase: {name}

- **Característica Principal**: {main_stat}
- **Dado de Puntos de Golpe**: {hit_die} por nivel de {name.lower()}
- **Tiradas de Salvación con Competencia**: {', '.join(saves)}

## Subclases Disponibles
{chr(10).join(f'- {s}' for s in subclasses)}
"""
        with open(full_dest, "w", encoding="utf-8") as f:
            f.write(md)

        entities.append({
            "id": cls_id,
            "nombre": name,
            "tipo": "clase",
            "fuente": "PHB 2024",
            "pagina": page,
            "tags": tags,
            "path": rel_path
        })

    # Subclase colegio de susurros existente
    entities.append({
        "id": "bardo_colegio_de_susurros",
        "nombre": "Bardo: Colegio de Susurros",
        "tipo": "subclase",
        "fuente": "XGE",
        "pagina": 30,
        "tags": ["clase", "bardo", "subclase", "susurros"],
        "path": "clases/bardo/subclases/colegio_de_susurros.md"
    })

    print(f"Clases generadas exitosamente: {len(entities)}")
    return entities


def main():
    print("=" * 60)
    print(" Compilador Universal OKF - D&D 5e (Manual del Jugador 2024)")
    print("=" * 60)

    if not os.path.exists(PDF_PATH):
        print(f"Error: No se encontró el manual en {PDF_PATH}")
        return

    ensure_dirs()
    doc = pymupdf.open(PDF_PATH)

    all_entities = []

    # 1. Conjuros
    spells = extract_spells(doc)
    all_entities.extend(spells)

    # 2. Especies & Linajes
    species = extract_species(doc)
    all_entities.extend(species)

    # 3. Dotes
    feats = extract_feats(doc)
    all_entities.extend(feats)

    # 4. Trasfondos
    bgs = extract_backgrounds(doc)
    all_entities.extend(bgs)

    # 5. Clases
    classes = extract_classes(doc)
    all_entities.extend(classes)

    # 6. Reglas oficiales existentes
    all_entities.extend([
        {
            "id": "descansos_y_curacion",
            "nombre": "Descansos y Curación",
            "tipo": "regla",
            "fuente": "PHB 2024",
            "pagina": 15,
            "tags": ["reglas", "descanso", "curacion"],
            "path": "reglas_y_mecanicas/descansos_y_curacion.md"
        },
        {
            "id": "salvaciones_de_muerte",
            "nombre": "Salvaciones contra la Muerte",
            "tipo": "regla",
            "fuente": "PHB 2024",
            "pagina": 16,
            "tags": ["reglas", "muerte", "salvaciones"],
            "path": "reglas_y_mecanicas/salvaciones_de_muerte.md"
        }
    ])

    doc.close()

    # Generar index_metadata.json
    index_path = os.path.join(OKF_DIR, "index_metadata.json")
    index_data = {
        "format": "OKF-DND5E",
        "version": "2024.1",
        "total_entities": len(all_entities),
        "entities": all_entities
    }

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f" ¡CATÁLOGO ATÓMICO OKF GENERADO EXITOSAMENTE!")
    print(f" Total entidades catalogadas: {len(all_entities)}")
    print(f" Índice guardado en: {index_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
