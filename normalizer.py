from datetime import datetime

def clean_spaces(s: str) -> str:
    return " ".join(s.split())

def normalize_fio(fio: str) -> str:
    return " ".join(word.capitalize() for word in fio.split())

def normalize_date(s: str) -> str:
    formats = [
        "%d.%m.%Y",   # 12.05.2025
        "%Y/%m/%d",   # 2025/05/12
        "%d/%m/%Y",   # 12/05/2025 (уже нужный формат — пройдёт насквозь)
        "%d-%m-%Y",   # 12-05-2025
        "%Y-%m-%d",   # 2025-07-03
        "%Y.%m.%d",   # 2025.05.12
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s.strip(), fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    raise ValueError(f"Неизвестный формат даты: {s!r}")


if __name__ == "__main__":
    tests = [
        ("Иванов   Иван   Иваныч", "12.05.2025"),
        ("петров-водкин пётр", "2025/05/12"),
        ("СИДОРОВА  аННА", "2024-07-03"),
    ]
    for fio, date in tests:
        fio_clean = normalize_fio(clean_spaces(fio))
        date_std = normalize_date(date)
        print(f"{fio_clean:<25} {date_std}")