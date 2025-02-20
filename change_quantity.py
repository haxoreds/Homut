from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, error as telegram_error
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
)
import re
import logging
from menu import menu, create_inventory_submenus, inventory_list, get_menu_keyboard, back_to_menu_keyboard
from database import get_stamp_id_by_action
from showballance import show_balance
from constants import States

logger = logging.getLogger(__name__)

def get_adjust_quantity_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("+1", callback_data='adjust_quantity:+1'),
            InlineKeyboardButton("-1", callback_data='adjust_quantity:-1'),
        ],
        [
            InlineKeyboardButton("+10", callback_data='adjust_quantity:+10'),
            InlineKeyboardButton("-10", callback_data='adjust_quantity:-10'),
        ],
        [
            InlineKeyboardButton("Готово", callback_data='done_adjustment'),
            InlineKeyboardButton("Назад", callback_data='go_back'),
        ],
    ])

async def get_items_in_category(db, item_type, stamp_id):
    # Определяем таблицу на основе item_type
    table_mapping = {
        'punches': 'Punches',
        'inserts': 'Inserts',
        'stampparts': 'Parts',
        'knives': 'Knives',
        'cams': 'Clamps',
        'discparts': 'Disc_Parts',
        'pushers': 'Pushers',
    }

    table = table_mapping.get(item_type)
    if not table:
        logger.error(f"Unknown item type: {item_type}")
        return []

    try:
        async with db.execute(
            f"SELECT name, id FROM {table} WHERE stamp_id = ?",
            (stamp_id,)
        ) as cursor:
            results = await cursor.fetchall()
            items = [{'name': row[0], 'id': row[1]} for row in results]
            return items
    except Exception as e:
        logger.exception(f"Error fetching items: {e}")
        return []

