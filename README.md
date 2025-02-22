git clone https://github.com/your-username/homut.git
cd homut
```

2. Установите зависимости:
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


## Запуск

1. Запустите бот:
```bash
python homut.py
```

## Развертывание на сервере

1. Установите все зависимости на сервере
2. Настройте переменные окружения в файле .env
3. Запустите бота через systemd или screen/tmux для работы в фоновом режиме

### Пример systemd сервиса

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

Затем выполните:
```bash
sudo systemctl enable homut-bot
sudo systemctl start homut-bot
```

## Мониторинг

Для просмотра логов бота используйте:
```bash
tail -f /var/log/syslog | grep homut.py
```

или через systemd:
```bash
journalctl -u homut-bot -f