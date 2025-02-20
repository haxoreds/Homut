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

# Функция получения названия таблицы по категории
def get_table_name(category):
    category_to_table = {
        'punches': 'Punches',
        'inserts': 'Inserts',
        'knives': 'Knives',
        'discs': 'Discs',
        'pushers': 'Pushers',
        'cams': 'Clamps',
        'discparts': 'Disc_Parts',
        'stampparts': 'Parts',
        'drawings': 'Drawings'  # Добавляем таблицу чертежей
    }
    return category_to_table.get(category)

# Функция для получения stamp_id по действию
async def get_stamp_id_by_action(action):
    """Получение stamp_id на основе действия"""
    try:
        # Извлекаем категорию и inv_id из action
        category_match = re.match(r'^(?:addnewitem|showbalance|updatedb|changequantity|editdelete|upload_for_stamp_)(\d+)', action)
        if category_match:
            stamp_id = category_match.group(1)
            logger.info(f"Извлечён stamp_id: {stamp_id} из action: {action}")
            return int(stamp_id)
        else:
            logger.warning(f"Не удалось извлечь stamp_id из action: {action}")
            return None
    except Exception as e:
        logger.error(f"Ошибка при получении stamp_id: {e}")
        return None

# Функция получения списка позиций в категории для данного штампа
async def get_items_in_category(category, inv_id):
    table_name = get_table_name(category)
    if not table_name:
        logger.warning(f"Таблица не найдена для категории {category}")
        return []

    # Получаем stamp_id по inv_id
    inv_name = None
    from menu import inventory_list  # Импортируем inventory_list из menu.py
    for inv_id_item, inv_name_item in inventory_list:
        if inv_id_item == inv_id:
            inv_name = inv_name_item
            break
    if not inv_name:
        logger.warning(f"inv_id {inv_id} не найден в inventory_list.")
        return []

    async with get_async_connection() as conn:
        cursor = await conn.execute("SELECT id FROM Stamps WHERE name = ?", (inv_name,))
        result = await cursor.fetchone()
        await cursor.close()
        if result:
            stamp_id = result[0]
        else:
            logger.warning(f"Штамп с именем {inv_name} не найден в базе данных.")
            return []

        query = f"SELECT id, name FROM {table_name} WHERE stamp_id = ?"
        cursor = await conn.execute(query, (stamp_id,))
        rows = await cursor.fetchall()
        await cursor.close()

        items = [{'id': row[0], 'name': row[1]} for row in rows]
        return items

# Функция получения позиции по ID
async def get_item_by_id(category, item_id):
    table_name = get_table_name(category)
    if not table_name:
        logger.warning(f"Таблица не найдена для категории {category}")
        return None

    async with get_async_connection() as conn:
        query = f"SELECT * FROM {table_name} WHERE id = ?"
        cursor = await conn.execute(query, (item_id,))
        row = await cursor.fetchone()
        await cursor.close()

        if row:
            # Получаем названия столбцов
            cursor = await conn.execute(f"PRAGMA table_info({table_name})")
            columns_info = await cursor.fetchall()
            await cursor.close()
            columns = [info[1] for info in columns_info]
            item = dict(zip(columns, row))
            return item
        else:
            logger.warning(f"Позиция с id {item_id} не найдена в таблице {table_name}.")
            return None

# Функция обновления поля позиции
async def update_item_field(category, item_id, field, value):
    table_name = get_table_name(category)
    if not table_name:
        logger.warning(f"Таблица не найдена для категории {category}")
        return

    async with get_async_connection() as conn:
        query = f"UPDATE {table_name} SET {field} = ?, updatedAt = CURRENT_TIMESTAMP WHERE id = ?"
        await conn.execute(query, (value, item_id))
        await conn.commit()
        logger.info(f"Обновлено поле {field} для позиции id {item_id} в таблице {table_name}.")

# Функция удаления позиции из базы данных
async def delete_item_from_database(category, item_id):
    table_name = get_table_name(category)
    if not table_name:
        logger.warning(f"Таблица не найдена для категории {category}")
        return

    async with get_async_connection() as conn:
        query = f"DELETE FROM {table_name} WHERE id = ?"
        await conn.execute(query, (item_id,))
        await conn.commit()
        logger.info(f"Удалена позиция id {item_id} из таблицы {table_name}.")

# Дополнительные функции по необходимости