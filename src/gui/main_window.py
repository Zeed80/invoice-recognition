import sys
import os
from pathlib import Path
from datetime import datetime
import json
import logging
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QProgressBar, QTabWidget,
    QTableWidget, QTableWidgetItem, QComboBox, QSpinBox,
    QCheckBox, QMessageBox, QSplitter, QMenu, QStatusBar,
    QDockWidget, QTextEdit, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSettings
from PySide6.QtGui import QAction, QIcon, QPixmap, QImage, QPainter

from ..models.invoice_processor import InvoiceProcessor
from ..utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class ProcessingThread(QThread):
    """Поток для обработки счетов"""
    progress = Signal(int)
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, processor: InvoiceProcessor, files: List[str]):
        super().__init__()
        self.processor = processor
        self.files = files
        
    def run(self):
        try:
            results = {}
            for i, file in enumerate(self.files):
                result = self.processor.process_file(file)
                results[file] = result
                self.progress.emit((i + 1) * 100 // len(self.files))
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.processor = InvoiceProcessor()
        self.current_results = {}
        self.processing_thread = None
        
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Система распознавания счетов")
        self.setMinimumSize(1200, 800)
        
        # Главный виджет
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Верхняя панель инструментов
        toolbar = self.addToolBar("Основные действия")
        self.create_toolbar(toolbar)
        
        # Сплиттер для разделения областей
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Левая панель: дерево файлов и настройки
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.create_left_panel(left_layout)
        splitter.addWidget(left_panel)
        
        # Центральная панель: просмотр и редактирование
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        self.create_center_panel(center_layout)
        splitter.addWidget(center_panel)
        
        # Правая панель: результаты и метрики
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.create_right_panel(right_layout)
        splitter.addWidget(right_panel)
        
        # Устанавливаем размеры сплиттера
        splitter.setSizes([300, 600, 300])
        
        # Статусбар
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Док для логов
        self.create_log_dock()
        
        # Меню
        self.create_menu()
        
    def create_toolbar(self, toolbar):
        """Создание панели инструментов"""
        # Открыть файлы
        open_action = QAction(QIcon.fromTheme("document-open"), "Открыть", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_files)
        toolbar.addAction(open_action)
        
        # Открыть директорию
        open_dir_action = QAction(QIcon.fromTheme("folder"), "Открыть директорию", self)
        open_dir_action.triggered.connect(self.open_directory)
        toolbar.addAction(open_dir_action)
        
        toolbar.addSeparator()
        
        # Запуск обработки
        process_action = QAction(QIcon.fromTheme("media-playback-start"), "Обработать", self)
        process_action.setShortcut("F5")
        process_action.triggered.connect(self.start_processing)
        toolbar.addAction(process_action)
        
        # Остановка обработки
        stop_action = QAction(QIcon.fromTheme("media-playback-stop"), "Остановить", self)
        stop_action.triggered.connect(self.stop_processing)
        toolbar.addAction(stop_action)
        
        toolbar.addSeparator()
        
        # Экспорт результатов
        export_action = QAction(QIcon.fromTheme("document-save"), "Экспорт", self)
        export_action.setShortcut("Ctrl+S")
        export_action.triggered.connect(self.export_results)
        toolbar.addAction(export_action)
        
    def create_left_panel(self, layout):
        """Создание левой панели"""
        # Дерево файлов
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabel("Файлы")
        self.file_tree.itemSelectionChanged.connect(self.file_selected)
        layout.addWidget(self.file_tree)
        
        # Настройки обработки
        settings_group = QWidget()
        settings_layout = QVBoxLayout(settings_group)
        
        # Выбор модели
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Модель:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["YOLOv5s", "YOLOv5m", "YOLOv5l"])
        model_layout.addWidget(self.model_combo)
        settings_layout.addLayout(model_layout)
        
        # Выбор OCR
        ocr_layout = QHBoxLayout()
        ocr_layout.addWidget(QLabel("OCR:"))
        self.ocr_combo = QComboBox()
        self.ocr_combo.addItems(["EasyOCR", "Google Cloud Vision"])
        ocr_layout.addWidget(self.ocr_combo)
        settings_layout.addLayout(ocr_layout)
        
        # Порог уверенности
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(QLabel("Порог:"))
        self.conf_spin = QSpinBox()
        self.conf_spin.setRange(1, 100)
        self.conf_spin.setValue(80)
        self.conf_spin.setSuffix("%")
        conf_layout.addWidget(self.conf_spin)
        settings_layout.addLayout(conf_layout)
        
        # Использование GPU
        self.gpu_check = QCheckBox("Использовать GPU")
        self.gpu_check.setChecked(torch.cuda.is_available())
        settings_layout.addWidget(self.gpu_check)
        
        layout.addWidget(settings_group)
        
    def create_center_panel(self, layout):
        """Создание центральной панели"""
        # Вкладки для разных режимов просмотра
        self.view_tabs = QTabWidget()
        
        # Вкладка просмотра изображения
        self.image_view = QLabel()
        self.image_view.setAlignment(Qt.AlignCenter)
        self.view_tabs.addTab(self.image_view, "Изображение")
        
        # Вкладка с таблицей результатов
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["Поле", "Значение", "Уверенность"])
        self.view_tabs.addTab(self.result_table, "Данные")
        
        layout.addWidget(self.view_tabs)
        
        # Панель инструментов редактирования
        edit_toolbar = QWidget()
        edit_layout = QHBoxLayout(edit_toolbar)
        
        # Кнопки редактирования
        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(self.edit_field)
        edit_layout.addWidget(edit_btn)
        
        verify_btn = QPushButton("Подтвердить")
        verify_btn.clicked.connect(self.verify_field)
        edit_layout.addWidget(verify_btn)
        
        reset_btn = QPushButton("Сбросить")
        reset_btn.clicked.connect(self.reset_field)
        edit_layout.addWidget(reset_btn)
        
        layout.addWidget(edit_toolbar)
        
    def create_right_panel(self, layout):
        """Создание правой панели"""
        # Вкладки для разных типов информации
        info_tabs = QTabWidget()
        
        # Вкладка с метриками
        metrics_widget = QWidget()
        metrics_layout = QVBoxLayout(metrics_widget)
        
        # Общая точность
        self.accuracy_label = QLabel("Точность: -")
        metrics_layout.addWidget(self.accuracy_label)
        
        # Прогресс обработки
        self.progress_bar = QProgressBar()
        metrics_layout.addWidget(self.progress_bar)
        
        # Статистика по полям
        self.field_stats = QTableWidget()
        self.field_stats.setColumnCount(3)
        self.field_stats.setHorizontalHeaderLabels(["Поле", "Точность", "Время"])
        metrics_layout.addWidget(self.field_stats)
        
        info_tabs.addTab(metrics_widget, "Метрики")
        
        # Вкладка с историей
        self.history_list = QTreeWidget()
        self.history_list.setHeaderLabels(["Время", "Действие", "Результат"])
        info_tabs.addTab(self.history_list, "История")
        
        layout.addWidget(info_tabs)
        
    def create_log_dock(self):
        """Создание дока для логов"""
        dock = QDockWidget("Логи", self)
        dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        dock.setWidget(self.log_text)
        
        self.addDockWidget(Qt.BottomDockWidgetArea, dock)
        
    def create_menu(self):
        """Создание главного меню"""
        menubar = self.menuBar()
        
        # Меню Файл
        file_menu = menubar.addMenu("Файл")
        
        open_action = QAction("Открыть файлы...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_files)
        file_menu.addAction(open_action)
        
        open_dir_action = QAction("Открыть директорию...", self)
        open_dir_action.triggered.connect(self.open_directory)
        file_menu.addAction(open_dir_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Экспорт результатов...", self)
        export_action.setShortcut("Ctrl+S")
        export_action.triggered.connect(self.export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Вид
        view_menu = menubar.addMenu("Вид")
        
        theme_menu = view_menu.addMenu("Тема")
        light_action = QAction("Светлая", self)
        light_action.triggered.connect(lambda: self.set_theme("light"))
        theme_menu.addAction(light_action)
        
        dark_action = QAction("Темная", self)
        dark_action.triggered.connect(lambda: self.set_theme("dark"))
        theme_menu.addAction(dark_action)
        
        view_menu.addSeparator()
        
        log_action = QAction("Показать логи", self)
        log_action.setCheckable(True)
        log_action.setChecked(True)
        log_action.triggered.connect(self.toggle_logs)
        view_menu.addAction(log_action)
        
        # Меню Инструменты
        tools_menu = menubar.addMenu("Инструменты")
        
        settings_action = QAction("Настройки...", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        tools_menu.addSeparator()
        
        cleanup_action = QAction("Очистка...", self)
        cleanup_action.triggered.connect(self.run_cleanup)
        tools_menu.addAction(cleanup_action)
        
        check_action = QAction("Проверка системы", self)
        check_action.triggered.connect(self.check_system)
        tools_menu.addAction(check_action)
        
        # Меню Справка
        help_menu = menubar.addMenu("Справка")
        
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def open_files(self):
        """Открытие файлов для обработки"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите файлы",
            "",
            "Изображения (*.jpg *.jpeg *.png);;PDF (*.pdf);;Все файлы (*.*)"
        )
        if files:
            self.add_files(files)
            
    def open_directory(self):
        """Открытие директории для обработки"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Выберите директорию",
            ""
        )
        if directory:
            files = []
            for ext in [".jpg", ".jpeg", ".png", ".pdf"]:
                files.extend(Path(directory).glob(f"**/*{ext}"))
            self.add_files([str(f) for f in files])
            
    def add_files(self, files: List[str]):
        """Добавление файлов в дерево"""
        for file in files:
            item = QTreeWidgetItem(self.file_tree)
            item.setText(0, os.path.basename(file))
            item.setData(0, Qt.UserRole, file)
            
    def file_selected(self):
        """Обработка выбора файла"""
        items = self.file_tree.selectedItems()
        if items:
            file_path = items[0].data(0, Qt.UserRole)
            self.show_file(file_path)
            
    def show_file(self, file_path: str):
        """Отображение файла"""
        # Показываем изображение
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                self.image_view.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_view.setPixmap(scaled)
            
        # Показываем результаты, если есть
        if file_path in self.current_results:
            self.show_results(self.current_results[file_path])
            
    def show_results(self, results: Dict):
        """Отображение результатов распознавания"""
        self.result_table.setRowCount(0)
        for field, data in results.items():
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            self.result_table.setItem(row, 0, QTableWidgetItem(field))
            self.result_table.setItem(row, 1, QTableWidgetItem(str(data["value"])))
            self.result_table.setItem(row, 2, QTableWidgetItem(f"{data['confidence']:.2%}"))
            
    def start_processing(self):
        """Запуск обработки файлов"""
        if self.processing_thread and self.processing_thread.isRunning():
            return
            
        files = []
        for i in range(self.file_tree.topLevelItemCount()):
            item = self.file_tree.topLevelItem(i)
            files.append(item.data(0, Qt.UserRole))
            
        if not files:
            QMessageBox.warning(self, "Ошибка", "Нет файлов для обработки")
            return
            
        # Обновляем настройки процессора
        self.processor.config.update({
            "model": {
                "name": self.model_combo.currentText(),
                "confidence_threshold": self.conf_spin.value() / 100,
                "device": "cuda" if self.gpu_check.isChecked() else "cpu"
            },
            "ocr": {
                "engine": self.ocr_combo.currentText()
            }
        })
        
        # Запускаем обработку
        self.processing_thread = ProcessingThread(self.processor, files)
        self.processing_thread.progress.connect(self.progress_bar.setValue)
        self.processing_thread.finished.connect(self.processing_finished)
        self.processing_thread.error.connect(self.processing_error)
        self.processing_thread.start()
        
        self.statusBar.showMessage("Обработка...")
        
    def stop_processing(self):
        """Остановка обработки"""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.terminate()
            self.statusBar.showMessage("Обработка остановлена")
            
    def processing_finished(self, results: Dict):
        """Обработка завершена"""
        self.current_results.update(results)
        self.statusBar.showMessage("Обработка завершена")
        
        # Обновляем статистику
        self.update_statistics(results)
        
        # Показываем результаты текущего файла
        items = self.file_tree.selectedItems()
        if items:
            self.show_results(results[items[0].data(0, Qt.UserRole)])
            
    def processing_error(self, error: str):
        """Ошибка обработки"""
        QMessageBox.critical(self, "Ошибка", f"Ошибка при обработке: {error}")
        self.statusBar.showMessage("Ошибка обработки")
        
    def update_statistics(self, results: Dict):
        """Обновление статистики"""
        total_confidence = 0
        field_stats = {}
        
        for file_results in results.values():
            for field, data in file_results.items():
                if field not in field_stats:
                    field_stats[field] = {"total": 0, "count": 0}
                field_stats[field]["total"] += data["confidence"]
                field_stats[field]["count"] += 1
                total_confidence += data["confidence"]
                
        # Обновляем общую точность
        avg_confidence = total_confidence / sum(len(r) for r in results.values())
        self.accuracy_label.setText(f"Точность: {avg_confidence:.2%}")
        
        # Обновляем статистику по полям
        self.field_stats.setRowCount(0)
        for field, stats in field_stats.items():
            row = self.field_stats.rowCount()
            self.field_stats.insertRow(row)
            self.field_stats.setItem(row, 0, QTableWidgetItem(field))
            avg = stats["total"] / stats["count"]
            self.field_stats.setItem(row, 1, QTableWidgetItem(f"{avg:.2%}"))
            
    def export_results(self):
        """Экспорт результатов"""
        if not self.current_results:
            QMessageBox.warning(self, "Ошибка", "Нет результатов для экспорта")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результаты",
            "",
            "JSON (*.json);;Excel (*.xlsx);;CSV (*.csv)"
        )
        
        if file_path:
            try:
                ext = os.path.splitext(file_path)[1]
                if ext == ".json":
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(self.current_results, f, ensure_ascii=False, indent=2)
                elif ext == ".xlsx":
                    self.export_to_excel(file_path)
                elif ext == ".csv":
                    self.export_to_csv(file_path)
                    
                self.statusBar.showMessage(f"Результаты сохранены в {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {e}")
                
    def load_settings(self):
        """Загрузка настроек"""
        settings = QSettings("InvoiceRecognition", "GUI")
        
        # Восстанавливаем размер и положение окна
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        # Восстанавливаем настройки
        self.model_combo.setCurrentText(settings.value("model", "YOLOv5s"))
        self.ocr_combo.setCurrentText(settings.value("ocr", "EasyOCR"))
        self.conf_spin.setValue(int(settings.value("confidence", 80)))
        self.gpu_check.setChecked(settings.value("use_gpu", True, type=bool))
        
    def save_settings(self):
        """Сохранение настроек"""
        settings = QSettings("InvoiceRecognition", "GUI")
        
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("model", self.model_combo.currentText())
        settings.setValue("ocr", self.ocr_combo.currentText())
        settings.setValue("confidence", self.conf_spin.value())
        settings.setValue("use_gpu", self.gpu_check.isChecked())
        
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        self.save_settings()
        event.accept()
        
    def set_theme(self, theme: str):
        """Установка темы оформления"""
        if theme == "dark":
            # Применяем темную тему
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QTableWidget {
                    gridline-color: #3d3d3d;
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QHeaderView::section {
                    background-color: #3d3d3d;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    border: 1px solid #505050;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QComboBox, QSpinBox {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    border: 1px solid #505050;
                }
            """)
        else:
            # Сбрасываем на светлую тему
            self.setStyleSheet("")
            
    def toggle_logs(self, show: bool):
        """Показать/скрыть панель логов"""
        for dock in self.findChildren(QDockWidget):
            if dock.windowTitle() == "Логи":
                dock.setVisible(show)
                
    def show_settings(self):
        """Показ окна настроек"""
        # TODO: Реализовать окно настроек
        pass
        
    def run_cleanup(self):
        """Запуск очистки временных файлов"""
        reply = QMessageBox.question(
            self,
            "Очистка",
            "Вы уверены, что хотите очистить временные файлы?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from scripts.cleanup import main as cleanup_main
                cleanup_main()
                self.statusBar.showMessage("Очистка выполнена")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при очистке: {e}")
                
    def check_system(self):
        """Запуск проверки системы"""
        try:
            from scripts.check_system import main as check_main
            check_main()
            self.statusBar.showMessage("Проверка системы выполнена")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при проверке: {e}")
            
    def show_about(self):
        """Показ информации о программе"""
        QMessageBox.about(
            self,
            "О программе",
            """<h3>Система распознавания счетов</h3>
            <p>Версия 1.0</p>
            <p>Система для автоматического распознавания информации со сканов счетов
            с использованием технологий компьютерного зрения и машинного обучения.</p>
            <p>Основные возможности:</p>
            <ul>
                <li>Распознавание ключевых полей счета</li>
                <li>Извлечение табличных данных</li>
                <li>Поддержка различных форматов</li>
                <li>Высокая точность распознавания</li>
            </ul>"""
        ) 