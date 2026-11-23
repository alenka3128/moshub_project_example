import random
from datetime import date, timedelta
from faker import Faker
from database import Database

# Инициализируем генератор русских данных
fake = Faker("ru_RU")

SUBJECTS = [
    "Базы данных",
    "Программирование на Python",
    "Алгоритмы и структуры данных",
    "Операционные системы",
    "Компьютерные сети",
    "Математический анализ",
    "Дискретная математика",
]

GROUPS = ["ИВТ-21", "ИВТ-22", "ПИ-21", "ПИ-22", "ИБ-23"]
GRADES = ["5", "4", "3", "2", "зачет", "незачет"]


def generate_100_records(db_path: str = "data/vedomosti.db"):
    db = Database(db_path)

    # Заранее создаем 5 постоянных преподавателей и 35 студентов,
    # чтобы в таблицах справочников не было по 100 одинаковых записей
    teachers = [
        f"{fake.last_name_male()} {fake.first_name_male()[0]}.{fake.middle_name_male()[0]}."
        for _ in range(5)
    ]

    students = []
    for i in range(1, 36):
        group = random.choice(GROUPS)
        students.append({
            "full_name": fake.name(),
            "record_book": f"22-{group}-{i:03d}",
            "group": group,
        })

    added_count = 0
    # Генерируем оценки, пока в основной таблице не наберется ровно 100 уникальных записей
    while added_count < 100:
        student = random.choice(students)
        days_ago = random.randint(1, 180)
        exam_date = (date.today() - timedelta(days=days_ago)).isoformat()

        record = {
            "full_name": student["full_name"],
            "record_book": student["record_book"],
            "subject": random.choice(SUBJECTS),
            "group": student["group"],
            "teacher": random.choice(teachers),
            "date": exam_date,
            "grade": random.choices(GRADES, weights=[30, 35, 20, 5, 8, 2])[0],
        }

        if db.insert_grade(record):
            added_count += 1

    # Записываем факт генерации в журнал загрузок
    db.log_import("faker_seed_100.py", accepted=added_count, rejected=0)

    stats = db.get_statistics()
    print(f"Успешно добавлено уникальных записей: {added_count}")
    print(f"Всего оценок в базе: {stats['total']}")
    print(f"Распределение оценок: {stats['distribution']}")
    print(f"Процент успевающих: {stats['pass_rate']}%")

    db.close()


if __name__ == "__main__":
    generate_100_records()