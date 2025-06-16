from typing import List


class IO:
    @staticmethod
    def input_path()-> None:

        print("Переместите все ваши GPX для работы в папку gpx_files/row/. ")
        user_input = input("После перемещения нажмите Enter: ")

        if not user_input:
            return None
        else:
            print("Ошибка при создании папки для GPX файлов. "
                  "Пожалуйста, убедитесь, что у вас есть права на запись в текущей директории.")
            return IO.input_path()

    @staticmethod
    def input_bad_segments() -> List[int]:
        """Ввод сегментов с ошибками от пользователя"""
        bad_segments = []
        while True:
            user_input = input(
                "Введите сегмент, который нужно удалить (формат: \"1 11 23\") или 'q' для выхода: ").strip()
            if user_input.lower() == 'q':
                break
            try:
                numbers = list(map(int, user_input.split()))
                if any(n < 0 for n in numbers):
                    raise ValueError("Номера сегментов должны быть неотрицательными числами.")
                bad_segments.extend(numbers)
            except ValueError as e:
                print(f"Ошибка ввода: {e}. Попробуйте ещё раз.")
        return bad_segments
