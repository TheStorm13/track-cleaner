# Поиск частей для обрезки GPX-файла
# Удаление частей которые были найдены
from concurrent.futures import ThreadPoolExecutor, as_completed

import gpxpy
import gpxpy.gpx
from geopy.distance import geodesic
from tqdm import tqdm


class TrackCutter:

    def distance(self, p1, p2):
        return geodesic((p1.latitude, p1.longitude), (p2.latitude, p2.longitude)).meters

    def process_segment(self, segment_points, max_path_km=10000.0, close_threshold=30.0, min_path_length=200.0):
        points = segment_points
        n = len(points)
        bad_gpx_list = []
        bad_ranges = []

        for i in range(n):
            total_distance = 0.0

            for j in range(i + 1, n):
                seg_dist = self.distance(points[j - 1], points[j])
                total_distance += seg_dist

                if total_distance > max_path_km:
                    break  # выходим, если отрезок слишком длинный (больше 1 км)

                # Проверяем замкнутость
                if self.distance(points[i], points[j]) < close_threshold and total_distance > min_path_length:
                    # Проверка на перекрытия
                    if any(max(i, r1) <= min(j, r2) for r1, r2 in bad_ranges):
                        continue

                    # Создаем отдельный GPX
                    gpx_bad = self.create_gpx(i, j, points)
                    bad_gpx_list.append(gpx_bad)
                    bad_ranges.append((i, j))
                    break  # идем к следующей точке

        return bad_gpx_list, bad_ranges

    def extract_bad_segments(self, gpx, max_path_km=1000.0, close_threshold=30.0, min_path_length=200.0) -> list[
        gpxpy.gpx.GPX]:
        all_segment_points = []

        # Собираем все сегменты
        for track in gpx.tracks:
            for segment in track.segments:
                all_segment_points.append(segment.points)

        bad_gpx_list = []
        bad_ranges = []

        # Параллельная обработка с прогресс-баром
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.process_segment, seg_points, max_path_km, close_threshold, min_path_length)
                for seg_points in all_segment_points
            ]

            # tqdm оборачивает итерацию по futures
            for future in tqdm(as_completed(futures), total=len(futures), desc="Обработка сегментов"):
                try:
                    gpx_list, ranges = future.result()
                    bad_gpx_list.extend(gpx_list)
                    bad_ranges.extend(ranges)
                except Exception as e:
                    print(f"Ошибка в одном из потоков: {e}")

        self.cut_ranges = bad_ranges
        return bad_gpx_list

    def create_gpx(self, i, j, points):
        segment_points = points[i:j + 1]
        gpx_bad = gpxpy.gpx.GPX()
        track = gpxpy.gpx.GPXTrack()
        gpx_bad.tracks.append(track)
        segment = gpxpy.gpx.GPXTrackSegment()
        track.segments.append(segment)
        segment.points.extend(segment_points)
        return gpx_bad
