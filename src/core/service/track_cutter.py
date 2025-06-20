import logging
from concurrent.futures import ProcessPoolExecutor, as_completed

import gpxpy.gpx
from tqdm import tqdm

from src.utils.gpx_utils import GpxUtils

logger = logging.getLogger(__name__)


class TrackCutter:
    def process_segment_static(self,
                               segment_points,
                               loop_closure_threshold_m: float,
                               min_closed_loop_length_km: float,
                               max_closed_loop_length_km: float
                               ) -> tuple[list[gpxpy.gpx.GPX], list[tuple[int, int]]]:
        """
        Обрабатывает один сегмент трека для поиска замыкающихся петель.

        Args:
            segment_points: список точек сегмента трека
            loop_closure_threshold_m: расстояние в метрах, при котором считается, что петля замкнулась
            min_closed_loop_length_km: минимальная длина замыкающей петли в километрах
            max_closed_loop_length_km: максимальная длина замыкающей петли в километрах

        Returns:
            tuple: список плохих GPX-сегментов и список диапазонов индексов, где найдены замыкающиеся петли
        """
        n = len(segment_points)
        bad_gpx_list = []
        bad_ranges = []

        for i in range(n):
            total_distance = 0.0

            for j in range(i + 1, n):
                seg_dist = GpxUtils.distance_between_points(segment_points[j - 1], segment_points[j])
                total_distance += seg_dist

                if total_distance > max_closed_loop_length_km:
                    break

                if GpxUtils.distance_between_points(segment_points[i],
                                                    segment_points[
                                                        j]) < loop_closure_threshold_m and total_distance > min_closed_loop_length_km:
                    if any(max(i, r1) <= min(j, r2) for r1, r2 in bad_ranges):
                        continue
                    gpx_bad = GpxUtils.create_gpx(i, j, segment_points)
                    bad_gpx_list.append(gpx_bad)
                    bad_ranges.append((i, j))
                    break

        return bad_gpx_list, bad_ranges

    def extract_bad_segments(self,
                             gpx: gpxpy.gpx.GPX,
                             loop_closure_threshold_m: float,
                             min_closed_loop_length_km: float,
                             max_closed_loop_length_km: float
                             ) -> list[gpxpy.gpx.GPX]:
        """


        Args:
            gpx:
            max_closed_loop_length_km:
            loop_closure_threshold_m:
            min_closed_loop_length_km:

        Returns:

        """
        all_segment_points = []

        for track in gpx.tracks:
            for segment in track.segments:
                all_segment_points.append(segment.points)

        bad_gpx_list = []
        bad_ranges = []

        # Используем ProcessPoolExecutor для распараллеливания CPU-bound задач
        with ProcessPoolExecutor() as executor:
            futures = [
                executor.submit(
                    self.process_segment_static,
                    seg_points, loop_closure_threshold_m, min_closed_loop_length_km, max_closed_loop_length_km
                )
                for seg_points in all_segment_points
            ]

            for future in tqdm(as_completed(futures), total=len(futures), desc="Обработка сегментов"):
                try:
                    gpx_list, ranges = future.result()
                    bad_gpx_list.extend(gpx_list)
                    bad_ranges.extend(ranges)
                except Exception as e:
                    print(f"Ошибка в одном из процессов: {e}")

        self.cut_ranges = bad_ranges
        return bad_gpx_list

    def cut_segments(self,
                     gpx: gpxpy.gpx.GPX,
                     bad_segments: list[gpxpy.gpx.GPX],
                     bad_segments_indexes: list[int]
                     ) -> gpxpy.gpx.GPX:
        """

        Args:
            gpx:
            bad_segments:
            bad_segments_indexes:

        Returns:

        """
        # Собираем все "плохие" точки из указанных индексов
        bad_points = set()

        for index in bad_segments_indexes:
            i = index - 1
            if 0 <= i < len(bad_segments):
                bad_gpx = bad_segments[i]
                for track in bad_gpx.tracks:
                    for segment in track.segments:
                        for point in segment.points:
                            # Добавляем координаты (широта, долгота, высота) в множество
                            bad_points.add((point.latitude, point.longitude, point.elevation))

        # Удаляем эти точки из оригинального gpx
        for track in gpx.tracks:
            for segment in track.segments:
                segment.points = [
                    pt for pt in segment.points
                    if (pt.latitude, pt.longitude, pt.elevation) not in bad_points
                ]

        return gpx
