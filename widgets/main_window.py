from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QMessageBox,
    QComboBox, QHBoxLayout, QVBoxLayout, QWidget, QLabel,
    QProgressDialog, QPushButton, QFileDialog
)
from PyQt6.QtCore import Qt
from database import Database
from models import Exam, ParsedExamData, ExamAttempt, Subject
from widgets.load_tab import LoadTab
from widgets.retake_tab import RetakeTab
from widgets.stats_tab import StatsTab
from widgets.exam_manager import ExamManagerWidget
from report_generator import ReportGenerator


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система учёта результатов экзаменов ОГЭ/ЕГЭ")
        self.setGeometry(100, 100, 1400, 700)

        # Инициализация БД
        self.db = Database()

        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Верхняя панель с кнопками экспорта
        top_layout = QHBoxLayout()

        self.btn_export_student_report = QPushButton("📄 Отчёт по ученикам")
        self.btn_export_student_report.clicked.connect(self.export_student_report)
        self.btn_export_student_report.setEnabled(False)

        self.btn_export_detailed_report = QPushButton("📋 Детальный отчёт по классам")
        self.btn_export_detailed_report.clicked.connect(self.export_detailed_report)
        self.btn_export_detailed_report.setEnabled(False)

        self.btn_export_stats_report = QPushButton("📊 Статистика")
        self.btn_export_stats_report.clicked.connect(self.export_stats_report)
        self.btn_export_stats_report.setEnabled(False)

        top_layout.addWidget(self.btn_export_student_report)
        top_layout.addWidget(self.btn_export_detailed_report)
        top_layout.addWidget(self.btn_export_stats_report)
        top_layout.addStretch()

        main_layout.addLayout(top_layout)

        # Фильтр по предмету
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Фильтр по предмету:"))
        self.subject_filter = QComboBox()
        self.subject_filter.addItem("Все предметы")
        self.subject_filter.currentTextChanged.connect(self.on_subject_filter_changed)
        filter_layout.addWidget(self.subject_filter)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Создание вкладок (сначала создаём tabs)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Создаём вкладки
        self.load_tab = LoadTab(main_window=self)
        self.retake_tab = RetakeTab(main_window=self)
        self.stats_tab = StatsTab(main_window=self)
        self.exam_manager_tab = ExamManagerWidget(main_window=self)

        # Добавляем вкладки
        self.tabs.addTab(self.load_tab, "📁 Загрузка и просмотр")
        self.tabs.addTab(self.retake_tab, "🔄 Пересдачи")
        self.tabs.addTab(self.stats_tab, "📊 Статистика")
        self.tabs.addTab(self.exam_manager_tab, "🗃️ Управление экзаменами")

        # Статус бар
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Готов к работе")

        # Обновляем кнопки после загрузки данных
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        """При переключении вкладки обновляем доступность кнопок"""
        if index == 2:  # Вкладка статистики
            has_data = self.db.get_subjects_list() != []
            self.btn_export_stats_report.setEnabled(has_data)
            self.btn_export_student_report.setEnabled(has_data)
            self.btn_export_detailed_report.setEnabled(has_data)
        else:
            self.btn_export_stats_report.setEnabled(False)
            self.btn_export_student_report.setEnabled(False)
            self.btn_export_detailed_report.setEnabled(False)

    def on_subject_filter_changed(self, subject: str):
        if subject == "Все предметы":
            self.stats_tab.refresh_stats(subject=None)
        else:
            self.stats_tab.refresh_stats(subject=subject)

    def export_student_report(self):
        """Экспорт отчёта по ученикам в PDF"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчёт", "student_report.pdf", "PDF files (*.pdf)"
        )
        if not file_path:
            return

        try:
            data = self.db.get_student_report()

            if not data:
                QMessageBox.warning(self, "Нет данных", "Нет данных для экспорта")
                return

            ReportGenerator.generate_student_report(data, file_path)

            QMessageBox.information(self, "Успех", f"Отчёт сохранён в:\n{file_path}")
            self.statusbar.showMessage(f"Отчёт экспортирован: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта:\n{str(e)}")

    def export_detailed_report(self):
        """Экспорт детального отчёта по классам в PDF"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить детальный отчёт", "detailed_class_report.pdf", "PDF files (*.pdf)"
        )
        if not file_path:
            return

        try:
            data = self.db.get_student_report()

            if not data:
                QMessageBox.warning(self, "Нет данных", "Нет данных для экспорта")
                return

            ReportGenerator.generate_detailed_class_report(data, file_path)

            QMessageBox.information(self, "Успех", f"Детальный отчёт сохранён в:\n{file_path}")
            self.statusbar.showMessage(f"Детальный отчёт экспортирован: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта:\n{str(e)}")

    def export_stats_report(self):
        """Экспорт статистики в PDF"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить статистику", "statistics_report.pdf", "PDF files (*.pdf)"
        )
        if not file_path:
            return

        try:
            current_filter = self.subject_filter.currentText()
            if current_filter == "Все предметы":
                stats = self.db.get_stats_by_subject_and_class(subject=None)
                subject_filter = None
            else:
                stats = self.db.get_stats_by_subject_and_class(subject=current_filter)
                subject_filter = current_filter

            if stats['total']['total'] == 0:
                QMessageBox.warning(self, "Нет данных", "Нет данных для экспорта")
                return

            ReportGenerator.generate_statistics_report(stats, file_path, subject_filter)

            QMessageBox.information(self, "Успех", f"Статистика сохранена в:\n{file_path}")
            self.statusbar.showMessage(f"Статистика экспортирована: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта:\n{str(e)}")

    def save_exam_data(self, exam_data: ParsedExamData):
        """Сохранение данных экзамена с прогрессом"""
        try:
            progress = QProgressDialog("Сохранение данных экзамена...", "Отмена", 0, 100, self)
            progress.setWindowTitle("Сохранение")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setAutoClose(True)
            progress.setMinimumDuration(0)
            progress.show()

            progress.setLabelText("Сохранение информации об экзамене...")
            progress.setValue(10)

            exam = Exam(
                subject=exam_data.subject,
                exam_date=exam_data.exam_date,
                exam_code=exam_data.subject_code,
                region=exam_data.region,
                file_hash=exam_data.file_hash
            )
            exam_id = self.db.save_exam(exam)

            for participant in exam_data.participants:
                participant.exam_id = exam_id
                participant.exam_date = exam_data.exam_date

            progress.setLabelText(f"Сохранение {len(exam_data.participants)} участников...")

            def update_progress(current, total):
                percent = 10 + int((current / total) * 80)
                progress.setValue(percent)
                progress.setLabelText(f"Сохранено {current} из {total} участников...")

            saved, duplicates = self.db.save_attempts_batch(exam_data.participants, update_progress)

            progress.setValue(100)

            if duplicates > 0:
                QMessageBox.information(self, "Успех (с предупреждением)",
                                        f"✅ Сохранено {saved} новых записей\n"
                                        f"⚠️ Пропущено дубликатов: {duplicates}\n"
                                        f"Предмет: {exam_data.subject}\n"
                                        f"Дата: {exam_data.exam_date or 'не указана'}")
            else:
                QMessageBox.information(self, "Успех",
                                        f"✅ Сохранено {saved} записей\n"
                                        f"Предмет: {exam_data.subject}\n"
                                        f"Дата: {exam_data.exam_date or 'не указана'}")

            self.stats_tab.refresh_stats()
            self.retake_tab.update_students_list(exam_data.participants)
            self.update_subjects_filter()

            # Обновляем список в управлении экзаменами
            self.exam_manager_tab.refresh_list()

            self.statusbar.showMessage(f"Сохранено {saved} участников ({exam_data.subject})")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"❌ Не удалось сохранить в БД:\n{e}")
            self.statusbar.showMessage("Ошибка сохранения")

    def update_subjects_filter(self):
        """Обновление фильтра предметов"""
        subjects = self.db.get_subjects_list()
        current = self.subject_filter.currentText()

        self.subject_filter.blockSignals(True)
        self.subject_filter.clear()
        self.subject_filter.addItem("Все предметы")
        self.subject_filter.addItems(subjects)

        idx = self.subject_filter.findText(current)
        if idx >= 0:
            self.subject_filter.setCurrentIndex(idx)
        else:
            self.subject_filter.setCurrentIndex(0)

        self.subject_filter.blockSignals(False)

    def save_retakes(self, retakes: list):
        """Сохранение пересдач"""
        try:
            progress = QProgressDialog("Сохранение пересдач...", "Отмена", 0, 100, self)
            progress.setWindowTitle("Сохранение")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setAutoClose(True)
            progress.show()

            subject = retakes[0].subject if retakes else "Неизвестный предмет"
            exam = Exam(subject=f"{subject} (пересдача)", exam_date=None)
            exam_id = self.db.save_exam(exam)

            progress.setValue(50)

            for retake in retakes:
                retake.exam_id = exam_id
                self.db.save_attempt(retake)

            progress.setValue(100)

            self.statusbar.showMessage(f"Сохранено {len(retakes)} пересдач")
            self.stats_tab.refresh_stats()
            self.update_subjects_filter()
            self.exam_manager_tab.refresh_list()

            QMessageBox.information(self, "Успех", f"✅ Сохранено {len(retakes)} пересдач")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"❌ Не удалось сохранить пересдачи:\n{e}")

    def closeEvent(self, event):
        self.db.close()
        event.accept()