"""
Compatibility Module - Модуль управления совместимостью деталей
=========================================================

Этот модуль обеспечивает функциональность для:
- Проверки совместимости деталей между различными штампами
- Добавления новых записей о совместимости
- Редактирования существующих записей
- Удаления информации о совместимости

Основные возможности:
1. Проверка совместимости деталей между штампами
2. Добавление новых совместимых деталей
3. Редактирование существующих записей
4. Управление заметками о совместимости
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import get_connection
from menu import back_to_menu_keyboard
from constants import States

logger = logging.getLogger(__name__)

async def show_compatibility_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает главное меню управления совместимостью деталей.

    Параметры:
    - update (Update): Объект обновления от Telegram
    - context (ContextTypes.DEFAULT_TYPE): Контекст бота

    Возвращает:
    - States.COMPATIBILITY_MENU: Состояние меню совместимости

    Действия:
    1. Очищает временные данные пользователя
    2. Создает клавиатуру с опциями управления
    3. Отображает меню с возможными действиями
    """
    query = update.callback_query
    await query.answer()

    # Очищаем все временные данные при входе в меню
    context.user_data.clear()
    context.user_data['menu_path'] = ['main_menu', 'compatibility_menu']

    keyboard = [
        [InlineKeyboardButton("Проверить совместимость", callback_data="check_compatibility")],
        [InlineKeyboardButton("Добавить совместимость", callback_data="add_compatibility")],
        [InlineKeyboardButton("Изменить совместимость", callback_data="edit_compatibility")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back")]
    ]

    try:
        await query.message.edit_text(
            "Меню управления совместимостью деталей:\n"
            "Выберите необходимое действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return States.COMPATIBILITY_MENU
    except Exception as e:
        logger.error(f"Ошибка при показе меню совместимости: {e}", exc_info=True)
        # В случае ошибки возвращаемся в главное меню
        keyboard = [[InlineKeyboardButton("🔙 В главное меню", callback_data="back")]]
        await query.message.edit_text(
            "Произошла ошибка. Возвращаемся в главное меню.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END

async def check_compatibility(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню выбора штампа для проверки совместимости"""
    query = update.callback_query
    await query.answer()

    # Получаем список штампов из базы данных
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM Stamps ORDER BY name")
    stamps = cursor.fetchall()
    conn.close()

    keyboard = []
    for stamp_id, stamp_name in stamps:
        keyboard.append([InlineKeyboardButton(
            stamp_name, 
            callback_data=f"check_stamp_{stamp_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_compatibility")])

    await query.message.edit_text(
        "Выберите штамп, для которого хотите проверить совместимость деталей:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return States.CHECKING_COMPATIBILITY

async def show_compatible_parts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список совместимых деталей для выбранного штампа"""
    query = update.callback_query
    await query.answer()

    stamp_id = int(query.data.split('_')[2])

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Получаем информацию о выбранном штампе
        cursor.execute("SELECT name FROM Stamps WHERE id = ?", (stamp_id,))
        stamp_name = cursor.fetchone()[0]

        # Получаем список совместимых деталей
        cursor.execute("""
            SELECT 
                s.name as target_stamp,
                pc.part_type,
                pc.notes
            FROM Parts_Compatibility pc
            JOIN Stamps s ON s.id = pc.target_stamp_id
            WHERE pc.source_stamp_id = ?
            ORDER BY s.name, pc.part_type
        """, (stamp_id,))

        compatibilities = cursor.fetchall()

        if not compatibilities:
            message = f"Для штампа {stamp_name} не найдено совместимых деталей."
        else:
            message = f"Совместимые детали для штампа {stamp_name}:\n\n"
            current_stamp = None
            for target_stamp, part_type, notes in compatibilities:
                if current_stamp != target_stamp:
                    message += f"\n🔹 {target_stamp}:\n"
                    current_stamp = target_stamp
                message += f"  • {part_type}"
                if notes:
                    message += f" ({notes})"
                message += "\n"

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_stamp_list")]]

        await query.message.edit_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return States.CHECKING_COMPATIBILITY
    except Exception as e:
        logger.error(f"Ошибка при получении совместимых деталей: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_stamp_list")]]
        await query.message.edit_text(
            "❌ Произошла ошибка при получении списка совместимых деталей.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return States.CHECKING_COMPATIBILITY
    finally:
        conn.close()

async def add_compatibility_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс добавления новой совместимости"""
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
            callback_data=f"source_stamp_{stamp_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_compatibility")])

    await query.message.edit_text(
        "Выберите исходный штамп для добавления совместимости:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return States.ADDING_COMPATIBILITY_SOURCE

async def select_target_stamp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор целевого штампа для совместимости"""
    query = update.callback_query
    await query.answer()

    source_stamp_id = int(query.data.split('_')[2])
    context.user_data['source_stamp_id'] = source_stamp_id

    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем все штампы кроме исходного
    cursor.execute("""
        SELECT id, name 
        FROM Stamps 
        WHERE id != ? 
        ORDER BY name
    """, (source_stamp_id,))
    
    stamps = cursor.fetchall()
    conn.close()

    keyboard = []
    for stamp_id, stamp_name in stamps:
        keyboard.append([InlineKeyboardButton(
            stamp_name, 
            callback_data=f"target_stamp_{stamp_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_source_selection")])

    await query.message.edit_text(
        "Выберите штамп, с которым есть совместимые детали:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return States.ADDING_COMPATIBILITY_TARGET

async def select_part_type_and_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор типа детали и указание имени"""
    query = update.callback_query
    await query.answer()

    target_stamp_id = int(query.data.split('_')[2])
    context.user_data['target_stamp_id'] = target_stamp_id

    part_types = [
        ("Пуансоны", "Punches"),
        ("Вставки", "Inserts"),
        ("Ножи", "Knives"),
        ("Кулачки", "Clamps"),
        ("Запчасти диска", "Disc_Parts"),
        ("Толкатели", "Pushers"),
        ("Запчасти", "Parts")
    ]

    keyboard = []
    for display_name, table_name in part_types:
        keyboard.append([InlineKeyboardButton(
            display_name, 
            callback_data=f"part_type_{table_name}"
        )])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_target_selection")])

    await query.message.edit_text(
        "1. Выберите тип деталей для проверки совместимости\n"
        "2. Затем вы сможете выбрать конкретную деталь из базы данных",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return States.ADDING_COMPATIBILITY_TYPE

async def handle_part_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор имени детали из существующих в базе"""
    query = update.callback_query
    await query.answer()

    part_type = query.data.split('_')[2]
    context.user_data['part_type'] = part_type

    # Используем точное имя таблицы из базы данных
    table_name = part_type  # Имя таблицы уже в правильном формате

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Получаем список деталей для выбранного штампа
        source_stamp_id = context.user_data.get('source_stamp_id')
        cursor.execute(f"""
            SELECT id, name, size, description 
            FROM {table_name} 
            WHERE stamp_id = ?
            ORDER BY name
        """, (source_stamp_id,))

        parts = cursor.fetchall()

        if not parts:
            await query.message.edit_text(
                f"❌ В базе нет деталей типа '{table_name}' для выбранного штампа.\n"
                "Сначала добавьте детали в инвентарь штампа.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="back_to_type_selection")
                ]])
            )
            return States.ADDING_COMPATIBILITY_TYPE

        keyboard = []
        for part_id, name, size, description in parts:
            display_text = name
            if size:
                display_text += f" ({size})"
            if description:
                display_text += f" - {description}"
            keyboard.append([InlineKeyboardButton(
                display_text,
                callback_data=f"select_part_{name}"
            )])

        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_type_selection")])

        await query.message.edit_text(
            "Выберите существующую деталь из списка:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return States.ADDING_COMPATIBILITY_NAME
    
    except Exception as e:
        logger.error(f"Ошибка при получении списка деталей: {e}")
        await query.message.edit_text(
            "❌ Произошла ошибка при получении списка деталей.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_type_selection")
            ]])
        )
        return States.ADDING_COMPATIBILITY_TYPE
    finally:
        conn.close()

