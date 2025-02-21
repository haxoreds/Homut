"""
Drawings Table Initialization - Инициализация таблицы чертежей
=========================================================

Этот модуль создает таблицу для хранения информации о чертежах.
Таблица Drawings хранит:
- Информацию о чертежах
- Связи с штампами
- Метаданные файлов
"""

import sqlite3
import logging

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def init_drawings_table():
    """
    Создает таблицу Drawings для хранения информации о чертежах.

    Структура таблицы:
    - id: Уникальный идентификатор чертежа
    - stamp_id: Внешний ключ, связывающий чертеж со штампом
    - name: Название чертежа
    - file_type: Тип файла
    - file_path: Путь к файлу чертежа
    - description: Описание чертежа
    - version: Версия чертежа
    - created_at: Дата создания
    - updated_at: Дата обновления

    Особенности реализации:
    - Использует FOREIGN KEY для связи со штампами
    - Автоматически управляет временными метками
    """
    conn = None
    try:
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()

        # Создание таблицы для чертежей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Drawings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stamp_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            description TEXT,
            version TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stamp_id) REFERENCES Stamps(id)
        )
        ''')

        conn.commit()
        logger.info("Таблица Drawings успешно создана или уже существует")

    except Exception as e:
        logger.error(f"Ошибка при создании таблицы Drawings: {e}")
        raise
    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    init_drawings_table()