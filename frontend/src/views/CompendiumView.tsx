import React, { useState, useEffect, useRef } from "react";
import { api } from "../api/client";
import { useTranslation } from "../i18n";
import { useCharacter } from "../context/CharacterContext";
import type {
  CompendiumCategory,
  CompendiumSearchResult,
  CompendiumMonsterDetail,
  CompendiumSpellDetail,
  CompendiumItemDetail,
} from "../api/types";
import { Search, Shield, Heart, Zap, Sparkles, Sword, Crosshair } from "lucide-react";
import { MarkdownViewer } from "../components/MarkdownViewer";

export const CompendiumView: React.FC = () => {
  const { t, language, translateCategory, translateSpellName, translateClass } = useTranslation();
  const { dndEdition, activeExpansions, toggleExpansion } = useCharacter();

  // `spell.classes` is a shared comma-separated string stored in Spanish; map each class name to the active language.
  const formatSpellClasses = (raw: string): string =>
    raw
      .split(",")
      .map((c) => translateClass(c.trim()))
      .filter(Boolean)
      .join(", ");

  const [categories, setCategories] = useState<CompendiumCategory[]>([]);
  const [selectedCat, setSelectedCat] = useState<string>("");
  const [selectedEdition, setSelectedEdition] = useState<string>(dndEdition || "5.5e");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [results, setResults] = useState<CompendiumSearchResult[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // Referencias para evitar condiciones de carrera por resolución asíncrona desordenada
  const lastSearchIdRef = useRef<number>(0);
  const lastLoadIdRef = useRef<number>(0);
  // Contenedor del panel de detalle: se resetea a la cima al cambiar de entrada
  const detailScrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (dndEdition) {
      setSelectedEdition(dndEdition);
    }
  }, [dndEdition]);

  useEffect(() => {
    if (detailScrollRef.current) {
      detailScrollRef.current.scrollTop = 0;
    }
  }, [selectedEntry?.id, selectedEntry?.name]);

  useEffect(() => {
    async function loadCategories() {
      try {
        const cats = await api.getCompendiumCategories(language, selectedEdition || undefined, activeExpansions);
        setCategories(cats);
        if (cats.length > 0 && !selectedCat) setSelectedCat(cats[0].id);
      } catch (e) {
        console.error("Error loading categories:", e);
      }
    }
    loadCategories();
  }, [language, selectedEdition, activeExpansions]);

  useEffect(() => {
    const timer = setTimeout(async () => {
      const searchId = ++lastSearchIdRef.current;
      setLoading(true);
      try {
        const queryToRun = searchQuery.trim();
        const edFilter = selectedEdition || undefined;

        if (selectedCat === "monstruos") {
          const res = await api.searchMonsters(queryToRun, null, null, null, null, edFilter, language, 1, 150, activeExpansions);
          if (searchId !== lastSearchIdRef.current) return;
          const mapped: CompendiumSearchResult[] = res.items.map((m) => ({
            id: m.entity_id,
            name: language === "en" && m.name_en ? m.name_en : m.name,
            category: "monstruos",
            snippet: `${m.size || ""} ${m.monster_type || ""} • CR ${m.cr_text || "0"} • CA ${m.ac ?? 10} • PG ${m.hp_avg ?? 10}`.trim(),
            path: "sqlite:compendium_monsters",
            source: m.source,
            expansion_tag: m.expansion_tag,
          }));
          setResults(mapped);
          if (mapped.length > 0) {
            loadEntry("monstruos", mapped[0].name, mapped[0].id);
          } else {
            setSelectedEntry(null);
          }
        } else if (selectedCat === "conjuros") {
          const res = await api.searchSpells(queryToRun, null, null, null, null, null, null, edFilter, language, 1, 150, activeExpansions);
          if (searchId !== lastSearchIdRef.current) return;
          const mapped: CompendiumSearchResult[] = res.items.map((s) => ({
            id: s.entity_id,
            name: language === "en" && s.name_en ? s.name_en : s.name,
            category: "conjuros",
            snippet: `${language === "en" ? "Level" : "Nivel"} ${s.level} • ${s.school} • ${s.casting_time}`,
            path: "sqlite:compendium_spells",
            source: s.source,
            expansion_tag: s.expansion_tag,
          }));
          setResults(mapped);
          if (mapped.length > 0) {
            loadEntry("conjuros", mapped[0].name, mapped[0].id);
          } else {
            setSelectedEntry(null);
          }
        } else if (selectedCat === "equipo_y_armamento") {
          const res = await api.searchItems(queryToRun, null, null, null, edFilter, language, 1, 150, activeExpansions);
          if (searchId !== lastSearchIdRef.current) return;
          const mapped: CompendiumSearchResult[] = res.items.map((it) => ({
            id: it.entity_id,
            name: language === "en" && it.name_en ? it.name_en : it.name,
            category: "equipo_y_armamento",
            snippet: `${it.item_type} • ${it.rarity}${it.weapon_mastery ? " • Dominio: " + it.weapon_mastery : ""}`,
            path: "sqlite:compendium_items",
            source: it.source,
            expansion_tag: it.expansion_tag,
          }));
          setResults(mapped);
          if (mapped.length > 0) {
            loadEntry("equipo_y_armamento", mapped[0].name, mapped[0].id);
          } else {
            setSelectedEntry(null);
          }
        } else {
          // OKF y compendium_entities en SQLite
          const data = await api.searchCompendium(queryToRun, selectedCat || undefined, language, edFilter, activeExpansions);
          if (searchId !== lastSearchIdRef.current) return;
          setResults(data);
          if (data.length > 0) {
            loadEntry(data[0].category, data[0].name, data[0].id);
          } else {
            setSelectedEntry(null);
          }
        }
      } catch (e) {
        if (searchId === lastSearchIdRef.current) {
          console.error("Error searching compendium:", e);
        }
      } finally {
        if (searchId === lastSearchIdRef.current) {
          setLoading(false);
        }
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [searchQuery, selectedCat, language, selectedEdition, activeExpansions]);

  const loadEntry = async (category: string, name: string, id?: string) => {
    const loadId = ++lastLoadIdRef.current;
    try {
      if (category === "monstruos") {
        const monster = await api.getMonsterById(id || name);
        if (loadId !== lastLoadIdRef.current) return;
        if (monster) {
          setSelectedEntry({
            id: monster.entity_id,
            name: language === "en" && monster.name_en ? monster.name_en : monster.name,
            category: "monstruos",
            monster,
          });
          return;
        }
      }

      if (category === "conjuros") {
        const spell = await api.getSpellById(id || name);
        if (loadId !== lastLoadIdRef.current) return;
        if (spell) {
          setSelectedEntry({
            id: spell.entity_id,
            name: language === "en" && spell.name_en ? spell.name_en : spell.name,
            category: "conjuros",
            spell,
            content: spell.description,
          });
          return;
        }
      }

      if (category === "equipo_y_armamento") {
        const item = await api.getItemById(id || name);
        if (loadId !== lastLoadIdRef.current) return;
        if (item) {
          setSelectedEntry({
            id: item.entity_id,
            name: language === "en" && item.name_en ? item.name_en : item.name,
            category: "equipo_y_armamento",
            item,
            content: item.description,
          });
          return;
        }
      }

      const entry = await api.getCompendiumEntry(category, id || name, language);
      if (loadId !== lastLoadIdRef.current) return;
      setSelectedEntry(entry);
    } catch (e) {
      if (loadId === lastLoadIdRef.current) {
        console.error("Error loading entry:", e);
      }
    }
  };

  const formatMod = (score: number) => {
    const mod = Math.floor((score - 10) / 2);
    return mod >= 0 ? `+${mod}` : `${mod}`;
  };

  return (
    <div className="h-full flex flex-col p-4 md:p-6 space-y-4 max-w-7xl mx-auto overflow-hidden">
      {/* 1. Header del Compendio, Filtro de Edición y Buscador Central */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-border-iron pb-3 shrink-0">
        <div>
          <h1 className="font-display font-bold text-2xl text-gold">{t("compendium.title")}</h1>
          <p className="text-xs text-muted">{t("compendium.subtitle")}</p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Selector de Edición D&D */}
          <div className="flex items-center bg-card border border-border-iron rounded-lg p-0.5 text-xs">
            <button
              onClick={() => setSelectedEdition("5.5e")}
              className={`px-2.5 py-1 rounded font-medium transition-colors ${
                selectedEdition === "5.5e" ? "bg-gold text-canvas font-bold" : "text-muted hover:text-main"
              }`}
            >
              2024 (5.5e)
            </button>
            <button
              onClick={() => setSelectedEdition("5e")}
              className={`px-2.5 py-1 rounded font-medium transition-colors ${
                selectedEdition === "5e" ? "bg-gold text-canvas font-bold" : "text-muted hover:text-main"
              }`}
            >
              2014 (5e)
            </button>
            <button
              onClick={() => setSelectedEdition("")}
              className={`px-2 py-1 rounded font-medium transition-colors ${
                selectedEdition === "" ? "bg-gold text-canvas font-bold" : "text-muted hover:text-main"
              }`}
            >
              {language === "en" ? "All" : "Todas"}
            </button>
          </div>

          {/* Selector de Expansiones Activas: chips compactos (nombre completo en title) */}
          <div className="flex items-center bg-card border border-border-iron rounded-lg p-0.5 text-[11px] gap-0.5">
            <button
              type="button"
              aria-pressed={!!activeExpansions?.includes("xge")}
              onClick={() => toggleExpansion("xge")}
              title="Xanathar's Guide to Everything"
              className={`px-1.5 py-0.5 rounded font-stat font-semibold border transition-colors ${
                activeExpansions?.includes("xge")
                  ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                  : "text-muted hover:text-main border-transparent opacity-50"
              }`}
            >
              XGtE
            </button>
            <button
              type="button"
              aria-pressed={!!activeExpansions?.includes("tce")}
              onClick={() => toggleExpansion("tce")}
              title="Tasha's Cauldron of Everything"
              className={`px-1.5 py-0.5 rounded font-stat font-semibold border transition-colors ${
                activeExpansions?.includes("tce")
                  ? "bg-purple-500/20 text-purple-300 border-purple-500/40"
                  : "text-muted hover:text-main border-transparent opacity-50"
              }`}
            >
              TCoE
            </button>
          </div>

          {/* Input de Búsqueda */}
          <div className="relative w-full md:w-72">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-muted pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t("compendium.searchPlaceholder")}
              className="w-full bg-input text-main border border-border-iron rounded-lg pl-9 pr-3 py-1.5 text-sm focus:border-gold outline-none transition-colors"
            />
          </div>
        </div>
      </div>

      {/* 2. Categorías (Tabs Horizontales) */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 shrink-0">
        <button
          onClick={() => setSelectedCat("")}
          className={`px-3 py-1 rounded text-xs font-semibold whitespace-nowrap transition-colors ${
            selectedCat === "" ? "bg-gold text-canvas" : "bg-card text-muted hover:text-main"
          }`}
        >
          {t("common.all")}
        </button>
        {categories.map((c) => (
          <button
            key={c.id}
            onClick={() => setSelectedCat(c.id)}
            className={`px-3 py-1 rounded text-xs font-semibold whitespace-nowrap transition-colors ${
              selectedCat === c.id ? "bg-gold text-canvas" : "bg-card text-muted hover:text-main"
            }`}
          >
            {translateCategory(c.id)} ({c.count})
          </button>
        ))}
      </div>

      {/* 3. Panel Dividido: Lista de Resultados a la izquierda, Detalle a la derecha */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4 min-h-0 overflow-hidden">
        {/* Lista de Entradas */}
        <div className="bg-card border border-border-iron rounded-xl overflow-y-auto divide-y divide-border-iron/50 min-h-0">
          {loading ? (
            <div className="p-6 text-center text-xs text-muted">{t("common.loading")}</div>
          ) : results.length > 0 ? (
            results.map((r, idx) => (
              <div
                key={idx}
                onClick={() => loadEntry(r.category, r.name, r.id)}
                className={`p-3 cursor-pointer transition-colors ${
                  (selectedEntry?.id === r.id || selectedEntry?.name === r.name) ? "bg-surface border-l-2 border-gold" : "hover:bg-surface/50"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <h4 className="font-semibold text-xs text-main">
                    {r.category === "conjuros" && language === "en" ? translateSpellName(r.name) : r.name}
                  </h4>
                  <div className="flex items-center gap-1.5 shrink-0">
                    {r.expansion_tag && r.expansion_tag !== "phb_2024" && r.expansion_tag !== "srd_2014" && (
                      <span className="text-[9px] uppercase px-1.5 py-0.2 rounded bg-amber-500/15 text-amber-300 font-stat border border-amber-500/30">
                        {r.expansion_tag}
                      </span>
                    )}
                    <span className="text-[10px] uppercase font-stat text-gold/80">{translateCategory(r.category)}</span>
                  </div>
                </div>
                {r.snippet && <p className="text-[11px] text-muted line-clamp-2 leading-relaxed">{r.snippet}</p>}
              </div>
            ))
          ) : (
            <div className="p-6 text-center text-xs text-muted">{t("compendium.noResults")}</div>
          )}
        </div>

        {/* Visor de Contenido Detallado */}
        <div ref={detailScrollRef} className="md:col-span-2 bg-card border border-border-iron rounded-xl p-5 overflow-y-auto space-y-4">
          {selectedEntry ? (
            <div>
              {/* Header de la Entrada */}
              <div className="border-b border-border-iron pb-3 mb-4">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] uppercase font-stat tracking-widest text-gold">
                    {translateCategory(selectedEntry.category)}
                  </span>
                  {(selectedEntry.source || selectedEntry.monster?.source || selectedEntry.spell?.source || selectedEntry.item?.source) && (
                    <span className="text-[10px] px-2 py-0.5 rounded font-stat bg-surface text-gold/90 border border-border-iron">
                      {selectedEntry.source || selectedEntry.monster?.source || selectedEntry.spell?.source || selectedEntry.item?.source}
                    </span>
                  )}
                </div>
                <h2 className="font-display font-bold text-2xl text-main mt-0.5">
                  {selectedEntry.category === "conjuros" && language === "en"
                    ? translateSpellName(selectedEntry.name)
                    : selectedEntry.name}
                </h2>
                {selectedEntry.monster && (
                  <p className="text-xs text-muted italic mt-0.5">
                    {selectedEntry.monster.size} {selectedEntry.monster.monster_type}, {selectedEntry.monster.alignment}
                  </p>
                )}
                {selectedEntry.spell && (
                  <p className="text-xs text-muted italic mt-0.5">
                    {language === "en" ? "Level" : "Nivel"} {selectedEntry.spell.level} • {selectedEntry.spell.school}
                  </p>
                )}
                {selectedEntry.item && (
                  <p className="text-xs text-muted italic mt-0.5">
                    {selectedEntry.item.item_type} • {selectedEntry.item.rarity}
                  </p>
                )}
              </div>

              {/* STATBLOCK DE CRIATURA / MONSTRUO */}
              {selectedEntry.monster && (
                <div className="space-y-4">
                  {/* Tarjetas de Vigor y Combate */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    <div className="bg-surface/60 border border-border-iron/80 rounded-lg p-2.5 text-center">
                      <div className="flex items-center justify-center gap-1 text-[10px] uppercase font-stat text-muted">
                        <Shield className="w-3 h-3 text-gold" />
                        <span>{language === "en" ? "Armor Class" : "Armadura (CA)"}</span>
                      </div>
                      <div className="text-lg font-bold text-main font-stat mt-0.5">{selectedEntry.monster.ac ?? 10}</div>
                    </div>
                    <div className="bg-surface/60 border border-border-iron/80 rounded-lg p-2.5 text-center">
                      <div className="flex items-center justify-center gap-1 text-[10px] uppercase font-stat text-muted">
                        <Heart className="w-3 h-3 text-red-400" />
                        <span>{language === "en" ? "Hit Points" : "Vida (PG)"}</span>
                      </div>
                      <div className="text-lg font-bold text-main font-stat mt-0.5">
                        {selectedEntry.monster.hp_avg ?? 10}
                        {selectedEntry.monster.hp_formula && (
                          <span className="text-[10px] text-muted font-normal block font-sans">
                            {selectedEntry.monster.hp_formula}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="bg-surface/60 border border-border-iron/80 rounded-lg p-2.5 text-center">
                      <div className="flex items-center justify-center gap-1 text-[10px] uppercase font-stat text-muted">
                        <Zap className="w-3 h-3 text-amber-400" />
                        <span>{language === "en" ? "Speed" : "Velocidad"}</span>
                      </div>
                      <div className="text-xs font-semibold text-main mt-1 line-clamp-2">
                        {selectedEntry.monster.speed || "30 ft."}
                      </div>
                    </div>
                    <div className="bg-surface/60 border border-border-iron/80 rounded-lg p-2.5 text-center">
                      <div className="flex items-center justify-center gap-1 text-[10px] uppercase font-stat text-muted">
                        <Crosshair className="w-3 h-3 text-gold" />
                        <span>{language === "en" ? "Challenge (CR)" : "Desafío (CR)"}</span>
                      </div>
                      <div className="text-lg font-bold text-gold font-stat mt-0.5">{selectedEntry.monster.cr_text || "0"}</div>
                    </div>
                  </div>

                  {/* Atributos / Scores de Características */}
                  {selectedEntry.monster.details && (
                    <div className="grid grid-cols-6 gap-1 bg-surface/40 border border-border-iron/60 rounded-lg p-2 text-center">
                      {[
                        { label: "FUE", val: selectedEntry.monster.details.str ?? 10 },
                        { label: "DES", val: selectedEntry.monster.details.dex ?? 10 },
                        { label: "CON", val: selectedEntry.monster.details.con ?? 10 },
                        { label: "INT", val: selectedEntry.monster.details.int ?? 10 },
                        { label: "SAB", val: selectedEntry.monster.details.wis ?? 10 },
                        { label: "CAR", val: selectedEntry.monster.details.cha ?? 10 },
                      ].map((st, i) => (
                        <div key={i} className="p-1">
                          <span className="text-[10px] font-bold text-muted font-stat">{st.label}</span>
                          <div className="text-sm font-bold text-main font-stat">{st.val}</div>
                          <span className="text-[10px] text-gold font-stat">{formatMod(st.val)}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Rasgos y Capacidades Especiales */}
                  {selectedEntry.monster.details?.trait && selectedEntry.monster.details.trait.length > 0 && (
                    <div className="space-y-2 border-t border-border-iron/60 pt-3">
                      <h4 className="text-xs uppercase font-stat tracking-wider text-gold font-bold">
                        {language === "en" ? "Traits & Special Traits" : "Rasgos y Habilidades"}
                      </h4>
                      {selectedEntry.monster.details.trait.map((t: any, idx: number) => (
                        <div key={idx} className="text-xs leading-relaxed">
                          <span className="font-semibold text-main">{t.name}: </span>
                          <span className="text-muted">
                            {Array.isArray(t.entries) ? t.entries.join(" ") : t.desc || t.entries || ""}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Acciones */}
                  {selectedEntry.monster.details?.action && selectedEntry.monster.details.action.length > 0 && (
                    <div className="space-y-2 border-t border-border-iron/60 pt-3">
                      <h4 className="text-xs uppercase font-stat tracking-wider text-gold font-bold">
                        {language === "en" ? "Actions" : "Acciones"}
                      </h4>
                      {selectedEntry.monster.details.action.map((a: any, idx: number) => (
                        <div key={idx} className="text-xs leading-relaxed">
                          <span className="font-semibold text-main">{a.name}: </span>
                          <span className="text-muted">
                            {Array.isArray(a.entries) ? a.entries.join(" ") : a.desc || a.entries || ""}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* DETALLE DE CONJURO */}
              {selectedEntry.spell && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                    <div className="bg-surface/60 border border-border-iron/80 rounded-lg p-2">
                      <span className="text-[10px] uppercase font-stat text-muted block">
                        {language === "en" ? "Casting Time" : "Tiempo de Lanzamiento"}
                      </span>
                      <span className="font-semibold text-main">{selectedEntry.spell.casting_time}</span>
                    </div>
                    <div className="bg-surface/60 border border-border-iron/80 rounded-lg p-2">
                      <span className="text-[10px] uppercase font-stat text-muted block">
                        {language === "en" ? "Range / Area" : "Alcance / Área"}
                      </span>
                      <span className="font-semibold text-main">{selectedEntry.spell.range_area}</span>
                    </div>
                    <div className="bg-surface/60 border border-border-iron/80 rounded-lg p-2">
                      <span className="text-[10px] uppercase font-stat text-muted block">
                        {language === "en" ? "Components" : "Componentes"}
                      </span>
                      <span className="font-semibold text-main">{selectedEntry.spell.components}</span>
                    </div>
                    <div className="bg-surface/60 border border-border-iron/80 rounded-lg p-2">
                      <span className="text-[10px] uppercase font-stat text-muted block">
                        {language === "en" ? "Duration" : "Duración"}
                      </span>
                      <span className="font-semibold text-main">{selectedEntry.spell.duration}</span>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-1.5 items-center">
                    {Boolean(selectedEntry.spell.is_concentration) && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                        {language === "en" ? "Concentration" : "Concentración"}
                      </span>
                    )}
                    {Boolean(selectedEntry.spell.is_ritual) && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/40">
                        Ritual
                      </span>
                    )}
                    {selectedEntry.spell.classes && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-surface text-muted border border-border-iron">
                        {formatSpellClasses(selectedEntry.spell.classes)}
                      </span>
                    )}
                  </div>

                  <div className="border-t border-border-iron/60 pt-3">
                    <MarkdownViewer content={selectedEntry.spell.description || selectedEntry.content || ""} />
                  </div>
                </div>
              )}

              {/* DETALLE DE OBJETO / ARMA (WEAPON MASTERY 2024) */}
              {selectedEntry.item && (
                <div className="space-y-4">
                  <div className="flex flex-wrap gap-2 items-center">
                    {selectedEntry.item.weapon_mastery && (
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-gold/20 text-gold border border-gold/40 text-xs font-semibold">
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>
                          {language === "en" ? "Weapon Mastery (2024):" : "Dominio de Arma (2024):"} {selectedEntry.item.weapon_mastery}
                        </span>
                      </div>
                    )}
                    {selectedEntry.item.damage && (
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface border border-border-iron text-xs font-semibold text-main">
                        <Sword className="w-3.5 h-3.5 text-muted" />
                        <span>{selectedEntry.item.damage} {selectedEntry.item.damage_type || ""}</span>
                      </div>
                    )}
                    {selectedEntry.item.cost && (
                      <span className="px-2 py-0.5 rounded text-xs bg-surface text-muted border border-border-iron">
                        {selectedEntry.item.cost}
                      </span>
                    )}
                    {selectedEntry.item.weight && (
                      <span className="px-2 py-0.5 rounded text-xs bg-surface text-muted border border-border-iron">
                        {selectedEntry.item.weight}
                      </span>
                    )}
                  </div>

                  <div className="border-t border-border-iron/60 pt-3">
                    <MarkdownViewer content={selectedEntry.item.description || selectedEntry.content || ""} />
                  </div>
                </div>
              )}

              {/* RENDERIZADO MARKDOWN GENERAL (OKF O CONTENIDO SIN ESTRUCTURA ESPECÍFICA) */}
              {!selectedEntry.monster && !selectedEntry.spell && !selectedEntry.item && (
                <MarkdownViewer
                  content={selectedEntry.content || "Sin descripción disponible."}
                />
              )}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-muted text-sm text-center">
              {t("compendium.noResults")}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
