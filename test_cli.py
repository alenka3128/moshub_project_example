import subprocess
import sys
from pathlib import Path
import pytest


class AppCLIPage:
    """PageObject для взаимодействия с консольным приложением app.py."""

    def __init__(self, tmp_path: Path, script_path: str = "app.py"):
        self.tmp_path = tmp_path
        self.script_path = script_path
        self.db_path = tmp_path / "test_cli.db"
        self.last_result = None

    def create_csv(self, filename: str, rows: list[str]) -> Path:
        """Создает временный CSV-файл с шапкой и переданными строками."""
        file_path = self.tmp_path / filename
        header = "ФИО,Зачетка,Предмет,Группа,Преподаватель,Дата,Оценка"
        content = "\n".join([header] + rows)
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def run_import(self, file_path: str | Path):
        """Запускает app.py в консоли и сохраняет результат выполнения."""
        self.last_result = subprocess.run(
            [sys.executable, "-X", "utf8", self.script_path, str(file_path), str(self.db_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return self

    @property
    def output(self) -> str:
        """Возвращает весь текст, который программа вывела в консоль."""
        if not self.last_result:
            return ""
        return (self.last_result.stdout or "") + (self.last_result.stderr or "")

    @property
    def return_code(self) -> int:
        return self.last_result.returncode if self.last_result else -1


# --- 5 консольных тестов на исключения через PageObject ---

def test_cli_exception_letters_instead_of_grade(tmp_path):
    """Тест 1 (CLI): Буквы вместо числа в оценке."""
    cli = AppCLIPage(tmp_path)
    csv_file = cli.create_csv("letters.csv", [
        "Иванов Иван,22-ИВТ-01,Базы данных,ИВТ-22,Петров П.П.,15.10.2026,пять"
    ])

    cli.run_import(csv_file)

    assert "Отклонено: 1" in cli.output
    assert "недопустима" in cli.output.lower()


def test_cli_exception_empty_field(tmp_path):
    """Тест 2 (CLI): Пустая строка в обязательном поле (ФИО)."""
    cli = AppCLIPage(tmp_path)
    csv_file = cli.create_csv("empty.csv", [
        "   ,22-ИВТ-02,Базы данных,ИВТ-22,Петров П.П.,15.10.2026,5"
    ])

    cli.run_import(csv_file)

    assert "Отклонено: 1" in cli.output
    assert "не может быть пустым" in cli.output.lower()


def test_cli_exception_negative_grade(tmp_path):
    """Тест 3 (CLI): Отрицательное число в оценке (-5)."""
    cli = AppCLIPage(tmp_path)
    csv_file = cli.create_csv("negative.csv", [
        "Сидорова Анна,22-ИВТ-03,Базы данных,ИВТ-22,Петров П.П.,15.10.2026,-5"
    ])

    cli.run_import(csv_file)

    assert "Отклонено: 1" in cli.output
    assert "недопустима" in cli.output.lower()


def test_cli_exception_invalid_file_path(tmp_path):
    """Тест 4 (CLI): Передача несуществующего пути к файлу в консоль."""
    cli = AppCLIPage(tmp_path)
    missing_file = tmp_path / "no_such_file.csv"

    cli.run_import(missing_file)

    assert cli.return_code != 0
    assert "не найден" in cli.output.lower()


def test_cli_exception_duplicate_record(tmp_path):
    """Тест 5 (CLI): Попытка повторно загрузить дубликат через консоль."""
    cli = AppCLIPage(tmp_path)
    row = "Козлов Дмитрий,22-ИВТ-04,Базы данных,ИВТ-22,Петров П.П.,15.10.2026,4"
    csv_file = cli.create_csv("duplicate.csv", [row, row])

    cli.run_import(csv_file)

    assert "Принято: 1, Отклонено: 1" in cli.output
    assert "дубликат" in cli.output.lower()