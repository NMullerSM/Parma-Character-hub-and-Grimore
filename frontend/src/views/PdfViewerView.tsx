import React, { useState, useEffect } from "react";
import { api } from "../api/client";
import type { PdfDocumentSummary, PdfDocumentInfo, PdfTocItem } from "../api/types";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Maximize2, Minimize2, FolderOpen, List } from "lucide-react";

export const PdfViewerView: React.FC = () => {
  const [docList, setDocList] = useState<PdfDocumentSummary[]>([]);
  const [selectedPath, setSelectedPath] = useState<string>("");
  const [docInfo, setDocInfo] = useState<PdfDocumentInfo | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [zoom, setZoom] = useState<number>(1.0);
  const [pageBase64, setPageBase64] = useState<string>("");
  const [showToc, setShowToc] = useState<boolean>(true);
  const [isZen, setIsZen] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    async function init() {
      try {
        const docs = await api.listPdfDocuments();
        setDocList(docs);
        if (docs.length > 0) {
          loadDocument(docs[0].path);
        }
      } catch (e) {
        console.error("Error listing PDFs:", e);
      }
    }
    init();
  }, []);

  const loadDocument = async (filePath: string) => {
    setSelectedPath(filePath);
    setLoading(true);
    try {
      const info = await api.openPdfDocument(filePath);
      if (info.success) {
        setDocInfo(info);
        setCurrentPage(1);
        await renderPage(1, zoom);
      }
    } catch (e) {
      console.error("Error opening PDF:", e);
    } finally {
      setLoading(false);
    }
  };

  const renderPage = async (page: number, zoomLevel: number) => {
    setLoading(true);
    try {
      const res = await api.renderPdfPage(page, zoomLevel);
      if (res.success && res.image_base64) {
        setPageBase64(res.image_base64);
      }
    } catch (e) {
      console.error("Error rendering page:", e);
    } finally {
      setLoading(false);
    }
  };

  const gotoPage = async (p: number) => {
    if (!docInfo) return;
    const target = Math.max(1, Math.min(docInfo.page_count, p));
    setCurrentPage(target);
    await renderPage(target, zoom);
  };

  const handleZoom = async (delta: number) => {
    const nextZoom = Math.max(0.5, Math.min(2.5, Math.round((zoom + delta) * 10) / 10));
    setZoom(nextZoom);
    await renderPage(currentPage, nextZoom);
  };

  return (
    <div
      className={`h-full flex flex-col p-3 md:p-5 space-y-3 mx-auto overflow-hidden ${
        isZen ? "fixed inset-0 z-50 bg-canvas p-4" : "max-w-7xl"
      }`}
    >
      {/* 1. Barra de Herramientas del Lector */}
      <div className="bg-card border border-border-iron rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 shrink-0 select-none shadow-xs">
        {/* Selector de Documento y Toggle de Índice */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowToc(!showToc)}
            title="Alternar Índice Digital"
            className={`p-1.5 rounded border transition-colors ${
              showToc ? "border-gold bg-gold/10 text-gold" : "border-border-iron text-muted hover:text-main"
            }`}
          >
            <List className="w-4 h-4" />
          </button>

          <select
            value={selectedPath}
            onChange={(e) => loadDocument(e.target.value)}
            className="bg-surface text-main border border-border-iron rounded px-2.5 py-1 text-xs focus:border-gold outline-none max-w-[220px] md:max-w-xs truncate"
          >
            {docList.map((d) => (
              <option key={d.path} value={d.path}>
                📄 {d.name}
              </option>
            ))}
          </select>
        </div>

        {/* Controles de Navegación de Página */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => gotoPage(currentPage - 1)}
            disabled={currentPage <= 1}
            className="p-1 rounded border border-border-iron hover:border-gold disabled:opacity-30 text-main"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-1 text-xs font-stat">
            <input
              type="number"
              min={1}
              max={docInfo?.page_count || 1}
              value={currentPage}
              onChange={(e) => gotoPage(parseInt(e.target.value, 10) || 1)}
              className="w-12 bg-input border border-border-iron rounded px-1.5 py-0.5 text-center font-bold text-main focus:border-gold outline-none"
            />
            <span className="text-muted">/ {docInfo?.page_count || 1}</span>
          </div>
          <button
            onClick={() => gotoPage(currentPage + 1)}
            disabled={!docInfo || currentPage >= docInfo.page_count}
            className="p-1 rounded border border-border-iron hover:border-gold disabled:opacity-30 text-main"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Controles de Zoom y Pantalla Completa */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleZoom(-0.2)}
            title="Reducir Zoom"
            className="p-1.5 rounded border border-border-iron hover:border-gold text-muted hover:text-main"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-xs font-stat text-muted min-w-[45px] text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={() => handleZoom(0.2)}
            title="Aumentar Zoom"
            className="p-1.5 rounded border border-border-iron hover:border-gold text-muted hover:text-main"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsZen(!isZen)}
            title={isZen ? "Salir de Pantalla Completa" : "Pantalla Completa Zen"}
            className="p-1.5 rounded border border-border-iron hover:border-gold text-muted hover:text-main ml-1"
          >
            {isZen ? <Minimize2 className="w-4 h-4 text-crimson" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* 2. Área de Lectura y Panel de Índice */}
      <div className="flex-1 flex gap-3 min-h-0 overflow-hidden">
        {/* Panel Lateral de Índice (TOC) */}
        {showToc && docInfo?.toc && docInfo.toc.length > 0 && (
          <aside className="w-64 bg-card border border-border-iron rounded-xl p-3 overflow-y-auto space-y-1 shrink-0 select-none">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted mb-2 pb-1 border-b border-border-iron/60">
              Índice Digital ({docInfo.toc.length})
            </h3>
            <div className="space-y-0.5">
              {docInfo.toc.map((item: PdfTocItem, idx: number) => {
                const indent = Math.max(0, (item.level - 1) * 12);
                const isActive = item.page === currentPage;
                return (
                  <button
                    key={idx}
                    onClick={() => gotoPage(item.page)}
                    style={{ paddingLeft: `${indent + 8}px` }}
                    className={`w-full text-left py-1 pr-2 rounded text-xs truncate flex items-center justify-between transition-colors ${
                      isActive ? "bg-surface text-gold font-semibold" : "text-muted hover:text-main hover:bg-surface/40"
                    }`}
                  >
                    <span className="truncate">{item.title}</span>
                    <span className="font-stat text-[10px] text-muted/70 ml-1 shrink-0">{item.page}</span>
                  </button>
                );
              })}
            </div>
          </aside>
        )}

        {/* Viewport Central de la Página Renderizada */}
        <main className="flex-1 bg-input border border-border-iron rounded-xl overflow-auto flex items-center justify-center p-4 relative">
          {loading && (
            <div className="absolute top-4 right-4 bg-card/90 border border-border-iron px-3 py-1 rounded text-xs text-gold shadow-md">
              Renderizando página...
            </div>
          )}

          {pageBase64 ? (
            <img
              src={`data:image/png;base64,${pageBase64}`}
              alt={`Página ${currentPage}`}
              className="max-w-full h-auto shadow-2xl rounded-sm border border-border-iron/40 object-contain"
              style={{ transform: `scale(${zoom > 1 ? 1 : zoom})` }}
            />
          ) : (
            <div className="text-center text-xs text-muted space-y-2 p-8">
              <FolderOpen className="w-8 h-8 text-muted mx-auto opacity-50" />
              <p>Selecciona un manual o ficha PDF para visualizarlo en alta resolución.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
