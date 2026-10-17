import React, { useState } from "react";
import { useCharacter } from "../context/CharacterContext";
import { api } from "../api/client";
import type { CharacterSheetData } from "../api/types";

export const CharacterWizard: React.FC<{ onComplete: () => void }> = ({ onComplete }) => {
  const { reloadCharacters, showToast } = useCharacter();

  const [step, setStep] = useState<number>(1);

  // Estado del nuevo personaje
  const [name, setName] = useState<string>("");
  const [level, setLevel] = useState<number>(1);
  const [race, setRace] = useState<string>("Humano");
  const [subrace, setSubrace] = useState<string>("");
  const [charClass, setCharClass] = useState<string>("Guerrero");
  const [subclass, setSubclass] = useState<string>("");
  const [background, setBackground] = useState<string>("Soldado");
  const [alignment, setAlignment] = useState<string>("Neutral Bueno");

  // Atributos y Point Buy
  const [scores, setScores] = useState<Record<string, number>>({
    FUE: 15,
    DES: 14,
    CON: 13,
    INT: 12,
    SAB: 10,
    CAR: 8,
  });

  const [pointBuyValidation, setPointBuyValidation] = useState<{
    valid: boolean;
    points_spent: number;
    points_remaining: number;
    error?: string;
  }>({ valid: true, points_spent: 27, points_remaining: 0 });

  const races = [
    { name: "Humano", subraces: ["Estándar", "Variante"] },
    { name: "Elfo", subraces: ["Alto Elfo", "Elfo de los Bosques", "Drow"] },
    { name: "Enano", subraces: ["Enano de las Colinas", "Enano de las Montañas"] },
    { name: "Mediano", subraces: ["Piesligeros", "Fuertecorazón"] },
    { name: "Tiflin", subraces: ["Infernal", "Abisal"] },
    { name: "Dracónido", subraces: ["Rojo", "Azul", "Dorado", "Plateado"] },
    { name: "Semielfo", subraces: [] },
    { name: "Semiorco", subraces: [] },
    { name: "Gnomo", subraces: ["Gnomo de las Rocas", "Gnomo de los Bosques"] },
  ];

  const classes = [
    { name: "Bárbaro", subclassLevel: 3, subclasses: ["Camino del Berserker", "Camino del Tótem"] },
    { name: "Bardo", subclassLevel: 3, subclasses: ["Colegio del Conocimiento", "Colegio del Valor"] },
    { name: "Clérigo", subclassLevel: 1, subclasses: ["Dominio de la Vida", "Dominio de la Guerra", "Dominio de la Luz"] },
    { name: "Druida", subclassLevel: 2, subclasses: ["Círculo de la Tierra", "Círculo de la Luna"] },
    { name: "Guerrero", subclassLevel: 3, subclasses: ["Campeón", "Maestro de la Batalla", "Caballero Arcano"] },
    { name: "Monje", subclassLevel: 3, subclasses: ["Camino de la Palma Abierta", "Camino de las Sombras"] },
    { name: "Paladín", subclassLevel: 3, subclasses: ["Juramento de Devoción", "Juramento de Venganza"] },
    { name: "Pícaro", subclassLevel: 3, subclasses: ["Ladrón", "Asesino", "Bribón Arcano"] },
    { name: "Hechicero", subclassLevel: 1, subclasses: ["Linaje Dracónico", "Magia Salvaje"] },
    { name: "Brujo", subclassLevel: 1, subclasses: ["El Señor Feérico", "El Infernal", "El Primigenio"] },
    { name: "Mago", subclassLevel: 2, subclasses: ["Escuela de Evocación", "Escuela de Abjuración", "Escuela de Adivinación"] },
  ];

  const currentClassObj = classes.find((c) => c.name === charClass);
  const isSubclassUnlocked = currentClassObj ? level >= currentClassObj.subclassLevel : false;

  const handleScoreChange = async (attr: string, delta: number) => {
    const nextVal = Math.max(8, Math.min(15, (scores[attr] || 8) + delta));
    const nextScores = { ...scores, [attr]: nextVal };
    setScores(nextScores);
    try {
      const res = await api.validatePointBuy(nextScores);
      setPointBuyValidation(res);
    } catch (e) {
      console.error("Error validating point buy:", e);
    }
  };

  const handleCreate = async () => {
    if (!name.trim()) {
      showToast("Ingresa un nombre para el personaje", "warn");
      return;
    }

    const calcMod = (score: number) => Math.floor((score - 10) / 2);
    const profBonus = Math.floor((level - 1) / 4) + 2;

    const newChar: CharacterSheetData = {
      name: name.trim(),
      char_class: charClass,
      subclass: isSubclassUnlocked ? subclass : "",
      level,
      race: subrace ? `${race} (${subrace})` : race,
      background,
      alignment,
      xp: 0,
      inspiration: false,
      proficiency_bonus: profBonus,
      ac: 10 + calcMod(scores.DES),
      speed: 30,
      initiative: calcMod(scores.DES),
      hp_current: 10 + calcMod(scores.CON) * level,
      hp_max: 10 + calcMod(scores.CON) * level,
      hp_temp: 0,
      hit_dice_total: `${level}d10`,
      hit_dice_current: `${level}d10`,
      death_save_successes: 0,
      death_save_failures: 0,
      abilities: {
        FUE: { base: scores.FUE, override: 0, bonus: calcMod(scores.FUE), proficient: false, save_bonus: calcMod(scores.FUE) },
        DES: { base: scores.DES, override: 0, bonus: calcMod(scores.DES), proficient: false, save_bonus: calcMod(scores.DES) },
        CON: { base: scores.CON, override: 0, bonus: calcMod(scores.CON), proficient: false, save_bonus: calcMod(scores.CON) },
        INT: { base: scores.INT, override: 0, bonus: calcMod(scores.INT), proficient: false, save_bonus: calcMod(scores.INT) },
        SAB: { base: scores.SAB, override: 0, bonus: calcMod(scores.SAB), proficient: false, save_bonus: calcMod(scores.SAB) },
        CAR: { base: scores.CAR, override: 0, bonus: calcMod(scores.CAR), proficient: false, save_bonus: calcMod(scores.CAR) },
      },
      skills: {
        Atletismo: { proficient: true, bonus: calcMod(scores.FUE) + profBonus, expertise: false },
        Percepción: { proficient: true, bonus: calcMod(scores.SAB) + profBonus, expertise: false },
      },
      spells: [],
      spell_slots_total: {},
      spell_slots_used: {},
      weapon_actions: [
        {
          name: "Espada Larga",
          type: "Cuerpo a cuerpo",
          range_val: "5 pies",
          hit_dc: `+${calcMod(scores.FUE) + profBonus}`,
          damage_dice: `1d8+${calcMod(scores.FUE)}`,
          damage_type: "Cortante",
          notes: "Versátil (1d10).",
        },
      ],
      features: [
        { name: "Competencia en Armas", source: charClass, description: "Entrenado en todas las armas marciales y simples." },
      ],
    };

    try {
      const res = await api.saveCharacter(newChar);
      if (res.success) {
        showToast(`¡${newChar.name} ha sido forjado exitosamente!`, "success");
        await reloadCharacters();
        onComplete();
      }
    } catch (e) {
      showToast("Error al forjar personaje", "warn");
    }
  };

  return (
    <div className="h-full overflow-y-auto p-4 md:p-6 max-w-4xl mx-auto space-y-6">
      {/* 1. Header y Progreso por Pasos */}
      <div className="border-b border-border-iron pb-4">
        <h1 className="font-display font-bold text-2xl md:text-3xl text-gold">Forja de Héroes D&D 5e</h1>
        <p className="text-xs text-muted mt-1">Crea un nuevo personaje siguiendo las reglas oficiales paso a paso.</p>

        {/* Stepper Progresivo (Ley de Hick: Enfoque secuencial) */}
        <div className="flex items-center justify-between mt-4 max-w-md">
          {[
            { num: 1, label: "Concepto" },
            { num: 2, label: "Especie" },
            { num: 3, label: "Clase" },
            { num: 4, label: "Atributos" },
          ].map((s) => (
            <div key={s.num} className="flex items-center gap-2">
              <span
                className={`w-6 h-6 rounded-full flex items-center justify-center font-stat font-bold text-xs ${
                  step === s.num
                    ? "bg-gold text-canvas shadow-[0_0_8px_rgba(201,164,92,0.5)]"
                    : step > s.num
                    ? "bg-surface border border-gold text-gold"
                    : "bg-surface border border-border-iron text-muted"
                }`}
              >
                {s.num}
              </span>
              <span className={`text-xs ${step === s.num ? "font-semibold text-main" : "text-muted"}`}>{s.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 2. Formularios Dinámicos por Paso */}
      <div className="bg-card border border-border-iron rounded-xl p-6 min-h-[340px]">
        {/* PASO 1: Concepto */}
        {step === 1 && (
          <div className="space-y-4 max-w-lg">
            <h2 className="font-display font-semibold text-lg text-gold">1. Concepto y Nivel</h2>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
                Nombre del Héroe
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ej: Thorin Escudo de Roble"
                className="w-full bg-input text-main border border-border-iron rounded px-3 py-2 text-sm focus:border-gold outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">Nivel Inicial</label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={level}
                  onChange={(e) => setLevel(Math.max(1, Math.min(20, parseInt(e.target.value, 10) || 1)))}
                  className="w-full bg-input text-main border border-border-iron rounded px-3 py-1.5 text-sm font-stat font-bold focus:border-gold outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">Trasfondo</label>
                <select
                  value={background}
                  onChange={(e) => setBackground(e.target.value)}
                  className="w-full bg-input text-main border border-border-iron rounded px-3 py-2 text-sm focus:border-gold outline-none"
                >
                  {["Soldado", "Acólito", "Criminal", "Noble", "Sabio", "Héroe del Pueblo", "Fugitivo"].map((b) => (
                    <option key={b} value={b}>{b}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">Alineamiento</label>
              <select
                value={alignment}
                onChange={(e) => setAlignment(e.target.value)}
                className="w-full bg-input text-main border border-border-iron rounded px-3 py-2 text-sm focus:border-gold outline-none"
              >
                {["Legal Bueno", "Neutral Bueno", "Caótico Bueno", "Legal Neutral", "Neutral Auténtico", "Caótico Neutral", "Legal Malvado", "Neutral Malvado", "Caótico Malvado"].map((a) => (
                  <option key={a} value={a}>{a}</option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* PASO 2: Especie y Subraza (Divulgación Progresiva) */}
        {step === 2 && (
          <div className="space-y-4">
            <h2 className="font-display font-semibold text-lg text-gold">2. Elige tu Especie / Raza</h2>

            <div className="grid grid-cols-3 gap-2">
              {races.map((r) => (
                <button
                  key={r.name}
                  onClick={() => {
                    setRace(r.name);
                    setSubrace(r.subraces[0] || "");
                  }}
                  className={`p-3 rounded border text-left transition-all ${
                    race === r.name ? "border-gold bg-surface font-semibold text-gold" : "border-border-iron bg-surface/40 text-muted hover:text-main"
                  }`}
                >
                  <div className="text-sm">{r.name}</div>
                  <div className="text-[11px] text-muted">{r.subraces.length > 0 ? `${r.subraces.length} linajes` : "Base"}</div>
                </button>
              ))}
            </div>

            {/* Subraza contextual (solo si aplica) */}
            {races.find((r) => r.name === race)?.subraces.length! > 0 && (
              <div className="pt-3 border-t border-border-iron/60">
                <label className="block text-xs font-semibold uppercase tracking-wider text-gold mb-2">
                  Linaje / Subraza de {race}
                </label>
                <div className="flex flex-wrap gap-2">
                  {races.find((r) => r.name === race)!.subraces.map((sub) => (
                    <button
                      key={sub}
                      onClick={() => setSubrace(sub)}
                      className={`px-3 py-1.5 rounded border text-xs transition-colors ${
                        subrace === sub ? "border-gold bg-gold text-canvas font-semibold" : "border-border-iron bg-surface text-muted hover:text-main"
                      }`}
                    >
                      {sub}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* PASO 3: Clase y Subclase */}
        {step === 3 && (
          <div className="space-y-4">
            <h2 className="font-display font-semibold text-lg text-gold">3. Elige tu Clase</h2>

            <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
              {classes.map((c) => (
                <button
                  key={c.name}
                  onClick={() => {
                    setCharClass(c.name);
                    setSubclass(c.subclasses[0] || "");
                  }}
                  className={`p-3 rounded border text-left transition-all ${
                    charClass === c.name ? "border-gold bg-surface font-semibold text-gold" : "border-border-iron bg-surface/40 text-muted hover:text-main"
                  }`}
                >
                  <div className="text-sm">{c.name}</div>
                  <div className="text-[10px] text-muted">Subclase Nvl {c.subclassLevel}</div>
                </button>
              ))}
            </div>

            {/* Subclase con Desbloqueo Condicional */}
            <div className="pt-3 border-t border-border-iron/60">
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-2">
                Arquetipo / Subclase
              </label>
              {isSubclassUnlocked ? (
                <div className="flex flex-wrap gap-2">
                  {currentClassObj?.subclasses.map((sub) => (
                    <button
                      key={sub}
                      onClick={() => setSubclass(sub)}
                      className={`px-3 py-1.5 rounded border text-xs transition-colors ${
                        subclass === sub ? "border-gold bg-gold text-canvas font-semibold" : "border-border-iron bg-surface text-muted hover:text-main"
                      }`}
                    >
                      {sub}
                    </button>
                  ))}
                </div>
              ) : (
                <div className="p-3 rounded bg-surface/50 border border-border-iron text-xs text-muted">
                  🔒 El arquetipo se desbloquea al alcanzar el <span className="text-gold font-semibold">Nivel {currentClassObj?.subclassLevel}</span> de {charClass}.
                </div>
              )}
            </div>
          </div>
        )}

        {/* PASO 4: Atributos y Point-Buy */}
        {step === 4 && (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-display font-semibold text-lg text-gold">4. Compra por Puntos (Point Buy)</h2>
                <p className="text-xs text-muted">Presupuesto estándar: 27 puntos. Rango legal de 8 a 15.</p>
              </div>
              <div className="text-right">
                <span className="text-xs text-muted uppercase font-semibold">Puntos Restantes: </span>
                <span
                  className={`font-stat font-bold text-xl ${
                    pointBuyValidation.points_remaining === 0
                      ? "text-emerald-400"
                      : pointBuyValidation.points_remaining < 0
                      ? "text-crimson"
                      : "text-gold"
                  }`}
                >
                  {pointBuyValidation.points_remaining}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
              {Object.entries(scores).map(([attr, val]) => (
                <div key={attr} className="bg-surface border border-border-iron rounded-lg p-3 text-center">
                  <span className="text-xs font-stat font-semibold uppercase tracking-widest text-muted">{attr}</span>
                  <div className="font-stat font-bold text-3xl text-main my-1">{val}</div>
                  <div className="flex items-center justify-center gap-2 mt-2">
                    <button
                      onClick={() => handleScoreChange(attr, -1)}
                      disabled={val <= 8}
                      className="w-7 h-7 rounded border border-border-iron hover:border-gold disabled:opacity-30 disabled:pointer-events-none flex items-center justify-center text-xs font-bold"
                    >
                      -
                    </button>
                    <button
                      onClick={() => handleScoreChange(attr, 1)}
                      disabled={val >= 15}
                      className="w-7 h-7 rounded border border-border-iron hover:border-gold disabled:opacity-30 disabled:pointer-events-none flex items-center justify-center text-xs font-bold"
                    >
                      +
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {pointBuyValidation.error && (
              <p className="text-xs text-crimson font-medium bg-crimson/10 border border-crimson/30 p-2.5 rounded">
                ⚠ {pointBuyValidation.error}
              </p>
            )}
          </div>
        )}
      </div>

      {/* 3. Acciones de Navegación del Wizard */}
      <div className="flex items-center justify-between pt-2">
        <button
          onClick={() => setStep((s) => Math.max(1, s - 1))}
          disabled={step === 1}
          className="px-4 py-2 rounded border border-border-iron text-xs font-semibold text-muted hover:text-main hover:bg-card disabled:opacity-30 disabled:pointer-events-none transition-colors"
        >
          Anterior
        </button>

        {step < 4 ? (
          <button
            onClick={() => setStep((s) => Math.min(4, s + 1))}
            className="px-5 py-2 rounded bg-gold hover:bg-gold-hover text-canvas text-xs font-semibold transition-all shadow-sm active:scale-95"
          >
            Siguiente Paso
          </button>
        ) : (
          <button
            onClick={handleCreate}
            disabled={!pointBuyValidation.valid}
            className="px-6 py-2 rounded bg-crimson hover:bg-crimson-hover disabled:opacity-50 text-white text-xs font-bold transition-all shadow-md active:scale-95"
          >
            Forjar Personaje
          </button>
        )}
      </div>
    </div>
  );
};
