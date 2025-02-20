<replit_final_file>
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from database import (
    get_items_in_category,
    get_item_by_id,
    #update_item_field, #removed the original function
    delete_item_from_database
)
from menu import back_to_menu_keyboard  # Предполагаю, что эта функция у вас реализована
from constants import States
import logging

logger = logging.getLogger(__name__)
# Функция для начала выбора действия (изменить или удалить данные)
async def start_change_or_delete(query, context, category, inv_id):
    keyboard = [
        [
            InlineKeyboardButton('Изменить данные', callback_data='edit'),
            InlineKeyboardButton('Удалить позицию', callback_data='delete')
        ],
        [InlineKeyboardButton('Назад', callback_data='back_to_category')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text='Выберите действие:', reply_markup=reply_markup)

# Функция для отображения списка позиций для редактирования
async def show_items_list_for_edit(query, context, category, inv_id):
    items = await get_items_in_category(category, inv_id)
    if not items:
        await query.message.edit_text(
            'Нет доступных позиций для редактирования.',
            reply_markup=back_to_menu_keyboard(f'{category}_{inv_id}')
        )
        return

    keyboard = []
    for item in items:
        keyboard.append([
            InlineKeyboardButton(
                f"{item['id']}: {item['name']}",
                callback_data=f'edititem_{item["id"]}'
            )
        ])

    keyboard.append([InlineKeyboardButton('Назад', callback_data='back_to_action_selection')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text='Выберите позицию для редактирования:', reply_markup=reply_markup)

# Функция для отображения списка позиций для удаления
async def show_items_list_for_delete(query, context, category, inv_id):
    items = await get_items_in_category(category, inv_id)
    if not items:
        await query.message.edit_text(
            'Нет доступных позиций для удаления.',
            reply_markup=back_to_menu_keyboard(f'{category}_{inv_id}')
        )
        return

    keyboard = []
    for item in items:
        keyboard.append([
            InlineKeyboardButton(
                f"{item['id']}: {item['name']}",
                callback_data=f'deleteitem_{item["id"]}'
            )
        ])

    keyboard.append([InlineKeyboardButton('Назад', callback_data='back_to_action_selection')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text='Выберите позицию для удаления:', reply_markup=reply_markup)

# Функция для начала редактирования выбранной позиции
async def start_edit_item(query, context, category, item_id):
    item = await get_item_by_id(category, item_id)
    if not item:
        await query.message.edit_text(
            'Позиция не найдена.',
            reply_markup=back_to_menu_keyboard(f'{category}_{context.user_data.get("inv_id")}')
        )
        return

    # Предлагаем выбрать поле для редактирования
    keyboard = []
    fields = ['name', 'description', 'quantity']  # Добавьте другие поля, если необходимо
    field_names = {'name': 'Имя', 'description': 'Описание', 'quantity': 'Количество'}

    for field in fields:
        if field in item:
            keyboard.append([
                InlineKeyboardButton(
                    f'Изменить {field_names.get(field, field)}',
                    callback_data=f'editfield_{field}_{item_id}'
                )
            ])

    keyboard.append([InlineKeyboardButton('Назад', callback_data='back_to_items_list')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        text=f"Выбрана позиция: {item['name']}\nВыберите поле для редактирования:",
        reply_markup=reply_markup
    )

# Функция для подтверждения удаления позиции
async def confirm_delete_item(query, context, category, item_id):
    item = await get_item_by_id(category, item_id)
    if not item:
        await query.message.edit_text(
            'Позиция не найдена.',
            reply_markup=back_to_menu_keyboard(f'{category}_{context.user_data.get("inv_id")}')
        )
        return

    keyboard = [
        [
            InlineKeyboardButton('Да', callback_data=f'confirmdelete_{item_id}'),
            InlineKeyboardButton('Нет', callback_data='back_to_items_list')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        text=f'Вы уверены, что хотите удалить позицию "{item["name"]}"?',
        reply_markup=reply_markup
    )

# Функция для удаления позиции
async def delete_item(query, context, category, item_id):
    await delete_item_from_database(category, item_id)
    await query.message.edit_text('Позиция успешно удалена.')
    # Возвращаемся к списку позиций для удаления
    await show_items_list_for_delete(query, context, category, context.user_data.get('inv_id'))

# Функция для обработки ввода нового значения
async def edit_value_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("edit_value_received called")
    new_value = update.message.text.strip()
    edit_item = context.user_data.get('edit_item')
    if not edit_item:
        await update.message.reply_text("Произошла ошибка. Попробуйте снова.")
        return ConversationHandler.END

    category = edit_item['category']
    item_id = edit_item['item_id']
    field = edit_item['field']

    # Если поле 'quantity', проверим, что введено число
    if field == 'quantity':
        try:
            new_value = int(new_value)
        except ValueError:
            await update.message.reply_text('Пожалуйста, введите числовое значение для количества.')
            return States.EDIT_VALUE

    # Обновляем данные в базе
    await update_item_field(category, item_id, field, new_value)
    await update.message.reply_text('Данные успешно обновлены.')

    # Очищаем сохраненные данные
    context.user_data.pop('edit_item', None)

    # Возвращаемся к списку позиций для редактирования
    await show_items_list_for_edit(update, context, category, context.user_data.get('inv_id'))

    return States.EDIT_CHOOSE_ITEM  # Продолжаем диалог

# Функция обновления поля позиции
async def update_item_field(category, item_id, field, value):
    table_name = get_table_name(category)
    if not table_name:
        logger.warning(f"Таблица не найдена для категории {category}")
        return

    async with get_async_connection() as conn:
        query = f"UPDATE {table_name} SET {field} = ?, last_modified = datetime('now', '+3 hours') WHERE id = ?"
        await conn.execute(query, (value, item_id))
        await conn.commit()
        logger.info(f"Обновлено поле {field} для позиции id {item_id} в таблице {table_name}.")

def get_table_name(category):
    # Replace this with your actual logic to get the table name based on category
    # This is a placeholder,  you need to implement this function based on your database structure
    table_names = {
        "category1": "table1",
        "category2": "table2"
    }
    return table_names.get(category)

async def get_async_connection():
    # Replace this with your actual logic to get an asynchronous database connection
    # This is a placeholder; you must implement this based on your database setup (e.g., using a library like `aiosqlite`)
    import aiosqlite
    async with aiosqlite.connect('your_database.db') as db:
      yield db