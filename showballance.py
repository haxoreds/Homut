import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from menu import menu
from database import get_stamp_id_by_action
from menu import process_main_menu_action
from menu import back_to_menu_keyboard

logger = logging.getLogger(__name__)

# Словарь эмодзи для категорий
CATEGORY_EMOJI = {
    'Punches': '🔨',
    'Inserts': '🔧',
    'Parts': '⚙️',
    'Knives': '🔪',
    'Clamps': '🗜️',
    'Disc_Parts': '💿',
    'Pushers': '👊'
}

async def show_balance(query, context, action, current_menu):
    db = context.application.db
    logger.info(f"Action: {action}, Current Menu: {current_menu}")

    table = None
    if 'punches' in action:
        table = 'Punches'
    elif 'inserts' in action:
        table = 'Inserts'
    elif 'stampparts' in action:
        table = 'Parts'
    elif 'knives' in action:
        table = 'Knives'
    elif 'cams' in action:
        table = 'Clamps'
    elif 'discparts' in action:
        table = 'Disc_Parts'
    elif 'pushers' in action:
        table = 'Pushers'
    else:
        await query.message.reply_text(
            "Неизвестный раздел.", reply_markup=back_to_menu_keyboard(current_menu)
        )
        return

    context.user_data['table'] = table
    context.user_data['current_menu'] = current_menu
    context.user_data['action'] = action

    stamp_id = await get_stamp_id_by_action(action)
    if not stamp_id:
        await query.message.reply_text(
            "Штамп не найден.", reply_markup=back_to_menu_keyboard(current_menu)
        )
        return

    context.user_data['stamp_id'] = stamp_id

    try:
        # Get table columns
        async with db.execute(f"PRAGMA table_info({table})") as cursor:
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            logger.info(f"Columns in {table}: {column_names}")

        # Build dynamic SELECT query based on available columns
        base_columns = ['id', 'name', 'quantity']  # Always required columns
        optional_columns = ['size', 'description']  # Optional columns

        select_columns = base_columns + [col for col in optional_columns if col in column_names]

        # Add timestamp columns if they exist
        if 'createdAt' in column_names:
            select_columns.append("datetime(createdAt, '+3 hours') as created_at")
        if 'updatedAt' in column_names:
            select_columns.append("datetime(updatedAt, '+3 hours') as updated_at")
        if 'last_modified' in column_names:
            select_columns.append("datetime(last_modified, '+3 hours') as last_modified")

        query_text = f"""
            SELECT {', '.join(select_columns)}
            FROM {table} 
            WHERE stamp_id = ?
        """
        logger.info(f"Executing query: {query_text}")

        async with db.execute(query_text, (stamp_id,)) as cursor:
            rows = await cursor.fetchall()

    except Exception as e:
        logger.exception("Ошибка при выполнении запроса к базе данных: %s", e)
        await query.message.reply_text(
            "Ошибка при получении данных из базы данных.",
            reply_markup=back_to_menu_keyboard(current_menu),
        )
        return

    if not rows:
        message = "Данных нет."
    else:
        emoji = CATEGORY_EMOJI.get(table, '📦')
        message = f"{emoji} <b>Остаток по {menu[current_menu]['text']}</b>\n\n"

        for row in rows:
            # Get column names from cursor description
            columns = [description[0] for description in cursor.description]
            data = dict(zip(columns, row))

            message += f"<b>{data['name']}</b>\n"
            message += f"└ Количество: {data['quantity']}\n"

            # Add optional fields if they exist in data
            if 'size' in data and data['size']:
                message += f"└ Размер: {data['size']}\n"
            if 'description' in data and data['description']:
                message += f"└ Описание: {data['description']}\n"

            # Add timestamp information
            if 'created_at' in data:
                message += f"└ Создано: {data['created_at'] or '(данные отсутствуют)'}\n"
            if 'updated_at' in data:
                message += f"└ Обновлено: {data['updated_at'] or '(данные отсутствуют)'}\n"
            if 'last_modified' in data:
                message += f"└ Последнее изменение: {data['last_modified'] or '(данные отсутствуют)'}\n"

            message += "\n"

    change_quantity_action = action.replace('showbalance', 'changequantity')

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Изменить количество", callback_data=change_quantity_action)],
            [InlineKeyboardButton("Назад", callback_data='back')],
        ]
    )

    await query.message.reply_text(
        message, 
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )