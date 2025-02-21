# Homut - Telegram Bot for Warehouse Management

Telegram-бот для управления складским учетом инструментов и деталей. Поддерживает работу с различными категориями: пуансоны, ножи, диски, вставки и другие специализированные компоненты.

## Основные возможности

- Отслеживание остатков товаров
- Работа с множеством категорий инструментов
- Гибкий механизм базы данных SQLite
- Поддержка различных типов складских позиций
- Управление чертежами и документацией
- Система совместимости деталей

## Системные требования

- Python 3.9 или выше
- SQLite3
- Место на диске: минимум 100MB (для хранения чертежей)
- ОС: Linux (рекомендуется), Windows, macOS

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/homut.git
cd homut
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/macOS
venv\Scripts\activate     # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

### Список основных зависимостей и их версии:

- python-telegram-bot==21.10
- python-dotenv==1.0.1
- aiosqlite==0.21.0
- validators==0.34.0

## Настройка окружения

1. Создайте файл .env на основе .env.example:
```bash
cp .env.example .env
```

2. Отредактируйте .env файл, добавив ваш токен Telegram бота:
```
TELEGRAM_TOKEN=your_bot_token_here
```

## Получение токена бота

1. Получите токен бота у @BotFather в Telegram:
   - Напишите /newbot
   - Следуйте инструкциям для создания нового бота
   - Скопируйте полученный токен в .env файл

## Инициализация базы данных

1. При первом запуске будет автоматически создана база данных SQLite с необходимыми таблицами.
2. Для инициализации таблицы чертежей выполните:
```bash
python init_drawings_table.py
```

## Запуск

1. Запустите бот:
```bash
python homut.py
```

## Развертывание на сервере

1. Установите все необходимые пакеты:
```bash
apt update
apt install python3 python3-pip sqlite3
```

2. Клонируйте репозиторий и установите зависимости:
```bash
git clone https://github.com/your-username/homut.git
cd homut
pip3 install -r requirements.txt
```

3. Настройте systemd сервис для автоматического запуска.
Создайте файл `/etc/systemd/system/homut-bot.service`:

```ini
[Unit]
Description=Homut Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/homut
Environment=PYTHONPATH=/path/to/homut
ExecStart=/usr/bin/python3 homut.py
Restart=always

[Install]
WantedBy=multi-user.target
```

4. Активируйте и запустите сервис:
```bash
sudo systemctl enable homut-bot
sudo systemctl start homut-bot
```

## Мониторинг

Для просмотра логов бота используйте:
```bash
# Через systemd
journalctl -u homut-bot -f

# Напрямую из файла логов
tail -f homut.log
```

## Бэкап данных

1. Регулярно делайте резервные копии базы данных:
```bash
# Создание бэкапа
sqlite3 inventory.db ".backup 'inventory.db.backup'"

# Восстановление из бэкапа
sqlite3 inventory.db ".restore 'inventory.db.backup'"
```

2. Также сохраняйте папку с чертежами:
```bash
tar -czf drawings_backup.tar.gz drawings/
```

## Обновление

1. Остановите бота:
```bash
sudo systemctl stop homut-bot
```

2. Создайте резервную копию данных.

3. Обновите код:
```bash
git pull origin main
```

4. Установите новые зависимости:
```bash
pip install -r requirements.txt
```

5. Запустите бота:
```bash
sudo systemctl start homut-bot
```

## Структура проекта

```
├── homut.py           # Основной файл приложения
├── config.py          # Конфигурация и настройки
├── database.py        # Работа с базой данных
├── constants.py       # Константы и перечисления
├── menu.py           # Меню и клавиатуры
├── drawings.py        # Функционал работы с чертежами
├── showballance.py    # Отображение остатков
├── change_quantity.py # Функционал изменения количества
├── compatibility.py   # Функционал совместимости деталей
├── edit_delete_item.py # Функционал редактирования и удаления
├── new_item.py        # Функционал добавления новых позиций
└── drawings/          # Папка для хранения чертежей
```

## Структура базы данных

База данных использует SQLite и содержит следующие таблицы:

### Stamps (Основная таблица штампов)
- id (PRIMARY KEY)
- name (TEXT)
- description (TEXT)
- createdAt (TIMESTAMP)
- updatedAt (TIMESTAMP)

### Punches (Таблица пуансонов)
- id (PRIMARY KEY)
- stamp_id (FOREIGN KEY)
- name (TEXT)
- type (TEXT)
- size (TEXT)
- quantity (INTEGER)
- description (TEXT)
- createdAt (TIMESTAMP)
- updatedAt (TIMESTAMP)

### Drawings (Таблица чертежей)
- id (PRIMARY KEY)
- stamp_id (FOREIGN KEY)
- name (TEXT)
- file_type (TEXT)
- file_path (TEXT)
- description (TEXT)
- version (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

И аналогичные таблицы для других категорий (Parts, Knives, Clamps, Disc_Parts, Pushers).


## Лицензия

MIT

## Автор

Your Name <your.email@example.com>

## Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для ваших изменений
3. Внесите изменения
4. Отправьте pull request

При разработке придерживайтесь:
- PEP 8 для Python кода
- Добавляйте документацию к новым функциям
- Пишите тесты для новой функциональности