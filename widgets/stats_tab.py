from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit, QComboBox, QHBoxLayout, QLabel


class StatsTab(QWidget):
    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.current_subject = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Панель выбора
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Предмет:"))
        self.subject_filter = QComboBox()
        self.subject_filter.addItem("Все предметы")
        self.subject_filter.currentTextChanged.connect(self.on_subject_changed)
        filter_layout.addWidget(self.subject_filter)
        filter_layout.addStretch()

        self.btn_refresh = QPushButton("🔄 Обновить статистику")
        self.btn_refresh.clicked.connect(self.refresh_stats)
        filter_layout.addWidget(self.btn_refresh)

        layout.addLayout(filter_layout)

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet("font-family: 'Courier New'; font-size: 11px;")
        layout.addWidget(self.stats_text)

    def on_subject_changed(self, subject: str):
        if subject == "Все предметы":
            self.refresh_stats(subject=None)
        else:
            self.refresh_stats(subject=subject)

    def update_subjects_list(self):
        """Обновить список предметов"""
        if not self.main_window:
            return

        current = self.subject_filter.currentText()
        self.subject_filter.blockSignals(True)
        self.subject_filter.clear()
        self.subject_filter.addItem("Все предметы")

        try:
            subjects = self.main_window.db.get_subjects_list()
            for subject in subjects:
                if subject and subject not in ["Все предметы", None]:
                    self.subject_filter.addItem(subject)
        except Exception as e:
            print(f"Ошибка обновления списка предметов: {e}")

        # Восстанавливаем выбор
        idx = self.subject_filter.findText(current)
        if idx >= 0:
            self.subject_filter.setCurrentIndex(idx)

        self.subject_filter.blockSignals(False)

    def refresh_stats(self, subject=None):
        """Обновление статистики"""
        self.current_subject = subject

        if not self.main_window:
            self.stats_text.setText("Ошибка: нет связи с главным окном")
            return

        # Обновляем список предметов
        self.update_subjects_list()

        try:
            stats = self.main_window.db.get_stats_by_subject_and_class(subject=subject)
        except Exception as e:
            self.stats_text.setText(f"Ошибка получения статистики: {e}")
            return

        if stats['total']['total'] == 0:
            if subject:
                self.stats_text.setText(
                    f"📭 Нет данных по предмету '{subject}'.\n\nЗагрузите и сохраните результаты экзаменов.")
            else:
                self.stats_text.setText("📭 Нет данных.\n\nЗагрузите и сохраните результаты экзаменов.")
            return

        # Формируем отчёт
        text = ""

        # Общая статистика
        if subject:
            text += f"\n{'=' * 70}\n"
            text += f"  СТАТИСТИКА ПО ПРЕДМЕТУ: {subject.upper()}\n"
            text += f"{'=' * 70}\n"
        else:
            text += f"\n{'=' * 70}\n"
            text += f"  ОБЩАЯ СТАТИСТИКА ПО ВСЕМ ПРЕДМЕТАМ\n"
            text += f"{'=' * 70}\n"

        total_stats = stats['total']
        total_students = total_stats.get('total', 0)

        text += f"\n📊 ИТОГИ ЭКЗАМЕНОВ:\n"
        text += f"   Всего участников: {total_students}\n"
        text += f"   Оценка '5': {total_stats.get('5', 0)}\n"
        text += f"   Оценка '4': {total_stats.get('4', 0)}\n"
        text += f"   Оценка '3': {total_stats.get('3', 0)}\n"
        text += f"   Оценка '2': {total_stats.get('2', 0)}\n"

        if total_students > 0:
            success = total_stats.get('3', 0) + total_stats.get('4', 0) + total_stats.get('5', 0)
            quality = total_stats.get('4', 0) + total_stats.get('5', 0)
            text += f"\n   📈 Успеваемость: {success / total_students * 100:.1f}%"
            text += f"\n   ⭐ Качество знаний: {quality / total_students * 100:.1f}%"

        # Статистика по предметам (если выбран "Все предметы")
        if not subject and stats.get('by_subject'):
            text += f"\n\n{'─' * 70}\n"
            text += f"📚 СТАТИСТИКА ПО ПРЕДМЕТАМ:\n"
            text += f"{'─' * 70}\n"

            for subj, subj_stats in sorted(stats['by_subject'].items()):
                subj_total = subj_stats['total']
                text += f"\n   {subj}:\n"
                text += f"      5: {subj_stats.get('5', 0)}  |  4: {subj_stats.get('4', 0)}  |  3: {subj_stats.get('3', 0)}  |  2: {subj_stats.get('2', 0)}  |  Всего: {subj_total}\n"
                if subj_total > 0:
                    subj_success = subj_stats.get('3', 0) + subj_stats.get('4', 0) + subj_stats.get('5', 0)
                    subj_quality = subj_stats.get('4', 0) + subj_stats.get('5', 0)
                    text += f"      Успеваемость: {subj_success / subj_total * 100:.1f}%  |  Качество: {subj_quality / subj_total * 100:.1f}%"

        # Статистика по классам
        if stats.get('by_class'):
            text += f"\n\n{'─' * 70}\n"
            text += f"🏫 СТАТИСТИКА ПО КЛАССАМ:\n"
            text += f"{'─' * 70}\n"

            for class_name in sorted(stats['by_class'].keys()):
                class_stats = stats['by_class'][class_name]
                class_total = class_stats['total']
                text += f"\n   Класс {class_name}:\n"
                text += f"      5: {class_stats.get('5', 0)}  |  4: {class_stats.get('4', 0)}  |  3: {class_stats.get('3', 0)}  |  2: {class_stats.get('2', 0)}  |  Всего: {class_total}\n"
                if class_total > 0:
                    class_success = class_stats.get('3', 0) + class_stats.get('4', 0) + class_stats.get('5', 0)
                    class_quality = class_stats.get('4', 0) + class_stats.get('5', 0)
                    text += f"      Успеваемость: {class_success / class_total * 100:.1f}%  |  Качество: {class_quality / class_total * 100:.1f}%"

        self.stats_text.setText(text)