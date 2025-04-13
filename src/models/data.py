import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import json
import time
from dataclasses import dataclass, asdict

logger = logging.getLogger("Data")

@dataclass
class DataInfo:
    id: str
    type: str
    path: str
    created_at: float
    updated_at: float
    metadata: Dict[str, Any]
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class Data:
    def __init__(self, data_dir: Union[str, Path] = "data/data"):
        """
        Инициализация менеджера данных
        
        Args:
            data_dir: директория для хранения данных
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.data: Dict[str, DataInfo] = {}
        
        # Загружаем данные
        self._load_data()
        
        logger.info("Инициализирован менеджер данных")
        
    def _load_data(self) -> None:
        """
        Загрузка данных из файлов
        """
        try:
            # Загружаем данные из файлов
            for data_file in self.data_dir.glob("*.json"):
                try:
                    with open(data_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                    # Создаем данные
                    data_info = DataInfo(
                        id=data["id"],
                        type=data["type"],
                        path=data["path"],
                        created_at=data["created_at"],
                        updated_at=data["updated_at"],
                        metadata=data["metadata"],
                        status=data["status"],
                        result=data.get("result"),
                        error=data.get("error")
                    )
                    
                    # Добавляем данные
                    self.data[data_info.id] = data_info
                    
                except Exception as e:
                    logger.error(f"Ошибка загрузки данных {data_file}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Ошибка загрузки данных: {str(e)}")
            
    def _save_data(self, id: str) -> bool:
        """
        Сохранение данных в файл
        
        Args:
            id: идентификатор данных
            
        Returns:
            bool: успешность сохранения
        """
        try:
            # Создаем файл
            data_file = self.data_dir / f"{id}.json"
            
            # Сохраняем данные
            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self.data[id]), f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения данных {id}: {str(e)}")
            return False
            
    def add_data(self, type: str, path: str, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Добавление данных
        
        Args:
            type: тип данных
            path: путь к файлу данных
            metadata: метаданные
            
        Returns:
            Optional[str]: идентификатор данных
        """
        try:
            # Создаем данные
            data_info = DataInfo(
                id=str(int(time.time() * 1000)),
                type=type,
                path=path,
                created_at=time.time(),
                updated_at=time.time(),
                metadata=metadata,
                status="pending"
            )
            
            # Добавляем данные
            self.data[data_info.id] = data_info
            
            # Сохраняем данные
            if self._save_data(data_info.id):
                logger.info(f"Добавлены данные {data_info.id}")
                return data_info.id
                
            return None
            
        except Exception as e:
            logger.error(f"Ошибка добавления данных: {str(e)}")
            return None
            
    def get_data(self, id: str) -> Optional[DataInfo]:
        """
        Получение данных
        
        Args:
            id: идентификатор данных
            
        Returns:
            Optional[DataInfo]: данные
        """
        try:
            if id not in self.data:
                logger.error(f"Данные {id} не найдены")
                return None
                
            return self.data[id]
            
        except Exception as e:
            logger.error(f"Ошибка получения данных {id}: {str(e)}")
            return None
            
    def update_data(self, id: str, status: Optional[str] = None, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> bool:
        """
        Обновление данных
        
        Args:
            id: идентификатор данных
            status: новый статус
            result: результат обработки
            error: ошибка обработки
            
        Returns:
            bool: успешность обновления
        """
        try:
            if id not in self.data:
                logger.error(f"Данные {id} не найдены")
                return False
                
            # Получаем данные
            data = self.data[id]
            
            # Обновляем данные
            if status is not None:
                data.status = status
                
            if result is not None:
                data.result = result
                
            if error is not None:
                data.error = error
                
            data.updated_at = time.time()
            
            # Сохраняем данные
            return self._save_data(id)
            
        except Exception as e:
            logger.error(f"Ошибка обновления данных {id}: {str(e)}")
            return False
            
    def delete_data(self, id: str) -> bool:
        """
        Удаление данных
        
        Args:
            id: идентификатор данных
            
        Returns:
            bool: успешность удаления
        """
        try:
            if id not in self.data:
                logger.error(f"Данные {id} не найдены")
                return False
                
            # Удаляем файл
            data_file = self.data_dir / f"{id}.json"
            if data_file.exists():
                data_file.unlink()
                
            # Удаляем данные
            del self.data[id]
            
            logger.info(f"Удалены данные {id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления данных {id}: {str(e)}")
            return False
            
    def get_data_list(self, type: Optional[str] = None, status: Optional[str] = None) -> List[DataInfo]:
        """
        Получение списка данных
        
        Args:
            type: тип данных
            status: статус данных
            
        Returns:
            List[DataInfo]: список данных
        """
        try:
            # Фильтруем данные
            data_list = self.data.values()
            
            if type is not None:
                data_list = [data for data in data_list if data.type == type]
                
            if status is not None:
                data_list = [data for data in data_list if data.status == status]
                
            return list(data_list)
            
        except Exception as e:
            logger.error(f"Ошибка получения списка данных: {str(e)}")
            return []
            
    def get_data_stats(self) -> Dict[str, int]:
        """
        Получение статистики данных
        
        Returns:
            Dict[str, int]: статистика
        """
        try:
            stats = {
                "total": len(self.data),
                "types": {},
                "status": {}
            }
            
            # Считаем количество данных по типам и статусам
            for data in self.data.values():
                if data.type not in stats["types"]:
                    stats["types"][data.type] = 0
                    
                stats["types"][data.type] += 1
                
                if data.status not in stats["status"]:
                    stats["status"][data.status] = 0
                    
                stats["status"][data.status] += 1
                
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики данных: {str(e)}")
            return {} 