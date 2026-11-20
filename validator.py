from datetime import date, datetime

VALID_GRADES = {"2", "3", "4", "5", "зачет", "незачет"}


def clean_spaces(value: str) -> str:
    """Убирает пробелы по краям и заменяет множественные пробелы/переносы внутри на один."""
    if value is None:
        return ""
    return " ".join(str(value).split())


def normalize_full_name(full_name: str) -> str:
    """Очищает пробелы и делает каждое слово в ФИО с заглавной буквы."""
    cleaned = clean_spaces(full_name)



    dfd
    return " ".join(word.capitalize() for word in cleaned.split())


def normalize_date(value: str) -> str:
    """Приводит разные форматы дат к строгому стандарту YYYY-MM-DD."""
    cleaned = clean_spaces(value)
    formats = ("%d.%m.%Y", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d")
    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned, fmt).date()
            return dt.isoformat()
        except ValueError:
            continue
    raise ValueError(f"Неизвестный или неверный формат даты: '{value}'")


def check_not_empty(value, name: str) -> str:
    """Проверяет, что значение не None и не пустая строка."""
    if value is None or not str(value).strip():
        raise ValueError(f"Поле '{name}' не может быть пустым")
    return str(value).strip()


def check_grade(value, name: str = "оценка") -> str:
    """Проверяет оценку по белому списку и заменяет 'ё' на 'е'."""
    v = check_not_empty(value, name).lower().replace("ё", "е")
    if v not in VALID_GRADES:
        raise ValueError(f"Оценка '{value}' недопустима: разрешены 2, 3, 4, 5, зачет, незачет")
    return v


def check_date(value, name: str = "дата") -> date:
    """Проверяет формат даты (ДД.ММ.ГГГГ или ДД/ММ/ГГГГ) и что дата не в будущем."""
    v = check_not_empty(value, name)
    parsed_date = None

    for fmt in ("%d.%m.%Y", "%d/%m/%Y"):
        try:
            parsed_date = datetime.strptime(v, fmt).date()
            break
        except ValueError:
            continue

    if parsed_date is None:
        raise ValueError(f"Дата '{value}' должна быть в формате ДД.ММ.ГГГГ или ДД/ММ/ГГГГ")

    if parsed_date > date.today():
        raise ValueError(f"Дата {v} не может быть больше сегодняшней ({date.today().strftime('%d.%m.%Y')})")

    return parsed_date