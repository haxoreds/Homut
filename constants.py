"""
States Module - Модуль состояний диалога
=====================================

Этот модуль определяет все возможные состояния диалога в телеграм-боте.
Состояния используются для:
- Управления потоком диалога с пользователем
- Определения текущего контекста взаимодействия
- Организации переходов между различными функциями бота

Структура:
- Каждое состояние представляет определенный этап взаимодействия
- Состояния сгруппированы по функциональности
- Используется auto() для автоматической нумерации состояний
"""

from enum import Enum, auto

class States(Enum):
    """
    Перечисление всех возможных состояний диалога в боте.

    Группы состояний:
    1. Изменение количества (CHANGE_QTY_*)
    2. Добавление элементов (ADD_*)
    3. Редактирование/удаление (EDIT_DELETE_*)
    4. Совместимость деталей (COMPATIBILITY_*)
    5. Работа с чертежами (DRAWINGS_*)
    """

    # Состояния для изменения количества
    CHANGE_QTY_CHOOSING_ITEM = auto()      # Выбор элемента для изменения количества
    CHANGE_QTY_ADJUSTING_QUANTITY = auto() # Ввод нового количества
    CHANGE_QTY_CONFIRM_EXIT = auto()       # Подтверждение выхода из режима изменения

    # Состояния для добавления нового элемента
    ADD_ENTERING_DATA = auto()    # Ввод данных нового элемента
    ADD_CONFIRMATION = auto()     # Подтверждение добавления

    # Состояния для редактирования/удаления
    EDIT_DELETE_SELECT_ACTION = auto()  # Выбор действия (редактировать/удалить)
    EDIT_DELETE_CHOOSING = auto()       # Выбор элемента для редактирования/удаления
    EDIT_CHOOSING_FIELD = auto()        # Выбор поля для редактирования
    EDIT_ENTERING_VALUE = auto()        # Ввод нового значения
    EDIT_CONFIRM_EXIT = auto()          # Подтверждение выхода с несохраненными изменениями
    DELETE_CONFIRM = auto()             # Подтверждение удаления

    # Состояния для совместимости деталей
    COMPATIBILITY_MENU = auto()           # Главное меню совместимости
    CHECKING_COMPATIBILITY = auto()       # Проверка совместимости деталей
    ADDING_COMPATIBILITY_SOURCE = auto()  # Выбор исходного штампа
    ADDING_COMPATIBILITY_TARGET = auto()  # Выбор целевого штампа
    ADDING_COMPATIBILITY_TYPE = auto()    # Выбор типа совместимой детали
    ADDING_COMPATIBILITY_NAME = auto()    # Ввод названия совместимой детали
    ADDING_COMPATIBILITY_NOTES = auto()   # Добавление заметок о совместимости
    EDITING_COMPATIBILITY_CHOOSING = auto()  # Выбор записи для редактирования
    EDITING_COMPATIBILITY_ACTION = auto()    # Выбор действия редактирования

    # Состояния для работы с чертежами
    DRAWINGS_MENU = auto()                # Главное меню чертежей
    UPLOADING_DRAWING_STAMP = auto()      # Выбор штампа для загрузки чертежа
    UPLOADING_DRAWING_FILE = auto()       # Загрузка файла чертежа
    VIEWING_DRAWINGS = auto()             # Просмотр списка чертежей
    SEARCHING_DRAWINGS = auto()           # Поиск чертежей
    DRAWING_PREVIEW = auto()              # Предпросмотр чертежа
    DRAWING_DOWNLOAD = auto()             # Скачивание чертежа