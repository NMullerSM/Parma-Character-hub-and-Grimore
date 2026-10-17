import React from "react";
import { useCharacter } from "../context/CharacterContext";
import { Download } from "lucide-react";
import { api } from "../api/client";

export const SheetView: React.FC = () => {
  const { activeCharacter, updateActiveCharacter, saveCurrentCharacter, openDiceDrawer, showToast } =
    useCharacter();

  if (!activeCharacter) {
    return (
      <div className="h-full flex items-center justify-center p-8 text-center text-muted">
        <div>
          <p className="font-display text-2xl text-gold mb-2">No hay personaje seleccionado</p>
          <p className="text-sm">Selecciona uno en la barra superior o ve a la pestaña Forja para crear uno nuevo.</p>
        </div>
      </div>
    );
  }

  const {
    name,
    char_class,
    subclass,
    level,
    race,
    background,
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
  } = activeCharacter;

  const handleHpChange = (delta: number) => {
    const nextHp = Math.max(0, Math.min(hp_max + 50, hp_current + delta));
    updateActiveCharacter({ hp_current: nextHp });
  };

  const handleAbilityRoll = (abilityKey: string, bonus: number) => {
    openDiceDrawer({
      dice: { "20": 1 },
      modifier: bonus,
      label: `Prueba de ${abilityKey}`,
    });
  };

  const handleSkillRoll = (skillName: string, bonus: number) => {
    openDiceDrawer({
      dice: { "20": 1 },
      modifier: bonus,
      label: `Habilidad: ${skillName}`,
    });
  };

  const handleWeaponRoll = (wName: string, hitBonusStr: string, dmgDice: string) => {
    const bonus = parseInt(hitBonusStr.replace("+", ""), 10) || 0;
    openDiceDrawer({
      dice: { "20": 1 },
      modifier: bonus,
      label: `Ataque: ${wName} (${dmgDice})`,
    });
  };

  const handleExportPdf = async () => {
    if (!activeCharacter.id) return;
    try {
      showToast("Generando hoja oficial en PDF...", "info");
      const res = await api.exportPdf(activeCharacter.id);
      if (res.success && res.path) {
        showToast(`PDF generado con éxito: ${res.path}`, "success");
      } else {
        showToast("Error al exportar PDF: " + (res.error || "Desconocido"), "warn");
      }
    } catch (e) {
      showToast("Excepción al exportar PDF", "warn");
    }
  };

  return (
    <div className="h-full overflow-y-auto p-4 md:p-6 space-y-5 max-w-7xl mx-auto">
      {/* 1. Hero Header del Personaje */}
      <section className="bg-card border border-border-iron rounded-lg p-4 md:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h1 className="font-display font-bold text-2xl md:text-3xl text-gold">{name}</h1>
            <span className="text-xs uppercase px-2 py-0.5 rounded bg-surface border border-border-iron font-semibold text-muted">
              Nivel {level}
            </span>
          </div>
          <p className="text-sm text-muted">
            {race} • {char_class} {subclass && `(${subclass})`} • Trasfondo: {background || "Sin trasfondo"}
          </p>
        </div>

        <div className="flex items-center gap-2">
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
            <span>{hp_max} Max</span>
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
              style={{ width: `${Math.min(100, Math.max(0, (hp_current / hp_max) * 100))}%` }}
            />
          </div>
        </div>

        {/* Clase de Armadura */}
        <div className="bg-card border border-border-iron rounded-lg p-3 text-center flex flex-col justify-center">
          <span className="text-xs text-muted font-semibold uppercase tracking-wider">Armadura</span>
          <span className="font-stat font-bold text-3xl text-gold mt-1">{ac}</span>
        </div>

        {/* Iniciativa */}
        <div
          onClick={() => openDiceDrawer({ dice: { "20": 1 }, modifier: initiative, label: "Tirada de Iniciativa" })}
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
          <span className="text-xs text-muted font-semibold uppercase tracking-wider">Velocidad</span>
          <span className="font-stat font-bold text-3xl text-main mt-1">{speed} <span className="text-xs font-normal text-muted">pies</span></span>
        </div>

        {/* Bonificador de Competencia */}
        <div className="bg-card border border-border-iron rounded-lg p-3 text-center flex flex-col justify-center">
          <span className="text-xs text-muted font-semibold uppercase tracking-wider">Competencia</span>
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
              className="bg-card border border-border-iron hover:border-gold rounded-lg p-3 text-center cursor-pointer transition-all hover:scale-[1.02] group"
            >
              <div className="text-xs font-stat font-semibold tracking-widest text-muted uppercase group-hover:text-gold">
                {key}
              </div>
              <div className="font-stat font-bold text-3xl text-gold my-1">{modStr}</div>
              <div className="inline-block px-2 py-0.5 rounded bg-surface border border-border-iron text-xs font-stat text-muted">
                {data.base}
              </div>
              <div className="mt-2 pt-2 border-t border-border-iron/60 text-[10px] text-muted flex items-center justify-center gap-1">
                <span>Salvación:</span>
                <span className="font-stat font-semibold text-main">
                  {data.save_bonus >= 0 ? `+${data.save_bonus}` : data.save_bonus}
                </span>
              </div>
            </div>
          );
        })}
      </section>

      {/* 4. Columnas de Acciones de Combate y Habilidades */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Columna Izquierda: Acciones de Arma */}
        <div className="md:col-span-2 space-y-3">
          <h2 className="font-display font-semibold text-lg text-gold flex items-center justify-between">
            <span>Acciones y Ataques de Combate</span>
            <span className="text-xs text-muted font-sans font-normal">Clic para tirar ataque</span>
          </h2>

          <div className="space-y-2">
            {weapon_actions && weapon_actions.length > 0 ? (
              weapon_actions.map((w, idx) => (
                <div
                  key={idx}
                  onClick={() => handleWeaponRoll(w.name, w.hit_dc, w.damage_dice)}
                  className="bg-card border border-border-iron hover:border-gold/70 rounded-lg p-3.5 flex items-center justify-between cursor-pointer transition-colors"
                >
                  <div>
                    <h3 className="font-semibold text-sm text-main">{w.name}</h3>
                    <p className="text-xs text-muted">
                      {w.type} • Alcance: {w.range_val} • {w.notes}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="font-stat font-bold text-sm text-gold">{w.hit_dc} impacto</div>
                    <div className="font-stat text-xs text-main">{w.damage_dice} {w.damage_type}</div>
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
          <h2 className="font-display font-semibold text-lg text-gold pt-2">Rasgos y Habilidades Especiales</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {features && features.length > 0 ? (
              features.map((f, idx) => (
                <div key={idx} className="bg-card border border-border-iron rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-semibold text-xs text-main">{f.name}</h4>
                    <span className="text-[10px] text-gold">{f.source}</span>
                  </div>
                  <p className="text-xs text-muted leading-relaxed line-clamp-3">{f.description}</p>
                </div>
              ))
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
                    <span className={`${sData.proficient ? "font-semibold text-main" : "text-muted"}`}>
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
    </div>
  );
};
