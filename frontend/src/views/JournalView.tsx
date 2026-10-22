import React, { useState, useEffect } from "react";
import { useCharacter } from "../context/CharacterContext";
import { useTranslation } from "../i18n";
import { api } from "../api/client";
import type { SessionLogData } from "../api/types";
import { Plus, Trash2, Save, BookOpen, Edit3 } from "lucide-react";
import { MarkdownViewer } from "../components/MarkdownViewer";

export const JournalView: React.FC = () => {
  const { activeCharacter, showToast } = useCharacter();
  const { t } = useTranslation();
  const [sessions, setSessions] = useState<SessionLogData[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [mode, setMode] = useState<"write" | "read">("write");

  // Estado del formulario
  const [title, setTitle] = useState<string>("");
  const [date, setDate] = useState<string>("");
  const [summary, setSummary] = useState<string>("");
  const [loot, setLoot] = useState<string>("");
  const [xpGained, setXpGained] = useState<number>(0);

  useEffect(() => {
    if (activeCharacter?.id) {
      loadJournals(activeCharacter.id);
    }
  }, [activeCharacter?.id]);

  const loadJournals = async (charId: number) => {
    try {
      const data = await api.getCharacterJournals(charId);
      setSessions(data || []);
      if (data && data.length > 0) {
        selectSession(data[data.length - 1]);
      } else {
        setSelectedId(null);
      }
    } catch (e) {
      console.error("Error loading journals:", e);
    }
  };

  const selectSession = (sess: SessionLogData) => {
    setSelectedId(sess.id);
    setTitle(sess.title);
    setDate(sess.date);
    setSummary(sess.summary);
    setLoot(sess.loot);
    setXpGained(sess.xp_gained);
  };

  const handleNewSession = () => {
    const newSess: SessionLogData = {
      id: Date.now(),
      date: new Date().toISOString().split("T")[0],
      title: t("journal.sessionDefaultTitle"),
      summary: "",
      loot: "",
      xp_gained: 0,
    };
    setSessions((prev) => [...prev, newSess]);
    selectSession(newSess);
  };

  const handleSave = async () => {
    if (!activeCharacter?.id || !selectedId) return;
    try {
      const payload: SessionLogData = {
        id: selectedId,
        date,
        title: title.trim() || t("journal.untitledSession"),
        summary,
        loot,
        xp_gained: xpGained,
      };
      await api.saveCharacterJournal(activeCharacter.id, payload);
      showToast(t("journal.savedSuccess"), "success");
      await loadJournals(activeCharacter.id);
    } catch (e) {
      showToast(t("journal.saveError"), "warn");
    }
  };

  const handleDelete = async () => {
    if (!activeCharacter?.id || !selectedId) return;
    if (window.confirm(t("journal.confirmDelete"))) {
      try {
        await api.deleteCharacterJournal(activeCharacter.id, selectedId);
        showToast(t("journal.deletedSuccess"), "info");
        await loadJournals(activeCharacter.id);
      } catch (e) {
        showToast(t("journal.deleteError"), "warn");
      }
    }
  };

  if (!activeCharacter) {
    return (
      <div className="h-full flex items-center justify-center p-8 text-center text-muted">
        <p className="font-display text-xl text-gold">{t("journal.noCharacter")}</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-4 md:p-6 space-y-4 max-w-7xl mx-auto overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border-iron pb-3 shrink-0">
        <div>
          <h1 className="font-display font-bold text-2xl text-gold">{t("journal.title")}</h1>
          <p className="text-xs text-muted">{t("journal.subtitle")}</p>
        </div>
        <button
          onClick={handleNewSession}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-crimson hover:bg-crimson-hover text-white text-xs font-semibold rounded transition-all shadow-sm active:scale-95"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>{t("journal.newSession")}</span>
        </button>
      </div>

      {/* Panel Dividido: Lista a la izquierda, Editor/Visor a la derecha */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4 min-h-0 overflow-hidden">
        {/* Lista de Crónicas */}
        <div className="bg-card border border-border-iron rounded-xl overflow-y-auto divide-y divide-border-iron/50">
          {sessions.length > 0 ? (
            sessions.map((sess) => (
              <div
                key={sess.id}
                onClick={() => selectSession(sess)}
                className={`p-3.5 cursor-pointer transition-colors ${
                  selectedId === sess.id ? "bg-surface border-l-2 border-gold" : "hover:bg-surface/50"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <h4 className="font-semibold text-xs text-main truncate max-w-[180px]">{sess.title}</h4>
                  <span className="font-stat text-[10px] text-gold">{sess.date}</span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-muted">
                  <span>+{sess.xp_gained} XP</span>
                  {sess.loot && <span className="truncate max-w-[120px] text-main/80 font-stat">💎 {sess.loot}</span>}
                </div>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-xs text-muted">
              {t("journal.noSessions")}
            </div>
          )}
        </div>

        {/* Panel de Detalle y Edición */}
        <div className="md:col-span-2 bg-card border border-border-iron rounded-xl p-5 flex flex-col justify-between overflow-y-auto space-y-4">
          {selectedId ? (
            <>
              {/* Controles de Cabecera */}
              <div className="space-y-3 shrink-0">
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-2">
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder={t("journal.sessionTitle")}
                    className="sm:col-span-2 bg-input text-main border border-border-iron rounded px-3 py-1.5 text-sm font-semibold focus:border-gold outline-none"
                  />
                  <input
                    type="date"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    className="bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none"
                  />
                  <input
                    type="number"
                    value={xpGained}
                    onChange={(e) => setXpGained(parseInt(e.target.value, 10) || 0)}
                    placeholder={t("journal.xpTitle")}
                    className="bg-input text-main border border-border-iron rounded px-2.5 py-1.5 text-xs font-stat focus:border-gold outline-none"
                  />
                </div>

                <div>
                  <input
                    type="text"
                    value={loot}
                    onChange={(e) => setLoot(e.target.value)}
                    placeholder={t("journal.lootPlaceholder")}
                    className="w-full bg-input text-main border border-border-iron rounded px-3 py-1.5 text-xs focus:border-gold outline-none font-stat"
                  />
                </div>

                {/* Barra de Modo (Redactar vs Lectura) */}
                <div className="flex items-center justify-between border-y border-border-iron/60 py-2">
                  <div className="flex gap-1.5">
                    <button
                      onClick={() => setMode("write")}
                      className={`px-3 py-1 rounded text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                        mode === "write" ? "bg-gold text-canvas" : "bg-surface text-muted hover:text-main"
                      }`}
                    >
                      <Edit3 className="w-3 h-3" />
                      <span>{t("journal.writeTab")}</span>
                    </button>
                    <button
                      onClick={() => setMode("read")}
                      className={`px-3 py-1 rounded text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                        mode === "read" ? "bg-gold text-canvas" : "bg-surface text-muted hover:text-main"
                      }`}
                    >
                      <BookOpen className="w-3 h-3" />
                      <span>{t("journal.readTab")}</span>
                    </button>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={handleDelete}
                      title={t("journal.deleteChronicle")}
                      className="p-1.5 rounded text-crimson hover:bg-crimson/10 border border-transparent hover:border-crimson/30 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={handleSave}
                      className="flex items-center gap-1.5 px-4 py-1.5 bg-crimson hover:bg-crimson-hover text-white text-xs font-bold rounded transition-all shadow-sm active:scale-95"
                    >
                      <Save className="w-3.5 h-3.5" />
                      <span>{t("common.save")}</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Área de Contenido */}
              <div className="flex-1 min-h-[220px]">
                {mode === "write" ? (
                  <textarea
                    value={summary}
                    onChange={(e) => setSummary(e.target.value)}
                    placeholder={t("journal.summaryPlaceholder")}
                    className="w-full h-full min-h-[220px] bg-input text-main border border-border-iron rounded-lg p-3 text-xs leading-relaxed focus:border-gold outline-none resize-none font-body"
                  />
                ) : (
                  <div className="w-full h-full min-h-[220px] bg-surface/50 border border-border-iron rounded-lg p-4 overflow-y-auto">
                    <MarkdownViewer
                      content={summary || `*${t("journal.noSessions")}*`}
                    />
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-muted">
              {t("journal.noSessions")}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
