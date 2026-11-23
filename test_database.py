import pytest
from database import Database


def test_insert_and_duplicate():
    """Тест 1: Проверяем добавление записи и защиту от дубликатов."""
    db = Database(":memory:")

    record = {
        "full_name": "Смирнов Алексей Петрович",
        "record_book": "22-ИВТ-01",
        "subject": "Программирование",
        "group": "ИВТ-22",
        "teacher": "Иванов И.И.",
        "date": "2026-10-10",
        "grade": "5"
    }

    assert db.insert_grade(record) is True
    assert db.insert_grade(record) is False

    db.close()


def test_statistics():
    """Тест 2: Проверяем правильность подсчета статистики и процента сдавших."""
    db = Database(":memory:")

    records = [
        {"full_name": "А", "record_book": "1", "subject": "Мат", "group": "Г1", "teacher": "П1", "date": "2026-10-01", "grade": "5"},
        {"full_name": "Б", "record_book": "2", "subject": "Мат", "group": "Г1", "teacher": "П1", "date": "2026-10-01", "grade": "4"},
        {"full_name": "В", "record_book": "3", "subject": "Мат", "group": "Г1", "teacher": "П1", "date": "2026-10-01", "grade": "зачет"},
        {"full_name": "Г", "record_book": "4", "subject": "Мат", "group": "Г1", "teacher": "П1", "date": "2026-10-01", "grade": "2"},
    ]

    for r in records:
        db.insert_grade(r)

    stats = db.get_statistics()

    assert stats["total"] == 4
    assert stats["pass_rate"] == 75.0
    assert stats["distribution"]["5"] == 1
    assert stats["distribution"]["2"] == 1

    db.close()


def test_empty_database_statistics():
    """Тест 3: Проверяем статистику на пустой базе (защита от деления на ноль)."""
    db = Database(":memory:")
    stats = db.get_statistics()

    assert stats["total"] == 0
    assert stats["pass_rate"] == 0.0
    assert stats["distribution"] == {}

    db.close()


def test_same_student_different_subjects():
    """Тест 4: Один студент сдает два разных предмета в один день (не дубликат)."""
    db = Database(":memory:")

    rec1 = {"full_name": "Иванов И.И.", "record_book": "101", "subject": "Физика", "group": "Г1", "teacher": "П1", "date": "2026-10-05", "grade": "4"}
    rec2 = {"full_name": "Иванов И.И.", "record_book": "101", "subject": "Химия", "group": "Г1", "teacher": "П2", "date": "2026-10-05", "grade": "5"}

    assert db.insert_grade(rec1) is True
    assert db.insert_grade(rec2) is True
    assert db.get_statistics()["total"] == 2

    db.close()


def test_retake_on_different_date():
    """Тест 5: Пересдача одного и того же предмета в другую дату должна сохраняться."""
    db = Database(":memory:")

    rec_fail = {"full_name": "Петров П.П.", "record_book": "102", "subject": "История", "group": "Г1", "teacher": "П1", "date": "2026-10-01", "grade": "2"}
    rec_pass = {"full_name": "Петров П.П.", "record_book": "102", "subject": "История", "group": "Г1", "teacher": "П1", "date": "2026-10-15", "grade": "4"}

    assert db.insert_grade(rec_fail) is True
    assert db.insert_grade(rec_pass) is True
    assert db.get_statistics()["total"] == 2

    db.close()


def test_zero_pass_rate():
    """Тест 6: Если в базе только двойки и незачеты, успеваемость равна 0%."""
    db = Database(":memory:")

    records = [
        {"full_name": "А", "record_book": "1", "subject": "Мат", "group": "Г1", "teacher": "П1", "date": "2026-10-01", "grade": "2"},
        {"full_name": "Б", "record_book": "2", "subject": "Физ", "group": "Г1", "teacher": "П1", "date": "2026-10-01", "grade": "незачет"},
    ]

    for r in records:
        db.insert_grade(r)

    stats = db.get_statistics()
    assert stats["total"] == 2
    assert stats["pass_rate"] == 0.0

    db.close()


def test_database_file_creation(tmp_path):
    """Тест 7: Проверяем реальное создание файла базы данных на диске."""
    db_file = tmp_path / "subdir" / "test.db"
    db = Database(str(db_file))

    assert db_file.exists() is True
    db.close()