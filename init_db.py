"""
Database Initialization Module - Модуль инициализации базы данных
============================================================

Этот модуль отвечает за создание структуры базы данных.
Создает все необходимые таблицы:
- Stamps (Штампы)
- Punches (Пуансоны)
- Inserts (Вставки)
- Knives (Ножи)
- Discs (Диски)
- Pushers (Толкатели)
- Clamps (Кулачки)
- Parts (Запчасти)
- Parts_Compatibility (Совместимость деталей)
"""

import sqlite3
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def init_db():
    """
    Инициализирует базу данных, создавая все необходимые таблицы.

    Создает следующие таблицы:
    1. Stamps - основная таблица штампов
    2. Punches - таблица пуансонов
    3. Inserts - таблица вставок
    4. Knives - таблица ножей
    5. Discs - таблица дисков
    6. Clamps - таблица кулачков
    7. Disc_Parts - таблица запчастей для дисковых штампов
    8. Pushers - таблица толкателей
    9. Parts - таблица запчастей
    10. Parts_Compatibility - таблица совместимости деталей

    Особенности реализации:
    - Использует FOREIGN KEY для связей между таблицами
    - Включает поддержку временных меток (TIMESTAMP)
    - Автоматически создает первичные ключи (PRIMARY KEY)
    """
    conn = None
    try:
        # Создаем соединение с базой данных
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()

        # Создаем таблицу штампов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Stamps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Создаем таблицу пуансонов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Punches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stamp_id INTEGER,
            name TEXT NOT NULL,
            type TEXT,
            size TEXT,
            quantity INTEGER DEFAULT 0,
            image_url TEXT,
            description TEXT,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stamp_id) REFERENCES Stamps(id)
        )
        ''')

        # Создаем таблицу вставок
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Inserts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stamp_id INTEGER,
            name TEXT NOT NULL,
            size TEXT,
            quantity INTEGER DEFAULT 0,
            description TEXT,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stamp_id) REFERENCES Stamps(id)
        )
        ''')

        # Создаем таблицу ножей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Knives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stamp_id INTEGER,
            name TEXT NOT NULL,
            size TEXT,
            quantity INTEGER DEFAULT 0,
            description TEXT,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stamp_id) REFERENCES Stamps(id)
        )
        ''')

        # Создаем таблицу кулачков
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Clamps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stamp_id INTEGER,
            name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            description TEXT,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stamp_id) REFERENCES Stamps(id)
        )
        ''')

        # Создаем таблицу запчастей для дисковых штампов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Disc_Parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stamp_id INTEGER,
            name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            description TEXT,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stamp_id) REFERENCES Stamps(id)
        )
        ''')

        # Создаем таблицу толкателей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Pushers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stamp_id INTEGER,
            name TEXT NOT NULL,
            size TEXT,
            quantity INTEGER DEFAULT 0,
            description TEXT,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stamp_id) REFERENCES Stamps(id)
        )
        ''')

        # Создаем таблицу запчастей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stamp_id INTEGER,
            name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            description TEXT,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stamp_id) REFERENCES Stamps(id)
        )
        ''')

        # Создаем таблицу совместимости деталей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Parts_Compatibility (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_stamp_id INTEGER,
            target_stamp_id INTEGER,
            part_type TEXT NOT NULL,
            part_id INTEGER,
            notes TEXT,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_stamp_id) REFERENCES Stamps(id),
            FOREIGN KEY (target_stamp_id) REFERENCES Stamps(id)
        )
        ''')

        # Фиксируем изменения
        conn.commit()
        logger.info("База данных успешно инициализирована")

    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise
    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    init_db()