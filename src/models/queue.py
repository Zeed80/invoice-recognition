import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import json
import os
import threading
from datetime import datetime
from enum import Enum

logger = logging.getLogger("Queue")

class TaskStatus(Enum):
    """Статусы задачи"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskType(Enum):
    INVOICE = "invoice"
    TABLE = "table"
    OCR = "ocr"
    METRICS = "metrics"

class Task:
    def __init__(self, task_id: str, task_type: TaskType, data: Dict[str, Any]):
        """
        Инициализация задачи
        
        Args:
            task_id: идентификатор задачи
            task_type: тип задачи
            data: данные задачи
        """
        self.task_id = task_id
        self.task_type = task_type
        self.data = data
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None

class QueueManager:
    def __init__(self, queue_dir: Union[str, Path] = "queue"):
        """
        Инициализация менеджера очереди
        
        Args:
            queue_dir: директория для хранения очереди
        """
        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        
        # Загружаем задачи
        self.tasks: Dict[str, Task] = {}
        self._load_tasks()
        
        # Блокировка для потокобезопасности
        self._lock = threading.Lock()
        
        logger.info("Инициализирован менеджер очереди")
        
    def _load_tasks(self) -> None:
        """
        Загрузка задач из файлов
        """
        try:
            # Очищаем задачи
            self.tasks.clear()
            
            # Загружаем задачи из файлов
            for task_file in self.queue_dir.glob("*.json"):
                try:
                    with open(task_file, "r", encoding="utf-8") as f:
                        task_data = json.load(f)
                        
                    # Создаем задачу
                    task = Task(
                        task_id=task_data["task_id"],
                        task_type=TaskType(task_data["task_type"]),
                        data=task_data["data"]
                    )
                    
                    # Устанавливаем статус
                    task.status = TaskStatus(task_data["status"])
                    
                    # Устанавливаем результат
                    task.result = task_data.get("result")
                    
                    # Устанавливаем ошибку
                    task.error = task_data.get("error")
                    
                    # Устанавливаем время
                    task.created_at = datetime.fromisoformat(task_data["created_at"])
                    task.updated_at = datetime.fromisoformat(task_data["updated_at"])
                    
                    # Добавляем задачу
                    self.tasks[task.task_id] = task
                    
                except Exception as e:
                    logger.error(f"Ошибка загрузки задачи из {task_file}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Ошибка загрузки задач: {str(e)}")
            
    def _save_task(self, task: Task) -> bool:
        """
        Сохранение задачи в файл
        
        Args:
            task: задача
            
        Returns:
            bool: успешность сохранения
        """
        try:
            # Создаем файл задачи
            task_file = self.queue_dir / f"{task.task_id}.json"
            
            # Сохраняем задачу
            with open(task_file, "w", encoding="utf-8") as f:
                json.dump({
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "data": task.data,
                    "status": task.status.value,
                    "result": task.result,
                    "error": task.error,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat()
                }, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения задачи {task.task_id}: {str(e)}")
            return False
            
    def add_task(self, task_type: TaskType, data: Dict[str, Any]) -> Optional[str]:
        """
        Добавление задачи
        
        Args:
            task_type: тип задачи
            data: данные задачи
            
        Returns:
            Optional[str]: идентификатор задачи
        """
        try:
            with self._lock:
                # Создаем идентификатор задачи
                task_id = f"{task_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Создаем задачу
                task = Task(task_id, task_type, data)
                
                # Добавляем задачу
                self.tasks[task_id] = task
                
                # Сохраняем задачу
                if not self._save_task(task):
                    del self.tasks[task_id]
                    return None
                    
                return task_id
                
        except Exception as e:
            logger.error(f"Ошибка добавления задачи: {str(e)}")
            return None
            
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Получение задачи
        
        Args:
            task_id: идентификатор задачи
            
        Returns:
            Optional[Task]: задача
        """
        try:
            return self.tasks.get(task_id)
            
        except Exception as e:
            logger.error(f"Ошибка получения задачи {task_id}: {str(e)}")
            return None
            
    def update_task(self, task_id: str, status: TaskStatus, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> bool:
        """
        Обновление задачи
        
        Args:
            task_id: идентификатор задачи
            status: статус задачи
            result: результат задачи
            error: ошибка задачи
            
        Returns:
            bool: успешность обновления
        """
        try:
            with self._lock:
                # Получаем задачу
                task = self.get_task(task_id)
                if task is None:
                    return False
                    
                # Обновляем задачу
                task.status = status
                task.result = result
                task.error = error
                task.updated_at = datetime.now()
                
                # Сохраняем задачу
                return self._save_task(task)
                
        except Exception as e:
            logger.error(f"Ошибка обновления задачи {task_id}: {str(e)}")
            return False
            
    def delete_task(self, task_id: str) -> bool:
        """
        Удаление задачи
        
        Args:
            task_id: идентификатор задачи
            
        Returns:
            bool: успешность удаления
        """
        try:
            with self._lock:
                # Получаем задачу
                task = self.get_task(task_id)
                if task is None:
                    return False
                    
                # Удаляем файл задачи
                task_file = self.queue_dir / f"{task_id}.json"
                if task_file.exists():
                    task_file.unlink()
                    
                # Удаляем задачу
                del self.tasks[task_id]
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка удаления задачи {task_id}: {str(e)}")
            return False
            
    def clear_tasks(self) -> bool:
        """
        Очистка задач
        
        Returns:
            bool: успешность очистки
        """
        try:
            with self._lock:
                # Удаляем файлы задач
                for task_file in self.queue_dir.glob("*.json"):
                    task_file.unlink()
                    
                # Очищаем задачи
                self.tasks.clear()
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка очистки задач: {str(e)}")
            return False
            
    def get_tasks(self, task_type: Optional[TaskType] = None, status: Optional[TaskStatus] = None) -> List[Task]:
        """
        Получение списка задач
        
        Args:
            task_type: тип задачи
            status: статус задачи
            
        Returns:
            List[Task]: список задач
        """
        try:
            # Фильтруем задачи
            tasks = list(self.tasks.values())
            
            if task_type is not None:
                tasks = [task for task in tasks if task.task_type == task_type]
                
            if status is not None:
                tasks = [task for task in tasks if task.status == status]
                
            return tasks
            
        except Exception as e:
            logger.error(f"Ошибка получения списка задач: {str(e)}")
            return []
            
    def get_task_stats(self) -> Dict[str, int]:
        """
        Получение статистики задач
        
        Returns:
            Dict[str, int]: статистика задач
        """
        try:
            # Создаем статистику
            stats = {
                "total": len(self.tasks),
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0
            }
            
            # Считаем статистику
            for task in self.tasks.values():
                stats[task.status.value] += 1
                
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики задач: {str(e)}")
            return {
                "total": 0,
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0
            } 