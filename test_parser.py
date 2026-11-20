"""Тесты функций очистки и валидации данных."""
import unittest
from datetime import date, timedelta

from validator import (
    clean_spaces,
    normalize_full_name,
    normalize_date,
    check_not_empty,
    check_grade,
    check_date,
)


class TestCleanSpaces(unittest.TestCase):
    """Очистка лишних пробелов."""

    def test_collapses_internal_spaces(self):
        self.assertEqual(clean_spaces("Иванов    Иван"), "Иванов Иван")

    def test_strips_edges(self):
        self.assertEqual(clean_spaces("  Иванов  "), "Иванов")

    def test_tabs_and_newlines(self):
        self.assertEqual(clean_spaces("А\tБ\n  В"), "А Б В")

    def test_single_word_unchanged(self):
        self.assertEqual(clean_spaces("Иванов"), "Иванов")

    def test_only_spaces_to_empty(self):
        self.assertEqual(clean_spaces("   "), "")


class TestNormalizeFullname(unittest.TestCase):
    """Формат Title Case для ФИО."""

    def test_lower_to_title(self):
        self.assertEqual(normalize_full_name("иванов иван иванович"), "Иванов Иван Иванович")

    def test_upper_to_title(self):
        self.assertEqual(normalize_full_name("ИВАНОВ ИВАН"), "Иванов Иван")

    def test_mixed_case(self):
        self.assertEqual(normalize_full_name("иВАНОВ иван"), "Иванов Иван")

    def test_extra_spaces_removed(self):
        self.assertEqual(normalize_full_name("  сидорова   Анна "), "Сидорова Анна")

    def test_double_name_with_hyphen(self):
        # известная оговорка capitalize(): после дефиса буква станет строчной
        self.assertEqual(normalize_full_name("петров-водкин пётр"), "Петров-водкин Пётр")

    def test_single_word(self):
        self.assertEqual(normalize_full_name("иванов"), "Иванов")


class TestNormalizeDate(unittest.TestCase):
    """Приведение форматов дат к YYYY-MM-DD."""

    def test_dotted(self):
        self.assertEqual(normalize_date("12.05.2025"), "2025-05-12")

    def test_slashed_year_first(self):
        self.assertEqual(normalize_date("2025/05/12"), "2025-05-12")

    def test_slashed_day_first(self):
        self.assertEqual(normalize_date("12/05/2025"), "2025-05-12")

    def test_dashed(self):
        self.assertEqual(normalize_date("12-05-2025"), "2025-05-12")

    def test_leading_zeros_added(self):
        self.assertEqual(normalize_date("3.7.2024"), "2024-07-03")

    def test_spaces_around(self):
        self.assertEqual(normalize_date("  12.05.2025  "), "2025-05-12")

    def test_unknown_format_raises(self):
        with self.assertRaises(ValueError):
            normalize_date("12 мая 2025")

    def test_invalid_date_raises(self):
        # 32-го числа не бывает
        with self.assertRaises(ValueError):
            normalize_date("32.13.2025")


class TestCheckNotEmpty(unittest.TestCase):
    """Проверка полей на пустоту."""

    def test_normal_string(self):
        self.assertEqual(check_not_empty("Иванов", "ФИО"), "Иванов")

    def test_strips(self):
        self.assertEqual(check_not_empty("  Иванов  ", "ФИО"), "Иванов")

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError) as ctx:
            check_not_empty("", "ФИО")
        self.assertIn("ФИО", str(ctx.exception))

    def test_spaces_only_raises(self):
        with self.assertRaises(ValueError):
            check_not_empty("   ", "ФИО")

    def test_none_raises(self):
        with self.assertRaises(ValueError):
            check_not_empty(None, "ФИО")

    def test_message_contains_field_name(self):
        with self.assertRaises(ValueError) as ctx:
            check_not_empty("", "оценка")
        self.assertIn("оценка", str(ctx.exception))


class TestCheckGrade(unittest.TestCase):
    """Проверка оценки по белому списку."""

    def test_numeric_grades(self):
        for g in ("2", "3", "4", "5"):
            self.assertEqual(check_grade(g), g)

    def test_zachet_lower(self):
        self.assertEqual(check_grade("зачет"), "зачет")

    def test_zachet_with_yo(self):
        self.assertEqual(check_grade("зачёт"), "зачет")

    def test_uppercase(self):
        self.assertEqual(check_grade("ЗАЧЁТ"), "зачет")
        self.assertEqual(check_grade("НЕЗАЧЕТ"), "незачет")

    def test_spaces_around(self):
        self.assertEqual(check_grade("  5  "), "5")

    def test_invalid_number_raises(self):
        with self.assertRaises(ValueError):
            check_grade("6")

    def test_word_grade_raises(self):
        with self.assertRaises(ValueError):
            check_grade("отлично")

    def test_fraction_raises(self):
        with self.assertRaises(ValueError):
            check_grade("4.5")

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            check_grade("")

    def test_nezachet(self):
        self.assertEqual(check_grade("незачёт"), "незачет")


class TestCheckDate(unittest.TestCase):
    """Проверка даты: формат и не позже сегодняшней."""

    def test_valid_past_date(self):
        d = check_date("12.05.2025")
        self.assertEqual((d.year, d.month, d.day), (2025, 5, 12))

    def test_today_is_valid(self):
        today = date.today().strftime("%d.%m.%Y")
        d = check_date(today)
        self.assertEqual(d, date.today())

    def test_future_date_raises(self):
        future = (date.today() + timedelta(days=1)).strftime("%d.%m.%Y")
        with self.assertRaises(ValueError):
            check_date(future)

    def test_wrong_format_raises(self):
        with self.assertRaises(ValueError):
            check_date("2025-05-12")  # формат ISO не подходит, нужен ДД.ММ.ГГГГ или ДД/ММ/ГГГГ

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            check_date("")

    def test_impossible_date_raises(self):
        with self.assertRaises(ValueError):
            check_date("32.13.2025")

    def test_returns_date_object(self):
        self.assertIsInstance(check_date("12/05/2025"), date)


class TestFullPipeline(unittest.TestCase):
    """Интеграционный прогон: очистка -> нормализация -> валидация."""

    def _process(self, full_name, grade, dt):
        f = check_not_empty(normalize_full_name(clean_spaces(full_name)), "ФИО")
        g = check_grade(grade)
        d = check_date(dt)
        return f, g, d

    def test_good_record(self):
        f, g, d = self._process("  иванов   иван ", "Зачёт", "12.05.2025")
        self.assertEqual(f, "Иванов Иван")
        self.assertEqual(g, "зачет")
        self.assertEqual((d.year, d.month, d.day), (2025, 5, 12))

    def test_empty_full_name_fails_first(self):
        with self.assertRaises(ValueError):
            self._process("", "5", "12.05.2025")

    def test_bad_grade_fails(self):
        with self.assertRaises(ValueError):
            self._process("Иванов Иван", "отлично", "12.05.2025")


if __name__ == "__main__":
    unittest.main(verbosity=2)