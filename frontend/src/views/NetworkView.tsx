import React, { useState, useEffect } from "react";
import { useCharacter } from "../context/CharacterContext";
import { useTranslation } from "../i18n";
import { api } from "../api/client";
import type { NetworkNodeData, NetworkEdgeData } from "../api/types";
import { Link2, Trash2, UserPlus, X } from "lucide-react";

export const NetworkView: React.FC = () => {
  const { activeCharacter, showToast, characters } = useCharacter();
  const { t } = useTranslation();
  const [nodes, setNodes] = useState<NetworkNodeData[]>([]);
  const [edges, setEdges] = useState<NetworkEdgeData[]>([]);

  // Modales
  const [isNodeModalOpen, setIsNodeModalOpen] = useState<boolean>(false);
  const [isEdgeModalOpen, setIsEdgeModalOpen] = useState<boolean>(false);
  const [selectedNode, setSelectedNode] = useState<NetworkNodeData | null>(null);

  // Formulario de Nodo
  const [nodeName, setNodeName] = useState<string>("");
  const [nodeRole, setNodeRole] = useState<string>("Aliado");
  const [nodeDesc, setNodeDesc] = useState<string>("");

  // Formulario de Vínculo
  const [edgeSource, setEdgeSource] = useState<string>("");
  const [edgeTarget, setEdgeTarget] = useState<string>("");
  const [edgeRelation, setEdgeRelation] = useState<string>("Aliado");

  useEffect(() => {
    if (activeCharacter?.id) {
      loadNetwork(activeCharacter.id);
    }
  }, [activeCharacter?.id]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsNodeModalOpen(false);
        setIsEdgeModalOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const loadNetwork = async (charId: number) => {
    try {
      const net = await api.getCharacterNetwork(charId);
      setNodes(net.nodes || []);
      setEdges(net.edges || []);
      if (net.nodes && net.nodes.length >= 2) {
        setEdgeSource(net.nodes[0].id);
        setEdgeTarget(net.nodes[1].id);
      }
    } catch (e) {
      console.error("Error loading network:", e);
    }
  };

  const handleCreateNode = async () => {
    if (!activeCharacter?.id || !nodeName.trim()) return;
    try {
      const newNode: NetworkNodeData = {
        id: `node_${Date.now()}`,
        name: nodeName.trim(),
        role: nodeRole,
        description: nodeDesc,
        x: 100,
        y: 100,
      };
      const res = await api.saveNetworkNode(activeCharacter.id, newNode);
      if (res?.network?.nodes) {
        setNodes(res.network.nodes);
        setEdges(res.network.edges || []);
      } else {
        await loadNetwork(activeCharacter.id);
      }
      showToast(t("network.contactSaved", { name: newNode.name }), "success");
      setIsNodeModalOpen(false);
      setNodeName("");
      setNodeDesc("");
    } catch (e) {
      showToast(t("network.saveContact"), "warn");
    }
  };

  const handleImportCharacter = async (charSummary: any) => {
    if (!activeCharacter?.id) return;
    const newNode: NetworkNodeData = {
      id: `char_node_${charSummary.id}`,
      name: charSummary.name,
      role: "Compañero",
      description: `${t("common.level")} ${charSummary.level} ${charSummary.char_class} (${charSummary.race || t("common.name")})`,
      x: 120,
      y: 120,
    };
    try {
      const res = await api.saveNetworkNode(activeCharacter.id, newNode);
      if (res?.network?.nodes) {
        setNodes(res.network.nodes);
        setEdges(res.network.edges || []);
      } else {
        await loadNetwork(activeCharacter.id);
      }
      showToast(t("network.contactSaved", { name: charSummary.name }), "success");
    } catch (e) {
      showToast(t("common.error"), "warn");
    }
  };

  const handleDeleteNode = async (nodeId: string) => {
    if (!activeCharacter?.id) return;
    if (window.confirm(t("network.confirmDeleteContact"))) {
      try {
        await api.deleteNetworkNode(activeCharacter.id, nodeId);
        setSelectedNode(null);
        showToast(t("network.deleteContact"), "info");
        await loadNetwork(activeCharacter.id);
      } catch (e) {
        showToast(t("common.error"), "warn");
      }
    }
  };

  const handleCreateEdge = async () => {
    if (!activeCharacter?.id) return;
    if (edgeSource === edgeTarget) {
      return;
    }
    try {
      await api.saveNetworkEdge(activeCharacter.id, {
        source_id: edgeSource,
        target_id: edgeTarget,
        relation: edgeRelation,
      });
      showToast(t("network.linkSaved"), "success");
      setIsEdgeModalOpen(false);
      await loadNetwork(activeCharacter.id);
    } catch (e) {
      showToast(t("common.error"), "warn");
    }
  };

  const handleDeleteEdge = async (src: string, tgt: string) => {
    if (!activeCharacter?.id) return;
    try {
      await api.deleteNetworkEdge(activeCharacter.id, { source_id: src, target_id: tgt });
      showToast(t("network.linkSaved"), "info");
      await loadNetwork(activeCharacter.id);
    } catch (e) {
      showToast(t("common.error"), "warn");
    }
  };

  const roleColors: Record<string, string> = {
    Aliado: "text-emerald-400 border-emerald-500/40 bg-emerald-950/20",
    Ally: "text-emerald-400 border-emerald-500/40 bg-emerald-950/20",
    Amigo: "text-emerald-300 border-emerald-500/30 bg-emerald-950/10",
    Friend: "text-emerald-300 border-emerald-500/30 bg-emerald-950/10",
    Enemigo: "text-crimson border-crimson/50 bg-crimson/10",
    Enemy: "text-crimson border-crimson/50 bg-crimson/10",
    Rival: "text-amber-400 border-amber-500/40 bg-amber-950/20",
    Mentor: "text-gold border-gold/40 bg-gold/10",
    Deuda: "text-purple-400 border-purple-500/40 bg-purple-950/20",
    Debt: "text-purple-400 border-purple-500/40 bg-purple-950/20",
    Pacto: "text-indigo-400 border-indigo-500/40 bg-indigo-950/20",
    Pact: "text-indigo-400 border-indigo-500/40 bg-indigo-950/20",
    Familiar: "text-sky-300 border-sky-500/30 bg-sky-950/10",
    Family: "text-sky-300 border-sky-500/30 bg-sky-950/10",
    Neutral: "text-muted border-border-iron bg-surface",
    Compañero: "text-cyan-300 border-cyan-500/30 bg-cyan-950/10",
    Companion: "text-cyan-300 border-cyan-500/30 bg-cyan-950/10",
  };

  if (!activeCharacter) {
    return (
      <div className="h-full flex items-center justify-center p-8 text-center text-muted">
        <p className="font-display text-xl text-gold">{t("network.noCharacter")}</p>
      </div>
    );
  }

  const nodeMap = new Map(nodes.map((n) => [n.id, n.name]));

  return (
    <div className="h-full flex flex-col p-4 md:p-6 space-y-5 max-w-7xl mx-auto overflow-hidden">
      {/* 1. Header de la Red */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-iron pb-4 shrink-0">
        <div>
          <h1 className="font-display font-bold text-2xl text-gold">{t("network.title")}</h1>
          <p className="text-xs text-muted">{t("network.subtitle")}</p>
        </div>

        <div className="flex items-center gap-2">
          {characters.filter((c) => c.id !== activeCharacter.id).length > 0 && (
            <select
              onChange={(e) => {
                const target = characters.find((c) => String(c.id) === e.target.value);
                if (target) {
                  handleImportCharacter(target);
                  e.target.value = "";
                }
              }}
              defaultValue=""
              className="bg-surface text-main border border-border-iron hover:border-gold rounded px-2.5 py-1.5 text-xs focus:border-gold outline-none transition-colors"
            >
              <option value="" disabled>
                {t("network.importPartyMember")}
              </option>
              {characters
                .filter((c) => c.id !== activeCharacter.id)
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.char_class} {c.level})
                  </option>
                ))}
            </select>
          )}

          <button
            onClick={() => setIsNodeModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-semibold rounded text-main transition-colors"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>{t("network.addContact")}</span>
          </button>
          <button
            onClick={() => setIsEdgeModalOpen(true)}
            disabled={nodes.length < 2}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-crimson hover:bg-crimson-hover disabled:opacity-40 text-white text-xs font-bold rounded transition-all shadow-sm active:scale-95"
          >
            <Link2 className="w-3.5 h-3.5" />
            <span>{t("network.addLink")}</span>
          </button>
        </div>
      </div>

      {/* 2. Área Principal Dividida: Nodos & Vínculos */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-5 min-h-0 overflow-hidden">
        {/* Columna Izquierda: Tarjetas de Contactos */}
        <div className="md:col-span-2 bg-card border border-border-iron rounded-xl p-4 overflow-y-auto space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-border-iron/60">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              {t("network.contactsList")} ({nodes.length})
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {nodes.length > 0 ? (
              nodes.map((n) => {
                const colorCls = roleColors[n.role] || roleColors.Neutral;
                return (
                  <div
                    key={n.id}
                    onClick={() => setSelectedNode(n)}
                    className="p-3.5 rounded-lg border border-border-iron bg-surface/60 hover:border-gold/60 cursor-pointer transition-all space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold text-sm text-main">{n.name}</h4>
                      <span className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded border ${colorCls}`}>
                        {n.role}
                      </span>
                    </div>
                    {n.description && (
                      <p className="text-xs text-muted leading-relaxed line-clamp-2">{n.description}</p>
                    )}
                  </div>
                );
              })
            ) : (
              <div className="col-span-2 text-center py-12 text-xs text-muted">
                {t("network.noContacts")}
              </div>
            )}
          </div>
        </div>

        {/* Columna Derecha: Panel de Vínculos y Detalle */}
        <div className="bg-card border border-border-iron rounded-xl p-4 flex flex-col justify-between overflow-y-auto space-y-4">
          <div className="space-y-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted pb-2 border-b border-border-iron/60">
              {t("network.title")} ({edges.length})
            </h3>

            {/* Listado de Enlaces Existentes */}
            <div className="space-y-2">
              {edges.length > 0 ? (
                edges.map((e, idx) => {
                  const sName = nodeMap.get(e.source_id) || e.source_id;
                  const tName = nodeMap.get(e.target_id) || e.target_id;
                  return (
                    <div
                      key={idx}
                      className="p-2.5 rounded bg-surface border border-border-iron text-xs flex items-center justify-between"
                    >
                      <div>
                        <div className="font-semibold text-main">
                          {sName} ↔ {tName}
                        </div>
                        <div className="text-[10px] text-gold">{e.relation}</div>
                      </div>
                      <button
                        onClick={() => handleDeleteEdge(e.source_id, e.target_id)}
                        className="p-1 rounded text-muted hover:text-crimson"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  );
                })
              ) : (
                <div className="text-center py-4 text-xs text-muted">
                  {t("network.noContacts")}
                </div>
              )}
            </div>

            {/* Detalle del Nodo Seleccionado */}
            {selectedNode && (
              <div className="p-3.5 rounded-lg border border-gold/40 bg-surface space-y-2 mt-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-sm text-gold">{selectedNode.name}</h4>
                  <button
                    onClick={() => handleDeleteNode(selectedNode.id)}
                    className="p-1 rounded text-crimson hover:bg-crimson/10"
                    title={t("network.deleteContact")}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="text-xs text-muted">
                  <strong>{t("network.contactRole")}:</strong> {selectedNode.role}
                </div>
                {selectedNode.description && (
                  <p className="text-xs text-main/90 leading-relaxed pt-1">
                    {selectedNode.description}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal: Crear Contacto */}
      {isNodeModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-xs">
          <div className="w-full max-w-sm bg-card border border-border-iron rounded-xl p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border-iron pb-2">
              <h3 className="font-display font-bold text-base text-gold">{t("network.addContact")}</h3>
              <button onClick={() => setIsNodeModalOpen(false)}>
                <X className="w-4 h-4 text-muted" />
              </button>
            </div>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-muted mb-1">{t("network.contactName")}</label>
                <input
                  type="text"
                  value={nodeName}
                  onChange={(e) => setNodeName(e.target.value)}
                  className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 outline-none focus:border-gold"
                />
              </div>
              <div>
                <label className="block text-muted mb-1">{t("network.contactRole")}</label>
                <select
                  value={nodeRole}
                  onChange={(e) => setNodeRole(e.target.value)}
                  className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 outline-none focus:border-gold"
                >
                  <option value="Aliado">{t("network.roleAlly")}</option>
                  <option value="Enemigo">{t("network.roleEnemy")}</option>
                  <option value="Neutral">{t("network.roleNeutral")}</option>
                  <option value="Compañero">{t("network.roleCompanion")}</option>
                  <option value="Mentor">{t("network.roleMentor")}</option>
                  <option value="Patrón">{t("network.rolePatron")}</option>
                  <option value="Organización">{t("network.roleOrganization")}</option>
                </select>
              </div>
              <div>
                <label className="block text-muted mb-1">{t("network.contactDesc")}</label>
                <textarea
                  value={nodeDesc}
                  onChange={(e) => setNodeDesc(e.target.value)}
                  rows={2}
                  className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 outline-none focus:border-gold resize-none"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={() => setIsNodeModalOpen(false)}
                  className="px-3 py-1.5 rounded border border-border-iron text-muted"
                >
                  {t("common.cancel")}
                </button>
                <button
                  onClick={handleCreateNode}
                  className="px-4 py-1.5 rounded bg-crimson text-white font-semibold"
                >
                  {t("network.saveContact")}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Crear Enlace */}
      {isEdgeModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-xs">
          <div className="w-full max-w-sm bg-card border border-border-iron rounded-xl p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border-iron pb-2">
              <h3 className="font-display font-bold text-base text-gold">{t("network.addLink")}</h3>
              <button onClick={() => setIsEdgeModalOpen(false)}>
                <X className="w-4 h-4 text-muted" />
              </button>
            </div>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-muted mb-1">{t("network.linkSource")}</label>
                <select
                  value={edgeSource}
                  onChange={(e) => setEdgeSource(e.target.value)}
                  className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 outline-none focus:border-gold"
                >
                  {nodes.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-muted mb-1">{t("network.linkTarget")}</label>
                <select
                  value={edgeTarget}
                  onChange={(e) => setEdgeTarget(e.target.value)}
                  className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 outline-none focus:border-gold"
                >
                  {nodes.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-muted mb-1">{t("network.linkRelation")}</label>
                <input
                  type="text"
                  value={edgeRelation}
                  onChange={(e) => setEdgeRelation(e.target.value)}
                  placeholder="Aliado / Rival / Deuda..."
                  className="w-full bg-input text-main border border-border-iron rounded px-2.5 py-1.5 outline-none focus:border-gold"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={() => setIsEdgeModalOpen(false)}
                  className="px-3 py-1.5 rounded border border-border-iron text-muted"
                >
                  {t("common.cancel")}
                </button>
                <button
                  onClick={handleCreateEdge}
                  className="px-4 py-1.5 rounded bg-crimson text-white font-semibold"
                >
                  {t("network.saveLink")}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
