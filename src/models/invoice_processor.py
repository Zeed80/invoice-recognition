import cv2
import numpy as np
from typing import Dict, Optional
from pathlib import Path
import logging
from datetime import datetime
import json
import os

from .detection import InvoiceDetector
from .ocr import OCRProcessor
from .table_parser import TableParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("invoice_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("InvoiceProcessor")

class InvoiceProcessor:
    def __init__(self,
                 detector_model_path: Optional[str] = None,
                 ocr_engine: str = 'easyocr',
                 google_credentials_path: Optional[str] = None,
                 output_dir: str = "output"):
        """
        Инициализация процессора счетов
        
        Args:
            detector_model_path: путь к модели YOLOv5
            ocr_engine: 'easyocr' или 'google'
            google_credentials_path: путь к учетным данным Google Cloud
            output_dir: директория для сохранения результатов
        """
        self.detector = InvoiceDetector(model_path=detector_model_path)
        self.ocr = OCRProcessor(
            ocr_engine=ocr_engine,
            google_credentials_path=google_credentials_path
        )
        self.table_parser = TableParser()
        
        # Создаем директорию для результатов
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Создаем поддиректории
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(exist_ok=True)
        self.json_dir = self.output_dir / "json"
        self.json_dir.mkdir(exist_ok=True)
        
        logger.info(f"Инициализирован процессор счетов с OCR движком: {ocr_engine}")
        
    def process_invoice(self, 
                       image_path: str,
                       visualize: bool = False,
                       save_results: bool = True) -> Dict:
        """
        Обработка счета
        
        Args:
            image_path: путь к изображению счета
            visualize: флаг визуализации результатов
            save_results: флаг сохранения результатов
            
        Returns:
            dict: структурированные данные счета
        """
        logger.info(f"Начало обработки счета: {image_path}")
        
        # Загрузка изображения
        image = cv2.imread(image_path)
        if image is None:
            error_msg = f"Не удалось загрузить изображение: {image_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Детекция областей
        logger.info("Детекция областей счета")
        detections = self.detector.detect(image)
        
        # Распознавание текста в каждой области
        logger.info("Распознавание текста в областях")
        results = {}
        for region_type, bbox in detections.items():
            text = self.ocr.recognize(image, region=bbox)
            results[region_type] = {
                'text': text,
                'bbox': bbox
            }
            
        # Парсинг таблицы товаров
        if 'items_table' in results:
            logger.info("Парсинг таблицы товаров")
            items = self.table_parser.parse_table(
                image, 
                results['items_table']['bbox'],
                results['items_table']['text']
            )
            results['items_table']['parsed_items'] = items
            
        # Визуализация результатов
        if visualize:
            logger.info("Визуализация результатов")
            vis_image = self.detector.visualize_detections(image, detections)
            
            # Сохраняем визуализацию
            if save_results:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                vis_path = self.images_dir / f"{Path(image_path).stem}_{timestamp}_processed.jpg"
                cv2.imwrite(str(vis_path), vis_image)
                results['visualization_path'] = str(vis_path)
                
        # Извлечение структурированных данных
        structured_data = self.extract_structured_data(results)
        
        # Сохранение результатов
        if save_results:
            self._save_results(image_path, structured_data, results)
            
        logger.info(f"Обработка счета завершена: {image_path}")
        return structured_data
        
    def extract_structured_data(self, results: Dict) -> Dict:
        """
        Извлечение структурированных данных из результатов распознавания
        
        Args:
            results: результаты распознавания
            
        Returns:
            dict: структурированные данные
        """
        structured_data = {
            'invoice_number': None,
            'date': None,
            'total_amount': None,
            'supplier': {
                'name': None,
                'inn': None,
                'address': None
            },
            'items': [],
            'payment_info': None
        }
        
        # Извлечение номера счета
        if 'invoice_number' in results:
            structured_data['invoice_number'] = results['invoice_number']['text']
            
        # Извлечение даты
        if 'date' in results:
            structured_data['date'] = results['date']['text']
            
        # Извлечение общей суммы
        if 'total_amount' in results:
            structured_data['total_amount'] = results['total_amount']['text']
            
        # Извлечение информации о поставщике
        if 'supplier_name' in results:
            structured_data['supplier']['name'] = results['supplier_name']['text']
        if 'inn' in results:
            structured_data['supplier']['inn'] = results['inn']['text']
        if 'address' in results:
            structured_data['supplier']['address'] = results['address']['text']
            
        # Извлечение платежной информации
        if 'payment_info' in results:
            structured_data['payment_info'] = results['payment_info']['text']
            
        # Извлечение таблицы товаров
        if 'items_table' in results and 'parsed_items' in results['items_table']:
            structured_data['items'] = results['items_table']['parsed_items']
            
        return structured_data
        
    def _save_results(self, image_path: str, structured_data: Dict, raw_results: Dict):
        """
        Сохранение результатов обработки
        
        Args:
            image_path: путь к исходному изображению
            structured_data: структурированные данные
            raw_results: сырые результаты распознавания
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(image_path).stem
        
        # Сохраняем структурированные данные
        json_path = self.json_dir / f"{base_name}_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'structured_data': structured_data,
                'raw_results': raw_results,
                'processing_time': timestamp,
                'source_image': image_path
            }, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Результаты сохранены: {json_path}")
        
    def batch_process(self, 
                     image_dir: str, 
                     visualize: bool = False) -> Dict[str, Dict]:
        """
        Пакетная обработка счетов
        
        Args:
            image_dir: директория с изображениями счетов
            visualize: флаг визуализации результатов
            
        Returns:
            Dict[str, Dict]: результаты обработки для каждого счета
        """
        image_dir = Path(image_dir)
        if not image_dir.exists():
            raise ValueError(f"Директория не существует: {image_dir}")
            
        results = {}
        for image_path in image_dir.glob("*.jpg"):
            try:
                result = self.process_invoice(
                    str(image_path),
                    visualize=visualize
                )
                results[str(image_path)] = result
            except Exception as e:
                logger.error(f"Ошибка при обработке {image_path}: {str(e)}")
                results[str(image_path)] = {"error": str(e)}
                
        return results 