async def change_quantity_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> States:
    query = update.callback_query
    await query.answer()
    callback_data = query.data
    logger.info(f"Change quantity callback data: {callback_data}")

    match = re.match(r'^changequantity([a-z]+)([\w_]+)$', callback_data)
    if match:
        item_type = match.group(1)
        inv_id = match.group(2)
        logger.info(f"Extracted item_type: {item_type}, inv_id: {inv_id}")

        context.user_data['item_type'] = item_type
        context.user_data['inv_id'] = inv_id
        context.user_data['action'] = callback_data

        # Получаем stamp_id по action
        stamp_id = await get_stamp_id_by_action(callback_data)
        if not stamp_id:
            await query.message.reply_text(
                "Не удалось определить штамп.",
                reply_markup=back_to_menu_keyboard(context.user_data.get('current_menu', 'main_menu'))
            )
            return ConversationHandler.END

        # Получаем список позиций для данного штампа и категории
        items = await get_items_in_category(context.application.db, item_type, stamp_id)
        logger.info(f"Retrieved items: {items}")

        if not items:
            await query.message.reply_text(
                "Нет доступных позиций для изменения.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='go_back')]])
            )
            return ConversationHandler.END

        # Создаем кнопки для каждой позиции
        keyboard = []
        for item in items:
            callback_data = f"item_{item['id']}"  # Убедимся, что формат callback_data соответствует pattern в ConversationHandler
            logger.info(f"Creating button with callback_data: {callback_data}")
            keyboard.append([InlineKeyboardButton(item['name'], callback_data=callback_data)])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='go_back')])

        logger.info(f"Created keyboard with {len(keyboard)} buttons")

        await query.message.reply_text(
            "Выберите позицию, количество которой хотите изменить:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return States.CHANGE_QTY_CHOOSING_ITEM
    else:
        logger.warning(f"Invalid callback data format: {callback_data}")
        await query.message.reply_text(
            "Некорректные данные, попробуйте снова.",
            reply_markup=back_to_menu_keyboard('main_menu')
        )
        return ConversationHandler.END

async def item_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        logger.warning("Received message instead of callback query")
        return ConversationHandler.END

    await query.answer()
    callback_data = query.data
    logger.info(f"Item selection callback data received: {callback_data}")

    if callback_data == 'go_back':
        await query.message.reply_text(
            "Действие отменено.",
            reply_markup=back_to_menu_keyboard(context.user_data.get('current_menu', 'main_menu'))
        )
        return ConversationHandler.END

    try:
        if not callback_data.startswith('item_'):
            logger.warning(f"Invalid callback data format: {callback_data}")
            await query.message.reply_text(
                "Пожалуйста, выберите позицию из списка.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='go_back')]])
            )
            return States.CHANGE_QTY_CHOOSING_ITEM

        item_id = int(callback_data.replace('item_', ''))
        logger.info(f"Successfully parsed item_id: {item_id}")

        item_type = context.user_data.get('item_type')
        inv_id = context.user_data.get('inv_id')
        action = context.user_data.get('action')

        logger.info(f"Processing item_id: {item_id}, type: {item_type}, inv_id: {inv_id}")

        if not all([item_type, inv_id, action]):
            logger.error(f"Missing context data. item_type: {item_type}, inv_id: {inv_id}, action: {action}")
            await query.message.reply_text(
                "Не удалось определить тип элемента или идентификатор инвентаря.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='go_back')]])
            )
            return ConversationHandler.END

        # Get stamp_id from action
        stamp_id = await get_stamp_id_by_action(action)
        if not stamp_id:
            logger.error(f"Could not get stamp_id for action: {action}")
            await query.message.reply_text(
                "Штамп не найден.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='go_back')]])
            )
            return ConversationHandler.END

        # Define table based on item_type
        table_mapping = {
            'punches': 'Punches',
            'inserts': 'Inserts',
            'stampparts': 'Parts',
            'knives': 'Knives',
            'cams': 'Clamps',
            'discparts': 'Disc_Parts',
            'pushers': 'Pushers',
        }
        table = table_mapping.get(item_type)

        if not table:
            logger.error(f"Unknown item_type: {item_type}")
            await query.message.reply_text(
                "Неизвестный тип элемента.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='go_back')]])
            )
            return ConversationHandler.END

        db = context.application.db
        # Get current quantity from database
        try:
            async with db.execute(
                f"SELECT name, quantity FROM {table} WHERE id = ? AND stamp_id = ?",
                (item_id, stamp_id)
            ) as cursor:
                result = await cursor.fetchone()
                if result:
                    item_name, current_quantity = result
                    logger.info(f"Retrieved item: {item_name}, quantity: {current_quantity}")
                else:
                    logger.warning(f"No item found with id {item_id} in table {table}")
                    await query.message.reply_text(
                        "Позиция не найдена в базе данных.\nПожалуйста, выберите позицию из списка.",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='go_back')]])
                    )
                    return States.CHANGE_QTY_CHOOSING_ITEM
        except Exception as e:
            logger.exception("Database error: %s", e)
            await query.message.reply_text(
                "Ошибка при получении данных из базы.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='go_back')]])
            )
            return ConversationHandler.END

        # Save item data in context
        context.user_data.update({
            'selected_item_name': item_name,
            'current_quantity': current_quantity,
            'new_quantity': current_quantity,
            'changes_saved': False,
            'state': States.CHANGE_QTY_ADJUSTING_QUANTITY
        })

        # Create keyboard for quantity adjustment
        keyboard = get_adjust_quantity_keyboard()

        await query.message.reply_text(
            f"Текущее количество для {item_name}: {current_quantity}\nВыберите действие:",
            reply_markup=keyboard
        )

        return States.CHANGE_QTY_ADJUSTING_QUANTITY
    except ValueError as e:
        logger.error(f"Value error while parsing item_id from callback_data {callback_data}: {e}")
        await query.message.reply_text(
            "Произошла ошибка при выборе позиции. Пожалуйста, попробуйте снова.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='go_back')]])
        )
        return States.CHANGE_QTY_CHOOSING_ITEM
    except Exception as e:
        logger.exception(f"Unexpected error in item_name_received: {e}")
        await query.message.reply_text(
            "Произошла неожиданная ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=back_to_menu_keyboard(context.user_data.get('current_menu', 'main_menu'))
        )
        return ConversationHandler.END

