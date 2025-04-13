import torch
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger("InvoiceDetector")

class InvoiceDetector:
    def __init__(self, model_path: Optional[str] = None):
        """
        Инициализация детектора областей счета
        
        Args:
            model_path: путь к модели YOLOv5
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Используется устройство: {self.device}")
        
        if model_path is None:
            # Используем предобученную модель по умолчанию
            model_path = Path(__file__).parent / "weights" / "invoice_detector.pt"
            
        if not Path(model_path).exists():
            logger.warning(f"Модель не найдена по пути {model_path}. Используется детектор по умолчанию.")
            self.model = None
        else:
            try:
                self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
                self.model.to(self.device)
                logger.info(f"Модель загружена из {model_path}")
            except Exception as e:
                logger.error(f"Ошибка при загрузке модели: {str(e)}")
                self.model = None
                
        # Классы для детекции
        self.classes = {
            0: 'invoice_number',
            1: 'date',
            2: 'total_amount',
            3: 'supplier_name',
            4: 'inn',
            5: 'items_table',
            6: 'address',
            7: 'payment_info',
            8: 'logo'
        }
        
    def detect(self, image: np.ndarray) -> Dict[str, List[int]]:
        """
        Детекция областей счета
        
        Args:
            image: изображение счета
            
        Returns:
            Dict[str, List[int]]: словарь с координатами областей
        """
        if self.model is None:
            # Если модель не загружена, используем детектор по умолчанию
            return self._default_detector(image)
            
        # Предобработка изображения
        img = self._preprocess_image(image)
        
        # Детекция
        results = self.model(img)
        
        # Обработка результатов
        detections = {}
        for pred in results.xyxy[0].cpu().numpy():
            x1, y1, x2, y2, conf, cls = pred
            if conf > 0.5:  # Порог уверенности
                class_name = self.classes[int(cls)]
                if class_name not in detections:
                    detections[class_name] = []
                detections[class_name].append([int(x1), int(y1), int(x2), int(y2)])
                
        # Выбор лучшего детекта для каждого класса
        final_detections = {}
        for class_name, boxes in detections.items():
            if boxes:
                # Выбираем бокс с максимальной площадью
                best_box = max(boxes, key=lambda box: (box[2] - box[0]) * (box[3] - box[1]))
                final_detections[class_name] = best_box
                
        return final_detections
        
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Предобработка изображения для детекции
        
        Args:
            image: исходное изображение
            
        Returns:
            np.ndarray: обработанное изображение
        """
        # Конвертация в RGB
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        elif image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
        # Изменение размера
        max_size = 1280
        h, w = image.shape[:2]
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            image = cv2.resize(image, None, fx=scale, fy=scale)
            
        return image
        
    def _default_detector(self, image: np.ndarray) -> Dict[str, List[int]]:
        """
        Детектор по умолчанию на основе правил
        
        Args:
            image: изображение счета
            
        Returns:
            Dict[str, List[int]]: словарь с координатами областей
        """
        # Конвертация в оттенки серого
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Адаптивная бинаризация
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Поиск контуров
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Фильтрация контуров по размеру
        h, w = image.shape[:2]
        min_area = (h * w) * 0.001  # Минимальная площадь 0.1% от изображения
        max_area = (h * w) * 0.5    # Максимальная площадь 50% от изображения
        
        valid_contours = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area < area < max_area:
                valid_contours.append(cnt)
                
        # Преобразование контуров в прямоугольники
        detections = {}
        for i, cnt in enumerate(valid_contours):
            x, y, w, h = cv2.boundingRect(cnt)
            detections[f'region_{i}'] = [x, y, x + w, y + h]
            
        return detections
        
    def visualize_detections(self, 
                           image: np.ndarray, 
                           detections: Dict[str, List[int]]) -> np.ndarray:
        """
        Визуализация детекций на изображении
        
        Args:
            image: исходное изображение
            detections: словарь с координатами областей
            
        Returns:
            np.ndarray: изображение с визуализацией
        """
        vis_image = image.copy()
        
        # Цвета для разных классов
        colors = {
            'invoice_number': (255, 0, 0),    # Синий
            'date': (0, 255, 0),              # Зеленый
            'total_amount': (0, 0, 255),      # Красный
            'supplier_name': (255, 255, 0),   # Голубой
            'inn': (255, 0, 255),             # Пурпурный
            'items_table': (0, 255, 255),     # Желтый
            'address': (128, 128, 0),         # Темно-желтый
            'payment_info': (128, 0, 128),    # Темно-пурпурный
            'logo': (0, 128, 128)             # Темно-голубой
        }
        
        # Отрисовка детекций
        for class_name, bbox in detections.items():
            x1, y1, x2, y2 = bbox
            color = colors.get(class_name, (255, 255, 255))
            
            # Рисуем прямоугольник
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
            
            # Добавляем подпись
            label = f"{class_name}"
            (label_w, label_h), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            cv2.rectangle(
                vis_image, 
                (x1, y1 - label_h - 4), 
                (x1 + label_w, y1), 
                color, 
                -1
            )
            cv2.putText(
                vis_image, 
                label, 
                (x1, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                (0, 0, 0), 
                1
            )
            
        return vis_image 