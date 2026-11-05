import React, { useState, useEffect } from "react";
import { api } from "../api/client";
import type { CompendiumItemSummary, CompendiumItemDetail, EquipmentItemData } from "../api/types";
import { useTranslation } from "../i18n";
import { X, Search, Plus, Trash2, Check, Shield } from "lucide-react";

interface EquipmentManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentEquipment: EquipmentItemData[];
  onAddItem: (item: any) => Promise<boolean>;
  onRemoveItem: (itemName: string) => Promise<boolean>;
}

const ITEM_CATEGORIES = [
  { id: "all", es: "Todos", en: "All" },
  { id: "weapon", es: "Armas", en: "Weapons" },
  { id: "armor", es: "Armaduras", en: "Armor" },
  { id: "gear", es: "Equipo", en: "Adventuring Gear" },
  { id: "potion", es: "Pociones", en: "Potions" },
  { id: "wondrous", es: "Objetos Mágicos", en: "Magic Items" },
];

export const EquipmentManagerModal: React.FC<EquipmentManagerModalProps> = ({
  isOpen,
  onClose,
  currentEquipment,
  onAddItem,
  onRemoveItem,
}) => {
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [items, setItems] = useState<CompendiumItemSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [previewItem, setPreviewItem] = useState<CompendiumItemDetail | CompendiumItemSummary | null>(null);
  const { language } = useTranslation();

  // Escape key handler
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

  // Debounced search via Compendium SQLite
  useEffect(() => {
    if (!isOpen) return;
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const itemTypeParam = selectedCategory === "all" ? undefined : selectedCategory;
        const res = await api.searchItems(
          searchQuery.trim(),
          itemTypeParam,
          undefined, // rarity
          undefined, // weaponMastery
          "5.5e",
          language,
          1,
          50
        );
        const list = res?.items || [];
        setItems(list);
        if (list.length > 0) {
          setPreviewItem((prev) => {
            if (!prev) return list[0];
            const exists = list.find((it) => it.name === prev.name);
            return exists || list[0];
          });
        } else {
          setPreviewItem(null);
        }
      } catch (err) {
        console.error("Error al buscar ítems en compendio:", err);
        setItems([]);
      } finally {
        setLoading(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [isOpen, searchQuery, selectedCategory, language]);

  if (!isOpen) return null;

  const safeCurrent = Array.isArray(currentEquipment) ? currentEquipment : [];
  const currentNamesSet = new Set(
    safeCurrent.map((it) => String(it.name).toLowerCase().trim())
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
            <Shield className="w-5 h-5 text-gold" />
            <div>
              <h2 className="font-display font-bold text-lg text-gold">
                {language === "en" ? "Equipment & Armory Compendium" : "Compendio de Equipo y Armería"}
              </h2>
              <p className="text-xs text-muted">
                {language === "en"
                  ? `Equip weapons, armor, and adventuring gear (${safeCurrent.length} items carried)`
                  : `Equipa armas, armaduras y equipo de aventurero (${safeCurrent.length} objetos en inventario)`}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg border border-border-iron hover:border-gold text-muted hover:text-main transition-colors"
            title={language === "en" ? "Close" : "Cerrar"}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Filtros y Búsqueda */}
        <div className="p-3 border-b border-border-iron bg-surface/30 space-y-2 shrink-0">
          <div className="flex flex-col sm:flex-row gap-2 items-center">
            {/* Buscador */}
            <div className="relative flex-1 w-full">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-muted pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={language === "en" ? "Search weapon, armor, potion..." : "Buscar arma, armadura, poción..."}
                className="w-full bg-input text-main border border-border-iron rounded-lg pl-9 pr-3 py-1.5 text-xs focus:border-gold outline-none transition-colors"
              />
            </div>

            {/* Categorías */}
            <div className="flex items-center gap-1 overflow-x-auto w-full sm:w-auto pb-0.5">
              {ITEM_CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`px-2.5 py-1 rounded text-[11px] font-semibold whitespace-nowrap transition-colors ${
                    selectedCategory === cat.id
                      ? "bg-gold text-canvas"
                      : "bg-surface border border-border-iron text-muted hover:text-main"
                  }`}
                >
                  {language === "en" ? cat.en : cat.es}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Cuerpo del Modal: 2 Columnas */}
        <div className="flex-1 flex flex-col md:flex-row min-h-0 overflow-hidden">
          {/* Columna Izquierda: Lista de Ítems */}
          <div className="w-full md:w-3/5 overflow-y-auto p-3 space-y-2 border-b md:border-b-0 md:border-r border-border-iron">
            {loading ? (
              <div className="py-12 text-center text-xs text-muted animate-pulse">
                {language === "en" ? "Searching compendium items..." : "Buscando ítems en el compendio..."}
              </div>
            ) : items.length === 0 ? (
              <div className="py-12 text-center text-xs text-muted">
                {language === "en" ? "No items found in compendium." : "No se encontraron ítems en el compendio."}
              </div>
            ) : (
              items.map((it) => {
                const isAdded = currentNamesSet.has(it.name.toLowerCase().trim());
                const isSelected = previewItem?.name === it.name;

                return (
                  <div
                    key={it.entity_id || it.name}
                    onClick={() => setPreviewItem(it)}
                    className={`p-2.5 rounded-lg border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                      isSelected
                        ? "bg-surface border-gold/70"
                        : "bg-surface/50 border-border-iron hover:border-gold/40 hover:bg-surface/80"
                    }`}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold text-xs text-main truncate">
                          {language === "en" && it.name_en ? it.name_en : it.name}
                        </h4>
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-surface border border-border-iron text-gold uppercase shrink-0">
                          {it.item_type || "Equipo"}
                        </span>
                      </div>
                      <p className="text-[11px] text-muted truncate mt-0.5">
                        {it.damage ? `${it.damage} ${it.damage_type || ""} • ` : ""}
                        {it.cost ? `${it.cost} • ` : ""}
                        {it.weight || ""}
                        {it.weapon_mastery ? ` • Dominio: ${it.weapon_mastery}` : ""}
                      </p>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0" onClick={(e) => e.stopPropagation()}>
                      {isAdded ? (
                        <div className="flex items-center gap-1">
                          <span className="text-[10px] text-green-400 bg-green-500/10 border border-green-500/30 px-2 py-0.5 rounded font-semibold flex items-center gap-1">
                            <Check className="w-3 h-3" /> {language === "en" ? "Equipped" : "En Equipo"}
                          </span>
                          <button
                            onClick={() => onRemoveItem(it.name)}
                            className="p-1 rounded bg-crimson/20 hover:bg-crimson text-crimson hover:text-white transition-colors"
                            title={language === "en" ? "Remove from inventory" : "Eliminar de inventario"}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => onAddItem(it)}
                          className="px-2.5 py-1 rounded bg-gold hover:bg-gold-hover text-canvas font-semibold text-xs flex items-center gap-1 transition-all active:scale-95 shadow-xs"
                        >
                          <Plus className="w-3.5 h-3.5" />
                          <span>{language === "en" ? "Add" : "Añadir"}</span>
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
            {previewItem ? (
              <div className="space-y-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-surface border border-border-iron text-gold uppercase">
                      {previewItem.item_type || "Equipo"}
                    </span>
                    <span className="text-[10px] text-muted">{previewItem.rarity || "Común"}</span>
                  </div>
                  <h3 className="font-display font-bold text-lg text-gold">
                    {language === "en" && previewItem.name_en ? previewItem.name_en : previewItem.name}
                  </h3>
                  {previewItem.name_en && previewItem.name_en !== previewItem.name && (
                    <p className="text-xs text-muted italic">
                      {language === "en" ? previewItem.name : previewItem.name_en}
                    </p>
                  )}
                </div>

                <div className="text-xs space-y-1 bg-surface p-2.5 rounded border border-border-iron">
                  {previewItem.cost && (
                    <div>
                      <span className="text-muted">{language === "en" ? "Cost:" : "Precio:"}</span>{" "}
                      <span className="text-main font-medium">{previewItem.cost}</span>
                    </div>
                  )}
                  {previewItem.weight && (
                    <div>
                      <span className="text-muted">{language === "en" ? "Weight:" : "Peso:"}</span>{" "}
                      <span className="text-main font-medium">{previewItem.weight}</span>
                    </div>
                  )}
                  {previewItem.damage && (
                    <div>
                      <span className="text-muted">{language === "en" ? "Damage:" : "Daño:"}</span>{" "}
                      <span className="text-main font-medium">{previewItem.damage} {previewItem.damage_type || ""}</span>
                    </div>
                  )}
                  {previewItem.weapon_mastery && (
                    <div>
                      <span className="text-muted">{language === "en" ? "Mastery:" : "Dominio de Arma:"}</span>{" "}
                      <span className="text-gold font-semibold">{previewItem.weapon_mastery}</span>
                    </div>
                  )}
                </div>

                <div className="text-xs text-muted leading-relaxed max-h-56 overflow-y-auto pr-1 whitespace-pre-line">
                  {previewItem.description || (language === "en" ? "No additional description available." : "Sin descripción adicional disponible.")}
                </div>
              </div>
            ) : (
              <div className="py-20 text-center text-xs text-muted">
                {language === "en" ? "Select an item to view properties" : "Selecciona un objeto para ver sus propiedades"}
              </div>
            )}

            {previewItem && (
              <div className="pt-3 border-t border-border-iron mt-4">
                {currentNamesSet.has(previewItem.name.toLowerCase().trim()) ? (
                  <button
                    onClick={() => onRemoveItem(previewItem.name)}
                    className="w-full py-2 rounded-lg bg-crimson/20 hover:bg-crimson text-crimson hover:text-white font-semibold text-xs flex items-center justify-center gap-1.5 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                    <span>{language === "en" ? "Remove from Character" : "Eliminar del Personaje"}</span>
                  </button>
                ) : (
                  <button
                    onClick={() => onAddItem(previewItem)}
                    className="w-full py-2 rounded-lg bg-gold hover:bg-gold-hover text-canvas font-semibold text-xs flex items-center justify-center gap-1.5 transition-colors shadow-sm"
                  >
                    <Plus className="w-4 h-4" />
                    <span>{language === "en" ? "Equip to Character" : "Añadir a la Ficha"}</span>
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
