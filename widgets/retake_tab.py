from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QGroupBox, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView
)
from datetime import datetime
from models import ExamAttempt


class RetakeTab(QWidget):
    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Выбор ученика
        select_group = QGroupBox("Добавление пересдачи")
        select_layout = QHBoxLayout(select_group)

        select_layout.addWidget(QLabel("Ученик:"))
        self.cmb_student = QComboBox()
        self.cmb_student.setMinimumWidth(300)
        select_layout.addWidget(self.cmb_student)

        select_layout.addWidget(QLabel("Новая оценка:"))
        self.cmb_new_grade = QComboBox()
        self.cmb_new_grade.addItems(["3", "4", "5"])  # Пересдать можно на 3,4,5
        select_layout.addWidget(self.cmb_new_grade)

        self.btn_add_retake = QPushButton("➕ Добавить пересдачу")
        self.btn_add_retake.clicked.connect(self.add_retake)
        select_layout.addWidget(self.btn_add_retake)

        layout.addWidget(select_group)

        # Таблица пересдач
        self.retake_table = QTableWidget()
        self.retake_table.setColumnCount(7)
        self.retake_table.setHorizontalHeaderLabels([
            "ФИО", "Класс", "Оригинальная оценка",
            "Новая оценка", "Дата пересдачи", "Новый балл", "Примечание"
        ])
        # Исправляем resize mode
        header = self.retake_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Растягиваем ФИО
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.retake_table)

        # Кнопка сохранения
        self.btn_save_retakes = QPushButton("💾 Сохранить пересдачи в БД")
        self.btn_save_retakes.clicked.connect(self.save_retakes)
        layout.addWidget(self.btn_save_retakes)

        self.retakes_list = []
        self.original_participants = []

    def update_students_list(self, participants):
        """Обновление списка учеников"""
        self.original_participants = [p for p in participants if p.attempt_number == 1]
        self.cmb_student.clear()
        for student in self.original_participants:
            if student.grade == 2:  # Показываем только двоечников
                self.cmb_student.addItem(
                    f"{student.last_name} {student.first_name} {student.middle_name} "
                    f"(класс {student.class_name}, оценка {student.grade})",
                    student
                )

        if self.cmb_student.count() == 0:
            self.cmb_student.addItem("Нет двоечников для пересдачи", None)
            self.btn_add_retake.setEnabled(False)
        else:
            self.btn_add_retake.setEnabled(True)

    def add_retake(self):
        """Добавление пересдачи"""
        idx = self.cmb_student.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите ученика")
            return

        original = self.cmb_student.currentData()
        if original is None:
            QMessageBox.warning(self, "Ошибка", "Нет данных о ученике")
            return

        new_grade = int(self.cmb_new_grade.currentText())

        # Создаём новую попытку
        retake = ExamAttempt(
            last_name=original.last_name,
            first_name=original.first_name,
            middle_name=original.middle_name,
            class_name=original.class_name,
            attempt_number=original.attempt_number + 1,
            answers=original.answers,
            short_answer_score=original.short_answer_score,
            extended_answer_1=original.extended_answer_1,
            extended_answer_2=original.extended_answer_2,
            primary_score=original.primary_score,
            grade=new_grade,
            retake_date=datetime.now().strftime("%Y-%m-%d")
        )

        self.retakes_list.append(retake)
        self.update_retake_table()

        # Удаляем из списка доступных
        self.cmb_student.removeItem(idx)
        if self.cmb_student.count() == 0:
            self.cmb_student.addItem("Нет двоечников для пересдачи", None)
            self.btn_add_retake.setEnabled(False)

        QMessageBox.information(self, "Пересдача добавлена",
                                f"Для {original.last_name} {original.first_name} "
                                f"добавлена пересдача с оценкой {new_grade}")

    def update_retake_table(self):
        """Обновление таблицы пересдач"""
        self.retake_table.setRowCount(len(self.retakes_list))
        for row, retake in enumerate(self.retakes_list):
            self.retake_table.setItem(row, 0, QTableWidgetItem(
                f"{retake.last_name} {retake.first_name} {retake.middle_name}"
            ))
            self.retake_table.setItem(row, 1, QTableWidgetItem(retake.class_name))
            # Находим оригинальную оценку
            original_grade = 2  # По умолчанию
            for orig in self.original_participants:
                if (orig.last_name == retake.last_name and
                        orig.first_name == retake.first_name):
                    original_grade = orig.grade
                    break
            self.retake_table.setItem(row, 2, QTableWidgetItem(str(original_grade)))
            self.retake_table.setItem(row, 3, QTableWidgetItem(str(retake.grade)))
            self.retake_table.setItem(row, 4, QTableWidgetItem(retake.retake_date or ""))
            self.retake_table.setItem(row, 5, QTableWidgetItem(str(retake.primary_score)))
            self.retake_table.setItem(row, 6, QTableWidgetItem("Пересдача"))

    def save_retakes(self):
        """Сохранение пересдач"""
        if not self.retakes_list:
            QMessageBox.warning(self, "Нет данных", "Нет добавленных пересдач")
            return

        if self.main_window:
            self.main_window.save_retakes(self.retakes_list)
            QMessageBox.information(self, "Успех", f"Сохранено {len(self.retakes_list)} пересдач")
            self.retakes_list.clear()
            self.retake_table.setRowCount(0)
        else:
            QMessageBox.warning(self, "Ошибка", "Нет связи с главным окном")

    def get_retakes(self):
        return self.retakes_list

    def clear_retakes(self):
        self.retakes_list.clear()
        self.retake_table.setRowCount(0)