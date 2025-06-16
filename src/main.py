import logging
import pathlib

from src.core.service.track_cutter import TrackCutter
from src.core.service.track_merger import TrackMerger
from src.core.service.track_preprocessor import TrackPreprocessor
from src.core.service.track_simplifier import TrackSimplifier
from src.core.service.track_validator import TrackValidator
from src.core.storage.gpx_loader import GPXStorage
from src.ui.io import IO
from src.visualizer.track_visualizer import TrackVisualizer

# Настройка логирования
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")


def main():
    # Инициализация менеджера файлов


    base_path = pathlib.Path(__file__).parent

    gpx_dir = base_path / "gpx_files"
    gpx_dir.mkdir(exist_ok=True)

    gpx_row_dir = base_path / "gpx_files" / "raw"
    gpx_row_dir.mkdir(exist_ok=True)

    manager = GPXStorage(base_path)
    # Поиск и загрузка GPX-файлов

    IO.input_path()
    gpx_files = manager.find_gpx_files(gpx_dir)
    gpx_objects = []

    for file_path in gpx_files:
        if gpx := manager.load_gpx(file_path):
            gpx_objects.append(gpx)

    if not gpx_objects:
        logger.error("No valid GPX files loaded. Exiting.")
        return

    # Сортировка треков
    sorter = TrackPreprocessor()
    sorted_tracks = sorter.sort_by_date(gpx_objects)

    # Объединение первых трех треков
    merger = TrackMerger()
    merged_gpx = merger.merge_gpx_tracks(sorted_tracks)

    if not merged_gpx:
        logger.error("Failed to merge tracks. Exiting.")
        return

    # Анализ расстояний
    distance_checker = TrackValidator()
    max_dist, points = distance_checker.calculate_max_distance(merged_gpx)

    if max_dist > 0:
        logger.info(f"Max distance between points: {max_dist:.2f} meters")
        if points:
            p1, p2 = points
            logger.debug(f"Between points: ({p1.latitude},{p1.longitude}) and ({p2.latitude},{p2.longitude})")

    # Упрощение трека
    simplifier = TrackSimplifier()
    simplified_gpx = simplifier.simplify_track(merged_gpx, min_distance=15.0)

    # Сохранение результатов
    if simplified_gpx:
        manager.save_gpx(merged_gpx, "merged_tracks.gpx")
        manager.save_gpx(simplified_gpx, "simplified_track.gpx")
    else:
        logger.warning("Simplification failed, saving only merged track")
        manager.save_gpx(merged_gpx, "merged_tracks.gpx")

    visualizer = TrackVisualizer(base_path)

    cutter = TrackCutter()
    bad_segments = cutter.extract_bad_segments(simplified_gpx)

    # Визуализация одного трека
    track_map = visualizer.plot_track_with_bad_segments(
        base_gpx=simplified_gpx,
        bad_segments=bad_segments
    )

    if track_map:
        visualizer.save_map(track_map, "track_with_bad_segments.html")

    bad_segments_input = IO.input_bad_segments()

    cutting_track = cutter.cut_segments(
        simplified_gpx,
        bad_segments=bad_segments,
        bad_segments_indexes=bad_segments_input
    )

    track_map = visualizer.plot_single_track(cutting_track)

    if track_map:
        visualizer.save_map(track_map, "cutting_track.html")

    if cutting_track:
        manager.save_gpx(cutting_track, "cutting_track.gpx")
    else:
        logger.warning("Cutting failed, saving only merged track")


if __name__ == "__main__":
    try:
        main()

    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
