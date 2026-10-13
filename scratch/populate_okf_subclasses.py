"""
Script para poblar las subclases atómicas oficiales de D&D 5e en okf_dnd5e/clases/
Cubre manuales PHB 2024, Caldero de Tasha para Todo (TCE) y Guía de Xanathar (XGE).
Cada subclase se guarda con frontmatter YAML atómico y descripción Markdown,
y se actualiza index_metadata.json de forma unificada.
"""
import os
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OKF_DIR = os.path.join(BASE_DIR, "okf_dnd5e")
CLASSES_DIR = os.path.join(OKF_DIR, "clases")
INDEX_PATH = os.path.join(OKF_DIR, "index_metadata.json")

SUBCLASSES = [
    # BÁRBARO
    {"class": "barbaro", "class_name": "Bárbaro", "file": "berserker.md", "id": "barbaro_berserker",
     "nombre": "Senda del Bersérker", "nombre_en": "Path of the Berserker", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["bárbaro", "furia", "daño", "marcial", "phb2024"],
     "desc": "El bersérker canaliza su furia hacia una vorágine destructiva de violencia incontrolable, asestando golpes adicionales devastadores."},
    {"class": "barbaro", "class_name": "Bárbaro", "file": "corazon_salvaje.md", "id": "barbaro_corazon_salvaje",
     "nombre": "Senda del Corazón Salvaje", "nombre_en": "Path of the Wild Heart", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["bárbaro", "totem", "animal", "resistencia", "phb2024"],
     "desc": "Sintonizado con los espíritus totémicos de la naturaleza (Oso, Águila, Lobo), adquiere resistencias elementales y sentidos agudos."},
    {"class": "barbaro", "class_name": "Bárbaro", "file": "arbol_del_mundo.md", "id": "barbaro_arbol_del_mundo",
     "nombre": "Senda del Árbol del Mundo", "nombre_en": "Path of the World Tree", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["bárbaro", "yggdrasil", "vitalidad", "teletransporte", "phb2024"],
     "desc": "Conectado a las raíces de Yggdrasil, otorga vitalidad temporal a sus aliados y manipula ramas dimensionales en el campo de batalla."},
    {"class": "barbaro", "class_name": "Bárbaro", "file": "zelote.md", "id": "barbaro_zelote",
     "nombre": "Senda del Zelote", "nombre_en": "Path of the Zealot", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["bárbaro", "divino", "inmortal", "daño radiante", "phb2024"],
     "desc": "Imbuido del fervor de una deidad, inflige daño radiante o necrótico en cada embate y es prácticamente imposible de matar mientras ruge de furia."},
    {"class": "barbaro", "class_name": "Bárbaro", "file": "bestia.md", "id": "barbaro_bestia",
     "nombre": "Senda de la Bestia", "nombre_en": "Path of the Beast", "fuente": "Caldero de Tasha para Todo", "nivel": 3,
     "tags": ["bárbaro", "tasha", "mordisco", "garras", "licantropía"],
     "desc": "Transforma su cuerpo durante la furia manifestando armas naturales: fauces devoradoras de vida, garras desgarradoras o cola espinosa."},

    # BARDO
    {"class": "bardo", "class_name": "Bardo", "file": "conocimiento.md", "id": "bardo_conocimiento",
     "nombre": "Colegio del Conocimiento", "nombre_en": "College of Lore", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["bardo", "sabiduría", "palabras cortantes", "secretos mágicos", "phb2024"],
     "desc": "Buscadores de secretos antiguos y verdades ocultas, dominan las Palabras Cortantes para sabotear tiradas enemigas y roban conjuros de cualquier clase."},
    {"class": "bardo", "class_name": "Bardo", "file": "valor.md", "id": "bardo_valor",
     "nombre": "Colegio del Valor", "nombre_en": "College of Valor", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["bardo", "marcial", "armadura media", "combate", "phb2024"],
     "desc": "Héroes del frente de batalla que cantan hazañas heroicas, ganan competencia con armaduras medias, escudos y armas marciales con Ataque Adicional."},
    {"class": "bardo", "class_name": "Bardo", "file": "elocuencia.md", "id": "bardo_elocuencia",
     "nombre": "Colegio de la Elocuencia", "nombre_en": "College of Eloquence", "fuente": "Caldero de Tasha para Todo", "nivel": 3,
     "tags": ["bardo", "tasha", "persuasión", "oratoria", "inspiración infalible"],
     "desc": "Maestros absolutos de la retórica, jamás obtienen menos de 10 en Persuasión o Engaño y sus dados de inspiración no se gastan si el receptor falla."},
    {"class": "bardo", "class_name": "Bardo", "file": "glamour.md", "id": "bardo_glamour",
     "nombre": "Colegio del Glamour", "nombre_en": "College of Glamour", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["bardo", "fey", "fascinación", "presencia majestuosa", "phb2024"],
     "desc": "Tejido con la belleza hipnótica de las Tierras Feéricas, cautiva a multitudes, reposiciona a sus aliados en combate y comanda voluntades."},
    {"class": "bardo", "class_name": "Bardo", "file": "espadas.md", "id": "bardo_espadas",
     "nombre": "Colegio de las Espadas", "nombre_en": "College of Swords", "fuente": "Guia de Xanathar Para Todo", "nivel": 3,
     "tags": ["bardo", "xanathar", "duelo", "florituras", "armas sutiles"],
     "desc": "Duelistas acrobáticos que convierten su propia arma en un foco arcano, ejecutando Florituras de Espada que incrementan su CA y daño."},

    # CLÉRIGO
    {"class": "clerigo", "class_name": "Clérigo", "file": "vida.md", "id": "clerigo_vida",
     "nombre": "Dominio de la Vida", "nombre_en": "Life Domain", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["clérigo", "sanación", "armadura pesada", "vitalidad", "phb2024"],
     "desc": "El conducto supremo de energía restauradora divina, maximiza cada conjuro curativo y protege con armaduras pesadas."},
    {"class": "clerigo", "class_name": "Clérigo", "file": "luz.md", "id": "clerigo_luz",
     "nombre": "Dominio de la Luz", "nombre_en": "Light Domain", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["clérigo", "fuego", "sol", "resplandor", "blaster", "phb2024"],
     "desc": "Portadores del fuego solar purificador, ciegan ataques hostiles con Destello Protector y desatan Bolas de Fuego benditas."},
    {"class": "clerigo", "class_name": "Clérigo", "file": "guerra.md", "id": "clerigo_guerra",
     "nombre": "Dominio de la Guerra", "nombre_en": "War Domain", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["clérigo", "combate", "armas marciales", "guía divina", "phb2024"],
     "desc": "Paladines de la disciplina marcial sagrada, obtienen ataques adicionales de acción adicional y añaden +10 a tiradas de impacto."},
    {"class": "clerigo", "class_name": "Clérigo", "file": "engano.md", "id": "clerigo_engano",
     "nombre": "Dominio del Engaño", "nombre_en": "Trickery Domain", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["clérigo", "ilusión", "sigilo", "duplicado", "phb2024"],
     "desc": "Sirvientes de los dioses bromistas y de la sombra, proyectan un duplicado ilusorio perfecto para lanzar conjuros a distancia."},
    {"class": "clerigo", "class_name": "Clérigo", "file": "crepusculo.md", "id": "clerigo_crepusculo",
     "nombre": "Dominio del Crepúsculo", "nombre_en": "Twilight Domain", "fuente": "Caldero de Tasha para Todo", "nivel": 3,
     "tags": ["clérigo", "tasha", "visión 90m", "aura crepuscular", "vuelo"],
     "desc": "Vigilantes del umbral entre el día y la noche, otorgan visión en oscuridad de 90 m a su grupo y un santuario de puntos de golpe temporales continuos."},
    {"class": "clerigo", "class_name": "Clérigo", "file": "forja.md", "id": "clerigo_forja",
     "nombre": "Dominio de la Forja", "nombre_en": "Forge Domain", "fuente": "Guia de Xanathar Para Todo", "nivel": 3,
     "tags": ["clérigo", "xanathar", "metal", "artesanía", "fuego", "armadura"],
     "desc": "Discípulos de los dioses artesanos, encantan armas y armaduras con magia perenne y obtienen inmunidad absoluta al daño de fuego."},

    # DRUIDA
    {"class": "druida", "class_name": "Druida", "file": "luna.md", "id": "druida_luna",
     "nombre": "Círculo de la Luna", "nombre_en": "Circle of the Moon", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["druida", "forma salvaje", "bestias", "combate", "phb2024"],
     "desc": "Protectores feroces del equilibrio que asumen formas salvajes poderosas como acción adicional, absorbiendo castigo y desgarrando enemigos."},
    {"class": "druida", "class_name": "Druida", "file": "tierra.md", "id": "druida_tierra",
     "nombre": "Círculo de la Tierra", "nombre_en": "Circle of the Land", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["druida", "biomas", "recuperación natural", "elementos", "phb2024"],
     "desc": "Conectados a un bioma específico (Montaña, Pantano, Bosque), recuperan espacios de conjuro en descanso corto y dominan magia elemental."},
    {"class": "druida", "class_name": "Druida", "file": "mar.md", "id": "druida_mar",
     "nombre": "Círculo del Mar", "nombre_en": "Circle of the Sea", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["druida", "tormenta", "agua", "vuelo de vapor", "phb2024"],
     "desc": "Canalizan la furia del océano y la tempestad, rodeándose de una tormenta de spray y olas que empuja enemigos y absorbe frío/rayo."},
    {"class": "druida", "class_name": "Druida", "file": "estrellas.md", "id": "druida_estrellas",
     "nombre": "Círculo de las Estrellas", "nombre_en": "Circle of the Stars", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["druida", "constelaciones", "arquero", "cáliz", "dragón", "phb2024", "tasha"],
     "desc": "Lectores de las constelaciones celestiales, manifiestan tres formas estrelladas (Arquero, Cáliz, Dragón) para disparar luz o sanar sin gastar recursos."},

    # GUERRERO
    {"class": "guerrero", "class_name": "Guerrero", "file": "campeon.md", "id": "guerrero_campeon",
     "nombre": "Campeón", "nombre_en": "Champion", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["guerrero", "crítico 19-20", "atleta notable", "marcial", "phb2024"],
     "desc": "La cúspide de la potencia física bruta, obtiene golpes críticos con 19 y 20 natural, inspiración heroica adicional y regeneración en combate."},
    {"class": "guerrero", "class_name": "Guerrero", "file": "maestro_de_batalla.md", "id": "guerrero_maestro_de_batalla",
     "nombre": "Maestro de Batalla", "nombre_en": "Battle Master", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["guerrero", "maniobras", "dados de superioridad", "táctica", "phb2024"],
     "desc": "Táctico consumado que emplea dados de superioridad d8 para ejecutar maniobras: derribar, desarmar, contraatacar y dirigir a sus compañeros."},
    {"class": "guerrero", "class_name": "Guerrero", "file": "caballero_sobrenatural.md", "id": "guerrero_caballero_sobrenatural",
     "nombre": "Caballero Sobrenatural", "nombre_en": "Eldritch Knight", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["guerrero", "magia", "evocación", "abjuración", "vínculo de arma", "phb2024"],
     "desc": "Combina pericia marcial con magia de mago, vinculándose a sus armas para invocarlas al instante y sustituyendo ataques por trucos ofensivos."},
    {"class": "guerrero", "class_name": "Guerrero", "file": "guerrero_psiquico.md", "id": "guerrero_psiquico",
     "nombre": "Guerrero Psíquico", "nombre_en": "Psi Warrior", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["guerrero", "psiónico", "telequinesis", "escudo mental", "phb2024", "tasha"],
     "desc": "Manipula energía psiónica para impulsar sus golpes con telequinesis, proyectar escudos de fuerza y mover objetos o criaturas con la mente."},
    {"class": "guerrero", "class_name": "Guerrero", "file": "caballero_runico.md", "id": "guerrero_caballero_runico",
     "nombre": "Caballero Rúnico", "nombre_en": "Rune Knight", "fuente": "Caldero de Tasha para Todo", "nivel": 3,
     "tags": ["guerrero", "tasha", "runas", "gigantes", "tamaño grande"],
     "desc": "Graba runas de los gigantes en sus pertrechos y crece mágicamente a tamaño Grande, ganando ventaja en pruebas de Fuerza y daño masivo."},

    # MONJE
    {"class": "monje", "class_name": "Monje", "file": "mano_abierta.md", "id": "monje_mano_abierta",
     "nombre": "Camino de la Mano Abierta", "nombre_en": "Way of the Open Hand", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["monje", "ki", "derribar", "golpe de palma vibrante", "phb2024"],
     "desc": "Perfecciona el control físico absoluto, empujando y derribando enemigos con ráfagas de golpes y dominando el legendario Golpe de Palma Vibrante."},
    {"class": "monje", "class_name": "Monje", "file": "sombras.md", "id": "monje_sombras",
     "nombre": "Camino de las Sombras", "nombre_en": "Way of Shadow", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["monje", "sigilo", "paso sombrío", "oscuridad", "teletransporte", "phb2024"],
     "desc": "Asesinos y espías silenciosos que se teletransportan entre zonas de penumbra y conjuran mantos de oscuridad sobrenatural."},
    {"class": "monje", "class_name": "Monje", "file": "cuatro_elementos.md", "id": "monje_cuatro_elementos",
     "nombre": "Camino de los Cuatro Elementos", "nombre_en": "Warrior of the Elements", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["monje", "fuego", "aire", "agua", "tierra", "alcance", "phb2024"],
     "desc": "Canaliza los cuatro elementos primordiales en su energía desarmada, extendiendo su alcance a 4.5 metros con daño de fuego, frío, ácido o rayo."},
    {"class": "monje", "class_name": "Monje", "file": "misericordia.md", "id": "monje_misericordia",
     "nombre": "Camino de la Misericordia", "nombre_en": "Way of Mercy", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["monje", "sanación", "toque de daño", "máscara", "phb2024", "tasha"],
     "desc": "Médicos errantes de máscara enigmática que manipulan el ki vital para sanar aliados o infligir muerte y aflicción con Mano del Daño."},

    # PALADÍN
    {"class": "paladin", "class_name": "Paladín", "file": "devocion.md", "id": "paladin_devocion",
     "nombre": "Juramento de Devoción", "nombre_en": "Oath of Devotion", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["paladín", "arma sagrada", "luz", "aura de devoción", "phb2024"],
     "desc": "El arquetipo del caballero de armadura brillante; su Arma Sagrada resplandece sumando Carisma al impacto e impidiendo el hechizo."},
    {"class": "paladin", "class_name": "Paladín", "file": "venganza.md", "id": "paladin_venganza",
     "nombre": "Juramento de Venganza", "nombre_en": "Oath of Vengeance", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["paladín", "voto de enemistad", "perseguidor", "cazador", "phb2024"],
     "desc": "Jura castigar a los culpables sin piedad, marcando a un enemigo con Voto de Enemistad para ganar ventaja permanente en ataques."},
    {"class": "paladin", "class_name": "Paladín", "file": "antiguos.md", "id": "paladin_antiguos",
     "nombre": "Juramento de los Antiguos", "nombre_en": "Oath of the Ancients", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["paladín", "naturaleza", "aura de custodia", "resistencia mágica", "phb2024"],
     "desc": "Caballeros verdes dedicados a preservar la luz y la alegría, su Aura de Custodia otorga resistencia al daño de todos los conjuros."},
    {"class": "paladin", "class_name": "Paladín", "file": "gloria.md", "id": "paladin_gloria",
     "nombre": "Juramento de Gloria", "nombre_en": "Oath of Glory", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["paladín", "atleta", "aura de presteza", "velocidad", "phb2024", "tasha"],
     "desc": "Héroes legendarios destinados a la épica, inspiran velocidad a sus aliados con Aura de Presteza y realizan proezas atléticas milagrosas."},

    # EXPLORADOR
    {"class": "explorador", "class_name": "Explorador", "file": "cazador.md", "id": "explorador_cazador",
     "nombre": "Cazador", "nombre_en": "Hunter", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["explorador", "cazador de colosos", "multitaque", "defensa", "phb2024"],
     "desc": "Especialista consumado en abatir las amenazas más peligrosas del mundo, castigando presas heridas con daño d8 adicional continuo."},
    {"class": "explorador", "class_name": "Explorador", "file": "senor_de_las_bestias.md", "id": "explorador_senor_de_las_bestias",
     "nombre": "Señor de las Bestias", "nombre_en": "Beast Master", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["explorador", "compañero animal", "tierra", "mar", "cielo", "phb2024"],
     "desc": "Vinculado espiritualmente a un Compañero Primitivo (Tierra, Cielo o Mar) que combate sincronizadamente con él en el turno."},
    {"class": "explorador", "class_name": "Explorador", "file": "acechador_sombrio.md", "id": "explorador_acechador_sombrio",
     "nombre": "Acechador Sombrío", "nombre_en": "Gloom Stalker", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["explorador", "infratierra", "invisible en oscuridad", "emboscada", "phb2024", "xanathar"],
     "desc": "Cazador implacable del Inframundo, es totalmente invisible para criaturas con visión en la oscuridad y embosca con ataques letales en turno 1."},
    {"class": "explorador", "class_name": "Explorador", "file": "caminante_feerico.md", "id": "explorador_caminante_feerico",
     "nombre": "Caminante Feérico", "nombre_en": "Fey Wanderer", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["explorador", "carisma", "fey", "daño psíquico", "phb2024", "tasha"],
     "desc": "Bendecido con la magia de las cortes feéricas, suma Sabiduría a pruebas de Carisma e infunde sus flechas con daño psíquico."},

    # PÍCARO
    {"class": "picaro", "class_name": "Pícaro", "file": "ladron.md", "id": "picaro_ladron",
     "nombre": "Ladrón", "nombre_en": "Thief", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["pícaro", "manos rápidas", "usar objeto", "sigilo supremo", "phb2024"],
     "desc": "El maestro de la infiltración y el pillaje, utiliza objetos mágicos y herramientas de ladrones como acción adicional veloz."},
    {"class": "picaro", "class_name": "Pícaro", "file": "asesino.md", "id": "picaro_asesino",
     "nombre": "Asesino", "nombre_en": "Assassin", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["pícaro", "emboscada", "crítico automático", "venenos", "phb2024"],
     "desc": "Especialista en la muerte rápida y silenciosa, inflige impactos críticos automáticos contra objetivos sorprendidos en el primer asalto."},
    {"class": "picaro", "class_name": "Pícaro", "file": "bribon_arcano.md", "id": "picaro_bribon_arcano",
     "nombre": "Bribón Arcano", "nombre_en": "Arcane Trickster", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["pícaro", "magia", "mano de mago invisible", "ilusión", "phb2024"],
     "desc": "Combina sigilo con encantamientos e ilusiones, manipulando una Mano de Mago invisible para robar cerraduras y distraer objetivos."},
    {"class": "picaro", "class_name": "Pícaro", "file": "cuchilla_del_alma.md", "id": "picaro_cuchilla_del_alma",
     "nombre": "Cuchilla del Alma", "nombre_en": "Soulknife", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["pícaro", "psiónico", "hojas psíquicas", "telepatía", "phb2024", "tasha"],
     "desc": "Materializa dagas de energía psíquica pura que no dejan marcas físicas, establece telepatía grupal y altera el destino con dados psiónicos."},
    {"class": "picaro", "class_name": "Pícaro", "file": "espadachin.md", "id": "picaro_espadachin",
     "nombre": "Espadachín", "nombre_en": "Swashbuckler", "fuente": "Guia de Xanathar Para Todo", "nivel": 3,
     "tags": ["pícaro", "xanathar", "duelo 1v1", "iniciativa carisma", "movilidad"],
     "desc": "Duelista audaz que inflige Ataque Furtivo en duelos uno contra uno sin necesitar ventaja y suma su Carisma a la iniciativa."},

    # HECHICERO
    {"class": "hechicero", "class_name": "Hechicero", "file": "magia_salvaje.md", "id": "hechicero_magia_salvaje",
     "nombre": "Magia Salvaje", "nombre_en": "Wild Magic", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["hechicero", "oleada mágica", "azar", "marea de caos", "phb2024"],
     "desc": "Canaliza las fuerzas caóticas e impredecibles del multiverso, disparando oleadas de magia salvaje con efectos asombrosos o devastadores."},
    {"class": "hechicero", "class_name": "Hechicero", "file": "linaje_draconico.md", "id": "hechicero_linaje_draconico",
     "nombre": "Linaje Dracónico", "nombre_en": "Draconic Sorcery", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["hechicero", "dragón", "escamas", "alas dracónicas", "afinidad elemental", "phb2024"],
     "desc": "La sangre de los dragones antiguos late en sus venas, otorgando CA 13+DES sin armadura, puntos de golpe extra y alas mágicas."},
    {"class": "hechicero", "class_name": "Hechicero", "file": "mente_aberrante.md", "id": "hechicero_mente_aberrante",
     "nombre": "Mente Aberrante", "nombre_en": "Aberrant Mind", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["hechicero", "psiónico", "tentáculos", "telepatía", "phb2024", "tasha"],
     "desc": "Tocado por una entidad del Reino Lejano, lanza conjuros psiónicos sutiles sin componentes verbales o somáticos y transforma su cuerpo."},
    {"class": "hechicero", "class_name": "Hechicero", "file": "alma_mecanica.md", "id": "hechicero_alma_mecanica",
     "nombre": "Alma Mecánica", "nombre_en": "Clockwork Soul", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["hechicero", "mecanismo", "orden", "modron", "cancelar ventaja", "phb2024", "tasha"],
     "desc": "Conectado al plano de Mechanus y el orden cósmico absoluto, anula ventajas/desventajas enemigas y proyecta escudos de fuerza ordenados."},
    {"class": "hechicero", "class_name": "Hechicero", "file": "alma_divina.md", "id": "hechicero_alma_divina",
     "nombre": "Alma Divina", "nombre_en": "Divine Soul", "fuente": "Guia de Xanathar Para Todo", "nivel": 3,
     "tags": ["hechicero", "xanathar", "clérigo", "ángel", "sanación", "metamagia"],
     "desc": "Descendiente de seres celestiales, tiene acceso a la lista completa de conjuros de Clérigo combinada con la Metamagia de Hechicero."},

    # BRUJO
    {"class": "brujo", "class_name": "Brujo", "file": "infernal.md", "id": "brujo_infernal",
     "nombre": "El Infernal", "nombre_en": "Fiend Patron", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["brujo", "demonio", "diablo", "fuego", "bendición del oscuro", "phb2024"],
     "desc": "Pacto jurado con un señor de los Nueve Infiernos o el Abismo; gana PG temporales al abatir enemigos y desata llamas infernales."},
    {"class": "brujo", "class_name": "Brujo", "file": "primigenio.md", "id": "brujo_primigenio",
     "nombre": "El Primigenio", "nombre_en": "Great Old One Patron", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["brujo", "cthulhu", "mente", "telepatía", "locura", "phb2024"],
     "desc": "Vinculado a una deidad incomprensible del vacío estelar, establece telepatía despierta, proyecta escudos mentales y crea sirvientes."},
    {"class": "brujo", "class_name": "Brujo", "file": "feerico_ancestral.md", "id": "brujo_feerico_ancestral",
     "nombre": "El Feérico Ancestral", "nombre_en": "Archfey Patron", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["brujo", "fey", "paso brumoso", "hechizo", "ilusión", "phb2024"],
     "desc": "Pacto con un señor de las Cortes Feéricas, teleportándose con Paso Brumoso continuo y fascinando a grupos enteros de criaturas."},
    {"class": "brujo", "class_name": "Brujo", "file": "celestial.md", "id": "brujo_celestial",
     "nombre": "El Celestial", "nombre_en": "Celestial Patron", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["brujo", "ángel", "curación", "radiante", "phb2024", "xanathar"],
     "desc": "Alianza con un unicornio, solar o empíreo, disponiendo de una reserva de dados de sanación d6 que no consumen espacios de pacto."},
    {"class": "brujo", "class_name": "Brujo", "file": "filo_maldito.md", "id": "brujo_filo_maldito",
     "nombre": "El Filo Maldito", "nombre_en": "Hexblade Patron", "fuente": "Guia de Xanathar Para Todo", "nivel": 3,
     "tags": ["brujo", "xanathar", "espada", "carisma al ataque", "maldición", "armaduras medias"],
     "desc": "Forjado por entidades del Páramo Sombrío, ataca con armas cuerpo a cuerpo usando su Carisma, equipa armaduras medias y maldice objetivos."},

    # MAGO
    {"class": "mago", "class_name": "Mago", "file": "evocacion.md", "id": "mago_evocacion",
     "nombre": "Escuela de Evocación", "nombre_en": "School of Evocation", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["mago", "fuego", "área", "esculpir conjuros", "sobrecargar", "phb2024"],
     "desc": "El maestro de la artillería arcana elemental, esculpe zonas seguras para sus aliados dentro de Bolas de Fuego y maximiza el daño."},
    {"class": "mago", "class_name": "Mago", "file": "abjuracion.md", "id": "mago_abjuracion",
     "nombre": "Escuela de Abjuración", "nombre_en": "School of Abjuration", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["mago", "escudo arcano", "protección", "disipar magia", "phb2024"],
     "desc": "Defensor arcano por excelencia, crea una Custodia Arcana que absorbe daño dirigido a él o sus aliados y domina contraconjuros."},
    {"class": "mago", "class_name": "Mago", "file": "adivinacion.md", "id": "mago_adivinacion",
     "nombre": "Escuela de Adivinación", "nombre_en": "School of Divination", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["mago", "augurio", "portento", "d20", "visión", "phb2024"],
     "desc": "Vislumbra el tejido del futuro; tira 2 dados d20 al amanecer (Portento) y sustituye cualquier tirada aliada o enemiga por estos resultados."},
    {"class": "mago", "class_name": "Mago", "file": "ilusionismo.md", "id": "mago_ilusionismo",
     "nombre": "Escuela de Ilusionismo", "nombre_en": "School of Illusion", "fuente": "PHB 2024", "nivel": 3,
     "tags": ["mago", "engaño", "ilusión tangible", "maleable", "phb2024"],
     "desc": "Manipulador supremo de los sentidos y la percepción, es capaz de alterar ilusiones activas e incluso volverlas físicamente sólidas."},
    {"class": "mago", "class_name": "Mago", "file": "escribas.md", "id": "mago_escribas",
     "nombre": "Orden de los Escribas", "nombre_en": "Order of Scribes", "fuente": "Caldero de Tasha para Todo", "nivel": 3,
     "tags": ["mago", "tasha", "grimorio consciente", "cambio elemental", "pergaminos"],
     "desc": "Despierta la consciencia mágica de su grimorio, cambiando el tipo de daño de sus conjuros al vuelo y proyectando un avatar espectral."}
]