async def handle_part_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора конкретной детали"""
    query = update.callback_query
    await query.answer()

    part_name = query.data.split('_', 2)[2]  # select_part_NAME -> NAME
    context.user_data['part_name'] = part_name

    keyboard = [[InlineKeyboardButton("Пропустить", callback_data="skip_notes")]]

    await query.message.edit_text(
        "Введите дополнительные заметки о совместимости (например, особенности или ограничения)\n"
        "или нажмите 'Пропустить', если заметки не требуются:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return States.ADDING_COMPATIBILITY_NOTES

async def select_part_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор типа совместимых деталей"""
    query = update.callback_query
    await query.answer()

    target_stamp_id = int(query.data.split('_')[2])
    context.user_data['target_stamp_id'] = target_stamp_id

    part_types = [
        ("Пуансоны", "punches"),
        ("Вставки", "inserts"),
        ("Ножи", "knives"),
        ("Кулачки", "cams"),
        ("Диски", "discs"),
        ("Запчасти диска", "discparts"),
        ("Толкатели", "pushers"),
        ("Запчасти", "parts")
    ]

    keyboard = []
    for display_name, type_id in part_types:
        keyboard.append([InlineKeyboardButton(
            display_name, 
            callback_data=f"part_type_{type_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_target_selection")])

    await query.message.edit_text(
        "Выберите тип совместимых деталей:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return States.ADDING_COMPATIBILITY_TYPE

async def add_compatibility_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрашивает дополнительные заметки о совместимости"""
    query = update.callback_query
    await query.answer()

    part_type = query.data.split('_')[2]
    context.user_data['part_type'] = part_type

    keyboard = [[InlineKeyboardButton("Пропустить", callback_data="skip_notes")]]

    await query.message.edit_text(
        "Введите дополнительные заметки о совместимости (например, особенности или ограничения)\n"
        "или нажмите 'Пропустить', если заметки не требуются:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return States.ADDING_COMPATIBILITY_NOTES

async def save_compatibility(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет информацию о совместимости в базу данных"""
    if update.callback_query and update.callback_query.data == "skip_notes":
        await update.callback_query.answer()
        notes = None
    elif update.message:
        notes = update.message.text

    source_stamp_id = context.user_data['source_stamp_id']
    target_stamp_id = context.user_data['target_stamp_id']
    part_type = context.user_data['part_type']
    part_name = context.user_data.get('part_name', '')

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Формируем полное описание типа детали с именем
        full_part_type = f"{part_type} - {part_name}" if part_name else part_type

        cursor.execute("""
            INSERT INTO Parts_Compatibility 
            (source_stamp_id, target_stamp_id, part_type, notes) 
            VALUES (?, ?, ?, ?)
        """, (source_stamp_id, target_stamp_id, full_part_type, notes))

        # Добавляем обратную совместимость
        cursor.execute("""
            INSERT INTO Parts_Compatibility 
            (source_stamp_id, target_stamp_id, part_type, notes) 
            VALUES (?, ?, ?, ?)
        """, (target_stamp_id, source_stamp_id, full_part_type, notes))

        conn.commit()

        # Получаем названия штампов для сообщения
        cursor.execute("SELECT name FROM Stamps WHERE id IN (?, ?)", 
                      (source_stamp_id, target_stamp_id))
        stamps = cursor.fetchall()
        source_stamp_name = stamps[0][0]
        target_stamp_name = stamps[1][0]

        message = (f"✅ Совместимость успешно добавлена!\n\n"
                  f"Штампы: {source_stamp_name} ⟷ {target_stamp_name}\n"
                  f"Тип детали: {full_part_type}")

        if notes:
            message += f"\nЗаметки: {notes}"

    except Exception as e:
        logger.error(f"Ошибка при сохранении совместимости: {e}")
        message = "❌ Произошла ошибка при сохранении совместимости."
        conn.rollback()
    finally:
        conn.close()

    # Создаем клавиатуру с кнопкой возврата в главное меню
    keyboard = [[InlineKeyboardButton("🔙 В главное меню", callback_data="back")]]

    if update.callback_query:
        await update.callback_query.message.edit_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Очищаем данные пользователя
    context.user_data.clear()

    return ConversationHandler.END

async def edit_compatibility_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс редактирования совместимости"""
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Получаем список существующих совместимостей с уникальными комбинациями
        cursor.execute("""
            SELECT DISTINCT 
                pc1.id,
                s1.name as source_stamp,
                s2.name as target_stamp,
                pc1.part_type,
                pc1.notes
            FROM Parts_Compatibility pc1
            JOIN Stamps s1 ON s1.id = pc1.source_stamp_id
            JOIN Stamps s2 ON s2.id = pc1.target_stamp_id
            WHERE NOT EXISTS (
                SELECT 1 
                FROM Parts_Compatibility pc2
                WHERE pc2.source_stamp_id = pc1.target_stamp_id
                AND pc2.target_stamp_id = pc1.source_stamp_id
                AND pc2.id < pc1.id
            )
            ORDER BY s1.name, s2.name, pc1.part_type
        """)

        compatibilities = cursor.fetchall()

        if not compatibilities:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_compatibility")]]
            await query.message.edit_text(
                "В базе данных нет сохраненных совместимостей для редактирования.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return States.COMPATIBILITY_MENU

        keyboard = []
        for comp_id, source, target, part_type, notes in compatibilities:
            display_text = f"{source} ↔ {target}: {part_type}"
            if notes:
                display_text += f" ({notes})"
            keyboard.append([InlineKeyboardButton(
                display_text,
                callback_data=f"edit_compat_{comp_id}"
            )])

        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_compatibility")])

        await query.message.edit_text(
            "Выберите запись для редактирования:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return States.EDITING_COMPATIBILITY_CHOOSING

    except Exception as e:
        logger.error(f"Ошибка при получении списка совместимостей: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_compatibility")]]
        await query.message.edit_text(
            "❌ Произошла ошибка при получении списка совместимостей.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return States.COMPATIBILITY_MENU
    finally:
        conn.close()

async def handle_edit_compatibility_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора совместимости для редактирования"""
    query = update.callback_query
    await query.answer()

    comp_id = int(query.data.split('_')[2])
    context.user_data['editing_compatibility_id'] = comp_id

    # Получаем текущую информацию о совместимости
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pc.part_type, pc.notes,
               s1.name as source_stamp,
               s2.name as target_stamp
        FROM Parts_Compatibility pc
        JOIN Stamps s1 ON s1.id = pc.source_stamp_id
        JOIN Stamps s2 ON s2.id = pc.target_stamp_id
        WHERE pc.id = ?
    """, (comp_id,))

    compatibility = cursor.fetchone()
    conn.close()

    if not compatibility:
        await query.message.edit_text(
            "❌ Ошибка: Совместимость не найдена.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_compat_list")
            ]])
        )
        return States.COMPATIBILITY_MENU

    part_type, notes, source_stamp, target_stamp = compatibility
    message = (f"Текущая совместимость:\n"
              f"Штампы: {source_stamp} ↔ {target_stamp}\n"
              f"Тип детали: {part_type}\n")
    if notes:
        message += f"Заметки: {notes}\n"

    message += "\nВыберите действие:"

    keyboard = [
        [InlineKeyboardButton("Изменить заметки", callback_data="edit_compat_notes")],
        [InlineKeyboardButton("Удалить совместимость", callback_data="delete_compat")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_compat_list")]
    ]

    await query.message.edit_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return States.EDITING_COMPATIBILITY_ACTION

async def handle_edit_compatibility_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка удаления совместимости"""
    query = update.callback_query
    await query.answer()

    comp_id = context.user_data.get('editing_compatibility_id')
    if not comp_id:
        await query.message.edit_text(
            "❌ Ошибка: Не удалось определить совместимость для удаления.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_compat_list")
            ]])
        )
        return States.COMPATIBILITY_MENU

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Получаем информацию о совместимости перед удалением
        cursor.execute("""
            SELECT 
                s1.name, s2.name, pc.part_type,
                pc.source_stamp_id, pc.target_stamp_id
            FROM Parts_Compatibility pc
            JOIN Stamps s1 ON s1.id = pc.source_stamp_id
            JOIN Stamps s2 ON s2.id = pc.target_stamp_id
            WHERE pc.id = ?
        """, (comp_id,))
        compatibility = cursor.fetchone()

        if compatibility:
            source_stamp, target_stamp, part_type, source_id, target_id = compatibility

            # Удаляем прямую и обратную записи о совместимости
            cursor.execute("""
                DELETE FROM Parts_Compatibility 
                WHERE (source_stamp_id = ? AND target_stamp_id = ?) 
                OR (source_stamp_id = ? AND target_stamp_id = ?)
            """, (source_id, target_id, target_id, source_id))

            conn.commit()

            message = (f"✅ Совместимость успешно удалена:\n"
                      f"Штампы: {source_stamp} ↔ {target_stamp}\n"
                      f"Тип детали: {part_type}")
        else:
            message = "❌ Ошибка: Совместимость не найдена."

    except Exception as e:
        logger.error(f"Ошибка при удалении совместимости: {e}")
        message = "❌ Произошла ошибка при удалении совместимости."
        conn.rollback()

    finally:
        conn.close()

    keyboard = [[InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_compatibility")]]
    await query.message.edit_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
    return States.COMPATIBILITY_MENU

async def handle_edit_compatibility_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка изменения заметок совместимости"""
    query = update.callback_query
    await query.answer()

    comp_id = context.user_data.get('editing_compatibility_id')
    if not comp_id:
        await query.message.edit_text(
            "❌ Ошибка: Не удалось определить совместимость для редактирования.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_compat_list")
            ]])
        )
        return States.COMPATIBILITY_MENU

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_compat_list")]]
    await query.message.edit_text(
        "Введите новые заметки для совместимости:\n"
        "Или нажмите 'Назад' для возврата.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data['editing_notes'] = True
    return States.ADDING_COMPATIBILITY_NOTES

async def save_edited_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение отредактированных заметок"""
    if not update.message:
        return States.COMPATIBILITY_MENU

    comp_id = context.user_data.get('editing_compatibility_id')
    new_notes = update.message.text

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE Parts_Compatibility 
            SET notes = ?, updatedAt = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_notes, comp_id))
        conn.commit()
        message = "✅ Заметки успешно обновлены!"
    except Exception as e:
        logger.error(f"Ошибка при обновлении заметок: {e}")
        message = "❌ Произошла ошибка при обновлении заметок."
    finally:
        conn.close()

    keyboard = [[InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_compatibility")]]
    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
    return States.COMPATIBILITY_MENU

# Функции для обработки кнопки "Назад"
async def back_to_compatibility_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню совместимости"""
    query = update.callback_query
    await query.answer()

    try:
        # Полностью очищаем временные данные
        context.user_data.clear()
        context.user_data['menu_path'] = ['main_menu', 'compatibility_menu']

        keyboard = [
            [InlineKeyboardButton("Проверить совместимость", callback_data="check_compatibility")],
            [InlineKeyboardButton("Добавить совместимость", callback_data="add_compatibility")],
            [InlineKeyboardButton("Изменить совместимость", callback_data="edit_compatibility")],
            [InlineKeyboardButton("🔙 В главное меню", callback_data="back")]
        ]

        await query.message.edit_text(
            "Меню управления совместимостью деталей:\n"
            "Выберите необходимое действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return States.COMPATIBILITY_MENU

    except Exception as e:
        logger.error(f"Ошибка при возврате в меню совместимости: {e}", exc_info=True)
        try:
            # В случае ошибки отправляем новое сообщение
            keyboard = [[InlineKeyboardButton("🔙 В главное меню", callback_data="back")]]
            await query.message.reply_text(
                "Произошла ошибка. Возвращаемся в главное меню.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as reply_error:
            logger.error(f"Ошибка при отправке сообщения об ошибке: {reply_error}", exc_info=True)
        return ConversationHandler.END

async def back_to_stamp_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к списку штампов"""
    query = update.callback_query
    await query.answer()

    # Очищаем временные данные
    for key in ['editing_compatibility_id', 'editing_notes', 'source_stamp_id', 'target_stamp_id', 'part_type', 'part_name']:
        if key in context.user_data:
            del context.user_data[key]

    # Получаем список штампов из базы данных
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM Stamps ORDER BY name")
    stamps = cursor.fetchall()
    conn.close()

    keyboard = []
    for stamp_id, stamp_name in stamps:
        keyboard.append([InlineKeyboardButton(
            stamp_name, 
            callback_data=f"check_stamp_{stamp_id}"
        )])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_compatibility")])

    await query.message.edit_text(
        "Выберите штамп, для которого хотите проверить совместимость деталей:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return States.CHECKING_COMPATIBILITY

async def back_to_source_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к выбору исходного штампа"""
    # Очищаем временные данные, кроме необходимых для навигации
    for key in ['target_stamp_id', 'part_type', 'part_name']:
        if key in context.user_data:
            del context.user_data[key]
    return await add_compatibility_start(update, context)

async def back_to_target_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к выбору целевого штампа"""
    # Очищаем временные данные, сохраняя source_stamp_id
    for key in ['part_type', 'part_name']:
        if key in context.user_data:
            del context.user_data[key]
    return await select_target_stamp(update, context)

async def back_to_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к выбору типа детали"""
    # Очищаем временные данные, сохраняя stamp_ids
    if 'part_name' in context.user_data:
        del context.user_data['part_name']
    return await select_part_type_and_name(update, context)

async def back_to_compat_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к списку совместимостей"""
    # Очищаем все временные данные редактирования
    for key in ['editing_compatibility_id', 'editing_notes']:
        if key in context.user_data:
            del context.user_data[key]
    return await edit_compatibility_start(update, context)