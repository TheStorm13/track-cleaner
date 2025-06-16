import logging
import pathlib
from pathlib import Path
from typing import List
from typing import Optional, Tuple

import branca.colormap as cm
import folium
import gpxpy.gpx
import numpy as np
from folium import DivIcon
from folium.plugins import MeasureControl

logger = logging.getLogger("GPXVisualizer")


class TrackVisualizer:
    """Класс для визуализации GPX-треков на интерактивных картах"""

    DEFAULT_TILES = "OpenStreetMap"
    DEFAULT_ZOOM = 8
    DEFAULT_COLORS = ['blue', 'green']

    def __init__(self, base_path:Path,default_zoom: int = DEFAULT_ZOOM):
        """
        Инициализация визуализатора
        :param tiles: Стиль карты (OpenStreetMap, Stamen Terrain, CartoDB positron)
        :param default_zoom: Уровень масштабирования по умолчанию
        """
        self.default_zoom = default_zoom
        self.color_maps = {
            'elevation': cm.linear.YlOrRd_09,
            'speed': cm.linear.PuBuGn_09,
            'slope': cm.linear.RdYlGn_11
        }

        self.maps_dir = base_path / "maps"
        self.maps_dir.mkdir(exist_ok=True)

        logger.info("GPX visualizer initialized")

    def create_base_map(self, center: Tuple[float, float]) -> folium.Map:
        """Создание базовой карты с центром в указанных координатах"""
        return folium.Map(
            location=center,
            zoom_start=self.default_zoom,
            control_scale=True
        )

    @staticmethod
    def _calculate_center(gpx: gpxpy.gpx.GPX) -> Tuple[float, float]:
        """Расчет центра карты по точкам трека"""
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

    def plot_single_track(
            self,
            gpx: gpxpy.gpx.GPX,
            map_title: str = "GPX Track",
            color_by: str = "elevation",
            line_weight: int = 3
    ) -> folium.Map:
        """
        Визуализация одного трека, с разделением по сегментам разными цветами
        """
        try:
            center = self._calculate_center(gpx)
            if center == (0, 0):
                logger.error("No valid points for center calculation")
                return None

            folium_map = self.create_base_map(center)
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
                    if len(segment.points) < 2:
                        continue

                    # Создаем FeatureGroup для сегмента
                    group_name = f"Segment {track_index + 1}"
                    track_group = folium.FeatureGroup(name=group_name)
                    folium_map.add_child(track_group)

                    # Получаем координаты и значения для окраски
                    locations, values = self._process_segment(segment, color_by)

                    # Выбираем цвет
                    color = colors[track_index % len(colors)]

                    folium.PolyLine(
                        locations=locations,
                        color=color,
                        weight=line_weight,
                        opacity=0.8,
                        popup=group_name
                    ).add_to(track_group)

                    track_index += 1

            # Управление слоями
            folium.LayerControl().add_to(folium_map)

            return folium_map

        except Exception as e:
            logger.error(f"Error visualizing track: {e}", exc_info=True)
            return None

    def _process_segment(self, segment: gpxpy.gpx.GPXTrackSegment, color_by: str) -> Tuple[
        List[List[float]], List[float]]:
        """Обрабатывает сегмент и возвращает координаты и значения для цветовой окраски"""
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
                    dist = self._distance_between_points(prev_point, point)
                    values.append((dist / time_diff) * 3.6 if time_diff > 0 else 0)  # км/ч
                else:
                    values.append(0)
            elif color_by == "slope" and prev_point and point.elevation is not None and prev_point.elevation is not None:
                dist = self._distance_between_points(prev_point, point)
                elev_diff = point.elevation - prev_point.elevation
                values.append((elev_diff / dist) * 100 if dist > 0 else 0)  # % уклона
            else:
                values.append(0)

            prev_point = point

        return locations, values

    def save_map(self, folium_map: folium.Map, file_path: Path) -> bool:
        """Сохранение карты в HTML-файл"""
        try:
            path = self.maps_dir / Path(file_path)
            folium_map.save(str(path))
            logger.info(f"Map saved to: {path.resolve()}")
            return True
        except Exception as e:
            logger.error(f"Error saving map: {e}", exc_info=True)
            return False

    @staticmethod
    def _distance_between_points(point1, point2) -> float:
        """Расчет расстояния между двумя точками (в метрах)"""
        from math import radians, sin, cos, sqrt, asin

        lat1, lon1 = radians(point1.latitude), radians(point1.longitude)
        lat2, lon2 = radians(point2.latitude), radians(point2.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return 6371000 * 2 * asin(sqrt(a))  # Земной радиус в метрах

    def plot_track_with_bad_segments(
            self,
            base_gpx: gpxpy.gpx.GPX,
            bad_segments: list[gpxpy.gpx.GPX],
            base_color: str = "blue",
            bad_segments_color: str = "red",
            line_weight: int = 4
    ) -> Optional[folium.Map]:
        try:
            # Собираем все точки для вычисления центра карты
            all_points = []
            for gpx in [base_gpx] + bad_segments:
                for track in gpx.tracks:
                    for segment in track.segments:
                        all_points.extend(segment.points)

            if not all_points:
                logger.warning("No points found for visualization")
                return None

            # Создаем базовую карту
            center = (np.mean([p.latitude for p in all_points]),
                      np.mean([p.longitude for p in all_points]))
            folium_map = self.create_base_map(center)

            # Добавляем основной трек
            base_group = folium.FeatureGroup(name="Основной трек", show=True)
            folium_map.add_child(base_group)

            for track in base_gpx.tracks:
                for segment in track.segments:
                    if len(segment.points) < 2:
                        continue
                    locations = [[p.latitude, p.longitude] for p in segment.points]
                    folium.PolyLine(
                        locations=locations,
                        color=base_color,
                        weight=line_weight,
                        opacity=0.7,
                        popup="Основной трек"
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
                            popup=group_name
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
                                html=f'''
                                        <div style="
                                            font-size: 12pt;
                                            color: black;
                                            background-color: rgba(255, 255, 255, 0.7);
                                            padding: 4px 8px;
                                            border-radius: 4px;
                                            font-weight: bold;
                                            white-space: nowrap;">
                                            {group_name}
                                        </div>'''
                            )
                        ).add_to(folium_map)

            # Добавляем контроль слоев
            folium.LayerControl().add_to(folium_map)

            return folium_map

        except Exception as e:
            logger.error(f"Ошибка при визуализации трека: {e}", exc_info=True)
            return None
