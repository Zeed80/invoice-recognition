import cv2
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
import re

class TableParser:
    def __init__(self):
        """Инициализация парсера таблиц"""
        # Регулярные выражения для извлечения данных
        self.amount_pattern = re.compile(r'(\d+[\s.,]?\d*)')
        self.price_pattern = re.compile(r'(\d+[\s.,]?\d*)\s*руб')
        
    def parse_table(self, 
                   image: np.ndarray, 
                   table_region: Dict[str, int],
                   ocr_text: str) -> List[Dict]:
        """
        Парсинг таблицы товаров
        
        Args:
            image: изображение счета
            table_region: область таблицы {x1, y1, x2, y2}
            ocr_text: распознанный текст в области таблицы
            
        Returns:
            List[Dict]: список товаров с их характеристиками
        """
        # Вырезаем область таблицы
        table_img = image[
            table_region['y1']:table_region['y2'],
            table_region['x1']:table_region['x2']
        ]
        
        # Предобработка изображения для лучшего распознавания структуры
        processed_img = self._preprocess_table_image(table_img)
        
        # Определение строк и столбцов
        rows, cols = self._detect_table_structure(processed_img)
        
        # Разбиваем текст на строки
        text_lines = ocr_text.split('\n')
        
        # Парсим данные
        items = []
        for i, line in enumerate(text_lines):
            if i < len(rows) - 1:  # Пропускаем заголовок
                item = self._parse_table_row(line, cols)
                if item:
                    items.append(item)
                    
        return items
    
    def _preprocess_table_image(self, image: np.ndarray) -> np.ndarray:
        """
        Предобработка изображения таблицы
        
        Args:
            image: изображение таблицы
            
        Returns:
            np.ndarray: обработанное изображение
        """
        # Преобразование в оттенки серого
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Адаптивная бинаризация
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Морфологические операции для удаления шума
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        return binary
    
    def _detect_table_structure(self, 
                              binary_image: np.ndarray) -> Tuple[List[int], List[int]]:
        """
        Определение структуры таблицы (строки и столбцы)
        
        Args:
            binary_image: бинаризованное изображение таблицы
            
        Returns:
            Tuple[List[int], List[int]]: координаты строк и столбцов
        """
        # Определение горизонтальных линий (строки)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, horizontal_kernel)
        
        # Определение вертикальных линий (столбцы)
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, vertical_kernel)
        
        # Нахождение координат строк
        row_contours, _ = cv2.findContours(
            horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        rows = sorted([cv2.boundingRect(cnt)[1] for cnt in row_contours])
        
        # Нахождение координат столбцов
        col_contours, _ = cv2.findContours(
            vertical_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        cols = sorted([cv2.boundingRect(cnt)[0] for cnt in col_contours])
        
        return rows, cols
    
    def _parse_table_row(self, 
                        text: str, 
                        col_positions: List[int]) -> Optional[Dict]:
        """
        Парсинг строки таблицы
        
        Args:
            text: текст строки
            col_positions: позиции столбцов
            
        Returns:
            Optional[Dict]: данные о товаре или None
        """
        # Разбиваем текст на части по позициям столбцов
        parts = []
        for i in range(len(col_positions) - 1):
            start = col_positions[i]
            end = col_positions[i + 1]
            part = text[start:end].strip()
            parts.append(part)
            
        if len(parts) < 3:  # Минимальное количество столбцов
            return None
            
        # Извлекаем данные
        item = {
            'name': parts[0],
            'quantity': None,
            'price': None,
            'amount': None
        }
        
        # Извлекаем количество
        quantity_match = self.amount_pattern.search(parts[1])
        if quantity_match:
            item['quantity'] = float(quantity_match.group(1).replace(',', '.'))
            
        # Извлекаем цену
        price_match = self.price_pattern.search(parts[2])
        if price_match:
            item['price'] = float(price_match.group(1).replace(',', '.'))
            
        # Извлекаем сумму
        amount_match = self.amount_pattern.search(parts[-1])
        if amount_match:
            item['amount'] = float(amount_match.group(1).replace(',', '.'))
            
        return item 