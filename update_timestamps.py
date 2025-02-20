import aiosqlite
import asyncio
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_timestamps():
    tables = ['Punches', 'Inserts', 'Parts', 'Knives', 'Clamps', 'Disc_Parts', 'Pushers']

    try:
        async with aiosqlite.connect('inventory.db') as db:
            for table in tables:
                try:
                    # Сначала добавляем недостающие колонки, если их нет
                    for column in ['updatedAt', 'createdAt', 'last_modified']:
                        try:
                            await db.execute(f'ALTER TABLE {table} ADD COLUMN {column} TIMESTAMP')
                            logger.info(f"Добавлена колонка {column} в таблицу {table}")
                        except Exception as e:
                            if "duplicate column name" in str(e).lower():
                                logger.info(f"Колонка {column} уже существует в таблице {table}")
                            else:
                                logger.error(f"Ошибка при добавлении колонки {column} в таблицу {table}: {e}")

                    # Теперь обновляем записи без временных меток
                    await db.execute(f'''
                        UPDATE {table}
                        SET createdAt = CURRENT_TIMESTAMP,
                            updatedAt = CURRENT_TIMESTAMP,
                            last_modified = CURRENT_TIMESTAMP
                        WHERE createdAt IS NULL 
                           OR updatedAt IS NULL 
                           OR last_modified IS NULL
                    ''')

                    # Обновляем временные метки, добавляя 3 часа к UTC
                    await db.execute(f'''
                        UPDATE {table}
                        SET createdAt = datetime(createdAt, '+3 hours'),
                            updatedAt = datetime(updatedAt, '+3 hours'),
                            last_modified = datetime(last_modified, '+3 hours')
                        WHERE createdAt NOT LIKE '%+03:00'
                           AND updatedAt NOT LIKE '%+03:00'
                           AND last_modified NOT LIKE '%+03:00'
                    ''')

                    await db.commit()
                    logger.info(f"Успешно обновлены временные метки в таблице {table}")

                except Exception as e:
                    logger.error(f"Ошибка при обновлении таблицы {table}: {e}")
                    continue

    except Exception as e:
        logger.error(f"Ошибка при подключении к базе данных: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(update_timestamps())