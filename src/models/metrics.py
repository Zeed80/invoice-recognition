from typing import Dict, List, Union, Optional, Any
import numpy as np
from datetime import datetime
import json
import logging
from pathlib import Path
import threading
import time
from sklearn.metrics import precision_score, recall_score, f1_score
from dataclasses import dataclass, asdict

logger = logging.getLogger("Metrics")

@dataclass
class MetricValue:
    """Значение метрики"""
    value: float
    timestamp: float = time.time()
    metadata: Optional[Dict[str, Any]] = None

class Metrics:
    def __init__(self, metrics_dir: Union[str, Path] = "data/metrics"):
        """
        Инициализация менеджера метрик
        
        Args:
            metrics_dir: директория для хранения метрик
        """
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Загружаем метрики
        self.metrics: Dict[str, List[MetricValue]] = {}
        self._load_metrics()
        
        logger.info("Инициализирован менеджер метрик")
        
    def _load_metrics(self) -> None:
        """
        Загрузка метрик из файлов
        """
        try:
            # Очищаем список метрик
            self.metrics.clear()
            
            # Загружаем метрики из файлов
            for metric_file in self.metrics_dir.glob("*.json"):
                try:
                    with open(metric_file, "r", encoding="utf-8") as f:
                        metric_data = json.load(f)
                        
                    # Создаем список значений
                    values = []
                    for value_data in metric_data["values"]:
                        values.append(MetricValue(
                            value=value_data["value"],
                            timestamp=value_data["timestamp"],
                            metadata=value_data.get("metadata")
                        ))
                        
                    # Добавляем метрику
                    self.metrics[metric_file.stem] = values
                    
                except Exception as e:
                    logger.error(f"Ошибка загрузки метрики из {metric_file}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Ошибка загрузки метрик: {str(e)}")
            
    def _save_metric(self, metric_name: str) -> bool:
        """
        Сохранение метрики в файл
        
        Args:
            metric_name: название метрики
            
        Returns:
            bool: успешность сохранения
        """
        try:
            # Создаем файл метрики
            metric_file = self.metrics_dir / f"{metric_name}.json"
            
            # Сохраняем метрику
            with open(metric_file, "w", encoding="utf-8") as f:
                json.dump({
                    "values": [
                        {
                            "value": value.value,
                            "timestamp": value.timestamp,
                            "metadata": value.metadata
                        }
                        for value in self.metrics[metric_name]
                    ]
                }, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения метрики {metric_name}: {str(e)}")
            return False
            
    def add_metric(self, metric_name: str, value: float, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Добавление значения метрики
        
        Args:
            metric_name: название метрики
            value: значение
            metadata: дополнительные данные
            
        Returns:
            bool: успешность добавления
        """
        try:
            # Создаем значение
            metric_value = MetricValue(
                value=value,
                metadata=metadata
            )
            
            # Добавляем значение
            if metric_name not in self.metrics:
                self.metrics[metric_name] = []
            self.metrics[metric_name].append(metric_value)
            
            # Сохраняем метрику
            return self._save_metric(metric_name)
            
        except Exception as e:
            logger.error(f"Ошибка добавления метрики {metric_name}: {str(e)}")
            return False
            
    def get_metric(self, metric_name: str, start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[MetricValue]:
        """
        Получение значений метрики
        
        Args:
            metric_name: название метрики
            start_time: начальное время
            end_time: конечное время
            
        Returns:
            List[MetricValue]: значения метрики
        """
        try:
            # Получаем значения
            values = self.metrics.get(metric_name, [])
            
            # Фильтруем по времени
            if start_time is not None:
                values = [value for value in values if value.timestamp >= start_time]
                
            if end_time is not None:
                values = [value for value in values if value.timestamp <= end_time]
                
            return values
            
        except Exception as e:
            logger.error(f"Ошибка получения метрики {metric_name}: {str(e)}")
            return []
            
    def get_metric_stats(self, metric_name: str, start_time: Optional[float] = None, end_time: Optional[float] = None) -> Dict[str, float]:
        """
        Получение статистики метрики
        
        Args:
            metric_name: название метрики
            start_time: начальное время
            end_time: конечное время
            
        Returns:
            Dict[str, float]: статистика
        """
        try:
            # Получаем значения
            values = self.get_metric(metric_name, start_time, end_time)
            
            if not values:
                return {
                    "min": 0.0,
                    "max": 0.0,
                    "avg": 0.0,
                    "count": 0
                }
                
            # Считаем статистику
            return {
                "min": min(value.value for value in values),
                "max": max(value.value for value in values),
                "avg": sum(value.value for value in values) / len(values),
                "count": len(values)
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики метрики {metric_name}: {str(e)}")
            return {
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "count": 0
            }
            
    def clear_metric(self, metric_name: str) -> bool:
        """
        Очистка метрики
        
        Args:
            metric_name: название метрики
            
        Returns:
            bool: успешность очистки
        """
        try:
            # Удаляем файл метрики
            metric_file = self.metrics_dir / f"{metric_name}.json"
            if metric_file.exists():
                metric_file.unlink()
                
            # Удаляем метрику
            if metric_name in self.metrics:
                del self.metrics[metric_name]
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка очистки метрики {metric_name}: {str(e)}")
            return False
            
    def get_metrics(self) -> List[str]:
        """
        Получение списка метрик
        
        Returns:
            List[str]: список метрик
        """
        try:
            return list(self.metrics.keys())
            
        except Exception as e:
            logger.error(f"Ошибка получения списка метрик: {str(e)}")
            return []
            
    def get_metrics_stats(self, start_time: Optional[float] = None, end_time: Optional[float] = None) -> Dict[str, Dict[str, float]]:
        """
        Получение статистики всех метрик
        
        Args:
            start_time: начальное время
            end_time: конечное время
            
        Returns:
            Dict[str, Dict[str, float]]: статистика
        """
        try:
            # Создаем статистику
            stats = {}
            
            # Считаем статистику
            for metric_name in self.metrics:
                stats[metric_name] = self.get_metric_stats(metric_name, start_time, end_time)
                
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики метрик: {str(e)}")
            return {}

class MetricsCalculator:
    def __init__(self, output_dir: str = "metrics"):
        """
        Инициализация калькулятора метрик
        
        Args:
            output_dir: директория для сохранения метрик
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Метрики для разных типов данных
        self.metrics = {
            'invoice_number': {'tp': 0, 'fp': 0, 'fn': 0},
            'date': {'tp': 0, 'fp': 0, 'fn': 0},
            'total_amount': {'tp': 0, 'fp': 0, 'fn': 0},
            'supplier_name': {'tp': 0, 'fp': 0, 'fn': 0},
            'inn': {'tp': 0, 'fp': 0, 'fn': 0},
            'address': {'tp': 0, 'fp': 0, 'fn': 0},
            'payment_info': {'tp': 0, 'fp': 0, 'fn': 0},
            'items_table': {'tp': 0, 'fp': 0, 'fn': 0}
        }
        
    def calculate_metrics(self, 
                         predicted: Dict[str, Union[str, float, None]], 
                         ground_truth: Dict[str, Union[str, float, None]], 
                         region_type: str) -> Dict[str, float]:
        """
        Расчет метрик для одного типа данных
        
        Args:
            predicted: предсказанные данные
            ground_truth: эталонные данные
            region_type: тип области
            
        Returns:
            Dict[str, float]: метрики качества
        """
        if region_type not in self.metrics:
            logger.warning(f"Неизвестный тип области: {region_type}")
            return {}
            
        # Получаем значения
        pred_value = predicted.get('value')
        true_value = ground_truth.get('value')
        
        # Обновляем метрики
        if pred_value == true_value:
            if pred_value is not None:
                self.metrics[region_type]['tp'] += 1
        else:
            if pred_value is not None:
                self.metrics[region_type]['fp'] += 1
            if true_value is not None:
                self.metrics[region_type]['fn'] += 1
                
        # Рассчитываем метрики
        tp = self.metrics[region_type]['tp']
        fp = self.metrics[region_type]['fp']
        fn = self.metrics[region_type]['fn']
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
        
    def calculate_table_metrics(self, 
                              predicted_items: List[Dict], 
                              ground_truth_items: List[Dict]) -> Dict[str, float]:
        """
        Расчет метрик для таблицы товаров
        
        Args:
            predicted_items: предсказанные товары
            ground_truth_items: эталонные товары
            
        Returns:
            Dict[str, float]: метрики качества
        """
        # Считаем количество совпадений по наименованию
        tp = 0
        fp = 0
        fn = 0
        
        # Создаем множества наименований
        pred_names = {item['name'].lower() for item in predicted_items}
        true_names = {item['name'].lower() for item in ground_truth_items}
        
        # Считаем TP, FP, FN
        tp = len(pred_names.intersection(true_names))
        fp = len(pred_names - true_names)
        fn = len(true_names - pred_names)
        
        # Обновляем метрики
        self.metrics['items_table']['tp'] += tp
        self.metrics['items_table']['fp'] += fp
        self.metrics['items_table']['fn'] += fn
        
        # Рассчитываем метрики
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
        
    def get_overall_metrics(self) -> Dict[str, float]:
        """
        Получение общих метрик по всем типам данных
        
        Returns:
            Dict[str, float]: общие метрики
        """
        total_tp = sum(m['tp'] for m in self.metrics.values())
        total_fp = sum(m['fp'] for m in self.metrics.values())
        total_fn = sum(m['fn'] for m in self.metrics.values())
        
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
        
    def save_metrics(self, filename: Optional[str] = None) -> str:
        """
        Сохранение метрик в файл
        
        Args:
            filename: имя файла (если None, генерируется автоматически)
            
        Returns:
            str: путь к сохраненному файлу
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_{timestamp}.json"
            
        metrics_data = {
            'overall': self.get_overall_metrics(),
            'by_type': {
                region_type: {
                    'precision': tp / (tp + fp) if (tp + fp) > 0 else 0.0,
                    'recall': tp / (tp + fn) if (tp + fn) > 0 else 0.0,
                    'f1': 2 * (tp / (tp + fp) * tp / (tp + fn)) / (tp / (tp + fp) + tp / (tp + fn)) 
                          if (tp + fp) > 0 and (tp + fn) > 0 else 0.0
                }
                for region_type, (tp, fp, fn) in self.metrics.items()
            }
        }
        
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Метрики сохранены в {filepath}")
        return str(filepath)
        
    def reset_metrics(self):
        """Сброс всех метрик"""
        for metrics in self.metrics.values():
            metrics['tp'] = 0
            metrics['fp'] = 0
            metrics['fn'] = 0
        logger.info("Метрики сброшены") 