"""
Homut - Telegram Bot для управления складским учетом
=================================================

Этот модуль является основным файлом приложения, который содержит:
1. Инициализацию бота и его обработчиков
2. Обработку команд и callback-запросов
3. Управление состояниями диалога
4. Обработку ошибок

Основные компоненты:
- Система меню и навигации
- Управление инвентарем (добавление, редактирование, удаление)
- Работа с чертежами
- Управление совместимостью деталей
- Система логирования

Архитектурные особенности:
- Использует паттерн ConversationHandler для управления состояниями
- Асинхронное взаимодействие с базой данных через aiosqlite
- Модульная структура с разделением функциональности
- Extensive logging для отладки и мониторинга

Требования к окружению:
- Python 3.9+
- python-telegram-bot==21.10
- aiosqlite==0.21.0
- SQLite3 база данных
"""

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
from new_item import add_new_item, handle_new_item_input, invalid_input, go_back
from change_quantity import (
    change_quantity_callback,
    item_name_received,
    adjust_quantity_callback,
    done_adjustment,
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

from compatibility import (
    show_compatibility_menu,
    check_compatibility,
    show_compatible_parts,
    add_compatibility_start,
    select_target_stamp,
    select_part_type_and_name,
    handle_part_name_input,
    handle_part_selection,
    add_compatibility_notes,
    save_compatibility,
    back_to_compatibility_menu,
    back_to_stamp_list,
    back_to_source_selection,
    back_to_target_selection,
    back_to_type_selection,
    edit_compatibility_start,
    handle_edit_compatibility_choice,
    handle_edit_compatibility_delete,
    handle_edit_compatibility_notes,
    save_edited_notes,
    back_to_compat_list
)

from drawings import (
    show_drawings_menu,
    start_drawing_upload,
    handle_drawing_file,
    view_drawings,
    show_stamp_drawings,
    search_drawings,
    handle_drawing_search,
    back_to_drawings_menu,
    download_drawing,
    preview_drawing
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('homut.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Глобальный обработчик ошибок для бота.

    Параметры:
    - update (Update): Объект обновления от Telegram
    - context (ContextTypes.DEFAULT_TYPE): Контекст бота, содержащий информацию об ошибке

    Действия:
    1. Логирует ошибку с полным стектрейсом
    2. Отправляет пользователю сообщение об ошибке
    """
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Произошла ошибка. Пожалуйста, попробуйте позже."
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start.

    Параметры:
    - update (Update): Объект обновления от Telegram
    - context (ContextTypes.DEFAULT_TYPE): Контекст бота

    Действия:
    1. Инициализирует путь меню для пользователя
    2. Отправляет приветственное сообщение с главным меню
    """
    logger.info(f"Получена команда /start от пользователя {update.effective_user.id}")
    try:
        context.user_data['menu_path'] = ['main_menu']
        context.user_data['current_menu'] = 'main_menu'
        keyboard = get_menu_keyboard('main_menu')
        await update.message.reply_text(menu['main_menu']['text'], reply_markup=keyboard)
        logger.info("Главное меню успешно отправлено")
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /start: {e}")
        await update.message.reply_text("Произошла ошибка при запуске бота. Пожалуйста, попробуйте позже.")

async def show_drawings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> States.DRAWINGS_MENU:
    """
    Отображает меню управления чертежами.

    Параметры:
    - update (Update): Объект обновления от Telegram
    - context (ContextTypes.DEFAULT_TYPE): Контекст бота

    Возвращает:
    - States.DRAWINGS_MENU: Состояние меню чертежей

    Действия:
    1. Создает клавиатуру с опциями управления чертежами
    2. Отображает меню с возможностями загрузки, просмотра и поиска чертежей
    """
    try:
        query = update.callback_query
        if query is None:
            return States.DRAWINGS_MENU

        await query.answer()
        keyboard = [
            [InlineKeyboardButton("📤 Загрузить чертеж", callback_data="upload_drawing")],
            [InlineKeyboardButton("📋 Просмотр чертежей", callback_data="view_drawings")],
            [InlineKeyboardButton("🔍 Поиск чертежей", callback_data="search_drawings")],
            [InlineKeyboardButton("↩️ Назад в главное меню", callback_data="back")]
        ]
        await query.message.edit_text(
            "📐 Меню управления чертежами\n\n"
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return States.DRAWINGS_MENU
    except Exception as e:
        logger.error(f"Ошибка при показе меню чертежей: {e}")
        if query is not None:
            await query.message.reply_text(
                "Произошла ошибка при загрузке меню чертежей. Попробуйте позже."
            )
        return States.DRAWINGS_MENU

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Главный обработчик callback-запросов от кнопок инлайн-клавиатуры.

    Параметры:
    - update (Update): Объект обновления от Telegram
    - context (ContextTypes.DEFAULT_TYPE): Контекст бота

    Действия:
    1. Обрабатывает нажатия на кнопки меню
    2. Управляет навигацией по меню
    3. Вызывает соответствующие обработчики для различных действий

    Особенности реализации:
    - Поддерживает иерархическую структуру меню
    - Обрабатывает специальные действия (чертежи, совместимость)
    - Имеет систему обработки ошибок с информативными сообщениями
    """
    try:
        query = update.callback_query
        if query is None:
            logger.error("Получен update без callback_query")
            return

        await query.answer()

        # Инициализируем путь меню, если его нет
        if 'menu_path' not in context.user_data:
            context.user_data['menu_path'] = ['main_menu']

        user_path = context.user_data['menu_path']
        current_menu = user_path[-1] if user_path else 'main_menu'

        data = query.data
        logger.info(f"Получен callback с данными: {data} от пользователя {update.effective_user.id}")
        logger.info(f"Текущий путь в меню: {user_path}")

        # Обработка различных типов callback-данных
        if data == 'drawings':
            return await show_drawings_menu(update, context)
        elif data in ['upload_drawing', 'view_drawings', 'search_drawings', 'back_to_drawings']:
            return

        # Обработка действий совместимости
        if data in ["compatibility_parts", "back_to_compatibility", "back_to_stamp_list"]:
            if data == "compatibility_parts":
                await show_compatibility_menu(update, context)
            elif data == "back_to_compatibility":
                await back_to_compatibility_menu(update, context)
            elif data == "back_to_stamp_list":
                await back_to_stamp_list(update, context)
            return

        # Обработка кнопки "Назад"
        if data == 'back':
            logger.info("Обработка кнопки 'Назад в главное меню'")
            try:
                context.user_data.clear()
                context.user_data['menu_path'] = ['main_menu']
                keyboard = get_menu_keyboard('main_menu')
                try:
                    await query.message.edit_text(
                        text=menu['main_menu']['text'],
                        reply_markup=keyboard
                    )
                except Exception as edit_error:
                    logger.error(f"Ошибка при редактировании сообщения: {edit_error}", exc_info=True)
                    await query.message.reply_text(
                        text=menu['main_menu']['text'],
                        reply_markup=keyboard
                    )
                logger.info("Успешно вернулись в главное меню")
                return ConversationHandler.END
            except Exception as e:
                logger.error(f"Ошибка при возврате в главное меню: {e}", exc_info=True)
                keyboard = [[InlineKeyboardButton("🔄 Перезапустить", callback_data="start")]]
                await query.message.reply_text(
                    "Произошла ошибка. Пожалуйста, попробуйте перезапустить бота командой /start",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return ConversationHandler.END

        # Проверяем специальные callback'и
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
            'exit_without_save',
            'check_compatibility',
            'add_compatibility',
            'check_stamp_',
            'source_stamp_',
            'target_stamp_',
            'part_type_',
            'skip_notes',
            'edit_compat_',
            'view_drawings_stamp_',
            'upload_for_stamp_'
        ]):
            logger.info(f"Пропуск обработчика кнопок для callback конверсации: {data}")
            return

        if data in menu:
            logger.info(f"Переход к подменю: {data}")
            user_path.append(data)
            context.user_data['menu_path'] = user_path
            current_menu = data
            context.user_data['current_menu'] = current_menu
            keyboard = get_menu_keyboard(current_menu)
            text = menu[current_menu]['text']
            await query.message.edit_text(text=text, reply_markup=keyboard)
            return
        else:
            action = data
            logger.info(f"Обработка действия: {action}")

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
            else:
                logger.warning(f"Неизвестное действие: {action}")
                keyboard = get_menu_keyboard('main_menu')
                await query.message.edit_text(
                    "Действие не распознано.",
                    reply_markup=keyboard
                )
                return

    except Exception as e:
        logger.error(f"Ошибка при обработке callback кнопки: {e}", exc_info=True)
        try:
            if query is not None:
                keyboard = get_menu_keyboard('main_menu')
                try:
                    await query.message.edit_text(
                        "Произошла ошибка при обработке действия. Пожалуйста, попробуйте позже.",
                        reply_markup=keyboard
                    )
                except Exception as edit_error:
                    logger.error(f"Ошибка при отправке сообщения об ошибке: {edit_error}", exc_info=True)
                    await query.message.reply_text(
                        "Произошла ошибка при обработке действия. Пожалуйста, попробуйте позже.",
                        reply_markup=keyboard
                    )
        except Exception as message_error:
            logger.error(f"Ошибка при отправке сообщения об ошибке: {message_error}", exc_info=True)
        return ConversationHandler.END

# Обновляем ConversationHandler для совместимости
compatibility_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(show_compatibility_menu, pattern='^compatibility_parts$')
    ],
    states={
        States.COMPATIBILITY_MENU: [
            CallbackQueryHandler(check_compatibility, pattern='^check_compatibility$'),
            CallbackQueryHandler(add_compatibility_start, pattern='^add_compatibility$'),
            CallbackQueryHandler(edit_compatibility_start, pattern='^edit_compatibility$'),
            CallbackQueryHandler(back_to_compatibility_menu, pattern='^back_to_compatibility$'),
            CallbackQueryHandler(
                lambda u, c: button(u, c),
                pattern='^back$'
            )
        ],
        States.CHECKING_COMPATIBILITY: [
            CallbackQueryHandler(show_compatible_parts, pattern='^check_stamp_\d+$'),
            CallbackQueryHandler(back_to_stamp_list, pattern='^back_to_stamp_list$'),
            CallbackQueryHandler(back_to_compatibility_menu, pattern='^back_to_compatibility$'),
            CallbackQueryHandler(button, pattern='^back$')
        ],
        States.ADDING_COMPATIBILITY_SOURCE: [
            CallbackQueryHandler(select_target_stamp, pattern='^source_stamp_\d+$'),
            CallbackQueryHandler(back_to_compatibility_menu, pattern='^back_to_compatibility$'),
            CallbackQueryHandler(button, pattern='^back$')
        ],
        States.ADDING_COMPATIBILITY_TARGET: [
            CallbackQueryHandler(select_part_type_and_name, pattern='^target_stamp_\d+$'),
            CallbackQueryHandler(back_to_source_selection, pattern='^back_to_source_selection$'),
            CallbackQueryHandler(button, pattern='^back$')
        ],
        States.ADDING_COMPATIBILITY_TYPE: [
            CallbackQueryHandler(handle_part_name_input, pattern='^part_type_\w+$'),
            CallbackQueryHandler(back_to_target_selection, pattern='^back_to_target_selection$'),
            CallbackQueryHandler(button, pattern='^back$')
        ],
        States.ADDING_COMPATIBILITY_NAME: [
            CallbackQueryHandler(handle_part_selection, pattern='^select_part_.*$'),
            CallbackQueryHandler(back_to_type_selection, pattern='^back_to_type_selection$'),
            CallbackQueryHandler(button, pattern='^back$')
        ],
        States.ADDING_COMPATIBILITY_NOTES: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                lambda update, context: (
                    save_edited_notes(update, context)
                    if context.user_data.get('editing_notes')
                    else save_compatibility(update, context)
                )
            ),
            CallbackQueryHandler(save_compatibility, pattern='^skip_notes$'),
            CallbackQueryHandler(back_to_type_selection, pattern='^back_to_type_selection$'),
            CallbackQueryHandler(button, pattern='^back$')
        ],
        States.EDITING_COMPATIBILITY_CHOOSING: [
            CallbackQueryHandler(handle_edit_compatibility_choice, pattern='^edit_compat_\d+$'),
            CallbackQueryHandler(back_to_compatibility_menu, pattern='^back_to_compatibility$'),
            CallbackQueryHandler(button, pattern='^back$')
        ],
        States.EDITING_COMPATIBILITY_ACTION: [
            CallbackQueryHandler(handle_edit_compatibility_notes, pattern='^edit_compat_notes$'),
            CallbackQueryHandler(handle_edit_compatibility_delete, pattern='^delete_compat$'),
            CallbackQueryHandler(back_to_compat_list, pattern='^back_to_compat_list$'),
            CallbackQueryHandler(button, pattern='^back$')
        ]
    },
    fallbacks=[
        CommandHandler('start', start),
        CallbackQueryHandler(button, pattern='^back$')
    ],
    name="compatibility",
    persistent=False,
    allow_reentry=True
)

# Обновляем обработчик для работы с чертежами
drawings_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(show_drawings_menu, pattern='^drawings$')
    ],
    states={
        States.DRAWINGS_MENU: [
            CallbackQueryHandler(start_drawing_upload, pattern='^upload_drawing$'),
            CallbackQueryHandler(view_drawings, pattern='^view_drawings$'),
            CallbackQueryHandler(search_drawings, pattern='^search_drawings$'),
            CallbackQueryHandler(back_to_drawings_menu, pattern='^back_to_drawings$'),
            CallbackQueryHandler(button, pattern='^back$')
        ],
        States.UPLOADING_DRAWING_STAMP: [
            CallbackQueryHandler(handle_drawing_file, pattern='^upload_for_stamp_\d+$'),
            CallbackQueryHandler(back_to_drawings_menu, pattern='^back_to_drawings$'),
            CallbackQueryHandler(button, pattern='^back$')
        ],
        States.UPLOADING_DRAWING_FILE: [
            MessageHandler(
                filters.Document.ALL,
                handle_drawing_file
            ),
            CallbackQueryHandler(back_to_drawings_menu, pattern='^back_to_drawings$'),
            CallbackQueryHandler(button, pattern='^back$')
        ],
        States.VIEWING_DRAWINGS: [
            CallbackQueryHandler(show_stamp_drawings, pattern='^view_drawings_stamp_\d+$'),
            CallbackQueryHandler(download_drawing, pattern='^download_drawing_\d+$'),
            CallbackQueryHandler(preview_drawing, pattern='^preview_drawing_\d+$'),
            CallbackQueryHandler(view_drawings, pattern='^view_drawings$'),
            CallbackQueryHandler(back_to_drawings_menu, pattern='^back_to_drawings$'),
            CallbackQueryHandler(button, pattern='^back$')
        ],
        States.SEARCHING_DRAWINGS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_drawing_search),
            CallbackQueryHandler(back_to_drawings_menu, pattern='^back_to_drawings$'),
            CallbackQueryHandler(button, pattern='^back$')
        ]
    },
    fallbacks=[
        CommandHandler('start', start),
        CallbackQueryHandler(button, pattern='^back$')
    ],
    name="drawings",
    persistent=False,
    allow_reentry=True
)

ALLOWED_FILE_TYPES = ('.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.dwg')

async def on_startup(application: Application) -> None:
    application.db = await aiosqlite.connect('inventory.db')
    logger.info("Подключение к базе данных установлено.")

async def on_shutdown(application: Application) -> None:
    try:
        if hasattr(application, 'db'):
            await application.db.close()
            logger.info("Соединение с базой данных закрыто.")

        logger.info("Бот успешно остановлен.")
    except Exception as e:
        logger.error(f"Ошибка при остановке бота: {e}")

def main() -> None:
    from config import BOT_TOKEN

    logger.info("Запуск бота...")
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        logger.info("Успешно создано приложение с токеном")

        # Настройка обработчиков
        application.add_handler(CommandHandler("start", start))

        # Обработчик изменения количества
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
        application.add_handler(conv_handler)
        logger.info("Настроен обработчик изменения количества")

        # Обработчик добавления новых элементов
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
        application.add_handler(add_item_conv_handler)
        logger.info("Настроен обработчик добавления элементов")

        # Обработчик редактирования/удаления
        edit_delete_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(show_edit_delete_menu, pattern='^editdelete.*$')
            ],
            states={
                States.EDIT_DELETE_SELECT_ACTION: [
                    CallbackQueryHandler(handle_action_selection, pattern='^select_(edit|delete)$'),
                    CallbackQueryHandler(go_back, pattern='^back$')
                ],
                States.EDIT_DELETE_CHOOSING: [
                    CallbackQueryHandler(handle_edit_choice, pattern='^(edit|delete)_\d+$'),
                    CallbackQueryHandler(go_back, pattern='^back$')
                ],
                States.EDIT_CHOOSING_FIELD: [
                    CallbackQueryHandler(handle_edit_field, pattern='^edit_field_.*$'),
                    CallbackQueryHandler(go_back, pattern='^back$')
                ],
                States.EDIT_ENTERING_VALUE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_value),
                    CallbackQueryHandler(go_back, pattern='^back$')
                ],
                States.DELETE_CONFIRM: [
                    CallbackQueryHandler(handle_delete_confirm, pattern='^confirm_delete$'),
                    CallbackQueryHandler(go_back, pattern='^back$')
                ]
            },
            fallbacks=[
                CommandHandler('start', start),
                CallbackQueryHandler(go_back, pattern='^back$')
            ],
            name="edit_delete",
            persistent=False,
            allow_reentry=True
        )
        application.add_handler(edit_delete_handler)
        logger.info("Настроен обработчик редактирования/удаления")

        # Добавляем обработчик совместимости
        application.add_handler(compatibility_handler)

        # Добавляем обработчик чертежей
        application.add_handler(drawings_handler)

        # Общий обработчик кнопок
        application.add_handler(CallbackQueryHandler(button))
        application.add_error_handler(error_handler)

        application.post_init = on_startup
        application.post_shutdown = on_shutdown

        logger.info("Все обработчики успешно добавлены, запускаю бота...")
        application.run_polling()
        logger.info("Бот успешно запущен и работает")

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise

if __name__ == '__main__':
    main()