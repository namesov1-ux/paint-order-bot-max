# bot.py
import os
import sys
import logging
import asyncio
import json
from flask import Flask, request, jsonify

# Отключаем автоматический перезапуск Flask
os.environ['FLASK_RUN_FROM_CLI'] = 'false'

from config.settings import settings
from core.dispatcher import Dispatcher
from core.adapters.max_adapter import MAXAdapter
from handlers import start, search, vin_search

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class PaintBot:
    def __init__(self):
        self.adapter = MAXAdapter(settings.BOT_TOKEN, settings.MAX_API_URL)
        self.dp = Dispatcher(self.adapter)
        self.dp.include_router(start.router)
        self.dp.include_router(search.router)
        self.dp.include_router(vin_search.router)
        self.adapter.dispatcher = self.dp
        logger.info("✅ Бот инициализирован")
    
    async def process_webhook(self, data):
        return await self.dp.process_update(data)

# Глобальный экземпляр бота
bot = PaintBot()

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        logger.info(f"📡 Получен вебхук")
        
        # Создаём новый цикл событий для каждого запроса
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(bot.process_webhook(data))
            logger.info(f"✅ Результат обработки: {result}")
        finally:
            loop.close()
        
        return jsonify({"status": "ok", "processed": True})
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "bot": "paint_bot"
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🚀 Бот запускается на порту {port}")
    
    # Важно: запускаем Flask без debug режима
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        use_reloader=False,
        threaded=True
    )