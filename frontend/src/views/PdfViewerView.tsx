import React, { useState, useEffect, useRef } from "react";
import { api } from "../api/client";
import type { PdfDocumentSummary, PdfDocumentInfo, PdfTocItem, PdfLinkItem } from "../api/types";
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Minimize2,
  FolderOpen,
  List,
  PenTool,
  Eraser,
  Bookmark,
} from "lucide-react";

export const PdfViewerView: React.FC = () => {
  const [docList, setDocList] = useState<PdfDocumentSummary[]>([]);
  const [selectedPath, setSelectedPath] = useState<string>("");
  const [docInfo, setDocInfo] = useState<PdfDocumentInfo | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [zoom, setZoom] = useState<number>(1.0);
  const [pageBase64, setPageBase64] = useState<string>("");
  const [pageLinks, setPageLinks] = useState<PdfLinkItem[]>([]);
  const [pageDims, setPageDims] = useState<{ width: number; height: number }>({ width: 595, height: 842 });
  const [showToc, setShowToc] = useState<boolean>(false);
  const [isZen, setIsZen] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [trimMargins, setTrimMargins] = useState<boolean>(true);

  // Herramienta de Rotulador / Dibujo sobre el PDF
  const [isPenActive, setIsPenActive] = useState<boolean>(false);
  const [pageAnnotations, setPageAnnotations] = useState<Record<number, string>>({}); // page -> dataUrl
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isDrawing, setIsDrawing] = useState<boolean>(false);

  // Contenedor del visor para scroll suave
  const viewportRef = useRef<HTMLDivElement | null>(null);

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

  // Manejo de atajos de teclado (PageUp/PageDown, flechas)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key === "ArrowLeft" || e.key === "PageUp") {
        gotoPage(currentPage - 1);
      } else if (e.key === "ArrowRight" || e.key === "PageDown") {
        gotoPage(currentPage + 1);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentPage, docInfo]);

  const loadDocument = async (filePath: string) => {
    setSelectedPath(filePath);
    setLoading(true);
    try {
      const info = await api.openPdfDocument(filePath);
      if (info.success) {
        setDocInfo(info);
        setCurrentPage(1);
        await renderPage(1, zoom, trimMargins);
      }
    } catch (e) {
      console.error("Error opening PDF:", e);
    } finally {
      setLoading(false);
    }
  };

  const renderPage = async (page: number, zoomLevel: number, shouldTrim: boolean = trimMargins) => {
    setLoading(true);
    try {
      const res = await api.renderPdfPage(page, zoomLevel, shouldTrim);
      if (res.success && res.image_base64) {
        setPageBase64(res.image_base64);
        setPageLinks(res.links || []);
        if (res.width && res.height) {
          setPageDims({ width: res.width, height: res.height });
        }
      }
    } catch (e) {
      console.error("Error rendering page:", e);
    } finally {
      setLoading(false);
      // Volver el scroll al tope de la página
      if (viewportRef.current) {
        viewportRef.current.scrollTop = 0;
      }
    }
  };

  const gotoPage = async (p: number) => {
    if (!docInfo) return;
    const target = Math.max(1, Math.min(docInfo.page_count, p));
    setCurrentPage(target);
    await renderPage(target, zoom, trimMargins);
  };

  const handleZoom = async (delta: number) => {
    const nextZoom = Math.max(0.6, Math.min(2.5, Math.round((zoom + delta) * 10) / 10));
    setZoom(nextZoom);
    await renderPage(currentPage, nextZoom, trimMargins);
  };

  // ==========================================
  // CANVAS DE ANOTACIONES / ROTULADOR
  // ==========================================
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const existing = pageAnnotations[currentPage];
    if (existing) {
      const img = new Image();
      img.onload = () => ctx.drawImage(img, 0, 0);
      img.src = existing;
    }
  }, [currentPage, pageAnnotations, pageDims]);

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isPenActive) return;
    setIsDrawing(true);
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();
    ctx.beginPath();
    ctx.moveTo((e.clientX - rect.left) * (canvas.width / rect.width), (e.clientY - rect.top) * (canvas.height / rect.height));
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !isPenActive) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();

    ctx.strokeStyle = "rgba(230, 57, 70, 0.75)"; // Carmesí traslúcido
    ctx.lineWidth = 4;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.lineTo((e.clientX - rect.left) * (canvas.width / rect.width), (e.clientY - rect.top) * (canvas.height / rect.height));
    ctx.stroke();
  };

  const stopDrawing = () => {
    if (!isDrawing) return;
    setIsDrawing(false);
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dataUrl = canvas.toDataURL();
    setPageAnnotations((prev) => ({ ...prev, [currentPage]: dataUrl }));
  };

  const clearCurrentAnnotation = () => {
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext("2d");
      ctx?.clearRect(0, 0, canvas.width, canvas.height);
    }
    setPageAnnotations((prev) => {
      const next = { ...prev };
      delete next[currentPage];
      return next;
    });
  };

  // Filtrar capítulos principales para el combobox comprimido
  const majorChapters = (docInfo?.toc || []).filter((item) => item.level <= 2);

  return (
    <div
      className={`h-full flex flex-col p-3 md:p-5 space-y-3 mx-auto overflow-hidden ${
        isZen ? "fixed inset-0 z-50 bg-canvas p-4" : "max-w-7xl"
      }`}
    >
      {/* 1. Barra de Herramientas Ergonómica y Comprimida */}
      <div className="bg-card border border-border-iron rounded-xl p-2.5 flex flex-wrap items-center justify-between gap-2.5 shrink-0 select-none shadow-xs">
        {/* Selector de Manual y Combobox de Capítulos */}
        <div className="flex items-center gap-2">
          {/* Selector de Archivo PDF */}
          <select
            value={selectedPath}
            onChange={(e) => loadDocument(e.target.value)}
            className="bg-surface text-main border border-border-iron rounded px-2.5 py-1 text-xs focus:border-gold outline-none max-w-[200px] truncate"
          >
            {docList.map((d) => (
              <option key={d.path} value={d.path}>
                📄 {d.name}
              </option>
            ))}
          </select>

          {/* Combobox Comprimido de Capítulos / Secciones */}
          {majorChapters.length > 0 && (
            <div className="flex items-center gap-1">
              <Bookmark className="w-3.5 h-3.5 text-gold shrink-0" />
              <select
                onChange={(e) => gotoPage(Number(e.target.value))}
                value={majorChapters.reduce((acc, curr) => (curr.page <= currentPage ? curr.page : acc), majorChapters[0]?.page || 1)}
                className="bg-surface text-main border border-border-iron rounded px-2 py-1 text-xs focus:border-gold outline-none max-w-[190px] md:max-w-[240px] truncate font-medium"
                title="Saltar a Capítulo o Sección"
              >
                {majorChapters.map((ch, idx) => (
                  <option key={idx} value={ch.page}>
                    {ch.level > 1 ? `  ↳ ${ch.title}` : ch.title} (p. {ch.page})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Botón para alternar el árbol de índice lateral si se desea navegación completa */}
          {docInfo?.toc && docInfo.toc.length > 0 && (
            <button
              onClick={() => setShowToc(!showToc)}
              title={showToc ? "Ocultar Índice Lateral" : "Ver Índice Completo"}
              className={`p-1.5 rounded border transition-colors ${
                showToc ? "border-gold bg-gold/10 text-gold" : "border-border-iron text-muted hover:text-main"
              }`}
            >
              <List className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Controles de Navegación de Página */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => gotoPage(currentPage - 1)}
            disabled={currentPage <= 1}
            className="p-1 rounded border border-border-iron hover:border-gold disabled:opacity-30 text-main transition-colors"
            title="Página Anterior (←)"
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
            className="p-1 rounded border border-border-iron hover:border-gold disabled:opacity-30 text-main transition-colors"
            title="Página Siguiente (→)"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Herramientas de Rotulador, Zoom y Pantalla Completa */}
        <div className="flex items-center gap-1.5">
          {/* Rotulador de Anotaciones */}
          <button
            onClick={() => setIsPenActive(!isPenActive)}
            title={isPenActive ? "Desactivar Marcador" : "Activar Rotulador para Rayar / Marcar"}
            className={`p-1.5 rounded border transition-all flex items-center gap-1 text-xs ${
              isPenActive ? "border-crimson bg-crimson/20 text-crimson font-bold shadow-xs" : "border-border-iron text-muted hover:text-main"
            }`}
          >
            <PenTool className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Marcar</span>
          </button>

          {pageAnnotations[currentPage] && (
            <button
              onClick={clearCurrentAnnotation}
              title="Borrar anotaciones de esta página"
              className="p-1.5 rounded border border-border-iron hover:border-crimson text-muted hover:text-crimson transition-colors"
            >
              <Eraser className="w-3.5 h-3.5" />
            </button>
          )}

          <div className="h-4 w-px bg-border-iron mx-1" />

          {/* Zoom */}
          <button
            onClick={() => handleZoom(-0.2)}
            title="Reducir Zoom"
            className="p-1.5 rounded border border-border-iron hover:border-gold text-muted hover:text-main"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="text-xs font-stat text-muted min-w-[40px] text-center">{Math.round(zoom * 100)}%</span>
          <button
            onClick={() => handleZoom(0.2)}
            title="Aumentar Zoom"
            className="p-1.5 rounded border border-border-iron hover:border-gold text-muted hover:text-main"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>

          {/* Alternar Limpieza de Bordes / Escaneo */}
          <button
            onClick={async () => {
              const nextTrim = !trimMargins;
              setTrimMargins(nextTrim);
              await renderPage(currentPage, zoom, nextTrim);
            }}
            title={
              trimMargins
                ? "Bordes limpios activos (Recorta marcos de imprenta). Clic para ver original"
                : "Bordes originales activos. Clic para recortar marcos negros/rojos de escaneo"
            }
            className={`px-2 py-1 rounded border text-[11px] font-medium transition-colors ${
              trimMargins
                ? "border-gold/60 bg-gold/15 text-gold"
                : "border-border-iron text-muted hover:text-main"
            }`}
          >
            {trimMargins ? "Sin Marcos" : "Con Marcos"}
          </button>

          {/* Pantalla Completa */}
          <button
            onClick={() => setIsZen(!isZen)}
            title={isZen ? "Salir de Pantalla Completa" : "Pantalla Completa Zen"}
            className="p-1.5 rounded border border-border-iron hover:border-gold text-muted hover:text-main ml-1"
          >
            {isZen ? <Minimize2 className="w-3.5 h-3.5 text-crimson" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* 2. Área de Lectura y Panel de Índice */}
      <div className="flex-1 flex gap-3 min-h-0 overflow-hidden">
        {/* Panel Lateral de Índice Opcional (TOC) */}
        {showToc && docInfo?.toc && docInfo.toc.length > 0 && (
          <aside className="w-64 bg-card border border-border-iron rounded-xl p-3 overflow-y-auto space-y-1 shrink-0 select-none animate-in fade-in duration-200">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted mb-2 pb-1 border-b border-border-iron/60 flex items-center justify-between">
              <span>Índice Completo</span>
              <span className="font-stat text-[10px] text-muted">({docInfo.toc.length})</span>
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

        {/* Viewport de Página: Con Scroll Natural desde Arriba hacia Abajo */}
        <main
          ref={viewportRef}
          className="flex-1 bg-input border border-border-iron rounded-xl overflow-y-auto overflow-x-auto flex flex-col items-center justify-start p-4 relative"
        >
          {loading && (
            <div className="sticky top-2 z-30 bg-card/95 border border-border-iron px-3 py-1 rounded text-xs text-gold shadow-md">
              Renderizando página...
            </div>
          )}

          {pageBase64 ? (
            <div className="relative shadow-2xl rounded-sm inline-block overflow-hidden bg-canvas">
              {/* Imagen de la Página Renderizada */}
              <img
                src={`data:image/png;base64,${pageBase64}`}
                alt={`Página ${currentPage}`}
                className="block max-w-none rounded-sm select-none"
                style={{
                  width: `${pageDims.width * zoom}px`,
                  height: `${pageDims.height * zoom}px`,
                }}
              />

              {/* Capa de Enlaces Interactivos del PDF (TOC interno, referencias cruzadas) */}
              {!isPenActive &&
                pageLinks.map((link, lIdx) => {
                  const [x0, y0, x1, y1] = link.rect;
                  // En PyMuPDF, las coordenadas de rect son en puntos desde la esquina superior izquierda
                  const leftPct = (x0 / pageDims.width) * 100;
                  const topPct = (y0 / pageDims.height) * 100;
                  const widthPct = ((x1 - x0) / pageDims.width) * 100;
                  const heightPct = ((y1 - y0) / pageDims.height) * 100;

                  return (
                    <button
                      key={lIdx}
                      onClick={() => gotoPage(link.target_page)}
                      title={`Saltar a página ${link.target_page}`}
                      style={{
                        left: `${leftPct}%`,
                        top: `${topPct}%`,
                        width: `${widthPct}%`,
                        height: `${heightPct}%`,
                      }}
                      className="absolute z-10 bg-transparent hover:bg-gold/20 border border-transparent hover:border-gold/50 rounded-xs transition-colors cursor-pointer"
                    />
                  );
                })}

              {/* Capa Canvas para Rotulador / Anotaciones */}
              <canvas
                ref={canvasRef}
                width={pageDims.width * zoom}
                height={pageDims.height * zoom}
                onMouseDown={startDrawing}
                onMouseMove={draw}
                onMouseUp={stopDrawing}
                onMouseLeave={stopDrawing}
                className={`absolute inset-0 z-20 ${isPenActive ? "cursor-crosshair pointer-events-auto" : "pointer-events-none"}`}
              />
            </div>
          ) : (
            <div className="text-center text-xs text-muted space-y-2 p-12 my-auto">
              <FolderOpen className="w-10 h-10 text-muted mx-auto opacity-50" />
              <p className="font-semibold text-main text-sm">Visor de Manuales Oficiales D&D 5e</p>
              <p>Selecciona un PDF de la lista superior para comenzar tu lectura.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
