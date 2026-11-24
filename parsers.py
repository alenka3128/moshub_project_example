import csv
import sys
from pathlib import Path


def read_file(file_path):
    if file_path.endswith('.txt'):
        # Для текстовых файлов читаем всё сразу или построчно
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.readlines()
    elif file_path.endswith('.csv'):
        # Для CSV используется модуль csv — корректно обрабатывает запятые в кавычках
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            return [row for row in reader]
    else:
        raise ValueError("Неподдерживаемый тип файла. Разрешены только .txt и .csv")


def select_file_path() -> str:
    """Открывает стандартное окно проводника для выбора файла или запрашивает путь в консоли."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()  # Скрываем пустое главное окно
        root.attributes("-topmost", True)  # Выводим окно выбора поверх всех окон
        file_path = filedialog.askopenfilename(
            title="Выберите файл ведомости",
            filetypes=[("Ведомости", "*.csv *.txt"), ("Все файлы", "*.*")],
        )
        root.destroy()
        return file_path
    except Exception:
        # Запасной вариант для запуска в Docker или терминале без графического экрана
        return input("Введите путь к файлу ведомости (.csv или .txt): ").strip()


if __name__ == "__main__":
    # Если путь передали аргументом (как в автотестах), берем его; иначе — открываем выбор файла
    if len(sys.argv) >= 2:
        raw_path = sys.argv[1]
    else:
        raw_path = select_file_path()

    if not raw_path:
        print("Ошибка: файл не выбран", file=sys.stderr)
        sys.exit(1)

    target_file = Path(raw_path)
    if not target_file.exists():
        print(f"Ошибка: файл '{target_file}' не найден", file=sys.stderr)
        sys.exit(1)

    try:
        rows = read_file(str(target_file))
        print(f"Успешно прочитано строк из '{target_file.name}': {len(rows)}")
    except ValueError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)