def main():
    print("Iniciando expansión atómica de subclases OKF...")
    created_count = 0

    for sub in SUBCLASSES:
        cls_dir = os.path.join(CLASSES_DIR, sub["class"], "subclases")
        os.makedirs(cls_dir, exist_ok=True)
        file_path = os.path.join(cls_dir, sub["file"])

        content = f"""---
id: "{sub['id']}"
nombre: "{sub['nombre']}"
nombre_ingles: "{sub['nombre_en']}"
tipo: "subclase"
clase_padre: "{sub['class_name']}"
nivel_desbloqueo: {sub['nivel']}
fuente: "{sub['fuente']}"
tags: {json.dumps(sub['tags'], ensure_ascii=False)}
---

# Subclase: {sub['nombre']} ({sub['nombre_en']})
**Clase Base:** {sub['class_name']}  
**Manual / Fuente:** {sub['fuente']}  
**Nivel de Desbloqueo Oficial:** Nivel {sub['nivel']}

## Resumen del Arquetipo
{sub['desc']}
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        created_count += 1

    print(f"Creadas {created_count} subclases en formato atómico OKF.")

    # Crear regla de personalización Tasha
    tasha_rule_path = os.path.join(OKF_DIR, "reglas_y_mecanicas", "personalizacion_origen_tasha.md")
    with open(tasha_rule_path, "w", encoding="utf-8") as f:
        f.write("""---
