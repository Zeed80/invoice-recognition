import logging
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
import json
import yaml
import os
from datetime import datetime

logger = logging.getLogger("ConfigManager")

class ConfigManager:
    def __init__(self, config_dir: Union[str, Path] = "config"):
        """
        Инициализация менеджера конфигурации
        
        Args:
            config_dir: директория для хранения конфигурации
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Загружаем конфигурацию
        self.config: Dict[str, Any] = {}
        self._load_config()
        
        logger.info("Инициализирован менеджер конфигурации")
        
    def _load_config(self) -> None:
        """
        Загрузка конфигурации из файлов
        """
        try:
            # Очищаем конфигурацию
            self.config.clear()
            
            # Загружаем конфигурацию из файлов
            for config_file in self.config_dir.glob("*.json"):
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                        
                    # Добавляем конфигурацию
                    self.config[config_file.stem] = config_data
                    
                except Exception as e:
                    logger.error(f"Ошибка загрузки конфигурации из {config_file}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {str(e)}")
            
    def _save_config(self, config_name: str) -> bool:
        """
        Сохранение конфигурации в файл
        
        Args:
            config_name: название конфигурации
            
        Returns:
            bool: успешность сохранения
        """
        try:
            # Создаем файл конфигурации
            config_file = self.config_dir / f"{config_name}.json"
            
            # Сохраняем конфигурацию
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(self.config[config_name], f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации {config_name}: {str(e)}")
            return False
            
    def get_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        Получение конфигурации
        
        Args:
            config_name: название конфигурации
            
        Returns:
            Optional[Dict[str, Any]]: конфигурация
        """
        try:
            return self.config.get(config_name)
            
        except Exception as e:
            logger.error(f"Ошибка получения конфигурации {config_name}: {str(e)}")
            return None
            
    def set_config(self, config_name: str, config_data: Dict[str, Any]) -> bool:
        """
        Установка конфигурации
        
        Args:
            config_name: название конфигурации
            config_data: данные конфигурации
            
        Returns:
            bool: успешность установки
        """
        try:
            # Устанавливаем конфигурацию
            self.config[config_name] = config_data
            
            # Сохраняем конфигурацию
            return self._save_config(config_name)
            
        except Exception as e:
            logger.error(f"Ошибка установки конфигурации {config_name}: {str(e)}")
            return False
            
    def delete_config(self, config_name: str) -> bool:
        """
        Удаление конфигурации
        
        Args:
            config_name: название конфигурации
            
        Returns:
            bool: успешность удаления
        """
        try:
            # Удаляем файл конфигурации
            config_file = self.config_dir / f"{config_name}.json"
            if config_file.exists():
                config_file.unlink()
                
            # Удаляем конфигурацию
            if config_name in self.config:
                del self.config[config_name]
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления конфигурации {config_name}: {str(e)}")
            return False
            
    def get_configs(self) -> List[str]:
        """
        Получение списка конфигураций
        
        Returns:
            List[str]: список конфигураций
        """
        try:
            return list(self.config.keys())
            
        except Exception as e:
            logger.error(f"Ошибка получения списка конфигураций: {str(e)}")
            return []
            
    def get_config_value(self, config_name: str, key: str, default: Any = None) -> Any:
        """
        Получение значения конфигурации
        
        Args:
            config_name: название конфигурации
            key: ключ
            default: значение по умолчанию
            
        Returns:
            Any: значение
        """
        try:
            # Получаем конфигурацию
            config = self.get_config(config_name)
            if config is None:
                return default
                
            # Получаем значение
            return config.get(key, default)
            
        except Exception as e:
            logger.error(f"Ошибка получения значения конфигурации {config_name}.{key}: {str(e)}")
            return default
            
    def set_config_value(self, config_name: str, key: str, value: Any) -> bool:
        """
        Установка значения конфигурации
        
        Args:
            config_name: название конфигурации
            key: ключ
            value: значение
            
        Returns:
            bool: успешность установки
        """
        try:
            # Получаем конфигурацию
            config = self.get_config(config_name)
            if config is None:
                config = {}
                
            # Устанавливаем значение
            config[key] = value
            
            # Сохраняем конфигурацию
            return self.set_config(config_name, config)
            
        except Exception as e:
            logger.error(f"Ошибка установки значения конфигурации {config_name}.{key}: {str(e)}")
            return False
            
    def validate_config(self) -> bool:
        """
        Валидация конфигурации
        
        Returns:
            bool: успешность валидации
        """
        try:
            # Проверяем обязательные разделы
            required_sections = ["model", "processing", "storage"]
            for section in required_sections:
                if section not in self.config:
                    logger.error(f"Отсутствует раздел {section}")
                    return False
                    
            # Проверяем модель
            model_config = self.config["model"]
            if not Path(model_config["yolo_model_path"]).exists():
                logger.error(f"Модель YOLO не найдена: {model_config['yolo_model_path']}")
                return False
                
            if not Path(model_config["ocr_model_path"]).exists():
                logger.error(f"Модель OCR не найдена: {model_config['ocr_model_path']}")
                return False
                
            # Проверяем обработку
            processing_config = self.config["processing"]
            if processing_config["batch_size"] < 1:
                logger.error("Размер батча должен быть больше 0")
                return False
                
            if processing_config["num_workers"] < 1:
                logger.error("Количество workers должно быть больше 0")
                return False
                
            # Проверяем хранение
            storage_config = self.config["storage"]
            for dir_path in [storage_config["input_dir"], storage_config["output_dir"], storage_config["temp_dir"]]:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                
            if storage_config["max_file_size"] < 1:
                logger.error("Максимальный размер файла должен быть больше 0")
                return False
                
            if not storage_config["allowed_extensions"]:
                logger.error("Список разрешенных расширений пуст")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка валидации конфигурации: {str(e)}")
            return False 