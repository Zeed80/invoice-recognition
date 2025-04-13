from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QComboBox,
    QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QImage, QPixmap
import cv2
import numpy as np
from pathlib import Path

from ..models.invoice_processor import InvoiceProcessor

class ProcessingThread(QThread):
    """Поток для обработки счета"""
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, processor, image_path, visualize):
        super().__init__()
        self.processor = processor
        self.image_path = image_path
        self.visualize = visualize
        
    def run(self):
        try:
            results = self.processor.process_invoice(
                self.image_path,
                visualize=self.visualize
            )
            structured_data = self.processor.extract_structured_data(results)
            self.finished.emit({
                'results': results,
                'structured_data': structured_data
            })
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система распознавания счетов")
        self.setMinimumSize(1200, 800)
        
        # Инициализация процессора
        self.processor = InvoiceProcessor()
        
        # Создание интерфейса
        self._create_ui()
        
    def _create_ui(self):
        """Создание пользовательского интерфейса"""
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        layout = QHBoxLayout(central_widget)
        
        # Левая панель с изображением
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Кнопки управления
        controls_layout = QHBoxLayout()
        self.load_button = QPushButton("Загрузить счет")
        self.load_button.clicked.connect(self._load_image)
        controls_layout.addWidget(self.load_button)
        
        self.ocr_engine_combo = QComboBox()
        self.ocr_engine_combo.addItems(["easyocr", "google"])
        controls_layout.addWidget(QLabel("OCR движок:"))
        controls_layout.addWidget(self.ocr_engine_combo)
        
        left_layout.addLayout(controls_layout)
        
        # Область отображения изображения
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(800, 600)
        self.image_label.setStyleSheet("border: 1px solid gray")
        left_layout.addWidget(self.image_label)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)
        
        layout.addWidget(left_panel)
        
        # Правая панель с результатами
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Результаты распознавания
        self.results_label = QLabel("Результаты распознавания:")
        right_layout.addWidget(self.results_label)
        
        self.results_text = QLabel()
        self.results_text.setWordWrap(True)
        self.results_text.setStyleSheet("border: 1px solid gray; padding: 10px;")
        right_layout.addWidget(self.results_text)
        
        layout.addWidget(right_panel)
        
    def _load_image(self):
        """Загрузка изображения счета"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение счета",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            # Отображение изображения
            image = cv2.imread(file_path)
            if image is not None:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                h, w, ch = image.shape
                bytes_per_line = ch * w
                qt_image = QImage(
                    image.data,
                    w,
                    h,
                    bytes_per_line,
                    QImage.Format_RGB888
                )
                pixmap = QPixmap.fromImage(qt_image)
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                
                # Запуск обработки
                self._process_invoice(file_path)
                
    def _process_invoice(self, image_path):
        """Обработка счета в отдельном потоке"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Бесконечный прогресс
        
        # Создание и запуск потока обработки
        self.thread = ProcessingThread(
            self.processor,
            image_path,
            visualize=True
        )
        self.thread.finished.connect(self._processing_finished)
        self.thread.error.connect(self._processing_error)
        self.thread.start()
        
    def _processing_finished(self, results):
        """Обработка завершена успешно"""
        self.progress_bar.setVisible(False)
        
        # Отображение результатов
        structured_data = results['structured_data']
        results_text = (
            f"Номер счета: {structured_data['invoice_number']}\n"
            f"Дата: {structured_data['date']}\n"
            f"Сумма: {structured_data['total_amount']}\n"
            f"Поставщик: {structured_data['supplier']['name']}\n"
            f"ИНН: {structured_data['supplier']['inn']}\n"
            f"Адрес: {structured_data['supplier']['address']}\n"
            f"Платежная информация: {structured_data['payment_info']}"
        )
        self.results_text.setText(results_text)
        
        # Отображение обработанного изображения
        if 'visualization_path' in results['results']:
            vis_path = results['results']['visualization_path']
            image = cv2.imread(vis_path)
            if image is not None:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                h, w, ch = image.shape
                bytes_per_line = ch * w
                qt_image = QImage(
                    image.data,
                    w,
                    h,
                    bytes_per_line,
                    QImage.Format_RGB888
                )
                pixmap = QPixmap.fromImage(qt_image)
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                
    def _processing_error(self, error_message):
        """Обработка ошибки"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(
            self,
            "Ошибка",
            f"Ошибка при обработке счета: {error_message}"
        ) 