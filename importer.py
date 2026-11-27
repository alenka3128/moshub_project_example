"""importer - конвейер импорта ведомостей."""

from parsers import read_file
from validator import (
    clean_spaces,
    normalize_full_name,
    normalize_date,
    check_not_empty,
    check_grade,
    check_date,
)

EXPECTED_COLUMNS = 7


def process_row(cols: list) -> dict:
    """Очищает и проверяет одну строку ведомости из 7 колонок."""
    if len(cols) < EXPECTED_COLUMNS:
        raise ValueError(
            f"недостаточно колонок ({len(cols)} из {EXPECTED_COLUMNS})"
        )

    full_name = normalize_full_name(check_not_empty(cols[0], "ФИО"))
    record_book = clean_spaces(check_not_empty(cols[1], "Зачетка"))
    subject = clean_spaces(check_not_empty(cols[2], "Предмет"))
    group = clean_spaces(check_not_empty(cols[3], "Группа"))
    teacher = normalize_full_name(check_not_empty(cols[4], "Преподаватель"))

    raw_date = check_not_empty(cols[5], "Дата")
    check_date(raw_date, "Дата")         # дата не из будущего
    iso_date = normalize_date(raw_date)  # -> YYYY-MM-DD

    grade = check_grade(clean_spaces(cols[6]), "Оценка")

    return {
        "full_name": full_name,
        "record_book": record_book,
        "subject": subject,
        "group": group,
        "teacher": teacher,
        "date": iso_date,
        "grade": grade,
    }


def run_import(file_path: str, quarantine, db) -> tuple:
    """Импортирует файл: валидные строки - в базу, битые - в карантин."""
    raw_rows = read_file(file_path)
    accepted = 0
    rejected = 0

    # Шапку пропускаем; нумерация - как в исходном файле.
    for idx, row in enumerate(raw_rows[1:], start=2):
        if isinstance(row, list):                    # .csv: уже список полей
            cols, source_line = row, ";".join(row)
        else:                                        # .txt: строка с \n
            cols = row.split(";")
            source_line = row.rstrip("\r\n")

        try:
            record = process_row(cols)
        except ValueError as e:
            quarantine.add_from_error(idx, e, source_line)
            rejected += 1
            continue

        if db.insert_grade(record):
            accepted += 1
        else:
            quarantine.add(
                idx, "-", "дубликат записи (уже есть в базе)", source_line
            )
            rejected += 1

    quarantine.save()
    return accepted, rejected