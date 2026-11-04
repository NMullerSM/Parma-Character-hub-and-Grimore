"""
Sub-puente para auto-actualización del sistema y reinicio silencioso.
"""
from typing import Dict, Any


class UpdaterBridgeMixin:
    """Métodos de descarga en segundo plano y aplicación de actualizaciones."""

    def start_auto_update(self, download_url: str, version: str) -> Dict[str, Any]:
        """Inicia la descarga en segundo plano del instalador de la nueva versión."""
        return self._updater.start_download(download_url, version)

    def get_update_progress(self) -> Dict[str, Any]:
        """Retorna el progreso porcentual y estado de la descarga."""
        return self._updater.get_progress()

    def apply_update_and_restart(self) -> Dict[str, Any]:
        """Aplica la actualización silenciosa (/SILENT /CLOSEAPPLICATIONS) y reinicia."""
        return self._updater.apply_update_and_restart()
