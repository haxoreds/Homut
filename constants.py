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