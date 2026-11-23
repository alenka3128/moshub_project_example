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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Ошибка: не указан путь к файлу", file=sys.stderr)
        sys.exit(1)

    target_file = Path(sys.argv[1])
    if not target_file.exists():
        print(f"Ошибка: файл '{target_file}' не найден", file=sys.stderr)
        sys.exit(1)

    try:
        rows = read_file(str(target_file))
        print(f"Успешно прочитано строк: {len(rows)}")
    except ValueError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)