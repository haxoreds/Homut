import logging
import aiosqlite
import re
import asyncio
from constants import States
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
from menu import menu, create_inventory_submenus, inventory_list, get_menu_keyboard, back_to_menu_keyboard, process_main_menu_action
from showballance import show_balance
from new_item import add_new_item, handle_new_item_input
from change_quantity import (
    change_quantity_callback,
    item_name_received,
    adjust_quantity_callback,
    done_adjustment,
    go_back,
    save_and_exit,
    exit_without_saving,
    cancel,
    invalid_input_in_choosing,
    invalid_input_in_adjusting,
    unknown_message
)

from new_item import (
    add_new_item,
    invalid_input,
    handle_new_item_input,
    go_back,
)

from edit_delete import (
    start_change_or_delete,
    show_items_list_for_edit,
    show_items_list_for_delete,
    start_edit_item,
    confirm_delete_item,
    delete_item,
    edit_value_received,
)
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

from constants import States



async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    # Вы также можете отправлять сообщение пользователю или администратору
    if isinstance(update, Update) and update.effective_chat:
        await update.effective_chat.send_message("Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчики команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['menu_path'] = ['main_menu']
    keyboard = get_menu_keyboard('main_menu')
    await update.message.reply_text(menu['main_menu']['text'], reply_markup=keyboard)


# Функция для обработки нажатий на кнопки меню и действий
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_path = context.user_data.get('menu_path', ['main_menu'])
    current_menu = user_path[-1]
    data = query.data

    if data == 'back':
        if len(user_path) > 1:
            user_path.pop()
            current_menu = user_path[-1]
        else:
            await query.message.reply_text("Вы уже находитесь в главном меню.")
            return
        keyboard = get_menu_keyboard(current_menu)
        text = menu[current_menu]['text']
        await query.message.edit_text(text=text, reply_markup=keyboard)
        return
    elif data in menu:
        user_path.append(data)
        current_menu = data
        keyboard = get_menu_keyboard(current_menu)
        text = menu[current_menu]['text']
        await query.message.edit_text(text=text, reply_markup=keyboard)
        return
    else:
        action = data
        # Обработка действий
        if action.startswith('showbalance'):
            await show_balance(query, context, action, current_menu)
            return
        elif action.startswith('addnewitem'):
            await add_new_item(query, context, action, current_menu)
            return
        elif action.startswith('updatedb'):
            # Извлекаем категорию и inv_id из action
            action_info = action[len('updatedb'):]  # Получаем строку после 'updatedb'
            # Используем регулярное выражение, чтобы разделить категорию и inv_id
            import re
            match = re.match(r'([a-zA-Z_]+)(.*)', action_info)
            if match:
                category = match.group(1)  # Категория, например, 'punches'
                inv_id = match.group(2)    # inv_id, например, '12_8'
                # Сохраняем информацию в context.user_data
                context.user_data['category'] = category
                context.user_data['inv_id'] = inv_id

                # Начинаем процесс выбора действия (изменение или удаление)
                await start_change_or_delete(query, context, category, inv_id)
            else:
                await query.message.reply_text("Некорректные данные для обновления базы.", reply_markup=back_to_menu_keyboard(current_menu))
            return
        elif action == 'edit':
            category = context.user_data.get('category')
            inv_id = context.user_data.get('inv_id')
            if category and inv_id:
                context.user_data['last_action'] = 'edit'
                await show_items_list_for_edit(query, context, category, inv_id)
            else:
                await query.message.reply_text("Не удалось получить данные категории для редактирования.", reply_markup=back_to_menu_keyboard(current_menu))
            return
        elif action == 'delete':
            category = context.user_data.get('category')
            inv_id = context.user_data.get('inv_id')
            if category and inv_id:
                context.user_data['last_action'] = 'delete'
                await show_items_list_for_delete(query, context, category, inv_id)
            else:
                await query.message.reply_text("Не удалось получить данные категории для удаления.", reply_markup=back_to_menu_keyboard(current_menu))
            return
        elif action.startswith('edititem_'):
            item_id = action[len('edititem_'):]
            category = context.user_data.get('category')
            inv_id = context.user_data.get('inv_id')
            if category and item_id:
                await start_edit_item(query, context, category, item_id)
            else:
                await query.message.reply_text("Не удалось получить данные для редактирования.", reply_markup=back_to_menu_keyboard(f'{category}_{inv_id}'))
            return
        elif action.startswith('deleteitem_'):
            item_id = action[len('deleteitem_'):]
            category = context.user_data.get('category')
            inv_id = context.user_data.get('inv_id')
            if category and item_id:
                await confirm_delete_item(query, context, category, item_id)
            else:
                await query.message.reply_text("Не удалось получить данные для удаления.", reply_markup=back_to_menu_keyboard(f'{category}_{inv_id}'))
            return
        elif action.startswith('editfield_'):
            parts = action.split('_')
            if len(parts) == 3:
                field = parts[1]
                item_id = parts[2]
                category = context.user_data.get('category')
                inv_id = context.user_data.get('inv_id')
                if category and item_id and field:
                    # Сохраняем информацию для дальнейшего использования
                    context.user_data['edit_item'] = {
                        'category': category,
                        'item_id': item_id,
                        'field': field
                    }
                    field_names = {'name': 'Имя', 'description': 'Описание', 'quantity': 'Количество'}
                    await query.message.edit_text(text=f'Введите новое значение для поля "{field_names.get(field, field)}":')
                    return States.EDIT_VALUE  # Переходим к состоянию ожидания ввода значения
            else:
                await query.message.reply_text("Некорректные данные для редактирования.", reply_markup=back_to_menu_keyboard(f'{category}_{inv_id}'))
            return
        elif action.startswith('confirmdelete_'):
            item_id = action[len('confirmdelete_'):]
            category = context.user_data.get('category')
            inv_id = context.user_data.get('inv_id')
            if category and item_id:
                await delete_item(query, context, category, item_id)
            else:
                await query.message.reply_text("Не удалось удалить позицию.", reply_markup=back_to_menu_keyboard(f'{category}_{inv_id}'))
            return
        elif action == 'back_to_category':
            # Возвращаемся к предыдущему меню категории
            category = context.user_data.get('category')
            inv_id = context.user_data.get('inv_id')
            if category and inv_id:
                menu_name = f'{category}_{inv_id}'
                keyboard = get_menu_keyboard(menu_name)
                text = menu[menu_name]['text']
                await query.message.edit_text(text=text, reply_markup=keyboard)
                # Очищаем сохраненные данные
                context.user_data.pop('category', None)
                context.user_data.pop('inv_id', None)
                context.user_data.pop('last_action', None)
            else:
                await query.message.reply_text("Не удалось вернуться к предыдущему меню.", reply_markup=back_to_menu_keyboard('main_menu'))
            return
        elif action == 'back_to_action_selection':
            # Возвращаемся к выбору действия (Изменить или Удалить)
            await start_change_or_delete(query, context, context.user_data.get('category'), context.user_data.get('inv_id'))
            return
        elif action == 'back_to_items_list':
            # Возвращаемся к списку позиций
            category = context.user_data.get('category')
            inv_id = context.user_data.get('inv_id')
            last_action = context.user_data.get('last_action')
            if last_action == 'edit':
                await show_items_list_for_edit(query, context, category, inv_id)
            elif last_action == 'delete':
                await show_items_list_for_delete(query, context, category, inv_id)
            else:
                await query.message.reply_text("Не удалось вернуться к списку позиций.", reply_markup=back_to_menu_keyboard('main_menu'))
            return
        elif action.startswith('changequantity'):
            context.user_data['action'] = action  # Сохраняем действие в user_data
            await change_quantity_callback(update, context)
            return
        elif action in [
            'compatibility_parts',
            'drawings',
            'bolt_accounting',
            'stationery',
            'stamp_settings',
            'export_to_excel'
        ]:
            await process_main_menu_action(action, update, context)
            # После выполнения действия показываем кнопку "Назад"
            await query.message.reply_text(
                "Действие выполнено.",
                reply_markup=back_to_menu_keyboard('main_menu')
            )
            return
        else:
            await query.message.reply_text("Действие не распознано.")
            return

# Функция для подключения к базе данных при запуске бота
async def on_startup(application):
    application.db = await aiosqlite.connect('inventory.db')  # Изменение здесь
    logger.info("Подключение к базе данных установлено.")

# Функция для закрытия соединения с базой данных при остановке бота
async def on_shutdown(application):
    await application.db.close()  # Изменение здесь
    logger.info("Соединение с базой данных закрыто.")


def main():
    # Замените 'YOUR_TOKEN_HERE' на токен вашего бота
    application = ApplicationBuilder().token("тут токен") \
        .post_init(on_startup) \
        .post_shutdown(on_shutdown) \
        .build()

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(change_quantity_callback, pattern='^changequantity.*$')
        ],
        states={
            States.CHANGE_QTY_CHOOSING_ITEM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, item_name_received),
                MessageHandler(filters.ALL, invalid_input_in_choosing),
                CallbackQueryHandler(go_back, pattern='^go_back$'),
            ],
            States.CHANGE_QTY_ADJUSTING_QUANTITY: [
                CallbackQueryHandler(adjust_quantity_callback, pattern=r'^adjust_quantity:[+-]\d+$'),
                CallbackQueryHandler(done_adjustment, pattern='^done_adjustment$'),
                CallbackQueryHandler(go_back, pattern='^go_back$'),
                MessageHandler(filters.ALL, invalid_input_in_adjusting),
            ],
            States.CHANGE_QTY_CONFIRM_EXIT: [
                CallbackQueryHandler(save_and_exit, pattern='^save_and_exit$'),
                CallbackQueryHandler(exit_without_saving, pattern='^exit_without_saving$'),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern='^cancel$')
        ],
        allow_reentry=True,
        per_message=False,
    )

    add_item_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_new_item, pattern='^addnewitem.*$')
        ],
        states={
            States.ADD_ENTERING_DATA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_item_input),
                CallbackQueryHandler(go_back, pattern='^go_back$'),
                MessageHandler(filters.ALL, invalid_input),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(go_back, pattern='^go_back$')
        ],
        allow_reentry=True,
        per_message=False,
    )

    edit_delete_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_change_or_delete, pattern='^updatedb_.*$')
    ],
    states={
        States.EDIT_CHOOSE_ACTION: [
            CallbackQueryHandler(show_items_list_for_edit, pattern='^edit$'),
            CallbackQueryHandler(show_items_list_for_delete, pattern='^delete$'),
            CallbackQueryHandler(go_back, pattern='^back_to_category$'),
        ],
        States.EDIT_CHOOSE_ITEM: [
            CallbackQueryHandler(start_edit_item, pattern='^edititem_\\d+$'),
            CallbackQueryHandler(confirm_delete_item, pattern='^deleteitem_\\d+$'),
            CallbackQueryHandler(go_back, pattern='^back_to_action_selection$'),
        ],
        States.EDIT_VALUE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value_received),
            MessageHandler(filters.ALL, invalid_input),
        ],
        States.EDIT_CONFIRM_DELETE: [
            CallbackQueryHandler(delete_item, pattern='^confirmdelete_\\d+$'),
            CallbackQueryHandler(go_back, pattern='^back_to_items_list$'),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(go_back, pattern='^back_to_.*$'),
    ],
    allow_reentry=True,
)

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))
    application.add_error_handler(error_handler)

    # Добавляем обработчики в приложение
    application.add_handler(add_item_conv_handler)
    application.add_handler(edit_delete_conv_handler)
    application.add_handler(conv_handler)

    application.run_polling()
    

if __name__ == '__main__':
    main()
