import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from menu import menu
from database import get_stamp_id_by_action
from menu import process_main_menu_action
from menu import back_to_menu_keyboard
logger = logging.getLogger(__name__)

# Функция для отображения остатка с кнопкой "Изменить количество"
async def show_balance(query, context, action, current_menu):
    db = context.application.db
    logger.info(f"Action: {action}, Current Menu: {current_menu}")
    # Определение таблицы на основе действия
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

    # Сохранение информации о таблице и меню в user_data
    context.user_data['table'] = table
    context.user_data['current_menu'] = current_menu
    context.user_data['action'] = action

    # Получение stamp_id
    stamp_id = await get_stamp_id_by_action(action)
    if not stamp_id:
        await query.message.reply_text(
            "Штамп не найден.", reply_markup=back_to_menu_keyboard(current_menu)
        )
        return

    # Сохранение stamp_id в user_data
    context.user_data['stamp_id'] = stamp_id

    # Получение данных из базы данных
    try:
        async with db.execute(
            f"SELECT name, quantity FROM {table} WHERE stamp_id = ?", (stamp_id,)
        ) as cursor:
            rows = await cursor.fetchall()
    except Exception as e:
        logger.exception("Ошибка при выполнении запроса к базе данных: %s", e)
        await query.message.reply_text(
            "Ошибка при получении данных из базы данных.",
            reply_markup=back_to_menu_keyboard(current_menu),
        )
        return

    # Формирование сообщения с остатком
    if not rows:
        message = "Данных нет."
    else:
        message = f"Остаток по {menu[current_menu]['text']}:\n"
        for name, quantity in rows:
            message += f"- {name}: {quantity}\n"

    # Создание клавиатуры с кнопкой "Изменить количество"
    # Получаем новое действие для изменения количества
    change_quantity_action = action.replace('showbalance', 'changequantity')

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Изменить количество", callback_data=change_quantity_action)],
            [InlineKeyboardButton("Назад", callback_data='back')],
        ]
    )

    await query.message.reply_text(message, reply_markup=keyboard)


