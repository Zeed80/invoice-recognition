#!/usr/bin/env python
import sys
import logging
from PySide6.QtWidgets import QApplication
from .main_window import MainWindow

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/gui.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def main():
    """Точка входа в приложение"""
    try:
        # Настраиваем логирование
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Запуск приложения")
        
        # Создаем приложение
        app = QApplication(sys.argv)
        app.setApplicationName("Invoice Recognition")
        app.setOrganizationName("InvoiceRecognition")
        
        # Устанавливаем стиль
        app.setStyle("Fusion")
        
        # Создаем и показываем главное окно
        window = MainWindow()
        window.show()
        
        # Запускаем цикл обработки событий
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 