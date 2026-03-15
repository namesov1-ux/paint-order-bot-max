# config/settings.py
import os
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

class Settings:
    # Платформа (max или telegram)
    PLATFORM = os.getenv("PLATFORM", "max")

    # Bot Settings
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

    # MAX Settings
    MAX_API_URL = os.getenv("MAX_API_URL", "https://api.max.ru/v1")

    # Telegram Settings
    TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL")

    # Google Sheets
    GOOGLE_SHEETS_URL = os.getenv("GOOGLE_SHEETS_URL")
    ORDERS_SHEET_NAME = os.getenv("ORDERS_SHEET_NAME", "orders")
    SETTINGS_SHEET_NAME = os.getenv("SETTINGS_SHEET_NAME", "settings")

    # Order Settings
    DEFAULT_MAX_ORDERS_PER_DAY = int(os.getenv("DEFAULT_MAX_ORDERS_PER_DAY", "10"))
    MIN_ORDER_GRAMS = int(os.getenv("MIN_ORDER_GRAMS", "50"))
    ORDER_STEP_GRAMS = int(os.getenv("ORDER_STEP_GRAMS", "50"))

    # VIN API
    AUTO_DEV_API_KEY = os.getenv("AUTO_DEV_API_KEY")

    # Web Panel
    WEB_PANEL_PORT = int(os.getenv("WEB_PANEL_PORT", "5000"))
    WEB_PANEL_SECRET = os.getenv("WEB_PANEL_SECRET", "change-me-in-production")

settings = Settings()
