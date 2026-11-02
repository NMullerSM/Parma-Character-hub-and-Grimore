import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw, RotateCcw, ChevronDown, ChevronUp } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  showDetails: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
    showDetails: false,
  };

  public static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("[Parma ErrorBoundary] Error no controlado en la interfaz:", error, errorInfo);
    this.setState({ errorInfo });
  }

  private handleReload = () => {
    window.location.reload();
  };

  private handleResetOnboarding = () => {
    try {
      localStorage.removeItem("parma_has_completed_onboarding");
      localStorage.removeItem("parma_tour_skipped_all");
      localStorage.removeItem("parma_completed_section_tours");
    } catch (e) {
      console.warn("No se pudo limpiar el almacenamiento local:", e);
    }
    window.location.reload();
  };

  private toggleDetails = () => {
    this.setState((prev) => ({ showDetails: !prev.showDetails }));
  };

  public render() {
    if (this.state.hasError) {
      const errorMessage = this.state.error?.message || "Error desconocido";
      const componentStack = this.state.errorInfo?.componentStack || "";

      return (
        <div className="min-h-screen w-full flex items-center justify-center bg-[#0d1117] text-slate-200 p-6 select-none font-sans">
          <div className="max-w-xl w-full bg-[#161b22] border border-gold/30 rounded-2xl shadow-2xl p-7 flex flex-col items-center text-center relative overflow-hidden">
            {/* Resplandor decorativo de fondo */}
            <div className="absolute -top-16 -right-16 w-36 h-36 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute -bottom-16 -left-16 w-36 h-36 bg-red-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="p-3.5 bg-amber-500/10 border border-amber-500/30 rounded-2xl text-amber-400 mb-4 shadow-inner">
              <AlertTriangle className="w-9 h-9" />
            </div>

            <h1 className="text-xl font-bold text-slate-100 mb-2 tracking-wide font-serif">
              Anomalía en la Interfaz de Parma
            </h1>
            <p className="text-sm text-slate-400 mb-6 leading-relaxed max-w-md">
              Ocurrió un error inesperado al renderizar la interfaz gráfica. Tus datos de personajes,
              fichas y tiradas están a salvo en tu almacenamiento local.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-3 w-full mb-5">
              <button
                type="button"
                onClick={this.handleReload}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-amber-600 to-amber-500 text-slate-950 hover:from-amber-500 hover:to-amber-400 shadow-md hover:shadow-amber-500/20 active:scale-95 transition-all cursor-pointer"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Recargar Interfaz</span>
              </button>

              <button
                type="button"
                onClick={this.handleResetOnboarding}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700 active:scale-95 transition-all cursor-pointer"
                title="Reinicia el estado de guías visuales y recarga"
              >
                <RotateCcw className="w-4 h-4 text-slate-400" />
                <span>Reiniciar Guías & Recargar</span>
              </button>
            </div>

            {/* Detalles técnicos desplegables */}
            <div className="w-full text-left mt-2">
              <button
                type="button"
                onClick={this.toggleDetails}
                className="w-full flex items-center justify-between px-3 py-2 text-xs text-slate-400 hover:text-slate-300 bg-slate-900/60 hover:bg-slate-900/90 rounded-lg border border-slate-800 transition-colors cursor-pointer"
              >
                <span className="font-mono truncate">Detalles técnicos: {errorMessage}</span>
                {this.state.showDetails ? (
                  <ChevronUp className="w-4 h-4 flex-shrink-0 ml-2" />
                ) : (
                  <ChevronDown className="w-4 h-4 flex-shrink-0 ml-2" />
                )}
              </button>

              {this.state.showDetails && (
                <div className="mt-2 p-3 bg-black/60 border border-slate-800 rounded-lg text-xs font-mono text-red-300/90 overflow-x-auto max-h-48 whitespace-pre-wrap leading-relaxed select-text">
                  <div className="font-bold text-red-400 mb-1">{errorMessage}</div>
                  {componentStack && <div className="text-slate-400 text-[11px] mt-2">{componentStack}</div>}
                </div>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
