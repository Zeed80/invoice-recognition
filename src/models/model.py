import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import json
import time
from dataclasses import dataclass, asdict

logger = logging.getLogger("Model")

@dataclass
class ModelInfo:
    name: str
    type: str
    path: str
    version: str
    created_at: float
    updated_at: float
    params: Dict[str, Any]
    metrics: Dict[str, float]

class Model:
    def __init__(self, models_dir: Union[str, Path] = "data/models"):
        """
        Инициализация менеджера моделей
        
        Args:
            models_dir: директория для хранения моделей
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.models: Dict[str, ModelInfo] = {}
        
        # Загружаем модели
        self._load_models()
        
        logger.info("Инициализирован менеджер моделей")
        
    def _load_models(self) -> None:
        """
        Загрузка моделей из файлов
        """
        try:
            # Загружаем модели из файлов
            for model_file in self.models_dir.glob("*.json"):
                try:
                    with open(model_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                    # Создаем модель
                    model = ModelInfo(
                        name=data["name"],
                        type=data["type"],
                        path=data["path"],
                        version=data["version"],
                        created_at=data["created_at"],
                        updated_at=data["updated_at"],
                        params=data["params"],
                        metrics=data["metrics"]
                    )
                    
                    # Добавляем модель
                    self.models[model.name] = model
                    
                except Exception as e:
                    logger.error(f"Ошибка загрузки модели {model_file}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Ошибка загрузки моделей: {str(e)}")
            
    def _save_model(self, name: str) -> bool:
        """
        Сохранение модели в файл
        
        Args:
            name: название модели
            
        Returns:
            bool: успешность сохранения
        """
        try:
            # Создаем файл
            model_file = self.models_dir / f"{name}.json"
            
            # Сохраняем данные
            with open(model_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self.models[name]), f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения модели {name}: {str(e)}")
            return False
            
    def add_model(self, name: str, type: str, path: str, version: str, params: Dict[str, Any], metrics: Dict[str, float]) -> bool:
        """
        Добавление модели
        
        Args:
            name: название модели
            type: тип модели
            path: путь к файлу модели
            version: версия модели
            params: параметры модели
            metrics: метрики модели
            
        Returns:
            bool: успешность добавления
        """
        try:
            # Создаем модель
            model = ModelInfo(
                name=name,
                type=type,
                path=path,
                version=version,
                created_at=time.time(),
                updated_at=time.time(),
                params=params,
                metrics=metrics
            )
            
            # Добавляем модель
            self.models[name] = model
            
            # Сохраняем модель
            return self._save_model(name)
            
        except Exception as e:
            logger.error(f"Ошибка добавления модели {name}: {str(e)}")
            return False
            
    def get_model(self, name: str) -> Optional[ModelInfo]:
        """
        Получение модели
        
        Args:
            name: название модели
            
        Returns:
            Optional[ModelInfo]: модель
        """
        try:
            if name not in self.models:
                logger.error(f"Модель {name} не найдена")
                return None
                
            return self.models[name]
            
        except Exception as e:
            logger.error(f"Ошибка получения модели {name}: {str(e)}")
            return None
            
    def update_model(self, name: str, version: Optional[str] = None, params: Optional[Dict[str, Any]] = None, metrics: Optional[Dict[str, float]] = None) -> bool:
        """
        Обновление модели
        
        Args:
            name: название модели
            version: новая версия
            params: новые параметры
            metrics: новые метрики
            
        Returns:
            bool: успешность обновления
        """
        try:
            if name not in self.models:
                logger.error(f"Модель {name} не найдена")
                return False
                
            # Получаем модель
            model = self.models[name]
            
            # Обновляем модель
            if version is not None:
                model.version = version
                
            if params is not None:
                model.params.update(params)
                
            if metrics is not None:
                model.metrics.update(metrics)
                
            model.updated_at = time.time()
            
            # Сохраняем модель
            return self._save_model(name)
            
        except Exception as e:
            logger.error(f"Ошибка обновления модели {name}: {str(e)}")
            return False
            
    def delete_model(self, name: str) -> bool:
        """
        Удаление модели
        
        Args:
            name: название модели
            
        Returns:
            bool: успешность удаления
        """
        try:
            if name not in self.models:
                logger.error(f"Модель {name} не найдена")
                return False
                
            # Удаляем файл
            model_file = self.models_dir / f"{name}.json"
            if model_file.exists():
                model_file.unlink()
                
            # Удаляем модель
            del self.models[name]
            
            logger.info(f"Удалена модель {name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления модели {name}: {str(e)}")
            return False
            
    def get_models(self, type: Optional[str] = None) -> List[ModelInfo]:
        """
        Получение списка моделей
        
        Args:
            type: тип моделей
            
        Returns:
            List[ModelInfo]: список моделей
        """
        try:
            if type is None:
                return list(self.models.values())
                
            return [model for model in self.models.values() if model.type == type]
            
        except Exception as e:
            logger.error(f"Ошибка получения списка моделей: {str(e)}")
            return []
            
    def get_model_stats(self) -> Dict[str, int]:
        """
        Получение статистики моделей
        
        Returns:
            Dict[str, int]: статистика
        """
        try:
            stats = {
                "total": len(self.models),
                "types": {}
            }
            
            # Считаем количество моделей по типам
            for model in self.models.values():
                if model.type not in stats["types"]:
                    stats["types"][model.type] = 0
                    
                stats["types"][model.type] += 1
                
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики моделей: {str(e)}")
            return {} 