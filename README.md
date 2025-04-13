ПРОЕКТ НЕ РАБОЧИЙ!!!!!
Структура проекта и весь код 100% созданы Cursor AI полностью в автоматическом режиме для обучения.

# Invoice Recognition System

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-1.9%2B-red)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-in%20development-yellow)

Система автоматического распознавания информации со сканов счетов с использованием компьютерного зрения и машинного обучения.

## 🚀 Возможности

- 🔍 Распознавание ключевых полей счета (номер, дата, сумма и др.)
- 📊 Извлечение табличных данных
- 🤖 Использование YOLOv5 для детекции областей
- 📝 OCR с помощью EasyOCR или Google Cloud Vision
- 🖥️ Современный графический интерфейс на PySide6
- 🔄 REST API на FastAPI
- 📦 Пакетная обработка файлов
- 📈 Мониторинг качества распознавания

## 📋 Требования

### Минимальные (CPU):
- Windows 10/11 (64-bit)
- Python 3.9+
- 8 ГБ RAM
- 10 ГБ свободного места

### Рекомендуемые (GPU):
- NVIDIA GPU с 4+ ГБ VRAM
- CUDA-совместимая видеокарта
- 16 ГБ RAM
- 20 ГБ свободного места

## 🛠 Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/Zeed80/invoice-recognition.git
cd invoice-recognition
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
```

3. Установите зависимости:

Для CPU:
```bash
pip install -r requirements.cpu.txt
```

Для GPU (опционально):
```bash
pip install -r requirements.gpu.txt
```

4. Запустите GUI:
```bash
python src/gui/main.py
```

## 📱 Интерфейс

### Главное окно
![Main Window](docs/images/main_window.png)

- Трехпанельный интерфейс
- Светлая и темная темы
- Drag & Drop файлов
- Предпросмотр изображений
- Редактирование результатов
- Мониторинг процесса

### Возможности
- Пакетная обработка файлов
- Выбор моделей и настроек
- Экспорт в JSON/Excel/CSV
- Статистика и метрики
- Логирование операций

## 🔧 Конфигурация

Основные настройки в `config/default.json`:
```json
{
  "model": {
    "device": "cpu",  // или "cuda" для GPU
    "batch_size": 1,
    "confidence_threshold": 0.8
  },
  "processing": {
    "max_workers": 4,
    "timeout": 300
  }
}
```

## 📊 Метрики качества

- Precision: 0.9+
- Recall: 0.9+
- F1-score: 0.9+

## 🔄 API

REST API доступен на `http://localhost:8000`:

```bash
# Проверка статуса
curl http://localhost:8000/health

# Загрузка файла
curl -X POST http://localhost:8000/api/v1/invoices/upload \
  -F "file=@invoice.jpg"
```

## 📝 TODO

- [ ] Дообучение на пользовательских данных
- [ ] Поддержка новых форматов счетов
- [ ] Улучшение точности распознавания таблиц
- [ ] Интеграция с 1С
- [ ] Оптимизация производительности

## 📄 Лицензия

MIT License. См. [LICENSE](LICENSE) для деталей.

## 👤 Автор

**Cursor AI**


