# handlers/vin_search.py
import logging
import re
from core.dispatcher import Router
from services.vin_api import VINAPIService

logger = logging.getLogger(__name__)
router = Router(name="vin_search")

# Инициализируем сервис VIN API
vin_service = VINAPIService()

# Регулярка для проверки VIN (17 символов, без I, O, Q)
VIN_PATTERN = re.compile(r'^[A-HJ-NPR-Z0-9]{17}$')

# Временное хранилище для состояний подтверждения
pending_confirmations = {}

@router.message()
async def handle_vin_input(message):
    """Обработка ввода VIN-номера"""
    
    # Получаем текст сообщения
    text = message.text.strip().upper()
    
    # Пропускаем команды
    if text.startswith('/'):
        return
    
    # Проверяем, не ожидает ли пользователь подтверждения
    user_id = message.from_user.id
    if user_id in pending_confirmations:
        await handle_confirmation(message, pending_confirmations[user_id])
        return
    
    # Проверяем, похоже ли это на VIN (17 символов)
    if len(text) == 17 and VIN_PATTERN.match(text):
        await process_vin(message, text)
    else:
        # Если не VIN и не команда - игнорируем
        pass

async def process_vin(message, vin):
    """Обработка VIN-номера"""
    
    user_id = message.from_user.id
    
    # Отправляем сообщение о начале поиска
    await message.answer(f"🔍 Ищу информацию по VIN {vin}...")
    
    # Запрашиваем API
    vin_data = vin_service.decode_vin(vin)
    
    if not vin_data:
        await message.answer(
            "❌ Не удалось найти информацию по этому VIN.\n\n"
            "Возможные причины:\n"
            "• VIN введен неверно\n"
            "• Автомобиль отсутствует в базе\n"
            "• Технические проблемы с сервисом\n\n"
            "Попробуйте позже или введите код краски вручную."
        )
        return
    
    # Проверяем, есть ли код краски
    paint_code = vin_data.get('paint_code')
    
    if not paint_code:
        await message.answer(
            "❌ Не удалось определить код краски для этого автомобиля.\n\n"
            "Попробуйте ввести код краски вручную, если знаете его."
        )
        return
    
    # Формируем информацию об авто
    vehicle_info = vin_service.format_vehicle_info(vin_data)
    
    # Сохраняем данные для подтверждения
    pending_confirmations[user_id] = {
        'vin': vin,
        'data': vin_data,
        'paint_code': paint_code
    }
    
    # Запрашиваем подтверждение
    confirm_text = (
        f"✅ Найдена информация по VIN:\n\n"
        f"{vehicle_info}\n\n"
        f"Это ваш автомобиль?\n\n"
        f"Если да, напишите «Да»\n"
        f"Если нет — напишите «Нет»"
    )
    
    await message.answer(confirm_text)

async def handle_confirmation(message, pending_data):
    """Обработка подтверждения"""
    
    text = message.text.strip().lower()
    user_id = message.from_user.id
    
    if text in ['да', 'yes', 'д', 'y']:
        # Пользователь подтвердил
        paint_code = pending_data['paint_code']
        vehicle_info = vin_service.format_vehicle_info(pending_data['data'])
        
        # Удаляем из ожидания
        del pending_confirmations[user_id]
        
        # Предлагаем оформить заказ
        order_text = (
            f"🎨 Код краски: {paint_code}\n\n"
            f"Для заказа укажите:\n"
            f"• Требуемый объем (в мл)\n"
            f"• ФИО получателя\n"
            f"• Адрес доставки\n"
            f"• Телефон для связи\n\n"
            f"Или нажмите /order {paint_code} для быстрого оформления"
        )
        
        await message.answer(order_text)
        
    elif text in ['нет', 'no', 'н', 'n']:
        # Пользователь отклонил
        del pending_confirmations[user_id]
        await message.answer(
            "❌ Подтверждение отменено.\n\n"
            "Попробуйте ввести другой VIN или код краски вручную."
        )
    else:
        # Непонятный ответ - игнорируем
        pass
