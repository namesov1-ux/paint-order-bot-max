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

from config.settings import settings
from core.dispatcher import Dispatcher
from core.adapters.max_adapter import MAXAdapter
from handlers import start, search, vin_search

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,  # Временно ставим DEBUG для отладки
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

@app.route('/ping', methods=['GET'])
def ping():
    """Тестовый эндпоинт для проверки доступности сервиса"""
    return jsonify({
        "status": "pong",
        "time": datetime.now().isoformat(),
        "service": "paint-bot"
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик вебхуков с поддержкой реальной структуры MAX API"""
    request_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    
    try:
        # Получаем данные
        data = request.json
        logger.info(f"📡 [{request_id}] Получен вебхук")
        logger.info(f"📦 [{request_id}] Данные: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if not data:
            logger.warning(f"⚠️ [{request_id}] Пустой запрос")
            return jsonify({"status": "error", "message": "Empty request"}), 400
        
        # Определяем тип обновления
        update_type = data.get('update_type')
        logger.info(f"🔍 [{request_id}] Тип обновления: {update_type}")
        
        # Извлекаем данные в зависимости от типа
        if update_type == 'message_created':
            # Обрабатываем новое сообщение
            message_data = data.get('message', {})
            sender = message_data.get('sender', {})
            recipient = message_data.get('recipient', {})
            body = message_data.get('body', {})
            
            logger.info(f"👤 [{request_id}] Отправитель: {sender}")
            logger.info(f"💬 [{request_id}] Получатель: {recipient}")
            logger.info(f"📝 [{request_id}] Текст: {body.get('text')}")
            
            # Создаем структуру, совместимую с нашим диспетчером
            adapted_data = {
                'update_type': update_type,
                'message': {
                    'from': {
                        'id': sender.get('user_id'),
                        'first_name': sender.get('first_name'),
                        'last_name': sender.get('last_name'),
                        'username': sender.get('name')
                    },
                    'chat': {
                        'id': recipient.get('chat_id', recipient.get('user_id')),
                        'type': recipient.get('chat_type', 'private')
                    },
                    'text': body.get('text'),
                    'date': message_data.get('timestamp', data.get('timestamp', 0)) // 1000
                }
            }
            
            logger.info(f"🔄 [{request_id}] Адаптированные данные: {json.dumps(adapted_data, indent=2, ensure_ascii=False)}")
            
            # Передаем в диспетчер
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(bot.process_webhook(adapted_data))
                logger.info(f"✅ [{request_id}] Результат обработки: {result}")
            except Exception as e:
                logger.error(f"❌ [{request_id}] Ошибка в диспетчере: {e}", exc_info=True)
                result = False
            finally:
                loop.close()
            
            return jsonify({"status": "ok", "processed": result})
            
        elif update_type == 'bot_started':
            # Обработка запуска бота (кнопка "Старт")
            logger.info(f"🚀 [{request_id}] Бот запущен")
            
            # Создаем структуру для /start
            adapted_data = {
                'update_type': 'message_created',
                'message': {
                    'from': {
                        'id': data.get('user_id', 0),
                        'first_name': data.get('first_name', ''),
                        'last_name': data.get('last_name', ''),
                        'username': data.get('name', '')
                    },
                    'chat': {
                        'id': data.get('chat_id', data.get('user_id', 0)),
                        'type': 'private'
                    },
                    'text': '/start',
                    'date': int(datetime.now().timestamp())
                }
            }
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(bot.process_webhook(adapted_data))
                logger.info(f"✅ [{request_id}] Результат обработки старта: {result}")
            except Exception as e:
                logger.error(f"❌ [{request_id}] Ошибка при обработке старта: {e}", exc_info=True)
                result = False
            finally:
                loop.close()
            
            return jsonify({"status": "ok", "processed": result})
            
        else:
            logger.warning(f"⚠️ [{request_id}] Неизвестный тип update: {update_type}")
            return jsonify({"status": "ok", "message": f"Unhandled update type: {update_type}"})
        
    except Exception as e:
        logger.error(f"❌ [{request_id}] Критическая ошибка: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e),
            "request_id": request_id
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Проверка здоровья"""
    return jsonify({
        "status": "healthy",
        "bot": "paint_bot",
        "time": datetime.now().isoformat()
    })

@app.route('/debug', methods=['GET'])
def debug():
    """Отладочная информация"""
    return jsonify({
        "bot_initialized": True,
        "platform": settings.PLATFORM,
        "handlers": {
            "message": len(bot.dp.message_handlers),
            "callback": len(bot.dp.callback_handlers)
        },
        "settings": {
            "BOT_TOKEN": settings.BOT_TOKEN[:10] + "..." if settings.BOT_TOKEN else None,
            "MAX_API_URL": settings.MAX_API_URL,
            "ADMIN_IDS": settings.ADMIN_IDS
        },
        "time": datetime.now().isoformat()
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