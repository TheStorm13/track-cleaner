import logging

import gpxpy
import gpxpy.gpx

logger = logging.getLogger(__name__)


class TrackMerger:
    """Класс для объединения нескольких GPX-треков в один."""

    def merge_gpx_tracks(
            self,
            gpx_list: list[gpxpy.gpx.GPX],
            track_name: str = "Merged Track",
    ) -> gpxpy.gpx.GPX | None:
        """Объединяет список GPX-треков в один трек.

        Args:
            gpx_list: Список GPX-треков для объединения.
            track_name: Имя для объединённого трека. По умолчанию "Merged Track".

        Returns:
            gpxpy.gpx.GPX: Объединённый GPX-трек, или None в случае ошибки.

        """
        if not gpx_list:
            logger.warning("No GPX tracks provided for merging.")
            return None

        try:
            master_gpx = self._initialize_master_gpx(gpx_list[0], track_name, len(gpx_list))
            master_track = gpxpy.gpx.GPXTrack(name=track_name)
            master_gpx.tracks.append(master_track)

            for gpx in gpx_list:
                self._append_segments_from_gpx(gpx, master_track)

            total_points = sum(len(seg.points) for seg in master_track.segments)
            logger.info(
                "Merged %d tracks into one with %d total points across %d segments",
                len(gpx_list),
                total_points,
                len(master_track.segments),
            )

            return master_gpx

        except Exception:
            logger.exception("Failed to merge GPX tracks")
        return None

    def _initialize_master_gpx(
            self,
            source_gpx: gpxpy.gpx.GPX,
            track_name: str,
            track_count: int,
    ) -> gpxpy.gpx.GPX:
        """Инициализирует новый GPX-трек с метаданными из исходного GPX.

        Args:
            source_gpx: Исходный GPX-трек, от которого будут взяты метаданные.
            track_name: Имя для нового трека.
            track_count: Количество треков, которые будут объединены.

        Returns:
            gpxpy.gpx.GPX: Новый GPX-трек с метаданными.

        """
        gpx = gpxpy.gpx.GPX()
        gpx.name = track_name
        gpx.description = f"Merged from {track_count} tracks"
        gpx.time = source_gpx.time

        if source_gpx.creator:
            gpx.creator = source_gpx.creator
        if source_gpx.link:
            gpx.link = source_gpx.link

        return gpx

    def _append_segments_from_gpx(
            self,
            gpx: gpxpy.gpx.GPX,
            target_track: gpxpy.gpx.GPXTrack,
    ) -> None:
        for track in gpx.tracks:
            for segment in track.segments:
                new_segment = gpxpy.gpx.GPXTrackSegment(points=segment.points[:])
                target_track.segments.append(new_segment)
