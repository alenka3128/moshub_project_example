"""Импорт ведомости: выбрать файл, проверить его, разобрать и провалидировать."""

from file_utils import choose_file, prepare_file
from parser import read_file
from validator import clean_spaces, normalize_full_name, check_grade, check_date


def process_import():
    raw = choose_file(start_dir=".")
    if not raw:                                  # пользователь нажал «Отмена»
        print("Выбор файла отменён.")
        return

    try:
        path = prepare_file(raw)                 # путь, расширение, пустота
    except (FileNotFoundError, ValueError) as e:
        print(f"Файл не принят: {e}")
        return

    print(f"Файл принят: {path.name}")

    accepted, rejected = 0, 0
    lines = read_file(str(path))                 # чтение через существующий parser
    for i, line in enumerate(lines, 1):
        fields = [clean_spaces(x) for x in
                  (line.strip().split(",") if path.suffix == ".txt" else line)]
        if len(fields) != 3:
            print(f"Строка {i}: ожидалось 3 поля, получено {len(fields)} — отклонена")
            rejected += 1
            continue
        fio, grade, dt = fields
        try:
            fio = normalize_full_name(fio)
            grade = check_grade(grade)
            check_date(dt)
            accepted += 1
            print(f"Строка {i}: OK — {fio}, {grade}, {dt}")
        except ValueError as e:
            rejected += 1
            print(f"Строка {i}: отклонена — {e}")

    print(f"\nИтог: принято {accepted}, отклонено {rejected}")


if __name__ == "__main__":
    process_import()