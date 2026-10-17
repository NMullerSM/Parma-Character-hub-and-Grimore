import React, { useState, useEffect } from "react";
import { useCharacter } from "../context/CharacterContext";
import { X, RotateCcw } from "lucide-react";

export const DiceDrawer: React.FC = () => {
  const { isDiceDrawerOpen, closeDiceDrawer, diceRequest, executeRoll, lastRollResult, talespireStatus } =
    useCharacter();

  const [pool, setPool] = useState<Record<string, number>>({ "20": 1 });
  const [modifier, setModifier] = useState<number>(0);
  const [label, setLabel] = useState<string>("Tirada Rápida");
  const [sendToTaleSpire, setSendToTaleSpire] = useState<boolean>(true);
  const [isRolling, setIsRolling] = useState<boolean>(false);

  // Sincronizar si se abre con una petición específica (ej: clic en un arma o habilidad)
  useEffect(() => {
    if (diceRequest) {
      setPool(diceRequest.dice || { "20": 1 });
      setModifier(diceRequest.modifier || 0);
      setLabel(diceRequest.label || "Tirada Rápida");
      if (typeof diceRequest.send_to_talespire === "boolean") {
        setSendToTaleSpire(diceRequest.send_to_talespire);
      }
    }
  }, [diceRequest]);

  // Cerrar con Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isDiceDrawerOpen) {
        closeDiceDrawer();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isDiceDrawerOpen, closeDiceDrawer]);

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
    setLabel("Tirada Rápida");
  };

  const handleRoll = async () => {
    setIsRolling(true);
    try {
      await executeRoll({
        dice: pool,
        modifier,
        label,
        send_to_talespire: sendToTaleSpire,
      });
    } finally {
      setIsRolling(false);
    }
  };

  const totalDiceCount = Object.values(pool).reduce((acc, count) => acc + count, 0);

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop transparente / desenfoque con clic para cerrar */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-xs transition-opacity" onClick={closeDiceDrawer} />

      {/* Drawer Lateral */}
      <aside className="relative w-full max-w-sm h-full bg-surface border-l border-border-iron shadow-2xl flex flex-col p-5 z-10 select-none">
        {/* Cabecera del Drawer */}
        <div className="flex items-center justify-between pb-3 border-b border-border-iron">
          <div>
            <h2 className="font-display font-bold text-lg text-gold">Bandeja de Dados</h2>
            <p className="text-xs text-muted">Configura tu reserva y lanza al tablero</p>
          </div>
          <button
            onClick={closeDiceDrawer}
            className="p-1 rounded text-muted hover:text-main hover:bg-card transition-colors"
            title="Cerrar (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Cuerpo del Drawer con scroll adaptativo */}
        <div className="flex-1 overflow-y-auto py-4 space-y-5">
          {/* Nombre / Motivo de la tirada */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
              Motivo de la Tirada
            </label>
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="Ej: Ataque con Espada, Salvación CON..."
              className="w-full bg-input text-main border border-border-iron rounded px-3 py-1.5 text-sm focus:border-gold outline-none"
            />
          </div>

          {/* Selector de Dados (Rejilla de Botones Táctiles) */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted">Selección de Dados</label>
              <button
                onClick={handleReset}
                className="text-xs text-muted hover:text-gold flex items-center gap-1 transition-colors"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reiniciar</span>
              </button>
            </div>

            <div className="grid grid-cols-4 gap-2">
              {diceTypes.map((d) => {
                const count = pool[String(d.sides)] || 0;
                return (
                  <div
                    key={d.sides}
                    className={`flex flex-col items-center justify-between p-2 rounded border transition-all ${
                      count > 0 ? "border-gold bg-card/90" : "border-border-iron bg-card/40"
                    }`}
                  >
                    <button
                      onClick={() => handleAddDie(d.sides)}
                      className="w-full py-1 text-center font-stat font-bold text-sm text-gold hover:text-main transition-colors"
                    >
                      {d.name}
                    </button>
                    <div className="flex items-center gap-1.5 mt-1">
                      <button
                        onClick={() => handleRemoveDie(d.sides)}
                        disabled={count === 0}
                        className="w-5 h-5 flex items-center justify-center text-xs rounded border border-border-iron hover:border-gold disabled:opacity-30 disabled:pointer-events-none"
                      >
                        -
                      </button>
                      <span className="font-stat text-xs font-semibold text-main w-4 text-center">{count}</span>
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
              Modificador Numérico
            </label>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setModifier((m) => m - 1)}
                className="w-9 h-9 rounded border border-border-iron bg-card font-stat font-bold text-main hover:border-gold text-sm"
              >
                -1
              </button>
              <input
                type="number"
                value={modifier}
                onChange={(e) => setModifier(parseInt(e.target.value, 10) || 0)}
                className="flex-1 bg-input text-main border border-border-iron rounded px-3 py-1.5 text-center font-stat font-bold text-lg focus:border-gold outline-none"
              />
              <button
                onClick={() => setModifier((m) => m + 1)}
                className="w-9 h-9 rounded border border-border-iron bg-card font-stat font-bold text-main hover:border-gold text-sm"
              >
                +1
              </button>
            </div>
          </div>

          {/* Opciones de Integración TaleSpire */}
          {talespireStatus.is_installed && (
            <div className="p-3 rounded border border-border-iron bg-card/60 space-y-2">
              <label className="flex items-center gap-2 cursor-pointer text-xs text-main">
                <input
                  type="checkbox"
                  checked={sendToTaleSpire}
                  onChange={(e) => setSendToTaleSpire(e.target.checked)}
                  className="rounded border-border-iron text-crimson focus:ring-0"
                />
                <span>Despachar tirada física a TaleSpire (3D)</span>
              </label>
              <p className="text-[11px] text-muted leading-relaxed">
                {talespireStatus.is_connected
                  ? "Conexión activa con TaleSpire. Los dados se lanzarán físicamente en el tablero."
                  : "TaleSpire detectado pero no conectado. La tirada se procesará de forma local."}
              </p>
            </div>
          )}

          {/* Resultado de la última tirada */}
          {lastRollResult && (
            <div className="p-4 rounded border border-gold/40 bg-card/80 text-center">
              <p className="text-xs text-muted uppercase tracking-wider mb-1">{lastRollResult.label}</p>
              <div className="font-stat font-bold text-3xl text-gold mb-1">{lastRollResult.total}</div>
              <div className="text-[11px] text-muted font-stat">
                Dados: [ {lastRollResult.dice_rolls.map((r) => r.roll).join(", ")} ]
                {lastRollResult.modifier !== 0 && (
                  <span>
                    {" "}
                    {lastRollResult.modifier > 0 ? `+ ${lastRollResult.modifier}` : `- ${Math.abs(lastRollResult.modifier)}`}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Pie del Drawer: Acción Primaria Indiscutible (Ley de Hick) */}
        <div className="pt-3 border-t border-border-iron flex gap-2">
          <button
            onClick={closeDiceDrawer}
            className="w-1/3 py-2 rounded border border-border-iron text-xs font-medium text-muted hover:text-main hover:bg-card transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={handleRoll}
            disabled={totalDiceCount === 0 || isRolling}
            className="flex-1 py-2 rounded bg-crimson hover:bg-crimson-hover disabled:opacity-50 text-white font-semibold text-sm transition-all shadow-md active:scale-98"
          >
            {isRolling ? "Lanzando..." : `Tirar (${totalDiceCount} dados)`}
          </button>
        </div>
      </aside>
    </div>
  );
};
