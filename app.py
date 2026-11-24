import sys
from pathlib import Path
from database import Database
from parsers import read_file, select_file_path
from validator import (
    clean_spaces,
    normalize_full_name,
    normalize_date,
    check_not_empty,
    check_grade,
    check_date,
)
from seed_data import generate_100_records


def process_row(cols: list[str], row_num: int) -> dict:
    """Очищает и проверяет одну строку ведомости из 7 колонок."""
    if len(cols) < 7:
        raise ValueError(f"недостаточно колонок ({len(cols)} из 7)")

    full_name = normalize_full_name(check_not_empty(cols, "ФИО"))
    record_book = clean_spaces(check_not_empty(cols, "Зачетка"))
    subject = clean_spaces(check_not_empty(cols, "Предмет"))
    group = clean_spaces(check_not_empty(cols, "Группа"))
    teacher = normalize_full_name(check_not_empty(cols, "Преподаватель"))

    raw_date = check_not_empty(cols, "Дата")
    check_date(raw_date, "Дата")  # Проверка, что дата не из будущего
    iso_date = normalize_date(raw_date)

    grade = check_grade(cols, "Оценка")

    return {
        "full_name": full_name,
        "record_book": record_book,
        "subject": subject,
        "group": group,
        "teacher": teacher,
        "date": iso_date,
        "grade": grade,
    }


def main():
    db_path = "data/vedomosti.db"
    db = Database(db_path)

    # 1. Если база пустая — наполняем её на 100 записей через Faker
    if db.get_statistics()["total"] == 0:
        print("База данных пуста. Генерируем 100 тестовых записей через Faker...")
        db.close()
        generate_100_records(db_path)
        db = Database(db_path)

    # 2. Получаем путь к файлу (из аргумента или через окно проводника)
    if len(sys.argv) >= 2:
        raw_path = sys.argv
    else:
        print("\nВыберите файл ведомости (.csv или .txt) для загрузки...")
        raw_path = select_file_path()

    if raw_path:
        target_file = Path(raw_path)
        if not target_file.exists():
            print(f"Ошибка: файл '{target_file}' не найден.", file=sys.stderr)
            db.close()
            sys.exit(1)

        print(f"\nОбработка файла: {target_file.name}")
        raw_rows = read_file(str(target_file))

        accepted = 0
        errors = []

        # Пропускаем шапку (первую строку)
        for idx, row in enumerate(raw_rows[1:], start=2):
            cols = row if isinstance(row, list) else row.split(";")
            try:
                record = process_row(cols, idx)
                if db.insert_grade(record):
                    accepted += 1
                else:
                    errors.append(f"Строка {idx}: дубликат записи (уже есть в базе)")
            except ValueError as e:
                errors.append(f"Строка {idx}: {e}")

        db.log_import(target_file.name, accepted=accepted, rejected=len(errors))

        print(f"Импорт завершен. Принято: {accepted}, Отклонено: {len(errors)}")
        for err in errors:
            print(f"  - {err}")

    # 3. Выводим итоговую сводку по всей базе данных
    stats = db.get_statistics()
    print("\n=== СВОДКА ПО БАЗЕ ДАННЫХ ===")
    print(f"Всего оценок в базе: {stats['total']}")
    print(f"Распределение оценок: {stats['distribution']}")
    print(f"Процент успевающих: {stats['pass_rate']}%")
    db.close()


if __name__ == "__main__":
    main()