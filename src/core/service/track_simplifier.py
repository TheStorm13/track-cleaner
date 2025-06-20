import logging
from typing import Optional

import gpxpy
import gpxpy.gpx

from src.core.service.track_analyzer import TrackAnalyzer

logger = logging.getLogger(__name__)


class TrackSimplifier:
    """Упрощение трека путем сокращения точек с сохранением формы"""

    def __init__(self) -> None:
        self.distance_calculator = TrackAnalyzer()

    def simplify_track(
            self,
            gpx: gpxpy.gpx.GPX,
            min_distance: float,
            preserve_key_points: bool = True
    ) -> Optional[gpxpy.gpx.GPX]:
        if not gpx.tracks:
            logger.warning("GPX has no tracks to simplify.")
            return None

        try:
            simplified_gpx = self._copy_gpx_metadata(gpx)
            key_points = self._find_key_points(gpx) if preserve_key_points else set()

            for original_track in gpx.tracks:
                simplified_track = self._simplify_track(original_track, min_distance, key_points)
                simplified_gpx.tracks.append(simplified_track)

            self._log_reduction_stats(gpx, simplified_gpx)
            return simplified_gpx

        except Exception as e:
            logger.exception("Failed to simplify GPX track: %s", e)
            return None

    def _copy_gpx_metadata(self, gpx: gpxpy.gpx.GPX) -> gpxpy.gpx.GPX:
        simplified = gpxpy.gpx.GPX()
        simplified.name = gpx.name
        simplified.description = gpx.description
        simplified.creator = gpx.creator
        simplified.time = gpx.time
        simplified.link = gpx.link
        return simplified

    def _find_key_points(self, gpx: gpxpy.gpx.GPX) -> set[gpxpy.gpx.GPXTrackPoint]:
        key_points = set()
        for track in gpx.tracks:
            for segment in track.segments:
                if not segment.points:
                    continue
                key_points.add(segment.points[0])  # First
                key_points.add(segment.points[-1])  # Last
                highest_point = max(segment.points, key=lambda p: p.elevation or 0.0)
                key_points.add(highest_point)
        return key_points

    def _simplify_track(
            self,
            track: gpxpy.gpx.GPXTrack,
            min_distance: float,
            key_points: set[gpxpy.gpx.GPXTrackPoint]
    ) -> gpxpy.gpx.GPXTrack:
        simplified_track = gpxpy.gpx.GPXTrack()
        simplified_track.name = track.name
        simplified_track.description = track.description

        for segment in track.segments:
            simplified_segment = self._simplify_segment(segment, min_distance, key_points)
            if simplified_segment.points:
                simplified_track.segments.append(simplified_segment)

        return simplified_track

    def _simplify_segment(
            self,
            segment: gpxpy.gpx.GPXTrackSegment,
            min_distance: float,
            key_points: set[gpxpy.gpx.GPXTrackPoint]
    ) -> gpxpy.gpx.GPXTrackSegment:
        simplified_segment = gpxpy.gpx.GPXTrackSegment()

        if not segment.points:
            return simplified_segment

        last_point = segment.points[0]
        simplified_segment.points.append(last_point)

        for point in segment.points[1:]:
            if point in key_points:
                simplified_segment.points.append(point)
                last_point = point
                continue

            distance = self.distance_calculator.haversine_distance(
                last_point.latitude, last_point.longitude,
                point.latitude, point.longitude
            )

            if distance >= min_distance:
                simplified_segment.points.append(point)
                last_point = point

        return simplified_segment

    def _log_reduction_stats(self, original_gpx: gpxpy.gpx.GPX, simplified_gpx: gpxpy.gpx.GPX) -> None:
        original_points = sum(len(s.points) for t in original_gpx.tracks for s in t.segments)
        simplified_points = sum(len(s.points) for t in simplified_gpx.tracks for s in t.segments)

        if original_points == 0:
            logger.info("No points in original GPX for comparison.")
            return

        reduction_percent = (original_points - simplified_points) / original_points * 100
        logger.info(
            f"Simplified GPX track from {original_points} to {simplified_points} points "
            f"({reduction_percent:.1f}% reduction)"
        )
