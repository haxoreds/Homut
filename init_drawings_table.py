import sqlite3
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def init_drawings_table():
    try:
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()

        # Создаем таблицу для чертежей
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
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    init_drawings_table()
