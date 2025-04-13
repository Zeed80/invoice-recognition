ПОКА НЕ РАБОТАЕТ

# Система распознавания счетов

Система для автоматического распознавания информации со сканов счетов с использованием компьютерного зрения и машинного обучения.

## Возможности

- 🔍 Распознавание ключевых полей счета (номер, дата, сумма и др.)
- 📊 Извлечение табличных данных
- 🤖 Использование YOLOv5 для детекции областей
- 📝 OCR с помощью EasyOCR или Google Cloud Vision
- 🖥️ Удобный графический интерфейс
- 🔄 API для интеграции
- 📦 Пакетная обработка файлов
- 📈 Мониторинг качества распознавания

## Требования

### Минимальные:
- Windows 10/11 (64-bit)
- Python 3.9+
- CUDA-совместимая видеокарта (4+ ГБ VRAM)
- 8 ГБ RAM
- 10 ГБ свободного места

### Рекомендуемые:
- NVIDIA GPU с 8+ ГБ VRAM
- 16 ГБ RAM
- 20 ГБ свободного места

## Быстрый старт

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-repo/invoice-recognition.git
cd invoice-recognition
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Запустите GUI:
```bash
python src/gui/main.py
```

Подробная документация по установке и настройке доступна в [docs/deployment.md](docs/deployment.md).

## Документация

- [Руководство по развертыванию](docs/deployment.md)
- [Руководство пользователя](docs/usage.md)
- [API документация](docs/api.md)
- [Руководство разработчика](docs/development.md)

## Структура проекта

```
invoice-recognition/
├── config/              # Конфигурационные файлы
├── data/                # Данные
│   ├── input/          # Входящие файлы
│   ├── output/         # Результаты обработки
│   └── temp/           # Временные файлы
├── docs/               # Документация
├── models/             # Модели ML
├── src/                # Исходный код
│   ├── api/           # FastAPI сервер
│   ├── gui/           # PySide6 интерфейс
│   ├── models/        # Модели данных
│   └── worker/        # Обработчик очереди
└── tests/              # Тесты
```

## Технологии

- 🐍 Python 3.9+
- 🤖 YOLOv5 для детекции
- 📝 EasyOCR/Google Cloud Vision для OCR
- 🎯 PyTorch
- 🖥️ PySide6 для GUI
- 🚀 FastAPI для API
- 🐰 RabbitMQ для очередей
- 📊 Metabase для мониторинга

## Лицензия

MIT License. См. [LICENSE](LICENSE) для деталей.

