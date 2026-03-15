# handlers/start.py
import logging
from core.dispatcher import Router

logger = logging.getLogger(__name__)
router = Router(name="start")

@router.message()
async def start_handler(message):
    """Обработчик команды /start"""
    logger.info(f"🚀 Старт от пользователя {message.from_user.id}")
    
    welcome_text = (
        "👋 Добро пожаловать в бот подбора краски по коду автомобиля!\n\n"
        "Я помогу вам найти краску по VIN номеру или коду.\n\n"
        "Просто отправьте мне код краски (например: 150, 50A, BC04), "
        "и я покажу доступные варианты."
    )
    
    await message.answer(welcome_text)
