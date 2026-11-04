"""
Sub-puente para visualización, renderizado e importación/exportación de PDFs AcroForm.
"""
import os
from typing import Optional, Dict, Any, List

import webview
from core.pdf_engine import UniversalAcroFormHandler


class PdfBridgeMixin:
    """Métodos de lectura, renderizado y manipulación de PDFs oficiales y fichas AcroForm."""

    def open_pdf_dialog(self) -> Optional[str]:
        """Abre un diálogo nativo para seleccionar un PDF de personaje o manual."""
        if not self._window:
            return None
        file_types = ("Archivos PDF (*.pdf)", "Todos los Archivos (*.*)")
        result = self._window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        if result and len(result) > 0:
            return result[0]
        return None

    def list_pdf_documents(self) -> List[Dict[str, str]]:
        """Busca manuales y documentos PDF en el proyecto, detectando idioma (es/en)."""
        results = []
        search_dirs = [
            (os.path.join(self._base_dir, "data", "manuals", "es"), "es"),
            (os.path.join(self._base_dir, "data", "manuals", "en"), "en"),
            (os.path.join(self._base_dir, "data", "manuals"), "all"),
            (os.path.join(self._user_data_dir, "manuals", "es"), "es"),
            (os.path.join(self._user_data_dir, "manuals", "en"), "en"),
            (os.path.join(self._user_data_dir, "manuals"), "all"),
            (os.path.join(self._user_data_dir, "characters"), "all"),
        ]
        dev_char_dir = os.path.join(self._base_dir, "data", "characters")
        if dev_char_dir != os.path.join(self._user_data_dir, "characters"):
            search_dirs.append((dev_char_dir, "all"))

        for sdir, dir_lang in search_dirs:
            if os.path.exists(sdir) and os.path.isdir(sdir):
                for fname in sorted(os.listdir(sdir)):
                    if fname.lower().endswith(".pdf"):
                        full = os.path.join(sdir, fname)
                        if not any(r["path"] == full for r in results):
                            detected_lang = dir_lang
                            if detected_lang == "all":
                                lower_name = fname.lower()
                                if "[en]" in lower_name or "_en" in lower_name or "player's handbook" in lower_name or "dungeon master" in lower_name or "monster manual" in lower_name:
                                    detected_lang = "en"
                                elif "[es]" in lower_name or "_es" in lower_name or "manual del jugador" in lower_name or "guia" in lower_name or "guía" in lower_name or "caldero" in lower_name:
                                    detected_lang = "es"

                            results.append({
                                "name": fname,
                                "path": full,
                                "lang": detected_lang
                            })
        return results

    def open_pdf_document(self, file_path: str) -> Dict[str, Any]:
        """Abre un documento PDF y retorna su metainformación."""
        if not os.path.isabs(file_path):
            candidates = [
                os.path.join(self._base_dir, file_path),
                os.path.join(self._user_data_dir, file_path),
                os.path.join(self._base_dir, "data", "manuals", file_path),
                os.path.join(self._user_data_dir, "manuals", file_path),
                os.path.join(self._base_dir, "data", "manuals", "es", file_path),
                os.path.join(self._base_dir, "data", "manuals", "en", file_path),
                os.path.join(self._user_data_dir, "manuals", "es", file_path),
                os.path.join(self._user_data_dir, "manuals", "en", file_path),
            ]
            for c in candidates:
                if os.path.exists(c):
                    file_path = c
                    break

        success = self._pdf_reader.open_document(file_path)
        if not success:
            return {"success": False, "error": f"No se pudo abrir el archivo {file_path}"}

        return {
            "success": True,
            "path": file_path,
            "filename": os.path.basename(file_path),
            "page_count": self._pdf_reader.page_count,
            "toc": self._pdf_reader.get_toc(),
        }

    def render_pdf_page(self, page_num: int, zoom: float = 1.0, trim_margins: Optional[bool] = None) -> Dict[str, Any]:
        """Renderiza una página del PDF abierto a imagen base64 con opción de limpieza de marco."""
        if not self._pdf_reader.is_open:
            return {"success": False, "error": "No hay ningún PDF abierto."}

        b64 = self._pdf_reader.render_page_base64(page_num, zoom=zoom, trim_margins=trim_margins)
        links = self._pdf_reader.get_page_links(page_num, trim_margins=trim_margins)
        pw, ph = self._pdf_reader.get_page_dimensions(page_num, trim_margins=trim_margins)

        if b64 and not b64.startswith("data:"):
            b64 = f"data:image/png;base64,{b64}"

        return {
            "success": bool(b64),
            "page_num": page_num,
            "image_base64": b64,
            "links": links,
            "width": pw,
            "height": ph,
            "trimmed": self._pdf_reader._should_trim(trim_margins),
        }

    def export_character_pdf(self, char_id: int, target_path: Optional[str] = None) -> Dict[str, Any]:
        """Exporta el personaje a una hoja PDF oficial editable AcroForm con selector de guardado nativo."""
        char = self._db.get_character_by_id(char_id)
        if not char:
            return {"success": False, "error": "Personaje no encontrado"}

        template_candidates = [
            os.path.join(self._base_dir, "data", "templates", "character_sheet_template.pdf"),
            os.path.join(self._base_dir, "data", "characters", "template_sheet.pdf"),
            os.path.join(self._user_data_dir, "templates", "character_sheet_template.pdf"),
            os.path.join(self._base_dir, "data", "characters", "Artanis LVL 4.pdf"),
            os.path.join(self._base_dir, "Artanis LVL 4.pdf"),
        ]
        template_pdf = next((c for c in template_candidates if os.path.exists(c)), None)
        if not template_pdf:
            return {"success": False, "error": "No se encontró una plantilla PDF oficial de ficha de personaje en el sistema."}

        clean_name = "".join(c for c in char.name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        default_filename = f"{clean_name}_Sheet.pdf"
        char_dir = os.path.join(self._user_data_dir, "characters")
        os.makedirs(char_dir, exist_ok=True)

        if not target_path and self._window:
            try:
                res = self._window.create_file_dialog(
                    webview.SAVE_DIALOG,
                    directory=char_dir,
                    save_filename=default_filename,
                    file_types=("Archivos PDF (*.pdf)", "Todos los Archivos (*.*)"),
                )
                if res:
                    target_path = res[0] if isinstance(res, (list, tuple)) else str(res)
                elif res is not None:
                    return {"success": False, "cancelled": True}
            except Exception:
                pass

        if not target_path:
            target_path = os.path.join(char_dir, default_filename)

        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        try:
            out_file = UniversalAcroFormHandler.export_character_to_pdf(
                char=char,
                template_pdf_path=template_pdf,
                output_path=target_path,
            )
            return {"success": True, "path": out_file}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def import_character_pdf(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Importa una hoja de personaje desde un PDF AcroForm editable."""
        if not file_path:
            file_path = self.open_pdf_dialog()
            if not file_path:
                return {"success": False, "cancelled": True}

        if not os.path.exists(file_path):
            return {"success": False, "error": f"Archivo PDF no encontrado: {file_path}"}

        try:
            char = UniversalAcroFormHandler.load_character_from_pdf(file_path)
            char_id = self._db.save_character(char, set_active=True)
            saved = self._db.get_character_by_id(char_id)
            return {"success": True, "id": char_id, "character": self._serialize_character(saved)}
        except Exception as e:
            return {"success": False, "error": str(e)}
