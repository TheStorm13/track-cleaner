import gpxpy
import gpxpy.gpx
from geopy.distance import geodesic
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed


def distance(p1, p2):
    return geodesic((p1.latitude, p1.longitude), (p2.latitude, p2.longitude)).meters


def create_gpx(i, j, points):
    segment_points = points[i:j + 1]
    gpx_bad = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack()
    gpx_bad.tracks.append(track)
    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)
    segment.points.extend(segment_points)
    return gpx_bad


def process_segment_static(segment_points, max_path_km, close_threshold, min_path_length):
    n = len(segment_points)
    bad_gpx_list = []
    bad_ranges = []

    for i in range(n):
        total_distance = 0.0

        for j in range(i + 1, n):
            seg_dist = distance(segment_points[j - 1], segment_points[j])
            total_distance += seg_dist

            if total_distance > max_path_km:
                break

            if distance(segment_points[i], segment_points[j]) < close_threshold and total_distance > min_path_length:
                if any(max(i, r1) <= min(j, r2) for r1, r2 in bad_ranges):
                    continue
                gpx_bad = create_gpx(i, j, segment_points)
                bad_gpx_list.append(gpx_bad)
                bad_ranges.append((i, j))
                break

    return bad_gpx_list, bad_ranges


class TrackCutter:

    def extract_bad_segments(self, gpx, max_path_km=10000.0, close_threshold=30.0, min_path_length=200.0):
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
                    process_segment_static,
                    seg_points, max_path_km, close_threshold, min_path_length
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
