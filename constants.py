from enum import Enum, auto

class States(Enum):
    # Состояния для изменения количества
    CHANGE_QTY_CHOOSING_ITEM = auto()
    CHANGE_QTY_ADJUSTING_QUANTITY = auto()
    CHANGE_QTY_CONFIRM_EXIT = auto()

    # Состояния для добавления нового элемента
    ADD_ENTERING_DATA = auto()
    ADD_CONFIRMATION = auto()

    # Состояния для редактирования
    EDIT_CHOOSE_ACTION = auto()
    EDIT_CHOOSE_ITEM = auto()
    EDIT_CHOOSE_FIELD = auto()
    EDIT_VALUE = auto()
    EDIT_CONFIRM_DELETE = auto()
  
