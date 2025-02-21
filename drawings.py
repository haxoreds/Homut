"""
Drawings Module - Модуль управления чертежами
=======================================

Этот модуль обеспечивает функциональность для работы с чертежами в телеграм-боте.
Основные возможности:
- Загрузка новых чертежей
- Просмотр существующих чертежей
- Поиск чертежей по параметрам
- Управление файлами чертежей
- Привязка чертежей к штампам

Технические особенности:
- Использует файловую систему для хранения чертежей
- Поддерживает различные форматы файлов
- Обеспечивает безопасное хранение и доступ к файлам
"""

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, filters
from database import get_connection, get_stamp_id_by_action
from menu import back_to_menu_keyboard
from constants import States

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def show_drawings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает главное меню чертежей.

    Параметры:
    - update (Update): Объект обновления от Telegram
    - context (ContextTypes.DEFAULT_TYPE): Контекст бота

    Возвращает:
    - States.DRAWINGS_MENU: Состояние меню чертежей

    Действия:
    1. Создает клавиатуру с основными опциями управления чертежами
    2. Отображает меню с возможностями загрузки, просмотра и поиска
    3. Обрабатывает возможные ошибки при показе меню
    """
    query = update.callback_query
    await query.answer()

    logger.info("Вход в меню чертежей")

    keyboard = [
        [InlineKeyboardButton("Загрузить чертёж", callback_data="upload_drawing")],
        [InlineKeyboardButton("Просмотр чертежей", callback_data="view_drawings")],
        [InlineKeyboardButton("Поиск чертежей", callback_data="search_drawings")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back")]
    ]

    try:
        await query.message.edit_text(
            "Меню управления чертежами:\n"
            "Выберите необходимое действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logger.info("Меню чертежей успешно отображено")
        return States.DRAWINGS_MENU
    except Exception as e:
        logger.error(f"Ошибка при показе меню чертежей: {e}", exc_info=True)
        await query.message.edit_text(
            "Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="back")
            ]])
        )
        return ConversationHandler.END

async def start_drawing_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс загрузки чертежа"""
    query = update.callback_query
    await query.answer()

    logger.info("Начало процесса загрузки чертежа")
    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        logger.info("Получение списка штампов из базы данных")
        cursor.execute("SELECT id, name FROM Stamps ORDER BY name")
        stamps = cursor.fetchall()

        if not stamps:
            logger.warning("Список штампов пуст")
            await query.message.edit_text(
                "В базе данных нет доступных штампов.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="back_to_drawings")
                ]])
            )
            return States.DRAWINGS_MENU

        logger.info(f"Найдено штампов: {len(stamps)}")
        keyboard = []
        for stamp_id, stamp_name in stamps:
            keyboard.append([InlineKeyboardButton(
                stamp_name, 
                callback_data=f"upload_for_stamp_{stamp_id}"
            )])
            logger.debug(f"Добавлена кнопка для штампа: {stamp_name} (ID: {stamp_id})")

        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_drawings")])

        await query.message.edit_text(
            "Выберите штамп, для которого загружаете чертёж:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logger.info("Меню выбора штампа успешно отображено")
        return States.UPLOADING_DRAWING_STAMP

    except Exception as e:
        logger.error(f"Ошибка при получении списка штампов: {e}", exc_info=True)
        await query.message.edit_text(
            "Произошла ошибка при загрузке списка штампов.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_drawings")
            ]])
        )
        return States.DRAWINGS_MENU
    finally:
        if conn:
            logger.debug("Закрытие соединения с базой данных")
            conn.close()

