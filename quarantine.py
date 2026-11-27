"""quarantine - карантин отклонённых строк импорта ведомостей."""

import csv
import re
from pathlib import Path

HEADER = ["row_number", "field", "reason", "source_line"]
DEFAULT_FIELD = "-"

_FIELD_RULES = [
    (re.compile(r"Поле '([^']+)'"), lambda m: m.group(1)),
    (re.compile(r"^Оценка "), lambda m: "Оценка"),
    (re.compile(r"^Дата "), lambda m: "Дата"),
]


def flatten(text: str) -> str:
    """Схлопывает переносы строк и лишние пробелы в одну строку."""
    return re.sub(r"\s+", " ", str(text)).strip()


def extract_field(error_text: str) -> str:
    """Определяет виновное поле по тексту ошибки валидатора."""
    text = flatten(error_text)
    for pattern, get_name in _FIELD_RULES:
        match = pattern.search(text)
        if match:
            return get_name(match)
    return DEFAULT_FIELD


class Quarantine:
    """Накопитель отклонённых строк с сохранением в CSV."""

    def __init__(self, path: str = "rejected.csv"):
        self.path = Path(path)
        self.rows = []  # список [row_number, field, reason, source_line]

    def add(self, row_number: int, field: str, reason: str, source_line: str):
        self.rows.append(
            [row_number, field, flatten(reason), flatten(source_line)]
        )

    def add_from_error(self, row_number: int, error: Exception, source_line: str):
        self.add(row_number, extract_field(str(error)), str(error), source_line)

    def save(self):
        """Записывает накопленные строки в CSV (utf-8-sig - для Excel)."""
        with self.path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(HEADER)
            writer.writerows(self.rows)

    def __len__(self):
        return len(self.rows)