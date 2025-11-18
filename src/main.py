import copy
import logging

from config import BASE_PATH
from src.core.service.track_cutter import TrackCutter
from src.core.service.track_merger import TrackMerger
from src.core.service.track_preprocessor import TrackPreprocessor
from src.core.service.track_simplifier import TrackSimplifier
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
    # Инициализация основных компонентов приложения
    base_path = BASE_PATH
    manager = GPXStorage(base_path)
    sorter = TrackPreprocessor()
    merger = TrackMerger()
    simplifier = TrackSimplifier()
    cutter = TrackCutter()
    visualizer = TrackVisualizer(base_path)

    # Вывод информации о приложении и настройках
    IO.print_app_info()
    IO.print_path_info()
    simplification, min_length, max_length, threshold = IO.input_cleaning_parameters()

    # Поиск и загрузка GPX-файлов
    gpx_files = manager.find_gpx_files()
    gpx_objects = []

    for file_path in gpx_files:
        if gpx := manager.load_gpx(file_path):
            gpx_objects.append(gpx)

    if not gpx_objects:
        logger.error("No valid GPX files loaded. Exiting.")
        return

    # Сортировка треков
    sorted_tracks = sorter.sort_by_date(gpx_objects)

    # Объединение первых трех треков
    merged_track = merger.merge_gpx_tracks(sorted_tracks)

    if not merged_track:
        logger.error("Failed to merge tracks. Exiting.")
        return

    manager.save_gpx(merged_track, "merged_tracks.gpx")
    print("Треки успешно объединены и сохранены в 'merged_tracks.gpx'.")

    track_map = visualizer.plot_single_track(merged_track)
    visualizer.save_map(track_map, "track_merged.html")
    print("Трек успешно упрощён и сохранён в 'merged_track.gpx'. ")

    # Упрощение трека с заданным уровнем точности
    simplified_track = simplifier.simplify_track(merged_track, min_distance=simplification)
    manager.save_gpx(simplified_track, "simplified_track.gpx")

    track_map = visualizer.plot_single_track(simplified_track)

    visualizer.save_map(track_map, "track_simplified.html")
    print("Трек успешно упрощён и сохранён в 'simplified_track.gpx'. ")

    # Поиск плохих сегментов
    bad_segments = cutter.extract_bad_segments(simplified_track, threshold, min_length, max_length)

    track_map = visualizer.plot_track_with_bad_segments(
        base_gpx=simplified_track,
        bad_segments=bad_segments
    )

    visualizer.save_map(track_map, "track_with_bad_segments.html")

    # Выбор плохих сегментов трека для удаления
    bad_segments_input = IO.input_bad_segments(len(bad_segments))

    cutting_track = cutter.cut_segments(
        copy.deepcopy(simplified_track),
        bad_segments=bad_segments,
        bad_segments_indexes=bad_segments_input
    )

    track_map = visualizer.plot_single_track(cutting_track)

    visualizer.save_map(track_map, "result_track.html")
    manager.save_gpx(cutting_track, "result_track.gpx")

    compare_tracks_map = visualizer.plot_compare_tracks(
        simplified_track,
        cutting_track
    )

    visualizer.save_map(compare_tracks_map, "compare_simplified_and_result.html")

    compare_tracks_map = visualizer.plot_compare_tracks(
        merged_track,
        cutting_track
    )

    visualizer.save_map(compare_tracks_map, "compare_merged_and_result.html")

    print(f"Удаление плохих сегментов завершено. Удалено {len(bad_segments_input)} сегментов."
          "Результат можно посмотреть в 'result_track.html'. "
          "Результат сохранён в 'result_track.gpx'.")


if __name__ == "__main__":
    try:
        main()

    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
