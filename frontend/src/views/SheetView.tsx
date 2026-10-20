import React, { useState } from "react";
import { useCharacter } from "../context/CharacterContext";
import { Download, Upload, Sparkles, Wand2, User } from "lucide-react";
import { api } from "../api/client";
import { FeatureDetailModal } from "../components/FeatureDetailModal";
import { AiPortraitModal } from "../components/AiPortraitModal";
import type { FeatureItemData } from "../api/types";

export const SheetView: React.FC = () => {
  const {
    activeCharacter,
    updateActiveCharacter,
    saveCurrentCharacter,
    openDiceDrawer,
    showToast,
  } = useCharacter();

  const [activeFeatureForModal, setActiveFeatureForModal] = useState<FeatureItemData | null>(null);
  const [isAiPortraitModalOpen, setIsAiPortraitModalOpen] = useState<boolean>(false);

  if (!activeCharacter) {
    return (
      <div className="h-full flex items-center justify-center p-8 text-center text-muted">
        <div>
          <p className="font-display text-2xl text-gold mb-2">No hay personaje seleccionado</p>
          <p className="text-sm">
            Selecciona uno en la barra superior o ve a la pestaña Forja para crear uno nuevo.
          </p>
        </div>
      </div>
    );
  }

  const {
    id,
    name,
    char_class,
    subclass,
    level,
    race,
    background,
    alignment,
    hp_current,
    hp_max,
    hp_temp,
    ac,
    speed,
    initiative,
    proficiency_bonus,
    abilities,
    skills,
    weapon_actions,
    features,
    senses,
    languages,
    appearance,
    portrait_base64,
  } = activeCharacter;

  const handleHpChange = (delta: number) => {
    const nextHp = Math.max(0, Math.min(hp_max + 50, hp_current + delta));
    updateActiveCharacter({ hp_current: nextHp });
  };

  const handleUploadPortrait = async () => {
    if (!id) return;
    try {
      const res = await api.uploadCharacterPortrait(id);
      const newB64 = res.portrait_base64 || res.character?.portrait_base64;
      if (res.success && newB64) {
        updateActiveCharacter({
          portrait_path: res.portrait_path || res.character?.portrait_path,
          portrait_base64: newB64,
          ...(res.character || {}),
        });
        showToast("Retrato del personaje actualizado con éxito", "success");
      } else if (res.error && res.error !== "Selección cancelada.") {
        showToast(res.error, "warn");
      }
    } catch (e) {
      showToast("Error al subir retrato", "warn");
    }
  };

  const handleAbilityRoll = (abilityKey: string, bonus: number) => {
    openDiceDrawer({
      dice: { "20": 1 },
      modifier: bonus,
      label: `Prueba de ${abilityKey}`,
    });
  };

  const handleSaveRoll = (e: React.MouseEvent, abilityKey: string, saveBonus: number) => {
    e.stopPropagation();
    openDiceDrawer({
      dice: { "20": 1 },
      modifier: saveBonus,
      label: `Salvación de ${abilityKey}`,
    });
  };

  const handleSkillRoll = (skillName: string, bonus: number) => {
    openDiceDrawer({
      dice: { "20": 1 },
      modifier: bonus,
      label: `Habilidad: ${skillName}`,
    });
  };

  const handleWeaponAttackRoll = (wName: string, hitBonusStr: string) => {
    const bonus = parseInt(String(hitBonusStr).replace("+", ""), 10) || 0;
    openDiceDrawer({
      dice: { "20": 1 },
      modifier: bonus,
      label: `Ataque con ${wName}`,
    });
  };

  const handleWeaponDamageRoll = (e: React.MouseEvent, wName: string, dmgFormula: string) => {
    e.stopPropagation();
    const match = String(dmgFormula)
      .trim()
      .match(/^(\d+)d(\d+)(?:\s*([+-]\s*\d+))?/i);
    if (match) {
      const count = parseInt(match[1], 10) || 1;
      const sides = match[2];
      const mod = match[3] ? parseInt(match[3].replace(/\s+/g, ""), 10) || 0 : 0;
      openDiceDrawer({
        dice: { [sides]: count },
        modifier: mod,
        label: `Daño de ${wName}`,
      });
    } else {
      openDiceDrawer({
        dice: { "8": 1 },
        modifier: 0,
        label: `Daño de ${wName}`,
      });
    }
  };

  const handleToggleFeatureUse = (featureIdx: number, slotIdx: number) => {
    const nextFeatures = [...(features || [])];
    const target = { ...nextFeatures[featureIdx] };
    const maxUses = target.uses_max || 0;
    const currentUses = target.uses_current ?? maxUses;
    const spentCount = maxUses - currentUses;
    const nextSpent = slotIdx < spentCount ? slotIdx : slotIdx + 1;
    target.uses_current = Math.max(0, maxUses - nextSpent);
    nextFeatures[featureIdx] = target;
    updateActiveCharacter({ features: nextFeatures });
  };

  const handleExportPdf = async () => {
    if (!id) return;
    try {
      showToast("Generando hoja oficial en PDF...", "info");
      const res = await api.exportPdf(id);
      if (res.success && res.path) {
        showToast(`PDF generado con éxito: ${res.path}`, "success");
      } else {
        showToast("Error al exportar PDF: " + (res.error || "Desconocido"), "warn");
      }
    } catch (e) {
      showToast("Excepción al exportar PDF", "warn");
    }
  };

  const handleExportJson = async () => {
    if (!id) return;
    try {
      const res = await api.exportCharacterJson(id);
      if (res.success && res.path) {
        showToast(`Ficha exportada a JSON: ${res.path}`, "success");
      } else if (res.error && res.error !== "Exportación cancelada.") {
        showToast(res.error, "warn");
      }
    } catch (e) {
      showToast("Error al exportar JSON", "warn");
    }
  };

  return (
    <div className="h-full overflow-y-auto p-4 md:p-6 space-y-5 max-w-7xl mx-auto">
      {/* 1. Hero Header del Personaje */}
      <section className="bg-card border border-border-iron rounded-lg p-4 md:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-col sm:flex-row items-center sm:items-start gap-4">
          {/* Retrato del Personaje Heroico */}
          <div className="relative group shrink-0">
            <div className="w-28 h-28 sm:w-32 sm:h-32 md:w-36 md:h-36 rounded-xl border-2 border-border-iron group-hover:border-gold bg-surface overflow-hidden flex items-center justify-center shadow-lg transition-all">
              {portrait_base64 ? (
                <img
                  src={portrait_base64}
                  alt={name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="flex flex-col items-center justify-center text-center p-2">
                  <span className="font-display font-bold text-3xl text-gold">
                    {name.slice(0, 2).toUpperCase()}
                  </span>
                  <span className="text-[10px] text-muted mt-1">Sin Retrato</span>
                </div>
              )}

              {/* Overlay al pasar el cursor */}
              <div className="absolute inset-0 bg-black/75 opacity-0 group-hover:opacity-100 flex flex-col items-center justify-center gap-1.5 p-2 transition-opacity">
                <button
                  onClick={handleUploadPortrait}
                  className="w-full px-2 py-1 bg-surface hover:bg-gold hover:text-canvas border border-border-iron rounded text-[11px] font-semibold text-main transition-colors flex items-center justify-center gap-1"
                  title="Subir archivo de imagen desde disco"
                >
                  <Upload className="w-3 h-3" />
                  <span>Subir</span>
                </button>
                <button
                  onClick={() => setIsAiPortraitModalOpen(true)}
                  className="w-full px-2 py-1 bg-gold hover:bg-gold-hover text-canvas rounded text-[11px] font-bold transition-colors flex items-center justify-center gap-1 shadow-sm"
                  title="Generar retrato con IA basándose en apariencia"
                >
                  <Wand2 className="w-3 h-3" />
                  <span>Retrato IA</span>
                </button>
              </div>
            </div>

            {/* Acciones directas bajo el retrato */}
            <div className="flex items-center justify-center gap-1.5 mt-2">
              <button
                onClick={handleUploadPortrait}
                className="px-2 py-0.5 rounded bg-surface border border-border-iron hover:border-gold text-[10px] font-medium text-muted hover:text-main transition-colors flex items-center gap-1"
                title="Subir imagen"
              >
                <Upload className="w-2.5 h-2.5" />
                <span>Subir</span>
              </button>
              <button
                onClick={() => setIsAiPortraitModalOpen(true)}
                className="px-2 py-0.5 rounded bg-gold/15 border border-gold/40 hover:bg-gold hover:text-canvas text-[10px] font-bold text-gold transition-colors flex items-center gap-1"
                title="Generador IA"
              >
                <Sparkles className="w-2.5 h-2.5" />
                <span>IA</span>
              </button>
            </div>
          </div>

          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="font-display font-bold text-2xl md:text-3xl text-gold">{name}</h1>
              <span className="text-xs uppercase px-2 py-0.5 rounded bg-surface border border-border-iron font-semibold text-muted">
                Nivel {level}
              </span>
              {alignment && (
                <span className="text-xs text-muted/80 hidden sm:inline">• {alignment}</span>
              )}
            </div>
            <p className="text-sm text-muted">
              {race} • {char_class} {subclass && `(${subclass})`} • Trasfondo:{" "}
              {background || "Sin trasfondo"}
            </p>
            {(senses || languages) && (
              <p className="text-xs text-muted/80">
                {senses && <span>Sentidos: {senses}</span>}
                {senses && languages && <span> • </span>}
                {languages && <span>Idiomas: {languages}</span>}
              </p>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleExportJson}
            className="px-3 py-1.5 bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-medium rounded transition-colors text-muted hover:text-main"
          >
            Exportar JSON
          </button>
          <button
            onClick={handleExportPdf}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-medium rounded transition-colors text-muted hover:text-main"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Exportar PDF</span>
          </button>
          <button
            onClick={saveCurrentCharacter}
            className="px-4 py-1.5 bg-crimson hover:bg-crimson-hover text-white text-xs font-semibold rounded transition-all shadow-sm active:scale-95"
          >
            Guardar Cambios
          </button>
        </div>
      </section>

      {/* 2. Grid de Vitales y Estadísticas de Combate Táctico */}
      <section className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
        {/* Puntos de Golpe */}
        <div className="col-span-2 bg-card border border-border-iron rounded-lg p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-muted font-semibold uppercase tracking-wider">
            <span>Puntos de Golpe</span>
            <span>{hp_max} Máx</span>
          </div>
          <div className="flex items-center justify-between my-2">
            <button
              onClick={() => handleHpChange(-1)}
              className="w-8 h-8 rounded border border-border-iron hover:border-crimson text-crimson font-stat font-bold text-lg flex items-center justify-center bg-surface"
            >
              -
            </button>
            <div className="text-center">
              <span className="font-stat font-bold text-3xl text-main">{hp_current}</span>
              {hp_temp > 0 && <span className="text-xs text-gold ml-1">+{hp_temp}</span>}
            </div>
            <button
              onClick={() => handleHpChange(1)}
              className="w-8 h-8 rounded border border-border-iron hover:border-emerald-500 text-emerald-400 font-stat font-bold text-lg flex items-center justify-center bg-surface"
            >
              +
            </button>
          </div>
          <div className="w-full bg-surface h-1.5 rounded-full overflow-hidden">
            <div
              className="h-full bg-crimson transition-all duration-300"
              style={{ width: `${Math.min(100, Math.max(0, (hp_current / Math.max(1, hp_max)) * 100))}%` }}
            />
          </div>
        </div>

        {/* Clase de Armadura */}
        <div className="bg-card border border-border-iron rounded-lg p-3 text-center flex flex-col justify-center">
          <span className="text-xs text-muted font-semibold uppercase tracking-wider">
            Armadura
          </span>
          <span className="font-stat font-bold text-3xl text-gold mt-1">{ac}</span>
        </div>

        {/* Iniciativa */}
        <div
          onClick={() =>
            openDiceDrawer({
              dice: { "20": 1 },
              modifier: initiative,
              label: "Tirada de Iniciativa",
            })
          }
          className="bg-card border border-border-iron hover:border-gold rounded-lg p-3 text-center flex flex-col justify-center cursor-pointer transition-colors group"
        >
          <span className="text-xs text-muted group-hover:text-gold font-semibold uppercase tracking-wider">
            Iniciativa
          </span>
          <span className="font-stat font-bold text-3xl text-main group-hover:text-gold mt-1">
            {initiative >= 0 ? `+${initiative}` : initiative}
          </span>
        </div>

        {/* Velocidad */}
        <div className="bg-card border border-border-iron rounded-lg p-3 text-center flex flex-col justify-center">
          <span className="text-xs text-muted font-semibold uppercase tracking-wider">
            Velocidad
          </span>
          <span className="font-stat font-bold text-3xl text-main mt-1">
            {speed} <span className="text-xs font-normal text-muted">pies</span>
          </span>
        </div>

        {/* Bonificador de Competencia */}
        <div className="bg-card border border-border-iron rounded-lg p-3 text-center flex flex-col justify-center">
          <span className="text-xs text-muted font-semibold uppercase tracking-wider">
            Competencia
          </span>
          <span className="font-stat font-bold text-3xl text-gold mt-1">+{proficiency_bonus}</span>
        </div>
      </section>

      {/* 3. Matriz de Atributos Principales (6 Características) */}
      <section className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
        {Object.entries(abilities || {}).map(([key, data]) => {
          const modStr = data.bonus >= 0 ? `+${data.bonus}` : `${data.bonus}`;
          return (
            <div
              key={key}
              onClick={() => handleAbilityRoll(key, data.bonus)}
              className="bg-card border border-border-iron hover:border-gold rounded-lg p-3 text-center cursor-pointer transition-all hover:scale-[1.01] group"
            >
              <div className="text-xs font-stat font-semibold tracking-widest text-muted uppercase group-hover:text-gold">
                {key}
              </div>
              <div className="font-stat font-bold text-3xl text-gold my-1">{modStr}</div>
              <div className="inline-block px-2 py-0.5 rounded bg-surface border border-border-iron text-xs font-stat text-muted">
                {data.base}
              </div>
              <button
                onClick={(e) => handleSaveRoll(e, key, data.save_bonus)}
                title={`Tirar Salvación de ${key}`}
                className="w-full mt-2 pt-2 border-t border-border-iron/60 text-[10px] text-muted hover:text-gold flex items-center justify-center gap-1 transition-colors"
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    data.proficient ? "bg-gold" : "bg-border-iron"
                  }`}
                />
                <span>Salvación:</span>
                <span className="font-stat font-semibold text-main">
                  {data.save_bonus >= 0 ? `+${data.save_bonus}` : data.save_bonus}
                </span>
              </button>
            </div>
          );
        })}
      </section>

      {/* 4. Apariencia y Rasgos Físicos (Para generación de Retratos) */}
      <section className="bg-card border border-border-iron rounded-xl p-4 space-y-3">
        <div className="flex items-center justify-between border-b border-border-iron pb-2 flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <User className="w-4 h-4 text-gold" />
            <h2 className="font-display font-semibold text-base text-gold">
              Apariencia Física y Rasgos del Personaje
            </h2>
          </div>
          <button
            onClick={() => setIsAiPortraitModalOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-gold/15 hover:bg-gold hover:text-canvas border border-gold/40 text-gold text-xs font-bold transition-all flex items-center gap-1.5 shadow-xs active:scale-95"
            title="Generar ilustración del personaje con IA"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Generar Retrato con IA</span>
          </button>
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wider text-muted">
            Descripción de Aspecto, Fisonomía y Marcas Distintivas
          </label>
          <textarea
            value={appearance || ""}
            onChange={(e) => updateActiveCharacter({ appearance: e.target.value })}
            placeholder="Describe aquí la apariencia de tu personaje (altura, peso, ojos, cabello, tono de piel, vestimenta, armadura, cicatrices o expresión)..."
            rows={3}
            className="w-full bg-input text-main border border-border-iron rounded-lg p-2.5 text-xs focus:border-gold outline-none leading-relaxed transition-colors resize-none"
          />
          <p className="text-[11px] text-muted">
            Este texto se transmite de forma automática al Generador de Retratos IA para componer el prompt visual en estilos como Pixel Art, Fantasía Épica u Óleo Clásico.
          </p>
        </div>
      </section>

      {/* 5. Columnas de Acciones de Combate y Habilidades */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Columna Izquierda: Acciones de Arma */}
        <div className="md:col-span-2 space-y-3">
          <h2 className="font-display font-semibold text-lg text-gold flex items-center justify-between">
            <span>Acciones y Ataques de Combate</span>
            <span className="text-xs text-muted font-sans font-normal">
              Clic en arma para impacto • Clic en daño para tirar daño
            </span>
          </h2>

          <div className="space-y-2">
            {weapon_actions && weapon_actions.length > 0 ? (
              weapon_actions.map((w, idx) => (
                <div
                  key={idx}
                  onClick={() => handleWeaponAttackRoll(w.name, w.hit_dc)}
                  className="bg-card border border-border-iron hover:border-gold/70 rounded-lg p-3.5 flex items-center justify-between cursor-pointer transition-colors"
                >
                  <div>
                    <h3 className="font-semibold text-sm text-main">{w.name}</h3>
                    <p className="text-xs text-muted">
                      {w.type} • Alcance: {w.range_val} {w.notes ? `• ${w.notes}` : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className="font-stat font-bold text-sm text-gold">
                        {w.hit_dc} impacto
                      </div>
                      <div className="text-[10px] text-muted">1d20</div>
                    </div>
                    <button
                      onClick={(e) => handleWeaponDamageRoll(e, w.name, w.damage_dice)}
                      className="px-2.5 py-1.5 rounded bg-surface hover:bg-gold hover:text-canvas border border-border-iron font-stat text-xs text-main font-semibold transition-colors"
                      title="Tirar dados de daño"
                    >
                      {w.damage_dice} {w.damage_type}
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="bg-card border border-border-iron rounded-lg p-4 text-center text-xs text-muted">
                No hay armas registradas.
              </div>
            )}
          </div>

          {/* Rasgos y Dotes de Clase */}
          <h2 className="font-display font-semibold text-lg text-gold pt-2">
            Rasgos y Habilidades Especiales
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {features && features.length > 0 ? (
              features.map((f, idx) => {
                const maxUses = f.uses_max || 0;
                const currentUses = f.uses_current ?? maxUses;
                const spentUses = maxUses - currentUses;
                return (
                  <div
                    key={idx}
                    onClick={() => setActiveFeatureForModal(f)}
                    className="bg-card border border-border-iron hover:border-gold/80 rounded-lg p-3 flex flex-col justify-between cursor-pointer transition-all hover:scale-[1.01] group"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-semibold text-xs text-main group-hover:text-gold transition-colors">{f.name}</h4>
                        <span className="text-[10px] text-gold">{f.source}</span>
                      </div>
                      <p className="text-xs text-muted leading-relaxed line-clamp-3">{f.description}</p>
                    </div>

                    {maxUses > 0 && maxUses <= 10 && (
                      <div className="mt-2 pt-2 border-t border-border-iron/50 flex items-center justify-between text-[11px]" onClick={(e) => e.stopPropagation()}>
                        <span className="text-muted">
                          Usos ({f.recharge === "SR" ? "Desc. Corto" : "Desc. Largo"}):
                        </span>
                        <div className="flex items-center gap-1">
                          {Array.from({ length: maxUses }).map((_, sIdx) => (
                            <button
                              key={sIdx}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleToggleFeatureUse(idx, sIdx);
                              }}
                              className={`w-3.5 h-3.5 rounded-full border transition-all ${
                                sIdx < spentUses
                                  ? "border-border-iron bg-surface opacity-40"
                                  : "border-gold bg-gold"
                              }`}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div className="col-span-2 bg-card border border-border-iron rounded-lg p-4 text-center text-xs text-muted">
                No hay rasgos registrados.
              </div>
            )}
          </div>
        </div>

        {/* Columna Derecha: Habilidades con Tirada Directa */}
        <div className="space-y-3">
          <h2 className="font-display font-semibold text-lg text-gold">Habilidades y Pericias</h2>
          <div className="bg-card border border-border-iron rounded-lg divide-y divide-border-iron/60 overflow-hidden">
            {Object.entries(skills || {}).map(([sName, sData]) => {
              const sign = sData.bonus >= 0 ? `+${sData.bonus}` : `${sData.bonus}`;
              return (
                <div
                  key={sName}
                  onClick={() => handleSkillRoll(sName, sData.bonus)}
                  className="px-3.5 py-2 flex items-center justify-between text-xs hover:bg-surface/50 cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        sData.expertise
                          ? "bg-gold ring-2 ring-gold/40"
                          : sData.proficient
                          ? "bg-gold"
                          : "bg-border-iron"
                      }`}
                    />
                    <span
                      className={`${
                        sData.proficient ? "font-semibold text-main" : "text-muted"
                      }`}
                    >
                      {sName}
                    </span>
                  </div>
                  <span className="font-stat font-bold text-main">{sign}</span>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Modal Interactivo de Rasgo Pop-Forward */}
      <FeatureDetailModal
        feature={activeFeatureForModal}
        isOpen={!!activeFeatureForModal}
        onClose={() => setActiveFeatureForModal(null)}
        onSpendUse={() => {
          if (!activeFeatureForModal) return;
          const idx = (features || []).findIndex((f) => f.name === activeFeatureForModal.name);
          if (idx >= 0) {
            const next = [...(features || [])];
            const target = { ...next[idx] };
            const maxU = target.uses_max || 0;
            const curU = target.uses_current ?? maxU;
            if (curU > 0) {
              target.uses_current = curU - 1;
              next[idx] = target;
              updateActiveCharacter({ features: next });
              setActiveFeatureForModal(target);
              showToast(`1 uso de ${target.name} consumido`, "info");
            }
          }
        }}
        onRecoverUse={() => {
          if (!activeFeatureForModal) return;
          const idx = (features || []).findIndex((f) => f.name === activeFeatureForModal.name);
          if (idx >= 0) {
            const next = [...(features || [])];
            const target = { ...next[idx] };
            const maxU = target.uses_max || 0;
            const curU = target.uses_current ?? 0;
            if (curU < maxU) {
              target.uses_current = curU + 1;
              next[idx] = target;
              updateActiveCharacter({ features: next });
              setActiveFeatureForModal(target);
              showToast(`1 uso de ${target.name} recuperado`, "info");
            }
          }
        }}
        onToggleUse={(slotIdx) => {
          if (!activeFeatureForModal) return;
          const idx = (features || []).findIndex((f) => f.name === activeFeatureForModal.name);
          if (idx >= 0) {
            handleToggleFeatureUse(idx, slotIdx);
            const target = (features || [])[idx];
            if (target) setActiveFeatureForModal({ ...target });
          }
        }}
        onRollDice={(formula, label) => {
          const match = formula.match(/(\d*)d(\d+)/i);
          if (match) {
            const cnt = parseInt(match[1] || "1", 10);
            const s = match[2];
            openDiceDrawer({ dice: { [s]: cnt }, label });
          }
        }}
      />

      {/* Modal de Generador de Retrato IA */}
      <AiPortraitModal
        isOpen={isAiPortraitModalOpen}
        onClose={() => setIsAiPortraitModalOpen(false)}
        character={activeCharacter}
        onPortraitGenerated={(newImg) => {
          updateActiveCharacter({ portrait_base64: newImg });
          showToast("Retrato actualizado en la ficha", "success");
        }}
      />
    </div>
  );
};
