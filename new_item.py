from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode
from database import get_stamp_id_by_action
from menu import menu, create_inventory_submenus, inventory_list, get_menu_keyboard, back_to_menu_keyboard
import logging
import re
import sqlite3
from urllib.parse import urlparse
import validators
from constants import States

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def invalid_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> States:
    await update.message.reply_text(
        "Пожалуйста, введите корректные данные согласно инструкции или нажмите 'Назад' для возврата.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='go_back')]])
    )
    return States.ADD_ENTERING_DATA

async def add_new_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("add_new_item called")
    try:
        query = update.callback_query
        await query.answer()
        logger.info("Callback query answered.")

        action = query.data  # Получаем действие из callback_data
        logger.info(f"Action received: {action}")
        context.user_data['action'] = action  # Сохраняем действие для последующего использования

        # Сохраняем текущий путь меню для корректного возврата
        if 'menu_path' not in context.user_data:
            context.user_data['menu_path'] = ['main_menu']
        current_menu = context.user_data.get('current_menu', 'main_menu')
        context.user_data['menu_path'].append(current_menu)

        logger.info(f"Current menu path: {context.user_data['menu_path']}")

        # Извлекаем текущее меню или устанавливаем по умолчанию

        logger.info(f"Current menu: {current_menu}")

        # Создаём словарь для соответствия категорий и префиксов action
        category_prefixes = {
            'punches': 'addnewitempunches',
            'inserts': 'addnewiteminserts',
            'stampparts': 'addnewitemstampparts',
            'knives': 'addnewitemknives',
            'cams': 'addnewitemcams',
            'discparts': 'addnewitemdiscparts',
            'pushers': 'addnewitempushers',
        }

        # Ищем категорию, соответствующую action
        category = None
        inv_id = None
        for cat, prefix in category_prefixes.items():
            if action.startswith(prefix):
                category = cat
                inv_id = action[len(prefix):]  # Извлекаем inv_id из action
                logger.info(f"Category determined: {category}, inv_id: {inv_id}")
                break

        if category is None:
            # Если категория не определена, выводим сообщение об ошибке
            logger.warning(f"Unknown action: {action}")
            await query.message.reply_text(
                "🔴 Неизвестное действие. Пожалуйста, попробуйте ещё раз.",
                reply_markup=back_to_menu_keyboard(current_menu)
            )
            return ConversationHandler.END

        # Сохраняем категорию и inv_id в context.user_data для дальнейшего использования
        context.user_data['adding_category'] = category
        context.user_data['inv_id'] = inv_id

        # Шаблон инструкции для пользователя
        instruction_template = (
            "📥 **Введите данные для нового элемента, используя следующий формат:**\n\n"
            "`{fields}`\n\n"
            "Пример:\n""`{example}`"
        )

        # Кнопки для ввода данных - оставляем только кнопку "Назад"
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="go_back")]
        ]

        # Создаем разметку клавиатуры
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем сообщение с инструкцией и клавиатурой
        if category == 'punches':
            fields = "Имя, Количество, Тип(необязательно), Размер (необязательно), URL изображения (необязательно), Описание (необязательно)"
            example = "Пуансон A, 10, Тип B, Размер C, https://image.url, Описание"
        elif category == 'inserts':
            fields = "Имя, Количество, Размер(необязательно), Описание(необязательно)"
            example = "Вставка A, 5, Размер B, Описание"
        elif category == 'stampparts':
            fields = "Имя, Количество, Описание(необязательно)"
            example = "Запчасть A, 3, Описание"
        elif category == 'knives':
            fields = "Имя, Количество, Размер(необязательно), Описание(необязательно)"
            example = "Нож A, 7, Размер B, Описание"
        elif category == 'cams':
            fields = "Имя, Количество, Описание(необязательно)"
            example = "Кулачок A, 15, Описание"
        elif category == 'discparts':
            fields = "Имя, Количество, Описание(необязательно)"
            example = "Запчасть для диска A, 20, Описание"
        elif category == 'pushers':
            fields = "Имя, Количество, Размер(необязательно), Описание(необязательно)"
            example = "Толкатель A, 8, Размер B, Описание"
        else:
            # Неизвестная категория
            logger.warning(f"Unknown category: {category}")
            await query.message.reply_text(
                "🔴 Неизвестная категория. Пожалуйста, попробуйте ещё раз.",
                reply_markup=back_to_menu_keyboard(current_menu)
            )
            return ConversationHandler.END

        await query.message.reply_text(
            instruction_template.format(fields=fields, example=example),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        logger.info(f"Sent message for {category}.")

        return States.ADD_ENTERING_DATA

    except Exception as e:
        logger.exception("Exception in add_new_item")
        if 'query' in locals():
            await query.message.reply_text(
                "❗️ Произошла ошибка. Пожалуйста, попробуйте позже.",
                reply_markup=back_to_menu_keyboard(current_menu)
            )
        return ConversationHandler.END

MAX_NAME_LENGTH = 100
MAX_SIZE_LENGTH = 50
MAX_DESCRIPTION_LENGTH = 500
MAX_TYPE_LENGTH = 50
MAX_URL_LENGTH = 2000
MAX_QUANTITY = 10000

NAME_PATTERN = re.compile(r"^[A-Za-zА-Яа-я0-9\s\-_,\.]+$")

def get_category_table_name(category):
    category_tables = {
        'punches': 'Punches',
        'inserts': 'Inserts',
        'stampparts': 'Parts',
        'knives': 'Knives',
        'cams': 'Clamps',
        'discparts': 'Disc_Parts',
        'pushers': 'Pushers'
    }
    return category_tables.get(category)

async def handle_new_item_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Проверяем, является ли это callback query
    if update.callback_query:
        query = update.callback_query
        await query.answer()

        if query.data == 'go_back':
            await query.message.reply_text(
                "Действие отменено.",
                reply_markup=back_to_menu_keyboard(context.user_data.get('current_menu', 'main_menu'))
            )
            return ConversationHandler.END

        return States.ADD_ENTERING_DATA

    # Обработка текстового ввода
    if not update.message or not update.message.text:
        return States.ADD_ENTERING_DATA

    user_input = update.message.text.strip()
    category = context.user_data.get('adding_category')
    current_menu = context.user_data.get('current_menu')
    action = context.user_data.get('action')
    back_button = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='go_back')]])

    if not user_input:
        await update.message.reply_text(
            "Ошибка: Вы не ввели никаких данных.",
            reply_markup=back_button
        )
        return States.ADD_ENTERING_DATA

    if not category:
        await update.message.reply_text("Ошибка: Неизвестная категория. Повторите попытку.")
        return ConversationHandler.END

    data = [item.strip() for item in user_input.split(',')]

    if len(data) < 2:
        await update.message.reply_text(
            "Ошибка: Недостаточно данных. Пожалуйста, введите как минимум *Имя* и *Количество*.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_button
        )
        return States.ADD_ENTERING_DATA

    # Извлекаем и проверяем поля
    name = data[0].strip().capitalize()
    quantity_str = data[1].strip()

    # Проверка имени
    if len(name) > MAX_NAME_LENGTH:
        await update.message.reply_text(
            f"Ошибка: Имя не должно превышать {MAX_NAME_LENGTH} символов.",
            reply_markup=back_button
        )
        return States.ADD_ENTERING_DATA

    if not NAME_PATTERN.match(name):
        await update.message.reply_text(
            "Ошибка: Имя содержит недопустимые символы.",
            reply_markup=back_button
        )
        return States.ADD_ENTERING_DATA

    # Проверка количества
    try:
        quantity = int(quantity_str)
        if quantity < 0 or quantity > MAX_QUANTITY:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            f"Ошибка: Количество должно быть числом от 0 до {MAX_QUANTITY}.",
            reply_markup=back_button
        )
        return States.ADD_ENTERING_DATA

    # Получаем stamp_id
    stamp_id = await get_stamp_id_by_action(action)
    if not stamp_id:
        await update.message.reply_text(
            "Ошибка: Не удалось определить штамп.",
            reply_markup=back_to_menu_keyboard(current_menu)
        )
        return ConversationHandler.END

    db = context.application.db
    # Проверяем существование элемента с таким же именем
    category_table = get_category_table_name(category)
    if not category_table:
        await update.message.reply_text(
            "Ошибка: Не удалось определить таблицу для категории.",
            reply_markup=back_to_menu_keyboard(current_menu)
        )
        return ConversationHandler.END

    try:
        # Вставляем данные в базу
        if category == 'punches':
            type_ = data[2].strip() if len(data) > 2 else ''
            size = data[3].strip() if len(data) > 3 else ''
            image_url = data[4].strip() if len(data) > 4 else ''
            description = data[5].strip() if len(data) > 5 else ''

            await db.execute(
                "INSERT INTO Punches (stamp_id, name, quantity, type, size, image_url, description, last_modified) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', '+3 hours'))",
                (stamp_id, name, quantity, type_, size, image_url, description)
            )
            await db.commit()
            category_name = 'Пуансон'

        elif category == 'inserts':
            size = data[2].strip() if len(data) > 2 else ''
            description = data[3].strip() if len(data) > 3 else ''

            await db.execute(
                "INSERT INTO Inserts (stamp_id, name, quantity, size, description, last_modified) VALUES (?, ?, ?, ?, ?, datetime('now', '+3 hours'))",
                (stamp_id, name, quantity, size, description)
            )
            await db.commit()
            category_name = 'Вставка'

        elif category == 'stampparts':
            description = data[2].strip() if len(data) > 2 else ''

            await db.execute(
                "INSERT INTO Parts (stamp_id, name, quantity, description, last_modified) VALUES (?, ?, ?, ?, datetime('now', '+3 hours'))",
                (stamp_id, name, quantity, description)
            )
            await db.commit()
            category_name = 'Запчасть'

        elif category == 'knives':
            size = data[2].strip() if len(data) > 2 else ''
            description = data[3].strip() if len(data) > 3 else ''

            await db.execute(
                "INSERT INTO Knives (stamp_id, name, quantity, size, description, last_modified) VALUES (?, ?, ?, ?, ?, datetime('now', '+3 hours'))",
                (stamp_id, name, quantity, size, description)
            )
            await db.commit()
            category_name = 'Нож'

        elif category == 'cams':
            description = data[2].strip() if len(data) > 2 else ''

            await db.execute(
                "INSERT INTO Clamps (stamp_id, name, quantity, description, last_modified) VALUES (?, ?, ?, ?, datetime('now', '+3 hours'))",
                (stamp_id, name, quantity, description)
            )
            await db.commit()
            category_name = 'Кулачок'

        elif category == 'discparts':
            description = data[2].strip() if len(data) > 2 else ''

            await db.execute(
                "INSERT INTO Disc_Parts (stamp_id, name, quantity, description, last_modified) VALUES (?, ?, ?, ?, datetime('now', '+3 hours'))",
                (stamp_id, name, quantity, description)
            )
            await db.commit()
            category_name = 'Запчасть для дискового штампа'

        elif category == 'pushers':
            size = data[2].strip() if len(data) > 2 else ''
            description = data[3].strip() if len(data) > 3 else ''

            await db.execute(
                "INSERT INTO Pushers (stamp_id, name, quantity, size, description, last_modified) VALUES (?, ?, ?, ?, ?, datetime('now', '+3 hours'))",
                (stamp_id, name, quantity, size, description)
            )
            await db.commit()
            category_name = 'Толкатель'

        else:
            await update.message.reply_text(
                "Добавление для этой категории не реализовано."
            )
            return ConversationHandler.END

        await update.message.reply_text(
            f"✅ Новый {category_name} успешно добавлен!",
            reply_markup=back_to_menu_keyboard(current_menu)
        )
        return ConversationHandler.END

    except Exception as e:
        logger.exception("Exception during database insertion")
        await update.message.reply_text(
            "❗️ Произошла ошибка при добавлении в базу данных. Пожалуйста, попробуйте позже.",
            reply_markup=back_to_menu_keyboard(current_menu)
        )
        return ConversationHandler.END


async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # Получаем последнее меню из пути
    menu_path = context.user_data.get('menu_path', ['main_menu'])
    if len(menu_path) > 0:
        menu_path.pop()  # Удаляем текущее меню
        previous_menu = menu_path[-1] if menu_path else 'main_menu'
        context.user_data['current_menu'] = previous_menu
    else:
        previous_menu = 'main_menu'

    # Возвращаемся к предыдущему меню
    keyboard = get_menu_keyboard(previous_menu)
    await query.message.edit_text(
        text=menu[previous_menu]['text'],
        reply_markup=keyboard
    )
    return ConversationHandler.END