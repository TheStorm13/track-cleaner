# ruff: noqa: PGH003
import logging
from datetime import UTC, datetime

import gpxpy.gpx

logger = logging.getLogger(__name__)


class TrackPreprocessor:
    """Сортировка треков по дате с обработкой отсутствующих метаданных."""

    @staticmethod
    def get_track_date(gpx: gpxpy.gpx.GPX) -> datetime:
        """Получение даты трека с резервными вариантами.

        Приоритет источников даты:
        1. Время начала трека (time_bounds.start_time).
        2. Первое доступное время в точках трека.
        3. Текущее время (если метаданные отсутствуют).

        Args:
            gpx (gpxpy.gpx.GPX): GPX-объект для анализа.

        Returns:
            datetime: Дата трека. Если метаданные отсутствуют, возвращается текущее время.

        """
        try:
            # Попытка 1: Использовать время начала трека
            if (time_bounds := gpx.get_time_bounds()) and (start_time := time_bounds.start_time):
                return start_time  # type: ignore

            # Попытка 2: Использовать первое доступное время в точках
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        if point.time:
                            return point.time # type: ignore

        except Exception:
            logger.exception("Error getting track date: %s")

        # Попытка 3: Использовать текущее время
        return datetime.now(UTC)

    def sort_by_date(
            self,
            gpx_list: list[gpxpy.gpx.GPX],
            is_reverse: bool = True,
    ) -> list[gpxpy.gpx.GPX]:
        """Сортировка списка GPX-треков по дате.

        Args:
            gpx_list (list[gpxpy.gpx.GPX]): Список GPX-объектов для сортировки.
            is_reverse (bool): Если True, сортировка будет в обратном порядке (по убыванию).
                По умолчанию True.

        Returns:
            list[gpxpy.gpx.GPX]: Отсортированный список GPX-объектов.

        """
        try:
            return sorted(
                gpx_list,
                key=self.get_track_date,
                reverse=is_reverse,
            )
        except Exception:
            logger.exception("Error sorting tracks: %s")
        return gpx_list