async def handle_drawing_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает загруженный файл чертежа или выбор штампа"""
    try:
        logger.info("Начало handle_drawing_file")

        # Если это отправка файла
        if update.message and update.message.document:
            logger.info("Получено сообщение с документом")
            file = update.message.document
            file_name = file.file_name

            logger.info(f"Получен файл: {file_name}")

            stamp_id = context.user_data.get('selected_stamp_id')
            logger.info(f"Найден stamp_id в context.user_data: {stamp_id}")

            if not stamp_id:
                logger.error("Не найден selected_stamp_id в context.user_data")
                await update.message.reply_text(
                    "❌ Ошибка: не выбран штамп. Пожалуйста, начните процесс заново.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 В меню чертежей", callback_data="back_to_drawings")
                    ]])
                )
                return States.DRAWINGS_MENU

            try:
                # Создаем папку drawings, если она не существует
                os.makedirs('drawings', exist_ok=True)
                logger.info("Папка drawings создана или уже существует")

                # Загружаем файл
                new_file = await file.get_file()
                file_path = f"drawings/{stamp_id}_{file_name}"
                logger.info(f"Попытка сохранения файла по пути: {file_path}")

                await new_file.download_to_drive(file_path)
                logger.info(f"Файл успешно сохранен: {file_path}")

                # Сохраняем информацию в базу данных
                conn = get_connection()
                cursor = conn.cursor()

                try:
                    cursor.execute("""
                        INSERT INTO Drawings (stamp_id, name, file_type, file_path, description)
                        VALUES (?, ?, ?, ?, ?)
                    """, (stamp_id, file_name, os.path.splitext(file_name)[1].lower(), file_path, ""))
                    conn.commit()
                    logger.info("Информация о файле успешно добавлена в базу данных")

                    await update.message.reply_text(
                        "✅ Чертёж успешно загружен!",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 В меню чертежей", callback_data="back_to_drawings")
                        ]])
                    )
                    return States.DRAWINGS_MENU

                except Exception as db_error:
                    logger.error(f"Ошибка при сохранении в базу данных: {db_error}", exc_info=True)
                    raise
                finally:
                    if conn:
                        conn.close()

            except Exception as save_error:
                logger.error(f"Ошибка при сохранении файла: {save_error}", exc_info=True)
                await update.message.reply_text(
                    "❌ Произошла ошибка при сохранении файла.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 В меню чертежей", callback_data="back_to_drawings")
                    ]])
                )
                return States.DRAWINGS_MENU

        # Если это callback query (выбор штампа)
        elif update.callback_query:
            query = update.callback_query
            await query.answer()
            logger.info(f"Обработка callback query: {query.data}")

            try:
                stamp_id = int(query.data.split('_')[-1])
                context.user_data['selected_stamp_id'] = stamp_id
                logger.info(f"Выбран штамп с ID: {stamp_id}")

                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM Stamps WHERE id = ?", (stamp_id,))
                result = cursor.fetchone()

                if not result:
                    logger.error(f"Штамп с ID {stamp_id} не найден в базе")
                    raise ValueError(f"Штамп с ID {stamp_id} не найден")

                stamp_name = result[0]
                logger.info(f"Получено название штампа: {stamp_name}")

                await query.message.edit_text(
                    f"Выбран штамп: {stamp_name}\n\n"
                    "Пожалуйста, отправьте файл чертежа.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="back_to_drawings")
                    ]])
                )
                return States.UPLOADING_DRAWING_FILE

            except Exception as e:
                logger.error(f"Ошибка при обработке выбора штампа: {e}", exc_info=True)
                await query.message.edit_text(
                    "❌ Произошла ошибка при выборе штампа.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="back_to_drawings")
                    ]])
                )
                return States.DRAWINGS_MENU
            finally:
                if 'conn' in locals():
                    conn.close()

        else:
            logger.warning("Получено неожиданное обновление")
            return States.DRAWINGS_MENU

    except Exception as e:
        logger.error(f"Общая ошибка в handle_drawing_file: {e}", exc_info=True)
        if update.callback_query:
            await update.callback_query.message.edit_text(
                "❌ Произошла ошибка. Пожалуйста, попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 В меню чертежей", callback_data="back_to_drawings")
                ]])
            )
        elif update.message:
            await update.message.reply_text(
                "❌ Произошла ошибка. Пожалуйста, попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 В меню чертежей", callback_data="back_to_drawings")
                ]])
            )
        return States.DRAWINGS_MENU

async def view_drawings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список чертежей для выбранного штампа"""
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM Stamps ORDER BY name")
    stamps = cursor.fetchall()
    conn.close()

    keyboard = []
    for stamp_id, stamp_name in stamps:
        keyboard.append([InlineKeyboardButton(
            stamp_name, 
            callback_data=f"view_drawings_stamp_{stamp_id}"
        )])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_drawings")])

    await query.message.edit_text(
        "Выберите штамп для просмотра чертежей:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return States.VIEWING_DRAWINGS

async def show_stamp_drawings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список чертежей для конкретного штампа"""
    query = update.callback_query
    await query.answer()

    stamp_id = int(query.data.split('_')[-1])

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Получаем название штампа
        cursor.execute("SELECT name FROM Stamps WHERE id = ?", (stamp_id,))
        stamp_name = cursor.fetchone()[0]

        # Получаем список чертежей
        cursor.execute("""
            SELECT id, name, file_type, file_path, description, version
            FROM Drawings
            WHERE stamp_id = ?
            ORDER BY name
        """, (stamp_id,))

        drawings = cursor.fetchall()

        if not drawings:
            message = f"Для штампа {stamp_name} нет загруженных чертежей."
            keyboard = [[InlineKeyboardButton("🔙 Назад к списку штампов", callback_data="view_drawings")]]
        else:
            message = f"Чертежи для штампа {stamp_name}:\n\n"
            keyboard = []

            for drawing_id, name, file_type, _, description, version in drawings:
                message += f"📄 {name}"
                if version:
                    message += f" (Версия: {version})"
                message += f"\nТип: {file_type}"
                if description:
                    message += f"\nОписание: {description}"
                message += "\n\n"

                # Добавляем кнопки действий для каждого чертежа
                keyboard.append([
                    InlineKeyboardButton(f"📥 Скачать {name}", callback_data=f"download_drawing_{drawing_id}"),
                    InlineKeyboardButton(f"👀 Просмотр {name}", callback_data=f"preview_drawing_{drawing_id}")
                ])

            keyboard.append([InlineKeyboardButton("🔙 Назад к списку штампов", callback_data="view_drawings")])

        await query.message.edit_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return States.VIEWING_DRAWINGS

    except Exception as e:
        logger.error(f"Ошибка при получении списка чертежей: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад к списку штампов", callback_data="view_drawings")]]
        await query.message.edit_text(
            "❌ Произошла ошибка при получении списка чертежей.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return States.VIEWING_DRAWINGS
    finally:
        conn.close()

async def search_drawings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс поиска чертежей"""
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_drawings")]]

    await query.message.edit_text(
        "Введите текст для поиска чертежей:\n"
        "(поиск осуществляется по названию и описанию)",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return States.SEARCHING_DRAWINGS

async def handle_drawing_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает поисковый запрос для чертежей"""
    if not update.message or not update.message.text:
        return States.SEARCHING_DRAWINGS

    search_query = update.message.text.strip()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Поиск чертежей
        cursor.execute("""
            SELECT d.name, d.file_type, s.name as stamp_name
            FROM Drawings d
            JOIN Stamps s ON s.id = d.stamp_id
            WHERE d.name LIKE ? OR d.description LIKE ?
            ORDER BY d.name
        """, (f"%{search_query}%", f"%{search_query}%"))

        results = cursor.fetchall()

        if not results:
            message = f"По запросу '{search_query}' ничего не найдено."
        else:
            message = f"Результаты поиска по запросу '{search_query}':\n\n"
            for name, file_type, stamp_name in results:
                message += f"📄 {name}\n"
                message += f"Тип: {file_type}\n"
                message += f"Штамп: {stamp_name}\n\n"

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_drawings")]]

        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return States.DRAWINGS_MENU

    except Exception as e:
        logger.error(f"Ошибка при поиске чертежей: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_drawings")]]
        await update.message.reply_text(
            "❌ Произошла ошибка при поиске чертежей.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return States.DRAWINGS_MENU
    finally:
        conn.close()

# Функции для обработки кнопки "Назад"
async def back_to_drawings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню чертежей"""
    query = update.callback_query
    if not query:
        return States.DRAWINGS_MENU

    await query.answer()
    logger.info("Возврат в меню чертежей")

    keyboard = [
        [InlineKeyboardButton("Загрузить чертёж", callback_data="upload_drawing")],
        [InlineKeyboardButton("Просмотр чертежей", callback_data="view_drawings")],
        [InlineKeyboardButton("Поиск чертежей", callback_data="search_drawings")],
        [InlineKeyboardButton("🔙 В главное меню", callback_data="back")]
    ]

    await query.message.edit_text(
        "Меню управления чертежами:\n"
        "Выберите необходимое действие:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return States.DRAWINGS_MENU

async def download_drawing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет файл чертежа пользователю"""
    query = update.callback_query
    await query.answer()

    drawing_id = int(query.data.split('_')[-1])

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT d.file_path, d.name, s.name as stamp_name, s.id as stamp_id
            FROM Drawings d
            JOIN Stamps s ON s.id = d.stamp_id
            WHERE d.id = ?
        """, (drawing_id,))

        result = cursor.fetchone()
        if not result:
            await query.message.reply_text("❌ Чертёж не найден.")
            return States.VIEWING_DRAWINGS

        file_path, drawing_name, stamp_name, stamp_id = result

        if not os.path.exists(file_path):
            await query.message.reply_text("❌ Файл чертежа не найден на сервере.")
            return States.VIEWING_DRAWINGS

        # Отправляем файл
        with open(file_path, 'rb') as file:
            await query.message.reply_document(
                document=file,
                filename=drawing_name,
                caption=f"Чертёж для штампа {stamp_name}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад к списку чертежей", callback_data=f"view_drawings_stamp_{stamp_id}")],
                    [InlineKeyboardButton("🏠 В главное меню чертежей", callback_data="back_to_drawings")]
                ])
            )
        return States.VIEWING_DRAWINGS

    except Exception as e:
        logger.error(f"Ошибка при скачивании чертежа: {e}")
        await query.message.reply_text("❌ Произошла ошибка при скачивании чертежа.")
        return States.VIEWING_DRAWINGS
    finally:
        conn.close()

