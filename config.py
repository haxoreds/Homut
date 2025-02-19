import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get bot token from environment variable
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("Bot token not found in environment variables!")
