# Руководство по развертыванию на Windows

## Содержание
1. [Системные требования](#системные-требования)
2. [Подготовка системы](#подготовка-системы)
3. [Установка Python](#установка-python)
4. [Установка проекта](#установка-проекта)
5. [Настройка RabbitMQ](#настройка-rabbitmq)
6. [Настройка моделей](#настройка-моделей)
7. [Проверка установки](#проверка-установки)
8. [Оптимизация производительности](#оптимизация-производительности)
9. [Устранение неполадок](#устранение-неполадок)

## Системные требования

### Минимальные требования (CPU)
- Windows 10/11 (64-bit)
- Intel Core i5 / AMD Ryzen 5 или выше
- 8 ГБ оперативной памяти
- 10 ГБ свободного места на диске
- Права администратора

### Рекомендуемые требования (CPU)
- Windows 10/11 Pro (64-bit)
- Intel Core i7 / AMD Ryzen 7 или выше
- 16 ГБ оперативной памяти
- SSD с 20 ГБ свободного места
- Права администратора

### Рекомендуемые требования (GPU - опционально)
- NVIDIA GPU с 4+ ГБ VRAM
- CUDA-совместимая видеокарта
- Дополнительно 4 ГБ оперативной памяти

## Подготовка системы

1. Обновите Windows до последней версии:
   - Нажмите Win + I
   - Перейдите в "Обновление и безопасность"
   - Нажмите "Проверить наличие обновлений"

2. Установите Visual C++ Redistributable:
   - Скачайте [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
   - Запустите установщик от имени администратора
   - Следуйте инструкциям установщика

3. Установите Git для Windows:
   - Скачайте [Git для Windows](https://git-scm.com/download/win)
   - При установке выберите:
     - "Use Git from Git Bash only"
     - "Checkout as-is, commit as-is"
     - "Use Windows' default console window"

## Установка Python

1. Скачайте Python 3.9:
   - Перейдите на [python.org](https://www.python.org/downloads/)
   - Скачайте Python 3.9.x (64-bit)

2. Установите Python:
   - Запустите установщик от имени администратора
   - ✅ Отметьте "Add Python 3.9 to PATH"
   - ✅ Отметьте "Install pip"
   - Нажмите "Customize installation"
   - ✅ Отметьте все опциональные компоненты
   - Установите в `C:\Python39`

3. Проверьте установку:
```powershell
python --version
pip --version
```

## Установка проекта

1. Клонируйте репозиторий:
```powershell
git clone https://github.com/your-repo/invoice-recognition.git
cd invoice-recognition
```

2. Создайте виртуальное окружение:
```powershell
python -m venv venv
.\venv\Scripts\activate
```

3. Обновите pip:
```powershell
python -m pip install --upgrade pip
```

4. Установите зависимости:

Для CPU:
```powershell
pip install -r requirements.cpu.txt
```

Для GPU (опционально):
```powershell
pip install -r requirements.gpu.txt
```

5. Создайте директории:
```powershell
mkdir data\input, data\output, data\temp, data\backup, logs, models
```

## Настройка RabbitMQ

1. Установите Erlang:
   - Скачайте [Erlang для Windows](https://www.erlang.org/downloads)
   - Установите от имени администратора
   - Добавьте в PATH:
```
C:\Program Files\erl-24.x\bin
```

2. Установите RabbitMQ:
   - Скачайте [RabbitMQ для Windows](https://www.rabbitmq.com/install-windows.html)
   - Установите от имени администратора
   - Запустите службу:
```powershell
net start RabbitMQ
```

3. Включите веб-интерфейс:
```powershell
"C:\Program Files\RabbitMQ Server\rabbitmq_server-3.x.x\sbin\rabbitmq-plugins.bat" enable rabbitmq_management
```

4. Создайте пользователя:
```powershell
"C:\Program Files\RabbitMQ Server\rabbitmq_server-3.x.x\sbin\rabbitmqctl.bat" add_user admin password
"C:\Program Files\RabbitMQ Server\rabbitmq_server-3.x.x\sbin\rabbitmqctl.bat" set_user_tags admin administrator
"C:\Program Files\RabbitMQ Server\rabbitmq_server-3.x.x\sbin\rabbitmqctl.bat" set_permissions -p / admin ".*" ".*" ".*"
```

## Настройка моделей

1. Скачайте YOLOv5:
```powershell
curl.exe -L "https://github.com/ultralytics/yolov5/releases/download/v6.1/yolov5s.pt" -o "models/yolov5s.pt"
```

2. Установите модели EasyOCR:
```powershell
python -c "import easyocr; reader = easyocr.Reader(['ru', 'en'])"
```

3. Настройте конфигурацию:
```powershell
copy config\default.json config\local.json
```

4. Отредактируйте `config\local.json`:

Для CPU:
```json
{
  "model": {
    "device": "cpu",
    "batch_size": 1
  }
}
```

Для GPU (если установлен):
```json
{
  "model": {
    "device": "cuda",
    "batch_size": 4
  }
}
```

## Проверка установки

1. Проверьте конфигурацию:
```powershell
python scripts\check_config.py
```

2. Проверьте RabbitMQ:
   - Откройте http://localhost:15672
   - Войдите как admin/password

3. Запустите тесты:
```powershell
pytest tests
```

## Оптимизация производительности

### Для CPU

1. Оптимизация параметров:
   - Установите в `config\local.json`:
```json
{
  "model": {
    "device": "cpu",
    "batch_size": 1,
    "num_workers": 1,
    "use_mkldnn": true
  },
  "processing": {
    "max_concurrent_tasks": 2,
    "timeout": 600
  }
}
```

2. Настройка приоритетов процесса:
```powershell
# Запуск с высоким приоритетом
Start-Process python -ArgumentList "src/worker/main.py" -WindowStyle Normal -Priority High
```

3. Закройте ресурсоемкие приложения

### Для GPU (если установлен)

1. Оптимизация параметров:
   - Установите в `config\local.json`:
```json
{
  "model": {
    "device": "cuda",
    "batch_size": 4,
    "num_workers": 2,
    "use_amp": true
  },
  "processing": {
    "max_concurrent_tasks": 4,
    "timeout": 300
  }
}
```

## Устранение неполадок

### Общие проблемы
1. Проверьте виртуальное окружение:
```powershell
.\venv\Scripts\activate
python -c "import sys; print(sys.prefix)"
```

2. Пересоздайте окружение:
```powershell
deactivate
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.cpu.txt  # или requirements.gpu.txt
```

### Проблемы производительности CPU
1. Проверьте загрузку CPU:
```powershell
Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples 10
```

2. Оптимизация:
   - Уменьшите `batch_size` до 1
   - Уменьшите `num_workers` до 1
   - Включите `use_mkldnn` в конфигурации
   - Закройте фоновые процессы

### RabbitMQ не запускается
1. Проверьте службу:
```powershell
Get-Service RabbitMQ
```

2. Проверьте логи:
```powershell
type "$env:APPDATA\RabbitMQ\log\rabbit@localhost.log"
```

### Недостаточно памяти
1. Проверьте использование памяти:
```powershell
Get-Process python | Select-Object WorkingSet, PM, CPU
```

2. Оптимизация:
   - Уменьшите `batch_size`
   - Уменьшите количество workers
   - Увеличьте файл подкачки
   - Очистите временные файлы:
```powershell
Remove-Item -Path "data\temp\*" -Recurse -Force
```