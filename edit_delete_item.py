"""
Edit/Delete Module - Модуль редактирования и удаления элементов
==================================================

Этот модуль обеспечивает функциональность для редактирования и удаления элементов в инвентаре.
Основные возможности:
- Выбор элемента для редактирования или удаления
- Редактирование различных полей элементов (название, количество, тип и т.д.)
- Безопасное удаление элементов с подтверждением
- Обработка отмены операций

Процесс работы:
1. Выбор действия (редактирование/удаление)
2. Выбор конкретного элемента
3. Для редактирования - выбор поля и ввод нового значения
4. Для удаления - подтверждение операции
5. Сохранение изменений в базе данных

Особенности реализации:
- Использует States для управления процессом
- Обеспечивает безопасное обновление базы данных
- Поддерживает отмену операций на любом этапе
"""

import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging
from constants import States
from menu import back_to_menu_keyboard, menu, get_menu_keyboard
from database import get_stamp_id_by_action

logger = logging.getLogger(__name__)

async def show_edit_delete_menu_old(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """This function is now obsolete and will be removed in future versions."""
    return ConversationHandler.END

async def show_edit_delete_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Показывает меню выбора между редактированием и удалением элемента.

    Параметры:
    - update (Update): Объект обновления от Telegram
    - context (ContextTypes.DEFAULT_TYPE): Контекст бота

    Возвращает:
    - int: Новое состояние диалога (States.EDIT_DELETE_SELECT_ACTION или ConversationHandler.END)

    Действия:
    1. Обрабатывает callback запрос
    2. Проверяет валидность действия
    3. Создает клавиатуру с опциями редактирования/удаления
    4. Отображает меню выбора действия
    """
    query = update.callback_query
    if query:
        await query.answer()
        if query.data == "back":
            # При возврате из меню редактирования/удаления
            current_menu = context.user_data.get('current_menu', 'main_menu')
            keyboard = get_menu_keyboard(current_menu)
            await query.message.edit_text(
                menu[current_menu]['text'],
                reply_markup=keyboard
            )
            return ConversationHandler.END
        else:
            action = query.data
            context.user_data['edit_action'] = action
    else:
        action = context.user_data.get('edit_action')

    if not action or not action.startswith('editdelete'):
        logger.error(f"Invalid action for edit/delete menu: {action}")
        return ConversationHandler.END

    current_menu = context.user_data.get('current_menu', 'main_menu')

    # Создаем клавиатуру с кнопками выбора действия
    keyboard = [
        [
            InlineKeyboardButton("✏️ Изменить", callback_data="select_edit"),
            InlineKeyboardButton("🗑 Удалить", callback_data="select_delete")
        ],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back")]
    ]

    message = query.message if query else update.message
    try:
        await message.edit_text(
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception:
        await message.reply_text(
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    return States.EDIT_DELETE_SELECT_ACTION

async def handle_action_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает выбор действия (редактирование или удаление).

    Параметры:
    - update (Update): Объект обновления от Telegram
    - context (ContextTypes.DEFAULT_TYPE): Контекст бота

    Возвращает:
    - int: Новое состояние диалога (States.EDIT_DELETE_CHOOSING или ConversationHandler.END)

    Процесс:
    1. Получает выбранное действие из callback
    2. Определяет категорию и ID штампа
    3. Получает список элементов из соответствующей таблицы
    4. Создает клавиатуру для выбора конкретного элемента
    """
    query = update.callback_query
    await query.answer()

    if query.data == "back":
        current_menu = context.user_data.get('current_menu', 'main_menu')
        await query.message.edit_text(
            "Операция отменена.",
            reply_markup=back_to_menu_keyboard(current_menu)
        )
        return ConversationHandler.END

    action = context.user_data.get('edit_action')
    if not action:
        await query.message.edit_text(
            "Ошибка: Не удалось определить действие.",
            reply_markup=back_to_menu_keyboard('main_menu')
        )
        return ConversationHandler.END

    selected_action = query.data
    context.user_data['selected_action'] = selected_action

    # Извлекаем категорию и получаем stamp_id
    category_match = re.match(r'^editdelete([a-z]+).*$', action)
    if not category_match:
        await query.message.edit_text(
            "Ошибка: Неверный формат действия.",
            reply_markup=back_to_menu_keyboard('main_menu')
        )
        return ConversationHandler.END

    category = category_match.group(1)
    stamp_id = await get_stamp_id_by_action(action)

    if not stamp_id:
        await query.message.edit_text(
            "Ошибка: Не удалось определить штамп.",
            reply_markup=back_to_menu_keyboard('main_menu')
        )
        return ConversationHandler.END

    # Определяем таблицу и получаем данные
    table_mapping = {
        'punches': ('Punches', 'Пуансоны'),
        'inserts': ('Inserts', 'Вставки'),
        'stampparts': ('Parts', 'Запчасти'),
        'knives': ('Knives', 'Ножи'),
        'cams': ('Clamps', 'Кулачки'),
        'discparts': ('Disc_Parts', 'Запчасти для дисков'),
        'pushers': ('Pushers', 'Толкатели')
    }

    table_info = table_mapping.get(category)
    if not table_info:
        await query.message.edit_text(
            "Ошибка: Неизвестная категория.",
            reply_markup=back_to_menu_keyboard('main_menu')
        )
        return ConversationHandler.END

    table_name, category_name = table_info
    context.user_data['edit_table'] = table_name

    try:
        db = context.application.db
        async with db.execute(
            f"SELECT * FROM {table_name} WHERE stamp_id = ?",
            (stamp_id,)
        ) as cursor:
            items = await cursor.fetchall()
            column_names = [description[0] for description in cursor.description]

        if not items:
            await query.message.edit_text(
                f"В категории {category_name} нет данных.",
                reply_markup=back_to_menu_keyboard('main_menu')
            )
            return ConversationHandler.END

        message_text = f"📋 Данные в категории {category_name}:\n\n"
        keyboard = []

        for item in items:
            item_dict = dict(zip(column_names, item))
            item_id = item_dict['id']

            item_text = f"🔹 {item_dict['name']}\n"
            if 'quantity' in item_dict:
                item_text += f"   Количество: {item_dict['quantity']}\n"
            if 'type' in item_dict and item_dict['type']:
                item_text += f"   Тип: {item_dict['type']}\n"
            if 'size' in item_dict and item_dict['size']:
                item_text += f"   Размер: {item_dict['size']}\n"
            if 'description' in item_dict and item_dict['description']:
                item_text += f"   Описание: {item_dict['description']}\n"

            message_text += f"\n{item_text}"

            if selected_action == "select_edit":
                keyboard.append([
                    InlineKeyboardButton(
                        f"✏️ Изменить {item_dict['name']}",
                        callback_data=f"edit_{item_id}"
                    )
                ])
            else:  # select_delete
                keyboard.append([
                    InlineKeyboardButton(
                        f"🗑 Удалить {item_dict['name']}",
                        callback_data=f"delete_{item_id}"
                    )
                ])

        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])

        await query.message.edit_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return States.EDIT_DELETE_CHOOSING

    except Exception as e:
        logger.exception("Ошибка при получении данных из базы")
        await query.message.edit_text(
            "Произошла ошибка при получении данных.",
            reply_markup=back_to_menu_keyboard('main_menu')
        )
        return ConversationHandler.END

