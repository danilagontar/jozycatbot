import os
from datetime import time

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROXY_URL = os.getenv("PROXY_URL")

MORNING_START = time(5, 0)
MORNING_END = time(12, 0)

EVENING_START = time(17, 0)
EVENING_END = time(23, 59)

DATABASE_PATH = "jozycat.db"