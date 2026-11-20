from pathlib import Path
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError

Base = declarative_base()


# 1. Таблица учебных групп
class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)


# 2. Таблица студентов
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String, nullable=False)
    record_book = Column(String, unique=True, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)


# 3. Таблица преподавателей
class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String, unique=True, nullable=False)


# 4. Таблица дисциплин (предметов)
class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)


# 5. Справочник видов оценок
class GradeType(Base):
    __tablename__ = "grade_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(String, unique=True, nullable=False)
    is_passed = Column(Boolean, nullable=False, default=False)


# 6. Журнал загрузок ведомостей
class ImportLog(Base):
    __tablename__ = "import_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False)
    imported_at = Column(String, nullable=False)
    accepted_count = Column(Integer, nullable=False)
    rejected_count = Column(Integer, nullable=False)


# 7. Главная таблица оценок (связывает все справочники)
class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    grade_type_id = Column(Integer, ForeignKey("grade_types.id"), nullable=False)
    exam_date = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", "exam_date", name="uix_grade"),
    )


class Database:
    def __init__(self, db_path: str = "data/vedomosti.db"):
        if db_path == ":memory:":
            db_url = "sqlite:///:memory:"
        else:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite:///{db_path}"

        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self._seed_grade_types()

    def _seed_grade_types(self):
        """Заполняет справочник оценок при первом запуске."""
        if self.session.query(GradeType).count() == 0:
            types = [
                GradeType(value="5", is_passed=True),
                GradeType(value="4", is_passed=True),
                GradeType(value="3", is_passed=True),
                GradeType(value="2", is_passed=False),
                GradeType(value="зачет", is_passed=True),
                GradeType(value="незачет", is_passed=False),
            ]
            self.session.add_all(types)
            self.session.commit()

    def _get_or_create(self, model, **kwargs):
        """Ищет запись в справочнике или создает новую, если её еще нет."""
        instance = self.session.query(model).filter_by(**kwargs).first()
        if not instance:
            instance = model(**kwargs)
            self.session.add(instance)
            self.session.flush()
        return instance

    def insert_grade(self, record: dict) -> bool:
        """Раскладывает данные по 7 таблицам и сохраняет оценку."""
        try:
            group = self._get_or_create(Group, name=record["group"])

            student = self.session.query(Student).filter_by(
                record_book=record["record_book"]
            ).first()
            if not student:
                student = Student(
                    full_name=record["full_name"],
                    record_book=record["record_book"],
                    group_id=group.id,
                )
                self.session.add(student)
                self.session.flush()

            teacher = self._get_or_create(Teacher, full_name=record["teacher"])
            subject = self._get_or_create(Subject, name=record["subject"])

            grade_type = self.session.query(GradeType).filter_by(
                value=record["grade"]
            ).first()
            if not grade_type:
                is_passed = record["grade"] in ("3", "4", "5", "зачет")
                grade_type = self._get_or_create(
                    GradeType, value=record["grade"], is_passed=is_passed
                )

            new_grade = Grade(
                student_id=student.id,
                subject_id=subject.id,
                teacher_id=teacher.id,
                grade_type_id=grade_type.id,
                exam_date=record["date"],
            )
            self.session.add(new_grade)
            self.session.commit()
            return True

        except IntegrityError:
            self.session.rollback()
            return False

    def log_import(self, filename: str, accepted: int, rejected: int):
        """Записывает результат импорта файла в журнал загрузок."""
        log = ImportLog(
            filename=filename,
            imported_at=datetime.now().isoformat(timespec="seconds"),
            accepted_count=accepted,
            rejected_count=rejected,
        )
        self.session.add(log)
        self.session.commit()

    def get_statistics(self) -> dict:
        """Собирает сводку по оценкам через объединение таблиц (JOIN)."""
        total = self.session.query(func.count(Grade.id)).scalar()

        if not total:
            return {"total": 0, "distribution": {}, "pass_rate": 0.0}

        rows = (
            self.session.query(GradeType.value, func.count(Grade.id))
            .select_from(Grade)
            .join(GradeType, Grade.grade_type_id == GradeType.id)
            .group_by(GradeType.value)
            .all()
        )
        distribution = dict(rows)

        passed = (
            self.session.query(func.count(Grade.id))
            .select_from(Grade)
            .join(GradeType, Grade.grade_type_id == GradeType.id)
            .filter(GradeType.is_passed.is_(True))
            .scalar()
        )

        pass_rate = round((passed / total) * 100, 1)

        return {
            "total": total,
            "distribution": distribution,
            "pass_rate": pass_rate,
        }

    def close(self):
        self.session.close()
        self.engine.dispose()


if __name__ == "__main__":
    db = Database()
    print("База данных из 7 связанных таблиц создана!")
    db.close()