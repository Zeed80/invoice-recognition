import re
from typing import Dict, List, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger("DataExtractor")

class DataExtractor:
    def __init__(self):
        """Инициализация экстрактора данных"""
        # Регулярные выражения для извлечения данных
        self.patterns = {
            'invoice_number': re.compile(r'(?:Счет|Invoice)[\s№#]*([A-ZА-Я0-9-]+)', re.I),
            'date': re.compile(r'(?:от|from)?\s*(\d{2}[./-]\d{2}[./-]\d{4})'),
            'total_amount': re.compile(r'(?:Итого|Total)[\s:]*(\d+[\s.,]?\d*)\s*(?:руб|₽|RUB)', re.I),
            'supplier_name': re.compile(r'(?:Поставщик|Supplier)[\s:]*([^\n]+)', re.I),
            'inn': re.compile(r'(?:ИНН|INN)[\s:]*(\d{10}|\d{12})', re.I),
            'address': re.compile(r'(?:Адрес|Address)[\s:]*([^\n]+)', re.I),
            'payment_info': re.compile(r'(?:Реквизиты|Payment Info)[\s:]*([^\n]+)', re.I)
        }
        
    def extract_data(self, 
                    text: str, 
                    region_type: str,
                    confidence: Optional[float] = None) -> Dict[str, Union[str, float, None]]:
        """
        Извлечение структурированных данных из текста
        
        Args:
            text: распознанный текст
            region_type: тип области (invoice_number, date, etc.)
            confidence: оценка уверенности распознавания
            
        Returns:
            Dict[str, Union[str, float, None]]: извлеченные данные
        """
        if region_type not in self.patterns:
            logger.warning(f"Неизвестный тип области: {region_type}")
            return {
                'value': None,
                'confidence': confidence,
                'raw_text': text
            }
            
        # Извлечение данных с помощью регулярного выражения
        pattern = self.patterns[region_type]
        match = pattern.search(text)
        
        if match:
            value = match.group(1).strip()
            
            # Постобработка в зависимости от типа данных
            if region_type == 'date':
                value = self._normalize_date(value)
            elif region_type == 'total_amount':
                value = self._normalize_amount(value)
            elif region_type == 'inn':
                value = self._normalize_inn(value)
                
            return {
                'value': value,
                'confidence': confidence,
                'raw_text': text
            }
        else:
            logger.warning(f"Не удалось извлечь {region_type} из текста: {text}")
            return {
                'value': None,
                'confidence': confidence,
                'raw_text': text
            }
            
    def _normalize_date(self, date_str: str) -> str:
        """
        Нормализация формата даты
        
        Args:
            date_str: строка с датой
            
        Returns:
            str: нормализованная дата в формате DD.MM.YYYY
        """
        # Замена разделителей
        date_str = date_str.replace('/', '.').replace('-', '.')
        
        try:
            # Парсинг даты
            date = datetime.strptime(date_str, '%d.%m.%Y')
            return date.strftime('%d.%m.%Y')
        except ValueError:
            logger.error(f"Ошибка при парсинге даты: {date_str}")
            return date_str
            
    def _normalize_amount(self, amount_str: str) -> str:
        """
        Нормализация формата суммы
        
        Args:
            amount_str: строка с суммой
            
        Returns:
            str: нормализованная сумма
        """
        # Удаление пробелов и замена запятой на точку
        amount_str = amount_str.replace(' ', '').replace(',', '.')
        
        try:
            # Преобразование в float и обратно в строку
            amount = float(amount_str)
            return f"{amount:.2f}"
        except ValueError:
            logger.error(f"Ошибка при парсинге суммы: {amount_str}")
            return amount_str
            
    def _normalize_inn(self, inn_str: str) -> str:
        """
        Нормализация формата ИНН
        
        Args:
            inn_str: строка с ИНН
            
        Returns:
            str: нормализованный ИНН
        """
        # Удаление всех нецифровых символов
        inn_str = re.sub(r'\D', '', inn_str)
        
        # Проверка длины
        if len(inn_str) not in [10, 12]:
            logger.warning(f"Некорректная длина ИНН: {inn_str}")
            
        return inn_str
        
    def extract_table_data(self, 
                          text: str, 
                          confidence: Optional[float] = None) -> List[Dict[str, Union[str, float, None]]]:
        """
        Извлечение данных из таблицы товаров
        
        Args:
            text: распознанный текст таблицы
            confidence: оценка уверенности распознавания
            
        Returns:
            List[Dict[str, Union[str, float, None]]]: список товаров
        """
        # Разбиваем текст на строки
        lines = text.split('\n')
        
        items = []
        for line in lines:
            # Пропускаем пустые строки и заголовки
            if not line.strip() or any(header in line.lower() for header in ['наименование', 'количество', 'цена', 'сумма']):
                continue
                
            # Разбиваем строку на колонки
            columns = re.split(r'\s{2,}', line.strip())
            
            if len(columns) >= 4:  # Минимальное количество колонок
                item = {
                    'name': columns[0],
                    'quantity': self._parse_number(columns[1]),
                    'price': self._parse_number(columns[2]),
                    'amount': self._parse_number(columns[3]),
                    'confidence': confidence,
                    'raw_text': line
                }
                items.append(item)
                
        return items
        
    def _parse_number(self, text: str) -> Optional[float]:
        """
        Парсинг числового значения
        
        Args:
            text: строка с числом
            
        Returns:
            Optional[float]: распарсенное число или None
        """
        # Удаление пробелов и замена запятой на точку
        text = text.replace(' ', '').replace(',', '.')
        
        try:
            return float(text)
        except ValueError:
            return None 