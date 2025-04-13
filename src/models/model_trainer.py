import torch
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import shutil
from datetime import datetime
import json
import numpy as np
from sklearn.model_selection import train_test_split

logger = logging.getLogger("ModelTrainer")

class ModelTrainer:
    def __init__(self,
                 model_dir: Union[str, Path] = "models",
                 data_dir: Union[str, Path] = "data",
                 config_path: Optional[Union[str, Path]] = None):
        """
        Инициализация тренера модели
        
        Args:
            model_dir: директория для сохранения моделей
            data_dir: директория с данными
            config_path: путь к конфигурационному файлу
        """
        self.model_dir = Path(model_dir)
        self.data_dir = Path(data_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Загружаем конфигурацию
        if config_path:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {
                'model': {
                    'name': 'yolov5',
                    'version': 'latest',
                    'weights': 'yolov5s.pt'
                },
                'training': {
                    'epochs': 100,
                    'batch_size': 16,
                    'img_size': 640,
                    'device': 'cuda' if torch.cuda.is_available() else 'cpu'
                },
                'data': {
                    'train_ratio': 0.8,
                    'val_ratio': 0.1,
                    'test_ratio': 0.1
                }
            }
            
        logger.info(f"Инициализирован тренер модели: {model_dir}")
        
    def prepare_data(self,
                    data_path: Union[str, Path],
                    output_dir: Optional[Union[str, Path]] = None) -> Tuple[Path, Path, Path]:
        """
        Подготовка данных для обучения
        
        Args:
            data_path: путь к данным
            output_dir: директория для сохранения подготовленных данных
            
        Returns:
            Tuple[Path, Path, Path]: пути к train, val и test наборам
        """
        try:
            # Определяем выходную директорию
            if not output_dir:
                output_dir = self.data_dir / f"prepared_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            else:
                output_dir = Path(output_dir)
                
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Создаем поддиректории
            train_dir = output_dir / "train"
            val_dir = output_dir / "val"
            test_dir = output_dir / "test"
            
            for dir_path in [train_dir, val_dir, test_dir]:
                dir_path.mkdir(exist_ok=True)
                
            # Разделяем данные
            data_files = list(Path(data_path).glob("*.jpg"))
            train_files, test_files = train_test_split(
                data_files,
                test_size=self.config['data']['test_ratio'],
                random_state=42
            )
            
            train_files, val_files = train_test_split(
                train_files,
                test_size=self.config['data']['val_ratio'] / (1 - self.config['data']['test_ratio']),
                random_state=42
            )
            
            # Копируем файлы
            for files, target_dir in [
                (train_files, train_dir),
                (val_files, val_dir),
                (test_files, test_dir)
            ]:
                for file in files:
                    shutil.copy2(file, target_dir / file.name)
                    
            logger.info(f"Данные подготовлены: {output_dir}")
            
            return train_dir, val_dir, test_dir
            
        except Exception as e:
            logger.error(f"Ошибка подготовки данных: {str(e)}")
            raise
            
    def train(self,
              train_data: Union[str, Path],
              val_data: Union[str, Path],
              model_path: Optional[Union[str, Path]] = None,
              **kwargs) -> Path:
        """
        Обучение модели
        
        Args:
            train_data: путь к тренировочным данным
            val_data: путь к валидационным данным
            model_path: путь к предобученной модели
            **kwargs: дополнительные параметры обучения
            
        Returns:
            Path: путь к обученной модели
        """
        try:
            # Обновляем конфигурацию
            config = self.config.copy()
            config.update(kwargs)
            
            # Определяем путь для сохранения модели
            if not model_path:
                model_path = self.model_dir / f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pt"
            else:
                model_path = Path(model_path)
                
            # Загружаем модель
            if model_path.exists():
                model = torch.load(model_path)
                logger.info(f"Загружена модель: {model_path}")
            else:
                model = self._create_model()
                logger.info("Создана новая модель")
                
            # Обучаем модель
            model.train(
                data=train_data,
                val_data=val_data,
                epochs=config['training']['epochs'],
                batch_size=config['training']['batch_size'],
                img_size=config['training']['img_size'],
                device=config['training']['device']
            )
            
            # Сохраняем модель
            torch.save(model, model_path)
            logger.info(f"Модель сохранена: {model_path}")
            
            return model_path
            
        except Exception as e:
            logger.error(f"Ошибка обучения модели: {str(e)}")
            raise
            
    def evaluate(self,
                model_path: Union[str, Path],
                test_data: Union[str, Path]) -> Dict:
        """
        Оценка модели
        
        Args:
            model_path: путь к модели
            test_data: путь к тестовым данным
            
        Returns:
            Dict: метрики оценки
        """
        try:
            # Загружаем модель
            model = torch.load(model_path)
            
            # Оцениваем модель
            metrics = model.evaluate(
                data=test_data,
                batch_size=self.config['training']['batch_size'],
                img_size=self.config['training']['img_size'],
                device=self.config['training']['device']
            )
            
            logger.info(f"Модель оценена: {metrics}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Ошибка оценки модели: {str(e)}")
            raise
            
    def _create_model(self):
        """
        Создание новой модели
        
        Returns:
            Model: модель
        """
        try:
            # Создаем модель
            if self.config['model']['name'] == 'yolov5':
                from yolov5 import YOLOv5
                model = YOLOv5(
                    version=self.config['model']['version'],
                    weights=self.config['model']['weights']
                )
            else:
                raise ValueError(f"Неподдерживаемая модель: {self.config['model']['name']}")
                
            return model
            
        except Exception as e:
            logger.error(f"Ошибка создания модели: {str(e)}")
            raise 