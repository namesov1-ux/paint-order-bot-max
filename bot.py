# bot.py
import os
import sys
import logging
import asyncio
import json
from flask import Flask, request, jsonify

# Отключаем автоматический перезапуск Flask
os.environ['FLASK_RUN_FROM_CLI'] = 'false'
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

from config.settings import settings
from core.dispatcher import Dispatcher
from core.adapters.max_adapter import MAXAdapter
from handlers import start

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,  # Временно ставим DEBUG для подробной отладки
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('webhook_debug.log')  # Сохраняем логи в файл
    ]
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

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    """Обработчик вебхуков с подробной отладкой"""
    
    # Логируем метод запроса
    logger.info(f"📡 Получен {request.method} запрос на /webhook")
    
    # Логируем заголовки запроса
    logger.debug(f"📋 Заголовки: {dict(request.headers)}")
    
    # Для GET-запросов (например, проверка от MAX)
    if request.method == 'GET':
        logger.info("👋 Получен GET-запрос (возможно проверка от MAX)")
        return jsonify({
            "status": "ok",
            "message": "Webhook endpoint is active",
            "method": "GET"
        })
    
    # Для POST-запросов (основные события)
    try:
        # Получаем данные
        data = request.json
        logger.info(f"📦 Получены данные: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # Проверяем, есть ли данные
        if not data:
            logger.warning("⚠️ Пустой запрос")
            return jsonify({"status": "error", "message": "Empty request"}), 400
        
        # Проверяем структуру данных
        logger.info(f"🔍 Ключи в данных: {list(data.keys())}")
        
        # Создаем цикл событий и обрабатываем обновление
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(bot.dp.process_update(data))
            logger.info(f"✅ Результат обработки: {result}")
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке в диспетчере: {e}", exc_info=True)
            result = False
        finally:
            loop.close()
        
        return jsonify({"status": "ok", "processed": result})
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка вебхука: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Проверка здоровья"""
    logger.debug("✅ Health check")
    return jsonify({
        "status": "healthy",
        "platform": settings.PLATFORM,
        "bot": "paint_bot"
    })

@app.route('/debug', methods=['GET'])
def debug_info():
    """Отладочная информация"""
    return jsonify({
        "bot_initialized": True,
        "platform": settings.PLATFORM,
        "handlers": {
            "message": len(bot.dp.message_handlers),
            "callback": len(bot.dp.callback_handlers)
        }
    })

if __name__ == "__main__":
    # Запуск Flask приложения
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Бот запускается на порту {port}")
    logger.info(f"🐛 Режим отладки: ВЫКЛЮЧЕН")
    
    # Жёстко отключаем debug и reloader
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=False, 
        use_reloader=False,
        threaded=True
    )