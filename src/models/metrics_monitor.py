import logging
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import json
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import precision_recall_fscore_support

logger = logging.getLogger("MetricsMonitor")

class MetricsMonitor:
    def __init__(self,
                 output_dir: Union[str, Path] = "metrics",
                 history_file: str = "metrics_history.json"):
        """
        Инициализация монитора метрик
        
        Args:
            output_dir: директория для сохранения метрик
            history_file: файл истории метрик
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.history_file = self.output_dir / history_file
        self.metrics_history = self._load_history()
        
        logger.info("Инициализирован монитор метрик")
        
    def _load_history(self) -> Dict:
        """
        Загрузка истории метрик
        
        Returns:
            Dict: история метрик
        """
        try:
            if self.history_file.exists():
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {
                "metrics": [],
                "errors": [],
                "summary": {
                    "total_processed": 0,
                    "total_errors": 0,
                    "average_precision": 0.0,
                    "average_recall": 0.0,
                    "average_f1": 0.0
                }
            }
        except Exception as e:
            logger.error(f"Ошибка загрузки истории: {str(e)}")
            return {
                "metrics": [],
                "errors": [],
                "summary": {
                    "total_processed": 0,
                    "total_errors": 0,
                    "average_precision": 0.0,
                    "average_recall": 0.0,
                    "average_f1": 0.0
                }
            }
            
    def _save_history(self) -> None:
        """
        Сохранение истории метрик
        """
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.metrics_history, f, ensure_ascii=False, indent=2)
                
            logger.info("История метрик сохранена")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения истории: {str(e)}")
            
    def add_metrics(self,
                   metrics: Dict[str, float],
                   metadata: Optional[Dict] = None) -> None:
        """
        Добавление метрик
        
        Args:
            metrics: словарь метрик
            metadata: дополнительные метаданные
        """
        try:
            # Добавляем метрики
            entry = {
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics
            }
            
            if metadata:
                entry["metadata"] = metadata
                
            self.metrics_history["metrics"].append(entry)
            
            # Обновляем summary
            self._update_summary()
            
            # Сохраняем историю
            self._save_history()
            
            logger.info("Метрики добавлены")
            
        except Exception as e:
            logger.error(f"Ошибка добавления метрик: {str(e)}")
            
    def add_error(self,
                 error: str,
                 metadata: Optional[Dict] = None) -> None:
        """
        Добавление ошибки
        
        Args:
            error: описание ошибки
            metadata: дополнительные метаданные
        """
        try:
            # Добавляем ошибку
            entry = {
                "timestamp": datetime.now().isoformat(),
                "error": error
            }
            
            if metadata:
                entry["metadata"] = metadata
                
            self.metrics_history["errors"].append(entry)
            
            # Обновляем summary
            self.metrics_history["summary"]["total_errors"] += 1
            
            # Сохраняем историю
            self._save_history()
            
            logger.info("Ошибка добавлена")
            
        except Exception as e:
            logger.error(f"Ошибка добавления ошибки: {str(e)}")
            
    def _update_summary(self) -> None:
        """
        Обновление сводки метрик
        """
        try:
            metrics = self.metrics_history["metrics"]
            
            if not metrics:
                return
                
            # Обновляем количество обработанных
            self.metrics_history["summary"]["total_processed"] = len(metrics)
            
            # Считаем средние метрики
            precisions = [m["metrics"].get("precision", 0.0) for m in metrics]
            recalls = [m["metrics"].get("recall", 0.0) for m in metrics]
            f1_scores = [m["metrics"].get("f1", 0.0) for m in metrics]
            
            self.metrics_history["summary"]["average_precision"] = np.mean(precisions)
            self.metrics_history["summary"]["average_recall"] = np.mean(recalls)
            self.metrics_history["summary"]["average_f1"] = np.mean(f1_scores)
            
        except Exception as e:
            logger.error(f"Ошибка обновления сводки: {str(e)}")
            
    def calculate_metrics(self,
                         y_true: List[Any],
                         y_pred: List[Any],
                         average: str = "weighted") -> Dict[str, float]:
        """
        Расчет метрик
        
        Args:
            y_true: истинные значения
            y_pred: предсказанные значения
            average: тип усреднения
            
        Returns:
            Dict[str, float]: словарь метрик
        """
        try:
            # Считаем метрики
            precision, recall, f1, _ = precision_recall_fscore_support(
                y_true, y_pred, average=average
            )
            
            metrics = {
                "precision": precision,
                "recall": recall,
                "f1": f1
            }
            
            # Добавляем метрики
            self.add_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Ошибка расчета метрик: {str(e)}")
            raise
            
    def get_summary(self) -> Dict:
        """
        Получение сводки метрик
        
        Returns:
            Dict: сводка метрик
        """
        return self.metrics_history["summary"]
        
    def get_metrics_history(self,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict]:
        """
        Получение истории метрик
        
        Args:
            start_date: начальная дата
            end_date: конечная дата
            
        Returns:
            List[Dict]: история метрик
        """
        try:
            metrics = self.metrics_history["metrics"]
            
            if start_date:
                start = datetime.fromisoformat(start_date)
                metrics = [m for m in metrics if datetime.fromisoformat(m["timestamp"]) >= start]
                
            if end_date:
                end = datetime.fromisoformat(end_date)
                metrics = [m for m in metrics if datetime.fromisoformat(m["timestamp"]) <= end]
                
            return metrics
            
        except Exception as e:
            logger.error(f"Ошибка получения истории: {str(e)}")
            return []
            
    def get_errors_history(self,
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> List[Dict]:
        """
        Получение истории ошибок
        
        Args:
            start_date: начальная дата
            end_date: конечная дата
            
        Returns:
            List[Dict]: история ошибок
        """
        try:
            errors = self.metrics_history["errors"]
            
            if start_date:
                start = datetime.fromisoformat(start_date)
                errors = [e for e in errors if datetime.fromisoformat(e["timestamp"]) >= start]
                
            if end_date:
                end = datetime.fromisoformat(end_date)
                errors = [e for e in errors if datetime.fromisoformat(e["timestamp"]) <= end]
                
            return errors
            
        except Exception as e:
            logger.error(f"Ошибка получения истории ошибок: {str(e)}")
            return []
            
    def plot_metrics(self,
                    metric_name: str,
                    output_file: Optional[str] = None) -> None:
        """
        Построение графика метрик
        
        Args:
            metric_name: название метрики
            output_file: путь для сохранения графика
        """
        try:
            # Получаем данные
            metrics = self.metrics_history["metrics"]
            timestamps = [datetime.fromisoformat(m["timestamp"]) for m in metrics]
            values = [m["metrics"].get(metric_name, 0.0) for m in metrics]
            
            # Строим график
            plt.figure(figsize=(10, 6))
            sns.set_style("whitegrid")
            plt.plot(timestamps, values, marker="o")
            plt.title(f"Динамика метрики {metric_name}")
            plt.xlabel("Время")
            plt.ylabel("Значение")
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Сохраняем график
            if output_file:
                plt.savefig(output_file)
            else:
                plt.savefig(self.output_dir / f"{metric_name}_history.png")
                
            plt.close()
            
            logger.info(f"График метрики {metric_name} построен")
            
        except Exception as e:
            logger.error(f"Ошибка построения графика: {str(e)}")
            
    def plot_errors(self,
                   output_file: Optional[str] = None) -> None:
        """
        Построение графика ошибок
        
        Args:
            output_file: путь для сохранения графика
        """
        try:
            # Получаем данные
            errors = self.metrics_history["errors"]
            timestamps = [datetime.fromisoformat(e["timestamp"]) for e in errors]
            
            # Строим график
            plt.figure(figsize=(10, 6))
            sns.set_style("whitegrid")
            plt.hist(timestamps, bins=20)
            plt.title("Распределение ошибок по времени")
            plt.xlabel("Время")
            plt.ylabel("Количество ошибок")
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Сохраняем график
            if output_file:
                plt.savefig(output_file)
            else:
                plt.savefig(self.output_dir / "errors_distribution.png")
                
            plt.close()
            
            logger.info("График ошибок построен")
            
        except Exception as e:
            logger.error(f"Ошибка построения графика ошибок: {str(e)}")
            
    def generate_report(self,
                       output_file: Optional[str] = None) -> str:
        """
        Генерация отчета
        
        Args:
            output_file: путь для сохранения отчета
            
        Returns:
            str: текст отчета
        """
        try:
            # Получаем сводку
            summary = self.metrics_history["summary"]
            
            # Формируем отчет
            report = [
                "# Отчет по метрикам качества распознавания",
                "",
                f"## Общая статистика",
                f"- Всего обработано: {summary['total_processed']}",
                f"- Всего ошибок: {summary['total_errors']}",
                f"- Средняя точность: {summary['average_precision']:.3f}",
                f"- Средний recall: {summary['average_recall']:.3f}",
                f"- Средний F1-score: {summary['average_f1']:.3f}",
                "",
                "## Последние ошибки"
            ]
            
            # Добавляем последние ошибки
            errors = self.metrics_history["errors"][-5:]
            for error in errors:
                report.append(f"- {error['timestamp']}: {error['error']}")
                
            # Объединяем отчет
            report_text = "\n".join(report)
            
            # Сохраняем отчет
            if output_file:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(report_text)
            else:
                with open(self.output_dir / "metrics_report.md", "w", encoding="utf-8") as f:
                    f.write(report_text)
                    
            logger.info("Отчет сгенерирован")
            
            return report_text
            
        except Exception as e:
            logger.error(f"Ошибка генерации отчета: {str(e)}")
            return "" 