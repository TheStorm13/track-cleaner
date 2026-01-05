from math import asin, cos, radians, sin, sqrt

import gpxpy


class GpxUtils:
    """Класс с утилитами для работы с GPX-данными."""

    @staticmethod
    def distance_between_points(point1: gpxpy.gpx.GPXTrackPoint,
                                point2: gpxpy.gpx.GPXTrackPoint,
                                ) -> float:
        """Расчет расстояния между двумя точками (в метрах).

        Args:
            point1: Первая точка (широта и долгота).
            point2: Вторая точка (широта и долгота).

        """
        # Преобразование градусов в радианы
        lat1, lon1 = radians(point1.latitude), radians(point1.longitude)
        lat2, lon2 = radians(point2.latitude), radians(point2.longitude)

        # Разница широт и долгот
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Формула гаверсинуса
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2

        # Расстояние в метрах (средний радиус Земли)
        earth_radius_meters = 6_371_000
        return earth_radius_meters * 2 * asin(sqrt(a))

    @staticmethod
    def create_gpx(i: int, j: int, points: list[gpxpy.gpx.GPXTrackPoint]) -> gpxpy.gpx.GPX:
        """Создает новый GPX объект с сегментом, содержащим точки от i до j.

        Args:
            i (int): Начальный индекс сегмента.
            j (int): Конечный индекс сегмента.
            points (List[gpxpy.gpx.GPXTrackPoint]): Список точек, из которых будет создан сегмент.

        Returns:
            gpxpy.gpx.GPX: Новый GPX объект с указанным сегментом.

        """
        segment_points = points[i:j + 1]
        gpx_bad = gpxpy.gpx.GPX()
        track = gpxpy.gpx.GPXTrack()
        gpx_bad.tracks.append(track)
        segment = gpxpy.gpx.GPXTrackSegment()
        track.segments.append(segment)
        segment.points.extend(segment_points)
        return gpx_bad
