from enum import Enum, auto

class States(Enum):
    # Состояния для изменения количества
    CHANGE_QTY_CHOOSING_ITEM = auto()
    CHANGE_QTY_ADJUSTING_QUANTITY = auto()
    CHANGE_QTY_CONFIRM_EXIT = auto()

    # Состояния для добавления нового элемента
    ADD_ENTERING_DATA = auto()
    ADD_CONFIRMATION = auto()

    # Состояния для редактирования/удаления
    EDIT_DELETE_SELECT_ACTION = auto()  # Новое состояние для выбора действия
    EDIT_DELETE_CHOOSING = auto()    # Выбор элемента для редактирования/удаления
    EDIT_CHOOSING_FIELD = auto()     # Выбор поля для редактирования
    EDIT_ENTERING_VALUE = auto()     # Ввод нового значения
    EDIT_CONFIRM_EXIT = auto()       # Подтверждение выхода с несохраненными изменениями
    DELETE_CONFIRM = auto()          # Подтверждение удаления

    # Состояния для совместимости деталей
    COMPATIBILITY_MENU = auto()           # Главное меню совместимости
    CHECKING_COMPATIBILITY = auto()       # Проверка совместимости
    ADDING_COMPATIBILITY_SOURCE = auto()  # Выбор исходного штампа
    ADDING_COMPATIBILITY_TARGET = auto()  # Выбор целевого штампа
    ADDING_COMPATIBILITY_TYPE = auto()    # Выбор типа детали
    ADDING_COMPATIBILITY_NAME = auto()    # Ввод имени детали
    ADDING_COMPATIBILITY_NOTES = auto()   # Добавление заметок
    EDITING_COMPATIBILITY_CHOOSING = auto()  # Выбор совместимости для редактирования
    EDITING_COMPATIBILITY_ACTION = auto()    # Выбор действия для редактирования

    # Состояния для работы с чертежами
    DRAWINGS_MENU = auto()                # Главное меню чертежей
    UPLOADING_DRAWING_STAMP = auto()      # Выбор штампа для загрузки чертежа
    UPLOADING_DRAWING_FILE = auto()       # Загрузка файла чертежа
    VIEWING_DRAWINGS = auto()             # Просмотр списка чертежей
    SEARCHING_DRAWINGS = auto()           # Поиск чертежей
    DRAWING_PREVIEW = auto()              # Предпросмотр чертежа
    DRAWING_DOWNLOAD = auto()             # Скачивание чертежа