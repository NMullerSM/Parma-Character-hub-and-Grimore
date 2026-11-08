---
name: adversarial-testing
description: >-
  Metodología de testing adversarial: diseñar pruebas que intentan activamente romper
  el sistema (no confirmarlo), documentar cada intento haya fallado o no, y producir
  hallazgos auditables en vez de una suite que siempre pasa en verde. Skill genérica,
  portable a cualquier proyecto — no depende de contenido específico de ningún OKF.
---

# Testing Adversarial

Un test que siempre pasa no prueba que el sistema funciona: prueba que el test no
busca lo suficiente. El objetivo de este skill no es "cobertura" ni "TDD de
confirmación" — es diseñar deliberadamente las condiciones que un sistema debería
soportar y que probablemente no soporta, y dejar constancia de lo que se encontró.

Esto se usa como **auditoría**, no como reemplazo de la suite de tests normal:
corre por encima o en paralelo a los tests que ya confirman el camino feliz.

---

## 1. Principio rector

> Diseñar para romper, no para confirmar.

Si un test solo ejercita el camino que el autor del código ya tuvo en mente al
escribirlo, no aporta información nueva — solo repite la intención del autor.
Un test adversarial parte de la pregunta contraria: **¿qué secuencia de eventos,
input, fallo parcial o concurrencia haría que esto se rompa?**

---

## 2. Identificar invariantes antes de escribir ningún caso

Antes de generar casos, enumerar explícitamente lo que el sistema **nunca** debe
permitir — no lo que debe hacer, sino lo que no puede pasar bajo ninguna
circunstancia. Ejemplos de invariantes reales (no genéricos):
- Nunca se pierden datos ya guardados del usuario, aunque la operación que los
  tocó se interrumpa a mitad de camino.
- Nunca se escribe en una ruta de solo lectura / de solo distribución.
- Nunca un endpoint remoto expone datos o acciones sin la autenticación que el
  diseño exige.
- Nunca un valor numérico de dominio (vida, recursos, cantidades) queda en un
  estado imposible (negativo donde no corresponde, mayor que su propio máximo,
  etc.) tras una secuencia de operaciones válidas por separado pero combinadas
  de forma inesperada.

Un test adversarial sin un invariante explícito detrás es solo curiosidad — no
produce un hallazgo clasificable.

---

## 3. Categorías de ataque a cubrir sistemáticamente

Por cada invariante, recorrer (lo que aplique al tipo de componente):

1. **Valores límite y extremos**: cero, negativo, máximo representable, vacío,
   extremadamente largo, Unicode/encoding inesperado.
2. **Input malformado o inesperado**: tipos equivocados, campos faltantes,
   estructuras parcialmente válidas, datos que vienen de una versión anterior
   del esquema.
3. **Concurrencia y orden de eventos**: dos operaciones compitiendo por el mismo
   recurso, una operación disparada mientras otra está a mitad de camino, una
   señal de cierre/cancelación llegando entre dos pasos que deberían ser atómicos.
4. **Fallo parcial / interrupción**: el proceso muere, pierde red, o el disco se
   llena a mitad de una operación de varios pasos — ¿queda el sistema en un
   estado consistente o a medio camino?
5. **Agotamiento de recursos**: muchas entradas, archivos grandes, conexiones
   repetidas, memoria o hilos que se acumulan si algo no se libera.
6. **Seguridad**: inyección, path traversal, bypass de autenticación/autorización,
   confianza implícita en datos que vienen de fuera del proceso.
7. **Compatibilidad hacia atrás/adelante de datos persistidos**: ¿qué pasa si el
   dato que se lee fue escrito por una versión anterior (o futura) del esquema?

No todas las categorías aplican a todo — se recorren como checklist, se
descartan las que no tienen sentido para el componente en cuestión, y se
documenta por qué se descartaron si no es obvio.

---

## 4. Proceso

1. Elegir el componente o flujo a auditar.
2. Enumerar sus invariantes reales (sección 2).
3. Por cada invariante, generar al menos un caso adversarial de la sección 3 que
   intente violarlo deliberadamente.
4. Razonar o ejecutar el caso (si hay sandbox seguro para ello) y determinar si
   el invariante se sostuvo.
5. **Documentar el resultado siempre**, haya resistido o no. Un caso que resistió
   también es información: confirma que esa puerta está cerrada y no hay que
   volver a abrirla sin querer en un cambio futuro.
6. Si el invariante se rompió, generar un hallazgo (sección 5) con reproducción
   concreta.

---

## 5. Formato de hallazgo (obligatorio para auditar después)

Cada hallazgo real se reporta con:
- **Archivo:línea** (o paso de pipeline / endpoint) exacto.
- **Categoría**: bug / seguridad / pérdida-de-datos / rendimiento / mantenibilidad.
- **Escenario adversarial concreto**: la secuencia exacta de pasos o el input
  exacto que lo dispara — reproducible, no una descripción vaga.
- **Severidad**: crítica / alta / media / baja.
- **Dirección de arreglo sugerida** (sin implementarla en la misma pasada de
  auditoría, salvo que se pida explícitamente lo contrario).

Los hallazgos de una auditoría adversarial se documentan en un reporte aparte
(no se mezclan silenciosamente en el código) para que queden auditables por
cualquiera que revise después — humano o agente, en esta máquina o en otra.

---

## 6. Qué NO es este skill

- No es un linter ni un chequeo de estilo.
- No es "aumentar la cobertura de tests" per se — un test adversarial puede
  cubrir una sola línea y ser más valioso que cien tests de camino feliz.
- No es TDD de confirmación (escribir el test que ya sabés que va a pasar).
- No reemplaza la suite de regresión existente — la complementa buscando lo que
  esa suite, por diseño, no busca.

---

## 7. Cuándo invocarlo

- Antes de cerrar una tarjeta/feature como "lista" cuando el cambio toca datos
  persistidos, autenticación, concurrencia o dinero/recursos del dominio.
- Como auditoría periódica de arriba a abajo de un repo, independiente de
  cualquier feature puntual.
- Cuando una revisión de código normal (buscar errores obvios) ya se hizo y se
  quiere ir un nivel más profundo, deliberadamente adversarial.
