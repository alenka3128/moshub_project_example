import csv
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font


def export_to_excel(
    grades: list[dict],
    quarantine_csv: str | Path = "data/rejected.csv",
    output_path: str | Path = "out/vedomost.xlsx",
):
    """Выгружает ведомость, итоги с формулами и карантин в файл Excel (.xlsx)."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()

    # ==========================================
    # ЛИСТ 1: «Ведомость»
    # ==========================================
    ws_ved = wb.active
    ws_ved.title = "Ведомость"

    headers = ["ФИО", "Зачетка", "Предмет", "Группа", "Преподаватель", "Дата", "Оценка"]
    ws_ved.append(headers)

    for cell in ws_ved[1]:
        cell.font = Font(bold=True)

    for row in grades:
        ws_ved.append([
            row["full_name"],
            row["record_book"],
            row["subject"],
            row["group"],
            row["teacher"],
            row["date"],
            row["grade"],
        ])

    # Закреплённая шапка и автофильтр
    ws_ved.freeze_panes = "A2"
    last_row = max(len(grades) + 1, 2)
    ws_ved.auto_filter.ref = f"A1:G{last_row}"

    # ==========================================
    # ЛИСТ 2: «Итоги» (с живыми формулами СРЗНАЧ и СЧЁТЕСЛИ)
    # ==========================================
    ws_sum = wb.create_sheet(title="Итоги")
    ws_sum.append(["Показатель", "Значение"])
    ws_sum["A1"].font = Font(bold=True)
    ws_sum["B1"].font = Font(bold=True)

    # Формула СРЗНАЧ (в openpyxl пишется на английском AVERAGE)
    ws_sum.append(["Средний балл (по числовым оценкам)", f"=AVERAGE(Ведомость!G2:G{last_row})"])

    # Формулы СЧЁТЕСЛИ (в openpyxl пишется COUNTIF)
    grade_labels = [
        ("Количество оценок «5»", 5),
        ("Количество оценок «4»", 4),
        ("Количество оценок «3»", 3),
        ("Количество оценок «2»", 2),
        ("Количество «зачет»", '"зачет"'),
        ("Количество «незачет»", '"незачет"'),
    ]
    for title, criteria in grade_labels:
        ws_sum.append([title, f"=COUNTIF(Ведомость!G2:G{last_row}, {criteria})"])

    # ==========================================
    # ЛИСТ 3: «Карантин»
    # ==========================================
    ws_quar = wb.create_sheet(title="Карантин")
    q_headers = ["Номер строки", "Поле с ошибкой", "Причина отказа", "Исходная строка"]
    ws_quar.append(q_headers)
    for cell in ws_quar[1]:
        cell.font = Font(bold=True)

    q_path = Path(quarantine_csv)
    if q_path.exists():
        with q_path.open("r", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=";")
            next(reader, None)  # пропускаем заголовок CSV
            for q_row in reader:
                ws_quar.append(q_row)

    # Автоподбор ширины колонок для аккуратного отображения в LibreOffice / Excel
    for ws in (ws_ved, ws_sum, ws_quar):
        for col in ws.columns:
            max_len = max((len(str(c.value or "")) for c in col), default=10)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)

    wb.save(out_file)
    return out_file