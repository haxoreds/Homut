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
        # Изменяем запрос для единообразного отображения времени
        async with db.execute(
            f"""SELECT 
                id, name, quantity, type, size, image_url, description,
                datetime(createdAt, '+3 hours') as created_at,
                datetime(updatedAt, '+3 hours') as updated_at,
                datetime(last_modified, '+3 hours') as last_modified
            FROM {table} 
            WHERE stamp_id = ?""", 
            (stamp_id,)
        ) as cursor:
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
            # Получаем все колонки из результата запроса
            columns = [description[0] for description in cursor.description]
            data = dict(zip(columns, row))

            message += f"<b>{data['name']}</b>\n"
            message += f"└ Количество: {data['quantity']}\n"

            # Добавляем дополнительные поля с единообразным форматированием времени
            for key, value in data.items():
                if key not in ['name', 'quantity', 'stamp_id', 'id']:
                    # Сначала проверяем временные метки
                    if key == 'created_at':
                        message += f"└ Создано: {value or '(данные отсутствуют)'}\n"
                    elif key == 'updated_at':
                        message += f"└ Обновлено: {value or '(данные отсутствуют)'}\n"
                    elif key == 'last_modified':
                        message += f"└ Последнее изменение: {value or '(данные отсутствуют)'}\n"
                    # Затем проверяем остальные поля
                    elif key == 'type':
                        message += f"└ Тип: {value or '(данные отсутствуют)'}\n"
                    elif key == 'size':
                        message += f"└ Размер: {value or '(данные отсутствуют)'}\n"
                    elif key == 'image_url':
                        message += f"└ Фото: {value or '(данные отсутствуют)'}\n"
                    elif key == 'description':
                        message += f"└ Описание: {value or '(данные отсутствуют)'}\n"
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