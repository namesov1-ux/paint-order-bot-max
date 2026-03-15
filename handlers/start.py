# handlers/start.py
import logging
from core.dispatcher import Router

logger = logging.getLogger(__name__)
router = Router(name="start")

@router.message()
async def start_handler(message):
    """Обработчик команды /start"""
    logger.info(f"Старт от пользователя {message.from_user.id}")
    
    welcome_text = (
        "👋 Добро пожаловать в бот подбора краски по VIN!\n\n"
        "Я помогу вам:\n"
        "🔍 Найти код краски по VIN номеру автомобиля\n"
        "🎨 Оформить заказ на изготовление краски\n"
        "📅 Выбрать удобную дату получения\n\n"
        "Выберите действие:"
    )
    
    # Здесь будет клавиатура с выбором действия
    await message.reply(welcome_text)
