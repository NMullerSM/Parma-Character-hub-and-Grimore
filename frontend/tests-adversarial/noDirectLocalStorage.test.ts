/**
 * Guardia estatica de almacenamiento (invariante I3-a, hallazgo C3).
 *
 * Invariante: ningun archivo de frontend/src salvo utils/storage.ts referencia
 * `localStorage` directamente. Todo acceso debe pasar por `safeStorage`, que
 * evita ReferenceError/SecurityError en WebKitGTK, Safari y ventanas privadas.
 *
 * Categoria de ataque: seguridad / compatibilidad (entorno sin localStorage).
 *
 * Este test no importa codigo de src: solo escanea el texto de los archivos,
 * asi que no depende de React ni de los modulos de la aplicacion.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

const SRC_DIR = path.join(import.meta.dirname, "..", "src");
const ALLOWED_RELATIVE = "utils/storage.ts";
const PATTERN = /\blocalStorage\b/;

/**
 * Elimina comentarios de forma simple. Conserva los saltos de linea para que
 * los numeros de linea reportados coincidan con el archivo real.
 * El patron de `//` ignora `://` (URLs) para no borrar codigo util.
 */
function stripComments(source: string): string {
  const noBlock = source.replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, " "));
  return noBlock.replace(/(^|[^:\\])\/\/.*$/gm, (_match, pre: string) => pre);
}

function findLocalStorageUsages(source: string): Array<{ line: number; text: string }> {
  const hits: Array<{ line: number; text: string }> = [];
  stripComments(source).split("\n").forEach((text, index) => {
    if (PATTERN.test(text)) {
      hits.push({ line: index + 1, text: text.trim() });
    }
  });
  return hits;
}

function collectScannedFiles(dir: string): string[] {
  return readdirSync(dir, { recursive: true })
    .map((rel) => String(rel))
    .filter((rel) => /\.(ts|tsx)$/.test(rel))
    .filter((rel) => rel.split(path.sep).join("/") !== ALLOWED_RELATIVE)
    .map((rel) => path.join(dir, rel))
    .filter((abs) => statSync(abs).isFile());
}

test("I3-a: ningun archivo de frontend/src usa localStorage directo (fuera de utils/storage.ts)", () => {
  const files = collectScannedFiles(SRC_DIR);
  assert.ok(files.length > 0, "el escaneo no encontro archivos en frontend/src (ruta mal resuelta)");

  const problems: string[] = [];
  for (const abs of files) {
    const source = readFileSync(abs, "utf8");
    for (const hit of findLocalStorageUsages(source)) {
      const relative = path.relative(SRC_DIR, abs).split(path.sep).join("/");
      problems.push(`${relative}:${hit.line} -> ${hit.text}`);
    }
  }

  assert.deepEqual(
    problems,
    [],
    `Uso directo de localStorage (usar safeStorage de utils/storage.ts):\n${problems.join("\n")}`,
  );
});

test("I3-a (auto-chequeo): el detector marca localStorage directo y no marca safeStorage", () => {
  const direct = findLocalStorageUsages("const x = localStorage.getItem('a')");
  assert.equal(direct.length, 1, "debe detectar localStorage directo");
  assert.equal(direct[0].line, 1);

  const safe = findLocalStorageUsages("safeStorage.getItem('a')");
  assert.equal(safe.length, 0, "no debe detectar safeStorage");

  const commented = findLocalStorageUsages("// localStorage solo en comentario\nconst y = 1;");
  assert.equal(commented.length, 0, "un comentario no cuenta como uso");
});
