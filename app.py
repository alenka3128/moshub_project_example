import sys
from pathlib import Path
from database import Database
from importer import run_import
from quarantine import Quarantine
from seed_data import generate_100_records
from excel_export import export_to_excel


def select_file_path() -> str:
    """Открывает окно проводника или запрашивает путь в консоли."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            title="Выберите файл ведомости",
            filetypes=[("Ведомости", "*.txt *.csv"), ("Все файлы", "*.*")],
        )
        root.destroy()
        if path:
            return path
    except Exception:
        pass
    return input("Введите путь к файлу ведомости: ").strip().strip('"')


def main():
    # Второй аргумент (если передан из тестов) — путь к БД, иначе основная
    db_path = sys.argv[2] if len(sys.argv) >= 3 else "data/vedomosti.db"
    db = Database(db_path)

    # 1. Если основная база пустая — наполняем её на 100 записей через Faker
    if db_path == "data/vedomosti.db" and db.get_statistics()["total"] == 0:
        print("База данных пуста. Генерируем 100 тестовых записей через Faker...")
        db.close()
        generate_100_records(db_path)
        db = Database(db_path)

    # 2. Получаем путь к файлу (из первого аргумента или через выбор файла)
    if len(sys.argv) >= 2:
        raw_path = sys.argv[1]
    else:
        print("\nВыберите файл ведомости (.csv или .txt) для загрузки...")
        raw_path = select_file_path()

    if raw_path:
        target_file = Path(raw_path)
        if not target_file.exists():
            print(f"Ошибка: файл '{target_file}' не найден.", file=sys.stderr)
            db.close()
            sys.exit(1)

        print(f"\nОбработка файла: {target_file.name}")

        # Файл карантина сохраняем рядом с базой данных
        quarantine_path = Path(db_path).parent / "rejected.csv"
        quarantine = Quarantine(str(quarantine_path))

        accepted, rejected = run_import(str(target_file), quarantine, db)
        db.log_import(target_file.name, accepted=accepted, rejected=rejected)

        print(f"Импорт завершен. Принято: {accepted}, Отклонено: {rejected}")
        for row_num, field, reason, _ in quarantine.rows:
            print(f"  - Строка {row_num} [{field}]: {reason}")

        if rejected > 0:
            print(f"Отклонённые строки сохранены в карантин: {quarantine_path}")

    # 3. Выводим итоговую сводку по всей базе данных
    stats = db.get_statistics()
    dist_str = ", ".join(
        f"{grade}: {count}" for grade, count in stats["distribution"].items()
    )

    print("\n=== СВОДКА ПО БАЗЕ ДАННЫХ ===")
    print(f"Всего оценок в базе: {stats['total']}")
    print(f"Распределение оценок: {dist_str}")
    print(f"Процент успевающих: {stats['pass_rate']}%")
    
    # 4. Выгрузка в Excel (пункт меню / автоматический вопрос при интерактивном запуске)
    if len(sys.argv) < 2 or "--excel" in sys.argv:
        choice = input("\nВыгрузить данные в Excel (out/vedomost.xlsx)? [y/n]: ").strip().lower()
        if choice in ("y", "д", "да", "yes", ""):
            out_path = export_to_excel(
                grades=db.get_all_grades(),
                quarantine_csv=Path(db_path).parent / "rejected.csv",
                output_path="out/vedomost.xlsx",
            )
            print(f"Готово! Отчёт успешно выгружен в {out_path}")

    db.close()


if __name__ == "__main__":
    main()