async def handle_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает подтверждение удаления элемента.

    Параметры:
    - update (Update): Объект обновления от Telegram
    - context (ContextTypes.DEFAULT_TYPE): Контекст бота

    Возвращает:
    - int: Новое состояние диалога

    Процесс:
    1. Проверяет наличие необходимых данных
    2. Выполняет удаление из базы данных
    3. Отправляет подтверждение пользователю
    4. Обрабатывает возможные ошибки
    """
    query = update.callback_query
    await query.answer()

    if query.data == "back":
        return await show_edit_delete_menu(update, context)

    try:
        table_name = context.user_data.get('edit_table')
        item_id = context.user_data.get('edit_item_id')

        if not all([table_name, item_id]):
            raise ValueError("Could not get data for deletion")

        db = context.application.db
        await db.execute(f"DELETE FROM {table_name} WHERE id = ?", (item_id,))
        await db.commit()

        current_menu = context.user_data.get('current_menu', 'main_menu')
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад в меню", callback_data="back")
        ]])

        await query.message.reply_text(
            "✅ Элемент успешно удален.",
            reply_markup=keyboard
        )

        return States.EDIT_DELETE_CHOOSING

    except Exception as e:
        logger.exception("Error during deletion")
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад в меню", callback_data="back")
        ]])
        await query.message.reply_text(
            "Произошла ошибка при удалении элемента.",
            reply_markup=keyboard
        )
        return States.EDIT_DELETE_CHOOSING

async def handle_edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ввод нового значения при редактировании.

    Параметры:
    - update (Update): Объект обновления от Telegram
    - context (ContextTypes.DEFAULT_TYPE): Контекст бота

    Возвращает:
    - int: Новое состояние диалога

    Особенности:
    - Проверяет валидность введенного значения
    - Для количества проверяет, что значение положительное
    - Сохраняет изменения в базе данных
    - Отправляет подтверждение об успешном обновлении
    """
    if not update.message:
        return States.EDIT_ENTERING_VALUE

    try:
        new_value = update.message.text.strip()
        field = context.user_data.get('edit_field')
        table_name = context.user_data.get('edit_table')
        item_id = context.user_data.get('edit_item_id')

        if not all([field, table_name, item_id]):
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад в меню", callback_data="back")
            ]])
            await update.message.reply_text(
                "Ошибка: Не удалось получить данные для редактирования.",
                reply_markup=keyboard
            )
            return States.EDIT_DELETE_CHOOSING

        if field == 'quantity':
            try:
                new_value = int(new_value)
                if new_value < 0:
                    raise ValueError
            except ValueError:
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад в меню", callback_data="back")
                ]])
                await update.message.reply_text(
                    "Ошибка: Количество должно быть положительным целым числом.",
                    reply_markup=keyboard
                )
                return States.EDIT_ENTERING_VALUE

        db = context.application.db
        await db.execute(
            f"UPDATE {table_name} SET {field} = ? WHERE id = ?",
            (new_value, item_id)
        )
        await db.commit()

        current_menu = context.user_data.get('current_menu', 'main_menu')
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад в меню", callback_data="back")
        ]])

        await update.message.reply_text(
            "✅ Значение успешно обновлено.",
            reply_markup=keyboard
        )

        return States.EDIT_DELETE_CHOOSING

    except Exception as e:
        logger.exception("Error updating value")
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад в меню", callback_data="back")
        ]])
        await update.message.reply_text(
            "Произошла ошибка при обновлении значения.",
            reply_markup=keyboard
        )
        return States.EDIT_DELETE_CHOOSING

