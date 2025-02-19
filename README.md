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
- `logger.py` - Настройка логирования
- `new_item.py` - Функционал добавления новых позиций
- `change_quantity.py` - Функционал изменения количества
- `menu.py` - Меню и клавиатуры
- `showballance.py` - Отображение остатков

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
  - image_url (TEXT)
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

(и аналогичные таблицы для других категорий)

## Использование

После запуска бота:

1. Отправьте команду /start для начала работы
2. Используйте интерактивное меню для навигации
3. Выберите нужную категорию и действие
4. Следуйте инструкциям бота

## Функциональность

1. **Управление инвентарем**:
   - Просмотр остатков по категориям
   - Добавление новых позиций
   - Изменение количества
   - Редактирование информации

2. **Категории**:
   - Пуансоны
   - Вставки
   - Запчасти штампов
   - Ножи
   - Кулачки
   - Запчасти дисковых штампов
   - Толкатели

3. **Дополнительные возможности**:
   - Отслеживание изменений
   - Подтверждение действий
   - Интерактивное меню навигации

## Инициализация базы данных

Для первоначальной настройки базы данных выполните:
```bash
python init_db.py
```

## Запуск

```bash
python homut.py