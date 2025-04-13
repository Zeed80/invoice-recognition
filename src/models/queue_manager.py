import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import json
import os
from datetime import datetime
import threading
import shutil
import time
from enum import Enum
from dataclasses import dataclass, asdict

logger = logging.getLogger("QueueManager")

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    id: str
    type: str
    data: Dict[str, Any]
    status: TaskStatus
    created_at: float
    updated_at: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class QueueManager:
    def __init__(self, queue_dir: Union[str, Path] = "data/queue",
                 max_size: int = 1000,
                 max_retries: int = 3):
        """
        Инициализация менеджера очереди
        
        Args:
            queue_dir: директория для хранения очереди
            max_size: максимальный размер очереди
            max_retries: максимальное количество попыток
        """
        self.queue_dir = Path(queue_dir)
        self.max_size = max_size
        self.max_retries = max_retries
        
        # Создаем директории
        self.pending_dir = self.queue_dir / "pending"
        self.processing_dir = self.queue_dir / "processing"
        self.completed_dir = self.queue_dir / "completed"
        self.failed_dir = self.queue_dir / "failed"
        
        for dir_path in [self.pending_dir, self.processing_dir,
                        self.completed_dir, self.failed_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # Инициализируем очередь и статистику
        self.queue: List[Task] = []
        self.stats = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "retries": 0
        }
        
        self.lock = threading.Lock()
        
        # Загружаем состояние
        self._load_state()
        
        logger.info("Инициализирован менеджер очереди")
        
    def _load_state(self) -> None:
        """
        Загрузка состояния очереди
        """
        try:
            # Загружаем задачи
            self.tasks: Dict[str, Task] = {}
            for task_file in self.queue_dir.glob("*.json"):
                try:
                    with open(task_file, "r", encoding="utf-8") as f:
                        task_data = json.load(f)
                        
                        # Создаем объект задачи
                        task = Task(
                            id=task_data["id"],
                            type=task_data["type"],
                            data=task_data["data"],
                            status=TaskStatus(task_data["status"]),
                            created_at=task_data["created_at"],
                            updated_at=task_data["updated_at"],
                            result=task_data.get("result"),
                            error=task_data.get("error")
                        )
                        
                        self.tasks[task.id] = task
                        
                except Exception as e:
                    logger.error(f"Ошибка загрузки задачи {task_file}: {str(e)}")
                    
            # Загружаем статистику
            stats_file = self.queue_dir / "stats.json"
            if stats_file.exists():
                with open(stats_file, "r", encoding="utf-8") as f:
                    self.stats = json.load(f)
                    
        except Exception as e:
            logger.error(f"Ошибка загрузки состояния: {str(e)}")
            
    def _save_state(self) -> None:
        """
        Сохранение состояния очереди
        """
        try:
            # Сохраняем задачи
            for task in self.tasks.values():
                self._save_task(task)
                
            # Сохраняем статистику
            stats_file = self.queue_dir / "stats.json"
            with open(stats_file, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Ошибка сохранения состояния: {str(e)}")
            
    def _save_task(self, task: Task) -> None:
        """
        Сохранение задачи в файл
        
        Args:
            task: задача
        """
        try:
            task_file = self.queue_dir / f"{task.id}.json"
            
            with open(task_file, "w", encoding="utf-8") as f:
                json.dump(asdict(task), f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Ошибка сохранения задачи {task.id}: {str(e)}")
            
    def add_task(self, task_type: str, data: Dict[str, Any]) -> Optional[str]:
        """
        Добавление задачи
        
        Args:
            task_type: тип задачи
            data: данные задачи
            
        Returns:
            Optional[str]: ID задачи
        """
        try:
            with self.lock:
                # Проверяем размер очереди
                if len(self.queue) >= self.max_size:
                    logger.warning("Очередь переполнена")
                    return None
                    
                # Генерируем ID
                task_id = f"{task_type}_{int(time.time())}_{len(self.tasks)}"
                
                # Создаем задачу
                task = Task(
                    id=task_id,
                    type=task_type,
                    data=data,
                    status=TaskStatus.PENDING,
                    created_at=time.time(),
                    updated_at=time.time()
                )
                
                # Сохраняем задачу
                self.tasks[task_id] = task
                self._save_task(task)
                
                # Добавляем в очередь
                self.queue.append(task)
                self.stats["total"] += 1
                
                # Сохраняем состояние
                self._save_state()
                
                logger.info(f"Добавлена задача {task_id}")
                return task_id
                
        except Exception as e:
            logger.error(f"Ошибка добавления задачи: {str(e)}")
            return None
            
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Получение задачи
        
        Args:
            task_id: ID задачи
            
        Returns:
            Optional[Task]: задача
        """
        try:
            return self.tasks.get(task_id)
        except Exception as e:
            logger.error(f"Ошибка получения задачи {task_id}: {str(e)}")
            return None
            
    def complete_task(self, task_id: str, result: Dict) -> bool:
        """
        Завершение задачи
        
        Args:
            task_id: идентификатор задачи
            result: результат выполнения
            
        Returns:
            bool: успешность завершения
        """
        try:
            with self.lock:
                # Ищем задачу
                task = self.tasks.get(task_id)
                
                if task is None:
                    logger.error(f"Задача {task_id} не найдена")
                    return False
                    
                # Обновляем задачу
                task.status = TaskStatus.COMPLETED
                task.updated_at = time.time()
                task.result = result
                
                # Перемещаем файл
                src = self.processing_dir / f"{task_id}.json"
                dst = self.completed_dir / f"{task_id}.json"
                shutil.move(str(src), str(dst))
                
                # Обновляем статистику
                self.stats["completed"] += 1
                
                # Сохраняем состояние
                self._save_state()
                
                logger.info(f"Завершена задача {task_id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка завершения задачи: {str(e)}")
            return False
            
    def fail_task(self, task_id: str, error: str) -> bool:
        """
        Отметка о неудачном выполнении задачи
        
        Args:
            task_id: идентификатор задачи
            error: описание ошибки
            
        Returns:
            bool: успешность отметки
        """
        try:
            with self.lock:
                # Ищем задачу
                task = self.tasks.get(task_id)
                
                if task is None:
                    logger.error(f"Задача {task_id} не найдена")
                    return False
                    
                # Увеличиваем счетчик попыток
                task.retries = task.retries + 1 if task.retries else 1
                task.error = error
                
                if task.retries >= self.max_retries:
                    # Превышено максимальное количество попыток
                    task.status = TaskStatus.FAILED
                    task.updated_at = time.time()
                    
                    # Перемещаем файл
                    src = self.processing_dir / f"{task_id}.json"
                    dst = self.failed_dir / f"{task_id}.json"
                    shutil.move(str(src), str(dst))
                    
                    # Обновляем статистику
                    self.stats["failed"] += 1
                    
                else:
                    # Возвращаем в очередь
                    task.status = TaskStatus.PENDING
                    
                    # Перемещаем файл
                    src = self.processing_dir / f"{task_id}.json"
                    dst = self.pending_dir / f"{task_id}.json"
                    shutil.move(str(src), str(dst))
                    
                    # Обновляем статистику
                    self.stats["retries"] += 1
                    
                # Сохраняем состояние
                self._save_state()
                
                logger.info(f"Отмечена ошибка в задаче {task_id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка отметки ошибки: {str(e)}")
            return False
            
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        Получение статуса задачи
        
        Args:
            task_id: идентификатор задачи
            
        Returns:
            Optional[Dict]: статус задачи
        """
        try:
            with self.lock:
                # Ищем задачу
                task = self.tasks.get(task_id)
                
                if task is None:
                    return None
                    
                return {
                    "id": task.id,
                    "status": task.status.value,
                    "retries": task.retries,
                    "created_at": task.created_at,
                    "started_at": task.updated_at,
                    "completed_at": task.updated_at,
                    "failed_at": task.updated_at,
                    "last_error": task.error,
                    "result": task.result
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {str(e)}")
            return None
            
    def get_queue_stats(self) -> Dict:
        """
        Получение статистики очереди
        
        Returns:
            Dict: статистика
        """
        try:
            with self.lock:
                # Считаем задачи по статусам
                status_stats = {
                    "pending": 0,
                    "processing": 0,
                    "completed": 0,
                    "failed": 0
                }
                
                for task in self.queue:
                    status_stats[task.status.value] += 1
                    
                return {
                    "total": self.stats["total"],
                    "completed": self.stats["completed"],
                    "failed": self.stats["failed"],
                    "retries": self.stats["retries"],
                    "status": status_stats
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {str(e)}")
            return {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "retries": 0,
                "status": {
                    "pending": 0,
                    "processing": 0,
                    "completed": 0,
                    "failed": 0
                }
            }
            
    def clear_queue(self) -> bool:
        """
        Очистка очереди
        
        Returns:
            bool: успешность очистки
        """
        try:
            with self.lock:
                # Очищаем директории
                for dir_path in [self.pending_dir, self.processing_dir,
                               self.completed_dir, self.failed_dir]:
                    for file in dir_path.glob("*.json"):
                        file.unlink()
                        
                # Очищаем очередь и статистику
                self.queue = []
                self.stats = {
                    "total": 0,
                    "completed": 0,
                    "failed": 0,
                    "retries": 0
                }
                
                # Сохраняем состояние
                self._save_state()
                
                logger.info("Очередь очищена")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка очистки очереди: {str(e)}")
            return False
            
    def get_pending_tasks(self, task_type: Optional[str] = None) -> List[Task]:
        """
        Получение ожидающих задач
        
        Args:
            task_type: тип задачи
            
        Returns:
            List[Task]: список задач
        """
        try:
            tasks = []
            
            for task in self.tasks.values():
                if task.status == TaskStatus.PENDING:
                    if task_type is None or task.type == task_type:
                        tasks.append(task)
                        
            return tasks
            
        except Exception as e:
            logger.error(f"Ошибка получения ожидающих задач: {str(e)}")
            return []
            
    def update_task(self, task_id: str, status: TaskStatus, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> bool:
        """
        Обновление задачи
        
        Args:
            task_id: ID задачи
            status: статус
            result: результат
            error: ошибка
            
        Returns:
            bool: успешность обновления
        """
        try:
            with self.lock:
                task = self.tasks.get(task_id)
                
                if task is None:
                    logger.error(f"Задача {task_id} не найдена")
                    return False
                    
                # Обновляем задачу
                task.status = status
                task.updated_at = time.time()
                task.result = result
                task.error = error
                
                # Сохраняем задачу
                self._save_task(task)
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка обновления задачи {task_id}: {str(e)}")
            return False
            
    def remove_task(self, task_id: str) -> bool:
        """
        Удаление задачи
        
        Args:
            task_id: ID задачи
            
        Returns:
            bool: успешность удаления
        """
        try:
            with self.lock:
                task = self.tasks.get(task_id)
                
                if task is None:
                    logger.error(f"Задача {task_id} не найдена")
                    return False
                    
                # Удаляем файл
                task_file = self.queue_dir / f"{task_id}.json"
                if task_file.exists():
                    task_file.unlink()
                    
                # Удаляем задачу
                del self.tasks[task_id]
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка удаления задачи {task_id}: {str(e)}")
            return False
            
    def cleanup_tasks(self, max_age: float = 86400) -> int:
        """
        Очистка старых задач
        
        Args:
            max_age: максимальный возраст в секундах
            
        Returns:
            int: количество удаленных задач
        """
        try:
            count = 0
            current_time = time.time()
            
            with self.lock:
                # Получаем список задач для удаления
                tasks_to_remove = []
                
                for task_id, task in self.tasks.items():
                    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                        if current_time - task.updated_at > max_age:
                            tasks_to_remove.append(task_id)
                            
                # Удаляем задачи
                for task_id in tasks_to_remove:
                    if self.remove_task(task_id):
                        count += 1
                        
                return count
                
        except Exception as e:
            logger.error(f"Ошибка очистки задач: {str(e)}")
            return 0
            
    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики
        
        Returns:
            Dict[str, Any]: статистика
        """
        try:
            stats = {
                "total": len(self.tasks),
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0,
                "by_type": {}
            }
            
            # Считаем статистику
            for task in self.tasks.values():
                stats[task.status.value] += 1
                
                if task.type not in stats["by_type"]:
                    stats["by_type"][task.type] = {
                        "total": 0,
                        "pending": 0,
                        "processing": 0,
                        "completed": 0,
                        "failed": 0
                    }
                    
                stats["by_type"][task.type]["total"] += 1
                stats["by_type"][task.type][task.status.value] += 1
                
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {str(e)}")
            return {} 