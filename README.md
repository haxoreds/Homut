git clone https://github.com/your-username/homut.git
cd homut
```

2. Установите зависимости:
```bash
pip install python-telegram-bot python-dotenv aiosqlite validators
```

3. Создайте файл .env на основе .env.example:
```bash
cp .env.example .env
```

4. Отредактируйте .env файл, добавив ваш токен Telegram бота:
```
BOT_TOKEN=your_bot_token_here
```

## Настройка бота

1. Получите токен бота у @BotFather в Telegram:
   - Напишите /newbot
   - Следуйте инструкциям для создания нового бота
   - Скопируйте полученный токен в .env файл

2. База данных создастся автоматически при первом запуске.

## Структура проекта

- `homut.py` - Основной файл приложения
- `config.py` - Конфигурация и настройки
- `database.py` - Работа с базой данных
- `constants.py` - Константы и перечисления
- `menu.py` - Меню и клавиатуры
- `showballance.py` - Отображение остатков
- `change_quantity.py` - Функционал изменения количества
- `edit_delete_item.py` - Функционал редактирования и удаления
- `new_item.py` - Функционал добавления новых позиций

## Структура базы данных

База данных использует SQLite и содержит следующие таблицы:

- **Stamps**: Основная таблица штампов
  - id (PRIMARY KEY)
  - name (TEXT)
  - description (TEXT)
  - createdAt (TIMESTAMP)
  - updatedAt (TIMESTAMP)

- **Punches**: Таблица пуансонов
  - id (PRIMARY KEY)
  - stamp_id (FOREIGN KEY)
  - name (TEXT)
  - type (TEXT)
  - size (TEXT)
  - quantity (INTEGER)
  - description (TEXT)
  - createdAt (TIMESTAMP)
  - updatedAt (TIMESTAMP)

- **Inserts**: Таблица вставок
  - id (PRIMARY KEY)
  - stamp_id (FOREIGN KEY)
  - name (TEXT)
  - size (TEXT)
  - quantity (INTEGER)
  - description (TEXT)
  - createdAt (TIMESTAMP)
  - updatedAt (TIMESTAMP)

И аналогичные таблицы для других категорий (Parts, Knives, Clamps, Disc_Parts, Pushers).

## Запуск

1. Запустите бот:
```bash
python homut.py