id: "regla_personalizacion_tasha"
nombre: "Opciones de Personalización de Linaje (Tasha)"
nombre_ingles: "Customizing Your Origin (Tasha's Cauldron)"
tipo: "regla"
fuente: "Caldero de Tasha para Todo"
pagina: 7
tags: ["tasha", "regla_opcional", "atributos", "personalización"]
---

# Regla Opcional: Personalización de Linaje (Tasha)

Permite separar los incrementos fijos tradicionales de característica de la especie:
- Si una especie otorgaba tradicionalmente +2 FUE / +1 CON, el jugador puede reasignar libremente **+2 a cualquier característica** y **+1 a otra distinta**, o bien asignar **+1 / +1 / +1** a tres características diferentes.
- Permite cambiar competencias de idiomas y armas por herramientas o habilidades alternativas.
""")
    print("Creada regla opcional de Tasha en OKF.")

    # Actualizar index_metadata.json
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        idx_data = json.load(f)

    entities = idx_data.get("entities", [])
    # Eliminar subclases previas duplicadas si existieran
    existing_ids = {e.get("id") for e in entities}

    for sub in SUBCLASSES:
        if sub["id"] not in existing_ids:
            rel_path = f"clases/{sub['class']}/subclases/{sub['file']}"
            entities.append({
                "id": sub["id"],
                "nombre": sub["nombre"],
                "nombre_ingles": sub["nombre_en"],
                "tipo": "subclase",
                "clase": sub["class_name"],
                "nivel": sub["nivel"],
                "fuente": sub["fuente"],
                "tags": sub["tags"],
                "path": rel_path
            })
            existing_ids.add(sub["id"])

    # Añadir la regla de Tasha
    if "regla_personalizacion_tasha" not in existing_ids:
        entities.append({
            "id": "regla_personalizacion_tasha",
            "nombre": "Opciones de Personalización de Linaje (Tasha)",
            "tipo": "regla",
            "fuente": "Caldero de Tasha para Todo",
            "tags": ["tasha", "regla", "atributos"],
            "path": "reglas_y_mecanicas/personalizacion_origen_tasha.md"
        })

    idx_data["entities"] = entities
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(idx_data, f, indent=2, ensure_ascii=False)

    print(f"✅ index_metadata.json actualizado con éxito. Total entidades: {len(entities)}")

if __name__ == "__main__":
    main()
