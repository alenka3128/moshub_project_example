"""Тесты карантина отклонённых строк (quarantine + importer)."""

import csv
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from database import Database
from importer import run_import
from quarantine import Quarantine, extract_field, flatten
from validator import check_date, check_grade, check_not_empty

BAD_FILE = Path(__file__).parent / "bad_grades.txt"

GOOD_FILE_LINES = [
    "ФИО;Зачетка;Предмет;Группа;Преподаватель;Дата;Оценка",
    "Иванов Иван;22-ИВТ-21-001;Базы данных;ИВТ-21;Смирнов А.В.;12.05.2025;5",
]


def _write_lines(directory, name, lines):
    path = Path(directory) / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


class TestBadFileIntegrity(unittest.TestCase):
    """Проверяет, что bad_grades.txt полный: все 8 строк на месте."""

    def test_bad_file_exists_and_complete(self):
        self.assertTrue(BAD_FILE.exists(), "Файл bad_grades.txt не найден")
        lines = BAD_FILE.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 8, "В bad_grades.txt должно быть 8 строк")
        self.assertEqual(lines[0], "ФИО;Зачетка;Предмет;Группа;Преподаватель;Дата;Оценка")
        self.assertEqual(lines[-1], "Одна-единственная-колонка",
                         "Потерялась последняя строка bad_grades.txt")


class TestExtractField(unittest.TestCase):
    """Имя поля извлекается из всех видов ошибок валидатора."""

    def test_empty_field_error(self):
        try:
            check_not_empty("", "ФИО")
        except ValueError as e:
            self.assertEqual(extract_field(str(e)), "ФИО")

    def test_invalid_grade_error(self):
        try:
            check_grade("6")
        except ValueError as e:
            self.assertEqual(extract_field(str(e)), "Оценка")

    def test_future_date_error(self):
        try:
            check_date("01.01.2099")
        except ValueError as e:
            self.assertEqual(extract_field(str(e)), "Дата")

    def test_bad_date_format_error(self):
        try:
            check_date("только вчера")
        except ValueError as e:
            self.assertEqual(extract_field(str(e)), "Дата")

    def test_unknown_error_returns_dash(self):
        self.assertEqual(extract_field("что-то совсем другое пошло не так"), "-")


class TestQuarantine(unittest.TestCase):
    """Накопитель: добавление, очистка переносов, запись и чтение CSV."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.q = Quarantine(os.path.join(self.tmp, "rejected.csv"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_add_accumulates(self):
        self.q.add(3, "ФИО", "пусто", "строка")
        self.q.add(4, "Оценка", "плохая", "строка")
        self.assertEqual(len(self.q), 2)

    def test_add_flattens_newlines(self):
        self.q.add(2, "Дата", "причина\nс переносом", "строка\r\nс переносом")
        field, reason, source = self.q.rows[0][1:]
        self.assertNotIn("\n", reason)
        self.assertNotIn("\r", source)
        self.assertEqual(reason, "причина с переносом")

    def test_save_and_read_back(self):
        self.q.add(3, "ФИО", "Поле 'ФИО' не может быть пустым", ";;данные")
        self.q.save()
        with open(self.q.path, encoding="utf-8-sig") as f:
            rows = list(csv.reader(f, delimiter=";"))
        self.assertEqual(rows[0], ["row_number", "field", "reason", "source_line"])
        self.assertEqual(rows[1][0], "3")
        self.assertEqual(rows[1][1], "ФИО")

    def test_add_from_error_extracts_field(self):
        try:
            check_grade("хорошо")
        except ValueError as e:
            self.q.add_from_error(6, e, "строка с ошибкой")
        self.assertEqual(self.q.rows[0][1], "Оценка")


class TestImportQuarantine(unittest.TestCase):
    """Конвейер на заведомо битом файле: каждая строка - с правильной причиной."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.quarantine = Quarantine(os.path.join(self.tmp, "rejected.csv"))
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run_bad_file(self):
        accepted, rejected = run_import(str(BAD_FILE), self.quarantine, self.db)
        if len(self.quarantine.rows) != 6:
            self.fail(
                f"В карантине {len(self.quarantine.rows)} строк вместо 6. "
                "Проверьте bad_grades.txt: должно быть 8 строк, последняя - "
                "'Одна-единственная-колонка'."
            )
        return accepted, rejected

    def _load_csv(self):
        with open(self.quarantine.path, encoding="utf-8-sig") as f:
            return list(csv.reader(f, delimiter=";"))

    def test_counts_on_bad_file(self):
        accepted, rejected = self._run_bad_file()
        self.assertEqual(accepted, 1)   # только строка 2 - корректная
        self.assertEqual(rejected, 6)   # строки 3-8 - все с дефектами

    def test_row_numbers(self):
        self._run_bad_file()
        numbers = [row[0] for row in self.quarantine.rows]
        self.assertEqual(numbers, [3, 4, 5, 6, 7, 8])

    def test_csv_created_with_header(self):
        self._run_bad_file()
        rows = self._load_csv()
        self.assertEqual(rows[0], ["row_number", "field", "reason", "source_line"])
        self.assertEqual(len(rows), 7)  # шапка + 6 строк

    def test_empty_fio_row(self):
        self._run_bad_file()
        field, reason = self.quarantine.rows[0][1:3]
        self.assertEqual(field, "ФИО")
        self.assertIn("не может быть пустым", reason)

    def test_invalid_grade_row(self):
        self._run_bad_file()
        field, reason = self.quarantine.rows[1][1:3]
        self.assertEqual(field, "Оценка")
        self.assertIn("недопустима", reason)
        self.assertIn("'6'", reason)

    def test_future_date_row(self):
        self._run_bad_file()
        field, reason = self.quarantine.rows[2][1:3]
        self.assertEqual(field, "Дата")
        self.assertIn("не может быть больше сегодняшней", reason)

    def test_word_grade_row(self):
        self._run_bad_file()
        field, reason = self.quarantine.rows[3][1:3]
        self.assertEqual(field, "Оценка")
        self.assertIn("'отлично'", reason)

    def test_bad_format_date_row(self):
        self._run_bad_file()
        field, reason = self.quarantine.rows[4][1:3]
        self.assertEqual(field, "Дата")
        self.assertIn("должна быть в формате", reason)

    def test_not_enough_columns_row(self):
        self._run_bad_file()
        field, reason = self.quarantine.rows[5][1:3]
        self.assertEqual(field, "-")
        self.assertIn("недостаточно колонок (1 из 7)", reason)

    def test_clean_file_all_accepted(self):
        good = _write_lines(self.tmp, "good.txt", GOOD_FILE_LINES)
        accepted, rejected = run_import(good, self.quarantine, self.db)
        self.assertEqual((accepted, rejected), (1, 0))
        rows = self._load_csv()
        self.assertEqual(len(rows), 1)  # только шапка

    def test_duplicate_goes_to_quarantine(self):
        lines = GOOD_FILE_LINES + [GOOD_FILE_LINES[1]]
        dup = _write_lines(self.tmp, "dup.txt", lines)
        accepted, rejected = run_import(dup, self.quarantine, self.db)
        self.assertEqual((accepted, rejected), (1, 1))
        field, reason = self.quarantine.rows[0][1:3]
        self.assertEqual(field, "-")
        self.assertIn("дубликат", reason)


if __name__ == "__main__":
    unittest.main(verbosity=2)