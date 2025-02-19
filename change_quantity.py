from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import re
import logging  
from menu import menu, create_inventory_submenus, inventory_list, get_menu_keyboard, back_to_menu_keyboard
from database import get_stamp_id_by_action
from showballance import show_balance
from constants import States
logger = logging.getLogger(__name__)



# Функция для создания клавиатуры изменения количества
def get_adjust_quantity_keyboard():
    return InlineKeyboardMarkup(
        [
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
        ]
    )

async def change_quantity_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    callback_data = query.data

    # Используем обновлённое регулярное выражение
    match = re.match(r'^changequantity([a-z]+)([\w_]+)$', callback_data)
    if match:
        item_type = match.group(1)
        inv_id = match.group(2)

        context.user_data['item_type'] = item_type
        context.user_data['inv_id'] = inv_id
        context.user_data['action'] = callback_data  # Сохраняем action в user_data
        await query.message.reply_text(
            "Пожалуйста, введите название позиции, количество которой вы хотите изменить:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Отмена", callback_data='cancel')]]
            )
        )
        return States.CHANGE_QTY_CHOOSING_ITEM
    else:
        await query.message.reply_text(
            "Некорректные данные, попробуйте снова.", reply_markup=back_to_menu_keyboard('main_menu')
        )
        return ConversationHandler.END

async def item_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    item_name = update.message.text.strip()
    logger.info(f"Entering item_name_received")
    logger.info(f"User input: {item_name}")

    item_type = context.user_data.get('item_type')
    inv_id = context.user_data.get('inv_id')
    action = context.user_data.get('action')
    logger.info(f"Item type: {item_type}")
    logger.info(f"Inventory ID: {inv_id}")

    db = context.application.db
    if not item_type or not inv_id or not action:
        await update.message.reply_text("Не удалось определить тип элемента или идентификатор инвентаря.")
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
        await update.message.reply_text("Неизвестный тип элемента.")
        return ConversationHandler.END

    # Получаем stamp_id по action
    stamp_id = await get_stamp_id_by_action(action)
    if not stamp_id:
        await update.message.reply_text("Штамп не найден.")
        return ConversationHandler.END

    # Получаем текущее количество из базы данных
    try:
        async with db.execute(
            f"SELECT quantity FROM {table} WHERE stamp_id = ? AND name = ?",
            (stamp_id, item_name),
        ) as cursor:
            result = await cursor.fetchone()
            if result:
                current_quantity = result[0]
                logger.info(f"Current quantity retrieved: {current_quantity}")
            else:
                # Элемент не найден, предлагаем повторить ввод
                await update.message.reply_text(
                    f"Элемент '{item_name}' не найден в базе данных.\n"
                    "Пожалуйста, проверьте корректность названия и попробуйте снова.",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Назад", callback_data='go_back')]]
                    )
                )
                return States.CHANGE_QTY_CHOOSING_ITEM  # Остаёмся в том же состоянии для повторного ввода
    except Exception as e:
        logger.exception("Ошибка при получении текущего количества: %s", e)
        await update.message.reply_text("Ошибка при получении данных из базы.")
        return ConversationHandler.END

    context.user_data['selected_item_name'] = item_name
    context.user_data['current_quantity'] = current_quantity
    context.user_data['new_quantity'] = current_quantity
    context.user_data['changes_saved'] = False  # Инициализируем флаг

    # Создаем клавиатуру для изменения количества
    keyboard = get_adjust_quantity_keyboard()

    # Отправляем пользователю сообщение с возможностью изменить количество
    await update.message.reply_text(
        f"Текущее количество для {item_name}: {current_quantity}\nВыберите действие:",
        reply_markup=keyboard
    )

    return States.CHANGE_QTY_ADJUSTING_QUANTITY


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
    except telegram.error.BadRequest as e:
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
        return CHANGE_QTY_ADJUSTING_QUANTITY  # Остаёмся в текущем состоянии

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

    # Обновляем количество в базе данных
    try:
        await db.execute(
            f"UPDATE {table} SET quantity = ? WHERE stamp_id = ? AND name = ?",
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

    # Проверяем, были ли сохранены изменения
    if not context.user_data.get('changes_saved', False):
        # Пользователь не сохранил изменения, выводим сообщение с подтверждением
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
        return States.CHANGE_QTY_CONFIRM_EXIT  # Переходим в состояние подтверждения выхода
    else:
        # Если изменения сохранены, возвращаемся к показу остатка
        action = context.user_data.get('action')
        current_menu = context.user_data.get('current_menu')
        if action and current_menu:
            await show_balance(query, context, action, current_menu)
        else:
            # Если отсутствуют необходимые данные, можно вернуть в главное меню или вывести сообщение
            await query.message.reply_text("Не удалось вернуться к показу остатка.")
            keyboard = get_menu_keyboard('main_menu')
            await query.message.reply_text(menu['main_menu']['text'], reply_markup=keyboard)
        return ConversationHandler.END


async def save_and_exit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Эквивалентно нажатию кнопки 'Готово'
    query = update.callback_query
    await query.answer()

    # Проверяем, были ли уже сохранены изменения
    if not context.user_data.get('changes_saved'):
        # Сохраняем изменения
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

        # Обновляем количество в базе данных
        try:
            await db.execute(
                f"UPDATE {table} SET quantity = ? WHERE stamp_id = ? AND name = ?",
                (new_quantity, stamp_id, item_name),
            )
            await db.commit()
        except Exception as e:
            logger.exception("Ошибка при обновлении базы данных: %s", e)
            await query.message.reply_text("Ошибка при обновлении данных.")
            return ConversationHandler.END

        # Устанавливаем флаг, что изменения сохранены
        context.user_data['changes_saved'] = True

        await query.message.reply_text("Успешно сохранено.")
    else:
        await query.message.reply_text("Изменения уже были сохранены ранее.")

    # Возвращаемся к показу остатка
    action = context.user_data.get('action')
    current_menu = context.user_data.get('current_menu')
    if action and current_menu:
        await show_balance(query, context, action, current_menu)
    else:
        await query.message.reply_text("Не удалось вернуться к показу остатка.")
        keyboard = get_menu_keyboard('main_menu')
        await query.message.reply_text(menu['main_menu']['text'], reply_markup=keyboard)
    return ConversationHandler.END

async def exit_without_saving(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # Сбрасываем новое количество к исходному
    context.user_data['new_quantity'] = context.user_data['current_quantity']

    await query.message.reply_text("Изменения не сохранены.")

    # Возвращаемся к показу остатка
    action = context.user_data.get('action')
    current_menu = context.user_data.get('current_menu')
    if action and current_menu:
        await show_balance(query, context, action, current_menu)
    else:
        await query.message.reply_text("Не удалось вернуться к показу остатка.")
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

                                    
