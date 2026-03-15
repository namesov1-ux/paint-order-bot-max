# core/dispatcher.py
import logging
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
        """Обработка входящего обновления"""
        try:
            if 'message' in update_data:
                return await self._process_message(update_data['message'])
            elif 'callback_query' in update_data:
                return await self._process_callback(update_data['callback_query'])
        except Exception as e:
            logger.error(f"❌ Ошибка обработки update: {e}")
        return False
    
    async def _process_message(self, data: Dict) -> bool:
        user = User(
            id=data['from']['id'],
            first_name=data['from'].get('first_name', ''),
            last_name=data['from'].get('last_name'),
            username=data['from'].get('username')
        )
        chat = Chat(id=data['chat']['id'])
        message = Message(
            message_id=data.get('message_id', 0),
            from_user=user,
            chat=chat,
            date=data.get('date', 0),
            text=data.get('text')
        )
        
        for handler in self.message_handlers:
            await handler.callback(message)
            return True
        
        return False
    
    async def _process_callback(self, data: Dict) -> bool:
        user = User(
            id=data['from']['id'],
            first_name=data['from'].get('first_name', ''),
            last_name=data['from'].get('last_name'),
            username=data['from'].get('username')
        )
        message = Message(
            message_id=data['message']['message_id'],
            from_user=user,
            chat=Chat(id=data['message']['chat']['id']),
            date=data['message']['date'],
            text=data['message'].get('text')
        )
        callback = CallbackQuery(
            id=data['id'],
            from_user=user,
            message=message,
            data=data.get('data', '')
        )
        
        for handler in self.callback_handlers:
            await handler.callback(callback)
            return True
        
        return False
