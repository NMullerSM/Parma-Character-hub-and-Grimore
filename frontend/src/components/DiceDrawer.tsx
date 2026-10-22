import React, { useState, useEffect, useRef } from "react";
import { useCharacter } from "../context/CharacterContext";
import { useTranslation } from "../i18n";
import type { RollMode } from "../api/types";
import { X, RotateCcw, Trash2, History, Dice5 } from "lucide-react";

export const DiceDrawer: React.FC = () => {
  const { t, language } = useTranslation();
  const {
    isDiceDrawerOpen,
    closeDiceDrawer,
    diceRequest,
    executeRoll,
    lastRollResult,
    rollHistory,
    clearRollHistory,
    talespireStatus,
    activeCharacter,
    updateActiveCharacter,
    showToast,
  } = useCharacter();

  const [activeTab, setActiveTab] = useState<"roller" | "history">("roller");
  const [pool, setPool] = useState<Record<string, number>>({ "20": 1 });
  const [modifier, setModifier] = useState<number>(0);
  const [label, setLabel] = useState<string>(t("dice.quickRoll"));
  const [mode, setMode] = useState<RollMode>("normal");
  const [sendToTaleSpire, setSendToTaleSpire] = useState<boolean>(true);
  const [isRolling, setIsRolling] = useState<boolean>(false);
  const [dc, setDc] = useState<number | undefined>(undefined);
  const [isDeathSave, setIsDeathSave] = useState<boolean>(false);

  const lastSyncedRequestRef = useRef<any>(null);
  const wasOpenRef = useRef<boolean>(false);

  useEffect(() => {
    const justOpened = isDiceDrawerOpen && !wasOpenRef.current;
    wasOpenRef.current = isDiceDrawerOpen;

    if (isDiceDrawerOpen && diceRequest) {
      if (justOpened || diceRequest !== lastSyncedRequestRef.current) {
        lastSyncedRequestRef.current = diceRequest;
        setPool(diceRequest.dice || { "20": 1 });
        setModifier(diceRequest.modifier || 0);
        setLabel(diceRequest.label || t("dice.quickRoll"));
        setMode(diceRequest.mode || "normal");
        setDc(diceRequest.dc);
        setIsDeathSave(Boolean(diceRequest.is_death_save || diceRequest.label?.toLowerCase().includes("muerte") || diceRequest.label?.toLowerCase().includes("death")));
        if (typeof diceRequest.send_to_talespire === "boolean") {
          setSendToTaleSpire(diceRequest.send_to_talespire);
        }
        setActiveTab("roller");
      }
    }
  }, [diceRequest, isDiceDrawerOpen]);

  if (!isDiceDrawerOpen) return null;

  const diceTypes = [
    { sides: 4, name: "d4" },
    { sides: 6, name: "d6" },
    { sides: 8, name: "d8" },
    { sides: 10, name: "d10" },
    { sides: 12, name: "d12" },
    { sides: 20, name: "d20" },
    { sides: 100, name: "d100" },
  ];

  const handleAddDie = (sides: number) => {
    const key = String(sides);
    setPool((prev) => ({ ...prev, [key]: (prev[key] || 0) + 1 }));
  };

  const handleRemoveDie = (sides: number) => {
    const key = String(sides);
    setPool((prev) => {
      const next = { ...prev };
      if ((next[key] || 0) > 1) {
        next[key] -= 1;
      } else {
        delete next[key];
      }
      return next;
    });
  };

  const handleReset = () => {
    setPool({ "20": 1 });
    setModifier(0);
    setLabel(t("dice.quickRoll"));
    setMode("normal");
    setDc(undefined);
    setIsDeathSave(false);
  };

  const handleRoll = async () => {
    setIsRolling(true);
    try {
      await executeRoll({
        dice: pool,
        modifier,
        label,
        mode,
        send_to_talespire: sendToTaleSpire,
        dc,
        is_death_save: isDeathSave,
        is_saving_throw: Boolean(dc !== undefined || isDeathSave || label.toLowerCase().includes("salvaci") || label.toLowerCase().includes("save")),
      });
    } finally {
      setIsRolling(false);
    }
  };

  const totalDiceCount = Object.values(pool).reduce((acc, count) => acc + count, 0);
  const hasD20 = (pool["20"] || 0) > 0;

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      {/* Backdrop con clic para cerrar */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-xs transition-opacity"
        onClick={closeDiceDrawer}
      />

      {/* Drawer Lateral con animación de entrada deslizante */}
      <aside className="relative w-full max-w-sm h-full bg-surface border-l border-border-iron shadow-2xl flex flex-col z-10 select-none animate-slide-in-right">
        {/* Cabecera del Drawer */}
        <div className="p-4 border-b border-border-iron flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <h2 className="font-display font-bold text-lg text-gold">{t("dice.drawerTitle")}</h2>
          </div>
          <button
            onClick={closeDiceDrawer}
            className="p-1.5 rounded text-muted hover:text-main hover:bg-card transition-colors"
            title={t("common.close")}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Pestañas: Lanzador vs Historial de Tiradas */}
        <div className="grid grid-cols-2 p-2 border-b border-border-iron bg-card/40 gap-1 shrink-0">
          <button
            onClick={() => setActiveTab("roller")}
            className={`py-1.5 text-xs font-semibold rounded flex items-center justify-center gap-1.5 transition-colors ${
              activeTab === "roller"
                ? "bg-gold text-canvas font-bold shadow-xs"
                : "text-muted hover:text-main"
            }`}
          >
            <Dice5 className="w-3.5 h-3.5" />
            <span>{t("dice.tabRoller")}</span>
          </button>
          <button
            onClick={() => setActiveTab("history")}
            className={`py-1.5 text-xs font-semibold rounded flex items-center justify-center gap-1.5 transition-colors ${
              activeTab === "history"
                ? "bg-gold text-canvas font-bold shadow-xs"
                : "text-muted hover:text-main"
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>{t("dice.tabHistory")} ({rollHistory.length})</span>
          </button>
        </div>

        {/* CONTENIDO 1: LANZADOR DE DADOS */}
        {activeTab === "roller" ? (
          <>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {/* Motivo de la tirada */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
                  {t("dice.rollReasonLabel")}
                </label>
                <input
                  type="text"
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  placeholder={t("dice.rollReasonPlaceholder")}
                  className="w-full bg-input text-main border border-border-iron rounded px-3 py-1.5 text-sm focus:border-gold outline-none"
                />
              </div>

              {/* Modo de Tirada (Normal / Ventaja / Desventaja) */}
              {hasD20 && (
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1.5">
                    {t("dice.rollModeTitle")} (d20)
                  </label>
                  <div className="grid grid-cols-3 gap-1.5">
                    {(
                      [
                        { id: "normal", label: t("dice.modeNormal") },
                        { id: "advantage", label: t("dice.modeAdvantage") },
                        { id: "disadvantage", label: t("dice.modeDisadvantage") },
                      ] as const
                    ).map((m) => (
                      <button
                        key={m.id}
                        onClick={() => setMode(m.id)}
                        className={`py-1.5 rounded border text-xs font-semibold transition-all ${
                          mode === m.id
                            ? m.id === "advantage"
                              ? "border-emerald-500 bg-emerald-500/15 text-emerald-400"
                              : m.id === "disadvantage"
                              ? "border-crimson bg-crimson/15 text-crimson"
                              : "border-gold bg-gold/15 text-gold"
                            : "border-border-iron bg-card/40 text-muted hover:text-main"
                        }`}
                      >
                        {m.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Selector de Dados */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-semibold uppercase tracking-wider text-muted">
                    {t("dice.dicePoolTitle")}
                  </label>
                  <button
                    onClick={handleReset}
                    className="text-xs text-muted hover:text-gold flex items-center gap-1 transition-colors"
                  >
                    <RotateCcw className="w-3 h-3" />
                    <span>{t("common.reset")}</span>
                  </button>
                </div>

                <div className="grid grid-cols-4 gap-2">
                  {diceTypes.map((d) => {
                    const count = pool[String(d.sides)] || 0;
                    return (
                      <div
                        key={d.sides}
                        className={`flex flex-col items-center justify-between p-2 rounded border transition-all ${
                          count > 0 ? "border-gold bg-card" : "border-border-iron bg-card/40"
                        }`}
                      >
                        <button
                          onClick={() => handleAddDie(d.sides)}
                          className="w-full py-0.5 text-center font-stat font-bold text-sm text-gold hover:text-main"
                        >
                          {d.name}
                        </button>
                        <div className="flex items-center gap-1 mt-1">
                          <button
                            onClick={() => handleRemoveDie(d.sides)}
                            disabled={count === 0}
                            className="w-5 h-5 flex items-center justify-center text-xs rounded border border-border-iron hover:border-gold disabled:opacity-20"
                          >
                            -
                          </button>
                          <span className="font-stat text-xs font-semibold text-main w-3.5 text-center">
                            {count}
                          </span>
                          <button
                            onClick={() => handleAddDie(d.sides)}
                            className="w-5 h-5 flex items-center justify-center text-xs rounded border border-border-iron hover:border-gold"
                          >
                            +
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Modificador Numérico */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
                  {t("dice.modifierTitle")}
                </label>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setModifier((m) => m - 1)}
                    className="w-9 h-8 rounded border border-border-iron bg-card font-stat font-bold text-main hover:border-gold text-sm"
                  >
                    -1
                  </button>
                  <input
                    type="number"
                    value={modifier}
                    onChange={(e) => setModifier(parseInt(e.target.value, 10) || 0)}
                    className="flex-1 bg-input text-main border border-border-iron rounded px-3 py-1 text-center font-stat font-bold text-lg focus:border-gold outline-none"
                  />
                  <button
                    onClick={() => setModifier((m) => m + 1)}
                    className="w-9 h-8 rounded border border-border-iron bg-card font-stat font-bold text-main hover:border-gold text-sm"
                  >
                    +1
                  </button>
                </div>
              </div>

              {/* CD Objetivo (Dificultad de Salvación) */}
              {(hasD20 || isDeathSave) && (
                <div className="p-2.5 rounded border border-border-iron bg-card/40 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted">
                      {t("dice.dcTitle")}
                    </label>
                    {dc !== undefined && (
                      <button
                        onClick={() => setDc(undefined)}
                        className="text-[10px] text-muted hover:text-crimson"
                      >
                        {t("dice.removeDc")}
                      </button>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={dc ?? ""}
                      placeholder={t("dice.dcPlaceholder")}
                      onChange={(e) => setDc(e.target.value ? parseInt(e.target.value, 10) : undefined)}
                      className="flex-1 bg-input text-main border border-border-iron rounded px-2.5 py-1 text-xs focus:border-gold outline-none"
                    />
                    <div className="flex gap-1">
                      {[10, 12, 15, 18].map((v) => (
                        <button
                          key={v}
                          type="button"
                          onClick={() => setDc(v)}
                          className={`px-2 py-1 rounded text-[11px] font-stat border transition-colors ${
                            dc === v
                              ? "border-gold bg-gold/20 text-gold font-bold"
                              : "border-border-iron bg-surface text-muted hover:text-main"
                          }`}
                        >
                          CD{v}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Conexión TaleSpire */}
              {talespireStatus.is_installed && (
                <div className="p-3 rounded border border-border-iron bg-card/60 space-y-1.5">
                  <label className="flex items-center gap-2 cursor-pointer text-xs text-main">
                    <input
                      type="checkbox"
                      checked={sendToTaleSpire}
                      onChange={(e) => setSendToTaleSpire(e.target.checked)}
                      className="rounded border-border-iron text-crimson focus:ring-0"
                    />
                    <span>{t("dice.sendToTalespire")}</span>
                  </label>
                  <p className="text-[11px] text-muted leading-tight">
                    {talespireStatus.is_connected
                      ? t("dice.talespireConnected")
                      : t("dice.talespireInstalled")}
                  </p>
                </div>
              )}

              {/* Resultado Anterior */}
              {lastRollResult && (
                <div className="p-3 rounded-lg border border-gold/40 bg-card text-center space-y-1.5">
                  <p className="text-[11px] text-muted uppercase tracking-wider font-semibold">
                    {t("dice.lastRoll", { label: lastRollResult.label })}
                  </p>
                  {lastRollResult.talespire_sent ? (
                    <div className="font-stat font-bold text-sm text-gold py-1">
                      {t("dice.rolledInTalespire")}
                    </div>
                  ) : (
                    <>
                      <div className="font-stat font-bold text-2xl text-gold">
                        {lastRollResult.total}
                      </div>

                      {/* Veredicto de Éxito / Fracaso para Salvaciones */}
                      {lastRollResult.success !== undefined && (
                        <div
                          className={`py-1 px-3 rounded text-xs font-bold uppercase tracking-wider mx-auto inline-block ${
                            lastRollResult.is_crit
                              ? "bg-emerald-500/25 border border-emerald-500 text-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.3)]"
                              : lastRollResult.is_fumble
                              ? "bg-crimson/25 border border-crimson text-crimson animate-pulse"
                              : lastRollResult.success
                              ? "bg-emerald-500/20 border border-emerald-500/60 text-emerald-400"
                              : "bg-crimson/20 border border-crimson/60 text-crimson"
                          }`}
                        >
                          {lastRollResult.is_death_save
                            ? lastRollResult.is_crit
                              ? t("dice.critSuccessSave")
                              : lastRollResult.is_fumble
                              ? t("dice.critFumbleSave")
                              : lastRollResult.success
                              ? t("dice.successSave")
                              : t("dice.failureSave")
                            : lastRollResult.success
                            ? t("dice.successVsDc", { total: lastRollResult.total, dc: lastRollResult.dc || 10 })
                            : t("dice.failureVsDc", { total: lastRollResult.total, dc: lastRollResult.dc || 10 })}
                        </div>
                      )}

                      {/* Botón rápido para asentar en ficha si es Salvación de Muerte */}
                      {lastRollResult.is_death_save && activeCharacter && (
                        <div className="pt-1">
                          <button
                            onClick={() => {
                              if (lastRollResult.success) {
                                const addCount = lastRollResult.is_crit ? 2 : 1;
                                const nextSucc = Math.min(3, (activeCharacter.death_save_successes || 0) + addCount);
                                updateActiveCharacter({ death_save_successes: nextSucc });
                                showToast(t("dice.recordedDeathSuccess", { count: nextSucc }), "success");
                              } else {
                                const addCount = lastRollResult.is_fumble ? 2 : 1;
                                const nextFail = Math.min(3, (activeCharacter.death_save_failures || 0) + addCount);
                                updateActiveCharacter({ death_save_failures: nextFail });
                                showToast(t("dice.recordedDeathFailure", { count: nextFail }), "warn");
                              }
                            }}
                            className="px-2.5 py-1 rounded bg-surface border border-border-iron hover:border-gold text-[11px] font-semibold text-main transition-colors"
                          >
                            {t("dice.recordDeathSave")}
                          </button>
                        </div>
                      )}

                      <div className="text-[11px] text-muted font-stat">
                        {lastRollResult.detail ||
                          `${language === "es" ? "Dados" : "Dice"}: [${lastRollResult.dice_rolls.map((r) => r.roll).join(", ")}]`}
                        {lastRollResult.modifier !== 0 && (
                          <span>
                            {" "}
                            {lastRollResult.modifier > 0
                              ? `+${lastRollResult.modifier}`
                              : lastRollResult.modifier}
                          </span>
                        )}
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>

            {/* Pie del Drawer Fijo */}
            <div className="p-4 border-t border-border-iron bg-surface flex gap-2 shrink-0">
              <button
                onClick={closeDiceDrawer}
                className="w-1/3 py-2 rounded border border-border-iron text-xs font-semibold text-muted hover:text-main hover:bg-card transition-colors"
              >
                {t("common.close")}
              </button>
              <button
                onClick={handleRoll}
                disabled={totalDiceCount === 0 || isRolling}
                className="flex-1 py-2 rounded bg-crimson hover:bg-crimson-hover disabled:opacity-40 text-white font-bold text-sm transition-all shadow-md active:scale-95"
              >
                {isRolling ? t("dice.rolling") : t("dice.rollCount", { count: totalDiceCount })}
              </button>
            </div>
          </>
        ) : (
          /* CONTENIDO 2: HISTORIAL DE TIRADAS DE LA SESIÓN */
          <div className="flex-1 flex flex-col min-h-0">
            <div className="flex items-center justify-between px-4 py-2 bg-card/30 border-b border-border-iron/60 text-xs text-muted">
              <span>{t("dice.historyCount", { count: rollHistory.length })}</span>
              {rollHistory.length > 0 && (
                <button
                  onClick={clearRollHistory}
                  className="flex items-center gap-1 text-crimson hover:underline"
                >
                  <Trash2 className="w-3 h-3" />
                  <span>{t("dice.clearHistory")}</span>
                </button>
              )}
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {rollHistory.length > 0 ? (
                rollHistory.map((item) => (
                  <div
                    key={item.id}
                    className="p-2.5 rounded border border-border-iron bg-card/70 space-y-1 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-main truncate max-w-[190px]">
                        {item.reason}
                      </span>
                      <span className="font-stat text-[11px] text-muted">{item.time_str}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="font-stat text-muted text-[11px]">
                        {item.formula} {item.detail}
                      </span>
                      <span
                        className={`font-stat font-bold text-sm ${
                          item.is_crit
                            ? "text-emerald-400"
                            : item.is_fumble
                            ? "text-crimson"
                            : "text-gold"
                        }`}
                      >
                        {item.channel === "TaleSpire 3D" ? "3D" : item.total}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-muted/70 pt-0.5 border-t border-border-iron/40">
                      <span>{item.character_name}</span>
                      <span className="text-gold/80">{item.channel}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="h-full flex items-center justify-center p-8 text-center text-xs text-muted">
                  {t("dice.noHistory")}
                </div>
              )}
            </div>
          </div>
        )}
      </aside>
    </div>
  );
};
