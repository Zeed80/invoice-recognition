import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import json
import time
from dataclasses import dataclass, asdict

logger = logging.getLogger("Log")

@dataclass
class LogEntry:
    id: str
    level: str
    message: str
    timestamp: float
    module: str
    function: str
    line: int
    metadata: Optional[Dict[str, Any]] = None

class Log:
    def __init__(self, log_dir: Union[str, Path] = "data/logs"):
        """
        Инициализация менеджера логов
        
        Args:
            log_dir: директория для хранения логов
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logs: Dict[str, List[LogEntry]] = {}
        
        # Загружаем логи
        self._load_logs()
        
        logger.info("Инициализирован менеджер логов")
        
    def _load_logs(self) -> None:
        """
        Загрузка логов из файлов
        """
        try:
            # Загружаем логи из файлов
            for log_file in self.log_dir.glob("*.json"):
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                    # Создаем логи
                    module = log_file.stem
                    self.logs[module] = []
                    
                    # Загружаем записи
                    for entry_data in data:
                        entry = LogEntry(
                            id=entry_data["id"],
                            level=entry_data["level"],
                            message=entry_data["message"],
                            timestamp=entry_data["timestamp"],
                            module=entry_data["module"],
                            function=entry_data["function"],
                            line=entry_data["line"],
                            metadata=entry_data.get("metadata")
                        )
                        self.logs[module].append(entry)
                        
                except Exception as e:
                    logger.error(f"Ошибка загрузки логов {log_file}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Ошибка загрузки логов: {str(e)}")
            
    def _save_log(self, module: str) -> bool:
        """
        Сохранение логов в файл
        
        Args:
            module: название модуля
            
        Returns:
            bool: успешность сохранения
        """
        try:
            # Создаем файл
            log_file = self.log_dir / f"{module}.json"
            
            # Сохраняем данные
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump([asdict(entry) for entry in self.logs[module]], f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения логов {module}: {str(e)}")
            return False
            
    def add_log(self, level: str, message: str, module: str, function: str, line: int, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Добавление записи в лог
        
        Args:
            level: уровень логирования
            message: сообщение
            module: название модуля
            function: название функции
            line: номер строки
            metadata: метаданные
            
        Returns:
            bool: успешность добавления
        """
        try:
            # Создаем запись
            entry = LogEntry(
                id=str(int(time.time() * 1000)),
                level=level,
                message=message,
                timestamp=time.time(),
                module=module,
                function=function,
                line=line,
                metadata=metadata
            )
            
            # Добавляем запись
            if module not in self.logs:
                self.logs[module] = []
                
            self.logs[module].append(entry)
            
            # Сохраняем логи
            return self._save_log(module)
            
        except Exception as e:
            logger.error(f"Ошибка добавления записи в лог: {str(e)}")
            return False
            
    def get_logs(self, module: Optional[str] = None, level: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[LogEntry]:
        """
        Получение записей лога
        
        Args:
            module: название модуля
            level: уровень логирования
            start_time: начальное время
            end_time: конечное время
            
        Returns:
            List[LogEntry]: записи лога
        """
        try:
            # Получаем записи
            entries = []
            
            if module is not None:
                if module not in self.logs:
                    return []
                    
                entries = self.logs[module]
            else:
                for module_logs in self.logs.values():
                    entries.extend(module_logs)
                    
            # Фильтруем записи
            if level is not None:
                entries = [entry for entry in entries if entry.level == level]
                
            if start_time is not None:
                entries = [entry for entry in entries if entry.timestamp >= start_time]
                
            if end_time is not None:
                entries = [entry for entry in entries if entry.timestamp <= end_time]
                
            return entries
            
        except Exception as e:
            logger.error(f"Ошибка получения записей лога: {str(e)}")
            return []
            
    def clear_logs(self, module: Optional[str] = None, before_time: Optional[float] = None) -> bool:
        """
        Очистка логов
        
        Args:
            module: название модуля
            before_time: удалить записи до этого времени
            
        Returns:
            bool: успешность очистки
        """
        try:
            if module is not None:
                if module not in self.logs:
                    return True
                    
                if before_time is not None:
                    self.logs[module] = [entry for entry in self.logs[module] if entry.timestamp >= before_time]
                else:
                    self.logs[module] = []
                    
                return self._save_log(module)
                
            for module in list(self.logs.keys()):
                if before_time is not None:
                    self.logs[module] = [entry for entry in self.logs[module] if entry.timestamp >= before_time]
                else:
                    self.logs[module] = []
                    
                self._save_log(module)
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка очистки логов: {str(e)}")
            return False
            
    def get_log_stats(self) -> Dict[str, int]:
        """
        Получение статистики логов
        
        Returns:
            Dict[str, int]: статистика
        """
        try:
            stats = {
                "total": sum(len(logs) for logs in self.logs.values()),
                "modules": {},
                "levels": {}
            }
            
            # Считаем количество записей по модулям и уровням
            for module, logs in self.logs.items():
                stats["modules"][module] = len(logs)
                
                for entry in logs:
                    if entry.level not in stats["levels"]:
                        stats["levels"][entry.level] = 0
                        
                    stats["levels"][entry.level] += 1
                    
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики логов: {str(e)}")
            return {} 