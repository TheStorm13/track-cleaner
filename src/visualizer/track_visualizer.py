import logging
from pathlib import Path

import branca.colormap as cm
import folium
import gpxpy.gpx
import numpy as np
from folium import DivIcon
from folium.plugins import MeasureControl

from config import BASE_PATH
from src.utils.gpx_utils import GpxUtils

logger = logging.getLogger(__name__)


class TrackVisualizer:
    """Класс для визуализации GPX-треков на интерактивных картах."""

    DEFAULT_ZOOM: int = 8
    DEFAULT_COLORS: list[str] = ["blue", "green"]
    MIN_POINTS_FOR_SEGMENT: int = 2  # Константа для минимального количества точек

    def __init__(self, base_path: Path = BASE_PATH, default_zoom: int = DEFAULT_ZOOM) -> None:
        """Инициализация визуализатора.

        Args:
            base_path (Path): Базовый путь для сохранения карт.
            default_zoom (int): Уровень масштабирования карты по умолчанию.

        """
        self.default_zoom = default_zoom
        self.color_maps = {
            "elevation": cm.linear.YlOrRd_09,
            "speed": cm.linear.PuBuGn_09,
            "slope": cm.linear.RdYlGn_11,
        }

        self.maps_dir = base_path / "maps"
        self.maps_dir.mkdir(exist_ok=True)

        logger.info("GPX visualizer initialized")

    def _create_base_map(self, center: tuple[float, float]) -> folium.Map:
        """Создает базовую карту с заданным центром.

        Args:
            center (tuple[float, float]): Координаты центра карты (широта, долгота).

        Returns:
            folium.Map: Объект карты Folium.

        """
        return folium.Map(
            location=center,
            zoom_start=self.default_zoom,
            control_scale=True,
        )

    @staticmethod
    def _calculate_center(gpx: gpxpy.gpx.GPX) -> tuple[float, float]:
        """Вычисляет центр карты на основе точек GPX-трека.

        Args:
            gpx (gpxpy.gpx.GPX): GPX-объект.

        Returns:
            tuple[float, float]: Координаты центра (широта, долгота).

        """
        lats = []
        lons = []

        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    lats.append(point.latitude)
                    lons.append(point.longitude)

        if not lats or not lons:
            return (0, 0)

        return (np.mean(lats), np.mean(lons))

    def _collect_points(self, gpx_objects: list[gpxpy.gpx.GPX]) -> list[gpxpy.gpx.GPXTrackPoint]:
        """Собирает все точки из списка GPX-объектов."""
        points: list[gpxpy.gpx.GPXTrackPoint] = []
        for gpx in gpx_objects:
            for track in gpx.tracks:
                for segment in track.segments:
                    points.extend(segment.points)
        return points

    def plot_single_track(
            self,
            gpx: gpxpy.gpx.GPX,
            map_title: str = "GPX Track",
            color_by: str = "elevation",
            line_weight: int = 3,
    ) -> folium.Map | None:
        """Визуализирует один GPX-трек с окрашиванием по сегментам.

        Args:
            gpx (gpxpy.gpx.GPX): GPX-объект для визуализации.
            map_title (str): Заголовок карты.
            color_by (str): Критерий окрашивания трека ("elevation", "speed", "slope").
            line_weight (int): Толщина линий трека.

        Returns:
            folium.Map: Объект карты Folium.

        """
        try:
            center = self._calculate_center(gpx)
            if center == (0, 0):
                logger.error("No valid points for center calculation")
                return None

            folium_map = self._create_base_map(center)
            folium_map.title = map_title

            # Добавление элементов управления
            folium_map.add_child(MeasureControl())
            folium_map.add_child(folium.LatLngPopup())

            # Цвета для сегментов
            colors = self.DEFAULT_COLORS * 10  # Повторяем, если мало цветов

            # Обработка всех треков и сегментов
            track_index = 0
            for track in gpx.tracks:
                for segment in track.segments:
                    if len(segment.points) < self.MIN_POINTS_FOR_SEGMENT:
                        continue

                    # Создаем FeatureGroup для сегмента
                    group_name = f"Segment {track_index + 1}"
                    track_group = folium.FeatureGroup(name=group_name)
                    folium_map.add_child(track_group)

                    # Получаем координаты и значения для окраски
                    locations, _values = self._process_segment(segment, color_by)

                    # Выбираем цвет
                    color = colors[track_index % len(colors)]

                    folium.PolyLine(
                        locations=locations,
                        color=color,
                        weight=line_weight,
                        opacity=0.8,
                        popup=group_name,
                    ).add_to(track_group)

                    track_index += 1

            # Управление слоями
            folium.LayerControl().add_to(folium_map)

            return folium_map

        except Exception:
            logger.exception("Error visualizing track: %s")
        return None

    def _process_segment(
            self, segment: gpxpy.gpx.GPXTrackSegment, color_by: str,
    ) -> tuple[list[list[float]], list[float]]:
        """Обрабатывает сегмент трека для визуализации.

        Args:
            segment (gpxpy.gpx.GPXTrackSegment): Сегмент GPX-трека.
            color_by (str): Критерий окрашивания ("elevation", "speed", "slope").

        Returns:
            tuple[list[list[float]], list[float]]: Список координат и значений для окрашивания.

        """
        locations = []
        values = []
        prev_point = None

        for point in segment.points:
            locations.append([point.latitude, point.longitude])

            # Вычисление значений в зависимости от критерия
            if color_by == "elevation":
                values.append(point.elevation or 0)
            elif color_by == "speed" and prev_point:
                if point.time and prev_point.time:
                    time_diff = (point.time - prev_point.time).total_seconds()
                    dist = GpxUtils.distance_between_points(prev_point, point)
                    values.append((dist / time_diff) * 3.6 if time_diff > 0 else 0)  # км/ч
                else:
                    values.append(0)
            elif color_by == "slope" and prev_point and point.elevation is not None and prev_point.elevation is not None:
                dist = GpxUtils.distance_between_points(prev_point, point)
                elev_diff = point.elevation - prev_point.elevation
                values.append((elev_diff / dist) * 100 if dist > 0 else 0)  # % уклона
            else:
                values.append(0)

            prev_point = point

        return locations, values

    def save_map(self, folium_map: folium.Map, file_path: str | Path) -> bool:
        """Сохраняет карту в HTML-файл.

        Args:
            folium_map (folium.Map): Объект карты Folium.
            file_path (str or Path): Путь для сохранения файла.

        Returns:
            bool: True, если карта успешно сохранена, иначе False.

        """
        try:
            path = self.maps_dir / Path(file_path)
            folium_map.save(str(path))
            logger.info("Map saved to: %s", path.resolve())
            return True
        except Exception:
            logger.exception("Error saving map: %s")
            return False

    def plot_track_with_bad_segments(
            self,
            base_gpx: gpxpy.gpx.GPX,
            bad_segments: list[gpxpy.gpx.GPX],
            base_color: str = "blue",
            bad_segments_color: str = "red",
            line_weight: int = 4,
    ) -> folium.Map | None:
        """Визуализирует трек с выделением плохих сегментов.

        Args:
            base_gpx (gpxpy.gpx.GPX): Основной GPX-трек.
            bad_segments (list[gpxpy.gpx.GPX]): Список GPX-треков с плохими сегментами.
            base_color (str): Цвет основного трека.
            bad_segments_color (str): Цвет плохих сегментов.
            line_weight (int): Толщина линий трека.

        Returns:
            folium.Map | None: Объект карты Folium или None в случае ошибки.

        """
        try:
            all_points = self._collect_points([base_gpx, *bad_segments])
            if not all_points:
                logger.warning("No points found for visualization")
                return None

            # Создаем базовую карту
            center = (np.mean([p.latitude for p in all_points]),
                      np.mean([p.longitude for p in all_points]))
            folium_map = self._create_base_map(center)

            # Добавляем основной трек
            base_group = folium.FeatureGroup(name="Основной трек", show=True)
            folium_map.add_child(base_group)

            for track in base_gpx.tracks:
                for segment in track.segments:
                    if len(segment.points) < self.MIN_POINTS_FOR_SEGMENT:
                        continue
                    locations = [[p.latitude, p.longitude] for p in segment.points]
                    folium.PolyLine(
                        locations=locations,
                        color=base_color,
                        weight=line_weight,
                        opacity=0.7,
                        popup="Основной трек",
                    ).add_to(base_group)

            # Добавляем плохие сегменты
            for i, bad_segment in enumerate(bad_segments, 1):
                group_name = f"Плохой сегмент {i}"
                segment_group = folium.FeatureGroup(name=group_name, show=True)
                folium_map.add_child(segment_group)

                for track in bad_segment.tracks:
                    for segment in track.segments:
                        locations = [[p.latitude, p.longitude] for p in segment.points]
                        folium.PolyLine(
                            locations=locations,
                            color=bad_segments_color,
                            weight=line_weight + 1,
                            opacity=0.9,
                            popup=group_name,
                        ).add_to(segment_group)
                        # Находим центр сегмента для подписи
                        center_lat = np.mean([p.latitude for p in segment.points])
                        center_lon = np.mean([p.longitude for p in segment.points])

                        # Добавляем невидимый маркер с текстом
                        folium.map.Marker(
                            [center_lat, center_lon],
                            icon=DivIcon(
                                icon_size=(170, 36),
                                icon_anchor=(0, 0),
                                html=f"""
                                        <div style="
                                            font-size: 12pt;
                                            color: black;
                                            background-color: rgba(255, 255, 255, 0.7);
                                            padding: 4px 8px;
                                            border-radius: 4px;
                                            font-weight: bold;
                                            white-space: nowrap;">
                                            {group_name}
                                        </div>""",
                            ),
                        ).add_to(folium_map)

            # Добавляем контроль слоев
            folium.LayerControl().add_to(folium_map)

            return folium_map

        except Exception:
            logger.exception("Ошибка при визуализации трека: %s")
        return None

    def _add_track_to_map(
            self,
            folium_map: folium.Map,
            gpx: gpxpy.gpx.GPX,
            group_name: str,
            color: str,
            line_weight: int,
    ) -> None:
        """Добавляет GPX-трек на карту в указанную группу.

        Args:
            folium_map (folium.Map): Объект карты Folium.
            gpx (gpxpy.gpx.GPX): GPX-трек для добавления.
            group_name (str): Название группы слоя.
            color (str): Цвет трека.
            line_weight (int): Толщина линий трека.

        """
        group = folium.FeatureGroup(name=group_name, show=True)
        folium_map.add_child(group)

        for track in gpx.tracks:
            for segment in track.segments:
                if len(segment.points) < self.MIN_POINTS_FOR_SEGMENT:
                    continue
                locations = [[p.latitude, p.longitude] for p in segment.points]
                folium.PolyLine(
                    locations=locations,
                    color=color,
                    weight=line_weight,
                    opacity=0.7,
                    popup=group_name,
                ).add_to(group)

    def plot_compare_tracks(
            self,
            gpx1: gpxpy.gpx.GPX,
            gpx2: gpxpy.gpx.GPX,
            color1: str = "red",
            color2: str = "blue",
            line_weight: int = 4,
    ) -> folium.Map | None:
        """Сравнивает два GPX-трека на одной карте.

        Args:
            gpx1 (gpxpy.gpx.GPX): Первый GPX-трек.
            gpx2 (gpxpy.gpx.GPX): Второй GPX-трек.
            color1 (str): Цвет первого трека.
            color2 (str): Цвет второго трека.
            line_weight (int): Толщина линий трека.

        Returns:
            folium.Map | None: Объект карты Folium или None в случае ошибки.

        """
        try:
            # Собираем все точки для вычисления центра карты
            all_points = []
            for gpx in [gpx1, gpx2]:
                for track in gpx.tracks:
                    for segment in track.segments:
                        all_points.extend(segment.points)

            if not all_points:
                logger.warning("No points found for visualization")
                return None

            # Создаем базовую карту
            center = (np.mean([p.latitude for p in all_points]),
                      np.mean([p.longitude for p in all_points]))
            folium_map = self._create_base_map(center)

            # Добавляем треки на карту
            self._add_track_to_map(folium_map, gpx1, "Трек 1", color1, line_weight)
            self._add_track_to_map(folium_map, gpx2, "Трек 2", color2, line_weight)

            # Добавляем контроль слоев
            folium.LayerControl().add_to(folium_map)

            return folium_map

        except Exception:
            logger.exception("Ошибка при визуализации сравнения треков: %s")
        return None
