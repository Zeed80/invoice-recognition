#!/usr/bin/env python
import os
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def cleanup_temp_files(temp_dir: str = "data/temp", max_age_days: int = 7):
    """Очистка временных файлов старше max_age_days"""
    temp_path = Path(temp_dir)
    if not temp_path.exists():
        logger.warning(f"Директория {temp_dir} не существует")
        return
    
    now = datetime.now()
    count = 0
    size = 0
    
    for item in temp_path.glob("**/*"):
        if item.is_file():
            mtime = datetime.fromtimestamp(item.stat().st_mtime)
            if now - mtime > timedelta(days=max_age_days):
                size += item.stat().st_size
                item.unlink()
                count += 1
                logger.debug(f"Удален файл: {item}")
    
    logger.info(f"Удалено {count} файлов (всего {size / 1024 / 1024:.1f} MB)")

def cleanup_logs(log_dir: str = "logs", max_age_days: int = 30):
    """Очистка старых лог-файлов"""
    log_path = Path(log_dir)
    if not log_path.exists():
        logger.warning(f"Директория {log_dir} не существует")
        return
    
    now = datetime.now()
    count = 0
    size = 0
    
    for item in log_path.glob("*.log*"):
        if item.is_file():
            mtime = datetime.fromtimestamp(item.stat().st_mtime)
            if now - mtime > timedelta(days=max_age_days):
                size += item.stat().st_size
                item.unlink()
                count += 1
                logger.debug(f"Удален лог: {item}")
    
    logger.info(f"Удалено {count} лог-файлов (всего {size / 1024 / 1024:.1f} MB)")

def cleanup_backups(backup_dir: str = "data/backup", keep_last: int = 5):
    """Оставляет только последние keep_last резервных копий"""
    backup_path = Path(backup_dir)
    if not backup_path.exists():
        logger.warning(f"Директория {backup_dir} не существует")
        return
    
    # Получаем список бэкапов, сортированных по времени создания
    backups = [(f, f.stat().st_mtime) for f in backup_path.glob("*.zip")]
    backups.sort(key=lambda x: x[1], reverse=True)
    
    # Удаляем старые бэкапы
    if len(backups) > keep_last:
        count = 0
        size = 0
        for f, _ in backups[keep_last:]:
            size += f.stat().st_size
            f.unlink()
            count += 1
            logger.debug(f"Удален бэкап: {f}")
        
        logger.info(f"Удалено {count} бэкапов (всего {size / 1024 / 1024:.1f} MB)")

def main():
    """Основная функция"""
    try:
        logger.info("Начало очистки...")
        
        cleanup_temp_files()
        cleanup_logs()
        cleanup_backups()
        
        # Очищаем кэш Python
        cache_dirs = ["__pycache__", ".pytest_cache", ".mypy_cache"]
        count = 0
        size = 0
        
        for cache_dir in cache_dirs:
            for root, dirs, files in os.walk("."):
                if cache_dir in dirs:
                    cache_path = Path(root) / cache_dir
                    cache_size = sum(f.stat().st_size for f in cache_path.glob("**/*") if f.is_file())
                    shutil.rmtree(cache_path)
                    count += 1
                    size += cache_size
                    logger.debug(f"Удален кэш: {cache_path}")
        
        logger.info(f"Удалено {count} кэш-директорий (всего {size / 1024 / 1024:.1f} MB)")
        logger.info("Очистка завершена")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке: {e}")

if __name__ == "__main__":
    main() 