import cv2
import numpy as np
from typing import Dict, List, Optional, Union
import logging
import os
from pathlib import Path
import re
import easyocr
from google.cloud import vision
from google.oauth2 import service_account
import torch

logger = logging.getLogger("OCRProcessor")

class OCRProcessor:
    def __init__(self, 
                 ocr_engine: str = 'easyocr',
                 google_credentials_path: Optional[str] = None,
                 languages: List[str] = ['ru', 'en']):
        """
        Инициализация OCR процессора
        
        Args:
            ocr_engine: 'easyocr' или 'google'
            google_credentials_path: путь к учетным данным Google Cloud
            languages: список языков для распознавания
        """
        self.ocr_engine = ocr_engine.lower()
        self.languages = languages
        
        if self.ocr_engine == 'easyocr':
            logger.info(f"Инициализация EasyOCR с языками: {languages}")
            self.reader = easyocr.Reader(languages, gpu=torch.cuda.is_available())
            self.client = None
        elif self.ocr_engine == 'google':
            if not google_credentials_path:
                raise ValueError("Для Google Cloud Vision OCR необходимо указать путь к учетным данным")
                
            if not os.path.exists(google_credentials_path):
                raise FileNotFoundError(f"Файл учетных данных не найден: {google_credentials_path}")
                
            logger.info("Инициализация Google Cloud Vision OCR")
            credentials = service_account.Credentials.from_service_account_file(
                google_credentials_path
            )
            self.client = vision.ImageAnnotatorClient(credentials=credentials)
            self.reader = None
        else:
            raise ValueError(f"Неподдерживаемый OCR движок: {ocr_engine}")
            
        # Регулярные выражения для постобработки
        self.date_pattern = re.compile(r'\d{2}[./-]\d{2}[./-]\d{4}')
        self.amount_pattern = re.compile(r'(\d+[\s.,]?\d*)\s*(?:руб|₽|RUB)')
        self.inn_pattern = re.compile(r'(?:ИНН|INN)[:\s]*(\d{10}|\d{12})')
        
    def recognize(self, 
                 image: np.ndarray, 
                 region: Optional[List[int]] = None) -> str:
        """
        Распознавание текста в области изображения
        
        Args:
            image: исходное изображение
            region: область для распознавания [x1, y1, x2, y2]
            
        Returns:
            str: распознанный текст
        """
        # Вырезаем область если указана
        if region:
            x1, y1, x2, y2 = region
            image = image[y1:y2, x1:x2]
            
        # Предобработка изображения
        processed_image = self._preprocess_image(image)
        
        # Распознавание текста
        if self.ocr_engine == 'easyocr':
            results = self.reader.readtext(processed_image)
            text = ' '.join([result[1] for result in results])
        else:  # google
            # Конвертация в bytes
            success, encoded_image = cv2.imencode('.jpg', processed_image)
            if not success:
                raise ValueError("Ошибка при кодировании изображения")
                
            content = encoded_image.tobytes()
            image = vision.Image(content=content)
            
            # Распознавание текста
            response = self.client.text_detection(image=image)
            if response.error.message:
                raise Exception(
                    '{}\nFor more info on error messages, check: '
                    'https://cloud.google.com/apis/design/errors'.format(
                        response.error.message))
                        
            text = response.text_annotations[0].description if response.text_annotations else ""
            
        # Постобработка текста
        text = self._postprocess_text(text)
        
        return text
        
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Предобработка изображения для улучшения распознавания
        
        Args:
            image: исходное изображение
            
        Returns:
            np.ndarray: обработанное изображение
        """
        # Конвертация в оттенки серого
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Адаптивная бинаризация
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Удаление шума
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # Увеличение контраста
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(binary)
        
        return enhanced
        
    def _postprocess_text(self, text: str) -> str:
        """
        Постобработка распознанного текста
        
        Args:
            text: исходный текст
            
        Returns:
            str: обработанный текст
        """
        # Нормализация пробелов
        text = ' '.join(text.split())
        
        # Исправление типичных ошибок OCR
        text = text.replace('0', 'О').replace('1', 'I')
        
        # Извлечение структурированных данных
        date_match = self.date_pattern.search(text)
        if date_match:
            date = date_match.group(0)
            # Нормализация формата даты
            date = date.replace('/', '.').replace('-', '.')
            text = text.replace(date_match.group(0), date)
            
        amount_match = self.amount_pattern.search(text)
        if amount_match:
            amount = amount_match.group(1)
            # Нормализация формата суммы
            amount = amount.replace(' ', '').replace(',', '.')
            text = text.replace(amount_match.group(0), f"{amount} руб.")
            
        inn_match = self.inn_pattern.search(text)
        if inn_match:
            inn = inn_match.group(1)
            text = text.replace(inn_match.group(0), f"ИНН: {inn}")
            
        return text
        
    def recognize_with_confidence(self, 
                                image: np.ndarray, 
                                region: Optional[List[int]] = None) -> Dict[str, Union[str, float]]:
        """
        Распознавание текста с оценкой уверенности
        
        Args:
            image: исходное изображение
            region: область для распознавания [x1, y1, x2, y2]
            
        Returns:
            Dict[str, Union[str, float]]: текст и оценка уверенности
        """
        if self.ocr_engine == 'easyocr':
            if region:
                x1, y1, x2, y2 = region
                image = image[y1:y2, x1:x2]
                
            processed_image = self._preprocess_image(image)
            results = self.reader.readtext(processed_image)
            
            # Расчет средней уверенности
            confidences = [result[2] for result in results]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            text = ' '.join([result[1] for result in results])
            text = self._postprocess_text(text)
            
            return {
                'text': text,
                'confidence': avg_confidence
            }
        else:
            # Google Cloud Vision не предоставляет оценку уверенности
            text = self.recognize(image, region)
            return {
                'text': text,
                'confidence': 1.0  # Заглушка
            } 