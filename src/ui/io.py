# ruff: noqa: T201
import logging

from config import (
    LOOP_CLOSURE_THRESHOLD_M,
    MAX_CLOSED_LOOP_LENGTH_M,
    MIN_CLOSED_LOOP_LENGTH_M,
    TRACK_SIMPLIFICATION_TOLERANCE_M,
)

logger = logging.getLogger(__name__)


class IO:
    """Класс для взаимодействия с пользователем через консоль."""

    @staticmethod
    def print_app_info() -> None:
        """Выводит информацию о программе и её использовании."""
        print("GPX Cleaner - программа для работы с треками походов.")
        print("Программа объединяет треки, сокращает количество точек с заданной точностью и удаляет лишние сегменты.")

    @staticmethod
    def print_path_info() -> None:
        """Выводит информацию о текущей директории и ожидаемых файлах."""
        print("\nПереместите все ваши GPX для работы в папку gpx_files/row/. ")
        user_input = input("После перемещения нажмите Enter: ")

        if not user_input:
            return None
        print("Ошибка при создании папки для GPX файлов."
              "Пожалуйста, убедитесь, что у вас есть права на запись в текущей директории.")
        return IO.print_path_info()

    @staticmethod
    def input_cleaning_parameters() -> tuple[float, float, float, float]:
        """Запрашивает у пользователя параметры для анализа треков.

        Returns:
                  tuple[float, float, float, float]:
                    параметры упрощения трека,
                    минимальной длины петли,
                    максимальной длины петли,
                    точности замыкания

        """
        print("\n=== Настройка параметров анализа маршрутов ===\n")
        print("Для анализа ваших маршрутов используются следующие параметры:\n")
        print("1. Упрощение трека — минимальное расстояние между точками в упрощённом маршруте.")
        print("   Это позволяет уменьшить количество точек в маршруте без потери важных деталей.")
        print(f"   По умолчанию: {TRACK_SIMPLIFICATION_TOLERANCE_M} метров.\n")

        print("2. Минимальная длина петли — это самый короткий путь, который программа "
              "будет учитывать как замкнутый маршрут.")
        print("   Слишком короткие маршруты могут быть случайными или несущественными.")
        print(f"   По умолчанию: {MIN_CLOSED_LOOP_LENGTH_M} метров.\n")

        print("3. Максимальная длина петли — самый длинный путь, который программа"
              "будет рассматривать. ")
        print("   Очень длинные маршруты могут часть важной радиалки.")
        print(f"   По умолчанию: {MAX_CLOSED_LOOP_LENGTH_M}  метров.\n")

        print("4. Точность замыкания — насколько близко должны находиться начальная и конечная "
              "точки петли, чтобы она считалась таковой.")
        print(f"   По умолчанию: {LOOP_CLOSURE_THRESHOLD_M}  метров.\n")

        print("Чтобы использовать стандартное значение, просто нажмите Enter.")

        simplification_input = input(f"Упрощение трека в метрах [по умолчанию {TRACK_SIMPLIFICATION_TOLERANCE_M}]: ").strip()
        min_length_input = input(f"Минимальная длина петли в метрах [по умолчанию {MIN_CLOSED_LOOP_LENGTH_M}]: ").strip()
        max_length_input = input(f"Максимальная длина петли в метрах [по умолчанию {MAX_CLOSED_LOOP_LENGTH_M}]: ").strip()
        threshold_input = input(f"Точность замыкания в метрах [по умолчанию {LOOP_CLOSURE_THRESHOLD_M}]: ").strip()

        # Используем временные переменные для float значений
        simplification_val = float(simplification_input) if simplification_input else TRACK_SIMPLIFICATION_TOLERANCE_M
        min_length_val = float(min_length_input) if min_length_input else MIN_CLOSED_LOOP_LENGTH_M
        max_length_val = float(max_length_input) if max_length_input else MAX_CLOSED_LOOP_LENGTH_M
        threshold_val = float(threshold_input) if threshold_input else LOOP_CLOSURE_THRESHOLD_M

        return simplification_val, min_length_val, max_length_val, threshold_val

    @staticmethod
    def input_bad_segments(len_bad_segments: int) -> list[int]:
        """Ввод сегментов для удаления от пользователя.

        Returns
        -------
            list[int]: Список индексов сегментов, которые нужно удалить.

        """
        print("\n=== Выбор сегментов для удаления ===\n")
        print(f"Найдено {len_bad_segments} плохих сегментов.")
        print()

        mode = IO._input_mode_select_segments()

        selected_segments = IO._input_bad_segments()

        if mode == 1:
            # Удалить выбранные сегменты
            return selected_segments
        # Удалить все, кроме выбранных
        return [seg for seg in range(len_bad_segments) if seg not in selected_segments]

    @staticmethod
    def _input_bad_segments() -> list[int]:
        """Ввод сегментов для удаления от пользователя.

        Returns:
            list[int]: Список индексов сегментов, которые нужно удалить.

        """
        selected_segments: set[int] = set()
        while True:
            print(f"\nВыбранные сегменты: {sorted(selected_segments)}")
            user_input = input(
                "  Введите номера сегментов (через пробел)\n"
                "  Для удаления сегмента поставьте перед ним '-'\n"
                "  'q' - завершить, 'c' - очистить список\n"
                "> ").strip().lower()

            if user_input.lower() == "q":
                break
            if user_input.lower() == "c":
                selected_segments.clear()
            try:
                parts = user_input.split()
                for part in parts:
                    num = abs(int(part))  # Получаем абсолютное значение числа
                    if part.startswith("-"):
                        # Удаляем сегмент, если он есть
                        if num in selected_segments:
                            selected_segments.discard(num)
                    else:
                        # Добавляем сегмент только если его еще нет
                        selected_segments.add(num)
            except ValueError as e:
                print(f"Ошибка ввода: {e}. Попробуйте ещё раз.")
        return sorted(selected_segments)

    @staticmethod
    def _input_mode_select_segments() -> int:
        """Запрашивает у пользователя режим выбора сегментов для удаления.

        Returns:
            int: Режим выбора сегментов:
                 1 - Удалить ВЫБРАННЫЕ сегменты
                 2 - Удалить ВСЕ, КРОМЕ выбранных сегментов

        """
        mode = 1

        while True:
            mode_input = input(
                "Выберите режим выбора сегментов для удаления:\n"
                "1 - Удалить ВЫБРАННЫЕ сегменты\n"
                "2 - Удалить ВСЕ, КРОМЕ выбранных сегментов\n"
                "Введите 1 или 2: ",
            ).strip()

            if mode_input not in {"1", "2"}:
                print("Ошибка: нужно ввести 1 или 2.")
                continue
            mode = int(mode_input)
            break

        return mode
