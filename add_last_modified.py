import aiosqlite
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def add_last_modified_column():
    tables = ['Punches', 'Inserts', 'Parts', 'Knives', 'Clamps', 'Disc_Parts', 'Pushers']

    try:
        async with aiosqlite.connect('inventory.db') as db:
            for table in tables:
                try:
                    # Добавляем колонку last_modified без значения по умолчанию
                    await db.execute(f'''
                        ALTER TABLE {table} 
                        ADD COLUMN last_modified TIMESTAMP
                    ''')

                    # Обновляем существующие записи
                    await db.execute(f'''
                        UPDATE {table}
                        SET last_modified = CURRENT_TIMESTAMP
                    ''')

                    await db.commit()
                    logger.info(f"Успешно добавлена колонка last_modified в таблицу {table}")

                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info(f"Колонка last_modified уже существует в таблице {table}")
                    else:
                        logger.error(f"Ошибка при обновлении таблицы {table}: {e}")
                        raise
    except Exception as e:
        logger.error(f"Ошибка при подключении к базе данных: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(add_last_modified_column())