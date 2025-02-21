"""
Menu Module - Модуль структуры меню
================================

Этот модуль определяет структуру меню телеграм-бота и функции для работы с ним.
Содержит:
- Определение структуры всех меню и подменю
- Функции создания подменю для каждого штампа
- Функции генерации клавиатур
- Обработчики действий меню
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# Определение основной структуры меню
menu = {
    'main_menu': {
        'text': 'Главное меню',
        'buttons': {
            'Инвентарь штампов': 'inventory_stamps',
            'Совместимость деталей': 'compatibility_parts',
            'Чертежи': 'drawings',
            'Учёт болтов': 'bolt_accounting',
            'Канцелярия': 'stationery',
            'Настройка Штампов': 'stamp_settings',
            'Вывод информации в EXCEL': 'export_to_excel',
        },
    },
    'compatibility_menu': {
        'text': 'Меню совместимости деталей',
        'buttons': {
            'Проверить совместимость': 'check_compatibility',
            'Добавить совместимость': 'add_compatibility',
            'Изменить совместимость': 'edit_compatibility',
            'Назад': 'back',
        },
    },
}

def create_inventory_submenus(inv_id, inv_name):
    """
    Создает подменю для конкретного штампа.

    Параметры:
    - inv_id (str): Идентификатор штампа
    - inv_name (str): Название штампа

    Создает следующие подменю:
    1. Инвентарь штампа
    2. Меню штампа (пуансоны, вставки, запчасти)
    3. Меню пуансонов
    4. Меню вставок
    5. Меню запчастей штампа
    6. Меню ножей
    7. Меню дисков
    8. Меню запчастей диска
    9. Меню толкателей
    10. Меню кулачков
    """
    # Инвентарь штампов
    menu[f'inventory_{inv_id}'] = {
        'text': f'Инвентарь {inv_name}',
        'buttons': {
            'Штамп': f'stamp_{inv_id}',
            'Ножи': f'knives_{inv_id}',
            'Диски': f'discs_{inv_id}',
            'Кулачки': f'cams_{inv_id}',
            'Назад': 'back',
        },
    }
    # Штамп
    menu[f'stamp_{inv_id}'] = {
        'text': f'Штамп {inv_name}',
        'buttons': {
            'Пуансоны': f'punches_{inv_id}',
            'Вставки': f'inserts_{inv_id}',
            'Запчасти для штампа': f'stampparts_{inv_id}',
            'Назад': 'back',
        },
    }
    # Пуансоны
    menu[f'punches_{inv_id}'] = {
        'text': f'Пуансоны {inv_name}',
        'buttons': {
            'Показать остаток': f'showbalancepunches{inv_id}',
            'Добавить новую позицию': f'addnewitempunches{inv_id}',
            'Изменить или удалить данные в базе': f'editdeletepunches{inv_id}',
            'Назад': 'back',
        },
    }
    # Вставки
    menu[f'inserts_{inv_id}'] = {
        'text': f'Вставки {inv_name}',
        'buttons': {
            'Показать остаток': f'showbalanceinserts{inv_id}',
            'Добавить новую позицию': f'addnewiteminserts{inv_id}',
            'Изменить или удалить данные в базе': f'editdeleteinserts{inv_id}',
            'Назад': 'back',
        },
    }
    # Запчасти для штампа
    menu[f'stampparts_{inv_id}'] = {
        'text': f'Запчасти для штампа {inv_name}',
        'buttons': {
            'Показать остаток': f'showbalancestampparts{inv_id}',
            'Добавить новую позицию': f'addnewitemstampparts{inv_id}',
            'Изменить или удалить данные в базе': f'editdeletestampparts{inv_id}',
            'Назад': 'back',
        },
    }
    # Ножи
    menu[f'knives_{inv_id}'] = {
        'text': f'Ножи {inv_name}',
        'buttons': {
            'Показать остаток': f'showbalanceknives{inv_id}',
            'Добавить новую позицию': f'addnewitemknives{inv_id}',
            'Изменить или удалить данные в базе': f'editdeleteknives{inv_id}',
            'Назад': 'back',
        },
    }
    # Диски
    menu[f'discs_{inv_id}'] = {
        'text': f'Диски {inv_name}',
        'buttons': {
            'Запчасти для диска': f'discparts_{inv_id}',
            'Толкатели': f'pushers_{inv_id}',
            'Назад': 'back',
        },
    }
    # Запчасти для диска
    menu[f'discparts_{inv_id}'] = {
        'text': f'Запчасти для диска {inv_name}',
        'buttons': {
            'Показать остаток': f'showbalancediscparts{inv_id}',
            'Добавить новую позицию': f'addnewitemdiscparts{inv_id}',
            'Изменить или удалить данные в базе': f'editdeletediscparts{inv_id}',
            'Назад': 'back',
        },
    }
    # Толкатели
    menu[f'pushers_{inv_id}'] = {
        'text': f'Толкатели {inv_name}',
        'buttons': {
            'Показать остаток': f'showbalancepushers{inv_id}',
            'Добавить новую позицию': f'addnewitempushers{inv_id}',
            'Изменить или удалить данные в базе': f'editdeletepushers{inv_id}',
            'Назад': 'back',
        },
    }
    # Кулачки
    menu[f'cams_{inv_id}'] = {
        'text': f'Кулачки {inv_name}',
        'buttons': {
            'Показать остаток': f'showbalancecams{inv_id}',
            'Добавить новую позицию': f'addnewitemcams{inv_id}',
            'Изменить или удалить данные в базе': f'editdeletecams{inv_id}',
            'Назад': 'back',
        },
    }

# Список инвентаря штампов с их идентификаторами
inventory_list = [
    ('11_3', '11.3'),
    ('12_8', '12.8'),
    ('13_3_dwb_new', '13.3 dwb new'),
    ('13_3_dwb_2', '13.3 dwb 2'),
    ('13_3_old', '13.3 old'),
    ('14_0', '14.0'),
]

# Создание подменю для каждого штампа
for inv_id, inv_name in inventory_list:
    create_inventory_submenus(inv_id, inv_name)

# Определение основного меню инвентаря штампов
menu['inventory_stamps'] = {
    'text': 'Инвентарь штампов',
    'buttons': {
        **{inv_name: f'inventory_{inv_id}' for inv_id, inv_name in inventory_list},
        'Назад': 'back'
    },
}

def get_menu_keyboard(menu_name):
    """
    Создает клавиатуру для указанного меню.

    Параметры:
    - menu_name (str): Имя меню

    Возвращает:
    - InlineKeyboardMarkup: Объект клавиатуры с кнопками
    """
    buttons = []
    for button_text, callback_data in menu[menu_name]['buttons'].items():
        buttons.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    return InlineKeyboardMarkup(buttons)

def back_to_menu_keyboard(menu_name):
    """
    Создает клавиатуру только с кнопкой "Назад".

    Параметры:
    - menu_name (str): Имя меню для возврата

    Возвращает:
    - InlineKeyboardMarkup: Объект клавиатуры с кнопкой "Назад"
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад", callback_data='back')]
    ])

