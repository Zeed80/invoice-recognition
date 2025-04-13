#!/usr/bin/env python
import sys
import os
import platform
import psutil
import torch
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_system():
    """Проверка системных требований"""
    results = {
        "system": {},
        "python": {},
        "hardware": {},
        "dependencies": {},
        "directories": {},
        "models": {}
    }
    
    # Проверка системы
    results["system"] = {
        "os": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor()
    }
    
    # Проверка Python
    results["python"] = {
        "version": sys.version.split()[0],
        "path": sys.executable,
        "pip": os.popen("pip --version").read().strip()
    }
    
    # Проверка оборудования
    results["hardware"] = {
        "cpu_cores": psutil.cpu_count(),
        "cpu_freq": psutil.cpu_freq().max if psutil.cpu_freq() else "Unknown",
        "memory_total": psutil.virtual_memory().total / (1024 ** 3),
        "memory_available": psutil.virtual_memory().available / (1024 ** 3),
        "disk_total": psutil.disk_usage('/').total / (1024 ** 3),
        "disk_free": psutil.disk_usage('/').free / (1024 ** 3)
    }
    
    # Проверка CUDA
    if torch.cuda.is_available():
        results["hardware"].update({
            "gpu": torch.cuda.get_device_name(0),
            "cuda_version": torch.version.cuda,
            "gpu_memory": torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        })
    
    # Проверка зависимостей
    required_packages = [
        "torch", "torchvision", "easyocr", "opencv-python",
        "numpy", "PySide6", "fastapi", "pika", "pandas"
    ]
    results["dependencies"] = {
        pkg: os.popen(f"pip show {pkg}").read().strip() 
        for pkg in required_packages
    }
    
    # Проверка директорий
    required_dirs = [
        "data/input", "data/output", "data/temp", "data/backup",
        "logs", "models", "config"
    ]
    results["directories"] = {
        dir_: os.path.exists(dir_) for dir_ in required_dirs
    }
    
    # Проверка моделей
    model_files = [
        "models/yolov5s.pt"
    ]
    results["models"] = {
        model: os.path.exists(model) for model in model_files
    }
    
    return results

def print_results(results):
    """Вывод результатов проверки"""
    logger.info("\n=== Отчет о проверке системы ===\n")
    
    # Система
    logger.info("Система:")
    logger.info(f"  ОС: {results['system']['os']} {results['system']['release']}")
    logger.info(f"  Версия: {results['system']['version']}")
    logger.info(f"  Архитектура: {results['system']['architecture']}")
    
    # Python
    logger.info("\nPython:")
    logger.info(f"  Версия: {results['python']['version']}")
    logger.info(f"  Путь: {results['python']['path']}")
    
    # Оборудование
    logger.info("\nОборудование:")
    logger.info(f"  Процессор: {results['hardware']['processor']}")
    logger.info(f"  Ядра: {results['hardware']['cpu_cores']}")
    logger.info(f"  Частота: {results['hardware']['cpu_freq']} MHz")
    logger.info(f"  Память: {results['hardware']['memory_total']:.1f} GB")
    logger.info(f"  Свободно: {results['hardware']['memory_available']:.1f} GB")
    
    if "gpu" in results["hardware"]:
        logger.info(f"\nGPU:")
        logger.info(f"  Модель: {results['hardware']['gpu']}")
        logger.info(f"  CUDA: {results['hardware']['cuda_version']}")
        logger.info(f"  Память: {results['hardware']['gpu_memory']:.1f} GB")
    
    # Директории
    logger.info("\nДиректории:")
    for dir_, exists in results["directories"].items():
        status = "✓" if exists else "✗"
        logger.info(f"  {status} {dir_}")
    
    # Модели
    logger.info("\nМодели:")
    for model, exists in results["models"].items():
        status = "✓" if exists else "✗"
        logger.info(f"  {status} {model}")
    
    # Проверка минимальных требований
    logger.info("\nПроверка требований:")
    checks = []
    
    # CPU
    checks.append(("CPU cores >= 4", results["hardware"]["cpu_cores"] >= 4))
    checks.append(("RAM >= 8GB", results["hardware"]["memory_total"] >= 8))
    checks.append(("Free disk >= 10GB", results["hardware"]["disk_free"] >= 10))
    
    # Вывод результатов проверки
    for check, passed in checks:
        status = "✓" if passed else "✗"
        logger.info(f"  {status} {check}")

def main():
    """Основная функция"""
    try:
        results = check_system()
        print_results(results)
        
        # Сохраняем результаты в файл
        output_file = "logs/system_check.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\nРезультаты сохранены в {output_file}")
        
    except Exception as e:
        logger.error(f"Ошибка при проверке системы: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 