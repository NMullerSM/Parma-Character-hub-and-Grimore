"""
Script de prueba para analizar el 100% de los conjuros de PHB 2024.
"""
import pymupdf
import re
import sys

doc = pymupdf.open("Manual del Jugador 2024.pdf")

# Unir todo el texto de las páginas 240 a 344 (páginas impresas 241 a 345)
# Preservando saltos de página con marcador especial para seguimiento
full_text = ""
page_map = [] # lista de (pos_inicio, num_pagina)

for p in range(240, 345):
    txt = doc[p].get_text()
    pos = len(full_text)
    page_map.append((pos, p + 1))
    full_text += txt + "\n\n"

doc.close()

def get_page_for_pos(pos):
    current_p = 241
    for start_pos, p_num in page_map:
        if pos >= start_pos:
            current_p = p_num
        else:
            break
    return current_p

# Patrón de encabezado de conjuro:
# Nombre en MAYÚSCULAS seguido de Escuela y Nivel con clases entre paréntesis
# Ej:
# ABRIR
# Transmutación de nivel 2 (bardo, hechicero, mago)
# o
# AGARRE ELECTRIZANTE
# Truco de evocación (hechicero, mago)

header_pattern = re.compile(
    r'(?:^|\n)([A-ZÁÉÍÓÚÑ\s\/\-\'\’]{2,45})\s*\n'
    r'((?:Truco de\s+(?:abjuración|adivinación|conjuración|encantamiento|evocación|ilusionismo|nigromancia|transmutación)|'
    r'(?:Abjuración|Adivinación|Conjuración|Encantamiento|Evocación|Ilusionismo|Nigromancia|Transmutación)\s+de\s+nivel\s+[1-9])'
    r'(?:\s*\(([^\)]+)\))?)',
    re.IGNORECASE | re.MULTILINE
)

matches = list(header_pattern.finditer(full_text))
print(f"Total coincidencias brutas de encabezado encontradas: {len(matches)}")

parsed_spells = []
for i, m in enumerate(matches):
    name = m.group(1).strip()
    # Limpiar posibles prefijos no deseados (ej. números de página o restos de columnas)
    lines = [l.strip() for l in name.splitlines() if l.strip()]
    if lines:
        name = lines[-1] # La última línea es el nombre real del conjuro

    # Descartar falsos positivos
    if name in ["CAPÍTULO", "CONJUROS", "DESCRIPCIONES DE CONJUROS", "APÉNDICE A"]:
        continue
    if len(name) < 2 or len(name) > 40:
        continue

    school_line = m.group(2).strip()
    classes_raw = m.group(3) or ""

    # Determinar rango de texto para este conjuro (hasta el siguiente encabezado)
    start_body = m.end()
    end_body = matches[i + 1].start() if (i + 1 < len(matches)) else len(full_text)
    body_raw = full_text[start_body:end_body].strip()

    # Parsear escuela, nivel y clases
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

    # Atributos de metadatos (Tiempo, Alcance, Componentes, Duración)
    time_m = re.search(r'Tiempo de lanzamiento:\s*([^\n]+)', body_raw, re.IGNORECASE)
    range_m = re.search(r'Alcance:\s*([^\n]+)', body_raw, re.IGNORECASE)
    comp_m = re.search(r'Componentes:\s*([^\n]+(?:\n\s*[^\n]+)?)', body_raw, re.IGNORECASE)
    dur_m = re.search(r'Duración:\s*([^\n]+)', body_raw, re.IGNORECASE)

    casting_time = time_m.group(1).strip() if time_m else "1 acción"
    spell_range = range_m.group(1).strip() if range_m else "18 m"
    components = comp_m.group(1).strip().replace("\n", " ") if comp_m else "V, S"
    duration = dur_m.group(1).strip() if dur_m else "Instantáneo"

    # Concentración y Ritual
    concentration = "concentración" in duration.lower() or "concentracion" in duration.lower()
    ritual = "ritual" in casting_time.lower() or "ritual" in school_line.lower()

    # Limpiar cuerpo: remover las líneas de metadatos
    body_clean = body_raw
    for prefix in [time_m, range_m, comp_m, dur_m]:
        if prefix:
            body_clean = body_clean.replace(prefix.group(0), "")
    body_clean = body_clean.strip()

    # Detectar texto de niveles superiores
    higher_levels = ""
    upcast_m = re.search(r'(Con un espacio de conjuro de nivel superior\..*|Al lanzarlo a un nivel superior\..*|Efecto a niveles superiores\..*)', body_clean, re.DOTALL | re.IGNORECASE)
    if upcast_m:
        higher_levels = upcast_m.group(1).strip()
        body_clean = body_clean[:upcast_m.start()].strip()

    page_num = get_page_for_pos(m.start())

    parsed_spells.append({
        "name": name.title(),
        "level": level,
        "school": school,
        "classes": classes,
        "casting_time": casting_time,
        "range": spell_range,
        "components": components,
        "duration": duration,
        "concentration": concentration,
        "ritual": ritual,
        "description": body_clean,
        "higher_levels": higher_levels,
        "page": page_num
    })

print(f"Total conjuros parseados con éxito: {len(parsed_spells)}")

# Muestra estadística de clases y niveles
from collections import Counter
lvl_counts = Counter(s["level"] for s in parsed_spells)
print("Distribución por nivel:", sorted(lvl_counts.items()))

class_counts = Counter(c for s in parsed_spells for c in s["classes"])
print("Distribución por clase:", class_counts.most_common())

# Verificar si hay conjuros sin clases
no_classes = [s["name"] for s in parsed_spells if not s["classes"]]
print(f"Conjuros sin clases detectadas: {len(no_classes)}")
if no_classes:
    print("Muestra sin clases:", no_classes[:10])

# Muestra de primeros 5 conjuros parseados
print("\n--- Muestra de primeros 3 conjuros parseados ---")
for s in parsed_spells[:3]:
    print(f"[{s['name']}] Nivel {s['level']} {s['school']} | Clases: {s['classes']} | Pág: {s['page']}")
    print(f"  Tiempo: {s['casting_time']} | Alcance: {s['range']} | Duración: {s['duration']}")
    print(f"  Desc: {s['description'][:150]}...")
    if s["higher_levels"]:
        print(f"  Upcast: {s['higher_levels'][:100]}...")
    print()