async def process_main_menu_action(action, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает действия главного меню.

    Параметры:
    - action (str): Идентификатор действия
    - update (Update): Объект обновления от Telegram
    - context (ContextTypes.DEFAULT_TYPE): Контекст бота

    Действия:
    1. Обрабатывает различные действия меню
    2. Отправляет соответствующие сообщения
    3. Показывает подходящие клавиатуры
    """
    if action == 'compatibility_parts':
        await update.callback_query.message.reply_text(
            "Меню совместимости деталей",
            reply_markup=get_menu_keyboard('compatibility_menu')
        )
    elif action == 'check_compatibility':
        await update.callback_query.message.reply_text(
            "Показываю проверку совместимости деталей.",
            reply_markup=back_to_menu_keyboard(context.user_data.get('current_menu', 'main_menu'))
        )
    elif action == 'add_compatibility':
        await update.callback_query.message.reply_text(
            "Показываю добавление совместимости деталей.",
            reply_markup=back_to_menu_keyboard(context.user_data.get('current_menu', 'main_menu'))
        )
    elif action == 'edit_compatibility':
        await update.callback_query.message.reply_text(
            "Показываю изменение совместимости деталей.",
            reply_markup=back_to_menu_keyboard(context.user_data.get('current_menu', 'main_menu'))
        )
    elif action == 'bolt_accounting':
        await update.callback_query.message.reply_text(
            "Показываю учёт болтов.",
            reply_markup=back_to_menu_keyboard(context.user_data.get('current_menu', 'main_menu'))
        )
    elif action == 'stationery':
        await update.callback_query.message.reply_text(
            "Показываю канцелярию.",
            reply_markup=back_to_menu_keyboard(context.user_data.get('current_menu', 'main_menu'))
        )
    elif action == 'stamp_settings':
        await update.callback_query.message.reply_text(
            "Показываю настройку штампов.",
            reply_markup=back_to_menu_keyboard(context.user_data.get('current_menu', 'main_menu'))
        )
    elif action == 'export_to_excel':
        await update.callback_query.message.reply_text(
            "Вывожу информацию в EXCEL.",
            reply_markup=back_to_menu_keyboard(context.user_data.get('current_menu', 'main_menu'))
        )
    elif action == 'back':
        await update.callback_query.message.reply_text(
            "Возвращаюсь в главное меню.",
            reply_markup=get_menu_keyboard('main_menu')
        )
    else:
        await update.callback_query.message.reply_text(
            "Действие не распознано.",
            reply_markup=back_to_menu_keyboard(context.user_data.get('current_menu', 'main_menu'))
        )