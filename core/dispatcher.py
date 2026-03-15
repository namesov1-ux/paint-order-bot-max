# core/dispatcher.py
import logging
import json
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
            
            # Проверяем структуру данных от MAX
            if 'message' in update_data:
                logger.info("📩 Обнаружен тип: message")
                return await self._process_message(update_data)
            elif 'callback_query' in update_data:
                logger.info("🔄 Обнаружен тип: callback_query")
                return await self._process_callback(update_data)
            elif 'bot_started' in update_data:
                logger.info("🚀 Обнаружен тип: bot_started")
                return await self._process_bot_started(update_data)
            else:
                logger.warning(f"⚠️ Неизвестный тип update: {list(update_data.keys())}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки update: {e}", exc_info=True)
            return False
    
    async def _process_message(self, data: Dict) -> bool:
        """Обработка входящего сообщения"""
        try:
            logger.info(f"📩 Обработка сообщения. Полученные данные: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Извлекаем данные из структуры MAX
            message_data = data.get('message', {})
            
            # Извлекаем данные пользователя
            user_data = data.get('from', {})
            if not user_data and 'user' in data:
                user_data = data.get('user', {})
            
            # Извлекаем данные чата
            chat_data = data.get('chat', {})
            if not chat_data and 'peer' in data:
                chat_data = data.get('peer', {})
            
            # Создаем объекты с безопасным извлечением данных
            user_id = user_data.get('id', 0)
            if isinstance(user_id, str) and user_id.isdigit():
                user_id = int(user_id)
            
            user = User(
                id=user_id,
                first_name=user_data.get('first_name', user_data.get('name', '')),
                last_name=user_data.get('last_name'),
                username=user_data.get('username')
            )
            
            chat_id = chat_data.get('id', user_id)
            if isinstance(chat_id, str) and chat_id.isdigit():
                chat_id = int(chat_id)
            
            chat = Chat(
                id=chat_id,
                type=chat_data.get('type', 'private')
            )
            
            # Извлекаем текст сообщения
            text = message_data.get('text', data.get('text', ''))
            
            message_id = message_data.get('id', data.get('message_id', 0))
            if isinstance(message_id, str) and message_id.isdigit():
                message_id = int(message_id)
            
            timestamp = message_data.get('date', data.get('timestamp', data.get('date', 0)))
            
            message = Message(
                message_id=message_id,
                from_user=user,
                chat=chat,
                date=timestamp,
                text=text,
                bot=self.adapter
            )
            
            # Добавляем метод answer для обратной совместимости
            message.reply = message.answer
            
            logger.info(f"👤 Пользователь {user.id}: {message.text}")
            
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
        """Обработка callback query"""
        try:
            logger.info(f"🔄 Обработка callback. Полученные данные: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Извлекаем данные из структуры MAX
            callback_data = data.get('callback_query', {})
            
            # Извлекаем данные пользователя
            user_data = data.get('from', callback_data.get('from', {}))
            if not user_data and 'user' in data:
                user_data = data.get('user', {})
            
            # Извлекаем данные сообщения
            message_data = data.get('message', callback_data.get('message', {}))
            
            # Извлекаем данные чата
            chat_data = message_data.get('chat', {})
            if not chat_data and 'peer' in message_data:
                chat_data = message_data.get('peer', {})
            
            # Создаем объекты
            user_id = user_data.get('id', 0)
            if isinstance(user_id, str) and user_id.isdigit():
                user_id = int(user_id)
            
            user = User(
                id=user_id,
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name'),
                username=user_data.get('username')
            )
            
            chat_id = chat_data.get('id', user_id)
            if isinstance(chat_id, str) and chat_id.isdigit():
                chat_id = int(chat_id)
            
            chat = Chat(
                id=chat_id,
                type=chat_data.get('type', 'private')
            )
            
            message_id = message_data.get('id', 0)
            if isinstance(message_id, str) and message_id.isdigit():
                message_id = int(message_id)
            
            message = Message(
                message_id=message_id,
                from_user=user,
                chat=chat,
                date=message_data.get('date', 0),
                text=message_data.get('text', ''),
                bot=self.adapter
            )
            
            callback = CallbackQuery(
                id=callback_data.get('id', data.get('id', '')),
                from_user=user,
                message=message,
                data=callback_data.get('data', data.get('data', ''))
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
            logger.info(f"🚀 Обработка bot_started. Полученные данные: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Извлекаем данные
            user_data = data.get('from', data.get('user', {}))
            chat_data = data.get('chat', data.get('peer', {}))
            
            user_id = user_data.get('id', 0)
            if isinstance(user_id, str) and user_id.isdigit():
                user_id = int(user_id)
            
            user = User(
                id=user_id,
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name'),
                username=user_data.get('username')
            )
            
            chat_id = chat_data.get('id', user_id)
            if isinstance(chat_id, str) and chat_id.isdigit():
                chat_id = int(chat_id)
            
            chat = Chat(
                id=chat_id,
                type=chat_data.get('type', 'private')
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