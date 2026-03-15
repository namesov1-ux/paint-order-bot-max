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
            logger.info("🔍 Обработка данных от MAX")
            logger.info("=" * 60)
            
            update_type = update_data.get('update_type', '')
            
            if update_type == 'message_created':
                return await self._process_message(update_data)
            else:
                logger.warning(f"⚠️ Неизвестный тип update: {update_type}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки update: {e}", exc_info=True)
            return False
    
    async def _process_message(self, data: Dict) -> bool:
        """Обработка входящего сообщения от MAX"""
        try:
            message_data = data.get('message', {})
            sender_data = message_data.get('sender', {})
            recipient_data = message_data.get('recipient', {})
            body_data = message_data.get('body', {})
            
            user = User(
                id=sender_data.get('user_id', 0),
                first_name=sender_data.get('first_name', ''),
                last_name=sender_data.get('last_name', ''),
                username=None
            )
            
            chat = Chat(
                id=recipient_data.get('chat_id', recipient_data.get('user_id', 0)),
                type=recipient_data.get('chat_type', 'private')
            )
            
            message = Message(
                message_id=0,
                from_user=user,
                chat=chat,
                date=message_data.get('timestamp', data.get('timestamp', 0)) // 1000,
                text=body_data.get('text', ''),
                bot=self.adapter
            )
            
            message.reply = message.answer
            
            logger.info(f"👤 Пользователь {user.id}: {message.text}")
            
            for handler in self.message_handlers:
                filters_passed = True
                for filter_func in handler.filters:
                    if callable(filter_func):
                        try:
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
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка в _process_message: {e}", exc_info=True)
            return False
