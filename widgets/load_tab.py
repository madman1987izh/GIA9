from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QFileDialog,
    QMessageBox, QProgressBar, QGroupBox,
    QFormLayout, QLabel, QHeaderView, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from pdf_parser import PDFParser
from models import ParsedExamData, ExamAttempt, Subject


class ParseThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(ParsedExamData)
    error = pyqtSignal(str)

    def __init__(self, file_path, manual_subject=None):
        super().__init__()
        self.file_path = file_path
        self.manual_subject = manual_subject

    def run(self):
        try:
            data = PDFParser.parse(self.file_path, manual_subject=self.manual_subject)
            self.progress.emit(100)
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))


class LoadTab(QWidget):
    data_loaded = pyqtSignal(ParsedExamData)

    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.current_data = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Информационная панель
        info_group = QGroupBox("Информация об экзамене")
        info_layout = QFormLayout(info_group)
        self.lbl_subject = QLabel("Не загружен")
        self.lbl_subject.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.lbl_exam_date = QLabel("Не загружена")
        info_layout.addRow("Предмет:", self.lbl_subject)
        info_layout.addRow("Дата экзамена:", self.lbl_exam_date)
        layout.addWidget(info_group)

        # Панель выбора предмета для импорта
        import_group = QGroupBox("Настройки импорта")
        import_layout = QHBoxLayout(import_group)

        import_layout.addWidget(QLabel("Выберите предмет:"))
        self.subject_combo = QComboBox()
        # Уникальные предметы из Enum
        unique_subjects = list(dict.fromkeys(Subject.get_all_subjects()))
        self.subject_combo.addItems(unique_subjects)
        self.subject_combo.setCurrentText("Математика")
        import_layout.addWidget(self.subject_combo)

        self.use_auto_detect = QPushButton("🔍 Автоопределение")
        self.use_auto_detect.clicked.connect(self.set_auto_detect)
        import_layout.addWidget(self.use_auto_detect)

        self.auto_detect_label = QLabel("(автоопределение отключено)")
        self.auto_detect_label.setStyleSheet("color: gray;")
        import_layout.addWidget(self.auto_detect_label)

        layout.addWidget(import_group)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton("📂 Загрузить PDF")
        self.btn_load.clicked.connect(self.load_pdf)
        self.btn_load.setMinimumHeight(35)

        self.btn_save_db = QPushButton("💾 Сохранить в БД")
        self.btn_save_db.setEnabled(False)
        self.btn_save_db.setMinimumHeight(35)

        self.btn_export_excel = QPushButton("📊 Экспорт в Excel")
        self.btn_export_excel.setEnabled(False)
        self.btn_export_excel.setMinimumHeight(35)

        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_save_db)
        btn_layout.addWidget(self.btn_export_excel)
        layout.addLayout(btn_layout)

        # Прогресс
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Фамилия", "Имя", "Отчество", "Класс", "Попытка",
            "Ответы", "Балл", "Разв.1", "Разв.2",
            "Первичный балл", "Оценка"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Статус
        self.status_label = QLabel("Готов к загрузке")
        self.status_label.setStyleSheet("color: gray; padding: 5px;")
        layout.addWidget(self.status_label)

        # Сигналы
        self.btn_save_db.clicked.connect(self.save_to_db_signal)
        self.btn_export_excel.clicked.connect(self.export_to_excel)

        self.use_auto_detect_flag = False

    def set_auto_detect(self):
        """Включить автоопределение предмета"""
        self.use_auto_detect_flag = True
        self.auto_detect_label.setText("(автоопределение ВКЛЮЧЕНО)")
        self.auto_detect_label.setStyleSheet("color: green;")
        self.subject_combo.setEnabled(False)
        QMessageBox.information(self, "Автоопределение",
                                "Автоопределение предмета включено.\n"
                                "Предмет будет определён автоматически из PDF.")

    def load_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите PDF файл", "", "PDF files (*.pdf)"
        )
        if not file_path:
            return

        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.btn_load.setEnabled(False)
        self.status_label.setText("⏳ Парсинг PDF файла...")
        self.status_label.setStyleSheet("color: orange; padding: 5px;")

        manual_subject = None if self.use_auto_detect_flag else self.subject_combo.currentText()

        self.thread = ParseThread(file_path, manual_subject=manual_subject)
        self.thread.progress.connect(self.progress.setValue)
        self.thread.finished.connect(self.on_parse_finished)
        self.thread.error.connect(self.on_parse_error)
        self.thread.start()

    def on_parse_finished(self, data):
        self.current_data = data
        self.progress.setVisible(False)
        self.btn_load.setEnabled(True)

        if self.use_auto_detect_flag:
            self.lbl_subject.setText(f"{data.subject} (автоопределено)")
            self.lbl_subject.setStyleSheet("color: green;")
        else:
            self.lbl_subject.setText(data.subject)
            self.lbl_subject.setStyleSheet("")

        self.lbl_exam_date.setText(data.exam_date or "Не определена")

        participants = data.participants

        if not participants:
            self.status_label.setText("❌ Не найдено участников в PDF")
            self.status_label.setStyleSheet("color: red; padding: 5px;")
            QMessageBox.warning(self, "Нет данных", "Не удалось найти данные участников.")
            return

        self.table.setRowCount(len(participants))

        grade_count = {2: 0, 3: 0, 4: 0, 5: 0}

        for row, student in enumerate(participants):
            self.table.setItem(row, 0, QTableWidgetItem(student.last_name))
            self.table.setItem(row, 1, QTableWidgetItem(student.first_name))
            self.table.setItem(row, 2, QTableWidgetItem(student.middle_name))
            self.table.setItem(row, 3, QTableWidgetItem(student.class_name))
            self.table.setItem(row, 4, QTableWidgetItem(str(student.attempt_number)))

            answers_item = QTableWidgetItem(
                student.answers[:50] + "..." if len(student.answers) > 50 else student.answers)
            self.table.setItem(row, 5, answers_item)

            self.table.setItem(row, 6, QTableWidgetItem(str(student.short_answer_score)))
            self.table.setItem(row, 7, QTableWidgetItem(str(student.extended_answer_1)))
            self.table.setItem(row, 8, QTableWidgetItem(str(student.extended_answer_2)))
            self.table.setItem(row, 9, QTableWidgetItem(str(student.primary_score)))

            grade_item = QTableWidgetItem(str(student.grade))
            if student.grade == 2:
                grade_item.setBackground(QColor(255, 200, 200))
                grade_item.setForeground(QColor(255, 0, 0))
                grade_count[2] += 1
            elif student.grade == 3:
                grade_item.setBackground(QColor(255, 255, 200))
                grade_count[3] += 1
            elif student.grade == 4:
                grade_item.setBackground(QColor(200, 255, 200))
                grade_count[4] += 1
            elif student.grade == 5:
                grade_item.setBackground(QColor(200, 200, 255))
                grade_count[5] += 1

            self.table.setItem(row, 10, grade_item)

        self.status_label.setText(
            f"✅ Загружено {len(participants)} участников | "
            f"5: {grade_count[5]}, 4: {grade_count[4]}, 3: {grade_count[3]}, 2: {grade_count[2]}"
        )
        self.status_label.setStyleSheet("color: green; padding: 5px;")

        self.btn_save_db.setEnabled(True)
        self.btn_export_excel.setEnabled(True)

        if self.main_window and hasattr(self.main_window, 'retake_tab'):
            self.main_window.retake_tab.update_students_list(participants)

        self.data_loaded.emit(data)

    def on_parse_error(self, error_msg):
        self.progress.setVisible(False)
        self.btn_load.setEnabled(True)
        self.status_label.setText("❌ Ошибка парсинга")
        self.status_label.setStyleSheet("color: red; padding: 5px;")
        QMessageBox.critical(self, "Ошибка", f"Не удалось распарсить PDF:\n{error_msg}")

    def save_to_db_signal(self):
        """Сигнал для сохранения в БД с проверкой дубликатов"""
        if self.current_data and self.current_data.participants:
            if self.main_window:
                # Проверяем, существует ли уже такой экзамен
                if self.current_data.file_hash:
                    existing_id = self.main_window.db.exam_exists(self.current_data.file_hash)
                    if existing_id:
                        reply = QMessageBox.question(
                            self, "Дубликат",
                            f"Экзамен '{self.current_data.subject}' от {self.current_data.exam_date}\n"
                            "уже существует в базе данных.\n\n"
                            "Хотите добавить его как новую попытку?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        )
                        if reply == QMessageBox.StandardButton.No:
                            return

                self.main_window.save_exam_data(self.current_data)
            else:
                QMessageBox.warning(self, "Ошибка", "Нет связи с главным окном")
        else:
            QMessageBox.warning(self, "Нет данных", "Нет данных для сохранения")

    def export_to_excel(self):
        if not self.current_data or not self.current_data.participants:
            QMessageBox.warning(self, "Нет данных", "Сначала загрузите PDF")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить Excel файл", "results.xlsx", "Excel files (*.xlsx)"
        )
        if file_path:
            try:
                import pandas as pd
                data = []
                for student in self.current_data.participants:
                    data.append({
                        'Фамилия': student.last_name,
                        'Имя': student.first_name,
                        'Отчество': student.middle_name,
                        'Класс': student.class_name,
                        'Предмет': student.subject,
                        'Ответы': student.answers,
                        'Первичный балл': student.primary_score,
                        'Оценка': student.grade
                    })
                df = pd.DataFrame(data)
                df.to_excel(file_path, index=False)
                QMessageBox.information(self, "Успех", f"Экспортировано в {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта: {e}")

    def get_current_data(self):
        return self.current_data