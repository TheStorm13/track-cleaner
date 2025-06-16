import logging
from typing import List, Optional

import gpxpy
import gpxpy.gpx

logger = logging.getLogger("TrackMerger")


class TrackMerger:
    """Объединение нескольких GPX-треков в один с обработкой ошибок"""

    def merge_gpx_tracks(
            self,
            gpx_list: List[gpxpy.gpx.GPX],
            track_name: str = "Merged Track"
    ) -> Optional[gpxpy.gpx.GPX]:
        try:
            if not gpx_list:
                logger.warning("No tracks to merge")
                return None

            master_gpx = gpxpy.gpx.GPX()
            master_track = gpxpy.gpx.GPXTrack(name=track_name)
            master_gpx.tracks.append(master_track)

            for gpx in gpx_list:
                for track in gpx.tracks:
                    for segment in track.segments:
                        # Копируем сегмент целиком
                        new_segment = gpxpy.gpx.GPXTrackSegment()
                        new_segment.points = segment.points[:]  # копируем список точек
                        master_track.segments.append(new_segment)

            # Копируем метаданные из первого файла
            if metadata := gpx_list[0]:
                master_gpx.time = metadata.time
                master_gpx.name = track_name
                master_gpx.description = f"Merged from {len(gpx_list)} tracks"
                if metadata.creator:
                    master_gpx.creator = metadata.creator
                if metadata.link:
                    master_gpx.link = metadata.link

            total_points = sum(len(seg.points) for seg in master_track.segments)
            logger.info(f"Merged {len(gpx_list)} tracks with {total_points} points across multiple segments")
            return master_gpx

        except Exception as e:
            logger.error(f"Error merging tracks: {e}", exc_info=True)
            return None
