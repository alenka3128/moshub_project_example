"""file_utils — выбор папки и файла, проверка пути, расширения и пустоты файла.

Работает в паре с parser.read_file (чтение .txt/.csv) и validator.py
(проверка полей ведомости). Если tkinter недоступен — консольный ввод.
"""

import sys
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

# Белый список расширений — тот же, что в parser.py
ALLOWED_EXTENSIONS = {".txt", ".csv"}


# ---------- Выбор папки и файла ----------

def choose_folder(title: str = "Выберите папку с ведомостями") -> str:
    """Диалог выбора папки. Без GUI — ввод пути с клавиатуры."""
    if GUI_AVAILABLE:
        root = tk.Tk()
        root.withdraw()                      # главное окно не показываем
        folder = filedialog.askdirectory(title=title)
        root.destroy()
        return folder
    return input(f"{title} (путь): ").strip().strip('"')


def choose_file(title: str = "Выберите файл ведомости",
                start_dir: str = ".") -> str:
    """Диалог выбора файла с фильтром по разрешённым расширениям."""
    if GUI_AVAILABLE:
        root = tk.Tk()
        root.withdraw()
        filetypes = [("Ведомости", " ".join(f"*{e}" for e in ALLOWED_EXTENSIONS)),
                     ("Все файлы", "*.*")]
        fname = filedialog.askopenfilename(title=title,
                                           initialdir=start_dir,
                                           filetypes=filetypes)
        root.destroy()
        return fname
    return input(f"{title} (путь): ").strip().strip('"')


# ---------- Проверки ----------

def check_path(raw: str) -> Path:
    """Путь существует? Возвращает абсолютный Path или бросает ошибку."""
    if not raw or not raw.strip():
        raise ValueError("Путь не указан")
    path = Path(raw.strip().strip('"')).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Путь не существует: {path}")
    return path


def check_extension(path: Path) -> Path:
    """Расширение из белого списка? Согласовано с parser.read_file."""
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(
            f"Неподдерживаемое расширение '{path.suffix}'. Разрешены: {allowed}"
        )
    return path


def check_not_empty_file(path: Path) -> Path:
    """Файл не пустой: размер > 0 и есть хотя бы один непробельный символ."""
    if path.stat().st_size == 0:
        raise ValueError(f"Файл пустой (0 байт): {path.name}")
    content = path.read_text(encoding="utf-8")
    if not content.strip():
        raise ValueError(f"Файл '{path.name}' содержит только пустые строки")
    return path


def prepare_file(raw: str) -> Path:
    """Полная проверка файла перед разбором: путь -> расширение -> пустота.

    Возвращает готовый Path; при любой проблеме бросает исключение
    с понятным сообщением (FileNotFoundError / ValueError).
    """
    path = check_path(raw)
    path = check_extension(path)
    return check_not_empty_file(path)
