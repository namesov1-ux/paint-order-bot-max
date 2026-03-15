# telegram_bot.py
import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🎨 Привет! Я бот для подбора краски по коду автомобиля.\n\n"
        "Отправьте мне код краски (например: 150, 50A, BC04), "
        "и я найду нужный цвет."
    )

# Обработка текстовых сообщений
@dp.message()
async def handle_paint_code(message: Message):
    paint_code = message.text.strip().upper()
    
    # Здесь будет логика поиска
    await message.answer(
        f"🔍 Ищу краску с кодом {paint_code}...\n\n"
        "⚙️ База данных подключается..."
    )

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())