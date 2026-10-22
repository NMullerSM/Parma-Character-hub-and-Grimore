import React, { useState, useEffect, useRef } from "react";
import { useTranslation } from "../i18n";
import { api } from "../api/client";
import type { PdfDocumentSummary, PdfDocumentInfo, PdfTocItem, PdfLinkItem } from "../api/types";
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Minimize2,
  List,
  PenTool,
  Eraser,
  Bookmark,
} from "lucide-react";

export const PdfViewerView: React.FC = () => {
  const { t, language } = useTranslation();
  const [docList, setDocList] = useState<PdfDocumentSummary[]>([]);
  const [selectedPath, setSelectedPath] = useState<string>("");
  const [docLangFilter, setDocLangFilter] = useState<"all" | "es" | "en">(language);
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
  const [pageAnnotations, setPageAnnotations] = useState<Record<number, string>>({});
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
    }
  };

  const gotoPage = async (page: number) => {
    if (!docInfo || page < 1 || page > docInfo.page_count) return;
    saveCurrentAnnotation();
    setCurrentPage(page);
    await renderPage(page, zoom, trimMargins);
    if (viewportRef.current) {
      viewportRef.current.scrollTop = 0;
    }
  };

  const handleZoom = async (delta: number) => {
    const nextZoom = Math.max(0.6, Math.min(2.5, Math.round((zoom + delta) * 10) / 10));
    setZoom(nextZoom);
    await renderPage(currentPage, nextZoom, trimMargins);
  };

  // Guardar y restaurar trazos del Canvas sobre la página
  const saveCurrentAnnotation = () => {
    if (canvasRef.current && isPenActive) {
      const dataUrl = canvasRef.current.toDataURL();
      setPageAnnotations((prev) => ({ ...prev, [currentPage]: dataUrl }));
    }
  };

  const clearCurrentAnnotation = () => {
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext("2d");
      if (ctx) ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
      setPageAnnotations((prev) => {
        const next = { ...prev };
        delete next[currentPage];
        return next;
      });
    }
  };

  useEffect(() => {
    if (canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const saved = pageAnnotations[currentPage];
      if (saved) {
        const img = new Image();
        img.onload = () => ctx.drawImage(img, 0, 0);
        img.src = saved;
      }
    }
  }, [currentPage, pageBase64]);

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isPenActive || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) * (canvas.width / rect.width);
    const y = (e.clientY - rect.top) * (canvas.height / rect.height);
    ctx.strokeStyle = "rgba(234, 179, 8, 0.45)";
    ctx.lineWidth = 14;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();
    ctx.moveTo(x, y);
    setIsDrawing(true);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !isPenActive || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) * (canvas.width / rect.width);
    const y = (e.clientY - rect.top) * (canvas.height / rect.height);
    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const stopDrawing = () => {
    if (!isDrawing) return;
    setIsDrawing(false);
    saveCurrentAnnotation();
  };

  const majorChapters = (docInfo?.toc || []).filter((item) => item.level <= 2);

  const filteredDocs = docList.filter((d) => {
    if (docLangFilter === "all") return true;
    return d.lang === docLangFilter || d.lang === "all";
  });

  return (
    <div className={`h-full flex flex-col p-2 sm:p-4 space-y-2 select-none overflow-hidden ${isZen ? "fixed inset-0 z-50 bg-canvas p-0" : ""}`}>
      {/* 1. Barra de Controles Tácticos Superiores */}
      <div className="bg-card border border-border-iron rounded-xl p-2.5 flex flex-wrap items-center justify-between gap-2.5 shrink-0 select-none shadow-xs">
        {/* Selector de Manual y Combobox de Capítulos */}
        <div className="flex items-center gap-2">
          {/* Selector de Filtro de Idioma de Manuales */}
          <div className="flex items-center rounded border border-border-iron bg-surface p-0.5 text-[10px] font-semibold">
            <button
              onClick={() => setDocLangFilter("all")}
              className={`px-1.5 py-0.5 rounded transition-colors ${
                docLangFilter === "all" ? "bg-gold text-canvas" : "text-muted hover:text-main"
              }`}
            >
              {t("common.all")}
            </button>
            <button
              onClick={() => setDocLangFilter("es")}
              className={`px-1.5 py-0.5 rounded transition-colors ${
                docLangFilter === "es" ? "bg-gold text-canvas" : "text-muted hover:text-main"
              }`}
            >
              ES
            </button>
            <button
              onClick={() => setDocLangFilter("en")}
              className={`px-1.5 py-0.5 rounded transition-colors ${
                docLangFilter === "en" ? "bg-gold text-canvas" : "text-muted hover:text-main"
              }`}
            >
              EN
            </button>
          </div>

          {/* Selector de Archivo PDF */}
          <select
            value={selectedPath}
            onChange={(e) => loadDocument(e.target.value)}
            className="bg-surface text-main border border-border-iron rounded px-2.5 py-1 text-xs focus:border-gold outline-none max-w-[200px] truncate"
          >
            {filteredDocs.map((d) => (
              <option key={d.path} value={d.path}>
                {d.lang === "en" ? "[EN] " : d.lang === "es" ? "[ES] " : "📄 "}{d.name}
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
                title={t("pdf.toc")}
              >
                {majorChapters.map((ch, idx) => (
                  <option key={idx} value={ch.page}>
                    {ch.level > 1 ? `  ↳ ${ch.title}` : ch.title} (p. {ch.page})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Botón para alternar el árbol de índice lateral */}
          {docInfo?.toc && docInfo.toc.length > 0 && (
            <button
              onClick={() => setShowToc(!showToc)}
              title={t("pdf.toc")}
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
            title={t("pdf.prevPage")}
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
            title={t("pdf.nextPage")}
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Herramientas de Rotulador, Zoom y Pantalla Completa */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setIsPenActive(!isPenActive)}
            title={t("pdf.penTool")}
            className={`p-1.5 rounded border transition-all flex items-center gap-1 text-xs ${
              isPenActive ? "border-crimson bg-crimson/20 text-crimson font-bold shadow-xs" : "border-border-iron text-muted hover:text-main"
            }`}
          >
            <PenTool className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{t("pdf.penTool")}</span>
          </button>

          {pageAnnotations[currentPage] && (
            <button
              onClick={clearCurrentAnnotation}
              title={t("pdf.clearDrawings")}
              className="p-1.5 rounded border border-border-iron hover:border-crimson text-muted hover:text-crimson transition-colors"
            >
              <Eraser className="w-3.5 h-3.5" />
            </button>
          )}

          <div className="h-4 w-px bg-border-iron mx-1" />

          {/* Zoom */}
          <button
            onClick={() => handleZoom(-0.2)}
            title={t("pdf.zoomOut")}
            className="p-1.5 rounded border border-border-iron hover:border-gold text-muted hover:text-main"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="text-xs font-stat text-muted min-w-[40px] text-center">{Math.round(zoom * 100)}%</span>
          <button
            onClick={() => handleZoom(0.2)}
            title={t("pdf.zoomIn")}
            className="p-1.5 rounded border border-border-iron hover:border-gold text-muted hover:text-main"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>

          {/* Alternar Limpieza de Bordes */}
          <button
            onClick={async () => {
              const nextTrim = !trimMargins;
              setTrimMargins(nextTrim);
              await renderPage(currentPage, zoom, nextTrim);
            }}
            title={t("pdf.trimMargins")}
            className={`px-2 py-1 rounded border text-[11px] font-medium transition-colors ${
              trimMargins
                ? "border-gold/60 bg-gold/15 text-gold"
                : "border-border-iron text-muted hover:text-main"
            }`}
          >
            {t("pdf.trimMargins")}
          </button>

          {/* Pantalla Completa */}
          <button
            onClick={() => setIsZen(!isZen)}
            title={t("pdf.zenMode")}
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
              <span>{t("pdf.toc")}</span>
              <span className="font-stat text-[10px] text-gold">{docInfo.toc.length}</span>
            </h3>
            <div className="space-y-0.5">
              {docInfo.toc.map((item: PdfTocItem, idx: number) => {
                const isActive = item.page === currentPage;
                return (
                  <button
                    key={idx}
                    onClick={() => gotoPage(item.page)}
                    style={{ paddingLeft: `${Math.max(4, (item.level - 1) * 12)}px` }}
                    className={`w-full text-left py-1 px-2 rounded text-xs transition-colors flex items-center justify-between group ${
                      isActive
                        ? "bg-gold/15 text-gold font-bold border-l-2 border-gold"
                        : "text-muted hover:text-main hover:bg-surface/60"
                    }`}
                  >
                    <span className="truncate pr-1">{item.title}</span>
                    <span className="text-[10px] font-stat text-muted/60 group-hover:text-gold shrink-0">
                      {item.page}
                    </span>
                  </button>
                );
              })}
            </div>
          </aside>
        )}

        {/* Visor Central de la Página Renderizada */}
        <div
          ref={viewportRef}
          className="flex-1 bg-surface/30 border border-border-iron rounded-xl overflow-auto flex items-start justify-center p-2 sm:p-4 relative"
        >
          {loading && (
            <div className="absolute inset-0 bg-canvas/60 backdrop-blur-xs flex items-center justify-center z-30">
              <div className="flex flex-col items-center gap-2">
                <span className="w-7 h-7 border-2 border-gold border-t-transparent rounded-full animate-spin" />
                <span className="text-xs text-gold font-medium">{t("pdf.loadingPage")}</span>
              </div>
            </div>
          )}

          {pageBase64 ? (
            <div className="relative shadow-2xl rounded overflow-hidden select-none inline-block">
              <img
                src={pageBase64.startsWith("data:") ? pageBase64 : `data:image/png;base64,${pageBase64}`}
                alt={t("pdf.pageNav", { current: currentPage, total: docInfo?.page_count || docInfo?.total_pages || 1 })}
                style={{ width: pageDims.width * zoom, height: pageDims.height * zoom }}
                className="max-w-none block pointer-events-none"
              />

              {/* Capa de Enlaces Interactivos del PDF */}
              {pageLinks.map((link, idx) => {
                const scaleX = (pageDims.width * zoom) / pageDims.width;
                const scaleY = (pageDims.height * zoom) / pageDims.height;
                return (
                  <div
                    key={idx}
                    onClick={() => {
                      if (link.target_page) gotoPage(link.target_page);
                      else if (link.uri) window.open(link.uri, "_blank");
                    }}
                    style={{
                      left: link.rect[0] * scaleX,
                      top: link.rect[1] * scaleY,
                      width: (link.rect[2] - link.rect[0]) * scaleX,
                      height: (link.rect[3] - link.rect[1]) * scaleY,
                    }}
                    className="absolute cursor-pointer border border-transparent hover:border-gold hover:bg-gold/15 transition-all rounded"
                    title={link.uri || `Ir a página ${link.target_page}`}
                  />
                );
              })}

              {/* Capa de Dibujo / Rotulador de Anotaciones */}
              <canvas
                ref={canvasRef}
                width={pageDims.width}
                height={pageDims.height}
                style={{
                  width: pageDims.width * zoom,
                  height: pageDims.height * zoom,
                  pointerEvents: isPenActive ? "auto" : "none",
                }}
                onMouseDown={startDrawing}
                onMouseMove={draw}
                onMouseUp={stopDrawing}
                onMouseLeave={stopDrawing}
                className="absolute inset-0 z-20 cursor-crosshair"
              />
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-muted">
              {t("pdf.noPdfs")}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
