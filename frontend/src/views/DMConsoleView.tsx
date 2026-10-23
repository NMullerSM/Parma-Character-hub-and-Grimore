import React, { useState, useEffect } from "react";
import { useCharacter } from "../context/CharacterContext";
import { api } from "../api/client";
import type { DmSessionStatus, DmSessionPlayer, DmHomebrewItem, DmSessionEventLog } from "../api/types";
import {
  Wifi,
  Copy,
  QrCode,
  Shield,
  Heart,
  Gift,
  Scroll,
  Users,
  Check,
  Sparkles,
  X,
  FileText,
  Tag,
  Power,
  Dices,
  Swords,
  Activity,
  Eye,
  Wand2,
} from "lucide-react";

export const DMConsoleView: React.FC = () => {
  const { showToast, setActiveSessionId, sessionScopeActive, toggleSessionScope } = useCharacter();

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

  // Jugador seleccionado para inspección completa de ficha 5e
  const [inspectedPlayer, setInspectedPlayer] = useState<DmSessionPlayer | null>(null);
  const [sheetModalTab, setSheetModalTab] = useState<"general" | "skills" | "combat" | "spells" | "features">("general");

  // Filtro de bitácora
  const [logFilter, setLogFilter] = useState<"all" | "rolls" | "combat" | "session">("all");

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
  const [hbScrollContent, setHbScrollContent] = useState<string>("");
  const [selectedRecipientToken, setSelectedRecipientToken] = useState<string>("");

  // Ledger y notas
  const [eventLogs, setEventLogs] = useState<DmSessionEventLog[]>([]);
  const [sessionNotes, setSessionNotes] = useState<string>("");

  // Jugadores seguros contra null
  const players = sessionStatus?.players || [];

  // Atajo de escape universal para modales (Hick's Law: escape hatch explícito)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (inspectedPlayer) {
          setInspectedPlayer(null);
        } else if (isQrModalOpen) {
          setIsQrModalOpen(false);
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [inspectedPlayer, isQrModalOpen]);

  useEffect(() => {
    loadStatus();
    loadPastSessions();
    loadHomebrewItems();
    const interval = setInterval(loadStatus, 4000);
    return () => clearInterval(interval);
  }, []);

  // Canal WebSocket en tiempo real para eventos de la mesa hacia la consola DM
  useEffect(() => {
    if (!sessionStatus.is_running || !sessionStatus.port) return;

    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(`ws://127.0.0.1:${sessionStatus.port}/ws?role=dm`);
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (
            data.type === "PLAYER_JOINED" ||
            data.type === "PLAYER_SOCKET_ONLINE" ||
            data.type === "PLAYER_SOCKET_OFFLINE" ||
            data.type === "PLAYER_SHEET_UPDATED" ||
            data.type === "PLAYER_LIST_UPDATED"
          ) {
            loadStatus();
            if (data.type === "PLAYER_JOINED" && data.character_name) {
              showToast(`¡${data.character_name} se ha unido a la mesa!`, "success");
            }
          } else if (data.type === "DICE_ROLL_SHARED") {
            loadStatus();
          }
        } catch (_) {}
      };
    } catch (_) {}

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [sessionStatus.is_running, sessionStatus.port, showToast]);

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
        damage_dice: hbCategory === "weapon" ? (hbDamageDice.trim() || undefined) : undefined,
        damage_type: hbCategory === "weapon" ? (hbDamageType.trim() || undefined) : undefined,
        secondary_dice: hbCategory === "weapon" ? (hbSecondaryDice.trim() || undefined) : undefined,
        secondary_type: hbCategory === "weapon" ? (hbSecondaryType.trim() || undefined) : undefined,
        bonus_attack: hbCategory === "weapon" ? hbBonusAttack : 0,
        bonus_damage: hbCategory === "weapon" ? hbBonusDamage : 0,
        ac_bonus: hbCategory === "armor" ? hbAcBonus : 0,
        description: hbDesc.trim(),
        scroll_content: hbCategory === "scroll" ? hbScrollContent.trim() : undefined,
      };
      await api.dmSaveHomebrewItem(newItem);
      showToast(`Objeto "${newItem.name}" forjado y guardado`, "success");
      setHbName("");
      setHbDesc("");
      setHbScrollContent("");
      await loadHomebrewItems();
    } catch (e) {
      showToast("Error al guardar objeto homebrew", "warn");
    }
  };

  const handleGiftItem = async (item: DmHomebrewItem, targetToken?: string) => {
    const recipientToken = targetToken || selectedRecipientToken;
    if (!recipientToken) {
      showToast("Selecciona a qué jugador deseas entregar el objeto", "warn");
      return;
    }
    const targetPlayer = players.find((p) => p.player_token === recipientToken);
    try {
      await api.dmGiftItem(recipientToken, item);
      showToast(`¡"${item.name}" entregado a ${targetPlayer?.character_name || "jugador"}!`, "success");
      await loadStatus();
    } catch (e) {
      showToast("Error al entregar objeto al jugador", "warn");
    }
  };

  const effectiveSessionId = sessionStatus.session_id || (selectedSessionId !== "new" ? selectedSessionId : null);

  return (
    <div className="h-full flex flex-col bg-canvas text-main overflow-hidden select-none">
      {/* Barra de Sesión Unificada (Slim & Hick's Law compliant) */}
      {sessionStatus.is_running ? (
        <div className="px-5 py-2.5 border-b border-border-iron bg-surface flex flex-wrap items-center justify-between gap-3 shrink-0">
          <div className="flex items-center gap-2.5 min-w-0 flex-1">
            {/* Indicador ONLINE */}
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/40 text-[10px] font-bold text-emerald-400 shrink-0">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>ONLINE</span>
            </div>

            {/* Nombre de la Sesión */}
            <span className="font-display font-bold text-sm text-gold truncate shrink-0 max-w-[180px]">
              {sessionStatus.session_name || sessionNameInput}
            </span>

            {/* ID de la Sesión */}
            {sessionStatus.session_id && (
              <div className="flex items-center gap-1 text-[11px] font-mono text-muted bg-card px-2 py-0.5 rounded border border-border-iron shrink-0">
                <span>ID: {sessionStatus.session_id}</span>
                <button
                  onClick={handleCopySessionId}
                  className="text-gold hover:underline ml-0.5 font-sans"
                  title="Copiar ID de la Sesión"
                >
                  {copiedId ? "✓" : <Copy className="w-3 h-3 inline" />}
                </button>
              </div>
            )}

            {/* Enlace Público Truncado */}
            {sessionStatus.tunnel_url && (
              <div className="flex items-center gap-1.5 text-xs font-mono text-muted bg-card/60 px-2 py-0.5 rounded border border-border-iron/80 truncate flex-1 min-w-0 max-w-md">
                <span className="text-gold font-semibold shrink-0">Link:</span>
                <span className="truncate text-main select-all">{sessionStatus.tunnel_url}</span>
              </div>
            )}
          </div>

          {/* Acciones del DM a la Derecha */}
          <div className="flex items-center gap-2 shrink-0">
            {/* Ámbito de Recursos de Sesión (Session Scope) */}
            <button
              onClick={toggleSessionScope}
              title={
                sessionScopeActive
                  ? "Recursos de Sesión: ACTIVADO (Mostrando solo personajes y notas de esta sesión). Clic para ver todos."
                  : "Recursos de Sesión: DESACTIVADO (Mostrando todos los recursos globales). Clic para filtrar solo esta sesión."
              }
              className={`px-2.5 py-1 rounded-lg border text-xs font-semibold transition-all ${
                sessionScopeActive
                  ? "bg-amber-500/20 border-amber-500/60 text-amber-300 ring-1 ring-amber-500/40"
                  : "bg-card border-border-iron text-muted hover:text-main"
              }`}
            >
              {sessionScopeActive ? "🎯 Sesión: ON" : "🎯 Sesión: OFF"}
            </button>

            {/* Copiar Enlace */}
            {sessionStatus.tunnel_url && (
              <button
                onClick={handleCopyLink}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 active:scale-95 ${
                  copiedUrl
                    ? "bg-emerald-500 text-canvas font-bold"
                    : "bg-gold hover:bg-gold-hover text-canvas"
                }`}
                title="Copiar enlace de invitación"
              >
                {copiedUrl ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedUrl ? "¡Copiado!" : "Copiar Link"}</span>
              </button>
            )}

            {/* Código QR */}
            {sessionStatus.qr_code && (
              <button
                onClick={() => setIsQrModalOpen(true)}
                className="p-1.5 rounded-lg border border-border-iron bg-card hover:bg-surface text-muted hover:text-gold transition-colors"
                title="Ver código QR para móviles"
              >
                <QrCode className="w-4 h-4" />
              </button>
            )}

            {/* Botón de Solo Apagar (Power) para terminar sesión */}
            <button
              onClick={handleStopSession}
              disabled={isLoading}
              className="p-1.5 rounded-lg border border-crimson/50 bg-crimson/10 text-crimson hover:bg-crimson hover:text-white transition-colors"
              title="Terminar y cerrar sesión online (Apagar túnel)"
            >
              <Power className="w-4 h-4" />
            </button>
          </div>
        </div>
      ) : (
        /* Barra de Control cuando NO está en línea */
        <div className="px-5 py-2.5 border-b border-border-iron bg-surface flex flex-wrap items-center justify-between gap-3 shrink-0">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted font-medium">Sesión:</span>
              <select
                value={selectedSessionId}
                onChange={(e) => handleSelectSession(e.target.value)}
                className="bg-card text-main border border-border-iron rounded-lg px-2.5 py-1 text-xs font-semibold focus:border-gold outline-none"
              >
                <option value="new">+ Nueva Sesión...</option>
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
                  className="bg-card text-main border border-border-iron rounded-lg px-2.5 py-1 text-xs focus:border-gold outline-none w-44"
                />
                <input
                  type="text"
                  value={campaignNameInput}
                  onChange={(e) => setCampaignNameInput(e.target.value)}
                  placeholder="Campaña"
                  className="bg-card text-main border border-border-iron rounded-lg px-2.5 py-1 text-xs focus:border-gold outline-none w-36"
                />
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs text-muted">
                <span className="font-mono bg-card px-2 py-0.5 rounded border border-border-iron">
                  ID: {selectedSessionId}
                </span>
              </div>
            )}
          </div>

          <div>
            <button
              onClick={handleStartSession}
              disabled={isLoading}
              className="px-4 py-1.5 rounded-lg bg-gold hover:bg-gold-hover text-canvas font-bold text-xs shadow-sm transition-all flex items-center gap-1.5 active:scale-95"
            >
              <Wifi className="w-3.5 h-3.5" />
              <span>{isLoading ? "Iniciando..." : (selectedSessionId !== "new" ? "Reanudar Sesión" : "Iniciar Sesión Online")}</span>
            </button>
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
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3.5">
                {players.map((p) => {
                  const hpPct = Math.max(0, Math.min(100, (p.hp_current / (p.hp_max || 1)) * 100));
                  const isDead = p.status === "DEAD";
                  const isUnconscious = p.hp_current <= 0 || p.status === "UNCONSCIOUS";

                  let parsedData: any = null;
                  try {
                    if (p.data_json) parsedData = JSON.parse(p.data_json);
                  } catch (_) {}
                  const portraitUrl = parsedData?.portrait_base64 || parsedData?.avatar_url || null;

                  return (
                    <div
                      key={p.player_token}
                      className={`p-3.5 rounded-xl border bg-card/75 hover:bg-card/90 flex flex-col justify-between space-y-2.5 transition-all shadow-xs ${
                        isDead
                          ? "border-red-900/50 opacity-60"
                          : isUnconscious
                          ? "border-crimson shadow-[0_0_12px_rgba(230,57,70,0.25)]"
                          : "border-border-iron hover:border-gold/50"
                      }`}
                    >
                      {/* Cabecera compacta: Avatar, Nombre, Clase y CA */}
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2.5 min-w-0">
                          {portraitUrl ? (
                            <img
                              src={portraitUrl}
                              alt={p.character_name}
                              className="w-10 h-10 rounded-full object-cover border border-gold/40 shadow-xs shrink-0"
                            />
                          ) : (
                            <div className="w-10 h-10 rounded-full bg-surface border border-border-iron flex items-center justify-center font-bold text-xs text-gold shrink-0">
                              {p.character_name.slice(0, 2).toUpperCase()}
                            </div>
                          )}
                          <div className="min-w-0">
                            <h4 className="font-bold text-sm text-main truncate flex items-center gap-1.5">
                              <span className="truncate">{p.character_name}</span>
                              <span
                                className={`w-2 h-2 rounded-full shrink-0 ${p.is_online ? "bg-emerald-400" : "bg-muted"}`}
                                title={p.is_online ? "Conectado en vivo" : "Desconectado"}
                              />
                            </h4>
                            <p className="text-[11px] text-muted truncate">
                              Nvl {p.character_level} {p.character_class || "Aventurero"}
                            </p>
                          </div>
                        </div>

                        {/* CA Pill */}
                        <div className="flex items-center gap-1 bg-surface px-2 py-1 rounded-md border border-border-iron text-xs font-stat shrink-0" title="Clase de Armadura">
                          <Shield className="w-3.5 h-3.5 text-gold" />
                          <span className="font-bold text-main">{p.ac || 10}</span>
                        </div>
                      </div>

                      {/* Barra de Vida y Valores Numéricos */}
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs font-stat">
                          <span className="flex items-center gap-1 text-[11px] text-muted">
                            <Heart className={`w-3 h-3 ${isUnconscious ? "text-crimson" : "text-emerald-500"}`} />
                            <span>Puntos de Golpe</span>
                          </span>
                          <span className="font-bold text-main text-xs">
                            {p.hp_current} / {p.hp_max}
                          </span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-canvas border border-border-iron overflow-hidden">
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

                      {/* Botones de Acción Rápida de Daño / Curación */}
                      <div className="grid grid-cols-4 gap-1 pt-1">
                        <button
                          onClick={() => handleHpChange(p.player_token, -5, p.character_name)}
                          className="py-1 rounded bg-crimson/15 hover:bg-crimson text-crimson hover:text-white border border-crimson/70 text-xs font-bold transition-colors"
                          title="Infligir 5 de daño"
                        >
                          -5
                        </button>
                        <button
                          onClick={() => handleHpChange(p.player_token, -1, p.character_name)}
                          className="py-1 rounded bg-crimson/10 hover:bg-crimson text-crimson hover:text-white border border-crimson/50 text-xs font-bold transition-colors"
                          title="Infligir 1 de daño"
                        >
                          -1
                        </button>
                        <button
                          onClick={() => handleHpChange(p.player_token, 1, p.character_name)}
                          className="py-1 rounded bg-emerald-500/10 hover:bg-emerald-500 text-emerald-400 hover:text-white border border-emerald-500/50 text-xs font-bold transition-colors"
                          title="Curar 1 punto"
                        >
                          +1
                        </button>
                        <button
                          onClick={() => handleHpChange(p.player_token, 5, p.character_name)}
                          className="py-1 rounded bg-emerald-500/15 hover:bg-emerald-500 text-emerald-400 hover:text-white border border-emerald-500/70 text-xs font-bold transition-colors"
                          title="Curar 5 puntos"
                        >
                          +5
                        </button>
                      </div>

                      {/* Botón Hick's Law: Ver Ficha Completa */}
                      <button
                        onClick={() => setInspectedPlayer(p)}
                        className="w-full py-1.5 rounded-lg bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-semibold text-main hover:text-gold flex items-center justify-center gap-1.5 transition-colors shadow-2xs"
                        title="Abrir hoja de personaje completa del jugador"
                      >
                        <Eye className="w-3.5 h-3.5 text-gold" />
                        <span>Ver Ficha</span>
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
                      <option value="scroll">📜 Pergamino / Documento</option>
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

                {/* Campos específicos según categoría */}
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

                {hbCategory === "scroll" && (
                  <div className="space-y-1">
                    <label className="block text-xs font-semibold uppercase tracking-wider text-gold flex items-center gap-1.5 mb-1">
                      <Scroll className="w-3.5 h-3.5" />
                      <span>Contenido del Pergamino / Carta</span>
                    </label>
                    <textarea
                      rows={5}
                      value={hbScrollContent}
                      onChange={(e) => setHbScrollContent(e.target.value)}
                      placeholder="Escribe el texto íntegro que el jugador podrá leer en su ficha (cartas, acertijos, decretos reales, mapas textuales)..."
                      className="w-full bg-input text-main border border-border-iron rounded-lg p-2.5 text-xs focus:border-gold outline-none resize-none font-serif leading-relaxed"
                    />
                  </div>
                )}

                {hbCategory !== "scroll" && (
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
                )}

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
                    Descripción & Propiedades
                  </label>
                  <textarea
                    rows={2}
                    value={hbDesc}
                    onChange={(e) => setHbDesc(e.target.value)}
                    placeholder="Efectos mágicos, activación, notas breves..."
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

            {/* Catálogo de Objetos Homebrew Guardados & Entrega Directa */}
            <div className="lg:col-span-2 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-display font-semibold text-base text-main">
                  Biblioteca de Objetos del DM ({homebrewItems.length})
                </h3>

                {players.length > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted">Destinatario por Defecto:</span>
                    <select
                      value={selectedRecipientToken}
                      onChange={(e) => setSelectedRecipientToken(e.target.value)}
                      className="bg-card text-main border border-border-iron rounded px-2.5 py-1 text-xs focus:border-gold outline-none"
                    >
                      <option value="">Selecciona un jugador...</option>
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
                  Aún no has creado objetos Homebrew. Usa el formulario para forjar armas, armaduras, pergaminos o reliquias mágicas.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {homebrewItems.map((item) => (
                    <div
                      key={item.id}
                      className="p-3.5 rounded-xl border border-border-iron bg-card/70 flex flex-col justify-between space-y-2.5 hover:border-gold/50 transition-colors shadow-2xs"
                    >
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between gap-1">
                          <h4 className="font-bold text-sm text-gold truncate flex items-center gap-1.5">
                            {item.category === "scroll" ? <Scroll className="w-3.5 h-3.5 shrink-0 text-amber-400" /> : <Sparkles className="w-3.5 h-3.5 shrink-0 text-gold" />}
                            <span className="truncate">{item.name}</span>
                          </h4>
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface border border-border-iron text-muted capitalize shrink-0">
                            {item.rarity}
                          </span>
                        </div>
                        <p className="text-[11px] text-muted capitalize">
                          {item.category === "scroll" ? "Pergamino / Documento" : item.category}
                        </p>
                        {item.damage_dice && (
                          <div className="font-stat text-xs font-semibold text-main">
                            Daño: {item.damage_dice} {item.damage_type}
                          </div>
                        )}
                        {item.description && (
                          <p className="text-xs text-muted/90 line-clamp-2">{item.description}</p>
                        )}
                        {item.category === "scroll" && item.scroll_content && (
                          <div className="p-2 bg-surface/70 rounded border border-border-iron/80 text-[11px] text-main font-serif italic line-clamp-3">
                            "{item.scroll_content}"
                          </div>
                        )}
                      </div>

                      <div className="pt-2 border-t border-border-iron/40 space-y-2">
                        <div className="flex items-center gap-1.5">
                          {players.length > 0 && (
                            <button
                              onClick={() => handleGiftItem(item)}
                              disabled={!selectedRecipientToken}
                              className="flex-1 py-1.5 px-2.5 rounded bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-semibold text-main disabled:opacity-30 flex items-center justify-center gap-1.5 transition-colors shadow-2xs"
                              title={selectedRecipientToken ? "Entregar al jugador seleccionado por defecto" : "Selecciona un jugador en el desplegable superior"}
                            >
                              <Gift className="w-3.5 h-3.5 text-gold" />
                              <span>Entregar</span>
                            </button>
                          )}
                          <button
                            onClick={async () => {
                              if (item.id && window.confirm(`¿Eliminar ${item.name}?`)) {
                                await api.dmDeleteHomebrewItem(item.id);
                                await loadHomebrewItems();
                              }
                            }}
                            className="p-1.5 rounded text-muted hover:text-crimson hover:bg-surface border border-transparent hover:border-crimson/30 transition-colors"
                            title="Eliminar de la forja"
                          >
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* PESTAÑA 3: LEDGER DE TIRADAS & BITÁCORA */}
        {activeTab === "ledger" && (() => {
          const rollLogsCount = eventLogs.filter((l) => l.event_type === "ROLL").length;
          const combatLogsCount = eventLogs.filter((l) => l.event_type === "DAMAGE" || l.event_type === "HEAL").length;
          const sessionLogsCount = eventLogs.filter((l) => l.event_type !== "ROLL" && l.event_type !== "DAMAGE" && l.event_type !== "HEAL").length;

          const filteredLogs = eventLogs.filter((log) => {
            if (logFilter === "rolls") return log.event_type === "ROLL";
            if (logFilter === "combat") return log.event_type === "DAMAGE" || log.event_type === "HEAL";
            if (logFilter === "session") return log.event_type !== "ROLL" && log.event_type !== "DAMAGE" && log.event_type !== "HEAL";
            return true;
          });

          return (
            <div className="space-y-4 max-w-4xl">
              {/* Encabezado y Barra de Filtros de Bitácora */}
              <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-border-iron/60">
                <div>
                  <h3 className="font-display font-semibold text-base text-main">
                    Bitácora de Sesión y Tiradas en Vivo
                  </h3>
                  <p className="text-xs text-muted">
                    Historial sincronizado en tiempo real de todos los participantes.
                  </p>
                </div>

                {/* Filtros tipo Tabs para evitar saturación visual */}
                <div className="flex items-center gap-1 bg-surface p-1 rounded-xl border border-border-iron text-xs">
                  <button
                    onClick={() => setLogFilter("all")}
                    className={`px-3 py-1 rounded-lg font-semibold transition-all ${
                      logFilter === "all"
                        ? "bg-gold text-canvas shadow-xs font-bold"
                        : "text-muted hover:text-main"
                    }`}
                  >
                    Todas ({eventLogs.length})
                  </button>
                  <button
                    onClick={() => setLogFilter("rolls")}
                    className={`px-3 py-1 rounded-lg font-semibold flex items-center gap-1.5 transition-all ${
                      logFilter === "rolls"
                        ? "bg-gold text-canvas shadow-xs font-bold"
                        : "text-muted hover:text-main"
                    }`}
                  >
                    <Dices className="w-3.5 h-3.5" />
                    <span>Tiradas ({rollLogsCount})</span>
                  </button>
                  <button
                    onClick={() => setLogFilter("combat")}
                    className={`px-3 py-1 rounded-lg font-semibold flex items-center gap-1.5 transition-all ${
                      logFilter === "combat"
                        ? "bg-gold text-canvas shadow-xs font-bold"
                        : "text-muted hover:text-main"
                    }`}
                  >
                    <Swords className="w-3.5 h-3.5" />
                    <span>Combate ({combatLogsCount})</span>
                  </button>
                  <button
                    onClick={() => setLogFilter("session")}
                    className={`px-3 py-1 rounded-lg font-semibold flex items-center gap-1.5 transition-all ${
                      logFilter === "session"
                        ? "bg-gold text-canvas shadow-xs font-bold"
                        : "text-muted hover:text-main"
                    }`}
                  >
                    <Activity className="w-3.5 h-3.5" />
                    <span>Sesión ({sessionLogsCount})</span>
                  </button>
                </div>
              </div>

              {filteredLogs.length === 0 ? (
                <div className="p-10 text-center border border-dashed border-border-iron rounded-xl text-muted text-xs space-y-1">
                  <p className="font-semibold text-main">No hay eventos en esta categoría</p>
                  <p className="text-[11px]">
                    {logFilter === "rolls"
                      ? "Aún no se han realizado tiradas de dados en la mesa."
                      : logFilter === "combat"
                      ? "No hay registros de daño o curación todavía."
                      : "No hay eventos registrados en esta categoría aún."}
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredLogs.map((log) => {
                    const isRoll = log.event_type === "ROLL";
                    const isDamage = log.event_type === "DAMAGE";
                    const isHeal = log.event_type === "HEAL";

                    if (isRoll) {
                      return (
                        <div
                          key={log.id}
                          className="p-3 rounded-xl border border-border-iron bg-card/70 hover:bg-card/90 flex flex-wrap items-center justify-between gap-3 text-xs transition-colors shadow-2xs"
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            <div className="w-8 h-8 rounded-lg bg-gold/10 border border-gold/40 flex items-center justify-center text-gold shrink-0">
                              <Dices className="w-4 h-4" />
                            </div>
                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="font-bold text-main">{log.actor_name}</span>
                                <span className="px-1.5 py-0.5 rounded text-[10px] font-mono text-muted bg-surface border border-border-iron/80">
                                  {log.details?.formula || "d20"}
                                </span>
                                <span className="text-[11px] text-muted truncate">
                                  {log.details?.label || "Tirada"}
                                </span>
                              </div>
                              <div className="text-[10px] text-muted font-stat mt-0.5">
                                {log.timestamp}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            {log.details?.is_crit && (
                              <span className="px-2 py-0.5 rounded-full bg-gold/20 border border-gold text-gold font-bold text-[10px] animate-pulse">
                                ¡CRÍTICO!
                              </span>
                            )}
                            {log.details?.is_fumble && (
                              <span className="px-2 py-0.5 rounded-full bg-crimson/20 border border-crimson text-crimson font-bold text-[10px]">
                                PIFIA
                              </span>
                            )}
                            <div className="px-3 py-1 rounded-lg bg-surface border border-border-iron font-stat font-bold text-sm text-gold">
                              Total: {log.details?.total ?? log.details?.result ?? "—"}
                            </div>
                          </div>
                        </div>
                      );
                    }

                    if (isDamage) {
                      return (
                        <div
                          key={log.id}
                          className="p-3 rounded-xl border border-crimson/30 bg-crimson/5 hover:bg-crimson/10 flex flex-wrap items-center justify-between gap-3 text-xs transition-colors shadow-2xs"
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            <div className="w-8 h-8 rounded-lg bg-crimson/15 border border-crimson/40 flex items-center justify-center text-crimson shrink-0">
                              <Swords className="w-4 h-4" />
                            </div>
                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="font-bold text-main">{log.actor_name}</span>
                                <span className="text-muted">infligió daño a</span>
                                <span className="font-bold text-crimson">{log.details?.target_name || log.target_name || "Objetivo"}</span>
                              </div>
                              <div className="text-[10px] text-muted font-stat mt-0.5">
                                {log.timestamp}
                              </div>
                            </div>
                          </div>

                          <div className="px-2.5 py-1 rounded-lg bg-crimson/20 border border-crimson text-crimson font-bold font-stat text-xs shrink-0">
                            -{log.details?.delta} HP
                          </div>
                        </div>
                      );
                    }

                    if (isHeal) {
                      return (
                        <div
                          key={log.id}
                          className="p-3 rounded-xl border border-emerald-500/30 bg-emerald-500/5 hover:bg-emerald-500/10 flex flex-wrap items-center justify-between gap-3 text-xs transition-colors shadow-2xs"
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            <div className="w-8 h-8 rounded-lg bg-emerald-500/15 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shrink-0">
                              <Heart className="w-4 h-4" />
                            </div>
                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="font-bold text-main">{log.actor_name}</span>
                                <span className="text-muted">recibió curación</span>
                                {log.details?.target_name && (
                                  <span className="font-bold text-emerald-400">({log.details.target_name})</span>
                                )}
                              </div>
                              <div className="text-[10px] text-muted font-stat mt-0.5">
                                {log.timestamp}
                              </div>
                            </div>
                          </div>

                          <div className="px-2.5 py-1 rounded-lg bg-emerald-500/20 border border-emerald-500 text-emerald-400 font-bold font-stat text-xs shrink-0">
                            +{log.details?.delta} HP
                          </div>
                        </div>
                      );
                    }

                    return (
                      <div
                        key={log.id}
                        className="p-3 rounded-xl border border-border-iron bg-card/60 flex flex-wrap items-center justify-between gap-3 text-xs shadow-2xs"
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <div className="w-8 h-8 rounded-lg bg-surface border border-border-iron flex items-center justify-center text-gold shrink-0">
                            <Activity className="w-4 h-4" />
                          </div>
                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-main">{log.actor_name}</span>
                              <span className="text-muted">
                                {log.event_type === "ITEM_GIFT"
                                  ? `Entregó "${log.details?.item_name}" a ${log.details?.recipient_name || "jugador"}`
                                  : log.event_type === "PLAYER_JOIN"
                                  ? "Se unió a la sesión de juego"
                                  : "Evento registrado en sesión"}
                              </span>
                            </div>
                            <div className="text-[10px] text-muted font-stat mt-0.5">
                              {log.timestamp}
                            </div>
                          </div>
                        </div>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider bg-surface border border-border-iron text-muted">
                          {log.event_type}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })()}

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

      {/* MODAL DE FICHA COMPLETA 5E DEL JUGADOR */}
      {inspectedPlayer && (() => {
        let charData: any = {};
        try {
          if (inspectedPlayer.data_json) {
            charData = JSON.parse(inspectedPlayer.data_json);
          }
        } catch (_) {}

        const portraitUrl = charData?.portrait_base64 || charData?.avatar_url || null;
        const profBonus = Number(charData?.proficiency_bonus) || 2;

        const STANDARD_SKILLS: Array<{ id: string; name: string; ability: "str" | "dex" | "con" | "int" | "wis" | "cha" }> = [
          { id: "athletics", name: "Atletismo", ability: "str" },
          { id: "acrobatics", name: "Acrobacias", ability: "dex" },
          { id: "sleight_of_hand", name: "Juego de Manos", ability: "dex" },
          { id: "stealth", name: "Sigilo", ability: "dex" },
          { id: "arcana", name: "Arcanos", ability: "int" },
          { id: "history", name: "Historia", ability: "int" },
          { id: "investigation", name: "Investigación", ability: "int" },
          { id: "nature", name: "Naturaleza", ability: "int" },
          { id: "religion", name: "Religión", ability: "int" },
          { id: "animal_handling", name: "Trato con Animales", ability: "wis" },
          { id: "insight", name: "Perspicacia", ability: "wis" },
          { id: "medicine", name: "Medicina", ability: "wis" },
          { id: "perception", name: "Percepción", ability: "wis" },
          { id: "survival", name: "Supervivencia", ability: "wis" },
          { id: "deception", name: "Engaño", ability: "cha" },
          { id: "intimidation", name: "Intimidación", ability: "cha" },
          { id: "performance", name: "Interpretación", ability: "cha" },
          { id: "persuasion", name: "Persuasión", ability: "cha" },
        ];

        const ABILITY_KEYS: Array<{ key: "str" | "dex" | "con" | "int" | "wis" | "cha"; short: string; full: string }> = [
          { key: "str", short: "FUE", full: "Fuerza" },
          { key: "dex", short: "DES", full: "Destreza" },
          { key: "con", short: "CON", full: "Constitución" },
          { key: "int", short: "INT", full: "Inteligencia" },
          { key: "wis", short: "SAB", full: "Sabiduría" },
          { key: "cha", short: "CAR", full: "Carisma" },
        ];

        const getAbilityScore = (ab: string): number => {
          const val = charData?.abilities?.[ab] || charData?.[ab];
          if (typeof val === "number") return val;
          if (val && typeof val.override === "number" && val.override > 0) return val.override;
          if (val && typeof val.base === "number") return val.base;
          return 10;
        };

        const getAbilityMod = (score: number): number => {
          return Math.floor((score - 10) / 2);
        };

        const formatModifier = (mod: number): string => {
          return mod >= 0 ? `+${mod}` : `${mod}`;
        };

        const getSaveData = (abKey: string) => {
          const ab = charData?.abilities?.[abKey] || charData?.[abKey];
          const isProf = Boolean(ab?.proficient);
          const score = getAbilityScore(abKey);
          const mod = getAbilityMod(score);
          const extra = ab?.save_bonus || 0;
          const total = mod + (isProf ? profBonus : 0) + extra;
          return { isProf, bonus: total, bonusStr: formatModifier(total) };
        };

        const getSkillData = (skillId: string, abilityKey: string) => {
          const sk = charData?.skills?.[skillId];
          const isProf = Boolean(sk?.proficient);
          const isExpert = Boolean(sk?.expertise);
          const abScore = getAbilityScore(abilityKey);
          const baseMod = getAbilityMod(abScore);
          let total = baseMod;
          if (isExpert) total += profBonus * 2;
          else if (isProf) total += profBonus;
          if (sk?.bonus) total += sk.bonus;
          return { isProf, isExpert, bonus: total, bonusStr: formatModifier(total) };
        };

        const weaponActions = charData?.weapon_actions || [];
        const spells = charData?.spells || [];
        const features = charData?.features || [];
        const inventory = charData?.inventory || [];
        const spellSlotsTotal = charData?.spell_slots_total || {};
        const spellSlotsUsed = charData?.spell_slots_used || {};

        return (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center p-3 md:p-6 bg-black/80 backdrop-blur-xs select-none"
            onClick={(e) => {
              if (e.target === e.currentTarget) setInspectedPlayer(null);
            }}
          >
            <div className="relative bg-surface border border-border-iron rounded-2xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
              {/* Cabecera de la Ficha Completa */}
              <div className="p-4 md:p-5 border-b border-border-iron bg-card/50 flex items-start justify-between gap-4">
                <div className="flex items-center gap-3.5 min-w-0">
                  {portraitUrl ? (
                    <img
                      src={portraitUrl}
                      alt={inspectedPlayer.character_name}
                      className="w-14 h-14 rounded-full object-cover border-2 border-gold shadow-md shrink-0"
                    />
                  ) : (
                    <div className="w-14 h-14 rounded-full bg-surface border-2 border-border-iron flex items-center justify-center font-bold text-base text-gold shrink-0">
                      {inspectedPlayer.character_name.slice(0, 2).toUpperCase()}
                    </div>
                  )}

                  <div className="min-w-0 space-y-0.5">
                    <h3 className="font-display font-bold text-lg md:text-xl text-gold truncate">
                      {inspectedPlayer.character_name}
                    </h3>
                    <p className="text-xs text-muted truncate">
                      Nivel {charData.level || inspectedPlayer.character_level} {charData.race || ""} • {charData.char_class || inspectedPlayer.character_class} {charData.subclass ? `(${charData.subclass})` : ""}
                    </p>
                    <p className="text-[11px] text-muted/80 truncate">
                      Trasfondo: {charData.background || "Aventurero"} • Alineamiento: {charData.alignment || "Neutral"}
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => setInspectedPlayer(null)}
                  className="p-1.5 text-muted hover:text-main rounded-lg hover:bg-card border border-transparent hover:border-border-iron transition-colors shrink-0"
                  title="Cerrar Ficha (Esc)"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Estadísticas Clave en Banda Horizontal */}
              <div className="px-4 py-2.5 bg-canvas/60 border-b border-border-iron flex flex-wrap items-center gap-2 md:gap-4 text-xs font-stat">
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface border border-border-iron">
                  <Shield className="w-3.5 h-3.5 text-gold" />
                  <span className="text-muted">CA:</span>
                  <span className="font-bold text-main">{charData.ac || inspectedPlayer.ac || 10}</span>
                </div>

                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface border border-border-iron">
                  <Heart className="w-3.5 h-3.5 text-crimson" />
                  <span className="text-muted">Puntos de Golpe:</span>
                  <span className="font-bold text-main">
                    {charData.hp_current ?? inspectedPlayer.hp_current} / {charData.hp_max ?? inspectedPlayer.hp_max}
                  </span>
                  {charData.hp_temp > 0 && (
                    <span className="text-amber-400 font-bold">(+{charData.hp_temp} Temp)</span>
                  )}
                </div>

                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface border border-border-iron">
                  <span className="text-muted">Dados de Golpe:</span>
                  <span className="font-bold text-main">{charData.hit_dice_current || charData.hit_dice_total || "1d8"}</span>
                </div>

                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface border border-border-iron">
                  <span className="text-muted">Velocidad:</span>
                  <span className="font-bold text-main">{charData.speed || 30} pies</span>
                </div>

                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface border border-border-iron">
                  <span className="text-muted">Iniciativa:</span>
                  <span className="font-bold text-main">{formatModifier(charData.initiative || 0)}</span>
                </div>

                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface border border-border-iron">
                  <span className="text-muted">Competencia:</span>
                  <span className="font-bold text-main">+{profBonus}</span>
                </div>

                {charData.inspiration && (
                  <span className="px-2 py-0.5 rounded-full bg-gold/15 border border-gold/50 text-gold font-bold text-[11px]">
                    ⭐ Inspiración
                  </span>
                )}
              </div>

              {/* Sub-navegación de la Ficha (Hick's Law: Organización clara en 5 secciones) */}
              <div className="px-4 border-b border-border-iron bg-card/30 flex gap-1 shrink-0 overflow-x-auto">
                <button
                  onClick={() => setSheetModalTab("general")}
                  className={`py-2 px-3 text-xs font-semibold border-b-2 flex items-center gap-1.5 transition-colors whitespace-nowrap ${
                    sheetModalTab === "general"
                      ? "border-gold text-gold font-bold"
                      : "border-transparent text-muted hover:text-main"
                  }`}
                >
                  <Users className="w-3.5 h-3.5" />
                  <span>Atributos y Salvaciones</span>
                </button>
                <button
                  onClick={() => setSheetModalTab("skills")}
                  className={`py-2 px-3 text-xs font-semibold border-b-2 flex items-center gap-1.5 transition-colors whitespace-nowrap ${
                    sheetModalTab === "skills"
                      ? "border-gold text-gold font-bold"
                      : "border-transparent text-muted hover:text-main"
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Habilidades (18)</span>
                </button>
                <button
                  onClick={() => setSheetModalTab("combat")}
                  className={`py-2 px-3 text-xs font-semibold border-b-2 flex items-center gap-1.5 transition-colors whitespace-nowrap ${
                    sheetModalTab === "combat"
                      ? "border-gold text-gold font-bold"
                      : "border-transparent text-muted hover:text-main"
                  }`}
                >
                  <Swords className="w-3.5 h-3.5" />
                  <span>Armas y Ataques ({weaponActions.length})</span>
                </button>
                <button
                  onClick={() => setSheetModalTab("spells")}
                  className={`py-2 px-3 text-xs font-semibold border-b-2 flex items-center gap-1.5 transition-colors whitespace-nowrap ${
                    sheetModalTab === "spells"
                      ? "border-gold text-gold font-bold"
                      : "border-transparent text-muted hover:text-main"
                  }`}
                >
                  <Wand2 className="w-3.5 h-3.5" />
                  <span>Grimorio ({spells.length})</span>
                </button>
                <button
                  onClick={() => setSheetModalTab("features")}
                  className={`py-2 px-3 text-xs font-semibold border-b-2 flex items-center gap-1.5 transition-colors whitespace-nowrap ${
                    sheetModalTab === "features"
                      ? "border-gold text-gold font-bold"
                      : "border-transparent text-muted hover:text-main"
                  }`}
                >
                  <Scroll className="w-3.5 h-3.5" />
                  <span>Rasgos y Pergaminos ({features.length})</span>
                </button>
              </div>

              {/* Contenido Dinámico de la Pestaña Activa de la Ficha */}
              <div className="flex-1 overflow-y-auto p-5 text-xs">
                {/* 1. ATRIBUTOS Y TIRADAS DE SALVACIÓN */}
                {sheetModalTab === "general" && (
                  <div className="space-y-5">
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 text-center">
                      {ABILITY_KEYS.map(({ key, short, full }) => {
                        const score = getAbilityScore(key);
                        const mod = getAbilityMod(score);
                        const save = getSaveData(key);

                        return (
                          <div
                            key={key}
                            className="p-3 rounded-xl bg-card border border-border-iron flex flex-col justify-between space-y-1 shadow-xs"
                          >
                            <span className="text-[10px] font-bold text-muted uppercase tracking-wider">
                              {short} • {full}
                            </span>
                            <div className="font-stat font-bold text-2xl text-gold">
                              {formatModifier(mod)}
                            </div>
                            <div className="text-[11px] font-stat text-muted">
                              Puntuación: <span className="font-bold text-main">{score}</span>
                            </div>
                            <div className="pt-1.5 border-t border-border-iron/60 flex items-center justify-center gap-1 text-[11px]">
                              <span
                                className={`w-1.5 h-1.5 rounded-full ${
                                  save.isProf ? "bg-gold" : "bg-muted/40"
                                }`}
                              />
                              <span className="text-muted">Salvación:</span>
                              <span className={`font-bold font-stat ${save.isProf ? "text-gold" : "text-main"}`}>
                                {save.bonusStr}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Sentidos, Idiomas y Rasgos Biográficos */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                      <div className="p-3.5 rounded-xl bg-card border border-border-iron space-y-2">
                        <h4 className="font-bold text-gold text-xs flex items-center gap-1.5">
                          <Eye className="w-3.5 h-3.5" />
                          <span>Sentidos e Idiomas</span>
                        </h4>
                        <div className="space-y-1 text-muted">
                          <p>
                            <span className="font-semibold text-main">Percepción Pasiva:</span>{" "}
                            {10 + getAbilityMod(getAbilityScore("wis")) + (charData?.skills?.perception?.proficient ? profBonus : 0)}
                          </p>
                          <p>
                            <span className="font-semibold text-main">Sentidos especiales:</span>{" "}
                            {charData.senses || "Visión normal"}
                          </p>
                          <p>
                            <span className="font-semibold text-main">Idiomas:</span>{" "}
                            {charData.languages || "Común"}
                          </p>
                        </div>
                      </div>

                      <div className="p-3.5 rounded-xl bg-card border border-border-iron space-y-2">
                        <h4 className="font-bold text-gold text-xs flex items-center gap-1.5">
                          <FileText className="w-3.5 h-3.5" />
                          <span>Personalidad y Trasfondo</span>
                        </h4>
                        <div className="space-y-1 text-muted text-[11px] leading-relaxed">
                          {charData.personality_traits && (
                            <p><span className="font-semibold text-main">Rasgos:</span> {charData.personality_traits}</p>
                          )}
                          {charData.ideals && (
                            <p><span className="font-semibold text-main">Ideales:</span> {charData.ideals}</p>
                          )}
                          {charData.bonds && (
                            <p><span className="font-semibold text-main">Vínculos:</span> {charData.bonds}</p>
                          )}
                          {charData.flaws && (
                            <p><span className="font-semibold text-main">Defectos:</span> {charData.flaws}</p>
                          )}
                          {!charData.personality_traits && !charData.ideals && !charData.bonds && (
                            <p className="italic text-muted">Sin detalles de personalidad registrados.</p>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* 2. HABILIDADES */}
                {sheetModalTab === "skills" && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                    {STANDARD_SKILLS.map((sk) => {
                      const data = getSkillData(sk.id, sk.ability);
                      return (
                        <div
                          key={sk.id}
                          className={`p-2.5 rounded-lg border flex items-center justify-between transition-colors ${
                            data.isProf
                              ? "bg-gold/10 border-gold/40 text-main"
                              : "bg-card border-border-iron text-muted"
                          }`}
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <span
                              className={`w-2 h-2 rounded-full shrink-0 ${
                                data.isExpert
                                  ? "bg-amber-400 ring-2 ring-amber-400/40"
                                  : data.isProf
                                  ? "bg-gold"
                                  : "border border-border-iron bg-transparent"
                              }`}
                              title={data.isExpert ? "Maestría (Doble Bono)" : data.isProf ? "Competente" : "No competente"}
                            />
                            <span className="font-medium truncate">{sk.name}</span>
                            <span className="text-[10px] text-muted uppercase">({sk.ability.toUpperCase()})</span>
                          </div>
                          <span className={`font-stat font-bold text-xs shrink-0 ${data.isProf ? "text-gold" : "text-main"}`}>
                            {data.bonusStr}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* 3. ARMAS Y ACCIONES DE COMBATE */}
                {sheetModalTab === "combat" && (
                  <div className="space-y-3">
                    {weaponActions.length === 0 ? (
                      <div className="p-8 text-center border border-dashed border-border-iron rounded-xl text-muted">
                        No hay armas ni acciones de combate registradas en la ficha.
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {weaponActions.map((w: any, idx: number) => (
                          <div
                            key={idx}
                            className="p-3 rounded-xl border border-border-iron bg-card space-y-1.5 shadow-2xs"
                          >
                            <div className="flex items-center justify-between">
                              <h4 className="font-bold text-sm text-gold">{w.name}</h4>
                              <span className="font-stat font-bold text-xs px-2 py-0.5 rounded bg-surface border border-border-iron text-main">
                                Bono: {w.hit_dc || "+0"}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 font-stat text-xs text-main">
                              <span className="text-muted">Daño:</span>
                              <span className="font-bold text-gold">{w.damage_dice || "1d8"}</span>
                              <span className="text-muted capitalize">({w.damage_type || "cortante"})</span>
                              {w.range_val && (
                                <span className="text-muted ml-auto">• Alcance: {w.range_val}</span>
                              )}
                            </div>
                            {w.notes && (
                              <p className="text-[11px] text-muted italic line-clamp-2">{w.notes}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* 4. GRIMORIO Y ESPACIOS DE CONJURO */}
                {sheetModalTab === "spells" && (
                  <div className="space-y-4">
                    {/* Espacios de Conjuro */}
                    {Object.keys(spellSlotsTotal).length > 0 && (
                      <div className="p-3 rounded-xl bg-card border border-border-iron space-y-2">
                        <h4 className="font-bold text-gold text-xs uppercase tracking-wider">
                          Espacios de Conjuro por Nivel
                        </h4>
                        <div className="flex flex-wrap gap-2 font-stat">
                          {Object.entries(spellSlotsTotal).map(([lvl, total]) => {
                            const used = spellSlotsUsed[lvl] || 0;
                            const totalNum = Number(total);
                            const remaining = Math.max(0, totalNum - used);

                            return (
                              <div
                                key={lvl}
                                className="px-2.5 py-1 rounded bg-surface border border-border-iron text-center text-xs"
                              >
                                <div className="text-[10px] text-muted uppercase">Nvl {lvl}</div>
                                <div className="font-bold text-main">
                                  <span className="text-gold">{remaining}</span> / {totalNum}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Lista de Conjuros */}
                    {spells.length === 0 ? (
                      <div className="p-8 text-center border border-dashed border-border-iron rounded-xl text-muted">
                        No hay conjuros ni trucos registrados en el grimorio de este personaje.
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {spells.map((s: any, idx: number) => (
                          <div
                            key={idx}
                            className="p-3 rounded-xl border border-border-iron bg-card space-y-1.5 shadow-2xs"
                          >
                            <div className="flex items-center justify-between">
                              <h4 className="font-bold text-sm text-gold">{s.name}</h4>
                              <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface border border-border-iron text-muted">
                                {s.level === 0 ? "Truco" : `Nivel ${s.level}`}
                              </span>
                            </div>
                            <div className="flex flex-wrap gap-x-3 text-[11px] text-muted">
                              {s.school && <span>Escuela: {s.school}</span>}
                              {s.cast_time && <span>Casteo: {s.cast_time}</span>}
                              {s.range_area && <span>Alcance: {s.range_area}</span>}
                            </div>
                            {(s.notes || s.description) && (
                              <p className="text-[11px] text-muted/90 line-clamp-3">
                                {s.notes || s.description}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* 5. RASGOS, TALENTOS Y PERGAMINOS / DOCUMENTOS */}
                {sheetModalTab === "features" && (
                  <div className="space-y-4">
                    {features.length === 0 && inventory.length === 0 ? (
                      <div className="p-8 text-center border border-dashed border-border-iron rounded-xl text-muted">
                        No hay rasgos ni objetos de inventario registrados.
                      </div>
                    ) : (
                      <>
                        {features.length > 0 && (
                          <div className="space-y-2">
                            <h4 className="font-bold text-gold text-xs uppercase tracking-wider">
                              Rasgos de Clase, Raza y Documentos ({features.length})
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              {features.map((f: any, idx: number) => {
                                const isScroll = f.source?.includes("Pergamino") || f.source?.includes("Documento") || f.source?.startsWith("📜");
                                return (
                                  <div
                                    key={idx}
                                    className={`p-3.5 rounded-xl border space-y-1.5 ${
                                      isScroll
                                        ? "bg-amber-950/20 border-amber-500/40 text-amber-200"
                                        : "bg-card border-border-iron text-main"
                                    }`}
                                  >
                                    <div className="flex items-center justify-between">
                                      <h5 className="font-bold text-sm text-gold flex items-center gap-1.5">
                                        {isScroll && <Scroll className="w-3.5 h-3.5 text-amber-400" />}
                                        <span>{f.name}</span>
                                      </h5>
                                      <span className="text-[10px] px-2 py-0.5 rounded bg-surface border border-border-iron text-muted">
                                        {f.source || "Rasgo"}
                                      </span>
                                    </div>
                                    <p className={`text-[11px] leading-relaxed whitespace-pre-wrap ${isScroll ? "font-serif text-main" : "text-muted"}`}>
                                      {f.description}
                                    </p>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}

                        {inventory.length > 0 && (
                          <div className="space-y-2 pt-2 border-t border-border-iron/50">
                            <h4 className="font-bold text-gold text-xs uppercase tracking-wider">
                              Inventario / Pertenencias ({inventory.length})
                            </h4>
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                              {inventory.map((inv: any, idx: number) => (
                                <div
                                  key={idx}
                                  className="p-2 rounded-lg bg-surface border border-border-iron flex items-center justify-between text-xs"
                                >
                                  <span className="truncate">{inv.name}</span>
                                  <span className="text-[10px] font-mono text-muted shrink-0 ml-1">
                                    x{inv.quantity || 1}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>

              {/* Pie del Modal con Botón de Cierre Explícito */}
              <div className="p-3 border-t border-border-iron bg-card/40 flex items-center justify-between">
                <span className="text-[11px] text-muted">
                  Presiona <kbd className="px-1.5 py-0.5 rounded bg-surface border border-border-iron font-mono text-[10px]">Esc</kbd> para cerrar
                </span>
                <button
                  onClick={() => setInspectedPlayer(null)}
                  className="px-4 py-1.5 rounded-lg bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-semibold text-main transition-colors"
                >
                  Cerrar Ficha
                </button>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};