async def adjust_quantity_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    data = query.data  # Например, 'adjust_quantity:+1'
    logger.info(f"Callback data received: {data}")
    logger.info(f"Context user_data: {context.user_data}")

    pattern = r'^adjust_quantity:([+-]\d+)$'
    match = re.match(pattern, data)

    if not match:
        await query.message.reply_text("Действие не распознано.")
        return States.CHANGE_QTY_ADJUSTING_QUANTITY

    adjustment_str = match.group(1)
    adjustment = int(adjustment_str)

    item_name = context.user_data.get('selected_item_name')
    new_quantity = context.user_data.get('new_quantity')
    item_type = context.user_data.get('item_type')
    action = context.user_data.get('action')

    if item_name is None or new_quantity is None or item_type is None or action is None:
        await query.message.reply_text("Не удалось получить информацию о выбранном элементе.")
        return ConversationHandler.END

    # Преобразуем new_quantity в целое число, если это необходимо
    new_quantity = int(new_quantity)

    # Вычисляем новое количество
    new_quantity += adjustment
    if new_quantity < 0:
        new_quantity = 0
    context.user_data['new_quantity'] = new_quantity  # Сохраняем новое количество

    # Создаем клавиатуру для изменения количества
    keyboard = get_adjust_quantity_keyboard()

    # Добавляем логирование перед обновлением сообщения
    logger.info(f"Updating message for item {item_name} with new quantity: {new_quantity}")

    # Обновляем сообщение с новым количеством и клавиатурой
    try:
        await query.edit_message_text(
            text=f"Текущее количество для {item_name}: {new_quantity}\nВыберите действие:",
            reply_markup=keyboard,
        )
    except telegram_error.BadRequest as e:
        logger.exception("Ошибка при обновлении сообщения: %s", e)
        await query.message.reply_text("Ошибка при обновлении сообщения.")
        return States.CHANGE_QTY_ADJUSTING_QUANTITY
    except Exception as e:
        logger.exception("Неожиданная ошибка при обновлении сообщения: %s", e)
        await query.message.reply_text("Произошла неопределённая ошибка.")
        return States.CHANGE_QTY_ADJUSTING_QUANTITY

    return States.CHANGE_QTY_ADJUSTING_QUANTITY  # Остаёмся в текущем состоянии

async def done_adjustment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # Проверяем, были ли уже сохранены изменения
    if context.user_data.get('changes_saved'):
        await query.message.reply_text("Количество уже изменено, можете нажать кнопку 'Назад'.")
        return States.CHANGE_QTY_ADJUSTING_QUANTITY  # Остаёмся в текущем состоянии

    item_name = context.user_data.get('selected_item_name')
    new_quantity = context.user_data.get('new_quantity')
    item_type = context.user_data.get('item_type')
    action = context.user_data.get('action')
    db = context.application.db

    if item_name is None or new_quantity is None or item_type is None or action is None:
        await query.message.reply_text("Не удалось получить информацию о выбранном элементе.")
        return ConversationHandler.END

    # Определяем таблицу на основе item_type
    table_mapping = {
        'punches': 'Punches',
        'inserts': 'Inserts',
        'stampparts': 'Parts',
        'knives': 'Knives',
        'cams': 'Clamps',
        'discparts': 'Disc_Parts',
        'pushers': 'Pushers',
    }
    table = table_mapping.get(item_type)

    if not table:
        await query.message.reply_text("Неизвестный тип элемента.")
        return ConversationHandler.END

    # Получаем stamp_id по action
    stamp_id = await get_stamp_id_by_action(action)
    if not stamp_id:
        await query.message.reply_text("Штамп не найден.")
        return ConversationHandler.END

    # Обновляем количество в базе данных с учетом московского времени
    try:
        await db.execute(
            f"""
            UPDATE {table} 
            SET quantity = ?, 
                last_modified = datetime('now', '+3 hours') 
            WHERE stamp_id = ? AND name = ?
            """,
            (new_quantity, stamp_id, item_name),
        )
        await db.commit()
    except Exception as e:
        logger.exception("Ошибка при обновлении базы данных: %s", e)
        await query.message.reply_text("Ошибка при обновлении данных.")
        return ConversationHandler.END

    # Устанавливаем флаг, что изменения сохранены
    context.user_data['changes_saved'] = True

    await query.message.reply_text(
        f"Количество для {item_name} обновлено. Новый остаток: {new_quantity}"
    )

    return States.CHANGE_QTY_ADJUSTING_QUANTITY  # Остаёмся в текущем состоянии

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    current_state = context.user_data.get('state')

    # Проверяем сохранение изменений только если мы находимся в состоянии изменения количества
    # и есть несохраненные изменения
    if (current_state == States.CHANGE_QTY_ADJUSTING_QUANTITY and 
        not context.user_data.get('changes_saved', False) and
        all(key in context.user_data for key in ['selected_item_name', 'current_quantity', 'new_quantity'])):

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Сохранить изменения", callback_data='save_and_exit')],
                [InlineKeyboardButton("Выйти в меню", callback_data='exit_without_saving')],
            ]
        )
        await query.message.reply_text(
            "Уверены ли вы, что хотите выйти? Потому что вы не сохранили изменения кнопкой 'Готово'.",
            reply_markup=keyboard
        )
        return States.CHANGE_QTY_CONFIRM_EXIT
    else:
        # В остальных случаях просто возвращаемся к показу остатка
        action = context.user_data.get('action')
        current_menu = context.user_data.get('current_menu', 'main_menu')

        if action:
            await show_balance(query, context, action, current_menu)
        else:
            keyboard = get_menu_keyboard('main_menu')
            await query.message.reply_text(menu['main_menu']['text'], reply_markup=keyboard)
        return ConversationHandler.END


