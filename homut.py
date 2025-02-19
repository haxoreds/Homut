import logging
import aiosqlite
import re
import asyncio
from constants import States
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    filters,
    ConversationHandler,
    ContextTypes,
    MessageHandler
)

from menu import menu, create_inventory_submenus, inventory_list, get_menu_keyboard, back_to_menu_keyboard, process_main_menu_action
from showballance import show_balance
from new_item import add_new_item, handle_new_item_input, invalid_input
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
)

from edit_delete_item import (
    show_edit_delete_menu,
    handle_edit_choice,
    handle_edit_field,
    handle_edit_value,
    handle_delete_confirm,
    handle_exit_options,
    handle_action_selection
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Произошла ошибка. Пожалуйста, попробуйте позже."
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['menu_path'] = ['main_menu']
    keyboard = get_menu_keyboard('main_menu')
    await update.message.reply_text(menu['main_menu']['text'], reply_markup=keyboard)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_path = context.user_data.get('menu_path', ['main_menu'])
    current_menu = user_path[-1]
    data = query.data
    context.user_data['current_menu'] = current_menu

    logger.info(f"Button callback received with data: {data}")

    if any(data.startswith(prefix) for prefix in [
        'item_', 
        'adjust_quantity:', 
        'done_adjustment', 
        'go_back', 
        'save_and_exit', 
        'exit_without_saving',
        'editdelete',
        'edit_',
        'delete_',
        'edit_field_',
        'confirm_delete',
        'back_to_menu',
        'save_exit',
        'exit_without_save'
    ]):
        logger.info(f"Skipping button handler for conversation callback: {data}")
        return

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
        logger.info(f"Processing action: {action}")

        if action.startswith('showbalance'):
            await show_balance(query, context, action, current_menu)
            return
        elif action.startswith('addnewitem'):
            context.user_data['action'] = action
            await add_new_item(update, context)
            return
        elif action.startswith('changequantity'):
            context.user_data['action'] = action
            await change_quantity_callback(update, context)
            return
        elif action.startswith('editdelete'):
            context.user_data['action'] = action
            await show_edit_delete_menu(update, context)
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
            await query.message.reply_text(
                "Действие выполнено.",
                reply_markup=back_to_menu_keyboard('main_menu')
            )
            return
        else:
            logger.warning(f"Неизвестное действие: {action}")
            await query.message.reply_text(
                "Действие не распознано.",
                reply_markup=back_to_menu_keyboard(current_menu)
            )
            return

async def on_startup(application: Application) -> None:
    application.db = await aiosqlite.connect('inventory.db')
    logger.info("Подключение к базе данных установлено.")

async def on_shutdown(application: Application) -> None:
    await application.db.close()
    logger.info("Соединение с базой данных закрыто.")

def main() -> None:
    from config import BOT_TOKEN

    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(change_quantity_callback, pattern='^changequantity.*$')
        ],
        states={
            States.CHANGE_QTY_CHOOSING_ITEM: [
                CallbackQueryHandler(item_name_received, pattern='^item_.*$'),
                CallbackQueryHandler(go_back, pattern='^go_back$'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_input_in_choosing)
            ],
            States.CHANGE_QTY_ADJUSTING_QUANTITY: [
                CallbackQueryHandler(adjust_quantity_callback, pattern='^adjust_quantity:[+-]\d+$'),
                CallbackQueryHandler(done_adjustment, pattern='^done_adjustment$'),
                CallbackQueryHandler(go_back, pattern='^go_back$'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_input_in_adjusting)
            ],
            States.CHANGE_QTY_CONFIRM_EXIT: [
                CallbackQueryHandler(save_and_exit, pattern='^save_and_exit$'),
                CallbackQueryHandler(exit_without_saving, pattern='^exit_without_saving$')
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern='^cancel$'),
            CommandHandler('start', start)
        ],
        name="change_quantity",
        persistent=False,
        allow_reentry=True
    )

    add_item_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_new_item, pattern='^addnewitem.*$')
        ],
        states={
            States.ADD_ENTERING_DATA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_item_input),
                CallbackQueryHandler(go_back, pattern='^go_back$')
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern='^cancel$'),
            CommandHandler('start', start)
        ],
        name="add_item",
        persistent=False,
        allow_reentry=True
    )

    edit_delete_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_edit_delete_menu, pattern='^editdelete.*$')
        ],
        states={
            States.EDIT_DELETE_SELECT_ACTION: [
                CallbackQueryHandler(handle_action_selection, pattern='^select_(edit|delete)$'),
                CallbackQueryHandler(show_edit_delete_menu, pattern='^back$')
            ],
            States.EDIT_DELETE_CHOOSING: [
                CallbackQueryHandler(handle_edit_choice, pattern='^(edit|delete)_\d+$'),
                CallbackQueryHandler(show_edit_delete_menu, pattern='^back$')
            ],
            States.EDIT_CHOOSING_FIELD: [
                CallbackQueryHandler(handle_edit_field, pattern='^edit_field_.*$'),
                CallbackQueryHandler(show_edit_delete_menu, pattern='^back$')
            ],
            States.EDIT_ENTERING_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_value),
                CallbackQueryHandler(show_edit_delete_menu, pattern='^back$')
            ],
            States.DELETE_CONFIRM: [
                CallbackQueryHandler(handle_delete_confirm, pattern='^confirm_delete$'),
                CallbackQueryHandler(show_edit_delete_menu, pattern='^back$')
            ]
        },
        fallbacks=[
            CommandHandler('start', start),
            CallbackQueryHandler(show_edit_delete_menu, pattern='^back$')
        ],
        name="edit_delete",
        persistent=False,
        allow_reentry=True
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(add_item_conv_handler)
    application.add_handler(edit_delete_handler)
    application.add_handler(CallbackQueryHandler(button))
    application.add_error_handler(error_handler)

    application.post_init = on_startup
    application.post_shutdown = on_shutdown

    application.run_polling()

if __name__ == '__main__':
    main()