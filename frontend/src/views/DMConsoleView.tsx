import React, { useState, useEffect } from "react";
import { useCharacter } from "../context/CharacterContext";
import { api } from "../api/client";
import type { DmSessionStatus, DmSessionPlayer, DmHomebrewItem, DmSessionEventLog } from "../api/types";
import {
  Wifi,
  WifiOff,
  Copy,
  QrCode,
  Shield,
  Heart,
  Gift,
  Scroll,
  Users,
  Check,
  Sparkles,
  BookOpen,
  X,
  FileText,
  Tag,
} from "lucide-react";

export const DMConsoleView: React.FC = () => {
  const { showToast, setActiveSessionId } = useCharacter();

  const [sessionStatus, setSessionStatus] = useState<DmSessionStatus>({
    is_running: false,
    session_id: null,
    session_name: "Sesión de Campaña",
    campaign_name: "Campaña Principal",
    tunnel_url: null,
    qr_code: "",
    port: 8765,
    players: [],
    connected_count: 0,
  });

  const [pastSessions, setPastSessions] = useState<any[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string>("new");
  const [sessionNameInput, setSessionNameInput] = useState<string>("Sesión de Campaña");
  const [campaignNameInput, setCampaignNameInput] = useState<string>("Campaña Principal");

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [copiedUrl, setCopiedUrl] = useState<boolean>(false);
  const [copiedId, setCopiedId] = useState<boolean>(false);
  const [isQrModalOpen, setIsQrModalOpen] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"party" | "forge" | "ledger" | "notes">("party");

  // Jugador seleccionado para inspección completa de ficha
  const [inspectedPlayer, setInspectedPlayer] = useState<DmSessionPlayer | null>(null);

  // Forja Homebrew
  const [homebrewItems, setHomebrewItems] = useState<DmHomebrewItem[]>([]);
  const [hbName, setHbName] = useState<string>("");
  const [hbCategory, setHbCategory] = useState<DmHomebrewItem["category"]>("weapon");
  const [hbRarity, setHbRarity] = useState<DmHomebrewItem["rarity"]>("uncommon");
  const [hbAttunement, setHbAttunement] = useState<boolean>(false);
  const [hbDamageDice, setHbDamageDice] = useState<string>("1d8");
  const [hbDamageType, setHbDamageType] = useState<string>("cortante");
  const [hbSecondaryDice, setHbSecondaryDice] = useState<string>("");
  const [hbSecondaryType, setHbSecondaryType] = useState<string>("");
  const [hbBonusAttack, setHbBonusAttack] = useState<number>(0);
  const [hbBonusDamage, setHbBonusDamage] = useState<number>(0);
  const [hbAcBonus, setHbAcBonus] = useState<number>(0);
  const [hbDesc, setHbDesc] = useState<string>("");
  const [selectedRecipientToken, setSelectedRecipientToken] = useState<string>("");

  // Ledger y notas
  const [eventLogs, setEventLogs] = useState<DmSessionEventLog[]>([]);
  const [sessionNotes, setSessionNotes] = useState<string>("");

  // Jugadores seguros contra null
  const players = sessionStatus?.players || [];

  useEffect(() => {
    loadStatus();
    loadPastSessions();
    loadHomebrewItems();
    const interval = setInterval(loadStatus, 4000);
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    try {
      const status = await api.getDmSessionStatus();
      setSessionStatus(status);
      if (status.is_running && status.session_id) {
        setActiveSessionId(status.session_id);
      }
      if (status.session_id) {
        const logs = await api.dmGetSessionLogs(status.session_id);
        setEventLogs(logs || []);
        // Si no se han cargado notas aún o corresponden a la sesión activa
        const notes = await api.dmGetSessionNotes(status.session_id);
        if (notes !== undefined) {
          setSessionNotes(notes);
        }
      }
    } catch (e) {
      console.error("Error al cargar estado de sesión DM:", e);
    }
  };

  const loadPastSessions = async () => {
    try {
      const list = await api.dmListSessions();
      setPastSessions(list || []);
    } catch (e) {
      console.error("Error al listar sesiones históricas:", e);
    }
  };

  const loadHomebrewItems = async () => {
    try {
      const items = await api.dmListHomebrewItems();
      setHomebrewItems(items || []);
    } catch (e) {
      console.error("Error al cargar objetos homebrew:", e);
    }
  };

  // Cambio de sesión en el selector
  const handleSelectSession = async (sessId: string) => {
    setSelectedSessionId(sessId);
    if (sessId === "new") {
      setSessionNameInput("Nueva Sesión");
      setCampaignNameInput("Campaña Principal");
      setSessionNotes("");
    } else {
      const found = pastSessions.find((s) => s.id === sessId);
      if (found) {
        setSessionNameInput(found.name || "Sesión");
        setCampaignNameInput(found.campaign_name || "Campaña Principal");
      }
      try {
        const notes = await api.dmGetSessionNotes(sessId);
        setSessionNotes(notes || "");
      } catch (_) {}
    }
  };

  const handleStartSession = async () => {
    setIsLoading(true);
    try {
      const sid = selectedSessionId !== "new" ? selectedSessionId : undefined;
      const res = await api.startDmSession(sessionNameInput.trim() || "Sesión de Campaña", campaignNameInput.trim() || "Campaña Principal", sid);
      setSessionStatus(res);
      if (res.session_id) {
        setActiveSessionId(res.session_id);
      }
      await loadPastSessions();
      showToast("¡Túnel Cloudflare iniciado! Partida en línea lista para compartir.", "success");
    } catch (e) {
      showToast("Error al iniciar el túnel de Cloudflare", "warn");
    } finally {
      setIsLoading(false);
    }
  };

  const handleStopSession = async () => {
    if (window.confirm("¿Deseas finalizar la sesión y cerrar el túnel de Cloudflare?")) {
      setIsLoading(true);
      try {
        await api.stopDmSession();
        setSessionStatus((prev) => ({ ...prev, is_running: false, tunnel_url: null, qr_code: "" }));
        showToast("Sesión finalizada y túnel cerrado.", "info");
        await loadPastSessions();
      } catch (e) {
        showToast("Error al detener la sesión", "warn");
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleCopyLink = () => {
    if (!sessionStatus.tunnel_url) return;
    navigator.clipboard.writeText(sessionStatus.tunnel_url);
    setCopiedUrl(true);
    showToast("¡Enlace público de la partida copiado al portapapeles!", "success");
    setTimeout(() => setCopiedUrl(false), 3000);
  };

  const handleCopySessionId = () => {
    const sid = sessionStatus.session_id || (selectedSessionId !== "new" ? selectedSessionId : null);
    if (!sid) return;
    navigator.clipboard.writeText(sid);
    setCopiedId(true);
    showToast("ID de sesión copiado al portapapeles", "success");
    setTimeout(() => setCopiedId(false), 3000);
  };

  const handleHpChange = async (playerToken: string, delta: number, charName: string) => {
    try {
      await api.dmApplyHpChange(playerToken, delta);
      const action = delta > 0 ? `+${delta} HP (Curación)` : `${delta} HP (Daño)`;
      showToast(`${action} aplicado a ${charName}`, delta > 0 ? "success" : "warn");
      await loadStatus();
    } catch (e) {
      showToast("Error al modificar puntos de golpe", "warn");
    }
  };

  const handleSaveHomebrew = async () => {
    if (!hbName.trim()) {
      showToast("Ingresa un nombre para el objeto Homebrew", "warn");
      return;
    }
    try {
      const newItem: DmHomebrewItem = {
        name: hbName.trim(),
        category: hbCategory,
        rarity: hbRarity,
        requires_attunement: hbAttunement,
        damage_dice: hbDamageDice.trim() || undefined,
        damage_type: hbDamageType.trim() || undefined,
        secondary_dice: hbSecondaryDice.trim() || undefined,
        secondary_type: hbSecondaryType.trim() || undefined,
        bonus_attack: hbBonusAttack,
        bonus_damage: hbBonusDamage,
        ac_bonus: hbAcBonus,
        description: hbDesc.trim(),
      };
      await api.dmSaveHomebrewItem(newItem);
      showToast(`Objeto "${newItem.name}" forjado y guardado`, "success");
      setHbName("");
      setHbDesc("");
      await loadHomebrewItems();
    } catch (e) {
      showToast("Error al guardar objeto homebrew", "warn");
    }
  };

  const handleGiftItem = async (item: DmHomebrewItem) => {
    if (!selectedRecipientToken) {
      showToast("Selecciona a qué jugador deseas entregar el objeto", "warn");
      return;
    }
    const targetPlayer = players.find((p) => p.player_token === selectedRecipientToken);
    try {
      await api.dmGiftItem(selectedRecipientToken, item);
      showToast(`¡"${item.name}" entregado a ${targetPlayer?.character_name || "jugador"}!`, "success");
      await loadStatus();
    } catch (e) {
      showToast("Error al entregar objeto al jugador", "warn");
    }
  };

  const effectiveSessionId = sessionStatus.session_id || (selectedSessionId !== "new" ? selectedSessionId : null);

  return (
    <div className="h-full flex flex-col bg-canvas text-main overflow-hidden select-none">
      {/* 1. Barra de Control de Túnel Superior */}
      <div className="px-6 py-3.5 border-b border-border-iron bg-surface flex flex-wrap items-center justify-between gap-4 shrink-0">
        <div className="flex items-center gap-3">
          <div
            className={`w-3.5 h-3.5 rounded-full ${
              sessionStatus.is_running
                ? "bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.8)] animate-pulse"
                : "bg-muted"
            }`}
          />
          <div>
            <h1 className="font-display font-bold text-lg text-gold flex items-center gap-2">
              <span>{sessionStatus.session_name || sessionNameInput}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-card border border-border-iron text-muted font-normal">
                {sessionStatus.campaign_name || campaignNameInput}
              </span>
            </h1>
            <p className="text-xs text-muted">
              {sessionStatus.is_running
                ? `En línea vía Cloudflare • ${sessionStatus.connected_count} jugadores conectados`
                : "Túnel desconectado. Selecciona o crea una sesión para iniciar el túnel Cloudflare."}
            </p>
          </div>
        </div>

        {/* Acciones de Conectividad */}
        <div className="flex items-center gap-2.5">
          {sessionStatus.is_running ? (
            <button
              onClick={handleStopSession}
              disabled={isLoading}
              className="px-3.5 py-1.5 rounded-lg bg-crimson/15 border border-crimson hover:bg-crimson hover:text-white text-crimson text-xs font-semibold transition-colors flex items-center gap-1.5"
            >
              <WifiOff className="w-3.5 h-3.5" />
              <span>{isLoading ? "Cerrando..." : "Terminar Sesión"}</span>
            </button>
          ) : (
            <button
              onClick={handleStartSession}
              disabled={isLoading}
              className="px-4 py-2 rounded-lg bg-gold hover:bg-gold-hover text-canvas font-bold text-xs shadow-md transition-all flex items-center gap-2 active:scale-95"
            >
              <Wifi className="w-4 h-4" />
              <span>{isLoading ? "Iniciando Túnel..." : (selectedSessionId !== "new" ? "Reanudar Sesión Online" : "Iniciar Sesión Online")}</span>
            </button>
          )}
        </div>
      </div>

      {/* BANNER DESTACADO DE INVITACIÓN (Visible cuando el túnel está activo) */}
      {sessionStatus.is_running && (
        <div className="bg-gradient-to-r from-emerald-950/40 via-card to-emerald-950/20 border-b border-emerald-500/40 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4 shadow-sm shrink-0">
          <div className="flex items-center gap-3">
            <span className="flex h-3 w-3 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
            <div>
              <div className="text-xs font-bold text-emerald-300 flex items-center gap-2">
                <span>Enlace Público de Partida</span>
                {sessionStatus.session_id && (
                  <span className="text-[11px] font-mono text-muted bg-surface/90 px-2 py-0.5 rounded border border-border-iron">
                    ID: {sessionStatus.session_id}
                  </span>
                )}
                {sessionStatus.session_id && (
                  <button
                    onClick={handleCopySessionId}
                    className="text-[11px] text-gold hover:underline font-mono"
                    title="Copiar ID de la sesión"
                  >
                    {copiedId ? "✓ ID Copiado" : "Copiar ID"}
                  </button>
                )}
              </div>
              <div className="text-xs text-main font-mono truncate max-w-sm sm:max-w-md md:max-w-xl select-all mt-0.5">
                {sessionStatus.tunnel_url || "Estableciendo túnel de Cloudflare..."}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyLink}
              disabled={!sessionStatus.tunnel_url}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-md flex items-center gap-2 active:scale-95 ${
                copiedUrl
                  ? "bg-emerald-500 text-canvas font-bold"
                  : "bg-gold hover:bg-gold-hover text-canvas"
              }`}
            >
              {copiedUrl ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              <span>{copiedUrl ? "¡Enlace Copiado!" : "Copiar Enlace de Partida"}</span>
            </button>

            {sessionStatus.qr_code && (
              <button
                onClick={() => setIsQrModalOpen(true)}
                className="px-3 py-2 rounded-xl border border-border-iron bg-surface hover:bg-card text-muted hover:text-gold text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-xs"
                title="Mostrar código QR para celulares"
              >
                <QrCode className="w-4 h-4" />
                <span className="hidden sm:inline">Código QR</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* SELECTOR Y GESTOR DE SESIÓN (Visible cuando no está en línea para reanudar o crear nueva) */}
      {!sessionStatus.is_running && (
        <div className="bg-card/70 border-b border-border-iron px-6 py-3.5 flex flex-wrap items-center justify-between gap-4 shrink-0">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted font-medium">Sesión en SQLite:</span>
              <select
                value={selectedSessionId}
                onChange={(e) => handleSelectSession(e.target.value)}
                className="bg-surface text-main border border-border-iron rounded-lg px-3 py-1.5 text-xs font-semibold focus:border-gold outline-none"
              >
                <option value="new">+ Crear Nueva Sesión...</option>
                {pastSessions.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.campaign_name}) — {s.created_at ? s.created_at.split(" ")[0] : s.id}
                  </option>
                ))}
              </select>
            </div>

            {selectedSessionId === "new" ? (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={sessionNameInput}
                  onChange={(e) => setSessionNameInput(e.target.value)}
                  placeholder="Nombre de la Sesión"
                  className="bg-surface text-main border border-border-iron rounded-lg px-2.5 py-1 text-xs focus:border-gold outline-none w-44"
                />
                <input
                  type="text"
                  value={campaignNameInput}
                  onChange={(e) => setCampaignNameInput(e.target.value)}
                  placeholder="Campaña"
                  className="bg-surface text-main border border-border-iron rounded-lg px-2.5 py-1 text-xs focus:border-gold outline-none w-36"
                />
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs text-muted">
                <span className="font-mono bg-surface px-2 py-0.5 rounded border border-border-iron">
                  ID: {selectedSessionId}
                </span>
                <button
                  onClick={handleCopySessionId}
                  className="text-gold hover:underline text-[11px]"
                >
                  {copiedId ? "✓ Copiado" : "Copiar ID"}
                </button>
              </div>
            )}
          </div>

          <div className="text-xs text-muted">
            {selectedSessionId !== "new"
              ? "Reanudarás esta sesión existente con sus notas y bitácora previas."
              : "Se creará un registro separado en la base de datos local para esta sesión."}
          </div>
        </div>
      )}

      {/* 2. Pestañas de Navegación del DM */}
      <div className="px-6 border-b border-border-iron bg-card/40 flex gap-2 shrink-0">
        <button
          onClick={() => setActiveTab("party")}
          className={`py-2.5 px-4 text-xs font-semibold border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === "party"
              ? "border-gold text-gold font-bold"
              : "border-transparent text-muted hover:text-main"
          }`}
        >
          <Users className="w-3.5 h-3.5" />
          <span>Mesa de Jugadores ({players.length})</span>
        </button>
        <button
          onClick={() => setActiveTab("forge")}
          className={`py-2.5 px-4 text-xs font-semibold border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === "forge"
              ? "border-gold text-gold font-bold"
              : "border-transparent text-muted hover:text-main"
          }`}
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Forja Homebrew ({homebrewItems.length})</span>
        </button>
        <button
          onClick={() => setActiveTab("ledger")}
          className={`py-2.5 px-4 text-xs font-semibold border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === "ledger"
              ? "border-gold text-gold font-bold"
              : "border-transparent text-muted hover:text-main"
          }`}
        >
          <Scroll className="w-3.5 h-3.5" />
          <span>Tiradas y Bitácora ({eventLogs.length})</span>
        </button>
        <button
          onClick={() => setActiveTab("notes")}
          className={`py-2.5 px-4 text-xs font-semibold border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === "notes"
              ? "border-gold text-gold font-bold"
              : "border-transparent text-muted hover:text-main"
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Notas del DM</span>
          {effectiveSessionId && (
            <span className="w-1.5 h-1.5 rounded-full bg-gold" />
          )}
        </button>
      </div>

      {/* 3. Área de Contenido Principal */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* PESTAÑA 1: MESA DE JUGADORES */}
        {activeTab === "party" && (
          <div className="space-y-4">
            {players.length === 0 ? (
              <div className="p-12 text-center border border-dashed border-border-iron rounded-2xl bg-card/20 space-y-3">
                <Users className="w-10 h-10 text-muted mx-auto opacity-50" />
                <h3 className="font-display font-semibold text-base text-main">No hay jugadores en la sesión aún</h3>
                <p className="text-xs text-muted max-w-md mx-auto">
                  {sessionStatus.is_running
                    ? "Comparte el enlace o el código QR con tus jugadores para que carguen sus fichas desde cualquier navegador."
                    : "Inicia la sesión online para generar el enlace de conexión de Cloudflare."}
                </p>
                {sessionStatus.is_running && sessionStatus.tunnel_url && (
                  <button
                    onClick={handleCopyLink}
                    className="px-4 py-2 rounded-xl bg-gold hover:bg-gold-hover text-canvas font-bold text-xs inline-flex items-center gap-2 transition-all shadow-sm active:scale-95"
                  >
                    {copiedUrl ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedUrl ? "¡Enlace Copiado!" : "Copiar Enlace para Jugadores"}</span>
                  </button>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {players.map((p) => {
                  const hpPct = Math.max(0, Math.min(100, (p.hp_current / (p.hp_max || 1)) * 100));
                  const isDead = p.status === "DEAD";
                  const isUnconscious = p.hp_current <= 0 || p.status === "UNCONSCIOUS";

                  return (
                    <div
                      key={p.player_token}
                      className={`p-4 rounded-xl border bg-card/70 flex flex-col justify-between space-y-3 transition-all ${
                        isDead
                          ? "border-red-900/50 opacity-60"
                          : isUnconscious
                          ? "border-crimson shadow-[0_0_15px_rgba(230,57,70,0.2)]"
                          : "border-border-iron hover:border-gold/60"
                      }`}
                    >
                      {/* Cabecera del Jugador */}
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-bold text-sm text-main flex items-center gap-1.5">
                            <span>{p.character_name}</span>
                            {p.is_online ? (
                              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" title="En línea" />
                            ) : (
                              <span className="w-2 h-2 rounded-full bg-muted inline-block" title="Desconectado" />
                            )}
                          </h4>
                          <p className="text-xs text-muted">
                            Nvl {p.character_level} {p.character_class || "Aventurero"}
                          </p>
                        </div>
                        <div className="flex items-center gap-1 bg-surface px-2 py-1 rounded border border-border-iron text-xs font-stat">
                          <Shield className="w-3.5 h-3.5 text-gold" />
                          <span className="font-bold">{p.ac || 10} CA</span>
                        </div>
                      </div>

                      {/* Barra de Vida Interactiva */}
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between text-xs font-stat">
                          <span className="flex items-center gap-1 text-muted">
                            <Heart className={`w-3.5 h-3.5 ${isUnconscious ? "text-crimson" : "text-emerald-500"}`} />
                            <span>Puntos de Golpe</span>
                          </span>
                          <span className="font-bold text-main">
                            {p.hp_current} / {p.hp_max}
                          </span>
                        </div>
                        <div className="w-full h-2.5 rounded-full bg-canvas border border-border-iron overflow-hidden">
                          <div
                            className={`h-full transition-all duration-300 ${
                              isUnconscious
                                ? "bg-crimson"
                                : hpPct < 30
                                ? "bg-amber-500"
                                : "bg-emerald-500"
                            }`}
                            style={{ width: `${hpPct}%` }}
                          />
                        </div>
                      </div>

                      {/* Controles de Daño y Curación Inmediatos */}
                      <div className="space-y-2 pt-2 border-t border-border-iron/50">
                        <div className="flex items-center justify-between text-[11px] text-muted">
                          <span>Acción Rápida de DM:</span>
                          {isUnconscious && (
                            <span className="text-crimson font-bold uppercase tracking-wider text-[10px]">
                              Inconsciente
                            </span>
                          )}
                        </div>
                        <div className="grid grid-cols-4 gap-1.5">
                          <button
                            onClick={() => handleHpChange(p.player_token, -5, p.character_name)}
                            className="py-1 rounded bg-crimson/15 hover:bg-crimson text-crimson hover:text-white border border-crimson text-xs font-bold transition-colors"
                            title="Infligir 5 de daño"
                          >
                            -5
                          </button>
                          <button
                            onClick={() => handleHpChange(p.player_token, -1, p.character_name)}
                            className="py-1 rounded bg-crimson/10 hover:bg-crimson text-crimson hover:text-white border border-crimson/60 text-xs font-bold transition-colors"
                            title="Infligir 1 de daño"
                          >
                            -1
                          </button>
                          <button
                            onClick={() => handleHpChange(p.player_token, 1, p.character_name)}
                            className="py-1 rounded bg-emerald-500/10 hover:bg-emerald-500 text-emerald-400 hover:text-white border border-emerald-500/60 text-xs font-bold transition-colors"
                            title="Curar 1 punto"
                          >
                            +1
                          </button>
                          <button
                            onClick={() => handleHpChange(p.player_token, 5, p.character_name)}
                            className="py-1 rounded bg-emerald-500/15 hover:bg-emerald-500 text-emerald-400 hover:text-white border border-emerald-500 text-xs font-bold transition-colors"
                            title="Curar 5 puntos"
                          >
                            +5
                          </button>
                        </div>
                      </div>

                      {/* Botón de Auditoría / Ver Hoja Completa */}
                      <button
                        onClick={() => setInspectedPlayer(p)}
                        className="w-full mt-2 py-1 rounded bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-medium text-muted hover:text-main flex items-center justify-center gap-1.5 transition-colors"
                      >
                        <BookOpen className="w-3.5 h-3.5 text-gold" />
                        <span>Concordar / Ver Ficha</span>
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* PESTAÑA 2: FORJA HOMEBREW */}
        {activeTab === "forge" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Formulario Creador de Objeto Homebrew */}
            <div className="p-5 rounded-xl border border-border-iron bg-card/60 space-y-4">
              <h3 className="font-display font-bold text-base text-gold flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-gold" />
                <span>Forjar Objeto Mágico / Homebrew</span>
              </h3>

              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
                    Nombre del Objeto
                  </label>
                  <input
                    type="text"
                    value={hbName}
                    onChange={(e) => setHbName(e.target.value)}
                    placeholder="Ej. Espada del Alba Carmesí"
                    className="w-full bg-input text-main border border-border-iron rounded px-3 py-1.5 text-xs focus:border-gold outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
                      Categoría
                    </label>
                    <select
                      value={hbCategory}
                      onChange={(e) => setHbCategory(e.target.value as any)}
                      className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
                    >
                      <option value="weapon">Arma</option>
                      <option value="armor">Armadura</option>
                      <option value="wondrous">Objeto Maravilloso</option>
                      <option value="potion">Poción</option>
                      <option value="ring">Anillo</option>
                      <option value="scroll">Pergamino</option>
                      <option value="wand">Vara / Varita</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
                      Rareza
                    </label>
                    <select
                      value={hbRarity}
                      onChange={(e) => setHbRarity(e.target.value as any)}
                      className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
                    >
                      <option value="common">Común</option>
                      <option value="uncommon">Poco Común</option>
                      <option value="rare">Raro</option>
                      <option value="very_rare">Muy Raro</option>
                      <option value="legendary">Legendario</option>
                      <option value="artifact">Artefacto</option>
                    </select>
                  </div>
                </div>

                {hbCategory === "weapon" && (
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
                        Dado de Daño
                      </label>
                      <input
                        type="text"
                        value={hbDamageDice}
                        onChange={(e) => setHbDamageDice(e.target.value)}
                        placeholder="1d8"
                        className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
                        Tipo de Daño
                      </label>
                      <input
                        type="text"
                        value={hbDamageType}
                        onChange={(e) => setHbDamageType(e.target.value)}
                        placeholder="cortante"
                        className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
                        Daño Secundario (Opcional)
                      </label>
                      <input
                        type="text"
                        value={hbSecondaryDice}
                        onChange={(e) => setHbSecondaryDice(e.target.value)}
                        placeholder="1d6"
                        className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
                        Tipo Secundario
                      </label>
                      <input
                        type="text"
                        value={hbSecondaryType}
                        onChange={(e) => setHbSecondaryType(e.target.value)}
                        placeholder="fuego / radiante"
                        className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
                      />
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="block text-[10px] font-semibold uppercase text-muted mb-1">
                      Bono Ataque
                    </label>
                    <input
                      type="number"
                      value={hbBonusAttack}
                      onChange={(e) => setHbBonusAttack(parseInt(e.target.value, 10) || 0)}
                      className="w-full bg-input text-main border border-border-iron rounded px-2 py-1 text-xs text-center focus:border-gold outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-semibold uppercase text-muted mb-1">
                      Bono Daño
                    </label>
                    <input
                      type="number"
                      value={hbBonusDamage}
                      onChange={(e) => setHbBonusDamage(parseInt(e.target.value, 10) || 0)}
                      className="w-full bg-input text-main border border-border-iron rounded px-2 py-1 text-xs text-center focus:border-gold outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-semibold uppercase text-muted mb-1">
                      Bono CA
                    </label>
                    <input
                      type="number"
                      value={hbAcBonus}
                      onChange={(e) => setHbAcBonus(parseInt(e.target.value, 10) || 0)}
                      className="w-full bg-input text-main border border-border-iron rounded px-2 py-1 text-xs text-center focus:border-gold outline-none"
                    />
                  </div>
                </div>

                <label className="flex items-center gap-2 cursor-pointer text-xs text-muted">
                  <input
                    type="checkbox"
                    checked={hbAttunement}
                    onChange={(e) => setHbAttunement(e.target.checked)}
                    className="rounded border-border-iron text-gold"
                  />
                  <span>Requiere sintonización (Attunement)</span>
                </label>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-1">
                    Descripción & Propiedades Mágicas
                  </label>
                  <textarea
                    rows={3}
                    value={hbDesc}
                    onChange={(e) => setHbDesc(e.target.value)}
                    placeholder="Efectos mágicos, activación, daño elemental adicional..."
                    className="w-full bg-input text-main border border-border-iron rounded px-3 py-1.5 text-xs focus:border-gold outline-none resize-none"
                  />
                </div>

                <button
                  onClick={handleSaveHomebrew}
                  className="w-full py-2 rounded-lg bg-gold hover:bg-gold-hover text-canvas font-bold text-xs transition-colors shadow-sm"
                >
                  Guardar en la Forja
                </button>
              </div>
            </div>

            {/* Catálogo de Objetos Homebrew Guardados & Entrega en Vivo */}
            <div className="lg:col-span-2 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-display font-semibold text-base text-main">
                  Biblioteca de Objetos del DM ({homebrewItems.length})
                </h3>

                {players.length > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted">Destinatario:</span>
                    <select
                      value={selectedRecipientToken}
                      onChange={(e) => setSelectedRecipientToken(e.target.value)}
                      className="bg-card text-main border border-border-iron rounded px-2.5 py-1 text-xs focus:border-gold outline-none"
                    >
                      <option value="">Selecciona un jugador</option>
                      {players.map((p) => (
                        <option key={p.player_token} value={p.player_token}>
                          {p.character_name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              {homebrewItems.length === 0 ? (
                <div className="p-8 text-center border border-dashed border-border-iron rounded-xl text-muted text-xs">
                  Aún no has creado objetos Homebrew. Usa el formulario para forjar armas, armaduras o reliquias mágicas.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {homebrewItems.map((item) => (
                    <div
                      key={item.id}
                      className="p-3.5 rounded-xl border border-border-iron bg-card/70 flex flex-col justify-between space-y-2 hover:border-gold/50 transition-colors"
                    >
                      <div>
                        <div className="flex items-center justify-between">
                          <h4 className="font-bold text-sm text-gold">{item.name}</h4>
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface border border-border-iron text-muted capitalize">
                            {item.rarity}
                          </span>
                        </div>
                        <p className="text-xs text-muted capitalize mt-0.5">{item.category}</p>
                        {item.damage_dice && (
                          <div className="mt-1 font-stat text-xs font-semibold text-main">
                            Daño: {item.damage_dice} {item.damage_type}
                          </div>
                        )}
                        {item.description && (
                          <p className="text-xs text-muted/90 mt-1.5 line-clamp-2">{item.description}</p>
                        )}
                      </div>

                      <div className="pt-2 border-t border-border-iron/40 flex items-center justify-between gap-2">
                        <button
                          onClick={() => handleGiftItem(item)}
                          disabled={!selectedRecipientToken}
                          className="flex-1 py-1 px-2.5 rounded bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-semibold text-main disabled:opacity-30 flex items-center justify-center gap-1.5 transition-colors"
                          title="Entregar al jugador seleccionado"
                        >
                          <Gift className="w-3.5 h-3.5 text-gold" />
                          <span>Entregar a Jugador</span>
                        </button>
                        <button
                          onClick={async () => {
                            if (item.id && window.confirm(`¿Eliminar ${item.name}?`)) {
                              await api.dmDeleteHomebrewItem(item.id);
                              await loadHomebrewItems();
                            }
                          }}
                          className="p-1 rounded text-muted hover:text-crimson"
                          title="Eliminar de la forja"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* PESTAÑA 3: LEDGER DE TIRADAS & BITÁCORA */}
        {activeTab === "ledger" && (
          <div className="space-y-3 max-w-4xl">
            <h3 className="font-display font-semibold text-base text-main">
              Historial de Tiradas y Eventos en Vivo
            </h3>
            {eventLogs.length === 0 ? (
              <div className="p-8 text-center border border-dashed border-border-iron rounded-xl text-muted text-xs">
                No hay tiradas ni eventos registrados en esta sesión aún.
              </div>
            ) : (
              <div className="space-y-2">
                {eventLogs.map((log) => (
                  <div
                    key={log.id}
                    className="p-3 rounded-lg border border-border-iron bg-card/60 flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-stat text-[11px] text-muted">{log.timestamp}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-surface border border-border-iron text-gold">
                        {log.event_type}
                      </span>
                      <span className="font-semibold text-main">{log.actor_name}:</span>
                      <span className="text-muted">
                        {log.event_type === "ROLL"
                          ? `Total: ${log.details?.total || log.details?.result || "Tirada"} (${log.details?.label || "Dado"})`
                          : log.event_type === "DAMAGE"
                          ? `Infligió ${log.details?.delta} daño`
                          : log.event_type === "HEAL"
                          ? `Curó ${log.details?.delta} vida`
                          : log.event_type === "ITEM_GIFT"
                          ? `Entregó: ${log.details?.item_name}`
                          : "Evento de sesión"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* PESTAÑA 4: NOTAS DEL DM (Guardadas por session_id) */}
        {activeTab === "notes" && (
          <div className="space-y-4 max-w-3xl">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-display font-semibold text-base text-main">Notas de Campaña del DM</h3>
                <p className="text-xs text-muted">
                  Escribe apuntes, descubrimientos o secretos. Se guardan vinculadas al ID de la sesión en SQLite.
                </p>
              </div>
              {effectiveSessionId && (
                <div className="flex items-center gap-1.5 bg-surface border border-border-iron rounded-lg px-2.5 py-1 text-xs font-mono text-gold">
                  <Tag className="w-3.5 h-3.5 text-muted" />
                  <span>ID: {effectiveSessionId}</span>
                </div>
              )}
            </div>
            <textarea
              rows={12}
              value={sessionNotes}
              onChange={(e) => setSessionNotes(e.target.value)}
              placeholder="Notas de los encuentros, diálogos de NPCs, pistas descubiertas para esta sesión..."
              className="w-full bg-card text-main border border-border-iron rounded-xl p-4 text-xs focus:border-gold outline-none resize-none font-mono"
            />
            <div className="flex justify-between items-center">
              <span className="text-xs text-muted">
                {effectiveSessionId ? `Guardando para sesión ${effectiveSessionId}` : "Inicia o selecciona una sesión para vincular estas notas"}
              </span>
              <button
                onClick={async () => {
                  await api.dmSaveSessionNotes(sessionNotes, effectiveSessionId || undefined);
                  showToast("Notas de la sesión guardadas en la base de datos", "success");
                }}
                className="px-4 py-2 rounded-lg bg-gold hover:bg-gold-hover text-canvas font-bold text-xs transition-colors shadow-sm"
              >
                Guardar Notas de Sesión
              </button>
            </div>
          </div>
        )}
      </div>

      {/* MODAL DE CÓDIGO QR PARA CELULARES */}
      {isQrModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs select-none">
          <div className="relative bg-surface border border-border-iron rounded-2xl p-6 max-w-sm w-full flex flex-col items-center space-y-4 shadow-2xl">
            <button
              onClick={() => setIsQrModalOpen(false)}
              className="absolute top-4 right-4 p-1 text-muted hover:text-main rounded hover:bg-card transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            <h3 className="font-display font-bold text-lg text-gold">Escanear para Unirse</h3>
            <p className="text-xs text-muted text-center">
              Los jugadores pueden apuntar con la cámara de su teléfono o tablet para abrir su ficha al instante.
            </p>
            {sessionStatus.qr_code && (
              <div className="p-3 bg-white rounded-xl shadow-inner">
                <img src={sessionStatus.qr_code} alt="Código QR de la Partida" className="w-48 h-48 object-contain" />
              </div>
            )}
            <div className="text-[11px] font-mono text-muted text-center break-all">
              {sessionStatus.tunnel_url}
            </div>
            <button
              onClick={handleCopyLink}
              className="w-full py-2 rounded-xl bg-gold hover:bg-gold-hover text-canvas font-bold text-xs flex items-center justify-center gap-1.5 transition-colors shadow-sm"
            >
              <Copy className="w-3.5 h-3.5" />
              <span>Copiar Enlace</span>
            </button>
          </div>
        </div>
      )}

      {/* MODAL DE AUDITORÍA / CONCORDANCIA DE FICHA DEL JUGADOR */}
      {inspectedPlayer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs select-none">
          <div className="relative bg-surface border border-border-iron rounded-2xl p-6 max-w-2xl w-full flex flex-col max-h-[85vh] space-y-4 shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between border-b border-border-iron pb-3">
              <div>
                <h3 className="font-display font-bold text-lg text-gold">
                  Ficha de {inspectedPlayer.character_name}
                </h3>
                <p className="text-xs text-muted">
                  Nivel {inspectedPlayer.character_level} {inspectedPlayer.character_class} • {inspectedPlayer.ac} CA • {inspectedPlayer.hp_current}/{inspectedPlayer.hp_max} HP
                </p>
              </div>
              <button
                onClick={() => setInspectedPlayer(null)}
                className="p-1 text-muted hover:text-main rounded hover:bg-card transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 p-2 text-xs">
              {inspectedPlayer.data_json ? (
                <div className="space-y-3 font-mono">
                  {(() => {
                    try {
                      const data = JSON.parse(inspectedPlayer.data_json);
                      return (
                        <div className="space-y-3">
                          <div className="grid grid-cols-6 gap-2 text-center">
                            {["str", "dex", "con", "int", "wis", "cha"].map((ab) => (
                              <div key={ab} className="p-2 rounded bg-card border border-border-iron">
                                <div className="uppercase text-[10px] text-muted">{ab}</div>
                                <div className="text-sm font-bold text-main">{data[ab]?.base || 10}</div>
                              </div>
                            ))}
                          </div>
                          {data.spells && data.spells.length > 0 && (
                            <div className="p-3 rounded bg-card border border-border-iron space-y-1">
                              <span className="font-semibold text-gold font-body">Conjuros Preparados:</span>
                              <div className="flex flex-wrap gap-1 mt-1 font-body">
                                {data.spells.map((s: any, idx: number) => (
                                  <span key={idx} className="px-2 py-0.5 rounded bg-surface border border-border-iron text-[11px]">
                                    {s.name} (Nvl {s.level})
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          {data.inventory && data.inventory.length > 0 && (
                            <div className="p-3 rounded bg-card border border-border-iron space-y-1">
                              <span className="font-semibold text-gold font-body">Inventario del Jugador:</span>
                              <div className="flex flex-wrap gap-1 mt-1 font-body">
                                {data.inventory.map((inv: any, idx: number) => (
                                  <span key={idx} className="px-2 py-0.5 rounded bg-surface border border-border-iron text-[11px]">
                                    {inv.name} (x{inv.quantity || 1})
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    } catch (e) {
                      return <pre className="text-muted">{inspectedPlayer.data_json}</pre>;
                    }
                  })()}
                </div>
              ) : (
                <p className="text-muted text-center py-6">No hay datos extendidos recibidos de la ficha.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
