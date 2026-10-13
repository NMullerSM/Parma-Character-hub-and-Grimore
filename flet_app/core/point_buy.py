"""
Motor Matemático de Compra por Puntos (Point Buy) oficial D&D 5e (PHB 2024 / 2014).
Presupuesto: 27 puntos.
Rango permitido por característica: 8 a 15 (antes de bonos de trasfondo/especie).
"""
from typing import Dict

TOTAL_BUDGET: int = 27
MIN_SCORE: int = 8
MAX_SCORE: int = 15

POINT_COST_TABLE: Dict[int, int] = {
    8: 0,
    9: 1,
    10: 2,
    11: 3,
    12: 4,
    13: 5,
    14: 7,
    15: 9,
}

class PointBuyCalculator:
    total_budget: int = TOTAL_BUDGET
    min_score: int = MIN_SCORE
    max_score: int = MAX_SCORE
    cost_table: Dict[int, int] = POINT_COST_TABLE

    @classmethod
    def get_initial_scores(cls) -> Dict[str, int]:
        """Retorna las 6 características en el valor base de compra (8)."""
        return {"FUE": 8, "DES": 8, "CON": 8, "INT": 8, "SAB": 8, "CAR": 8}

    @classmethod
    def get_cost_for_score(cls, score: int) -> int:
        return cls.cost_table.get(score, 0)

    @classmethod
    def calculate_used_points(cls, scores: Dict[str, int]) -> int:
        """Calcula el total de puntos gastados según la tabla no lineal."""
        return sum(cls.cost_table.get(score, 0) for score in scores.values())

    @classmethod
    def get_remaining_points(cls, scores: Dict[str, int]) -> int:
        """Calcula los puntos restantes del presupuesto de 27."""
        return cls.total_budget - cls.calculate_used_points(scores)

    @classmethod
    def can_increment(cls, scores: Dict[str, int], ability: str) -> bool:
        """Verifica si es legal subir 1 punto la característica dada."""
        current = scores.get(ability, cls.min_score)
        if current >= cls.max_score:
            return False
        next_val = current + 1
        cost_diff = cls.cost_table[next_val] - cls.cost_table[current]
        return cls.get_remaining_points(scores) >= cost_diff

    @classmethod
    def can_decrement(cls, scores: Dict[str, int], ability: str) -> bool:
        """Verifica si es legal bajar 1 punto la característica dada."""
        current = scores.get(ability, cls.min_score)
        return current > cls.min_score

    @classmethod
    def increment(cls, scores: Dict[str, int], ability: str) -> bool:
        """Incrementa el valor si es válido y retorna True; en caso contrario False."""
        if cls.can_increment(scores, ability):
            scores[ability] = scores.get(ability, cls.min_score) + 1
            return True
        return False

    @classmethod
    def decrement(cls, scores: Dict[str, int], ability: str) -> bool:
        """Decrementa el valor si es válido y retorna True; en caso contrario False."""
        if cls.can_decrement(scores, ability):
            scores[ability] = scores.get(ability, cls.min_score) - 1
            return True
        return False
