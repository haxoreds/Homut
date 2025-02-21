"""
Logger Module - Модуль логирования
===============================

Этот модуль настраивает систему логирования для всего приложения.
Обеспечивает:
- Запись логов в консоль
- Форматирование сообщений логов
- Установку уровня логирования
"""

import logging
import sys

# Настройка логгера
logger = logging.getLogger('HomutBot')
logger.setLevel(logging.INFO)

# Создание обработчика консоли с повышенным уровнем логирования
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Создание форматтера для логов
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Добавление обработчика консоли к логгеру
logger.addHandler(console_handler)