import React, { useState, useEffect } from "react";
import { useCharacter } from "../context/CharacterContext";
import { api } from "../api/client";
import type { NetworkNodeData, NetworkEdgeData } from "../api/types";
import { Link2, Trash2, UserPlus, Users } from "lucide-react";

export const NetworkView: React.FC = () => {
  const { activeCharacter, showToast } = useCharacter();
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
      await api.saveNetworkNode(activeCharacter.id, newNode);
      showToast(`Contacto "${newNode.name}" registrado en la red`, "success");
      setIsNodeModalOpen(false);
      setNodeName("");
      setNodeDesc("");
      await loadNetwork(activeCharacter.id);
    } catch (e) {
      showToast("Error al registrar contacto", "warn");
    }
  };

  const handleDeleteNode = async (nodeId: string) => {
    if (!activeCharacter?.id) return;
    if (window.confirm("¿Eliminar este personaje y sus vínculos?")) {
      try {
        await api.deleteNetworkNode(activeCharacter.id, nodeId);
        setSelectedNode(null);
        showToast("Contacto eliminado de la red", "info");
        await loadNetwork(activeCharacter.id);
      } catch (e) {
        showToast("Error al eliminar", "warn");
      }
    }
  };

  const handleCreateEdge = async () => {
    if (!activeCharacter?.id) return;
    if (edgeSource === edgeTarget) {
      showToast("No puedes vincular un personaje consigo mismo", "warn");
      return;
    }
    try {
      await api.saveNetworkEdge(activeCharacter.id, {
        source_id: edgeSource,
        target_id: edgeTarget,
        relation: edgeRelation,
      });
      showToast("Vínculo relacional trazado exitosamente", "success");
      setIsEdgeModalOpen(false);
      await loadNetwork(activeCharacter.id);
    } catch (e) {
      showToast("Error al crear vínculo", "warn");
    }
  };

  const handleDeleteEdge = async (src: string, tgt: string) => {
    if (!activeCharacter?.id) return;
    try {
      await api.deleteNetworkEdge(activeCharacter.id, { source_id: src, target_id: tgt });
      showToast("Vínculo eliminado", "info");
      await loadNetwork(activeCharacter.id);
    } catch (e) {
      showToast("Error al eliminar vínculo", "warn");
    }
  };

  const roleColors: Record<string, string> = {
    Aliado: "text-emerald-400 border-emerald-500/40 bg-emerald-950/20",
    Amigo: "text-emerald-300 border-emerald-500/30 bg-emerald-950/10",
    Enemigo: "text-crimson border-crimson/50 bg-crimson/10",
    Rival: "text-amber-400 border-amber-500/40 bg-amber-950/20",
    Mentor: "text-gold border-gold/40 bg-gold/10",
    Deuda: "text-purple-400 border-purple-500/40 bg-purple-950/20",
    Pacto: "text-indigo-400 border-indigo-500/40 bg-indigo-950/20",
    Familiar: "text-sky-300 border-sky-500/30 bg-sky-950/10",
    Neutral: "text-muted border-border-iron bg-surface",
  };

  if (!activeCharacter) {
    return (
      <div className="h-full flex items-center justify-center p-8 text-center text-muted">
        <p className="font-display text-xl text-gold">Selecciona un personaje para consultar su red de campaña.</p>
      </div>
    );
  }

  const nodeMap = new Map(nodes.map((n) => [n.id, n.name]));

  return (
    <div className="h-full flex flex-col p-4 md:p-6 space-y-5 max-w-7xl mx-auto overflow-hidden">
      {/* 1. Header de la Red */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-iron pb-4 shrink-0">
        <div>
          <h1 className="font-display font-bold text-2xl text-gold">Red de Contactos & Vínculos de Campaña</h1>
          <p className="text-xs text-muted">Mapeo de alianzas, rivalidades, deudas y pactos de {activeCharacter.name}.</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsNodeModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-surface hover:bg-card border border-border-iron hover:border-gold text-xs font-semibold rounded text-main transition-colors"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Añadir PNJ / Contacto</span>
          </button>
          <button
            onClick={() => setIsEdgeModalOpen(true)}
            disabled={nodes.length < 2}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-crimson hover:bg-crimson-hover disabled:opacity-40 text-white text-xs font-bold rounded transition-all shadow-sm active:scale-95"
          >
            <Link2 className="w-3.5 h-3.5" />
            <span>Trazar Vínculo</span>
          </button>
        </div>
      </div>

      {/* 2. Área Principal Dividida: Nodos & Vínculos */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-5 min-h-0 overflow-hidden">
        {/* Columna Izquierda: Tarjetas de Contactos */}
        <div className="md:col-span-2 bg-card border border-border-iron rounded-xl p-4 overflow-y-auto space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-border-iron/60">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5 text-gold" />
              <span>Personajes y Facciones ({nodes.length})</span>
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
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase border ${colorCls}`}>
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
              <div className="col-span-2 p-8 text-center text-xs text-muted">
                No hay contactos registrados aún. Pulsa "+ Añadir PNJ / Contacto" para comenzar.
              </div>
            )}
          </div>
        </div>

        {/* Columna Derecha: Vínculos Relacionales & Detalle del Seleccionado */}
        <div className="bg-card border border-border-iron rounded-xl p-4 flex flex-col justify-between overflow-y-auto space-y-4">
          {/* Detalle del Nodo Seleccionado */}
          {selectedNode ? (
            <div className="p-3.5 rounded-lg border border-gold/40 bg-surface/80 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-sm text-gold">{selectedNode.name}</h4>
                  <span className="text-[10px] uppercase font-semibold text-muted">{selectedNode.role}</span>
                </div>
                <button
                  onClick={() => handleDeleteNode(selectedNode.id)}
                  className="p-1 text-crimson hover:bg-crimson/10 rounded transition-colors"
                  title="Eliminar de la red"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <p className="text-xs text-main/90 leading-relaxed bg-input p-2 rounded border border-border-iron/40 whitespace-pre-wrap font-body">
                {selectedNode.description || "Sin descripción registrada."}
              </p>
            </div>
          ) : (
            <div className="p-3 rounded bg-surface/30 border border-border-iron/50 text-xs text-muted text-center">
              Haz clic en cualquier personaje de la izquierda para ver sus notas y secretos de campaña.
            </div>
          )}

          {/* Lista de Vínculos Trazados */}
          <div className="space-y-2 flex-1 overflow-y-auto">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted pb-1 border-b border-border-iron/60">
              Vínculos Activos ({edges.length})
            </h3>
            <div className="space-y-1.5">
              {edges.length > 0 ? (
                edges.map((e, idx) => {
                  const sName = nodeMap.get(e.source_id) || "Desconocido";
                  const tName = nodeMap.get(e.target_id) || "Desconocido";
                  return (
                    <div
                      key={idx}
                      className="p-2.5 rounded bg-surface border border-border-iron flex items-center justify-between text-xs"
                    >
                      <div className="space-y-0.5">
                        <div className="font-semibold text-main">
                          {sName} <span className="text-gold font-stat">⇄</span> {tName}
                        </div>
                        <span className="text-[10px] text-muted font-stat uppercase">{e.relation}</span>
                      </div>
                      <button
                        onClick={() => handleDeleteEdge(e.source_id, e.target_id)}
                        className="p-1 text-muted hover:text-crimson transition-colors"
                        title="Eliminar vínculo"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  );
                })
              ) : (
                <div className="text-xs text-muted text-center py-4">No hay conexiones trazadas aún.</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Modal: Añadir PNJ */}
      {isNodeModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-xs" onClick={() => setIsNodeModalOpen(false)} />
          <div className="relative bg-surface border border-border-iron rounded-xl p-5 max-w-md w-full space-y-4 z-10 select-none shadow-2xl">
            <h3 className="font-display font-bold text-lg text-gold">Añadir Personaje o Facción</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold uppercase text-muted mb-1">Nombre</label>
                <input
                  type="text"
                  value={nodeName}
                  onChange={(e) => setNodeName(e.target.value)}
                  placeholder="Ej: Reina Sylviara, Gremio de Ladrones..."
                  className="w-full bg-input text-main border border-border-iron rounded px-3 py-1.5 text-sm focus:border-gold outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted mb-1">Rol / Vínculo Primario</label>
                <select
                  value={nodeRole}
                  onChange={(e) => setNodeRole(e.target.value)}
                  className="w-full bg-input text-main border border-border-iron rounded px-3 py-1.5 text-xs focus:border-gold outline-none"
                >
                  {["Aliado", "Amigo", "Enemigo", "Rival", "Mentor", "Deuda", "Pacto", "Familiar", "Neutral"].map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted mb-1">Notas y Secretos</label>
                <textarea
                  value={nodeDesc}
                  onChange={(e) => setNodeDesc(e.target.value)}
                  placeholder="Detalles de lealtad, rumores o secretos..."
                  className="w-full h-24 bg-input text-main border border-border-iron rounded p-2 text-xs focus:border-gold outline-none resize-none font-body"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t border-border-iron">
              <button
                onClick={() => setIsNodeModalOpen(false)}
                className="px-4 py-1.5 rounded border border-border-iron text-xs text-muted hover:text-main"
              >
                Cancelar
              </button>
              <button
                onClick={handleCreateNode}
                className="px-5 py-1.5 rounded bg-crimson hover:bg-crimson-hover text-white text-xs font-bold transition-all shadow-sm active:scale-95"
              >
                Guardar Contacto
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Trazar Vínculo */}
      {isEdgeModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-xs" onClick={() => setIsEdgeModalOpen(false)} />
          <div className="relative bg-surface border border-border-iron rounded-xl p-5 max-w-md w-full space-y-4 z-10 select-none shadow-2xl">
            <h3 className="font-display font-bold text-lg text-gold">Trazar Vínculo Relacional</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold uppercase text-muted mb-1">Personaje Origen</label>
                <select
                  value={edgeSource}
                  onChange={(e) => setEdgeSource(e.target.value)}
                  className="w-full bg-input text-main border border-border-iron rounded px-3 py-1.5 text-xs focus:border-gold outline-none"
                >
                  {nodes.map((n) => (
                    <option key={n.id} value={n.id}>{n.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted mb-1">Personaje Destino</label>
                <select
                  value={edgeTarget}
                  onChange={(e) => setEdgeTarget(e.target.value)}
                  className="w-full bg-input text-main border border-border-iron rounded px-3 py-1.5 text-xs focus:border-gold outline-none"
                >
                  {nodes.map((n) => (
                    <option key={n.id} value={n.id}>{n.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted mb-1">Tipo de Vínculo</label>
                <select
                  value={edgeRelation}
                  onChange={(e) => setEdgeRelation(e.target.value)}
                  className="w-full bg-input text-main border border-border-iron rounded px-3 py-1.5 text-xs focus:border-gold outline-none"
                >
                  {["Aliado", "Amigo", "Enemigo", "Rival", "Mentor", "Deuda", "Pacto", "Familiar", "Neutral"].map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t border-border-iron">
              <button
                onClick={() => setIsEdgeModalOpen(false)}
                className="px-4 py-1.5 rounded border border-border-iron text-xs text-muted hover:text-main"
              >
                Cancelar
              </button>
              <button
                onClick={handleCreateEdge}
                className="px-5 py-1.5 rounded bg-crimson hover:bg-crimson-hover text-white text-xs font-bold transition-all shadow-sm active:scale-95"
              >
                Crear Vínculo
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
