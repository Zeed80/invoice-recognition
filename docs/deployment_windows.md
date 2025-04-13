# Руководство по развертыванию на Windows

## Содержание
1. [Системные требования](#системные-требования)
2. [Подготовка системы](#подготовка-системы)
3. [Установка Python](#установка-python)
4. [Установка CUDA](#установка-cuda)
5. [Установка проекта](#установка-проекта)
6. [Настройка RabbitMQ](#настройка-rabbitmq)
7. [Настройка моделей](#настройка-моделей)
8. [Проверка установки](#проверка-установки)
9. [Устранение неполадок](#устранение-неполадок)

## Системные требования

### Минимальные требования
- Windows 10/11 (64-bit)
- Intel Core i5 / AMD Ryzen 5 или выше
- 8 ГБ оперативной памяти
- NVIDIA GPU с 4 ГБ VRAM
- 10 ГБ свободного места на диске
- Права администратора

### Рекомендуемые требования
- Windows 10/11 Pro (64-bit)
- Intel Core i7 / AMD Ryzen 7 или выше
- 16 ГБ оперативной памяти
- NVIDIA GPU с 8 ГБ VRAM
- SSD с 20 ГБ свободного места
- Права администратора

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

## Установка CUDA

1. Проверьте совместимость:
   - Откройте PowerShell от администратора
   - Выполните:
```powershell
nvidia-smi
```
   - Запомните версию CUDA

2. Установите CUDA Toolkit:
   - Перейдите на [NVIDIA CUDA Downloads](https://developer.nvidia.com/cuda-downloads)
   - Выберите:
     - Operating System: Windows
     - Architecture: x86_64
     - Version: 11.x (совместимую с вашей видеокартой)
   - Скачайте и установите драйверы
   - Скачайте и установите CUDA Toolkit

3. Установите cuDNN:
   - Зарегистрируйтесь на [NVIDIA Developer](https://developer.nvidia.com/)
   - Скачайте cuDNN для вашей версии CUDA
   - Распакуйте архив
   - Скопируйте файлы в папку CUDA:
```powershell
xcopy cuda\bin\* "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.x\bin"
xcopy cuda\include\* "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.x\include"
xcopy cuda\lib\x64\* "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.x\lib\x64"
```

4. Настройте переменные среды:
   - Нажмите Win + R
   - Введите `sysdm.cpl`
   - Перейдите на вкладку "Дополнительно"
   - Нажмите "Переменные среды"
   - В системных переменных добавьте в PATH:
```
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.x\bin
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.x\libnvvp
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
```powershell
pip install -r requirements.txt
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

## Проверка установки

1. Проверьте CUDA:
```powershell
python -c "import torch; print(torch.cuda.is_available())"
```

2. Проверьте RabbitMQ:
   - Откройте http://localhost:15672
   - Войдите как admin/password

3. Проверьте конфигурацию:
```powershell
copy config\default.json config\local.json
python scripts\check_config.py
```

4. Запустите тесты:
```powershell
pytest tests
```

## Устранение неполадок

### CUDA не работает
1. Проверьте драйверы:
```powershell
nvidia-smi
```
2. Проверьте переменные среды:
```powershell
echo $env:PATH
```
3. Переустановите PyTorch с CUDA:
```powershell
pip uninstall torch torchvision
pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu11x
```

### RabbitMQ не запускается
1. Проверьте службу:
```powershell
Get-Service RabbitMQ
```
2. Проверьте логи:
```powershell
type "$env:APPDATA\RabbitMQ\log\rabbit@localhost.log"
```
3. Переустановите RabbitMQ:
```powershell
net stop RabbitMQ
"C:\Program Files\RabbitMQ Server\rabbitmq_server-3.x.x\sbin\rabbitmq-service.bat" remove
"C:\Program Files\RabbitMQ Server\rabbitmq_server-3.x.x\sbin\rabbitmq-service.bat" install
net start RabbitMQ
```

### Проблемы с Python
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
pip install -r requirements.txt
```

### Недостаточно памяти
1. Закройте ненужные программы
2. Уменьшите параметры в `config\local.json`:
   - `batch_size`: 1
   - `num_workers`: 2
3. Отключите фоновые процессы Windows
4. Увеличьте файл подкачки 