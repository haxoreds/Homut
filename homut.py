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

    # Skip handling if the callback data should be handled by conversation handlers
    if any(data.startswith(prefix) for prefix in [
        'item_', 
        'adjust_quantity:', 
        'done_adjustment', 
        'go_back', 
        'save_and_exit', 
        'exit_without_saving'
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
        elif action.startswith('updatedb'):
            context.user_data['action'] = action
            await query.message.reply_text(
                "Эта функция находится в разработке.",
                reply_markup=back_to_menu_keyboard(current_menu)
            )
            return
        elif action.startswith('changequantity'):
            context.user_data['action'] = action
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

    # Conversation handler for changing quantity
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

    # Add new item conversation handler
    add_item_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_new_item, pattern='^addnewitem.*$')
        ],
        states={
            States.ADD_ENTERING_DATA: [
                CallbackQueryHandler(handle_new_item_input, pattern='^.*$'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_input)
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

    # Add handlers in correct order
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(add_item_conv_handler)
    application.add_handler(CallbackQueryHandler(button))
    application.add_error_handler(error_handler)

    # Add startup and shutdown handlers
    application.post_init = on_startup
    application.post_shutdown = on_shutdown

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()