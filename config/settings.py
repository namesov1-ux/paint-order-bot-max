# config/settings.py
import os
from dotenv import load_dotenv
from typing import List, Optional

# Явно загружаем .env файл
load_dotenv()

class Settings:
    # Платформа (max или telegram)
    PLATFORM = os.getenv("PLATFORM", "max")

    # Bot Settings - проверяем что токен не None
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN не найден в переменных окружения!")
    
    ADMIN_IDS = []
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if admin_ids_str:
        ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]

    # MAX Settings
    MAX_API_URL = os.getenv("MAX_API_URL", "https://platform-api.max.ru")

    # Google Sheets
    GOOGLE_SHEETS_URL = os.getenv("GOOGLE_SHEETS_URL")
    ORDERS_SHEET_NAME = os.getenv("ORDERS_SHEET_NAME", "orders")
    SETTINGS_SHEET_NAME = os.getenv("SETTINGS_SHEET_NAME", "settings")

    # Order Settings
    DEFAULT_MAX_ORDERS_PER_DAY = int(os.getenv("DEFAULT_MAX_ORDERS_PER_DAY", "10"))
    MIN_ORDER_GRAMS = int(os.getenv("MIN_ORDER_GRAMS", "50"))
    ORDER_STEP_GRAMS = int(os.getenv("ORDER_STEP_GRAMS", "50"))

    # VIN API
    AUTO_DEV_API_KEY = os.getenv("AUTO_DEV_API_KEY", "")

    # Web Panel
    WEB_PANEL_PORT = int(os.getenv("WEB_PANEL_PORT", "5000"))
    WEB_PANEL_SECRET = os.getenv("WEB_PANEL_SECRET", "change-me-in-production")

    # Проверка обязательных переменных
    def validate(self):
        """Проверяет наличие обязательных переменных"""
        required_vars = {
            'BOT_TOKEN': self.BOT_TOKEN,
            'MAX_API_URL': self.MAX_API_URL,
        }
        
        missing = [name for name, value in required_vars.items() if not value]
        if missing:
            raise ValueError(f"❌ Отсутствуют обязательные переменные: {', '.join(missing)}")
        
        return True

# Создаём экземпляр настроек
settings = Settings()

# Проверяем настройки при импорте
try:
    settings.validate()
    print(f"✅ Настройки загружены. Платформа: {settings.PLATFORM}")
    print(f"✅ BOT_TOKEN: {settings.BOT_TOKEN[:10]}...")
except Exception as e:
    print(f"❌ Ошибка загрузки настроек: {e}")
    raise