# core/dispatcher.py
import logging
import json
import traceback
from typing import Dict, Any, List, Optional, Callable
from .adapters.base import BaseAdapter, User, Chat, Message, CallbackQuery

logger = logging.getLogger(__name__)

class Handler:
    def __init__(self, callback: Callable, filters: List):
        self.callback = callback
        self.filters = filters

class Router:
    def __init__(self, name: str = None):
        self.name = name
        self.message_handlers = []
        self.callback_handlers = []
    
    def message(self, *filters):
        def decorator(func):
            self.message_handlers.append(Handler(func, filters))
            return func
        return decorator
    
    def callback(self, *filters):
        def decorator(func):
            self.callback_handlers.append(Handler(func, filters))
            return func
        return decorator

class Dispatcher:
    def __init__(self, adapter: BaseAdapter):
        self.adapter = adapter
        self.message_handlers = []
        self.callback_handlers = []
        self._routers = []
    
    def include_router(self, router: Router):
        self._routers.append(router)
        self.message_handlers.extend(router.message_handlers)
        self.callback_handlers.extend(router.callback_handlers)
        logger.info(f"📦 Подключен роутер: {router.name}")
    
    async def process_update(self, update_data: Dict) -> bool:
        """Обработка входящего обновления от MAX"""
        try:
            logger.info("=" * 60)
            logger.info("🔍 ПОЛУЧЕНЫ ДАННЫЕ ОТ MAX:")
            logger.info(json.dumps(update_data, indent=2, ensure_ascii=False))
            logger.info("=" * 60)
            
            # Определяем тип события по update_type
            update_type = update_data.get('update_type', '')
            
            if update_type == 'message_created':
                logger.info("📩 Обнаружен тип: message_created")
                return await self._process_message(update_data)
            elif update_type == 'callback_query':
                logger.info("🔄 Обнаружен тип: callback_query")
                return await self._process_callback(update_data)
            elif update_type == 'bot_started':
                logger.info("🚀 Обнаружен тип: bot_started")
                return await self._process_bot_started(update_data)
            else:
                logger.warning(f"⚠️ Неизвестный тип update: {update_type}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки update: {e}", exc_info=True)
            return False
    
    async def _process_message(self, data: Dict) -> bool:
        """Обработка входящего сообщения от MAX"""
        try:
            logger.info(f"📩 Обработка сообщения...")
            
            # Извлекаем данные из структуры MAX
            message_data = data.get('message', {})
            sender_data = message_data.get('sender', {})
            recipient_data = message_data.get('recipient', {})
            body_data = message_data.get('body', {})
            
            # Логируем для отладки
            logger.info(f"👤 Данные отправителя: {sender_data}")
            logger.info(f"💬 Данные получателя: {recipient_data}")
            logger.info(f"📝 Текст сообщения: {body_data.get('text', '')}")
            
            # Создаем объект пользователя (отправителя)
            user = User(
                id=sender_data.get('user_id', 0),
                first_name=sender_data.get('first_name', ''),
                last_name=sender_data.get('last_name', ''),
                username=None  # MAX не передаёт username
            )
            
            # Создаем объект чата (куда пришло сообщение)
            chat_id = recipient_data.get('chat_id', recipient_data.get('user_id', 0))
            chat = Chat(
                id=chat_id,
                type=recipient_data.get('chat_type', 'private')
            )
            
            # Конвертируем timestamp из миллисекунд в секунды
            timestamp = message_data.get('timestamp', data.get('timestamp', 0))
            if timestamp > 1e12:  # если timestamp в миллисекундах
                timestamp = timestamp // 1000
            
            # Создаем объект сообщения
            message = Message(
                message_id=0,  # MAX не передаёт message_id
                from_user=user,
                chat=chat,
                date=timestamp,
                text=body_data.get('text', ''),
                bot=self.adapter
            )
            
            # Добавляем метод answer для обратной совместимости
            message.reply = message.answer
            
            logger.info(f"✅ Создано сообщение от {user.id}: '{message.text}'")
            
            # Ищем подходящий handler
            for handler in self.message_handlers:
                filters_passed = True
                for filter_func in handler.filters:
                    if callable(filter_func):
                        try:
                            # Проверяем команды
                            if hasattr(filter_func, 'commands'):
                                cmd_match = False
                                for cmd in filter_func.commands:
                                    if message.text and message.text.startswith(f'/{cmd}'):
                                        cmd_match = True
                                        logger.info(f"✅ Команда /{cmd} совпала")
                                        break
                                if not cmd_match:
                                    filters_passed = False
                                    break
                            elif not filter_func(message):
                                filters_passed = False
                                break
                        except Exception as e:
                            logger.error(f"❌ Ошибка в фильтре: {e}")
                            filters_passed = False
                            break
                
                if filters_passed:
                    logger.info(f"✅ Найден handler: {handler.callback.__name__}")
                    await handler.callback(message)
                    return True
            
            logger.info(f"⚠️ Нет подходящего handler для сообщения")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка в _process_message: {e}", exc_info=True)
            return False
    
    async def _process_callback(self, data: Dict) -> bool:
        """Обработка callback query от MAX"""
        try:
            logger.info(f"🔄 Обработка callback...")
            
            # Извлекаем данные callback
            callback_data = data.get('callback_query', {})
            message_data = callback_data.get('message', {})
            sender_data = callback_data.get('sender', {})
            
            # Создаем объекты
            user = User(
                id=sender_data.get('user_id', 0),
                first_name=sender_data.get('first_name', ''),
                last_name=sender_data.get('last_name', ''),
                username=None
            )
            
            chat = Chat(
                id=message_data.get('chat_id', 0),
                type='private'
            )
            
            message = Message(
                message_id=0,
                from_user=user,
                chat=chat,
                date=0,
                text=message_data.get('text', ''),
                bot=self.adapter
            )
            
            callback = CallbackQuery(
                id=callback_data.get('id', ''),
                from_user=user,
                message=message,
                data=callback_data.get('data', '')
            )
            
            logger.info(f"🔄 Callback от {user.id}: {callback.data}")
            
            # Ищем подходящий handler
            for handler in self.callback_handlers:
                filters_passed = True
                for filter_func in handler.filters:
                    if callable(filter_func):
                        try:
                            if not filter_func(callback):
                                filters_passed = False
                                break
                        except Exception as e:
                            logger.error(f"❌ Ошибка в фильтре callback: {e}")
                            filters_passed = False
                            break
                
                if filters_passed:
                    logger.info(f"✅ Найден callback handler: {handler.callback.__name__}")
                    await handler.callback(callback)
                    return True
            
            logger.info(f"⚠️ Нет подходящего callback handler")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка в _process_callback: {e}", exc_info=True)
            return False
    
    async def _process_bot_started(self, data: Dict) -> bool:
        """Обработка события запуска бота (кнопка Старт)"""
        try:
            logger.info(f"🚀 Обработка bot_started...")
            
            # Извлекаем данные из структуры MAX
            message_data = data.get('message', {})
            sender_data = message_data.get('sender', {})
            
            # Создаем объекты
            user = User(
                id=sender_data.get('user_id', 0),
                first_name=sender_data.get('first_name', ''),
                last_name=sender_data.get('last_name', ''),
                username=None
            )
            
            chat = Chat(
                id=user.id,
                type='private'
            )
            
            # Создаем тестовое сообщение для обработчика start
            message = Message(
                message_id=0,
                from_user=user,
                chat=chat,
                date=0,
                text='/start',
                bot=self.adapter
            )
            message.reply = message.answer
            
            logger.info(f"🚀 Пользователь {user.id} запустил бота")
            
            # Ищем handler для /start
            for handler in self.message_handlers:
                filters_passed = True
                for filter_func in handler.filters:
                    if callable(filter_func):
                        try:
                            if hasattr(filter_func, 'commands'):
                                if 'start' in filter_func.commands:
                                    continue
                                else:
                                    filters_passed = False
                                    break
                            elif not filter_func(message):
                                filters_passed = False
                                break
                        except Exception as e:
                            logger.error(f"❌ Ошибка в фильтре bot_started: {e}")
                            filters_passed = False
                            break
                
                if filters_passed:
                    logger.info(f"✅ Найден handler для /start: {handler.callback.__name__}")
                    await handler.callback(message)
                    return True
            
            logger.info(f"⚠️ Нет handler для /start")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка в _process_bot_started: {e}", exc_info=True)
            return False