# bot.py
import os
import sys
import logging
import asyncio
import json
from datetime import datetime
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
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('webhook_debug.log')
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
    """Обработчик вебхуков с максимальной отладкой"""
    
    request_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    
    # Логируем метод запроса
    logger.info(f"📡 [{request_id}] Получен {request.method} запрос на /webhook")
    
    # Логируем заголовки запроса
    logger.debug(f"📋 [{request_id}] Заголовки: {dict(request.headers)}")
    
    # Для GET-запросов (например, проверка от MAX)
    if request.method == 'GET':
        logger.info(f"👋 [{request_id}] Получен GET-запрос (возможно проверка от MAX)")
        return jsonify({
            "status": "ok",
            "message": "Webhook endpoint is active",
            "method": "GET",
            "request_id": request_id
        })
    
    # Для POST-запросов (основные события)
    try:
        # Получаем данные
        data = request.json
        
        # Логируем сырые данные
        logger.info(f"📦 [{request_id}] СЫРЫЕ ДАННЫЕ (type: {type(data)}):")
        logger.info(f"📦 [{request_id}] {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # Проверяем, есть ли данные
        if not data:
            logger.warning(f"⚠️ [{request_id}] Пустой запрос")
            return jsonify({"status": "error", "message": "Empty request"}), 400
        
        # Анализируем структуру данных
        logger.info(f"🔍 [{request_id}] АНАЛИЗ СТРУКТУРЫ ДАННЫХ:")
        logger.info(f"🔍 [{request_id}] Все ключи верхнего уровня: {list(data.keys())}")
        
        # Проверяем наличие поля с информацией о пользователе
        user_fields = ['from', 'user', 'sender', 'author', 'creator', 'owner']
        for field in user_fields:
            if field in data:
                logger.info(f"✅ [{request_id}] Найдено поле '{field}': {json.dumps(data[field], ensure_ascii=False)}")
            else:
                logger.info(f"❌ [{request_id}] Поле '{field}' отсутствует")
        
        # Проверяем наличие поля с сообщением
        message_fields = ['message', 'msg', 'text', 'content', 'body']
        for field in message_fields:
            if field in data:
                logger.info(f"✅ [{request_id}] Найдено поле '{field}': {json.dumps(data[field], ensure_ascii=False)}")
            else:
                logger.info(f"❌ [{request_id}] Поле '{field}' отсутствует")
        
        # Проверяем наличие поля с чатом
        chat_fields = ['chat', 'peer', 'conversation', 'dialog', 'channel']
        for field in chat_fields:
            if field in data:
                logger.info(f"✅ [{request_id}] Найдено поле '{field}': {json.dumps(data[field], ensure_ascii=False)}")
            else:
                logger.info(f"❌ [{request_id}] Поле '{field}' отсутствует")
        
        # Проверяем тип события
        event_types = ['message', 'callback_query', 'bot_started', 'inline_query', 'chosen_inline_result']
        found_events = []
        for event in event_types:
            if event in data:
                found_events.append(event)
                logger.info(f"✅ [{request_id}] Обнаружено событие: {event}")
        
        if not found_events:
            logger.warning(f"⚠️ [{request_id}] Не удалось определить тип события!")
        
        # Сохраняем данные в файл для последующего анализа
        try:
            with open(f'/tmp/webhook_{request_id}.json', 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 [{request_id}] Данные сохранены в файл: /tmp/webhook_{request_id}.json")
        except Exception as e:
            logger.error(f"❌ [{request_id}] Не удалось сохранить данные в файл: {e}")
        
        # Создаем цикл событий и обрабатываем обновление
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            logger.info(f"🔄 [{request_id}] Передаём данные в dispatcher.process_update()")
            result = loop.run_until_complete(bot.dp.process_update(data))
            logger.info(f"✅ [{request_id}] Результат обработки: {result}")
        except Exception as e:
            logger.error(f"❌ [{request_id}] Ошибка при обработке в диспетчере: {e}", exc_info=True)
            result = False
        finally:
            loop.close()
        
        return jsonify({
            "status": "ok", 
            "processed": result,
            "request_id": request_id
        })
        
    except Exception as e:
        logger.error(f"❌ [{request_id}] Критическая ошибка вебхука: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e),
            "request_id": request_id
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Проверка здоровья"""
    logger.debug("✅ Health check")
    return jsonify({
        "status": "healthy",
        "platform": settings.PLATFORM,
        "bot": "paint_bot",
        "timestamp": datetime.now().isoformat()
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
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/logs/<request_id>', methods=['GET'])
def get_log(request_id):
    """Получить сохранённый лог по ID запроса"""
    try:
        with open(f'/tmp/webhook_{request_id}.json', 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except:
        return jsonify({"error": "Log not found"}), 404

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