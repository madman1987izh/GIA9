from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QLabel, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class ExamManagerWidget(QWidget):
    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Информационная группа
        info_group = QGroupBox("Управление экзаменами")
        info_layout = QHBoxLayout(info_group)

        self.btn_refresh = QPushButton("🔄 Обновить список")
        self.btn_refresh.clicked.connect(self.refresh_list)
        info_layout.addWidget(self.btn_refresh)

        self.btn_check_duplicates = QPushButton("🔍 Найти дубликаты")
        self.btn_check_duplicates.clicked.connect(self.check_duplicates)
        info_layout.addWidget(self.btn_check_duplicates)

        self.btn_delete_duplicates = QPushButton("🗑️ Удалить дубликаты")
        self.btn_delete_duplicates.clicked.connect(self.delete_duplicates)
        info_layout.addWidget(self.btn_delete_duplicates)

        self.btn_delete_selected = QPushButton("❌ Удалить выбранные")
        self.btn_delete_selected.clicked.connect(self.delete_selected)
        info_layout.addWidget(self.btn_delete_selected)

        layout.addWidget(info_group)

        # Таблица экзаменов
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Предмет", "Дата экзамена", "Регион", "Учеников", "Дата импорта"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

        # Статус
        self.status_label = QLabel("Готов")
        self.status_label.setStyleSheet("color: gray; padding: 5px;")
        layout.addWidget(self.status_label)

    def refresh_list(self):
        """Обновить список экзаменов"""
        if not self.main_window:
            return

        exams = self.main_window.db.get_all_exams()

        self.table.setRowCount(len(exams))

        for row, exam in enumerate(exams):
            self.table.setItem(row, 0, QTableWidgetItem(str(exam['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(exam['subject']))
            self.table.setItem(row, 2, QTableWidgetItem(exam['exam_date'] or "не указана"))
            self.table.setItem(row, 3, QTableWidgetItem(exam['region'] or "не указан"))
            self.table.setItem(row, 4, QTableWidgetItem(str(exam['students_count'])))
            self.table.setItem(row, 5, QTableWidgetItem(exam['created_at'][:19] if exam['created_at'] else ""))

            # Подсветка дубликатов
            if self.is_duplicate(exam['subject'], exam['exam_date'], exams, exam['id']):
                for col in range(6):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(QColor(255, 255, 200))

        self.status_label.setText(f"Загружено {len(exams)} экзаменов")

    def is_duplicate(self, subject, exam_date, exams, current_id):
        """Проверка, является ли экзамен дубликатом"""
        count = 0
        for exam in exams:
            if exam['subject'] == subject and exam['exam_date'] == exam_date:
                count += 1
        return count > 1

    def check_duplicates(self):
        """Проверка на дубликаты"""
        if not self.main_window:
            return

        duplicates = self.main_window.db.get_duplicate_exams()

        if not duplicates:
            QMessageBox.information(self, "Дубликаты не найдены",
                                    "В базе данных нет дублирующихся экзаменов.")
            return

        message = "Найдены следующие дубликаты:\n\n"
        for dup in duplicates:
            message += f"• {dup['subject']} ({dup['exam_date']}) - {dup['count']} копий\n"

        message += f"\nВсего найдено {len(duplicates)} групп дубликатов."

        QMessageBox.warning(self, "Найдены дубликаты", message)

    def delete_duplicates(self):
        """Удалить дубликаты экзаменов"""
        if not self.main_window:
            return

        duplicates = self.main_window.db.get_duplicate_exams()

        if not duplicates:
            QMessageBox.information(self, "Дубликаты не найдены",
                                    "В базе данных нет дублирующихся экзаменов.")
            return

        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Будет удалено {len(duplicates)} групп дубликатов.\n"
            "Будут оставлены только первые экземпляры.\n\n"
            "Вы уверены, что хотите продолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            deleted = self.main_window.db.delete_duplicate_exams(keep_first=True)
            QMessageBox.information(self, "Готово", f"Удалено {deleted} дублирующихся экзаменов.")
            self.refresh_list()
            self.main_window.stats_tab.refresh_stats()
            self.main_window.update_subjects_filter()

    def delete_selected(self):
        """Удалить выбранные экзамены"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            QMessageBox.warning(self, "Нет выбора", "Выберите экзамены для удаления.")
            return

        exam_ids = []
        exam_names = []

        for row in selected_rows:
            exam_id = int(self.table.item(row, 0).text())
            subject = self.table.item(row, 1).text()
            exam_date = self.table.item(row, 2).text()
            exam_ids.append(exam_id)
            exam_names.append(f"{subject} ({exam_date})")

        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Вы уверены, что хотите удалить следующие экзамены?\n\n" + "\n".join(exam_names),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            deleted = 0
            for exam_id in exam_ids:
                if self.main_window.db.delete_exam(exam_id):
                    deleted += 1

            QMessageBox.information(self, "Готово", f"Удалено {deleted} экзаменов.")
            self.refresh_list()
            self.main_window.stats_tab.refresh_stats()
            self.main_window.update_subjects_filter()