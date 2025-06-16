'''
1. Получить путь до папки с треками
2. Получить список треков в папке
3. Загрузить треки
4. Отсортировать треки по дате
5. Соеденить треки
5.1 Проверить, что точки в треке
6. Сохранить объединённый трек в файл
7. Предложить пользователю сократить количество точек
8. Найти все отростки в треке
9. Предложить пользователю удалить отростки
10. Сохранить трек без отростков
'''
import logging
from pathlib import Path

from src.core.service.track_cutter import TrackCutter
from src.core.service.track_merger import TrackMerger
from src.core.service.track_preprocessor import TrackPreprocessor
from src.core.service.track_simplifier import TrackSimplifier
from src.core.service.track_validator import TrackValidator
from src.core.storage.gpx_loader import GPXStorage
from src.visualizer.track_visualizer import TrackVisualizer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gpx_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")


def main():
    # Инициализация менеджера файлов
    manager = GPXStorage(storage_dir="processed_tracks")

    # Поиск и загрузка GPX-файлов
    gpx_files = manager.find_gpx_files(Path.home() / "Downloads" / "track")
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

    visualizer = TrackVisualizer(tiles="Stamen Terrain", default_zoom=10)

    cutter = TrackCutter()
    bad_segments = cutter.extract_bad_segments(simplified_gpx)



    # Визуализация одного трека
    track_map = visualizer.plot_track_with_loops(
        base_gpx=simplified_gpx,
        loops=bad_segments
    )
    # track_map = visualizer.plot_single_track(simplified_gpx)

    if track_map:
        visualizer.save_map(track_map, "single_track.html")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
