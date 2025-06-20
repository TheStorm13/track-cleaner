# После получения треков, отсортировать их по времени
import logging
from datetime import datetime, timezone

import gpxpy.gpx

logger = logging.getLogger(__name__)


class TrackPreprocessor:
    """Сортировка треков по дате с обработкой отсутствующих метаданных"""

    @staticmethod
    def get_track_date(gpx: gpxpy.gpx.GPX) -> datetime:
        """Получение даты трека с резервными вариантами"""
        try:
            # Попытка 1: Использовать время начала трека
            if time_bounds := gpx.get_time_bounds():
                if start_time := time_bounds.start_time:
                    return start_time

            # Попытка 2: Использовать первое доступное время в точках
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        if point.time:
                            return point.time

            # Попытка 3: Использовать время создания файла
            return datetime.now(timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)

    def sort_by_date(
            self,
            gpx_list: list[gpxpy.gpx.GPX],
            reverse: bool = True
    ) -> list[gpxpy.gpx.GPX]:
        """Сортировка списка GPX-треков по дате"""
        try:
            return sorted(
                gpx_list,
                key=self.get_track_date,
                reverse=reverse
            )
        except Exception as e:
            logger.error(f"Error sorting tracks: {e}", exc_info=True)
            return gpx_list
