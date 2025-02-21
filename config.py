"""
Configuration Module - Модуль конфигурации
======================================

Этот модуль отвечает за загрузку и управление конфигурационными параметрами бота.
Использует переменные окружения для безопасного хранения чувствительных данных.
"""

import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение токена бота из переменных окружения
BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Проверка наличия обязательных переменных окружения
if not BOT_TOKEN:
    raise ValueError("Bot token not found in environment variables!")