import logging
from typing import Optional

import gpxpy
import gpxpy.gpx

from src.core.service.track_validator import TrackValidator

logger = logging.getLogger("TrackSimplifier")


class TrackSimplifier:
    """Упрощение трека путем сокращения точек с сохранением формы"""

    def __init__(self):
        self.distance_calculator = TrackValidator()

    def simplify_track(
            self,
            gpx: gpxpy.gpx.GPX,
            min_distance: float = 10.0,
            preserve_key_points: bool = True
    ) -> Optional[gpxpy.gpx.GPX]:
        """
        Упрощение трека с минимальным расстоянием между точками
        min_distance: минимальное расстояние между точками в метрах
        preserve_key_points: сохранять первую/последнюю и высшие точки
        """
        try:
            if not gpx.tracks:
                logger.warning("No tracks to simplify")
                return None

            simplified_gpx = gpxpy.gpx.GPX()

            # Копирование метаданных
            simplified_gpx.name = gpx.name
            simplified_gpx.description = gpx.description
            simplified_gpx.creator = gpx.creator
            simplified_gpx.time = gpx.time
            simplified_gpx.link = gpx.link

            # Поиск ключевых точек для сохранения (если требуется)
            key_points = set()
            if preserve_key_points:
                for track in gpx.tracks:
                    for segment in track.segments:
                        if segment.points:
                            # Первая и последняя точки
                            key_points.add(segment.points[0])
                            key_points.add(segment.points[-1])

                            # Самая высокая точка
                            highest_point = max(
                                segment.points,
                                key=lambda p: p.elevation or 0
                            )
                            key_points.add(highest_point)

            for original_track in gpx.tracks:
                new_track = gpxpy.gpx.GPXTrack()
                new_track.name = original_track.name
                new_track.description = original_track.description
                simplified_gpx.tracks.append(new_track)

                for segment in original_track.segments:
                    new_segment = gpxpy.gpx.GPXTrackSegment()

                    if not segment.points:
                        continue

                    # Всегда добавляем первую точку
                    last_point = segment.points[0]
                    new_segment.points.append(last_point)

                    # Пропускаем точки, если они слишком близко
                    for point in segment.points[1:]:
                        # Всегда добавляем ключевые точки
                        if preserve_key_points and point in key_points:
                            new_segment.points.append(point)
                            last_point = point
                            continue

                        distance = self.distance_calculator.haversine_distance(
                            last_point.latitude, last_point.longitude,
                            point.latitude, point.longitude
                        )

                        # Добавляем точку только если расстояние превышает порог
                        if distance >= min_distance:
                            new_segment.points.append(point)
                            last_point = point

                    # Добавляем сегмент только если в нем есть точки
                    if new_segment.points:
                        new_track.segments.append(new_segment)

            original_points = sum(len(seg.points) for track in gpx.tracks for seg in track.segments)
            simplified_points = sum(len(seg.points) for track in simplified_gpx.tracks for seg in track.segments)
            reduction = (original_points - simplified_points) / original_points * 100

            logger.info(
                f"Simplified track: {original_points} -> {simplified_points} points "
                f"({reduction:.1f}% reduction)"
            )
            return simplified_gpx

        except Exception as e:
            logger.error(f"Error simplifying track: {e}", exc_info=True)
            return None
