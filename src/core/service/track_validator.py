# Проверять насколько отдаллены друг от друга точки в треке
import logging
from math import radians, cos, sin, asin, sqrt
from typing import Optional, Tuple

import gpxpy.gpx

logger = logging.getLogger("TrackValidator")


class TrackValidator:
    """Расчет расстояний между точками в треке"""

    @staticmethod
    def haversine_distance(
            lat1: float,
            lon1: float,
            lat2: float,
            lon2: float
    ) -> float:
        """Расчет расстояния между двумя точками (в метрах) по формуле Хаверсина"""
        try:
            # Константа радиуса Земли в метрах
            R = 6371.0088 * 1000

            # Преобразование градусов в радианы
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)

            # Формула Хаверсина
            a = (sin(dlat / 2) ** 2 +
                 cos(radians(lat1)) *
                 cos(radians(lat2)) *
                 sin(dlon / 2) ** 2)

            return R * 2 * asin(sqrt(a))
        except ValueError as e:
            logger.error(f"Invalid coordinate values: {e}")
            return 0.0

    def calculate_max_distance(self, gpx: gpxpy.gpx.GPX) -> Tuple[float, Optional[tuple]]:
        """Поиск максимального расстояния между соседними точками"""
        max_distance = 0.0
        max_points = None

        try:
            for track in gpx.tracks:
                for segment in track.segments:
                    if len(segment.points) < 2:
                        continue

                    for i in range(1, len(segment.points)):
                        p1 = segment.points[i - 1]
                        p2 = segment.points[i]

                        distance = self.haversine_distance(
                            p1.latitude, p1.longitude,
                            p2.latitude, p2.longitude
                        )

                        if distance > max_distance:
                            max_distance = distance
                            max_points = (p1, p2)

            logger.debug(f"Max distance calculated: {max_distance:.2f} meters")
            return max_distance, max_points

        except Exception as e:
            logger.error(f"Error calculating distances: {e}", exc_info=True)
            return 0.0, None
