
from haversine import Unit, haversine


class TrackAnalyzer:
    """Анализатор треков, предоставляющий методы для вычисления расстояний."""

    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Вычисляет расстояние между двумя точками по их координатам.

        Args:
            lat1 (float): Широта первой точки.
            lon1 (float): Долгота первой точки.
            lat2 (float): Широта второй точки.
            lon2 (float): Долгота второй точки.

        Returns:
            float: Расстояние между точками в метрах.

        """
        return float(haversine((lat1, lon1), (lat2, lon2), unit=Unit.METERS))
