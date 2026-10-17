import React, { useState, useEffect } from "react";
import { api } from "../api/client";
import type { CompendiumCategory, CompendiumSearchResult } from "../api/types";
import { Search } from "lucide-react";

export const CompendiumView: React.FC = () => {
  const [categories, setCategories] = useState<CompendiumCategory[]>([]);
  const [selectedCat, setSelectedCat] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [results, setResults] = useState<CompendiumSearchResult[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    async function loadCategories() {
      try {
        const cats = await api.getCompendiumCategories();
        setCategories(cats);
        if (cats.length > 0) setSelectedCat(cats[0].id);
      } catch (e) {
        console.error("Error loading categories:", e);
      }
    }
    loadCategories();
  }, []);

  useEffect(() => {
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const queryToRun = searchQuery.trim();
        const data = await api.searchCompendium(queryToRun, selectedCat || undefined);
        setResults(data);
        if (data.length > 0) {
          loadEntry(data[0].category, data[0].name);
        } else {
          setSelectedEntry(null);
        }
      } catch (e) {
        console.error("Error searching compendium:", e);
      } finally {
        setLoading(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [searchQuery, selectedCat]);

  const loadEntry = async (category: string, name: string) => {
    try {
      const entry = await api.getCompendiumEntry(category, name);
      setSelectedEntry(entry);
    } catch (e) {
      console.error("Error loading entry:", e);
    }
  };

  return (
    <div className="h-full flex flex-col p-4 md:p-6 space-y-4 max-w-7xl mx-auto overflow-hidden">
      {/* 1. Header del Compendio y Buscador Central */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-border-iron pb-3 shrink-0">
        <div>
          <h1 className="font-display font-bold text-2xl text-gold">Compendio de Reglas Oficiales (OKF)</h1>
          <p className="text-xs text-muted">Consulta rápida de clases, dotes, conjuros y mecánicas de juego.</p>
        </div>

        {/* Input de Búsqueda */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-muted pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar en el compendio..."
            className="w-full bg-input text-main border border-border-iron rounded-lg pl-9 pr-3 py-1.5 text-sm focus:border-gold outline-none transition-colors"
          />
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
          Todo
        </button>
        {categories.map((c) => (
          <button
            key={c.id}
            onClick={() => setSelectedCat(c.id)}
            className={`px-3 py-1 rounded text-xs font-semibold whitespace-nowrap transition-colors ${
              selectedCat === c.id ? "bg-gold text-canvas" : "bg-card text-muted hover:text-main"
            }`}
          >
            {c.label} ({c.count})
          </button>
        ))}
      </div>

      {/* 3. Panel Dividido: Lista de Resultados a la izquierda, Detalle a la derecha */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4 min-h-0 overflow-hidden">
        {/* Lista de Entradas */}
        <div className="bg-card border border-border-iron rounded-xl overflow-y-auto divide-y divide-border-iron/50">
          {loading ? (
            <div className="p-6 text-center text-xs text-muted">Buscando en el compendio...</div>
          ) : results.length > 0 ? (
            results.map((r, idx) => (
              <div
                key={idx}
                onClick={() => loadEntry(r.category, r.name)}
                className={`p-3 cursor-pointer transition-colors ${
                  selectedEntry?.name === r.name ? "bg-surface border-l-2 border-gold" : "hover:bg-surface/50"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <h4 className="font-semibold text-xs text-main">{r.name}</h4>
                  <span className="text-[10px] uppercase font-stat text-gold/80">{r.category}</span>
                </div>
                {r.snippet && <p className="text-[11px] text-muted line-clamp-2 leading-relaxed">{r.snippet}</p>}
              </div>
            ))
          ) : (
            <div className="p-6 text-center text-xs text-muted">No se encontraron resultados para la búsqueda.</div>
          )}
        </div>

        {/* Visor de Contenido Detallado */}
        <div className="md:col-span-2 bg-card border border-border-iron rounded-xl p-5 overflow-y-auto space-y-4">
          {selectedEntry ? (
            <div>
              <div className="border-b border-border-iron pb-3 mb-4">
                <span className="text-[10px] uppercase font-stat tracking-widest text-gold">
                  {selectedEntry.category}
                </span>
                <h2 className="font-display font-bold text-2xl text-main mt-0.5">{selectedEntry.name}</h2>
              </div>

              {/* Contenido Renderizado */}
              <div className="prose prose-invert max-w-none text-xs md:text-sm text-main/90 leading-relaxed space-y-3 font-body whitespace-pre-wrap">
                {selectedEntry.content || "Sin descripción disponible."}
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-muted text-sm text-center">
              Selecciona una entrada de la lista para ver su descripción oficial.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
