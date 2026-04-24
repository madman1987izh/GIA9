import re
import pdfplumber
import hashlib
from typing import Optional, List, Tuple
from models import ParsedExamData, ExamAttempt, Subject


class PDFParser:
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Вычисление MD5 хеша файла для проверки дубликатов"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def parse(file_path: str, manual_subject: Optional[str] = None) -> ParsedExamData:
        """Парсинг PDF файла"""
        print(f"Начинаем парсинг файла: {file_path}")

        # Вычисляем хеш файла
        file_hash = PDFParser.calculate_file_hash(file_path)
        print(f"Хеш файла: {file_hash}")

        try:
            with pdfplumber.open(file_path) as pdf:
                full_text = ""
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                        print(f"Страница {page_num + 1}: извлечено {len(text)} символов")

            with open("debug_text.txt", "w", encoding="utf-8") as f:
                f.write(full_text)
            print("Текст сохранён в debug_text.txt")

        except Exception as e:
            print(f"Ошибка при открытии PDF: {e}")
            raise

        # Определяем предмет
        if manual_subject:
            subject = manual_subject
            subject_code = None
        else:
            subject, subject_code = PDFParser._extract_subject_and_code(full_text)

        exam_date = PDFParser._extract_date(full_text)
        region = PDFParser._extract_region(full_text)

        # Парсим участников
        participants = PDFParser._extract_participants_v2(full_text, subject, exam_date)
        print(f"Найдено участников: {len(participants)}")

        return ParsedExamData(
            subject=subject,
            subject_code=subject_code,
            exam_date=exam_date,
            participants=participants,
            region=region,
            file_hash=file_hash
        )

    @staticmethod
    def _extract_subject_and_code(text: str) -> Tuple[str, Optional[str]]:
        """Определение предмета и его кода"""
        match = re.search(r'(\d{2})\s*[-—]\s*([А-Яа-я]+)', text)
        if match:
            code, subject_name = match.groups()
            subject = Subject.from_string(subject_name)
            return subject.value, code
        return Subject.UNKNOWN.value, None

    @staticmethod
    def _extract_date(text: str) -> Optional[str]:
        """Извлечение даты экзамена"""
        match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})', text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"
        return None

    @staticmethod
    def _extract_region(text: str) -> Optional[str]:
        """Извлечение региона"""
        match = re.search(r'(\d+)\s*[-—]\s*([А-Яа-я\s]+(?:Республика|область|край))', text)
        if match:
            return match.group(2).strip()
        return None

    @staticmethod
    def _extract_participants_v2(text: str, subject: str, exam_date: str) -> List[ExamAttempt]:
        """Новая версия парсера участников"""
        participants = []
        lines = text.split('\n')

        for line in lines:
            if len(line) < 30:
                continue

            fio_match = re.search(r'([А-ЯЁ][а-яё]+)\s+([А-ЯЁ][а-яё]+)\s+([А-ЯЁ][а-яё]+)', line)
            if not fio_match:
                continue

            last_name = fio_match.group(1)
            first_name = fio_match.group(2)
            middle_name = fio_match.group(3)

            # Ищем класс
            class_match = re.search(r'(\d+)([А-ЯЁ])', line)
            if class_match:
                class_num = class_match.group(1)
                class_letter = class_match.group(2)
                class_name = f"{class_num}{class_letter}"
            else:
                class_num_match = re.search(r'(\d+)\s+(?:[А-ЯЁ])?', line)
                class_name = class_num_match.group(1) if class_num_match else "9"

            # Ищем ответы
            answers_match = re.search(r'([-+]{10,})', line)
            if answers_match:
                answers_str = answers_match.group(1).replace('+', '*')
            else:
                answers_match = re.search(r'([-+]{5,})', line)
                answers_str = answers_match.group(1).replace('+', '*') if answers_match else ""

            # Ищем баллы
            numbers = re.findall(r'\b(\d{1,2})\b', line)
            primary_score = 0
            grade = 2

            if len(numbers) >= 2:
                primary_score = int(numbers[-2])
                grade = int(numbers[-1])
            elif len(numbers) >= 1:
                primary_score = int(numbers[-1])

            score_matches = re.findall(r'(\d+)\(\d+\)', line)
            short_answer_score = sum(int(s) for s in score_matches) if score_matches else 0

            # Создаём уникальный идентификатор ученика
            student_unique_id = f"{last_name}_{first_name}_{middle_name}_{class_name}"

            participant = ExamAttempt(
                last_name=last_name,
                first_name=first_name,
                middle_name=middle_name,
                class_name=class_name,
                attempt_number=1,
                answers=answers_str if answers_str else "-" * 20,
                short_answer_score=short_answer_score,
                extended_answer_1=0,
                extended_answer_2=0,
                primary_score=primary_score,
                grade=grade,
                subject=subject,
                exam_date=exam_date,
                student_unique_id=student_unique_id
            )
            participants.append(participant)

        return participants