async def handle_edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает выбор элемента для редактирования.

    Параметры:
    - update (Update): Объект обновления от Telegram
    - context (ContextTypes.DEFAULT_TYPE): Контекст бота

    Возвращает:
    - int: Новое состояние диалога (States.EDIT_CHOOSING_FIELD или States.DELETE_CONFIRM)

    Процесс:
    1. Получает ID выбранного элемента
    2. Определяет тип действия (редактирование/удаление)
    3. Получает данные элемента из базы
    4. Создает соответствующую клавиатуру для следующего шага
    """
    query = update.callback_query
    await query.answer()

    if query.data == "back":
        return await show_edit_delete_menu(update, context)

    try:
        item_id = int(query.data.split('_')[1])
        action = 'edit' if query.data.startswith('edit_') else 'delete'
        context.user_data['edit_item_id'] = item_id
        context.user_data['edit_type'] = action

        table_name = context.user_data.get('edit_table')
        if not table_name:
            await query.message.reply_text(
                "Ошибка: Не удалось определить таблицу.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад в меню", callback_data="back")
                ]])
            )
            return States.EDIT_DELETE_CHOOSING

        db = context.application.db
        async with db.execute(
            f"SELECT * FROM {table_name} WHERE id = ?",
            (item_id,)
        ) as cursor:
            item = await cursor.fetchone()
            if not item:
                await query.message.reply_text(
                    "Элемент не найден.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад в меню", callback_data="back")
                    ]])
                )
                return States.EDIT_DELETE_CHOOSING

            column_names = [description[0] for description in cursor.description]
            item_dict = dict(zip(column_names, item))

            if action == 'edit':
                keyboard = []
                editable_fields = ['name', 'quantity', 'type', 'size', 'description']

                for field in editable_fields:
                    if field in item_dict:
                        current_value = item_dict[field] or 'Не задано'
                        keyboard.append([
                            InlineKeyboardButton(
                                f"Изменить {field} (текущее: {current_value})",
                                callback_data=f"edit_field_{field}"
                            )
                        ])

                keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="back")])

                await query.message.reply_text(
                    f"Выберите поле для редактирования:\n",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return States.EDIT_CHOOSING_FIELD

            else:  # delete
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Да, удалить", callback_data="confirm_delete"),
                        InlineKeyboardButton("❌ Нет, отменить", callback_data="back")
                    ]
                ]

                await query.message.reply_text(
                    f"Вы уверены, что хотите удалить {item_dict['name']}?",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return States.DELETE_CONFIRM

    except Exception as e:
        logger.exception("Ошибка при обработке выбора")
        await query.message.reply_text(
            "Произошла ошибка при обработке запроса.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад в меню", callback_data="back")
            ]])
        )
        return States.EDIT_DELETE_CHOOSING

async def handle_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает выбор поля для редактирования.

    Параметры:
    - update (Update): Объект обновления от Telegram
    - context (ContextTypes.DEFAULT_TYPE): Контекст бота

    Возвращает:
    - int: Новое состояние диалога (States.EDIT_ENTERING_VALUE)

    Особенности:
    - Сохраняет выбранное поле в контексте
    - Отображает подсказку в зависимости от типа поля
    - Поддерживает различные типы полей (название, количество, тип, размер, описание)
    """
    query = update.callback_query
    await query.answer()

    if query.data == "back":
        return await show_edit_delete_menu(update, context)

    field = query.data.split('_')[2]
    context.user_data['edit_field'] = field

    field_descriptions = {
        'name': 'название',
        'quantity': 'количество (целое число)',
        'type': 'тип',
        'size': 'размер',
        'description': 'описание'
    }

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Назад в меню", callback_data="back")
    ]])

    await query.message.reply_text(
        f"Введите новое {field_descriptions.get(field, field)}:",
        reply_markup=keyboard
    )

    return States.EDIT_ENTERING_VALUE

