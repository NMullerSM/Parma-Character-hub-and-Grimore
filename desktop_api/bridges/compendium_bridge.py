"""
Sub-puente para consulta del compendio SQLite (monstruos, conjuros, equipo/objetos).
Expone métodos de búsqueda indexada, filtrado y detalle para la interfaz de usuario.
"""
from typing import Optional, Dict, Any, List


class CompendiumBridgeMixin:
    """Métodos de lectura, búsqueda y paginación sobre las tablas compendium_* de SQLite."""

    def search_monsters(
        self,
        query: str = "",
        cr_min: Optional[float] = None,
        cr_max: Optional[float] = None,
        type_filter: Optional[str] = None,
        size: Optional[str] = None,
        edition: Optional[str] = None,
        language: str = "en",
        page: int = 1,
        page_size: int = 25,
    ) -> Dict[str, Any]:
        """
        Búsqueda de criaturas en compendium_monsters con filtros de CR, tipo y tamaño.
        Retorna resultados paginados y el total de registros encontrados.
        """
        safe_page = max(1, int(page or 1))
        safe_limit = max(1, min(100, int(page_size or 25)))
        offset = (safe_page - 1) * safe_limit

        items = self._db.search_compendium_monsters(
            query=query or "",
            min_cr=cr_min,
            max_cr=cr_max,
            monster_type=type_filter,
            size=size,
            edition=edition,
            language=language,
            limit=safe_limit,
            offset=offset,
        )
        total = self._db.count_compendium_entries("monsters", edition=edition, language=language)
        return {
            "items": items,
            "total": total,
            "page": safe_page,
            "page_size": safe_limit,
            "has_more": (offset + len(items)) < total,
        }

    def get_monster_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retorna el registro completo de una criatura por entity_id o nombre."""
        if not entity_id:
            return None
        return self._db.get_compendium_monster_by_id(entity_id)

    def search_spells(
        self,
        query: str = "",
        level: Optional[int] = None,
        max_level: Optional[int] = None,
        school: Optional[str] = None,
        class_name: Optional[str] = None,
        is_concentration: Optional[bool] = None,
        is_ritual: Optional[bool] = None,
        edition: Optional[str] = None,
        language: str = "en",
        page: int = 1,
        page_size: int = 25,
    ) -> Dict[str, Any]:
        """
        Búsqueda de conjuros en compendium_spells con filtros de nivel, escuela, clase, concentración y ritual.
        """
        safe_page = max(1, int(page or 1))
        safe_limit = max(1, min(100, int(page_size or 25)))
        offset = (safe_page - 1) * safe_limit

        items = self._db.search_compendium_spells(
            query=query or "",
            level=level,
            max_level=max_level,
            school=school,
            class_name=class_name,
            is_concentration=is_concentration,
            is_ritual=is_ritual,
            edition=edition,
            language=language,
            limit=safe_limit,
            offset=offset,
        )
        total = self._db.count_compendium_entries("spells", edition=edition, language=language)
        return {
            "items": items,
            "total": total,
            "page": safe_page,
            "page_size": safe_limit,
            "has_more": (offset + len(items)) < total,
        }

    def get_spell_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retorna el registro completo de un conjuro por entity_id o nombre."""
        if not entity_id:
            return None
        return self._db.get_compendium_spell_by_id(entity_id)

    def search_items(
        self,
        query: str = "",
        item_type: Optional[str] = None,
        rarity: Optional[str] = None,
        weapon_mastery: Optional[str] = None,
        edition: Optional[str] = None,
        language: str = "en",
        page: int = 1,
        page_size: int = 25,
    ) -> Dict[str, Any]:
        """
        Búsqueda de equipo, armas y objetos mágicos en compendium_items con soporte de Weapon Mastery 2024.
        """
        safe_page = max(1, int(page or 1))
        safe_limit = max(1, min(100, int(page_size or 25)))
        offset = (safe_page - 1) * safe_limit

        items = self._db.search_compendium_items(
            query=query or "",
            item_type=item_type,
            rarity=rarity,
            weapon_mastery=weapon_mastery,
            edition=edition,
            language=language,
            limit=safe_limit,
            offset=offset,
        )
        total = self._db.count_compendium_entries("items", edition=edition, language=language)
        return {
            "items": items,
            "total": total,
            "page": safe_page,
            "page_size": safe_limit,
            "has_more": (offset + len(items)) < total,
        }

    def get_item_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retorna el registro completo de un objeto/arma/armadura por entity_id o nombre."""
        if not entity_id:
            return None
        return self._db.get_compendium_item_by_id(entity_id)

    def get_compendium_counts(self, edition: Optional[str] = None, language: str = "en") -> Dict[str, int]:
        """Retorna el conteo total de registros en las 3 categorías principales del compendio."""
        return {
            "monsters": self._db.count_compendium_entries("monsters", edition=edition, language=language),
            "spells": self._db.count_compendium_entries("spells", edition=edition, language=language),
            "items": self._db.count_compendium_entries("items", edition=edition, language=language),
        }
