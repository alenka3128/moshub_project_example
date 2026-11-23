import subprocess
import sys
import pytest
from pathlib import Path
from validator import check_grade, check_not_empty
from database import Database


# --- 1. Паттерн PageObject для консольного интерфейса (CLI) ---
class ParserCLIPage:
    """Обертка над запуском существующего скрипта parsers.py из терминала."""

    def __init__(self, script_path: str = "parsers.py"):
        self.script_path = script_path

    def parse_file(self, file_path: str | Path):
        """Запускает обработку ведомости через консоль и возвращает результат."""
        return subprocess.run(
            [sys.executable, "-X", "utf8", self.script_path, str(file_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )


# --- 2. 5 тестов на исключения и ошибочные сценарии ---

def test_exception_letters_instead_of_number():
    """Исключение 1: Буквы вместо числа в оценке."""
    with pytest.raises(ValueError, match="недопустима"):
        check_grade("пять")


def test_exception_empty_string():
    """Исключение 2: Пустая строка в обязательном поле."""
    with pytest.raises(ValueError, match="не может быть пустым"):
        check_not_empty("   ", "ФИО")


def test_exception_negative_number():
    """Исключение 3: Отрицательное число в оценке."""
    with pytest.raises(ValueError, match="недопустима"):
        check_grade("-5")


def test_exception_invalid_file_path(tmp_path):
    """Исключение 4: Неверный путь к несуществующему файлу через CLI PageObject."""
    cli = ParserCLIPage(script_path="parsers.py")
    fake_file = tmp_path / "nesushestvuyushiy_file.csv"

    result = cli.parse_file(fake_file)

    # Программа должна завершиться с кодом ошибки (не 0) и сообщить, что файл не найден
    assert result.returncode != 0
    assert "не найден" in (result.stderr or "").lower()



def test_exception_duplicate_record():
    """Исключение 5: Попытка добавить дубликат записи."""
    db = Database(":memory:")
    record = {
        "full_name": "Иванов Иван Иванович",
        "record_book": "22-ИВТ-01",
        "subject": "Базы данных",
        "group": "ИВТ-22",
        "teacher": "Петров П.П.",
        "date": "2026-10-10",
        "grade": "5",
    }

    assert db.insert_grade(record) is True
    # Повторная вставка должна быть отклонена
    assert db.insert_grade(record) is False
    db.close()