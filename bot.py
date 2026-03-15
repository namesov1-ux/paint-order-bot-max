# bot.py - МАКСИМАЛЬНО УПРОЩЁННАЯ ВЕРСИЯ ДЛЯ ОТЛАДКИ
import os
import sys
import logging
import json
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    """Простейший обработчик для отладки"""
    
    # Логируем метод
    logger.info(f"METHOD: {request.method}")
    
    # Логируем заголовки
    logger.info(f"HEADERS: {dict(request.headers)}")
    
    if request.method == 'GET':
        return jsonify({"status": "ok", "method": "GET"})
    
    # Для POST - просто логируем всё и возвращаем 200
    try:
        data = request.json
        logger.info("=" * 60)
        logger.info("📦 ПОЛУЧЕНЫ ДАННЫЕ:")
        logger.info(json.dumps(data, indent=2, ensure_ascii=False))
        logger.info("=" * 60)
        
        # Анализируем ключи
        logger.info(f"КЛЮЧИ ВЕРХНЕГО УРОВНЯ: {list(data.keys())}")
        
        # Ищем поле 'from'
        if 'from' in data:
            logger.info(f"✅ 'from' НАЙДЕН: {data['from']}")
        else:
            logger.info("❌ 'from' НЕ НАЙДЕН")
            
            # Ищем похожие поля
            for key in data.keys():
                if key in ['user', 'sender', 'author', 'creator']:
                    logger.info(f"🔍 Найдено похожее поле '{key}': {data[key]}")
        
        # Проверяем структуру
        if 'message' in data and isinstance(data['message'], dict):
            logger.info(f"message keys: {list(data['message'].keys())}")
            if 'from' in data['message']:
                logger.info(f"✅ 'from' в message: {data['message']['from']}")
        
        return jsonify({"status": "ok", "received": True})
        
    except Exception as e:
        logger.error(f"ОШИБКА: {e}", exc_info=True)
        return jsonify({"status": "error"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🚀 Запуск на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)