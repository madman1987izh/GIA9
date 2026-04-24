import sqlite3
from typing import List, Optional, Dict


class Database:
    def __init__(self, db_path: str = "exam_results.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def column_exists(self, cursor, table_name: str, column_name: str) -> bool:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        return any(column[1] == column_name for column in columns)

    def init_db(self):
        """Создание таблиц и миграция"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Таблица exams
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exams (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        subject TEXT,
                        subject_code TEXT,
                        exam_date TEXT,
                        region TEXT,
                        file_hash TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Добавляем колонку file_hash если её нет
                if not self.column_exists(cursor, 'exams', 'file_hash'):
                    cursor.execute('ALTER TABLE exams ADD COLUMN file_hash TEXT')

                # Таблица exam_attempts
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exam_attempts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        exam_id INTEGER,
                        subject TEXT,
                        last_name TEXT,
                        first_name TEXT,
                        middle_name TEXT,
                        class TEXT,
                        attempt_number INTEGER,
                        answers TEXT,
                        short_answer_score INTEGER,
                        extended_answer_1 INTEGER,
                        extended_answer_2 INTEGER,
                        primary_score INTEGER,
                        grade INTEGER,
                        retake_date TEXT,
                        exam_date TEXT,
                        student_unique_id TEXT,
                        FOREIGN KEY (exam_id) REFERENCES exams(id)
                    )
                ''')

                # Добавляем колонку student_unique_id если её нет
                if not self.column_exists(cursor, 'exam_attempts', 'student_unique_id'):
                    cursor.execute('ALTER TABLE exam_attempts ADD COLUMN student_unique_id TEXT')

                # Создаём уникальный индекс для предотвращения дублирования
                cursor.execute('''
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_student_exam 
                    ON exam_attempts(exam_id, student_unique_id)
                ''')

                # Создаём индексы
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_subject ON exam_attempts(subject)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_class ON exam_attempts(class)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_name ON exam_attempts(last_name, first_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_exam_id ON exam_attempts(exam_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_hash ON exams(file_hash)')

                conn.commit()
                print("База данных инициализирована успешно")

        except Exception as e:
            print(f"Ошибка инициализации БД: {e}")
            raise

    def exam_exists(self, file_hash: str) -> Optional[int]:
        """Проверка, существует ли экзамен с таким хешем файла"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM exams WHERE file_hash = ?", (file_hash,))
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"Ошибка проверки существования экзамена: {e}")
            return None

    def save_exam(self, exam) -> int:
        """Сохранить экзамен, вернуть ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO exams (subject, subject_code, exam_date, region, file_hash)
                    VALUES (?, ?, ?, ?, ?)
                ''', (exam.subject, exam.exam_code, exam.exam_date,
                      getattr(exam, 'region', None), getattr(exam, 'file_hash', None)))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Ошибка сохранения экзамена: {e}")
            raise

    def save_attempt(self, attempt):
        """Сохранить попытку"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO exam_attempts 
                    (exam_id, subject, last_name, first_name, middle_name, class,
                     attempt_number, answers, short_answer_score,
                     extended_answer_1, extended_answer_2, primary_score,
                     grade, retake_date, exam_date, student_unique_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    attempt.exam_id, attempt.subject, attempt.last_name, attempt.first_name,
                    attempt.middle_name, attempt.class_name, attempt.attempt_number,
                    attempt.answers, attempt.short_answer_score,
                    attempt.extended_answer_1, attempt.extended_answer_2,
                    attempt.primary_score, attempt.grade, attempt.retake_date,
                    attempt.exam_date, attempt.student_unique_id
                ))
                conn.commit()
        except sqlite3.IntegrityError:
            print(f"Дубликат пропущен: {attempt.last_name} {attempt.first_name}")
        except Exception as e:
            print(f"Ошибка сохранения попытки: {e}")
            raise

    def save_attempts_batch(self, attempts, progress_callback=None):
        """Массовое сохранение попыток с прогрессом"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                total = len(attempts)
                saved = 0
                duplicates = 0

                for i, attempt in enumerate(attempts):
                    try:
                        cursor.execute('''
                            INSERT INTO exam_attempts 
                            (exam_id, subject, last_name, first_name, middle_name, class,
                             attempt_number, answers, short_answer_score,
                             extended_answer_1, extended_answer_2, primary_score,
                             grade, retake_date, exam_date, student_unique_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            attempt.exam_id, attempt.subject, attempt.last_name, attempt.first_name,
                            attempt.middle_name, attempt.class_name, attempt.attempt_number,
                            attempt.answers, attempt.short_answer_score,
                            attempt.extended_answer_1, attempt.extended_answer_2,
                            attempt.primary_score, attempt.grade, attempt.retake_date,
                            attempt.exam_date, attempt.student_unique_id
                        ))
                        saved += 1
                    except sqlite3.IntegrityError:
                        duplicates += 1

                    if progress_callback:
                        progress_callback(i + 1, total)

                conn.commit()
                print(f"Сохранено {saved} попыток, пропущено дубликатов: {duplicates}")
                return saved, duplicates
        except Exception as e:
            print(f"Ошибка массового сохранения: {e}")
            raise

    def get_duplicate_exams(self) -> List[Dict]:
        """Найти дублирующиеся экзамены"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT subject, exam_date, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
                    FROM exams
                    GROUP BY subject, exam_date
                    HAVING COUNT(*) > 1
                    ORDER BY subject, exam_date
                ''')

                duplicates = []
                for row in cursor.fetchall():
                    ids = [int(x) for x in row[3].split(',')]
                    duplicates.append({
                        'subject': row[0],
                        'exam_date': row[1],
                        'count': row[2],
                        'ids': ids
                    })
                return duplicates
        except Exception as e:
            print(f"Ошибка поиска дубликатов: {e}")
            return []

    def delete_exam(self, exam_id: int) -> bool:
        """Удалить экзамен и все связанные с ним попытки"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Сначала удаляем связанные попытки
                cursor.execute("DELETE FROM exam_attempts WHERE exam_id = ?", (exam_id,))
                # Затем удаляем сам экзамен
                cursor.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка удаления экзамена: {e}")
            return False

    def delete_duplicate_exams(self, keep_first: bool = True) -> int:
        """Удалить дублирующиеся экзамены, оставляя первый или последний"""
        try:
            duplicates = self.get_duplicate_exams()
            deleted_count = 0

            for dup in duplicates:
                ids = dup['ids']
                if keep_first:
                    # Оставляем первый, удаляем остальные
                    to_delete = ids[1:]
                else:
                    # Оставляем последний, удаляем остальные
                    to_delete = ids[:-1]

                for exam_id in to_delete:
                    if self.delete_exam(exam_id):
                        deleted_count += 1

            return deleted_count
        except Exception as e:
            print(f"Ошибка удаления дубликатов: {e}")
            return 0

    def get_all_exams(self) -> List[Dict]:
        """Получить список всех экзаменов"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT e.id, e.subject, e.exam_date, e.region, e.created_at,
                           COUNT(a.id) as students_count
                    FROM exams e
                    LEFT JOIN exam_attempts a ON e.id = a.exam_id
                    GROUP BY e.id
                    ORDER BY e.created_at DESC
                ''')

                exams = []
                for row in cursor.fetchall():
                    exams.append({
                        'id': row[0],
                        'subject': row[1],
                        'exam_date': row[2],
                        'region': row[3],
                        'created_at': row[4],
                        'students_count': row[5]
                    })
                return exams
        except Exception as e:
            print(f"Ошибка получения списка экзаменов: {e}")
            return []

    def get_student_report(self, last_name: str = None, first_name: str = None, class_name: str = None) -> List:
        """Получить отчёт по ученикам (без дубликатов)"""
        from models import ExamAttempt

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                query = '''
                    SELECT DISTINCT last_name, first_name, middle_name, class, subject, 
                           exam_date, primary_score, grade, attempt_number
                    FROM exam_attempts
                    WHERE attempt_number = 1
                '''
                params = []

                if last_name:
                    query += " AND last_name = ?"
                    params.append(last_name)
                if first_name:
                    query += " AND first_name = ?"
                    params.append(first_name)
                if class_name:
                    query += " AND class = ?"
                    params.append(class_name)

                query += " ORDER BY class, last_name, first_name, exam_date"

                cursor.execute(query, params)
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'last_name': row[0],
                        'first_name': row[1],
                        'middle_name': row[2],
                        'class': row[3],
                        'subject': row[4],
                        'exam_date': row[5],
                        'primary_score': row[6],
                        'grade': row[7],
                        'attempt': row[8]
                    })
                return results
        except Exception as e:
            print(f"Ошибка получения отчёта: {e}")
            return []

    def get_stats_by_subject_and_class(self, subject: Optional[str] = None) -> Dict:
        """Получить статистику по предметам и классам (без дубликатов)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                result = {
                    'total': {'5': 0, '4': 0, '3': 0, '2': 0, 'total': 0},
                    'by_class': {},
                    'by_subject': {}
                }

                if subject:
                    cursor.execute('''
                        SELECT grade, COUNT(DISTINCT student_unique_id) 
                        FROM exam_attempts 
                        WHERE subject = ? AND attempt_number = 1
                        GROUP BY grade
                    ''', (subject,))
                    for grade, count in cursor.fetchall():
                        result['total'][str(grade)] = count
                        result['total']['total'] += count
                else:
                    cursor.execute('''
                        SELECT subject, grade, COUNT(DISTINCT student_unique_id) 
                        FROM exam_attempts 
                        WHERE attempt_number = 1
                        GROUP BY subject, grade
                    ''')
                    for subj, grade, count in cursor.fetchall():
                        if subj not in result['by_subject']:
                            result['by_subject'][subj] = {'5': 0, '4': 0, '3': 0, '2': 0, 'total': 0}
                        result['by_subject'][subj][str(grade)] = count
                        result['by_subject'][subj]['total'] += count
                        result['total'][str(grade)] = result['total'].get(str(grade), 0) + count
                        result['total']['total'] += count

                # Статистика по классам
                if subject:
                    cursor.execute('''
                        SELECT class, grade, COUNT(DISTINCT student_unique_id) 
                        FROM exam_attempts 
                        WHERE subject = ? AND attempt_number = 1
                        GROUP BY class, grade
                    ''', (subject,))
                else:
                    cursor.execute('''
                        SELECT class, grade, COUNT(DISTINCT student_unique_id) 
                        FROM exam_attempts 
                        WHERE attempt_number = 1
                        GROUP BY class, grade
                    ''')

                for class_name, grade, count in cursor.fetchall():
                    if class_name not in result['by_class']:
                        result['by_class'][class_name] = {'5': 0, '4': 0, '3': 0, '2': 0, 'total': 0}
                    result['by_class'][class_name][str(grade)] = count
                    result['by_class'][class_name]['total'] += count

                return result
        except Exception as e:
            print(f"Ошибка получения статистики: {e}")
            return {'total': {'5': 0, '4': 0, '3': 0, '2': 0, 'total': 0}, 'by_class': {}, 'by_subject': {}}

    def get_subjects_list(self) -> List[str]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT DISTINCT subject FROM exam_attempts WHERE subject IS NOT NULL AND subject != '' ORDER BY subject")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Ошибка получения списка предметов: {e}")
            return []

    def get_classes_list(self) -> List[str]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT DISTINCT class FROM exam_attempts WHERE class IS NOT NULL AND class != '' ORDER BY class")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Ошибка получения списка классов: {e}")
            return []

    def close(self):
        pass