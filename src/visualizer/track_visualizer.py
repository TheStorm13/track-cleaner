import logging
from pathlib import Path
from typing import List, Optional, Tuple, Union

import branca.colormap as cm
import folium
import gpxpy.gpx
import numpy as np
from folium.plugins import MarkerCluster, MeasureControl

logger = logging.getLogger("GPXVisualizer")


class TrackVisualizer:
    """Класс для визуализации GPX-треков на интерактивных картах"""

    DEFAULT_TILES = "OpenStreetMap"
    DEFAULT_ZOOM = 13
    DEFAULT_COLORS = ['blue', 'green']

    def __init__(self, tiles: str = DEFAULT_TILES, default_zoom: int = DEFAULT_ZOOM):
        """
        Инициализация визуализатора
        :param tiles: Стиль карты (OpenStreetMap, Stamen Terrain, CartoDB positron)
        :param default_zoom: Уровень масштабирования по умолчанию
        """
        # self.tiles = tiles
        self.default_zoom = default_zoom
        self.color_maps = {
            'elevation': cm.linear.YlOrRd_09,
            'speed': cm.linear.PuBuGn_09,
            'slope': cm.linear.RdYlGn_11
        }
        logger.info("GPX visualizer initialized")

    def create_base_map(self, center: Tuple[float, float]) -> folium.Map:
        """Создание базовой карты с центром в указанных координатах"""
        return folium.Map(
            location=center,
            # tiles=self.tiles,
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
            line_weight: int = 3,
            add_markers: bool = False,
            add_elevation_profile: bool = True
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

    def _add_key_point_markers(self, segment: gpxpy.gpx.GPXTrackSegment, folium_map: folium.Map) -> None:
        """Добавляет маркеры для ключевых точек трека"""
        marker_cluster = MarkerCluster(name="Key Points")
        folium_map.add_child(marker_cluster)

        start_point = segment.points[0]
        end_point = segment.points[-1]

        # Маркер старта
        folium.Marker(
            location=[start_point.latitude, start_point.longitude],
            popup=f"<b>Start</b><br>Time: {start_point.time}",
            icon=folium.Icon(color='green', icon='play', prefix='fa')
        ).add_to(marker_cluster)

        # Маркер финиша
        folium.Marker(
            location=[end_point.latitude, end_point.longitude],
            popup=f"<b>End</b><br>Time: {end_point.time}",
            icon=folium.Icon(color='red', icon='flag', prefix='fa')
        ).add_to(marker_cluster)

        # Маркер самой высокой точки
        if any(p.elevation for p in segment.points):
            highest_point = max(segment.points, key=lambda p: p.elevation or 0)
            folium.Marker(
                location=[highest_point.latitude, highest_point.longitude],
                popup=f"<b>Highest Point</b><br>Elevation: {highest_point.elevation:.1f}m",
                icon=folium.Icon(color='orange', icon='mountain', prefix='fa')
            ).add_to(marker_cluster)

    def _add_elevation_profile(self, segment: gpxpy.gpx.GPXTrackSegment, folium_map: folium.Map) -> None:
        """Добавляет график высот на карту"""
        elevations = [p.elevation for p in segment.points if p.elevation is not None]
        distances = [0]
        cumulative = 0

        for i in range(1, len(segment.points)):
            dist = self._distance_between_points(segment.points[i - 1], segment.points[i])
            cumulative += dist
            distances.append(cumulative)

        # Создание HTML для графика
        elevation_data = str([{'x': d / 1000, 'y': e} for d, e in zip(distances, elevations)])

        elevation_html = f"""
        <div id="elevationChart" style="height: 200px; margin: 10px;"></div>
        <script>
            var chart = new Chartist.Line('#elevationChart', {{
                series: [{{
                    name: 'elevation',
                    data: {elevation_data}
                }}]
            }}, {{
                axisY: {{
                    labelInterpolationFnc: function(value) {{
                        return value + ' m';
                    }}
                }},
                axisX: {{
                    labelInterpolationFnc: function(value) {{
                        return value + ' km';
                    }}
                }}
            }});
        </script>
        """

        folium_map.get_root().html.add_child(folium.Element(elevation_html))

    def plot_multiple_tracks(
            self,
            gpx_tracks: List[gpxpy.gpx.GPX],
            track_names: Optional[List[str]] = None,
            colors: Optional[List[str]] = None,
            line_weight: int = 3
    ) -> folium.Map:
        """
        Визуализация нескольких треков на одной карте
        :param gpx_tracks: Список объектов GPX
        :param track_names: Названия треков
        :param colors: Цвета для каждого трека
        :param line_weight: Толщина линий
        :return: Объект folium.Map
        """
        try:
            if not gpx_tracks:
                logger.warning("No tracks to visualize")
                return None

            # Расчет центра карты по всем трекам
            all_points = []
            for gpx in gpx_tracks:
                for track in gpx.tracks:
                    for segment in track.segments:
                        all_points.extend(segment.points)

            if not all_points:
                logger.error("No valid points found in tracks")
                return None

            lats = [p.latitude for p in all_points]
            lons = [p.longitude for p in all_points]
            center = (np.mean(lats), np.mean(lons))

            folium_map = self.create_base_map(center)
            folium_map.title = "Multiple GPX Tracks"

            # Добавление элементов управления
            folium_map.add_child(MeasureControl())
            folium_map.add_child(folium.LatLngPopup())

            # Настройка цветов и названий
            colors = colors or self.DEFAULT_COLORS[:len(gpx_tracks)]
            track_names = track_names or [f"Track {i + 1}" for i in range(len(gpx_tracks))]

            # Добавление каждого трека
            for gpx, color, name in zip(gpx_tracks, colors, track_names):
                track_group = folium.FeatureGroup(name=name)
                folium_map.add_child(track_group)

                for track in gpx.tracks:
                    for segment in track.segments:
                        if len(segment.points) < 2:
                            continue

                        locations = [[p.latitude, p.longitude] for p in segment.points]

                        folium.PolyLine(
                            locations=locations,
                            color=color,
                            weight=line_weight,
                            opacity=0.7,
                            popup=name
                        ).add_to(track_group)

                        # Добавление маркеров начала и конца
                        folium.Marker(
                            location=[segment.points[0].latitude, segment.points[0].longitude],
                            popup=f"<b>Start {name}</b>",
                            icon=folium.Icon(color='green', icon='play', prefix='fa')
                        ).add_to(track_group)

                        folium.Marker(
                            location=[segment.points[-1].latitude, segment.points[-1].longitude],
                            popup=f"<b>End {name}</b>",
                            icon=folium.Icon(color='red', icon='flag', prefix='fa')
                        ).add_to(track_group)

            # Добавление управления слоями
            folium.LayerControl().add_to(folium_map)

            return folium_map

        except Exception as e:
            logger.error(f"Error visualizing multiple tracks: {e}", exc_info=True)
            return None

    def save_map(self, folium_map: folium.Map, file_path: Union[str, Path]) -> bool:
        """Сохранение карты в HTML-файл"""
        try:
            path = Path(file_path)
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

    def plot_track_with_loops(
            self,
            base_gpx: gpxpy.gpx.GPX,
            loops: List[gpxpy.gpx.GPX],
            base_color: str = "blue",
            loop_color: str = "red",
            line_weight: int = 4
    ) -> folium.Map:
        """
        Визуализирует исходный трек и найденные петли на одной карте

        :param base_gpx: Исходный GPX трек
        :param loops: Список GPX объектов с найденными петлями
        :param base_color: Цвет основного трека
        :param loop_colors: Список цветов для петель (если не задан — будет автогенерация)
        :param line_weight: Толщина линий
        :return: Объект folium.Map
        """
        try:
            all_tracks = [base_gpx] + loops
            all_points = []

            for gpx in all_tracks:
                for track in gpx.tracks:
                    for segment in track.segments:
                        all_points.extend(segment.points)

            if not all_points:
                logger.warning("No points found for visualization")
                return None

            center = (np.mean([p.latitude for p in all_points]), np.mean([p.longitude for p in all_points]))
            folium_map = self.create_base_map(center)

            # Базовый трек (основной путь)
            base_group = folium.FeatureGroup(name="Base Track")
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
                        opacity=0.6,
                        popup="Base Track"
                    ).add_to(base_group)

            # Петли

            for i, loop_gpx in enumerate(loops):
                loop_group = folium.FeatureGroup(name=f"Loop {i + 1}")
                folium_map.add_child(loop_group)

                for track in loop_gpx.tracks:
                    for segment in track.segments:
                        if len(segment.points) < 2:
                            continue
                        locations = [[p.latitude, p.longitude] for p in segment.points]
                        folium.PolyLine(
                            locations=locations,
                            color=loop_color,
                            weight=line_weight + 1,
                            opacity=0.9,
                            popup=f"Loop {i + 1}"
                        ).add_to(loop_group)

            folium.LayerControl().add_to(folium_map)
            return folium_map

        except Exception as e:
            logger.error(f"Error plotting track with loops: {e}", exc_info=True)
            return None
