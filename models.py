from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum


class Subject(str, Enum):
    GEOGRAPHY = "География"
    RUSSIAN = "Русский язык"
    MATH = "Математика"
    PHYSICS = "Физика"
    CHEMISTRY = "Химия"
    BIOLOGY = "Биология"
    HISTORY = "История"
    SOCIAL = "Обществознание"
    ENGLISH = "Английский язык"
    LITERATURE = "Литература"
    INFORMATICS = "Информатика"
    UNKNOWN = "Не определен"

    @classmethod
    def from_string(cls, text: str) -> 'Subject':
        text_lower = text.lower()

        subject_map = {
            'географи': cls.GEOGRAPHY,
            'геогр': cls.GEOGRAPHY,
            'русск': cls.RUSSIAN,
            'русский': cls.RUSSIAN,
            'математ': cls.MATH,
            'математик': cls.MATH,
            'физик': cls.PHYSICS,
            'хими': cls.CHEMISTRY,
            'биолог': cls.BIOLOGY,
            'истори': cls.HISTORY,
            'обществоз': cls.SOCIAL,
            'общество': cls.SOCIAL,
            'англ': cls.ENGLISH,
            'английск': cls.ENGLISH,
            'литератур': cls.LITERATURE,
            'информат': cls.INFORMATICS,
        }

        for key, subject in subject_map.items():
            if key in text_lower:
                return subject
        return cls.UNKNOWN

    @classmethod
    def get_all_subjects(cls) -> List[str]:
        return [
            cls.MATH.value,
            cls.RUSSIAN.value,
            cls.GEOGRAPHY.value,
            cls.PHYSICS.value,
            cls.CHEMISTRY.value,
            cls.BIOLOGY.value,
            cls.HISTORY.value,
            cls.SOCIAL.value,
            cls.ENGLISH.value,
            cls.LITERATURE.value,
            cls.INFORMATICS.value
        ]


@dataclass
class Exam:
    subject: str
    exam_date: Optional[str]
    exam_code: Optional[str] = None
    region: Optional[str] = None
    file_hash: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None


@dataclass
class ExamAttempt:
    last_name: str
    first_name: str
    middle_name: str
    class_name: str
    attempt_number: int
    answers: str
    short_answer_score: int
    extended_answer_1: int
    extended_answer_2: int
    primary_score: int
    grade: int
    exam_id: Optional[int] = None
    retake_date: Optional[str] = None
    id: Optional[int] = None
    subject: Optional[str] = None
    exam_date: Optional[str] = None
    student_unique_id: Optional[str] = None  # Уникальный идентификатор ученика

    def __repr__(self):
        return f"{self.last_name} {self.first_name} (класс {self.class_name}, {self.subject}, оценка {self.grade})"

    def get_full_name(self) -> str:
        return f"{self.last_name} {self.first_name} {self.middle_name}"


@dataclass
class ParsedExamData:
    subject: str
    subject_code: Optional[str]
    exam_date: Optional[str]
    participants: List[ExamAttempt]
    region: Optional[str] = None
    file_hash: Optional[str] = None