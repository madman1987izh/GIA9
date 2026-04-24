import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox


def exception_hook(exctype, value, tb):
    """Глобальный обработчик исключений (упрощённый)"""
    error_msg = ''.join(traceback.format_exception(exctype, value, tb, limit=5))
    print(f"Ошибка:\n{error_msg}")
    QMessageBox.critical(None, "Ошибка", f"Произошла ошибка:\n{str(value)}")
    # Не вызываем sys.exit, чтобы не создавать рекурсию


def main():
    # Устанавливаем глобальный обработчик ошибок
    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    try:
        from widgets.main_window import MainWindow
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Ошибка при запуске: {e}")
        traceback.print_exc()
        QMessageBox.critical(None, "Ошибка запуска", f"Не удалось запустить приложение:\n{str(e)}")


if __name__ == "__main__":
    main()