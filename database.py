import logging
import sqlite3
import re
import aiosqlite
from menu import menu, create_inventory_submenus, inventory_list, get_menu_keyboard, back_to_menu_keyboard

# Настройка логирования
logger = logging.getLogger(__name__)

def get_connection():
    """Получение соединения с базой данных"""
    try:
        conn = sqlite3.connect('inventory.db')
        # Включаем поддержку внешних ключей
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Ошибка при подключении к базе данных: {e}")
        raise

async def get_async_connection():
    """Получение асинхронного соединения с базой данных"""
    try:
        conn = await aiosqlite.connect('inventory.db')
        await conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except aiosqlite.Error as e:
        logger.error(f"Ошибка при асинхронном подключении к базе данных: {e}")
        raise

async def get_stamp_id_by_action(action):
    """Получение stamp_id на основе действия"""
    try:
        logger.info(f"Получен action для обработки: {action}")

        # Извлекаем категорию и inv_id из action
        pattern = r'^(?:addnewitem|showbalance|updatedb|changequantity|editdelete)([a-z]+)(\d+(?:_\d+)?(?:_[a-z]+(?:_\d+)?)?)'
        match = re.match(pattern, action)

        if not match:
            logger.warning(f"Не удалось распознать формат action: {action}")
            return None

        category = match.group(1)
        inv_id = match.group(2)
        logger.info(f"Извлечена категория: {category}, inv_id: {inv_id}")

        # Ищем соответствующий штамп в inventory_list
        inv_name = None
        for inv_id_item, inv_name_item in inventory_list:
            if inv_id_item == inv_id:
                inv_name = inv_name_item
                logger.info(f"Найдено соответствие в inventory_list: {inv_name}")
                break

        if not inv_name:
            logger.warning(f"Не найдено соответствие в inventory_list для inv_id: {inv_id}")
            return None

        # Получаем stamp_id из базы данных
        db = await aiosqlite.connect('inventory.db')
        try:
            await db.execute("PRAGMA foreign_keys = ON")
            async with db.execute("SELECT id FROM Stamps WHERE name = ?", (inv_name,)) as cursor:
                result = await cursor.fetchone()
                if result:
                    stamp_id = result[0]
                    logger.info(f"Найден stamp_id в базе данных: {stamp_id} для штампа {inv_name}")
                    return stamp_id
                else:
                    logger.warning(f"Штамп {inv_name} не найден в базе данных")
                    return None
        finally:
            await db.close()

    except Exception as e:
        logger.error(f"Ошибка при получении stamp_id: {e}", exc_info=True)
        return None

def get_table_name(category):
    """Получение имени таблицы по категории"""
    category_to_table = {
        'punches': 'Punches',
        'inserts': 'Inserts',
        'knives': 'Knives',
        'discs': 'Discs',
        'pushers': 'Pushers',
        'cams': 'Clamps',
        'discparts': 'Disc_Parts',
        'stampparts': 'Parts',
        'drawings': 'Drawings'
    }
    return category_to_table.get(category)

async def get_items_in_category(category, inv_id):
    """Получение списка позиций в категории для данного штампа"""
    logger.info(f"Запрос позиций для категории {category} и inv_id {inv_id}")

    table_name = get_table_name(category)
    if not table_name:
        logger.warning(f"Таблица не найдена для категории {category}")
        return []

    try:
        # Находим соответствующий stamp_id
        inv_name = None
        for inv_id_item, inv_name_item in inventory_list:
            if inv_id_item == inv_id:
                inv_name = inv_name_item
                logger.info(f"Найдено имя штампа: {inv_name}")
                break

        if not inv_name:
            logger.warning(f"Не найдено имя штампа для inv_id: {inv_id}")
            return []

        async with await get_async_connection() as conn:
            # Получаем stamp_id
            cursor = await conn.execute("SELECT id FROM Stamps WHERE name = ?", (inv_name,))
            result = await cursor.fetchone()
            await cursor.close()

            if not result:
                logger.warning(f"Штамп {inv_name} не найден в базе данных")
                return []

            stamp_id = result[0]
            logger.info(f"Найден stamp_id: {stamp_id}")

            # Получаем список позиций
            query = f"SELECT id, name FROM {table_name} WHERE stamp_id = ?"
            cursor = await conn.execute(query, (stamp_id,))
            rows = await cursor.fetchall()
            await cursor.close()

            items = [{'id': row[0], 'name': row[1]} for row in rows]
            logger.info(f"Найдено {len(items)} позиций для штампа {inv_name}")
            return items

    except Exception as e:
        logger.error(f"Ошибка при получении списка позиций: {e}", exc_info=True)
        return []

async def get_item_by_id(category, item_id):
    """Получение позиции по ID"""
    table_name = get_table_name(category)
    if not table_name:
        logger.warning(f"Таблица не найдена для категории {category}")
        return None

    try:
        async with await get_async_connection() as conn:
            query = f"SELECT * FROM {table_name} WHERE id = ?"
            cursor = await conn.execute(query, (item_id,))
            row = await cursor.fetchone()

            if row:
                cursor = await conn.execute(f"PRAGMA table_info({table_name})")
                columns_info = await cursor.fetchall()
                columns = [info[1] for info in columns_info]
                item = dict(zip(columns, row))
                return item
            else:
                logger.warning(f"Позиция с id {item_id} не найдена в таблице {table_name}")
                return None
    except Exception as e:
        logger.error(f"Ошибка при получении позиции: {e}", exc_info=True)
        return None

async def update_item_field(category, item_id, field, value):
    """Обновление поля позиции"""
    table_name = get_table_name(category)
    if not table_name:
        logger.warning(f"Таблица не найдена для категории {category}")
        return False

    try:
        async with await get_async_connection() as conn:
            query = f"UPDATE {table_name} SET {field} = ?, updatedAt = CURRENT_TIMESTAMP WHERE id = ?"
            await conn.execute(query, (value, item_id))
            await conn.commit()
            logger.info(f"Обновлено поле {field} для позиции id {item_id} в таблице {table_name}")
            return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении поля: {e}", exc_info=True)
        return False

async def delete_item_from_database(category, item_id):
    """Удаление позиции из базы данных"""
    table_name = get_table_name(category)
    if not table_name:
        logger.warning(f"Таблица не найдена для категории {category}")
        return False

    try:
        async with await get_async_connection() as conn:
            query = f"DELETE FROM {table_name} WHERE id = ?"
            await conn.execute(query, (item_id,))
            await conn.commit()
            logger.info(f"Удалена позиция id {item_id} из таблицы {table_name}")
            return True
    except Exception as e:
        logger.error(f"Ошибка при удалении позиции: {e}", exc_info=True)
        return False