async def handle_exit_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает варианты выхода при несохраненных изменениях.

    Параметры:
    - update (Update): Объект обновления от Telegram
    - context (ContextTypes.DEFAULT_TYPE): Контекст бота

    Возвращает:
    - int: Новое состояние диалога (ConversationHandler.END)

    Действия:
    1. При выборе сохранения - сохраняет изменения в базе
    2. При выборе выхода без сохранения - отменяет изменения
    3. В обоих случаях возвращает пользователя в предыдущее меню
    """
    query = update.callback_query
    await query.answer()

    if query.data == "save_exit":
        try:
            field = context.user_data.get('edit_field')
            new_value = context.user_data.get('new_value')
            table_name = context.user_data.get('edit_table')
            item_id = context.user_data.get('edit_item_id')

            if all([field, new_value, table_name, item_id]):
                db = context.application.db
                await db.execute(
                    f"UPDATE {table_name} SET {field} = ? WHERE id = ?",
                    (new_value, item_id)
                )
                await db.commit()

                await query.message.reply_text(
                    "✅ Изменения сохранены.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад в меню", callback_data="back")
                    ]])
                )

            return ConversationHandler.END

        except Exception as e:
            logger.exception("Ошибка при сохранении изменений")
            await query.message.reply_text(
                "Произошла ошибка при сохранении изменений.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад в меню", callback_data="back")
                ]])
            )
            return ConversationHandler.END

    elif query.data == "exit_without_save":
        await query.message.reply_text(
            "Изменения отменены.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад в меню", callback_data="back")
            ]])
        )
        return ConversationHandler.END

    return ConversationHandler.END