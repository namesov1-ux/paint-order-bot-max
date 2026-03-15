# bot.py
import os
import sys
import logging
import asyncio
from flask import Flask, request, jsonify

from config.settings import settings
from core.dispatcher import Dispatcher
from core.adapters.max_adapter import MAXAdapter  # Импорт вынесен наверх
from handlers import start

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)

class PaintBot:
    def __init__(self):
        # Инициализация адаптера
        self.adapter = self._create_adapter()
        
        # Инициализация диспетчера
        self.dp = Dispatcher(self.adapter)
        
        # Подключение роутеров
        self.dp.include_router(start.router)
        
        # Устанавливаем ссылку на диспетчер в адаптере
        if hasattr(self.adapter, 'dispatcher'):
            self.adapter.dispatcher = self.dp
        
        logger.info("✅ Бот инициализирован")
    
    def _create_adapter(self):
        """Создает адаптер в зависимости от настроек"""
        logger.info(f"📱 Используется MAX адаптер")
        return MAXAdapter(settings.BOT_TOKEN, settings.MAX_API_URL)

# Глобальный экземпляр бота
bot = PaintBot()

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик вебхуков"""
    try:
        data = request.json
        logger.info(f"📡 Получен вебхук")
        
        # Создаем цикл событий и обрабатываем обновление
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(bot.dp.process_update(data))
        
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"❌ Ошибка вебхука: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/health', methods=['GET'])
def health():
    """Проверка здоровья"""
    return jsonify({
        "status": "healthy",
        "platform": settings.PLATFORM
    })

if __name__ == "__main__":
    # Запуск Flask приложения
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Бот запускается на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)