# Руководство по развертыванию системы распознавания счетов

## Содержание
1. [Требования к системе](#требования-к-системе)
2. [Установка зависимостей](#установка-зависимостей)
3. [Настройка окружения](#настройка-окружения)
4. [Установка RabbitMQ](#установка-rabbitmq)
5. [Настройка моделей](#настройка-моделей)
6. [Запуск системы](#запуск-системы)
7. [Проверка работоспособности](#проверка-работоспособности)

## Требования к системе

### Минимальные требования:
- Windows 10/11 (64-bit)
- Процессор: Intel Core i5 или аналогичный AMD
- Оперативная память: 8 ГБ
- Видеокарта: NVIDIA с 4 ГБ VRAM (для GPU-ускорения)
- Свободное место на диске: 10 ГБ

### Рекомендуемые требования:
- Windows 10/11 (64-bit)
- Процессор: Intel Core i7 или аналогичный AMD
- Оперативная память: 16 ГБ
- Видеокарта: NVIDIA с 8 ГБ VRAM
- Свободное место на диске: 20 ГБ

## Установка зависимостей

1. Установите Python 3.9 или выше:
   - Скачайте установщик с [python.org](https://www.python.org/downloads/)
   - При установке отметьте галочку "Add Python to PATH"

2. Установите CUDA Toolkit (для GPU-ускорения):
   - Скачайте и установите [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
   - Выберите версию, совместимую с вашей видеокартой

3. Установите Git:
   - Скачайте и установите [Git для Windows](https://git-scm.com/download/win)

4. Клонируйте репозиторий:
```bash
git clone https://github.com/your-repo/invoice-recognition.git
cd invoice-recognition
```

5. Создайте виртуальное окружение:
```bash
python -m venv venv
venv\Scripts\activate
```

6. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Настройка окружения

1. Создайте необходимые директории:
```bash
mkdir data\input data\output data\temp data\backup logs models
```

2. Скопируйте файл конфигурации:
```bash
copy config\default.json config\local.json
```

3. Отредактируйте `config\local.json`:
   - Укажите пути к моделям
   - Настройте параметры RabbitMQ
   - Установите параметры логирования

## Установка RabbitMQ

1. Установите Erlang:
   - Скачайте и установите [Erlang для Windows](https://www.erlang.org/downloads)
   - Добавьте путь к Erlang в переменную PATH

2. Установите RabbitMQ:
   - Скачайте и установите [RabbitMQ для Windows](https://www.rabbitmq.com/install-windows.html)
   - Запустите RabbitMQ Service:
```bash
net start RabbitMQ
```

3. Включите плагин управления:
```bash
rabbitmq-plugins enable rabbitmq_management
```

4. Создайте пользователя и настройте права:
```bash
rabbitmqctl add_user admin password
rabbitmqctl set_user_tags admin administrator
rabbitmqctl set_permissions -p / admin ".*" ".*" ".*"
```

## Настройка моделей

1. Скачайте предобученную модель YOLOv5:
```bash
curl -L https://github.com/ultralytics/yolov5/releases/download/v6.1/yolov5s.pt -o models/yolov5s.pt
```

2. Установите EasyOCR:
```bash
pip install easyocr
```

3. Проверьте наличие моделей:
```bash
python scripts/check_models.py
```

## Запуск системы

1. Запустите RabbitMQ (если не запущен):
```bash
net start RabbitMQ
```

2. Запустите API сервер:
```bash
python src/api/main.py
```

3. Запустите GUI:
```bash
python src/gui/main.py
```

4. Запустите обработчик очереди:
```bash
python src/worker/main.py
```

## Проверка работоспособности

1. Проверьте API:
```bash
curl http://localhost:8000/health
```

2. Проверьте RabbitMQ:
- Откройте http://localhost:15672
- Войдите с учетными данными admin/password
- Проверьте статус очереди invoice_processing

3. Проверьте логи:
```bash
type logs\invoice_processing.log
```

4. Тестовый запуск:
- Поместите тестовый счет в data/input
- Проверьте результат в data/output
- Проверьте логи на наличие ошибок

## Устранение неполадок

1. Проблемы с CUDA:
- Проверьте версию CUDA: `nvidia-smi`
- Убедитесь, что версия CUDA совместима с PyTorch

2. Проблемы с RabbitMQ:
- Проверьте статус сервиса: `net start RabbitMQ`
- Проверьте логи: `type "%APPDATA%\RabbitMQ\log\rabbit@localhost.log"`

3. Проблемы с моделями:
- Проверьте наличие файлов моделей
- Проверьте права доступа к файлам
- Проверьте версии зависимостей

4. Проблемы с памятью:
- Уменьшите batch_size в конфигурации
- Уменьшите количество workers
- Проверьте использование GPU памяти 