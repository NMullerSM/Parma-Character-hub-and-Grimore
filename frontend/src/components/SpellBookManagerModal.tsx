import React, { useState, useEffect } from "react";
import { api } from "../api/client";
import type { SpellItemData } from "../api/types";
import { useCharacter } from "../context/CharacterContext";
import { X, Search, Plus, Trash2, Check, BookOpen } from "lucide-react";

interface SpellBookManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  characterClass: string;
  characterLevel: number;
  currentSpells: SpellItemData[];
  onAddSpell: (spell: SpellItemData) => Promise<boolean>;
  onRemoveSpell: (spellName: string) => Promise<boolean>;
}

const DND_CLASSES = [
  "Bardo",
  "Mago",
  "Clérigo",
  "Druida",
  "Hechicero",
  "Brujo",
  "Paladín",
  "Explorador",
  "Artífice",
  "Todas",
];

const DND_SCHOOLS = [
  "Todas",
  "Evocación",
  "Abjuración",
  "Conjuración",
  "Adivinación",
  "Encantamiento",
  "Ilusionismo",
  "Nigromancia",
  "Transmutación",
];

export const SpellBookManagerModal: React.FC<SpellBookManagerModalProps> = ({
  isOpen,
  onClose,
  characterClass,
  characterLevel,
  currentSpells,
  onAddSpell,
  onRemoveSpell,
}) => {
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedClass, setSelectedClass] = useState<string>(characterClass || "Bardo");
  const [selectedLevel, setSelectedLevel] = useState<number | "all">("all");
  const [selectedSchool, setSelectedSchool] = useState<string>("Todas");
  const [spells, setSpells] = useState<SpellItemData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [previewSpell, setPreviewSpell] = useState<SpellItemData | null>(null);
  const { language } = useCharacter();

  useEffect(() => {
    if (characterClass) {
      setSelectedClass(characterClass);
    }
  }, [characterClass]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Búsqueda con debounce en compendio OKF
  useEffect(() => {
    if (!isOpen) return;
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const results = await api.getAvailableSpells({
          className: selectedClass === "Todas" ? undefined : selectedClass,
          level: selectedLevel === "all" ? undefined : selectedLevel,
          query: searchQuery.trim(),
          school: selectedSchool === "Todas" ? undefined : selectedSchool,
        });
        setSpells(results);
        if (results.length > 0 && !previewSpell) {
          setPreviewSpell(results[0]);
        }
      } catch (e) {
        console.error("Error al cargar conjuros del compendio:", e);
      } finally {
        setLoading(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [isOpen, searchQuery, selectedClass, selectedLevel, selectedSchool]);

  if (!isOpen) return null;

  const safeCurrentSpells = Array.isArray(currentSpells) ? currentSpells : [];
  const currentNamesSet = new Set(
    safeCurrentSpells
      .filter((s) => s && s.name)
      .map((s) => String(s.name).toLowerCase().trim())
  );

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-canvas/85 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-5xl h-[88vh] bg-card border border-border-iron rounded-xl shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Cabecera */}
        <div className="flex items-center justify-between p-4 border-b border-border-iron bg-surface/50 shrink-0">
          <div className="flex items-center gap-2.5">
            <BookOpen className="w-5 h-5 text-gold" />
            <div>
              <h2 className="font-display font-bold text-lg text-gold">
                Gestor del Grimorio & Compendio de Conjuros
              </h2>
              <p className="text-xs text-muted">
                {safeCurrentSpells.length} conjuros en ficha ({characterClass || "Personaje"} Nvl {characterLevel || 1}) • Consulta la base de datos oficial OKF
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg border border-border-iron hover:border-gold text-muted hover:text-main transition-colors"
            title="Cerrar (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Barra de Filtros y Búsqueda */}
        <div className="p-3 border-b border-border-iron bg-surface/30 space-y-2 shrink-0">
          <div className="flex flex-col sm:flex-row gap-2 items-center">
            {/* Buscador */}
            <div className="relative flex-1 w-full">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-muted pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Buscar por nombre en español o inglés..."
                className="w-full bg-input text-main border border-border-iron rounded-lg pl-9 pr-3 py-1.5 text-xs focus:border-gold outline-none transition-colors"
              />
            </div>

            {/* Selector de Clase */}
            <div className="flex items-center gap-1 overflow-x-auto w-full sm:w-auto pb-0.5">
              {DND_CLASSES.slice(0, 6).map((cName) => (
                <button
                  key={cName}
                  onClick={() => setSelectedClass(cName)}
                  className={`px-2.5 py-1 rounded text-[11px] font-semibold whitespace-nowrap transition-colors ${
                    selectedClass === cName
                      ? "bg-gold text-canvas"
                      : "bg-surface border border-border-iron text-muted hover:text-main"
                  }`}
                >
                  {cName}
                </button>
              ))}
            </div>
          </div>

          {/* Filtro por Nivel */}
          <div className="flex items-center justify-between gap-2 overflow-x-auto text-[11px] pt-1">
            <div className="flex items-center gap-1">
              <span className="text-muted text-[10px] uppercase font-semibold mr-1">Nivel:</span>
              <button
                onClick={() => setSelectedLevel("all")}
                className={`px-2 py-0.5 rounded transition-colors ${
                  selectedLevel === "all"
                    ? "bg-gold text-canvas font-bold"
                    : "bg-surface border border-border-iron text-muted hover:text-main"
                }`}
              >
                Todos
              </button>
              <button
                onClick={() => setSelectedLevel(0)}
                className={`px-2 py-0.5 rounded transition-colors ${
                  selectedLevel === 0
                    ? "bg-gold text-canvas font-bold"
                    : "bg-surface border border-border-iron text-muted hover:text-main"
                }`}
              >
                Trucos
              </button>
              {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((lvl) => (
                <button
                  key={lvl}
                  onClick={() => setSelectedLevel(lvl)}
                  className={`px-2 py-0.5 rounded transition-colors ${
                    selectedLevel === lvl
                      ? "bg-gold text-canvas font-bold"
                      : "bg-surface border border-border-iron text-muted hover:text-main"
                  }`}
                >
                  Niv {lvl}
                </button>
              ))}
            </div>

            {/* Selector de Escuela */}
            <select
              value={selectedSchool}
              onChange={(e) => setSelectedSchool(e.target.value)}
              className="bg-surface text-main border border-border-iron rounded px-2 py-0.5 text-[11px] outline-none"
            >
              {DND_SCHOOLS.map((sc) => (
                <option key={sc} value={sc}>
                  {sc === "Todas" ? "Todas las escuelas" : sc}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Contenido en Dos Columnas: Lista de Conjuros y Previsualizador */}
        <div className="flex-1 flex flex-col md:flex-row overflow-hidden divide-y md:divide-y-0 md:divide-x divide-border-iron">
          {/* Columna Izquierda: Lista de Conjuros */}
          <div className="w-full md:w-3/5 overflow-y-auto p-3 space-y-2">
            {loading ? (
              <div className="text-center py-12 text-muted text-xs">Buscando en el compendio OKF...</div>
            ) : spells.length === 0 ? (
              <div className="text-center py-12 text-muted text-xs">
                No se encontraron conjuros con los filtros seleccionados.
              </div>
            ) : (
              spells.map((sp, idx) => {
                if (!sp || !sp.name) return null;
                const sName = sp.name;
                const isAdded = currentNamesSet.has(sName.toLowerCase().trim());
                const isSelected = previewSpell?.name === sName;
                return (
                  <div
                    key={idx}
                    onClick={() => setPreviewSpell(sp)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all flex items-center justify-between gap-3 ${
                      isSelected
                        ? "bg-surface border-gold shadow-sm"
                        : "bg-surface/50 border-border-iron hover:border-gold/60"
                    }`}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs text-main truncate">
                          {language === "en" && sp.name_en ? sp.name_en : sName}
                        </span>
                        <span className="font-stat text-[10px] px-1.5 py-0.2 rounded bg-card border border-border-iron text-gold shrink-0">
                          {sp.level === 0 ? "Truco" : `Niv ${sp.level}`}
                        </span>
                        <span className="text-[10px] text-muted hidden sm:inline">{sp.school}</span>
                      </div>
                      <p className="text-[11px] text-muted truncate mt-0.5">
                        {sp.cast_time} • {sp.range_area} • {sp.components}
                      </p>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0" onClick={(e) => e.stopPropagation()}>
                      {isAdded ? (
                        <div className="flex items-center gap-1">
                          <span className="text-[10px] text-green-400 bg-green-500/10 border border-green-500/30 px-2 py-0.5 rounded font-semibold flex items-center gap-1">
                            <Check className="w-3 h-3" /> En Grimorio
                          </span>
                          <button
                            onClick={() => onRemoveSpell(sp.name)}
                            className="p-1 rounded bg-crimson/20 hover:bg-crimson text-crimson hover:text-white transition-colors"
                            title="Quitar del grimorio"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => onAddSpell(sp)}
                          className="px-2.5 py-1 rounded bg-gold hover:bg-gold-hover text-canvas font-semibold text-xs flex items-center gap-1 transition-all active:scale-95 shadow-xs"
                        >
                          <Plus className="w-3.5 h-3.5" />
                          <span>Añadir</span>
                        </button>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Columna Derecha: Vista Previa Detallada */}
          <div className="w-full md:w-2/5 overflow-y-auto p-4 bg-surface/20 flex flex-col justify-between">
            {previewSpell ? (
              <div className="space-y-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-surface border border-border-iron text-gold uppercase">
                      {previewSpell.level === 0 ? "Truco" : `Nivel ${previewSpell.level}`}
                    </span>
                    <span className="text-[10px] text-muted">{previewSpell.school}</span>
                  </div>
                  <h3 className="font-display font-bold text-lg text-gold">
                    {language === "en" && previewSpell.name_en ? previewSpell.name_en : previewSpell.name}
                  </h3>
                  {previewSpell.name_en && previewSpell.name_en !== previewSpell.name && (
                    <p className="text-xs text-muted italic">
                      {language === "en" ? previewSpell.name : previewSpell.name_en}
                    </p>
                  )}
                </div>

                <div className="text-xs space-y-1 bg-surface p-2.5 rounded border border-border-iron">
                  <div>
                    <span className="text-muted">Tiempo de lanzamiento:</span>{" "}
                    <span className="text-main font-medium">{previewSpell.cast_time}</span>
                  </div>
                  <div>
                    <span className="text-muted">Alcance:</span>{" "}
                    <span className="text-main font-medium">{previewSpell.range_area}</span>
                  </div>
                  <div>
                    <span className="text-muted">Componentes:</span>{" "}
                    <span className="text-main font-medium">{previewSpell.components}</span>
                  </div>
                  <div>
                    <span className="text-muted">Duración:</span>{" "}
                    <span className="text-main font-medium">{previewSpell.duration}</span>
                  </div>
                </div>

                <div className="text-xs text-muted leading-relaxed max-h-56 overflow-y-auto pr-1">
                  {previewSpell.description || previewSpell.notes}
                </div>

                {previewSpell.higher_levels && (
                  <div className="p-2 rounded bg-surface border border-border-iron text-xs">
                    <strong className="text-gold block mb-0.5">En Niveles Superiores:</strong>
                    <p className="text-muted">{previewSpell.higher_levels}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-center text-xs text-muted">
                Selecciona un conjuro para ver su descripción canónica.
              </div>
            )}

            {/* Acción al pie de la columna derecha */}
            {previewSpell && (
              <div className="pt-3 border-t border-border-iron mt-3 flex items-center justify-between">
                {previewSpell.name && currentNamesSet.has(previewSpell.name.toLowerCase().trim()) ? (
                  <button
                    onClick={() => onRemoveSpell(previewSpell.name)}
                    className="w-full py-1.5 rounded bg-crimson/20 border border-crimson text-crimson hover:bg-crimson hover:text-white text-xs font-semibold transition-colors flex items-center justify-center gap-1.5"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Eliminar de mi Grimorio</span>
                  </button>
                ) : (
                  <button
                    onClick={() => onAddSpell(previewSpell)}
                    className="w-full py-1.5 rounded bg-gold hover:bg-gold-hover text-canvas text-xs font-semibold transition-colors shadow-sm flex items-center justify-center gap-1.5"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Añadir a mi Grimorio</span>
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Pie del Modal */}
        <div className="p-3 border-t border-border-iron bg-surface/50 flex items-center justify-between shrink-0">
          <span className="text-xs text-muted">
            {spells.length} conjuros disponibles para {selectedClass}
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg border border-border-iron hover:border-gold text-xs text-muted hover:text-main font-medium transition-colors"
          >
            Listo / Cerrar (Esc)
          </button>
        </div>
      </div>
    </div>
  );
};