async def save_and_exit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # Проверяем наличие всех необходимых данных
    required_data = ['selected_item_name', 'new_quantity', 'item_type', 'action']
    if not all(key in context.user_data for key in required_data):
        await query.message.reply_text(
            "Не удалось получить информацию о выбранном элементе.",
            reply_markup=back_to_menu_keyboard('main_menu')
        )
        return ConversationHandler.END

    # Если изменения еще не сохранены
    if not context.user_data.get('changes_saved'):
        item_name = context.user_data['selected_item_name']
        new_quantity = context.user_data['new_quantity']
        item_type = context.user_data['item_type']
        action = context.user_data['action']
        db = context.application.db

        # Определяем таблицу на основе item_type
        table_mapping = {
            'punches': 'Punches',
            'inserts': 'Inserts',
            'stampparts': 'Parts',
            'knives': 'Knives',
            'cams': 'Clamps',
            'discparts': 'Disc_Parts',
            'pushers': 'Pushers',
        }
        table = table_mapping.get(item_type)

        if not table:
            await query.message.reply_text(
                "Неизвестный тип элемента.",
                reply_markup=back_to_menu_keyboard('main_menu')
            )
            return ConversationHandler.END

        # Получаем stamp_id по action
        stamp_id = await get_stamp_id_by_action(action)
        if not stamp_id:
            await query.message.reply_text(
                "Штамп не найден.",
                reply_markup=back_to_menu_keyboard('main_menu')
            )
            return ConversationHandler.END

        # Обновляем количество в базе данных
        try:
            await db.execute(
                f"UPDATE {table} SET quantity = ? WHERE stamp_id = ? AND name = ?",
                (new_quantity, stamp_id, item_name),
            )
            await db.commit()
            await query.message.reply_text("Изменения успешно сохранены.")
        except Exception as e:
            logger.exception("Ошибка при обновлении базы данных: %s", e)
            await query.message.reply_text(
                "Ошибка при сохранении изменений.",
                reply_markup=back_to_menu_keyboard('main_menu')
            )
            return ConversationHandler.END

    # Возвращаемся к показу остатка
    action = context.user_data.get('action')
    current_menu = context.user_data.get('current_menu', 'main_menu')
    if action:
        await show_balance(query, context, action, current_menu)
    else:
        keyboard = get_menu_keyboard('main_menu')
        await query.message.reply_text(menu['main_menu']['text'], reply_markup=keyboard)
    return ConversationHandler.END

async def exit_without_saving(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # Возвращаемся к показу остатка
    action = context.user_data.get('action')
    current_menu = context.user_data.get('current_menu', 'main_menu')

    if action:
        await show_balance(query, context, action, current_menu)
    else:
        keyboard = get_menu_keyboard('main_menu')
        await query.message.reply_text(menu['main_menu']['text'], reply_markup=keyboard)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        # Если это CallbackQuery, подтверждаем его
        await update.callback_query.answer()
        await update.callback_query.message.reply_text('Действие отменено.')
    elif update.message:
        # Если это обычное сообщение
        await update.message.reply_text('Действие отменено.')
    else:
        # Если ни того, ни другого нет
        await update.effective_chat.send_message('Действие отменено.')
    return ConversationHandler.END

async def invalid_input_in_adjusting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Пожалуйста, используйте кнопки для изменения количества или нажмите 'Назад'."
    )
    return States.CHANGE_QTY_ADJUSTING_QUANTITY

async def invalid_input_in_choosing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Пожалуйста, введите название позиции, количество которой вы хотите изменить, или нажмите 'Назад'."
    )
    return States.CHANGE_QTY_CHOOSING_ITEM

async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("unknown_message called")
    await update.message.reply_text(
        "Пожалуйста, используйте кнопки меню для навигации или введите /start для возврата в главное меню."
    )