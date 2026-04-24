from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
import os
from datetime import datetime


class ReportGenerator:
    @staticmethod
    def register_fonts():
        """Регистрация шрифтов для поддержки кириллицы"""
        try:
            font_paths = [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/times.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/System/Library/Fonts/Arial.ttf"
            ]

            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('CustomFont', font_path))
                    addMapping('CustomFont', 0, 0, 'CustomFont')
                    addMapping('CustomFont', 1, 0, 'CustomFont')
                    return 'CustomFont'
        except:
            pass
        return 'Helvetica'

    @staticmethod
    def generate_student_report(data, output_path, title="Отчёт по результатам экзаменов"):
        """Генерация PDF отчёта по ученикам"""

        font_name = ReportGenerator.register_fonts()

        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=15 * mm, leftMargin=15 * mm,
                                topMargin=20 * mm, bottomMargin=15 * mm)

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=16,
            alignment=1,
            spaceAfter=20
        )

        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=12,
            spaceAfter=10
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10
        )

        story = []

        story.append(Paragraph(title, title_style))
        story.append(Paragraph(f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}", normal_style))
        story.append(Spacer(1, 10 * mm))

        # Группировка по классам
        classes = {}
        for row in data:
            class_name = row['class']
            if class_name not in classes:
                classes[class_name] = []
            classes[class_name].append(row)

        for class_name in sorted(classes.keys()):
            story.append(Paragraph(f"Класс: {class_name}", header_style))

            # Таблица с результатами
            table_data = [
                ['№', 'Фамилия', 'Имя', 'Отчество', 'Экзамен (дата)', 'Балл', 'Оценка']
            ]

            for i, row in enumerate(classes[class_name], 1):
                exam_info = f"{row['subject']}\n({row['exam_date'] if row['exam_date'] else 'дата не указана'})"
                table_data.append([
                    str(i),
                    row['last_name'],
                    row['first_name'],
                    row['middle_name'],
                    exam_info,
                    str(row['primary_score']),
                    str(row['grade'])
                ])

            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
            ]))

            story.append(table)
            story.append(Spacer(1, 10 * mm))

            # Статистика по классу
            grades = {'5': 0, '4': 0, '3': 0, '2': 0}
            for row in classes[class_name]:
                grades[str(row['grade'])] += 1

            total = len(classes[class_name])
            success = grades['3'] + grades['4'] + grades['5']
            quality = grades['4'] + grades['5']

            stats_text = (f"Всего: {total} | "
                          f"«5»: {grades['5']} | «4»: {grades['4']} | "
                          f"«3»: {grades['3']} | «2»: {grades['2']} | "
                          f"Успеваемость: {success / total * 100:.1f}% | "
                          f"Качество: {quality / total * 100:.1f}%")

            story.append(Paragraph(stats_text, normal_style))
            story.append(Spacer(1, 15 * mm))

        doc.build(story)
        return True

    @staticmethod
    def generate_detailed_class_report(data, output_path, title="Детальный отчёт по классам"):
        """Генерация детального PDF отчёта по классам с полной информацией об учащихся"""

        font_name = ReportGenerator.register_fonts()

        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=15 * mm, leftMargin=15 * mm,
                                topMargin=20 * mm, bottomMargin=15 * mm)

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=16,
            alignment=1,
            spaceAfter=20
        )

        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=12,
            spaceAfter=10
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10
        )

        story = []

        # Заголовок
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}", normal_style))
        story.append(Spacer(1, 10 * mm))

        # Группировка по классам
        classes = {}
        for row in data:
            class_name = row['class']
            if class_name not in classes:
                classes[class_name] = []
            classes[class_name].append(row)

        # Сводная таблица по классам
        story.append(Paragraph("Сводная информация по классам:", header_style))

        summary_data = [['Класс', 'Всего уч.', '«5»', '«4»', '«3»', '«2»', 'Успеваемость', 'Качество']]

        for class_name in sorted(classes.keys()):
            grades = {'5': 0, '4': 0, '3': 0, '2': 0}
            for row in classes[class_name]:
                grades[str(row['grade'])] += 1

            total = len(classes[class_name])
            success = grades['3'] + grades['4'] + grades['5']
            quality = grades['4'] + grades['5']

            summary_data.append([
                class_name,
                str(total),
                str(grades['5']),
                str(grades['4']),
                str(grades['3']),
                str(grades['2']),
                f"{success / total * 100:.1f}%" if total > 0 else "0%",
                f"{quality / total * 100:.1f}%" if total > 0 else "0%"
            ])

        summary_table = Table(summary_data, repeatRows=1)
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
        ]))

        story.append(summary_table)
        story.append(Spacer(1, 20 * mm))

        # Детальная информация по каждому классу
        for class_name in sorted(classes.keys()):
            story.append(PageBreak())
            story.append(Paragraph(f"Класс: {class_name}", header_style))

            # Собираем всех учеников класса с их экзаменами
            students = {}
            for row in classes[class_name]:
                student_key = f"{row['last_name']} {row['first_name']} {row['middle_name']}"
                if student_key not in students:
                    students[student_key] = {
                        'last_name': row['last_name'],
                        'first_name': row['first_name'],
                        'middle_name': row['middle_name'],
                        'exams': []
                    }
                students[student_key]['exams'].append({
                    'subject': row['subject'],
                    'exam_date': row['exam_date'],
                    'score': row['primary_score'],
                    'grade': row['grade']
                })

            # Таблица с детальной информацией по ученикам
            table_data = [
                ['№', 'ФИО ученика', 'Экзамен', 'Дата сдачи', 'Балл', 'Оценка']
            ]

            row_num = 1
            for student_key in sorted(students.keys()):
                student = students[student_key]
                full_name = f"{student['last_name']} {student['first_name']} {student['middle_name']}"

                # Для каждого экзамена ученика - отдельная строка
                for i, exam in enumerate(student['exams']):
                    if i == 0:
                        table_data.append([
                            str(row_num),
                            full_name,
                            exam['subject'],
                            exam['exam_date'] if exam['exam_date'] else 'дата не указана',
                            str(exam['score']),
                            str(exam['grade'])
                        ])
                    else:
                        table_data.append([
                            '',
                            '',
                            exam['subject'],
                            exam['exam_date'] if exam['exam_date'] else 'дата не указана',
                            str(exam['score']),
                            str(exam['grade'])
                        ])
                row_num += 1

            # Создаём таблицу
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('ALIGN', (3, 1), (5, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
            ]))

            story.append(table)
            story.append(Spacer(1, 10 * mm))

            # Статистика по классу
            grades = {'5': 0, '4': 0, '3': 0, '2': 0}
            for row in classes[class_name]:
                grades[str(row['grade'])] += 1

            total = len(classes[class_name])
            success = grades['3'] + grades['4'] + grades['5']
            quality = grades['4'] + grades['5']
            unique_students = len(students)

            stats_text = (f"📊 Статистика класса {class_name}:\n"
                          f"   • Всего учеников: {unique_students}\n"
                          f"   • Всего сдач: {total}\n"
                          f"   • Оценки: «5» - {grades['5']}, «4» - {grades['4']}, «3» - {grades['3']}, «2» - {grades['2']}\n"
                          f"   • Успеваемость: {success / total * 100:.1f}% ({success} из {total})\n"
                          f"   • Качество знаний: {quality / total * 100:.1f}% ({quality} из {total})")

            story.append(Paragraph(stats_text, normal_style))

        doc.build(story)
        return True

    @staticmethod
    def generate_statistics_report(stats, output_path, subject_filter=None):
        """Генерация PDF отчёта со статистикой"""

        font_name = ReportGenerator.register_fonts()

        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=15 * mm, leftMargin=15 * mm,
                                topMargin=20 * mm, bottomMargin=15 * mm)

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=16,
            alignment=1,
            spaceAfter=20
        )

        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=12,
            spaceAfter=10
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10
        )

        story = []

        # Заголовок
        if subject_filter:
            title = f"Статистика по предмету: {subject_filter}"
        else:
            title = "Общая статистика по всем предметам"

        story.append(Paragraph(title, title_style))
        story.append(Paragraph(f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}", normal_style))
        story.append(Spacer(1, 10 * mm))

        # Общая статистика
        total_stats = stats['total']
        total_students = total_stats['total']

        story.append(Paragraph("Общие итоги:", header_style))

        stats_data = [
            ['Показатель', 'Значение'],
            ['Всего участников', str(total_students)],
            ['Оценка «5»', str(total_stats.get('5', 0))],
            ['Оценка «4»', str(total_stats.get('4', 0))],
            ['Оценка «3»', str(total_stats.get('3', 0))],
            ['Оценка «2»', str(total_stats.get('2', 0))]
        ]

        if total_students > 0:
            success = total_stats.get('3', 0) + total_stats.get('4', 0) + total_stats.get('5', 0)
            quality = total_stats.get('4', 0) + total_stats.get('5', 0)
            stats_data.append(['Успеваемость', f"{success / total_students * 100:.1f}%"])
            stats_data.append(['Качество знаний', f"{quality / total_students * 100:.1f}%"])

        stats_table = Table(stats_data)
        stats_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
        ]))

        story.append(stats_table)
        story.append(Spacer(1, 15 * mm))

        # Статистика по предметам
        if not subject_filter and stats.get('by_subject'):
            story.append(Paragraph("Статистика по предметам:", header_style))

            subject_data = [['Предмет', 'Всего', '«5»', '«4»', '«3»', '«2»', 'Успеваемость', 'Качество']]

            for subj, subj_stats in sorted(stats['by_subject'].items()):
                subj_total = subj_stats['total']
                success = subj_stats.get('3', 0) + subj_stats.get('4', 0) + subj_stats.get('5', 0)
                quality = subj_stats.get('4', 0) + subj_stats.get('5', 0)

                subject_data.append([
                    subj,
                    str(subj_total),
                    str(subj_stats.get('5', 0)),
                    str(subj_stats.get('4', 0)),
                    str(subj_stats.get('3', 0)),
                    str(subj_stats.get('2', 0)),
                    f"{success / subj_total * 100:.1f}%" if subj_total > 0 else "0%",
                    f"{quality / subj_total * 100:.1f}%" if subj_total > 0 else "0%"
                ])

            subject_table = Table(subject_data, repeatRows=1)
            subject_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
            ]))

            story.append(subject_table)
            story.append(Spacer(1, 15 * mm))

        # Статистика по классам
        if stats.get('by_class'):
            story.append(Paragraph("Статистика по классам:", header_style))

            class_data = [['Класс', 'Всего', '«5»', '«4»', '«3»', '«2»', 'Успеваемость', 'Качество']]

            for class_name in sorted(stats['by_class'].keys()):
                class_stats = stats['by_class'][class_name]
                total = class_stats['total']
                success = class_stats.get('3', 0) + class_stats.get('4', 0) + class_stats.get('5', 0)
                quality = class_stats.get('4', 0) + class_stats.get('5', 0)

                class_data.append([
                    class_name,
                    str(total),
                    str(class_stats.get('5', 0)),
                    str(class_stats.get('4', 0)),
                    str(class_stats.get('3', 0)),
                    str(class_stats.get('2', 0)),
                    f"{success / total * 100:.1f}%" if total > 0 else "0%",
                    f"{quality / total * 100:.1f}%" if total > 0 else "0%"
                ])

            class_table = Table(class_data, repeatRows=1)
            class_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
            ]))

            story.append(class_table)

        doc.build(story)
        return True