async def preview_drawing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает превью чертежа"""
    query = update.callback_query
    await query.answer()

    try:
        drawing_id = int(query.data.split('_')[-1])
        logger.info(f"Пытаемся показать превью для чертежа с ID: {drawing_id}")

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT d.file_path, d.name, d.file_type, s.name as stamp_name, s.id as stamp_id, d.description
                FROM Drawings d
                JOIN Stamps s ON s.id = d.stamp_id
                WHERE d.id = ?
            """, (drawing_id,))

            result = cursor.fetchone()
            if not result:
                logger.warning(f"Чертёж с ID {drawing_id} не найден в базе данных")
                await query.message.edit_text(
                    "❌ Чертёж не найден.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="back_to_drawings")
                    ]])
                )
                return States.DRAWINGS_MENU

            file_path, drawing_name, file_type, stamp_name, stamp_id, description = result
            logger.info(f"Получены данные для чертежа: {drawing_name}, штамп: {stamp_name}")

            if not os.path.exists(file_path):
                logger.error(f"Файл не найден по пути: {file_path}")
                await query.message.edit_text(
                    "❌ Файл чертежа не найден на сервере.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="back_to_drawings")
                    ]])
                )
                return States.DRAWINGS_MENU

            # Формируем информацию о чертеже
            message = (
                f"📄 Информация о чертеже\n\n"
                f"Название: {drawing_name}\n"
                f"Тип файла: {file_type}\n"
                f"Штамп: {stamp_name}"
            )
            if description:
                message += f"\n\nОписание: {description}"

            keyboard = [
                [InlineKeyboardButton("📥 Скачать", callback_data=f"download_drawing_{drawing_id}")],
                [InlineKeyboardButton("🔙 К списку чертежей", callback_data=f"view_drawings_stamp_{stamp_id}")],
                [InlineKeyboardButton("🏠 В главное меню чертежей", callback_data="back_to_drawings")]
            ]

            await query.message.edit_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            logger.info("Превью чертежа успешно отображено")
            return States.DRAWINGS_MENU

        except Exception as db_error:
            logger.error(f"Ошибка при работе с базой данных: {db_error}", exc_info=True)
            raise
        finally:
            if conn:
                conn.close()

    except Exception as e:
        logger.error(f"Общая ошибка при предпросмотре чертежа: {e}", exc_info=True)
        try:
            await query.message.edit_text(
                "❌ Произошла ошибка при предпросмотре чертежа.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="back_to_drawings")
                ]])
            )
        except Exception as edit_error:
            logger.error(f"Ошибка при отправке сообщения об ошибке: {edit_error}", exc_info=True)
            await query.message.reply_text(
                "❌ Произошла ошибка при предпросмотре чертежа.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="back_to_drawings")
                ]])
            )
        return States.DRAWINGS_MENU