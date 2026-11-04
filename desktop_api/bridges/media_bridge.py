"""
Sub-puente para gestión de retratos de personajes, generación con IA y diálogos de imágenes.
"""
import os
import base64
from pathlib import Path
from typing import Optional, Dict, Any

import webview


class MediaBridgeMixin:
    """Métodos de retratos, diálogos multimedia y generación con IA."""

    def open_image_dialog(self) -> Optional[str]:
        """Abre un diálogo nativo para seleccionar imagen de retrato."""
        if not self._window:
            return None
        file_types = ("Archivos de Imagen (*.png;*.jpg;*.jpeg;*.webp)", "Todos los Archivos (*.*)")
        result = self._window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        if result and len(result) > 0:
            return result[0]
        return None

    def upload_character_portrait(self, char_id: int) -> Dict[str, Any]:
        """Abre diálogo de imagen, guarda el retrato para el personaje y devuelve la ficha actualizada."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        img_path = self.open_image_dialog()
        if not img_path:
            return {"success": False, "cancelled": True}

        saved_path = self._db.save_portrait_file(img_path, char.name)
        if not saved_path or not os.path.exists(saved_path):
            return {"success": False, "error": "No se pudo copiar la imagen seleccionada."}

        char.portrait_path = saved_path
        try:
            ext = Path(saved_path).suffix.lower().lstrip(".") or "png"
            if ext == "jpg":
                ext = "jpeg"
            with open(saved_path, "rb") as f:
                b64_raw = base64.b64encode(f.read()).decode("ascii")
                char.portrait_base64 = f"data:image/{ext};base64,{b64_raw}"
        except Exception:
            pass

        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {
            "success": True,
            "portrait_path": char.portrait_path,
            "portrait_base64": char.portrait_base64,
            "character": self._serialize_character(char),
        }

    def set_character_portrait_base64(self, char_id: int, image_base64: str) -> Dict[str, Any]:
        """Guarda un retrato en formato base64 directamente en la ficha del personaje."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}
        char.portrait_base64 = image_base64
        self._db.save_character(char, set_active=self._is_active_character_id(char_id))
        return {
            "success": True,
            "portrait_base64": char.portrait_base64,
            "character": self._serialize_character(char),
        }

    def generate_ai_portrait(
        self,
        prompt: str,
        provider: str = "pollinations",
        api_key: str = "",
        api_url: str = "",
        model: str = ""
    ) -> Dict[str, Any]:
        """
        Genera una imagen con IA usando la cadena resiliente de proveedores:
        Pollinations -> AI Horde -> SD WebUI -> Google / OpenAI.
        """
        try:
            from ..image_providers import ImageProviderChain
            chain = ImageProviderChain()
            return chain.generate(
                prompt=prompt,
                provider=provider,
                api_key=api_key,
                api_url=api_url,
                model=model,
            )
        except Exception as e:
            return {"success": False, "error": f"Error en la generación de imagen: {e}"}
