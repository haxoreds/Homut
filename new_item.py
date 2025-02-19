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
from change_quantity import go_back
import validators
from constants import States

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def invalid_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> States:
    await update.message.reply_text(
        "Пожалуйста, введите корректные данные согласно инструкции или нажмите 'Назад' для возврата.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='go_back')]])
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

        # Извлекаем текущее меню или устанавливаем по умолчанию
        current_menu = context.user_data.get('current_menu', 'main_menu')
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

        # Кнопки для ввода данных
        keyboard = []
        if category == 'punches':
            keyboard = [
                [InlineKeyboardButton("Пуансон A, 10, Тип B, Размер C", callback_data="Пуансон A, 10, Тип B, Размер C")],
                [InlineKeyboardButton("Пуансон B, 5", callback_data="Пуансон B, 5")],
                [InlineKeyboardButton("🔙 Назад", callback_data="go_back")]
            ]
        elif category == 'inserts':
            keyboard = [
                [InlineKeyboardButton("Вставка A, 5, Размер B", callback_data="Вставка A, 5, Размер B")],
                [InlineKeyboardButton("Вставка C, 3", callback_data="Вставка C, 3")],
                [InlineKeyboardButton("🔙 Назад", callback_data="go_back")]
            ]
        elif category == 'stampparts':
            keyboard = [
                [InlineKeyboardButton("Запчасть A, 3", callback_data="Запчасть A, 3")],
                [InlineKeyboardButton("Запчасть B, 2", callback_data="Запчасть B, 2")],
                [InlineKeyboardButton("🔙 Назад", callback_data="go_back")]
            ]
        elif category == 'knives':
            keyboard = [
                [InlineKeyboardButton("Нож A, 7, Размер B", callback_data="Нож A, 7, Размер B")],
                [InlineKeyboardButton("Нож C, 4", callback_data="Нож C, 4")],
                [InlineKeyboardButton("🔙 Назад", callback_data="go_back")]
            ]
        elif category == 'cams':
            keyboard = [
                [InlineKeyboardButton("Кулачок A, 15", callback_data="Кулачок A, 15")],
                [InlineKeyboardButton("Кулачок B, 10", callback_data="Кулачок B, 10")],
                [InlineKeyboardButton("🔙 Назад", callback_data="go_back")]
            ]
        elif category == 'discparts':
            keyboard = [
                [InlineKeyboardButton("Запчасть для диска A, 20", callback_data="Запчасть для диска A, 20")],
                [InlineKeyboardButton("Запчасть для диска B, 15", callback_data="Запчасть для диска B, 15")],
                [InlineKeyboardButton("🔙 Назад", callback_data="go_back")]
            ]
        elif category == 'pushers':
            keyboard = [
                [InlineKeyboardButton("Толкатель A, 8, Размер B", callback_data="Толкатель A, 8, Размер B")],
                [InlineKeyboardButton("Толкатель C, 6", callback_data="Толкатель C, 6")],
                [InlineKeyboardButton("🔙 Назад", callback_data="go_back")]
            ]

        # Создаем разметку клавиатуры
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем сообщение с инструкцией и клавиатурой
        if category == 'punches':
            fields = "Имя, Количество, Тип(необязательно), Размер (необязательно), URL изображения (необязательно), Описание (необязательно)"
            example = "Пуансон A, 10, Тип B, Размер C, https://image.url, Описание"
            await query.message.reply_text(
                instruction_template.format(fields=fields, example=example),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            logger.info("Sent message for punches.")
        elif category == 'inserts':
            fields = "Имя, Количество, Размер(необязательно), Описание(необязательно)"
            example = "Вставка A, 5, Размер B, Описание"
            await query.message.reply_text(
                instruction_template.format(fields=fields, example=example),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            logger.info("Sent message for inserts.")
        elif category == 'stampparts':
            fields = "Имя, Количество, Описание(необязательно)"
            example = "Запчасть A, 3, Описание"
            await query.message.reply_text(
                instruction_template.format(fields=fields, example=example),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            logger.info("Sent message for stampparts.")
        elif category == 'knives':
            fields = "Имя, Количество, Размер(необязательно), Описание(необязательно)"
            example = "Нож A, 7, Размер B, Описание"
            await query.message.reply_text(
                instruction_template.format(fields=fields, example=example),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            logger.info("Sent message for knives.")
        elif category == 'cams':
            fields = "Имя, Количество, Описание(необязательно)"
            example = "Кулачок A, 15, Описание"
            await query.message.reply_text(
                instruction_template.format(fields=fields, example=example),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            logger.info("Sent message for cams.")
        elif category == 'discparts':
            fields = "Имя, Количество, Описание(необязательно)"
            example = "Запчасть для диска A, 20, Описание"
            await query.message.reply_text(
                instruction_template.format(fields=fields, example=example),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            logger.info("Sent message for discparts.")
        elif category == 'pushers':
            fields = "Имя, Количество, Размер(необязательно), Описание(необязательно)"
            example = "Толкатель A, 8, Размер B, Описание"
            await query.message.reply_text(
                instruction_template.format(fields=fields, example=example),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            logger.info("Sent message for pushers.")
        else:
            # Неизвестная категория
            logger.warning(f"Unknown category: {category}")
            await query.message.reply_text(
                "🔴 Неизвестная категория. Пожалуйста, попробуйте ещё раз.",
                reply_markup=back_to_menu_keyboard(current_menu)
            )
            return ConversationHandler.END

        logger.info("Returning States.ADD_ENTERING_DATA")
        return States.ADD_ENTERING_DATA  # Переходим в состояние ожидания ввода данных

    except Exception as e:
        logger.exception("Exception in add_new_item")
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
    query = update.callback_query
    await query.answer()

    user_input = query.data.strip()
    category = context.user_data.get('adding_category')
    current_menu = context.user_data.get('current_menu')
    action = context.user_data.get('action')
    db = context.application.db
    back_button = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='go_back')]])

    if user_input == 'go_back':
        await query.message.reply_text(
            "Действие отменено.",
            reply_markup=back_to_menu_keyboard(current_menu)
        )
        return ConversationHandler.END

    if not user_input:
        await query.message.reply_text(
            "Ошибка: Вы не ввели никаких данных. Пожалуйста, выберите один из предложенных вариантов.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='go_back')]])
        )
        return States.ADD_ENTERING_DATA

    if not category:
        await query.message.reply_text("Ошибка: Неизвестная категория. Повторите попытку.")
        return ConversationHandler.END

    data = [item.strip() for item in user_input.split(',')]

    if len(data) < 2:
        await query.message.reply_text(
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
        await query.message.reply_text(
            f"Ошибка: Имя не должно превышать {MAX_NAME_LENGTH} символов.",
            reply_markup=back_button
        )
        return States.ADD_ENTERING_DATA
    if not NAME_PATTERN.match(name):
        await query.message.reply_text(
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
        await query.message.reply_text(
            f"Ошибка: Количество должно быть числом от 0 до {MAX_QUANTITY}. Пожалуйста, введите данные заново.",
            reply_markup=back_button
        )
        return States.ADD_ENTERING_DATA

    # Обработка необязательных полей
    optional_data = data[2:]

    # Инициализация полей
    type_ = ''
    size = ''
    image_url = ''
    description = ''

    # Извлечение дополнительных данных в зависимости от категории
    if category == 'punches':
        # Ожидаемые поля: type, size, image_url, description
        if len(optional_data) >= 1:
            type_ = optional_data[0].strip()
            if len(type_) > MAX_TYPE_LENGTH:
                await query.message.reply_text(
                    f"Ошибка: Тип не должен превышать {MAX_TYPE_LENGTH} символов.",
                    reply_markup=back_button
                )
                return States.ADD_ENTERING_DATA
        if len(optional_data) >= 2:
            size = optional_data[1].strip()
            if len(size) > MAX_SIZE_LENGTH:
                await query.message.reply_text(
                    f"Ошибка: Размер не должен превышать {MAX_SIZE_LENGTH} символов.",
                    reply_markup=back_button
                )
                return States.ADD_ENTERING_DATA
        if len(optional_data) >= 3:
            image_url = optional_data[2].strip()
            if len(image_url) > MAX_URL_LENGTH or not validators.url(image_url):
                await query.message.reply_text(
                    "Ошибка: Введите корректный URL изображения.",
                    reply_markup=back_button
                )
                return States.ADD_ENTERING_DATA
        if len(optional_data) >= 4:
            description = optional_data[3].strip()
            if len(description) > MAX_DESCRIPTION_LENGTH:
                await query.message.reply_text(
                    f"Ошибка: Описание не должно превышать {MAX_DESCRIPTION_LENGTH} символов.",
                    reply_markup=back_button
                )
                return States.ADD_ENTERING_DATA

    elif category == 'inserts':
        # Ожидаемые поля: size, description
        if len(optional_data) >= 1:
            size = optional_data[0].strip()
            if len(size) > MAX_SIZE_LENGTH:
                await query.message.reply_text(
                    f"Ошибка: Размер не должен превышать {MAX_SIZE_LENGTH} символов.",
                    reply_markup=back_button
                )
                return States.ADD_ENTERING_DATA
        if len(optional_data) >= 2:
            description = optional_data[1].strip()
            if len(description) > MAX_DESCRIPTION_LENGTH:
                await query.message.reply_text(
                    f"Ошибка: Описание не должно превышать {MAX_DESCRIPTION_LENGTH} символов.",
                    reply_markup=back_button
                )
                return States.ADD_ENTERING_DATA

    elif category == 'stampparts':
        # Ожидаемые поля: description
        if len(optional_data) >= 1:
            description = optional_data[0].strip()
            if len(description) > MAX_DESCRIPTION_LENGTH:
                await query.message.reply_text(
                    f"Ошибка: Описание не должно превышать {MAX_DESCRIPTION_LENGTH} символов.",
                    reply_markup=back_button
                )
                return States.ADD_ENTERING_DATA

    elif category == 'knives':
        # Ожидаемые поля: size, description
        if len(optional_data) >= 1:
            size = optional_data[0].strip()
            if len(size) > MAX_SIZE_LENGTH:
                await query.message.reply_text(
                    f"Ошибка: Размер не должен превышать {MAX_SIZE_LENGTH} символов.",
                    reply_markup=back_button
                )
                return States.ADD_ENTERING_DATA
        if len(optional_data) >= 2:
            description = optional_data[1].strip()
            if len(description) > MAX_DESCRIPTION_LENGTH:
                await query.message.reply_text(
                    f"Ошибка: Описание не должно превышать {MAX_DESCRIPTION_LENGTH} символов.",
                    reply_markup=back_button
                )
                return States.ADD_ENTERING_DATA

    elif category == 'cams':
        # Ожидаемые поля: description
        if len(optional_data) >= 1:
            description = optional_data[0].strip()
            if len(description) > MAX_DESCRIPTION_LENGTH:
                await query.message.reply_text(
                    f"Ошибка: Описание не должно превышать {MAX_DESCRIPTION_LENGTH} символов.",
                    reply_markup=back_button
                )
                return States.ADD_ENTERING_DATA

    elif category == 'discparts':
        # Ожидаемые поля: description
        if len(optional_data) >= 1:
            description = optional_data[0].strip()
            if len(description) > MAX_DESCRIPTION_LENGTH:
                await query.message.reply_text(
                    f"Ошибка: Описание не должно превышать {MAX_DESCRIPTION_LENGTH} символов.",
                    reply_markup=back_button
                )
                return States.ADD_ENTERING_DATA

    elif category == 'pushers':
        # Ожидаемые поля: size, description
        if len(optional_data) >= 1:
            size = optional_data[0].strip()
            if len(size) > MAX_SIZE_LENGTH:
                await query.message.reply_text(
                    f"Ошибка: Размер не должен превышать {MAX_SIZE_LENGTH} символов.",
                    reply_markup=back_button
                )
                return States.ADD_ENTERING_DATA
        if len(optional_data) >= 2:
            description = optional_data[1].strip()
            if len(description) > MAX_DESCRIPTION_LENGTH:
                await query.message.reply_text(
                    f"Ошибка: Описание не должно превышать {MAX_DESCRIPTION_LENGTH} символов.",
                    reply_markup=back_button
                )
                return States.ADD_ENTERING_DATA

    else:
        await query.message.reply_text(
            "Добавление для этой категории не реализовано.",
            reply_markup=back_to_menu_keyboard(current_menu)
        )
        return ConversationHandler.END

    # Получаем stamp_id
    stamp_id = await get_stamp_id_by_action(action)
    if not stamp_id:
        await query.message.reply_text(
            "Ошибка: Не удалось определить штамп.",
            reply_markup=back_to_menu_keyboard(current_menu)
        )
        return ConversationHandler.END

    # Проверяем, существует ли элемент с таким же именем (без учета регистра)
    category_table = get_category_table_name(category)
    if not category_table:
        await query.message.reply_text(
            "Ошибка: Не удалось определить таблицу для категории.",
            reply_markup=back_to_menu_keyboard(current_menu)
        )
        return ConversationHandler.END

    cursor = await db.execute(
        f"SELECT id FROM {category_table} WHERE LOWER(name) = LOWER(?) AND stamp_id = ?",
        (name.lower(), stamp_id)
    )
    existing_item = await cursor.fetchone()

    if existing_item:
        await query.message.reply_text(
            "Ошибка: Элемент с таким именем уже существует. Пожалуйста, введите уникальное имя.",
            reply_markup=back_button
        )
        return States.ADD_ENTERING_DATA

    # Вставляем данные в базу
    try:
        if category == 'punches':
            await db.execute(
                "INSERT INTO Punches (stamp_id, type, name, size, quantity, image_url, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (stamp_id, type_, name, size, quantity, image_url, description)
            )
            await db.commit()
            category_name = 'Пуансон'

        elif category == 'inserts':
            await db.execute(
                "INSERT INTO Inserts (stamp_id, name, quantity, size, description, type) VALUES (?, ?, ?, ?, ?, ?)",
                (stamp_id, name, quantity, size, description, '')
            )
            await db.commit()
            category_name = 'Вставка'

        elif category == 'stampparts':
            await db.execute(
                "INSERT INTO Parts (stamp_id, name, quantity, description) VALUES (?, ?, ?, ?)",
                (stamp_id, name, quantity, description)
            )
            await db.commit()
            category_name = 'Запчасть'

        elif category == 'knives':
            await db.execute(
                "INSERT INTO Knives (stamp_id, name, quantity, size, description) VALUES (?, ?, ?, ?, ?)",
                (stamp_id, name, quantity, size, description)
            )
            await db.commit()
            category_name = 'Нож'

        elif category == 'cams':
            await db.execute(
                "INSERT INTO Clamps (stamp_id, name, quantity, description) VALUES (?, ?, ?, ?)",
                (stamp_id, name, quantity, description)
            )
            await db.commit()
            category_name = 'Кулачок'

        elif category == 'discparts':
            await db.execute(
                "INSERT INTO Disc_Parts (stamp_id, name, quantity, description) VALUES (?, ?, ?, ?)",
                (stamp_id, name, quantity, description)
            )
            await db.commit()
            category_name = 'Запчасть для дискового штампа'

        elif category == 'pushers':
            await db.execute(
                "INSERT INTO Pushers (stamp_id, name, quantity, size, description) VALUES (?, ?, ?, ?, ?)",
                (stamp_id, name, quantity, size, description)
            )
            await db.commit()
            category_name = 'Толкатель'

        else:
            await query.message.reply_text(
                "Добавление для этой категории не реализовано."
            )
            return ConversationHandler.END

    except Exception as e:
        logger.exception("Exception during database insertion")
        await query.message.reply_text(
            "❗️ Произошла ошибка при добавлении в базу данных. Пожалуйста, попробуйте позже.",
            reply_markup=back_to_menu_keyboard(current_menu)
        )
        return ConversationHandler.END

    await query.message.reply_text(
        f"✅ Новый {category_name} успешно добавлен!",
        reply_markup=back_to_menu_keyboard(current_menu)
    )
    return ConversationHandler.END