import os
from datetime import time

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROXY_URL = os.getenv("PROXY_URL")

ALLOWED_USER_IDS = {
    int(user_id.strip())
    for user_id in os.getenv("ALLOWED_USER_IDS", "").split(",")
    if user_id.strip()
}

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

MORNING_START = time(5, 0)
MORNING_END = time(12, 0)

EVENING_START = time(17, 0)
EVENING_END = time(23, 59)

DATABASE_PATH = "jozycat.db"