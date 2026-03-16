# handlers/search.py
import logging
import re
from core.dispatcher import Router

logger = logging.getLogger(__name__)
router = Router(name="search")

# Временная тестовая база данных красок
PAINT_DATABASE = {
    # Код: [название, производитель, цена за 100мл]
    "150": ["Серебристый металлик", "Toyota", 1500],
    "150": ["Серебристый металлик", "Toyota", 1500],
    "040": ["Черный", "BMW", 1200],
    "041": ["Черный металлик", "BMW", 1800],
    "202": ["Белый", "Renault", 1100],
    "50A": ["Синий металлик", "Nissan", 2000],
    "BC04": ["Красный перламутр", "Mazda", 2200],
    "PZ0": ["Фиолетовый", "Mitsubishi", 1900],
    "B74": ["Голубой", "Ford", 1700],
    "NH0": ["Серый", "Honda", 1600],
}

# Поиск по частичному совпадению (например, "15" найдет "150")
@router.message()
async def search_paint(message):
    """Поиск краски по коду"""
    # Получаем текст сообщения
    query = message.text.strip().upper()
    
    logger.info(f"🔍 Поиск краски по запросу: {query}")
    
    # Проверяем, не команда ли это
    if query.startswith('/'):
        return  # Пропускаем команды, их обработают другие хендлеры
    
    # Если запрос слишком короткий
    if len(query) < 2:
        await message.answer(
            "❌ Слишком короткий код. Введите минимум 2 символа.\n"
            "Например: 15, 04, 50, BC"
        )
        return
    
    # Ищем совпадения
    results = []
    
    # Точное совпадение
    if query in PAINT_DATABASE:
        paint_info = PAINT_DATABASE[query]
        results.append({
            'code': query,
            'name': paint_info[0],
            'manufacturer': paint_info[1],
            'price': paint_info[2],
            'exact': True
        })
    
    # Частичное совпадение (код начинается с запроса)
    for code, paint_info in PAINT_DATABASE.items():
        if code != query and code.startswith(query):
            results.append({
                'code': code,
                'name': paint_info[0],
                'manufacturer': paint_info[1],
                'price': paint_info[2],
                'exact': False
            })
    
    # Если ничего не найдено
    if not results:
        await message.answer(
            f"❌ Краска с кодом {query} не найдена.\n\n"
            f"Попробуйте:\n"
            f"• Проверить правильность кода\n"
            f"• Ввести первые цифры кода\n"
            f"• Обратиться к администратору"
        )
        return
    
    # Формируем ответ
    if len(results) == 1 and results[0]['exact']:
        # Точное совпадение
        paint = results[0]
        response = (
            f"✅ Найдена краска:\n\n"
            f"🎨 Код: {paint['code']}\n"
            f"🏷️ Название: {paint['name']}\n"
            f"🚗 Производитель: {paint['manufacturer']}\n"
            f"💰 Цена: {paint['price']} руб/100мл\n\n"
            f"Для заказа напишите /order {paint['code']}"
        )
    else:
        # Несколько вариантов
        response = f"🔍 Найдено {len(results)} вариантов:\n\n"
        for i, paint in enumerate(results[:5], 1):  # Показываем первые 5
            exact_mark = "✅ " if paint['exact'] else ""
            response += (
                f"{i}. {exact_mark}Код: {paint['code']}\n"
                f"   {paint['name']} ({paint['manufacturer']})\n"
                f"   {paint['price']} руб/100мл\n\n"
            )
        
        if len(results) > 5:
            response += f"... и ещё {len(results) - 5} вариантов\n\n"
        
        response += "Уточните код для точного подбора"
    
    await message.answer(response)
